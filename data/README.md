# IBD Evidence Intelligence: Prototype Dataset

Built 2026-09-19 for the data model in [../DATA_SPEC.md](../DATA_SPEC.md).

| File | What it is |
|---|---|
| `IBD_Evidence_Dataset.xlsx` | One sheet per table. **Cell colour shows provenance.** Start with the README sheet. |
| `json/<table>.json` | The same data for the dashboard. Every row has `_provenance` and `_source_ids`. |
| `json/_manifest.json` | Row counts and provenance mix per table. |
| `raw/ctgov/*.json` | Raw ClinicalTrials.gov API responses, the audit trail for registry fields. |
| `raw/pubs/*.json` | Raw PubMed + Crossref publication search results (3-year window) and `processed.json`. |
| `raw/uegw/uegw_abstracts.tsv` | UEG Week 2023–2025 posters/orals naming a tracked drug in the title, copied verbatim from UEG's Gutflix library via the browser (titles only; a few titles are truncated at source). |
| `raw/uegw/uegw_symposia.tsv` | Industry symposia at UEG Week 2023–2025 by company. |
| `raw/programs/acg_orals.tsv` | IBD oral papers at ACG 2023–2025, copied verbatim from ACG's official programme ("Oral Abstracts" listing). Used to mark ACG abstracts as oral; every other ACG abstract is a poster. Presenter names deliberately not stored. |

## Provenance: what is real and what is simulated

Every **field** in every row is tagged. The Excel file colour-codes each cell:

| Tag | Excel colour | Meaning | What to do |
|---|---|---|---|
| `public_verified` | white | From the ClinicalTrials.gov API or a web source checked on the build date | Keep; refresh periodically |
| `public_unverified` | yellow | Public knowledge that was **not** re-checked (e.g. QUASAR Ph3 rates, some approval months) | Verify against the cited source |
| `derived` | blue | Calculated by a stated rule (e.g. LPI = PCD − primary timepoint; readout = PCD + 3 months; gap coverage) | Don't edit; fix the inputs and rebuild |
| `simulated` | orange | Invented for the prototype | **Replace with real data** |
| `reference` | grey | Taxonomy or configuration (funder list, care segments, publication ladder) | Confirm with the team |

Each row also carries a summary: `data_origin` (a single tag, or `mixed`), plus `simulated_fields`, `derived_fields`, `unverified_fields` and `source_ids`. Source IDs resolve in the `sources` table. `SRC-SIM` means simulated and `SRC-AI` means an AI-inferred hypothesis.

**Overall mix:** about 7,000 verified public cells, 1,970 derived, 6,340 simulated, 210 unverified public and 290 reference.

## What is real (public)

- **51 J&J / J&J-product studies:** 44 from the registry and 7 clearly labelled `SIM-` studies.
  - Registry fields: NCT, acronym, phase, status, N, start/FPI, primary completion, completion/LPO, sponsor, arms, primary outcomes, and sites per country.
  - Includes studies announced recently: CHARGE (guselkumab vs risankizumab H2H in CD, Ph3b per the official title; registry phase field: Phase 3; N=530), DUET ENCORE-UC/CD (JNJ-4804 Ph3), REASON (transmural healing), ICONIC-UC (N=882) and ICONIC-CD (Ph2b/3, N=1,092), FUZION CD, pediatric MACARONI-23 / QUASAR Jr / TRILOGY, and more than 20 RWE studies.
- **93 competitor trials:** Skyrizi, Omvoh, Rinvoq, Entyvio, Velsipity, Zeposia, obefazimod, tulisokibart, duvakitug, afimkibart and MORF-057. Industry-sponsored Ph2–4 with primary completion in 2022 or later.
- **26 published efficacy results:** QUASAR, GALAXI 2/3 vs ustekinumab, GRAVITI, ASTRO, FUZION, ANTHEM-UC, DUET-UC/CD, SEQUENCE and ABTECT.
- **Regulatory events:** e.g. Tremfya SC induction in UC (FDA 2025-09-19, EC 2025-10-24); Icotyde psoriasis approval (2026-03-18); Skyrizi SC induction in CD filed (FDA 2026-04-27, EMA 2026-09).
- **Competitor events:** tulisokibart ATLAS-UC positive (2026-06-22); obefazimod ABTECT maintenance positive (2026-06-01) with the NDA planned for Q4 2026.
- **Market figures:** Tremfya Q2 2026 sales of $2.05B (+72.5%) and 58% of IL-23 UC induction; Stelara $740M (−55.7%); Skyrizi 2026 guidance of $21.6B.
- **Guidelines and HTA:** ACG UC 2025, AGA CD living guideline (Nov 2025) and NICE recommendations.
- **Congress dates:** ACG 2026 (Nashville, Oct 9–14), UEGW 2026 (Barcelona, Oct 17–20), ECCO 2027 (Copenhagen, Mar 3–6) and DDW 2027 (Washington DC, May 15–18).

## What is simulated (replace first)

1. **Strategy layer:** strategic imperatives, key questions, evidence gaps and the study → gap fit scores. Replace these with the real brand/medical plan.
2. **Funding:** all of `study_funding` (funder split, cost, spend, fiscal-year phasing). Costs use N × cost per patient benchmarks.
3. **Operations:** `study_enrollment` curves (only N and dates are real); milestone *baseline* dates and slippage.
4. **Placeholders for real trials:** `study_baseline` and `study_safety`. Take the real values from publications.
5. **Dissemination:** planned outputs (IDs `OUT-S…`), tactics, share of voice and MLR status.
6. **Competitive intelligence:** competitor gaps, inferred strategies, impact assessments and projected events (`EV-1xx`). These are AI hypotheses, not facts.
7. **Market shares, field insights, HTA outside the UK, AI insights, recommendations, scenarios and the decision log.**

## Rules and caveats

- **FPI** is the registry "actual start date", which ClinicalTrials.gov defines as when the first participant enrolled. **LPI** is not public: it is either derived (PCD − primary timepoint) or marked unknown.
- **Competitor expected readout** is PCD + 3 months unless a public topline exists. Registry dates are often estimates (`pcd_date_type`).
- **Cross-trial result comparisons are not head-to-head.** Result rows carry a caveat field.
- Classification fields on studies (indication, study type, care segment, regulatory intent) come from keyword rules on registry text. They are tagged `derived` and should be spot-checked.
- Tulisokibart NCT06052059 is Merck's UC Ph3 *programme*. The ATLAS-UC topline is linked to it.

## Rebuild or refresh

```bash
cd ibd-evidence-dashboard && python3 scripts/fetch_ctgov.py
```

```bash
cd ibd-evidence-dashboard && .venv/bin/python scripts/build_dataset.py
```

To add a real fact, put it in `scripts/curated_public.py` with a source, then rebuild. To replace simulated values, edit the matching block in `scripts/build_dataset.py`. Simulation is deterministic (seed 42), so values you haven't touched stay the same.

## Editing data (Data Editor)

Run the dashboard with the edit server (instead of a plain file server):

```bash
cd ibd-evidence-dashboard && python3 scripts/serve.py
```

Then open http://127.0.0.1:8765 → **Data Editor**. Click any cell to edit, add or delete rows, and **save with your name and a reason/source**. Edits:

- are stored as an append-only log in `data/overrides/overrides.json` (who, when, old → new, note), so they survive every rebuild and data refresh;
- show up in the dashboard immediately, tagged **manual** (green);
- are applied by `scripts/build_dataset.py` on **Rebuild**, which also recalculates derived scores (e.g. gap criticality, readiness) and regenerates the Excel file (manual cells are green; the note column records who/when/why);
- can be reverted from **Change history** (the reverted entry stays in the log for audit).

Rows are identified by their first field (e.g. `study_id`, `gap_id`, `pub_id`); if a source refresh removes a row, the build prints a warning listing edits that no longer match. Editing a *derived* field overrides the calculation and is kept on rebuild.

## How real publications feed the insights (derived)

- Each publication is linked to J&J studies by trial name (QUASAR, GALAXI, GRAVITI, ASTRO, FUZION, DUET, VEGA, ANTHEM, ICONIC…) and to evidence gaps by topic rules (`GAP_TOPICS` in `scripts/build_dataset.py`).
- Gap fields `published_closure_pct`, `pubs_jnj_journal/congress`, `competitor_pubs_12m`, `evidence_on_record` come from those links. Congress-only evidence counts up to 60%; some gaps have a lower cap when only a specific kind of evidence can close them (`GAP_PUB_CAP`, reason in `publication_cap_reason`, e.g. GAP-01 needs the CHARGE RCT).
- Study fields `pubs_congress`, `pubs_journal`, `peer_reviewed_paper` drive the evidence-debt alerts. Papers published before the search window are listed in `PRIOR_PAPERS` (unverified).
- `ai_insights` rows `AI-Pxx`, `publication_themes` and `competitor_strategies.publication_signals` are generated from real titles on every rebuild. Topic rules are keyword-based: spot-check and correct in the Data Editor.

## Oral presentations: how they are identified

| Congress | Oral signal | Source |
|---|---|---|
| ECCO | `OP` code = oral in a scientific session; `DOP` = digital oral (not counted as a full oral slot) | JCC supplement abstract codes |
| DDW | numbered abstract = oral (letter suffix = late-breaker); `Sa/Su/Mo/Tu` = poster | *Gastroenterology* supplement codes |
| UEG Week | "presentation" format in UEG's library | Gutflix |
| ACG | listed in the official programme's "Oral Abstracts" | `raw/programs/acg_orals.tsv`. The AJG number is **not** a guide: plain-numbered items (e.g. 89, 112 in 2025) are posters |

The Oral podium (Publications & SoV) counts full oral slots per asset, the oral rate (orals / abstracts) and how many orals are real-world studies. DDW 2024 has fewer abstracts indexed in Crossref (97 vs 124–152 in later years), so its counts are a floor.

## Product profiles (label-based)

Competitive Intel → **Profile vs competitor** compares TREMFYA and SKYRIZI attribute by attribute (administration, monitoring, safety, efficacy, evidence), for Crohn's and UC, under **today's labels** and **if SKYRIZI SC induction is approved as filed**.

| Table | What it holds |
|---|---|
| `regimens` | Dosing regimens copied from the US labels (TREMFYA revised 05/2026, SKYRIZI revised 6/2026; text kept in `raw/labels/`). Filed regimens carry only what the sponsor disclosed; blank = not disclosed |
| `product_attributes` | One row per attribute × indication, with both values, the verdict today and if approved, why, and who it matters to |
| `regimen_burden` | Derived year-1 burden per treatment path: injections (one per device), infusions and minimum infusion hours, dosing days, liver-test window |
| `watch_items` | Open questions (e.g. SKYRIZI SC induction dose) and the source that resolves each |

Verdict rules (`verdict()` in `scripts/build_dataset.py`): convenience and safety verdicts come only from labels; efficacy is never compared across trials ("No claim"); "not disclosed" is **Unknown**, never a disadvantage; an ongoing head-to-head trial makes a comparison **Pending**. To add a competitor, add its label regimens and attributes to `scripts/curated_public.py` with sources and rebuild.

## Lifecycle and loss of exclusivity (LOE)

Tables `loe`, `study_loe_window`, `loe_start_by`; view **Lifecycle & LOE**.

- **`loe`**: one row per product and market (US, EU) for all 15 products. The public signals were checked on 26 Sep 2026 in company filings:
  - TREMFYA: composition patent family, US 2031 (J&J 10-K FY2025).
  - SKYRIZI: US composition patent 2033.
  - RINVOQ: no US generic before April 2037, under settlements (AbbVie 10-K).
  - OMVOH: US compound patent 2037 and data protection 2035; EU patent 2038 (Lilly 10-K).
  - ZEPOSIA: US 2033, EU 2034 (BMS 10-K).
  - ENTYVIO: some patents to 2032; biosimilar AVT16 decision expected Q1 2027; Takeda sued in Sep 2026 (Takeda 20-F, Alvotech, Pearce IP).
  - STELARA: biosimilars on the US market since Jan 2025.

  Filings give only the year, so the planning date uses mid-year. Anything not public is a **placeholder (simulated)**: the TREMFYA EU date, icotrokinra, JNJ-4804 and pipeline competitors. The first-approval dates for older products are public knowledge that was not re-checked.
- **The TREMFYA date is a public signal, not J&J's LOE.** Other patent families may extend it. J&J IP must confirm the planning date (watch item W-006, recommendation REC-009). Edit it in the Data Editor (group "Lifecycle & LOE").
- **`study_loe_window`** (derived): for each J&J study, the chain runs readout, then paper, then guideline/HTA use, then years of use before the brand's US planning LOE.
  - Readout: the topline milestone, or primary completion + 3 months (+2 months for RWE).
  - Paper: the milestone or the first linked journal publication. Otherwise readout + 12 months (trials), 9 (prospective RWE) or 6 (retrospective RWE, synthesis).
  - Guideline/HTA use: paper + 18 months (reference assumption).
  - Windows: 3+ years, 1–3, 0–1, or after LOE.
  - Exceptions: paediatric studies (US paediatric exclusivity can add 6 months), post-marketing obligations and registrational studies.
- **`loe_start_by`** (derived): the last month a new study of each type can start and still give 2 years of use before LOE, plus the years of use if it started today. Typical duration is the median start-to-primary-completion time of our J&J studies of that type.
- The view recalculates live when you move the TREMFYA LOE, the paper-to-guideline lag or the minimum years. The result is sensitive to these: moving TREMFYA's US LOE 2 years later reduces the studies with under a year of use from 20 to 2.

## Evidence depth: what each study will and won't deliver

Tables `evidence_domains`, `study_endpoints`, `study_evidence_profile`, `evidence_depth_by_domain`. They feed the Studies & Timeline cards, the study and gap drawers, and insights AI-E01 and AI-E02.

- **All registered outcomes are kept:** primary, secondary and "other" (exploratory), each with its time frame. Before this, the build kept only 8 secondary outcomes (FUZION CD registers 39). That's 2,218 outcomes across 51 J&J and 93 competitor studies.
- **Keyword rules sort each outcome into 13 evidence types:**
  - clinical, endoscopic, histologic, transmural/bowel imaging, fistula, steroid-free
  - biomarkers, PROs/quality of life, persistence, resource use/cost, safety, drug levels
  - comparison vs another drug, taken from the study design: a randomised arm (direct), a real-world cohort, or a network meta-analysis (indirect)

  The rules are in `evidence_domains`. Every outcome is marked "auto (review)"; correct a row in the Data Editor (group "Evidence depth") and the profiles follow on the next build. About 14% of outcomes stay unassigned, mostly baseline characteristics.
- **Time horizon:** the longest timepoint of each outcome, bucketed as ≤12 weeks, ≤1 year or >1 year. The parser handles "Week M-40" (maintenance weeks, counted after a 12-week induction) and lists like "Weeks 12, 48 and 96".
- **Delivered vs promised:** J&J publication titles linked to a study also count as "reported". GALAXI's and QUASAR's long-term papers count as delivered even though their registry outcomes stop at about 1 year.
- **"Not registered" means not promised,** not "definitely absent". Exploratory endpoints are often unregistered, so confirm with study teams before acting.
- **Gap fit:** each gap now states the evidence types it needs (`evidence_gaps.needed_domains`; proposed, the evidence team confirms). A study's fit to a gap is the analyst's mapping, capped at what its registered or reported endpoints can answer. Three fits dropped:
  - GALAXI → GAP-03: no transmural endpoint.
  - TRILOGY → GAP-05: a safety-only paediatric extension.
  - The simulated US claims study → GAP-07: can't measure clinical effectiveness.

  Fits set by hand in the Data Editor are never capped.

## Insight review (Sep 2026)

All insights are now generated from the data. The former simulated examples AI-001…006 were rebuilt after the LOE and evidence-depth layers, in the review block of `build_dataset.py`.

- **Corrected facts:**
  - SKYRIZI SC-induction FDA decision: late 2026 (AbbVie guidance), not Feb 2027.
  - GAP-10 is no longer study-less.
  - The events list adds the ENTYVIO biosimilar litigation.
- **LOE and depth context added to:** P03, P04, P05, P06, D01, E01 and L01.
- **New portfolio insights:**
  - AI-PF01: TREMFYA, icotrokinra and JNJ-4804 share an IL-23 pathway and the same patients; the successors arrive about two years before TREMFYA's US LOE signal; GAP-20 (sequencing) has no study.
  - AI-PF02: evidence depth doesn't transfer; no transmural or biomarker endpoints in the icotrokinra or JNJ-4804 trials.
- **Recommendations:** REC-004 (CHARGE) now asks for a business-case review against LOE before EMEA co-funding. REC-010 (portfolio evidence plan) and REC-011 (bowel ultrasound and calprotectin in the successors' extensions) are new.

## Publication ladder: optional interim rung (Sep 2026)

- **New rung:** the trial ladder has an optional "Interim analysis" rung between Baseline and Topline. It's shown dashed in the study drawer.
- **When it applies:** open-label, single-arm and extension studies, or a pre-specified interim analysis that is made public. Blinded randomised trials usually don't publish interim efficacy before the primary readout.
- **Classification:** publications count as "Interim analysis" when a trial title says "interim" and has no observational wording; there are 11 today, none for J&J brands. Real-world interim data cuts stay in the real-world ladder.
- **Gap closure:** an interim paper counts 0.5 toward closing a gap (0.3 for an abstract).
- **Status:** the ladder is a reference configuration for the prototype, to be replaced with J&J publication planning standards.

## Methodology buttons (ⓘ)

- **What:** cards with calculated numbers have an ⓘ button. Clicking it shows What it shows · Source · How it's calculated · Limits · Provenance.
- **Where the texts live:** `METHODS` in `dashboard/index.html`, with 23 methodologies across 36 cards. Update them there when a calculation changes.

## AI assistants: how chat assistants answer IBD questions (Sep 2026)

Dissemination view → **AI assistants**. It monitors which drugs ChatGPT and Claude name when patients and HCPs ask unbranded IBD questions, which studies they cite, and whether they get checkable facts right. Monitoring only: nothing is done to influence the answers.

- **Question bank:** `LLM_QUESTIONS` in `scripts/curated_public.py` → table `llm_questions`. It has 34 questions: 12 patient, 16 HCP and 6 branded accuracy checks. Keep the wording fixed so runs stay comparable, and add new questions under new IDs.
- **Runs:** each file `data/raw/llm/<assistant>_<YYYY-MM-DD>.json` is one run: one assistant, one date, one fresh chat per question. It holds `run` (setup, method), an optional `web_search_used` list, and `questions` (`id`, `drugs` in order of mention joined by " > ", `studies`, `flags`). A flag starts with CORRECT, OMISSION, MISLEADING / UNDERSTATES or INACCURATE / WRONG, and the prefix sets the issue type.
- **Derived tables:**
  - `llm_runs`: per-run KPIs, plus `previous_run_id`, which points to the previous run of the same assistant.
  - `llm_answers`: one row per question and run.
  - `llm_drug_share`: share of unbranded answers that name each drug, and name it first, by persona. P11 and the accuracy checks are excluded.
  - Insights: AI-LLM01 and AI-LLM02.
- **Change over time:** drop a new run file in and rebuild (`python3 scripts/build_dataset.py && python3 scripts/build_dashboard_data.py`).
  - The KPI tiles then show the change against the previous run.
  - The TREMFYA-over-time chart adds a point per run.
  - The question drawer lists every run's answer, newest first.
- **Recommended cadence for a live version:** monthly, with each question asked 3 times per assistant. Answers vary between runs, so single-run differences of one or two answers are noise. The same setup is used each time (logged-out or incognito, default model, stated location).
- **Raw answer texts** are not stored in the repository; only the scored fields are.

## Provenance labels: fact, calculated, AI-inferred, simulated (Sep 2026)

Every card shows labels for the kinds of data it contains, so a tester can tell what to trust without checking each number. Hovering a label says which part of the card is which.

| Label | Meaning | Tag in the data |
|---|---|---|
| ✓ Fact | Found in a named public source: registry, label, filing, press release, publication, congress abstract, or an AI answer observed on the run date | `public_verified`, `reference` (definitions) |
| ∑ Calculated | Computed from other values by a stated rule; the ⓘ button gives the formula. Only as reliable as its inputs | `derived` |
| ✦ AI-inferred | A judgement written by AI while building the prototype: classification, estimate, assumption or interpretation. Plausible, not checked by a person | `ai_inferred` |
| ◇ Simulated | Made-up placeholder for internal J&J data (brand plan, budgets, field insights, market data). Study IDs starting SIM- are simulated | `simulated` |

- **Card labels** come from `CARD_PV` in `dashboard/index.html`, which gives each card title the kinds it contains plus a note. Value tags found inside the card are added automatically. A card with no label is logged to the browser console (`console.debug`).
- **Mark values** (top right) underlines single values: simulated, AI-inferred, calculated, public but not yet source-checked, and values edited by the team. Hovering a marked value explains its tag.
- **AI-inferred fields** are listed in `AI_INFERRED` in `scripts/build_dataset.py` and tagged at export. A value edited in the Data Editor becomes "manual".
- **Data & Provenance → What still needs checking** lists, per table:
  - unchecked public values: link a source;
  - AI-inferred values: have a person review them;
  - simulated values: replace them with internal data.

  Each row opens that table in the Data Editor.
- **Checked on 30 Sep 2026 and promoted to verified:**
  - QUASAR efficacy figures, against the Lancet abstract (PMID 39706209).
  - FDA approval dates for TREMFYA UC, SKYRIZI CD, OMVOH UC, RINVOQ UC, VELSIPITY UC and ZEPOSIA UC, against Drugs@FDA via openFDA. Wrong source links were replaced.
  - Company and generic names for RINVOQ, ENTYVIO, VELSIPITY and ZEPOSIA.
  - The VEGA primary paper (PMID 36738762) and the ACG Crohn's disease guideline 2025 (PMID 40701562).
- **Still unchecked (121 cells):**
  - congress venue names, dates and cities;
  - mechanism names;
  - HTA body names;
  - first-approval dates in the LOE table.

## Geographic Footprint (Sep 2026)

The former "World & Care Continuum" view is now **Geographic Footprint**. It holds registry facts only.
- **KPIs:** countries, sites and patients (planned or enrolled) across J&J-product studies, and how many of 12 key markets have a J&J site.
- **Site map.**
- **Footprint by asset:** trials, countries, sites, patients, sites per trial and key markets for J&J vs competitor assets.
- **Key-market matrix:** trials with a local site in US, CA, UK, DE, FR, IT, ES, JP, CN, KR, AU and BR.
- **Country table.**

Asset comparisons use active Phase 3 trials on both sides (recruiting, active or not yet recruiting; Ph3 or Ph2/3; industry-sponsored), because competitor site data is only fetched for those trials. Patients per country and investigator names are not public; one registry site usually means one principal investigator. Investigator data would come from J&J's trial management system, in aggregate only.

**Patient-segment coverage** and **Segments with thin evidence** (formerly "Care continuum coverage" and "Where evidence is missing") moved to Strategy & Gaps. The segment list is still a simulated placeholder. It came from reading "TCC" in the original brief as treatment/care continuum (DATA_SPEC §9, open question 1), which has not been confirmed.

## Guidelines, HTA decisions and asset names (30 Sep 2026)

- **Guidelines:** the main US, European and UK guidelines, found on PubMed:
  - ACG UC and CD (2025)
  - AGA living guidelines, UC (Dec 2024) and CD (Nov 2025)
  - ECCO medical treatment, CD (Oct 2024) and UC (Jul 2026)
  - BSG adult IBD (Jun 2025)

  Summaries only state what was checked: the AGA abstracts name guselkumab. The ECCO and BSG texts are not yet reviewed here and are marked so. Next-update dates remain simulated (version + 2 years).
- **HTA decisions for TREMFYA** now use the published decisions, and the simulated markets are removed:
  - **NICE**, TA1094 and TA1095 (28 Aug 2025): both recommended with restrictions.
  - **G-BA** (20 Nov 2025): UC, added benefit not proven; Crohn's, hint of minor added benefit after biologics.
  - **HAS:** UC (Jul 2025), moderate clinical benefit, no ASMR, reimbursed third line; Crohn's (Nov 2025), important clinical benefit, ASMR V.
  - **CDA-AMC:** UC (Nov 2025) and Crohn's (Sep 2025), reimburse with conditions.

  Australia, Italy and Japan are not yet checked. The random draws of the removed placeholders are kept, so other simulated data did not change.
- **Asset names:** plain names throughout: Icotrokinra, JNJ-4804, STELARA, MORF-057, and "Johnson & Johnson" or "Eli Lilly" as the company. Descriptions say "guselkumab + golimumab combination" instead of "co-antibody".

## Guideline positions: TREMFYA vs competitors (30 Sep 2026)

Access & Guidelines → **What the guidelines say** shows how each main guideline treats TREMFYA and seven competitors.
- **Guidelines read in full:**
  - ACG UC and CD 2025 (Am J Gastroenterol);
  - AGA living UC 2024 and CD 2025 (Gastroenterology, via PMC);
  - ECCO UC 2026 and CD 2024 (J Crohns Colitis);
  - BSG 2025 (Gut).
- **What is recorded:** one row per drug and recommendation in `GUIDELINE_POSITIONS` (`scripts/curated_public.py` → table `guideline_positions`). Each row has a setting (overall, new to advanced therapy, after advanced therapy, head-to-head, perianal, route), a position and a paraphrased note, never a quote.
- **Facts panel:** computed from these rows. The "What it could mean" box is labelled AI-inferred.
- **Main findings:**
  - TREMFYA is not covered in ECCO CD 2024 or BSG 2025 (UC and CD), while SKYRIZI is.
  - Head-to-head preferences exist only for vedolizumab over adalimumab (ACG UC, ECCO UC) and risankizumab over ustekinumab after anti-TNF (ACG CD).
  - No IL-23p19 drug is suggested for perianal fistulas.
  - Subcutaneous induction is named only for TREMFYA, in ACG CD and ECCO UC.
- **Also changed:**
  - The ACG UC summary's "higher infection risk" statement was not found in the full text and is removed.
  - The recommended route for gaps closed by a running study now gives both the registry primary completion and the expected topline. For CHARGE: primary completion Nov 2028 (estimated), topline about Feb 2029, study completion Dec 2030.

## Two versions: full and simplified (30 Sep 2026)

- **Full:** `dashboard/index.html` (standalone: `dist/IBD-Evidence-Dashboard.html`), with all 14 pages.
- **Simplified:** `dashboard/simple.html` (standalone: `dist/IBD-Evidence-Dashboard-Simple.html`).
  - **Six sections with tabs:** Overview, Evidence plan, Studies, Competition & guidelines, Communication, Admin.
  - **Overview:** a "Start here" card with five questions that link to their answers; the briefing shows its top 3 points and the actions list its top 5.
  - **Every page:** starts with an "In short" summary computed from the data, with detail cards folded under "More on this page".
  - **Names instead of codes:** gap, imperative, event and trial codes become names; the code shows on hover.
  - **Tester view switch:** provenance labels, ⓘ buttons and value marks appear only when it is on.
  - **AI assistants:** has its own tab.
- **Same code and data:** both versions use one source. `scripts/build_simple.py` writes `simple.html` from `index.html` by setting `window.IBD_SIMPLE = true`. `build_standalone.py` runs it and writes both standalone files.
- **Switching:** each version's sidebar links to the other and keeps the current page.
- **Where to change the simplified version:**
  - page summaries: `SX_SUMMARY`
  - cards shown before the fold: `SX_KEEP`
  - sections and tab names: `SECTIONS` and `TAB_LABEL`
