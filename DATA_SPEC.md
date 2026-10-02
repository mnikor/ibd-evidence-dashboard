# IBD Evidence Intelligence Dashboard: Data Specification

**Scope:** J&J Innovative Medicine, IBD (UC and Crohn's disease)
**Brands:** TREMFYA® (guselkumab, anti-IL-23p19 mAb) · Icotrokinra (JNJ-2113, oral targeted IL-23 receptor antagonist peptide)
**Status:** Prototype data model v0.1. Nothing is built yet.
**Data policy for the prototype:** every record carries `data_origin` = `public` | `simulated` | `internal`. The prototype uses public and simulated data only. Anything marked *(verify)* comes from public knowledge and has to be checked against the primary source before anyone relies on it.

---

## 0. How to read this document

| Section | What it defines |
|---|---|
| 1 | Who uses the dashboard and which decisions it supports |
| 2 | Dashboard views, with the questions each view answers |
| 3 | The core data model: every entity and every field |
| 4 | Derived metrics and scoring formulas |
| 5 | The AI layer: insight types, inference logic, guardrails, **decision engines and recommendations** |
| 6 | Simulated seed content (imperatives, gaps, studies, competitors) |
| 7 | Data sources and refresh cadence |
| 8 | Governance and compliance |
| 9 | Open questions to settle before build |

The dashboard runs on one chain of logic, and every view is a slice of it:

```
Strategic Imperative → Key Question → Evidence Gap → Study → Evidence Output → Dissemination Tactic → Stakeholder Impact
                                            ↑                                                              ↑
                         Competitor Evidence / Readout ──── Competitive Impact on J&J ───────────────────────┘
```

---

## 1. Users and decisions

| Persona | Strategic questions | Tactical questions |
|---|---|---|
| **Medical Affairs leadership (Global/Regional)** | Are we generating the right evidence to win each imperative? Where are we exposed? | Which gaps have no study against them? Which readouts are at risk? |
| **Evidence Generation / Clinical Development leads** | Is the portfolio balanced across gaps, geographies and the care continuum? | Which study milestones are slipping? Where should the next investigator-initiated study (IIS) or RWE study go? |
| **HEOR / Market Access** | Will the evidence satisfy HTA and payer requirements in time for launch or reassessment? | Which markets are missing local data or comparative-effectiveness data? |
| **Publications and Scientific Communications** | Is the dissemination plan sequenced to beat or answer competitor data? | What is going to which congress or journal, and when? Where are the gaps in the pipeline? |
| **MSL / Field Medical leads** | What story will HCPs hear from competitors over the next 12 months? | What reactive scientific-exchange material is needed, and what field insights back up the gaps? |
| **Competitive Intelligence** | What is each competitor's likely strategy, and what threatens our positioning? | Which readouts are coming up, and what is our response plan? |
| **Brand / Commercial (behind a firewall, see §8)** | Which evidence will change the label, guidelines or share? | Timing of label-enabling evidence relative to competitor launches. |

---

## 2. Dashboard views (to build later)

| # | View | Key questions | Main visuals | AI insight panel |
|---|---|---|---|---|
| V1 | **Executive Cockpit** | Where are we winning or losing, and what changed this week? | KPI tiles (Evidence Readiness Index, Gap Coverage %, Competitive Threat Index, readouts in the next 6 months); "What changed" feed | Executive brief with the top 3 risks and top 3 opportunities |
| V2 | **Strategic Imperatives** | How ready is our evidence for each imperative, by brand and indication? | Imperative × readiness bars; imperative → gap → study tree | Why each imperative is on or off track |
| V3 | **Evidence Gap Map** | Which gaps are critical, which are covered, and which are orphaned? | Heatmap of gap × stakeholder; criticality vs coverage bubble chart (bubble size = time to close) | Gap prioritisation rationale; suggested studies for orphan gaps |
| V4 | **Study Portfolio and Timeline** | Which studies close which gaps, when, and with what expected impact? | Gantt with milestones (CON → FPI → LPI → PCD → DBL → topline → publication, baseline vs forecast); enrollment curves actual vs plan; sites/patients by country; study "fact sheet" drawer (design, arms, N, endpoints, baseline, results, safety); Sankey of gap → study → output; impact vs probability-of-success scatter | Slippage alerts; "if this study fails, which gaps reopen?" |
| V5 | **Geographic Footprint** (patient-segment coverage moved to Strategy & Gaps, Sep 2026) | Where is the evidence geographically, and where in the patient journey? | World map (sites, patients, markets covered); care-continuum swimlane (disease stage × line of therapy × segment) | White-space analysis: segments or regions with no evidence |
| V6 | **Dissemination Plan** | Is the evidence reaching the right audiences, at the right venues, in the right order? | Congress/journal calendar; publication pipeline funnel; audience × channel matrix; share of voice | Sequencing advice; congresses where competitors will dominate |
| V7 | **Competitive Landscape** | Who is where, and when does their data land? | Pipeline chart (MoA × phase × indication); readout calendar interleaved with J&J milestones; label-feature comparison grid | Landscape narrative; class-level trends |
| V8 | **Competitor Deep-Dive** | What are this competitor's gaps, strategy and next moves? | Evidence profile radar vs TREMFYA/icotrokinra; gap list; inferred-strategy card with evidence chain | AI-inferred strategy with confidence score and cited signals |
| V9 | **Impact and Scenarios** | How would a competitor readout or a J&J readout shift our position? | Scenario board (bull, base, bear); tornado chart of impact drivers; before/after positioning map | War-game narrative and recommended pre-emptive actions |
| V10 | **Signals and Insight Feed** | What is new across trials, congresses, regulators, HTA bodies, guidelines and the field? | Filterable signal stream; signal volume trend | Signal triage: materiality score and suggested owner |
| V11 | **Data Provenance** | How fresh is the data, and can we trust it? | Source freshness table; origin mix (public/simulated/internal) | None |
| V12 | **Investment and Funding** | How much are we spending, who pays, and is it well allocated? | Total cost by funder (Global/US/EMEA MAF…) stacked by brand and evidence class; co-funding matrix study × funder; cost-per-impact ranking; pay-vs-benefit map; budget burn by fiscal year | Misallocation and overrun alerts; co-funding negotiation brief |
| V13 | **Dissemination Quality** | What kind of evidence are we putting out, and is it reaching peer review? | Matrix of analysis type × publication type; publication ladder per study (steps done/due/overdue); evidence-debt list; dark-period timeline vs competitors; J&J vs competitor analysis-type mix | "We're publishing post-hoc posters while competitors present primary orals"-type diagnosis |
| V14 | **Decision Room** | What should we decide this week or this quarter? | Recommendation queue (strategic / tactical tabs) with expected effect, cost and deadline; efficient-frontier chart (E1); scenario comparison; decision log | Each recommendation's rationale, with its evidence chain |

**Global filters on every view:** Brand · Indication (UC/CD/both) · **Evidence class (Interventional / RWE / Synthesis)** · Study type · **Funder (Global / US / EMEA MAF…)** · Analysis type · Publication type · Region/Country · Care-continuum segment · Stakeholder · Time window · Data origin · Confidence threshold.

---

## 3. Core data model

Field types: `str`, `text` (long), `int`, `float`, `bool`, `date`, `enum`, `fk` (foreign key), `list<>`, `json`.
Every entity also carries these **standard audit fields**: `created_at`, `updated_at`, `owner`, `data_origin` (public/simulated/internal), `source_ids` (list<fk Source>), `confidence` (0–1), `version`.

### 3.1 Reference entities

#### `Brand`
| Field | Type | Example | Notes |
|---|---|---|---|
| brand_id | str | `TRE` | |
| brand_name | str | TREMFYA | |
| inn | str | guselkumab | |
| company | str | Johnson & Johnson | |
| is_jnj | bool | true | Separates own assets from competitors |
| moa | fk MoA | IL-23p19 | |
| modality | enum | mAb / peptide / small molecule / bispecific / cell | |
| route | list<enum> | IV induction, SC induction, SC maintenance, oral | |
| dosing_summary | text | IV 200 mg q4w ×3 → SC 100 mg q8w / 200 mg q4w *(verify)* | |
| lifecycle_stage | enum | pipeline / launch / growth / mature / LOE | |
| indications_approved | list<fk Indication×Region> | UC US 2024, CD US 2025 *(verify)* | |
| indications_in_development | list | | |
| loe_dates | json | {US: …, EU: …} | Protects against biosimilar timing assumptions |

#### `MoA` (mechanism of action)
`moa_id, name (IL-23p19, IL-12/23p40, IL-23R oral, TL1A, α4β7, JAK1, S1P, miR-124, TNF, combination), pathway, class_first_in_class_date, class_safety_notes`.

#### `Indication`
`indication_id, name (UC, CD, perianal fistulizing CD, pouchitis, pediatric UC/CD, IBD-unclassified), icd10, prevalence_by_region (json), incidence_trend`.

#### `Geography`
| Field | Type | Notes |
|---|---|---|
| geo_id | str | ISO-3 or region code |
| level | enum | global / region / cluster / country |
| parent_geo_id | fk | EMEA → Germany |
| market_priority_tier | enum | T1/T2/T3 (simulated) |
| hta_body | str | NICE, G-BA/IQWiG, HAS, AIFA, CADTH, PBAC… |
| payer_archetype | enum | HTA-driven / budget-driven / free-pricing |
| ibd_prevalence | int | |
| biologic_penetration_pct | float | |
| key_access_hurdle | text | e.g. step-through-TNF requirement |

#### `CareContinuumSegment` (the "TCC" axis, assumed; see §9)
The patient-journey coordinates that studies, gaps and competitors are positioned on.
| Field | Type | Values |
|---|---|---|
| segment_id | str | |
| disease | enum | UC / CD |
| severity | enum | mild / moderate / severe / fulminant (ASUC) |
| line_of_therapy | enum | 1L advanced (biologic/ATT-naïve), 2L (1 prior advanced), 3L+ (multi-refractory) |
| prior_exposure | enum | bio-naïve / TNF-IR / multi-class-IR / JAK-IR |
| treatment_phase | enum | induction / maintenance / re-induction / dose escalation / de-escalation / switch |
| special_population | enum | pediatric, elderly, pregnancy, perianal fistula, extra-intestinal manifestations, post-surgical, EIM/psoriasis overlap |
| disease_extent | enum | UC: proctitis / left-sided / extensive; CD: ileal / colonic / ileocolonic / stricturing / penetrating |
| journey_stage | enum | diagnosis → first advanced therapy → optimisation → switch → surgery-avoidance → long-term remission |
| patient_share_pct | float | Share of advanced-therapy patients in the segment (by geo) |

#### `Stakeholder`
`stakeholder_id, type (gastroenterologist-academic, gastroenterologist-community, IBD nurse, colorectal surgeon, pharmacist, payer/HTA, guideline committee, regulator, patient/advocacy, PCP), geo_id, influence_weight (1–5), evidence_preferences (list: RCT, H2H, RWE, PROs, endoscopy, histology, cost-effectiveness)`.
Aggregate archetypes only. No named individuals (§8).

#### `Source`
`source_id, type (clinicaltrials.gov, EU CTR, PubMed, congress abstract, press release, earnings call, SEC 10-K/10-Q, FDA/EMA doc, HTA report, guideline, social/news, MSL insight, internal plan, simulated), url, title, publisher, publish_date, retrieved_at, reliability_grade (A–D), excerpt`.

---

### 3.2 Strategy layer

#### `StrategicImperative`
| Field | Type | Example |
|---|---|---|
| imperative_id | str | `SI-TRE-01` |
| brand_id | fk | TRE |
| indication_scope | list | UC, CD |
| title | str | "Establish TREMFYA as the IL-23 of choice in bio-naïve UC and CD" |
| description | text | |
| theme | enum | differentiation / expand population / convenience / durability / access / safety / lifecycle / launch readiness |
| time_horizon | enum | 0–12m / 1–3y / 3–5y |
| priority_rank | int | 1–n |
| target_stakeholders | list<fk Stakeholder> | |
| success_metrics | list<json> | {metric: "guideline preferred-agent status in ECCO UC", target: "by 2027"} |
| key_questions | list<fk KeyQuestion> | |
| linked_regions | list<fk Geography> | |
| evidence_readiness_index | float (derived) | §4.1 |
| status_rag | enum (derived + override) | green/amber/red |
| ai_status_narrative | fk AIInsight | |

#### `KeyQuestion` (strategic question the evidence must answer)
`kq_id, imperative_id, question ("Does guselkumab deliver transmural healing that exceeds ustekinumab?"), stakeholder_ids, decision_it_informs (label, guideline, formulary, prescribing), required_evidence_type (list), required_by_date`.

#### `EvidenceGap`
| Field | Type | Notes |
|---|---|---|
| gap_id | str | `GAP-017` |
| kq_ids | list<fk> | Links back to imperatives |
| brand_id | fk | |
| title | str | "No head-to-head data vs risankizumab in CD" |
| gap_type | enum | efficacy / comparative (H2H/ITC) / population / endpoint (histologic, transmural, PRO, fatigue) / durability / safety / dosing & convenience / RWE / HEOR & economic / mechanistic / biomarker & precision / pediatric / sequencing & positioning / combination |
| care_segment_ids | list<fk CareContinuumSegment> | Where in the patient journey |
| geo_ids | list<fk Geography> | Where the gap bites (e.g. local HTA needs) |
| stakeholder_ids | list<fk Stakeholder> | Who feels the gap |
| identified_from | list<enum> | advisory board, MSL insights, HTA feedback, guideline review, competitor comparison, literature review, AI scan |
| identified_date | date | |
| competitor_has_evidence | bool | Parity risk |
| competitor_evidence_refs | list<fk CompetitorStudy> | |
| stakeholder_importance | int 1–5 | |
| imperative_alignment | int 1–5 | |
| uncertainty_magnitude | int 1–5 | How little we currently know |
| hta_guideline_relevance | int 1–5 | |
| urgency | int 1–5 | Driven by competitor timing |
| gap_criticality_score | float (derived) | §4.2 |
| closing_study_ids | list<fk Study> | |
| gap_coverage_pct | float (derived) | §4.3 |
| expected_close_date | date (derived) | Earliest credible output date |
| status | enum | open-orphan / open-planned / in progress / partially closed / closed / deprioritised |
| residual_risk | text | What stays open even if the studies succeed |
| ai_recommendation | fk AIInsight | |

---

### 3.3 Evidence generation layer

#### `Study`
| Field | Type | Notes |
|---|---|---|
| study_id | str | Internal ID |
| nct_id / eu_ct_id | str | Public registry IDs |
| acronym | str | GALAXI, QUASAR, ASTRO, GRAVITI, DUET-UC… |
| brand_ids | list<fk> | Combination studies link to more than one brand |
| **evidence_class** | enum | **Interventional** / **Non-interventional (RWE)** / **Evidence synthesis & modelling**. This is the top-level filter on every view. |
| study_type | enum (depends on class) | **Interventional:** Ph1 / Ph2a / Ph2b / Ph2b/3 / Ph3 / Ph3b / Ph4 / LTE / pragmatic RCT / mechanistic / pediatric (PIP/PREA). **Non-interventional (RWE):** prospective observational cohort / retrospective database (claims, EHR) / registry / chart review / cross-sectional survey / PRO or patient-preference (DCE) / PASS / external control arm. **Synthesis & modelling:** SLR / ITC / NMA / MAIC / cost-effectiveness / budget impact / burden of illness. |
| sponsorship_model | enum | J&J-sponsored / J&J-sponsored with CRO / collaborative (academic partner) / IIS (J&J-supported) / consortium-registry participation / data-partner license |
| regulatory_intent | enum | registrational (label-enabling) / label-supportive / post-marketing commitment / medical (non-registrational) / HTA-supportive |
| indication_id | fk | |
| design | enum | placebo-controlled RCT / active-comparator H2H / single-arm / treat-through / randomized withdrawal / observational cohort / case-control / cross-sectional |
| comparator | str | placebo, ustekinumab, risankizumab, vedolizumab… |
| population_description | text | |
| care_segment_ids | list<fk> | Positioning on the care continuum |
| n_planned / n_enrolled | int | |
| enrollment_pct | float (derived) | |
| countries | list<fk Geography> | |
| sites_by_country | json | {USA: 120, DEU: 18…} for the world map |
| primary_endpoint | text | e.g. clinical remission (mMS) at wk 12 |
| key_secondary_endpoints | list<str> | endoscopic response, histo-endoscopic mucosal improvement, transmural healing, PROs, fatigue |
| endpoint_categories | list<enum> | clinical / endoscopic / histologic / transmural / biomarker / PRO / QoL / HCRU / safety / PK |
| gap_ids_addressed | list<fk EvidenceGap> | |
| gap_fit_score | json | {GAP-017: 0.8} — how completely the study closes each gap (0–1) |
| status | enum | planned / feasibility / start-up / recruiting / active not recruiting / completed / reported / terminated / on hold |
| milestones | list<fk StudyMilestone> | |
| probability_of_technical_success | float | 0–1, simulated or benchmark |
| expected_impact_if_positive | int 1–5 | per affected imperative |
| impact_dimensions | list<enum> | label change / guideline inclusion / HTA / formulary / clinical practice / publication-only |
| study_impact_score | float (derived) | §4.4 |
| competitive_timing_flag | enum (derived) | reads out before / near / after the matching competitor readout |
| lead_funder | enum (derived) | The funder with the largest share in `StudyFunding` |
| total_cost_usd | float (derived) | Sum of `StudyFunding.committed_usd` (see below). Internal; simulated in the prototype. |
| funding_split | json (derived) | {Global MAF: 60%, EMEA MAF: 25%, US MAF: 15%} for the stacked bars |
| risk_flags | list<enum> | enrollment, site activation, regulatory, protocol amendment, competitive-recruitment conflict |
| data_origin | enum | public (registry) / simulated |

#### `StudyMilestone`
One row per milestone per study. Each milestone keeps **baseline**, **forecast** and **actual** dates so slippage can be tracked.
| Field | Type | Notes |
|---|---|---|
| milestone_id | str | |
| study_id | fk | |
| type | enum | see the milestone list below |
| baseline_date | date | Date in the original approved plan (frozen) |
| planned_date | date | Current approved plan |
| forecast_date | date | Latest operational forecast (can be AI-projected from enrollment rate) |
| actual_date | date | Filled in when achieved |
| slippage_days | int (derived) | forecast_or_actual − baseline |
| date_source | enum | internal plan / registry / company guidance / AI-projected |
| confidence | float 0–1 | |
| is_critical_path | bool | Drives the label, a guideline or a competitive-timing claim |

**Standard milestone list, in order:**
| Code | Milestone |
|---|---|
| CON | Concept / study approval (governance) |
| PFA | Protocol final approved |
| REG | Registry posting (NCT / EU CT) |
| IRB1 | First IRB/EC approval |
| SIV1 | First site initiated (activated) |
| **FPI** | **First Patient In (first screened / first randomized; store both as FPS and FPR)** |
| 25/50/75E | 25% / 50% / 75% enrolled |
| **LPI** | **Last Patient In (last randomized)** |
| LPI-MA | Last patient enters maintenance (for induction → maintenance designs) |
| PCD | Primary completion date (last patient's primary-endpoint visit) |
| **LPO** | **Last Patient Out (last visit)** |
| DBL | Database lock (primary; plus interim/maintenance DBLs as separate rows) |
| TLR | Topline results (internal) |
| TLPR | Topline press release (public) |
| CSR | Clinical study report final |
| SUB | Regulatory submission (per agency) |
| APP | Approval / label update (per agency) |
| ABS1 | First abstract / congress presentation |
| MS1 | Primary manuscript published |
| RRP | Results posted on registry |
| LTE-END | Long-term extension end |

#### `StudyDesignDetail` (1:1 with Study)
| Field | Type | Example |
|---|---|---|
| phase | enum | 1 / 2a / 2b / 2b/3 / 3 / 3b / 4 |
| randomization_ratio | str | 1:1:1 |
| blinding | enum | open-label / single / double / double-dummy |
| arms | list<json> | [{arm: "GUS 200 mg IV q4w", n_planned: 200, dose, route, frequency}, {arm: "Placebo", …}] |
| n_arms | int (derived) | |
| induction_duration_wks / maintenance_duration_wks / total_duration_wks | int | 12 / 44 / 56 |
| treat_through vs re-randomized_withdrawal | enum | |
| rescue_allowed | bool | |
| stratification_factors | list<str> | prior advanced-therapy failure, baseline mMS, region |
| key_inclusion | list<str> | mMS 5–9, ES ≥ 2 |
| key_exclusion | list<str> | |
| primary_endpoint + timepoint | str | clinical remission (mMS) at wk 12 |
| secondary_endpoints | list<json> | [{endpoint, timepoint, category, multiplicity_rank}] |
| exploratory_endpoints | list<str> | biomarkers, IUS, fatigue |
| powering_assumption | text | delta, power, alpha |
| interim_analyses | list<json> | [{type: futility, planned_date}] |
| has_lte | bool | + lte_duration_wks |
| protocol_version / n_amendments | str / int | v4.0 / 3 |
| last_amendment_date + reason | date / text | |

#### `StudyEnrollment` (time series, one row per study × month × country)
| Field | Type | Notes |
|---|---|---|
| study_id, period (month), geo_id | fk, date, fk | |
| sites_planned / sites_activated / sites_enrolling | int | Site activation curve |
| patients_screened | int | Cumulative |
| patients_screen_failed | int | → screen failure rate |
| patients_randomized | int | Cumulative (the enrollment curve) |
| patients_planned_cumulative | int | Planned curve, for actual-vs-plan |
| patients_active / completed / discontinued | int | |
| discontinuation_reasons | json | {AE: 12, lack of efficacy: 20, withdrawal: 8} |
| enrollment_rate_pspm | float (derived) | patients per site per month |

#### `StudyCountrySite` (world map; one row per study × country)
`study_id, geo_id, n_sites_planned, n_sites_active, n_patients_planned, n_patients_randomized, first_site_activation_date, country_fpi_date, country_lpi_date, regulatory_approval_date, is_hta_relevant_market (bool)`.
Individual site names and investigator names are **not stored** in the dashboard. Counts only.

#### `StudyBaseline` (baseline characteristics, population actually enrolled)
`study_id, arm, n, mean_age, pct_female, mean_disease_duration_yrs, pct_severe (e.g. mMS 7–9 / CDAI > 330), mean_ses_cd_or_mayo_es, pct_bio_naive, pct_prior_tnf_failure, pct_prior_vedo_failure, pct_prior_jak_failure, pct_prior_ustekinumab_failure, pct_multi_class_failure (≥ 2 classes), pct_concomitant_steroids, pct_concomitant_immunomodulators, disease_location_mix (json), pct_perianal, region_mix (json)`.
Used to compare study populations vs competitor studies ("was their population easier?").

#### `StudyResult` (one row per study × endpoint × arm × timepoint × subgroup)
| Field | Type | Example |
|---|---|---|
| study_id, endpoint, timepoint_wk, arm, subgroup | | clinical remission, 12, GUS 200 IV, bio-naïve |
| population_set | enum | ITT / mITT / PP / responders (maintenance) |
| n | int | |
| responders_n / rate_pct | int / float | 22.6% |
| comparator_rate_pct | float | 7.9% |
| delta_pct (placebo-adjusted) | float | 14.7 |
| ci_low / ci_high | float | |
| p_value | float | |
| hr_or_or | float | For time-to-event / odds |
| multiplicity_controlled | bool | |
| is_primary | bool | |
| result_status | enum | topline / final / post-hoc |
| source_output_id | fk EvidenceOutput | Which abstract or paper reported it |

This enables a **cross-trial benchmarking view** (with a mandatory "cross-trial comparison, not head-to-head" caveat).

#### `StudySafety` (per study × arm)
`study_id, arm, exposure_patient_years, pct_any_ae, pct_sae, pct_ae_discontinuation, serious_infections_per_100py, malignancy_per_100py, mace_per_100py, vte_per_100py, deaths, injection_site_reaction_pct, hepatic_events_pct, aesi (json)`.

#### `StudyOperations` (internal; simulated in the prototype)
`study_id, executing_function (Clinical Development / GMA / RWE / HEOR), cro, study_lead (role, not a name), spend_to_date_usd, cost_per_patient_usd (derived: total_cost / n), enrollment_risk (RAG), competitive_recruitment_overlap (list<CompetitorStudy> competing for the same patients in the same countries), key_risks (list), mitigation_actions (list), last_status_update (date)`.

#### `Funder` (reference)
`funder_id, name, level (global / regional / local), region_geo_id, function`.
Seed values: **Global MAF** (Global Medical Affairs), **US MAF**, **EMEA MAF**, **APAC MAF**, **LATAM MAF**, **Japan MAF**, **Canada MAF**, **Global R&D / Clinical Development**, **Global HEOR / Market Access**, **Local operating company** (country affiliate), **External co-funder** (academic grant, consortium, partner such as Protagonist for icotrokinra).

#### `StudyFunding` (one row per study × funder)
| Field | Type | Notes |
|---|---|---|
| study_id / funder_id | fk | |
| funding_role | enum | lead funder / co-funder / in-kind (drug supply, data access) |
| share_pct | float | Co-funding share; must total 100% per study (validation rule) |
| committed_usd | float | Share of total study cost |
| approved_usd / spent_to_date_usd / forecast_at_completion_usd | float | Budget tracking |
| approval_status | enum | proposed / in governance / approved / on hold / cut |
| approval_date / governance_body | date / str | e.g. Global Evidence Council, EMEA Evidence Committee |
| funding_rationale | text | Why this funder pays (e.g. EMEA needs the data for G-BA reassessment) |
| benefiting_geo_ids | list<fk> | Markets that use the evidence (compared with who pays; §4.11) |
| fiscal_year_split | json | {2026: 1.2M, 2027: 2.0M, 2028: 0.8M} (cost phasing) |

#### `RWEStudyDetail` (1:1 with Study when `evidence_class` = Non-interventional)
| Field | Type | Example |
|---|---|---|
| data_source_type | enum | claims / EHR / disease registry / prospective cohort / chart review / survey / linked claims-EHR |
| data_source_names | list<str> | Optum, IQVIA PharMetrics, Flatiron-type EHR, national IBD registries |
| data_partner / license_cost_usd | str / float | |
| geo_ids | list<fk> | Countries covered |
| study_period / lookback / follow-up | date range / months / months | |
| index_event | str | first guselkumab claim |
| cohort_definition | text | adults with UC, ≥ 1 prior advanced therapy |
| n_expected / n_final | int | Patients in the cohort |
| comparator_cohorts | list<str> | risankizumab, ustekinumab biosimilar |
| analytic_method | list<enum> | descriptive / PSM / IPTW / regression / target-trial emulation / survival / MAIC |
| outcomes | list<str> | persistence, dose escalation, steroid-free remission, HCRU, costs |
| protocol_registration | str | EU PAS / RWE Registry ID (transparency) |
| data_cut_dates | list<date> | Planned and actual data cuts, each able to feed a separate output |
| regulatory_grade | bool | Designed to FDA/EMA RWE guidance standards |

Interventional studies use `StudyDesignDetail`, `StudyEnrollment`, `StudyBaseline` and `StudySafety`. RWE studies use `RWEStudyDetail`, and their milestones use RWE codes: protocol final → data access → data cut → analysis complete → report. Views switch the fact sheet and Gantt by `evidence_class`.

`CompetitorStudy` uses the same sub-entities, filled only with public data (registry: N, arms, countries, start date, primary completion date, status; results from abstracts and papers). Internal-only fields (`StudyOperations`, `StudyEnrollment` beyond registry updates) stay empty for competitors.

#### `EvidenceOutput` (each publication or communication of data)
Each output is classified on three independent axes: **what analysis**, **what publication type**, and **what peer-review level**. Keeping them separate lets the dashboard answer questions such as "how many primary analyses are still only posters?".

| Field | Type | Notes |
|---|---|---|
| output_id | str | |
| study_id | fk | |
| analysis_type | enum | **Trial in progress (TiP) / design & rationale** · **Baseline characteristics** · **Interim analysis** · **Primary analysis** · **Secondary analysis** (pre-specified secondary endpoints) · **Subgroup analysis** (pre-specified) · **Post-hoc analysis** · **Pooled / integrated analysis** (e.g. across GALAXI 2+3) · **Long-term extension** · **Exploratory / biomarker / mechanistic** · **Safety update** · **RWE data cut** (1st, 2nd…) · **HEOR / economic** · **ITC / NMA** · **Methodology** |
| analysis_prespecified | bool | Pre-specified vs post-hoc (drives evidence weight) |
| data_cut_date | date | Which data the output reports |
| data_maturity | enum | topline / interim / final / updated |
| publication_type | enum | **Congress:** abstract only (published in supplement) · oral presentation · late-breaking oral · plenary · poster · poster of distinction / poster tour · e-poster · industry symposium · **Journal:** primary manuscript · secondary manuscript · short communication / research letter · review / consensus · supplement article · correspondence · **Other:** preprint · encore · press release (topline) · plain-language summary · visual abstract · video abstract · podcast · infographic · slide deck (scientific exchange) · HTA dossier · value dossier · label / SmPC update |
| is_encore | bool + fk original_output_id | Tracks re-use at regional congresses |
| peer_review_status | enum | not peer-reviewed / peer-reviewed abstract / peer-reviewed journal |
| open_access | bool | |
| title | str | |
| key_message_ids | list<fk KeyMessage> | Approved scientific statements |
| gap_ids_closed | list<fk> | |
| gap_closure_weight | float 0–1 (derived) | How much this output counts toward closing a gap: peer-reviewed primary manuscript = 1.0, primary oral = 0.6, poster = 0.4, post-hoc poster = 0.2, TiP = 0 (configurable) |
| target_venue_id | fk Venue | |
| alternate_venue_ids | list<fk> | Fallback if rejected |
| planned_submission / submission / acceptance / presentation / publication dates | date | Plus planned vs actual |
| status | enum | concept / planned / in development / author review / MLR / submitted / accepted / presented / published / rejected / withdrawn |
| rejection_count | int | |
| lead_function / funder_id | enum / fk | Who owns and pays for it (Global vs regional pubs) |
| authorship_model | enum | investigator-led / J&J-led / collaborative (roles only, no names) |
| journal_impact_factor / journal_tier | float / enum | |
| altmetric_score / citations / downloads | float / int / int | Post-publication impact |
| audience_ids | list<fk Stakeholder> | |
| geo_ids | list<fk> | Regional encores |
| transparency_deadline | date (derived) | e.g. results within 12 months of PCD, per company disclosure policy |

#### `KeyMessage` (scientific narrative)
`msg_id, brand_id, pillar (efficacy / durability / speed of onset / deep healing / safety / convenience / value), statement, substantiating_output_ids, approval_status (MLR), valid_geos, expiry_date`.

---

### 3.4 Dissemination layer

#### `Venue`
`venue_id, name (DDW, ECCO, UEGW, ACG, AGA, APDW, Advances in IBD, JPGN/NASPGHAN, ISPOR, journals: Lancet, Gastroenterology, JCC, Gut, AJG, CGH, APT), type (congress/journal/symposium/digital), region, dates, abstract_deadline, late_breaker_deadline, audience_size, audience_mix, tier (1–3)`.

#### `DisseminationTactic`
| Field | Type | Notes |
|---|---|---|
| tactic_id | str | |
| output_ids | list<fk> | What is being communicated |
| channel | enum | congress presentation / symposium / publication / MSL scientific exchange / advisory board / med-ed (CME) / webinar / medical website / podcast / social (medical) / HTA submission / payer dossier / guideline submission / patient-org briefing |
| audience_ids | list<fk Stakeholder> | |
| geo_ids | list<fk> | |
| planned_date / actual_date | date | |
| wave | enum | pre-readout / readout / post-readout amplification / sustain |
| competitive_context | text | e.g. "Same congress as competitor X H2H data" |
| reach_target / reach_actual | int | HCPs reached |
| engagement_metrics | json | downloads, attendance, MSL interactions, time on page |
| message_recall_pct | float | From surveys (simulated) |
| owner_function | enum | Pubs / Medical Education / Field Medical / HEOR / Brand (firewalled) |
| status | enum | |

#### `ShareOfVoice` (time series)
`sov_id, period, venue_id or channel, brand_id, analysis_type, publication_type, n_abstracts, n_orals, n_late_breakers, n_posters, n_symposia, n_publications, social_mentions, sentiment_score (-1…1)`.
Tracked for competitors too, so the dashboard can compare *what kind* of data each company brings (e.g. competitor: 4 orals of primary data; J&J: 9 posters, mostly post-hoc).

#### `PublicationLadderTemplate` (the expected dissemination sequence per study type)
The reference "ideal" sequence that each study's actual outputs are checked against.
`template_id, applies_to (evidence_class + study_type), steps (ordered list<json>: {analysis_type, publication_type, trigger_milestone, target_offset_months, venue_tier, mandatory})`.

Example for a registrational Ph3:
| Step | Analysis | Publication type | Trigger | Target timing |
|---|---|---|---|---|
| 1 | Trial in progress | Poster | FPI | FPI + 6–12 m |
| 2 | Baseline characteristics | Poster | LPI | LPI + 3–6 m |
| 3 | Primary analysis | Topline PR → late-breaking oral | Topline | Next tier-1 congress |
| 4 | Primary analysis | Primary manuscript (tier-1 journal) | Topline | ≤ 12 m |
| 5 | Secondary / subgroup | Orals & posters | Primary presented | +3–9 m |
| 6 | Secondary / subgroup | Secondary manuscripts | | +12–18 m |
| 7 | Regional encores | Posters | Primary presented | EMEA/APAC/LATAM congresses |
| 8 | Post-hoc / pooled | Posters → manuscripts | Gap-driven | as needed |
| 9 | Long-term extension | Oral / manuscript | Each LTE data cut | yearly |

Example for RWE: protocol/design poster → first data cut (poster) → primary RWE manuscript → subsequent data cuts / country analyses.

**Validation rules** the dashboard enforces and flags:
- A post-hoc or secondary analysis cannot be published before the primary analysis is public.
- An encore needs a published original.
- A primary result with no manuscript 12 months after topline is flagged as a **transparency and credibility risk**.
- A study with no output for more than 9 months while a competitor presents on the same gap is flagged as a **"dark period"**.

---

### 3.5 Competitive layer

#### `CompetitorAsset` (extends `Brand` with `is_jnj=false`)
Additional fields:
| Field | Type | Notes |
|---|---|---|
| company | str | AbbVie, Lilly, Takeda, Pfizer, BMS, Merck, Roche, Sanofi/Teva, Abivax… |
| development_phase_by_indication | json | {UC: approved, CD: Ph3} |
| approval_dates_by_geo | json | |
| label_features | json | induction route, maintenance interval, H2H claims, endoscopic claims, boxed warnings |
| commercial_strength | int 1–5 | Field force, portfolio breadth, contracting power |
| pricing_access_position | text | |
| peak_sales_consensus_usd | float | Public analyst consensus (simulated in prototype) |
| current_share_by_segment | json | {UC-bio-naïve-US: 0.18} |
| evidence_profile | json | Scores 1–5 per dimension, for the radar chart (§4.7) |

#### `CompetitorStudy`
Same schema as `Study` plus:
`expected_readout_date, readout_confidence (based on registry primary completion plus company guidance), expected_venue, threat_to_jnj_gap_ids (list), comparator_is_jnj_asset (bool, e.g. H2H vs ustekinumab or guselkumab)`.

#### `CompetitorGap`
`cgap_id, asset_id, gap_type (same taxonomy as EvidenceGap), description, care_segment_ids, severity (1–5), jnj_can_exploit (bool), jnj_evidence_refs (studies or outputs that already cover it), exploitation_window (date range before the competitor closes it), competitor_closing_study_id (if any)`.

#### `CompetitorStrategy` (AI-inferred)
| Field | Type | Notes |
|---|---|---|
| strategy_id | str | |
| asset_id / company | fk | |
| inferred_strategy_statement | text | "Positioning risankizumab as the IL-23 efficacy leader via H2H vs ustekinumab; pushing into 1L CD" |
| strategic_pillars | list<enum> | H2H superiority / convenience / speed / breadth of label / oral switch / combination / price / portfolio bundling |
| target_segments | list<fk CareContinuumSegment> | |
| target_geos | list<fk> | |
| evidence_chain | list<json> | [{signal_id, observation, inference}] — required, every claim traceable |
| confidence | float 0–1 | |
| alternative_hypotheses | list<text> | Guards against anchoring |
| leading_indicators_to_watch | list<text> | Signals that would confirm or refute the inference |
| last_reassessed | date | |
| human_validated | bool | CI analyst sign-off |

#### `CompetitiveEvent` (calendar)
`event_id, asset_id, type (topline readout, congress presentation, filing, approval, label expansion, guideline update, HTA decision, price change, biosimilar entry, M&A/licensing, trial termination), expected_date, date_certainty (confirmed / guided / estimated / AI-predicted), probability_of_positive_outcome, description`.

#### `CompetitiveImpactAssessment`
| Field | Type | Notes |
|---|---|---|
| impact_id | str | |
| event_id | fk CompetitiveEvent | |
| jnj_brand_id | fk | |
| affected_imperative_ids | list<fk> | |
| affected_gap_ids | list<fk> | Gaps that become more urgent |
| affected_segments | list<fk> | |
| affected_geos | list<fk> | |
| impact_direction | enum | negative / neutral / positive (e.g. class validation) |
| impact_magnitude | int 1–5 | |
| impact_mechanism | enum | label parity lost / differentiation eroded / guideline repositioning / payer step-edit / HCP perception / new class entrant / price pressure |
| time_to_impact_months | int | |
| competitive_threat_index | float (derived) | §4.6 |
| jnj_response_options | list<text> | Evidence, dissemination and access responses |
| preparedness_status | enum | ready / in progress / not started |
| ai_narrative | fk AIInsight | |

#### `Scenario`
`scenario_id, name, type (bull/base/bear/custom), assumptions (json: {event_id: outcome, date_shift_months}), outputs (json: ERI per imperative, threat index, positioning shift per segment), created_by, ai_commentary`.

---

### 3.6 External environment and signals

#### `Guideline`
`guideline_id, body (ACG, AGA, ECCO, BSG, JSGE, APAGE), indication, version_date, next_update_expected, recommendation_by_asset (json: {guselkumab: "recommended, moderate certainty"}), positioning_by_segment, jnj_evidence_cited (list)`.

#### `HTADecision`
`hta_id, geo_id, body, asset_id, indication, decision (recommended / restricted / not recommended / pending), restriction_text, evidence_criticisms (text, a rich source of gaps), decision_date, reassessment_date`.

#### `RegulatoryEvent`
`reg_id, asset_id, agency (FDA, EMA, PMDA, NMPA, Health Canada, TGA), type (submission, acceptance, PDUFA/CHMP date, approval, label update, safety communication), date, label_text_diff`.

#### `MarketMetric` (time series, simulated)
`period, geo_id, segment_id, asset_id, patient_share, new_patient_share, switch_in, switch_out, persistence_12m`.

#### `FieldInsight` (MSL-sourced, anonymised and aggregated)
`insight_id, date, geo_id, stakeholder_type, theme (efficacy question, safety concern, competitor claim heard, unmet need, data request), verbatim_summary (de-identified), mapped_gap_id, frequency_count, sentiment`.

#### `Signal` (unified feed)
`signal_id, detected_at, source_id, signal_type (registry change, new trial, date shift, abstract, PR, earnings commentary, guideline, HTA, regulatory, publication, social/news, field insight), related_entity_ids, headline, materiality_score (0–1, AI), novelty (bool), routed_to_owner, status (new / triaged / actioned / dismissed)`.

---

### 3.7 AI layer entities

#### `AIInsight`
| Field | Type | Notes |
|---|---|---|
| insight_id | str | |
| insight_type | enum | summary / so-what / risk alert / opportunity / change-since-last / gap recommendation / strategy inference / scenario narrative / anomaly / forecast |
| scope_entity_type + scope_entity_ids | enum + list | The view or objects the insight explains |
| headline | str (≤ 15 words) | |
| body | text | 2–5 sentences, plain language |
| rationale_steps | list<text> | Reasoning chain |
| cited_source_ids / cited_entity_ids | list | **Required.** No citation, no display. |
| confidence | float 0–1 plus label (low/med/high) | |
| assumptions | list<text> | |
| suggested_actions | list<json> | {action, owner_function, by_date} |
| model / prompt_version | str | Reproducibility |
| generated_at | datetime | |
| review_status | enum | auto / analyst-reviewed / medical-reviewed / rejected |
| user_feedback | json | thumbs up/down and comments |
| audience_restriction | enum | medical-only / cross-functional / leadership |

#### `Recommendation` (output of the decision engines, §5.4)
| Field | Type | Notes |
|---|---|---|
| rec_id | str | |
| engine | enum | E1–E6, T1–T7 |
| decision_level | enum | strategic / tactical |
| action_type | enum | fund / defer / stop / reshape / accelerate / add country / new study concept / submit to venue / publish / encore / co-funding request / reactive material / reallocate budget |
| target_entity_ids | list | Study, gap, output, funder… |
| statement | text | "Submit GALAXI transmural post-hoc to UEGW (deadline 12 May) as an oral; competitor X presents IUS data there" |
| rationale / cited_entity_ids | text / list | Required |
| expected_effect | json | {ERI SI-TRE-02: +6, CTI: −0.1, dark-period days: −180} |
| cost_usd / effort | float / enum | |
| deadline | date | |
| owner_function / funder_id | enum / fk | |
| confidence | float | |
| status | enum | proposed / accepted / rejected (with reason) / in progress / done |
| outcome_observed | json | Filled in afterwards: actual effect, to calibrate the engine |

#### `DecisionLog`
`decision_id, date, forum (Global Evidence Council, EMEA MAF committee, brand medical team), question, options_considered (list<rec_id>), decision, rationale, decided_by (role), follow_up_date, linked_scenario_id`.
It gives an auditable history of why the portfolio looks the way it does.

---

## 4. Derived metrics and scoring formulas

All scores are normalised to 0–100 for display. Weights are configurable in the prototype through an admin panel.

### 4.1 Evidence Readiness Index (ERI), per Strategic Imperative
```
ERI(SI) = Σ_gaps [ criticality_w(g) × coverage(g) × timeliness(g) ] / Σ_gaps criticality_w(g)
timeliness(g) = 1 if expected_close_date ≤ kq.required_by_date
                else max(0, 1 − months_late / 24)
```
RAG: ≥ 70 green · 45–69 amber · < 45 red.

### 4.2 Gap Criticality Score
```
GCS = 0.25·stakeholder_importance + 0.25·imperative_alignment + 0.15·uncertainty_magnitude
    + 0.15·hta_guideline_relevance + 0.20·urgency
    (+1 bonus, capped at 5, if competitor_has_evidence = true → parity gap)
```

### 4.3 Gap Coverage %
```
coverage(g) = min(1, 1 − Π_studies (1 − fit(s,g) × PoS(s)))
```
This is the probability that at least one study closes the gap, weighted by fit. A gap with no studies is an **orphan gap** and gets flagged in red.

Coverage (planned) is kept separate from **realised closure**, i.e. what has actually been communicated:
```
realised_closure(g) = min(1, Σ_outputs fit(s,g) × gap_closure_weight(output))
```
A study can have read out positively while the gap is still only "closed" by a poster. The dashboard shows both bars: **planned coverage vs realised closure**.

### 4.4 Study Impact Score
```
SIS = PoS × Σ_imperatives [impact_if_positive × imperative_priority_w] × reach_factor × timing_factor
reach_factor  = share of priority-market patients covered by the study's evidence (0.3–1)
timing_factor = 1.2 if the readout lands ≥ 6 months before the matching competitor readout,
                1.0 if within ±6 months, 0.8 if after
```

### 4.5 Time-to-Close (months)
`expected_close_date − today`, where the close date is the earliest `EvidenceOutput` (publication or label) of a closing study, weighted by milestone confidence.

### 4.5b Study operational metrics
| Metric | Formula |
|---|---|
| Enrollment % | patients_randomized / n_planned |
| Enrollment vs plan | patients_randomized − patients_planned_cumulative (and as %) |
| Enrollment rate (PSPM) | new randomized in month / sites_enrolling |
| Screen-failure rate | screen_failed / screened |
| Site activation % | sites_activated / sites_planned |
| **Projected LPI** | today + (n_planned − randomized) / trailing-3-month randomization rate |
| Projected PCD / DBL / topline | projected LPI + protocol offsets (e.g. PCD = LPI + primary timepoint; DBL = PCD + ~8 wks; topline = DBL + ~4 wks; defaults configurable per study) |
| FPI→LPI duration | LPI − FPI (actual or forecast), benchmarked vs the IBD Ph3 median |
| Milestone slippage | forecast_or_actual − baseline, per milestone; worst critical-path slip per study |
| Discontinuation rate | discontinued / randomized, by reason |
| Readout race | projected J&J topline − projected competitor topline for studies addressing the same gap |

### 4.6 Competitive Threat Index (CTI), per competitor event or asset
```
CTI = P(positive) × overlap × differentiation_delta × proximity × commercial_strength_norm
overlap              = segment and geo overlap with J&J priority segments (0–1)
differentiation_delta = how much the event erodes a J&J advantage (0–1)
proximity            = 1 / (1 + months_to_event / 12)
```

### 4.7 Evidence Profile (radar), per asset
Dimensions scored 1–5: clinical efficacy · endoscopic/histologic depth · transmural (CD) · H2H evidence · durability (≥ 3y) · onset speed · safety database size · convenience (route/interval) · special populations · RWE volume · guideline standing · HTA acceptance.

### 4.8 Dissemination metrics
- **Publication Plan Adherence** = outputs delivered on time / outputs planned
- **Gap-to-Publication Lag** = publication_date − topline date
- **Share of Voice** = J&J items / all IBD advanced-therapy items per congress
- **Audience Coverage** = share of priority stakeholder × geo cells with ≥ 1 tactic in the last 12 months
- **Message Pull-through** = message_recall_pct (simulated)
- **Analysis-type mix** = share of outputs by analysis_type (primary / secondary / post-hoc / RWE…), J&J vs each competitor. A high post-hoc share with little new primary data signals weak momentum.
- **Publication-type mix** = orals vs posters vs manuscripts; **oral conversion rate** = orals / abstracts submitted
- **Peer-review conversion** = outputs with a peer-reviewed manuscript / outputs presented at congress
- **Abstract-to-manuscript lag** = manuscript publication − first congress presentation (benchmark ≤ 12 m)
- **Ladder completeness** per study = ladder steps delivered / steps due (vs `PublicationLadderTemplate`)
- **Evidence debt** = count of analyses with results available internally but not yet communicated, weighted by gap criticality
- **Dark-period days** = days since the last J&J output on a gap while a competitor output on the same gap exists
- **Acceptance rate** = accepted / submitted, by venue and analysis type

### 4.9 Portfolio balance
Distribution of study impact across gap_type, care segment, geography, time horizon and **evidence_class** (interventional vs RWE vs synthesis). The Gini coefficient flags over-concentration.

### 4.10 Signal Materiality
AI-scored 0–1 from source reliability, entity relevance, novelty and potential CTI change. Signals ≥ 0.7 raise alerts.

### 4.11 Funding and investment metrics
| Metric | Formula / logic | Decision it supports |
|---|---|---|
| Total evidence investment | Σ total_cost_usd by brand / indication / evidence_class / funder / fiscal year | Budget planning |
| Funder share | Σ committed_usd per funder / total | Who carries the portfolio |
| Co-funding ratio | studies with ≥ 2 funders / all studies | Cross-regional alignment |
| **Cost per impact point** | total_cost_usd / Study Impact Score | Value for money; ranking studies |
| **Cost per gap closed** | Σ cost of closing studies / Σ (fit × PoS) | Efficient ways to close a gap |
| Cost per patient | total_cost / n (interventional) or / cohort N (RWE) | Benchmark: RWE is typically 10–50× cheaper per patient |
| Spend on critical vs low-priority gaps | % of budget on gaps with GCS ≥ 4 | Misallocation alert |
| Orphan-gap funding need | Σ estimated cost of AI-suggested studies for orphan gaps | Business case |
| **Pay-vs-benefit balance** | per region: funding share − benefit share (benefiting_geo_ids weighted by market priority) | Negotiating co-funding (e.g. EMEA benefits 40% but pays 10%) |
| Budget burn vs plan | spent_to_date / planned-to-date by fiscal-year split | Operational control |
| Forecast overrun | forecast_at_completion − committed | Early warning |
| Committed vs pipeline | approved vs proposed/in-governance funding | Governance throughput |

---

## 5. AI layer

### 5.1 Insight types and where they appear
| Insight | Trigger | View |
|---|---|---|
| Executive brief | Weekly, or when any KPI moves more than 5 pts | V1 |
| Imperative status narrative | ERI change or RAG change | V2 |
| Gap prioritisation and orphan-gap study suggestions | New gap, or coverage < 30% | V3 |
| Slippage and failure-cascade alert | Milestone slip > 60 days, or PoS change | V4 |
| White-space analysis | Care-segment × geo cells with GCS high and coverage low | V5 |
| Dissemination sequencing advice | Competitor presenting at the same venue, or a deadline within 60 days | V6 |
| Landscape narrative and class trends | New competitor event | V7 |
| Competitor strategy inference | New signals on that asset (≥ 3 since last assessment) | V8 |
| Scenario narrative | User runs a scenario | V9 |
| Signal triage | Each new signal | V10 |
| Funding allocation and overrun commentary | Budget change, overrun > 20%, pay-vs-benefit imbalance | V12 |
| Dissemination quality diagnosis | Ladder violation, evidence debt, dark period | V13 |
| Recommendations (decision engines, §5.4) | Scheduled plus event-triggered | V14, and inline on every view |
| Ask-the-dashboard (chat) | On demand; answers grounded only in dashboard data plus cited sources | All |

### 5.2 Competitor strategy inference method
1. **Collect** signals per asset: trial registrations (design, comparator, population, endpoints, countries), congress activity, earnings-call language, hiring and partnership news, pricing moves, label changes, guideline submissions.
2. **Extract** observations, e.g. "3 new Ph3b studies all in bio-naïve CD with transmural endpoints".
3. **Map** observations to strategic pillars (§3.5) using an observation → pillar rubric.
4. **Infer** a strategy statement plus 1–2 alternative hypotheses, with confidence based on the number of independent corroborating sources and their reliability.
5. **Project**: expected data timing, target segments, and likely claims.
6. **Assess the effect on J&J**: generate `CompetitiveImpactAssessment` records and response options.
7. **Set a watch list**: the leading indicators that would change the inference.

### 5.3 Guardrails
- Every AI statement cites sources or entities. Uncited statements are suppressed.
- AI output is always labelled "AI-generated" and shows its confidence level.
- Inferences are labelled as inference, never as fact. Speculation about non-public competitor information is not allowed.
- No off-label promotional framing. Outputs are scientific and internal-only.
- The model refuses to generate content about named individual HCPs.
- Prompt and model version are logged, and a human review status is shown.

### 5.4 Decision intelligence engines
Insights explain the situation. **Engines recommend what to do next**, with a cost, a deadline, an owner and an expected effect on the scores. Each engine writes `Recommendation` records (§3.7), which users accept or reject. Outcomes are tracked, so the system learns which recommendations worked.

#### Strategic engines (quarterly / annual planning, governance)
| # | Engine | Question answered | Inputs | Logic | Output |
|---|---|---|---|---|---|
| E1 | **Evidence Portfolio Optimiser** | With budget X per funder, which studies should we fund, defer or stop? | Studies (proposed + ongoing), cost, SIS, PoS, gap links, funder budgets, competitor timing | Constrained optimisation: maximise Σ ERI uplift × imperative priority, subject to funder budgets, minimum regional coverage and readout-before-competitor preference | Fund / defer / stop list; efficient-frontier chart (cost vs ERI); what each extra $1M buys |
| E2 | **Gap-Closure Route Planner** | What is the fastest and cheapest credible way to close this gap? | Gap type and stakeholder, existing data assets, RWE sources, cost and time benchmarks | Decision tree: data already exists in a completed trial → **post-hoc** (weeks, low cost, low weight); payer/HTA comparative need → **ITC/NMA or RWE comparative**; practice/persistence need → **RWE**; label or guideline need → **interventional RCT**. Each route scored on time, cost, credibility per audience and competitor timing | Ranked routes with time-to-close, cost, expected closure weight |
| E3 | **Competitive Pre-emption** | Will we be first on this gap, and if not, how do we respond? | Readout race (§4.5b), CompetitiveEvents, dissemination plan | If J&J is behind: options are accelerate (add countries/sites, interim analysis), interim communication (baseline/TiP to hold voice), a reframe (different endpoint or segment), or a reactive scientific-exchange pack | Race chart plus a recommended option |
| E4 | **Co-funding Balancer** | Is each region paying its fair share for evidence it uses? | StudyFunding, benefiting_geo_ids, market priority | Pay-vs-benefit gap per funder (§4.11) | Suggested co-funding shares per study; negotiation brief for EMEA/US MAF |
| E5 | **Study Health & Reshape** | Should this study continue as planned? | Projected LPI/topline, cost overrun, competitor readouts, gap still critical? | Flags studies whose projected readout lands after the competitor's and whose SIS has dropped below a threshold, or whose overrun exceeds 20% | Continue / reshape (add countries, amend, convert to RWE) / stop |
| E6 | **White-space Finder** | Where across segments and geographies do we have no evidence? | Gap × segment × geo coverage, patient_share_pct | Ranks empty cells by patient volume × gap criticality | Top 10 white spaces, each with a proposed study concept |

#### Tactical engines (weekly / monthly execution)
| # | Engine | Question answered | Logic | Output |
|---|---|---|---|---|
| T1 | **Venue Recommender** | Where should this analysis go? | Scores each venue: audience fit × tier × deadline feasibility × analysis-type fit (primary → late-breaker at a tier-1 congress; post-hoc → poster at a regional congress) × competitor presence (counter-programme or avoid) × ladder-rule compliance | Top 3 venues with deadlines and rationale |
| T2 | **Evidence Debt Clearer** | Which results are sitting unpublished? | Evidence debt (§4.8), ranked by gap criticality × competitor pressure × transparency deadline | Prioritised publication to-do list with owner |
| T3 | **Dark-Period Filler** | Where are we silent while competitors speak? | Dark-period days per gap vs the competitor congress calendar | Suggested quick outputs: TiP, baseline, encore, RWE data cut |
| T4 | **Enrollment Rescue** | How do we pull LPI back? | Country enrollment rates, screen-failure rates, competitor recruitment overlap | Add/drop countries, site actions; projected LPI gain in weeks |
| T5 | **Readout Readiness** | Are we ready for the next J&J or competitor readout? | Readouts in the next 90 days × prepared outputs, reactive materials, MSL training | Readiness checklist with gaps flagged |
| T6 | **Congress Planner** | What is our full plan for DDW/ECCO/UEGW? | All outputs targeting the venue + competitor expectations | Per-congress plan: J&J orals/posters by analysis type, expected competitor presence, share-of-voice forecast |
| T7 | **Budget Burn Watch** | Where is money at risk? | Burn vs plan per funder / FY | Reallocation suggestions within the fiscal year |

#### Alert rules (examples, all configurable)
- Critical-path milestone forecast slips > 60 days → notify study lead and gap owner
- A competitor readout moves earlier than a J&J readout on the same gap → E3 is triggered
- Primary analysis with no manuscript 12 months after topline → evidence-debt alert
- Post-hoc output planned before the primary analysis is public → ladder violation, blocked
- Funder share on a study does not total 100%, or the forecast overrun exceeds 20% → finance alert
- Critical gap (GCS ≥ 4) is still an orphan 90 days after identification → escalation to governance
- Competitor share of voice at an upcoming tier-1 congress is forecast above 2× J&J → T6 is triggered

#### Decision question catalogue (what the dashboard must answer in one click)
**Strategic**
1. Which imperatives will not be evidence-ready by their target date, and why?
2. What is our total IBD evidence investment by brand, funder, evidence class and year, and is it aligned with imperative priority?
3. Which critical gaps are unfunded, and what would closing them cost?
4. Which competitor readouts in the next 18 months threaten which imperative?
5. Where should the next $5M go for the highest ERI uplift?
6. Is EMEA/US funding proportional to the evidence each region uses?
7. What is the right interventional vs RWE mix for icotrokinra pre-launch?

**Tactical**
1. What is going to DDW next year: which analyses, which publication types, and do we beat the competitors' share of voice?
2. Which studies will miss LPI, and which countries would fix it?
3. Which results are unpublished and overdue?
4. Which gaps have been silent for more than 9 months while a competitor presents?
5. For each primary result: presented? published? encored in EMEA/APAC?
6. What reactive materials are needed before the competitor's topline in Q?

---

## 6. Simulated seed content (prototype)

> Items marked *(verify)* are based on public information as of the model's knowledge cutoff and must be checked. Everything else is **simulated** for illustration.

### 6.1 Strategic imperatives (simulated)

**TREMFYA (guselkumab)**
| ID | Imperative | Horizon |
|---|---|---|
| SI-TRE-01 | Establish TREMFYA as the preferred IL-23 in bio-naïve moderate-severe UC and CD (1L advanced) | 1–3y |
| SI-TRE-02 | Own "deep healing": endoscopic, histologic and transmural remission as a differentiator | 1–3y |
| SI-TRE-03 | Lead on flexibility and convenience: fully SC regimen (SC induction and maintenance) | 0–12m |
| SI-TRE-04 | Demonstrate long-term durability and a safety profile consistent across indications (≥ 3–5y data) | 1–3y |
| SI-TRE-05 | Win access: HTA acceptance and comparative value vs IL-23 peers and ustekinumab biosimilars | 0–12m |
| SI-TRE-06 | Expand to special populations: pediatric, perianal fistulizing CD, EIMs | 3–5y |
| SI-TRE-07 | Lifecycle: combination therapy (guselkumab + golimumab) to raise the efficacy ceiling in refractory patients | 3–5y |

**Icotrokinra (JNJ-2113)**
| ID | Imperative | Horizon |
|---|---|---|
| SI-ICO-01 | Establish oral IL-23R blockade as delivering biologic-level efficacy in UC | 1–3y |
| SI-ICO-02 | Build the case for "oral first advanced therapy" ahead of JAKs and S1Ps (a better benefit-risk story) | 3–5y |
| SI-ICO-03 | Generate CD proof of concept and a Phase 3 path | 3–5y |
| SI-ICO-04 | Define the TREMFYA–icotrokinra portfolio story (sequencing, switching, patient preference) without cannibalisation | 1–3y |
| SI-ICO-05 | Use cross-indication (psoriasis ICONIC) safety and efficacy to build confidence in IBD | 0–12m |
| SI-ICO-06 | Launch readiness: payer value story for an oral peptide vs generic or biosimilar options | 3–5y |

### 6.2 Example evidence gaps (simulated)
| Gap | Brand | Type | Segment | Competitor has it? |
|---|---|---|---|---|
| No H2H vs risankizumab or mirikizumab in CD or UC | TRE | Comparative | 1L/2L | Partially (IL-23 vs ustekinumab H2H exist for several) |
| Limited transmural healing data (IUS/MRE) in CD | TRE | Endpoint | CD, all lines | Emerging |
| Real-world persistence in the post-ustekinumab-biosimilar switch population | TRE | RWE | 2L switch | Yes (RWE volume) |
| Perianal fistulizing CD outcomes | TRE | Population | Special pop | Limited |
| Pediatric UC/CD dosing and efficacy | TRE/ICO | Pediatric | Pediatric | Some |
| Oral IL-23R efficacy vs advanced-therapy benchmarks (ITC/NMA) | ICO | Comparative | 1L advanced | n/a |
| Icotrokinra efficacy in multi-class refractory UC | ICO | Population | 3L+ | JAKs strong here |
| Icotrokinra CD proof of concept | ICO | Efficacy | CD | Oral competitors in CD |
| Patient preference oral vs SC in IBD | ICO | PRO | 1L | Some (JAK/S1P) |
| Cost-effectiveness vs biosimilar ustekinumab | TRE | HEOR | All | Payer-driven |
| Histology-based treat-to-target outcomes | TRE | Endpoint | Maintenance | Some |

### 6.3 J&J studies to seed
| Study | Brand | Indication | Purpose | Origin |
|---|---|---|---|---|
| QUASAR (Ph2b/3) | TRE | UC | Pivotal IV induction + SC maintenance | public *(verify)* |
| GALAXI 2 & 3 (Ph3) | TRE | CD | Pivotal incl. ustekinumab active reference | public *(verify)* |
| GRAVITI (Ph3) | TRE | CD | SC induction | public *(verify)* |
| ASTRO (Ph3) | TRE | UC | SC induction | public *(verify)* |
| DUET-UC / DUET-CD (Ph2b) | TRE + golimumab | UC/CD | Combination therapy | public *(verify)* |
| FUZION CD | TRE | Perianal fistulizing CD | Special population | public *(verify)* |
| Pediatric studies (e.g. QUASAR Jr, MACARONI-23) | TRE | Ped UC/CD | Pediatric | public *(verify)* |
| LTEs of QUASAR / GALAXI | TRE | UC/CD | Durability | public *(verify)* |
| ANTHEM-UC (Ph2b) | ICO | UC | Dose-ranging, proof of concept | public *(verify)* |
| Icotrokinra Ph3 UC program | ICO | UC | Registrational | public, program name *(verify)* |
| Icotrokinra CD Ph2 | ICO | CD | Proof of concept | **simulated** |
| Transmural healing IUS study | TRE | CD | Deep-healing endpoint | **simulated** |
| Post-biosimilar switch RWE (US claims + EU registries) | TRE | UC/CD | Real-world persistence | **simulated** |
| ITC/NMA oral advanced therapies | ICO | UC | Comparative positioning | **simulated** |
| Patient-preference DCE study | ICO | UC | Oral vs injectable preference | **simulated** |

**Simulated funding seed:** each J&J study gets a lead funder and co-funders. Registrational trials are 100% Global R&D. Ph3b/4 and LTEs are Global MAF-led with US/EMEA co-funding. RWE studies are regional MAF-led (e.g. EMEA MAF 70% / Global MAF 30%). Total costs use simulated benchmarks: Ph3 IBD ≈ $80–150M, Ph3b ≈ $20–40M, prospective RWE ≈ $2–6M, retrospective database RWE ≈ $0.2–0.8M, ITC/NMA ≈ $0.1–0.3M. **All funding figures are simulated.**

### 6.4 Competitor set to seed
| Asset | Company | MoA | Status (to verify) | Why it matters |
|---|---|---|---|---|
| Skyrizi (risankizumab) | AbbVie | IL-23p19 | Approved UC & CD; SEQUENCE H2H vs ustekinumab in CD | Main IL-23 rival |
| Omvoh (mirikizumab) | Lilly | IL-23p19 | Approved UC & CD; VIVID-1 in CD | IL-23 rival |
| Rinvoq (upadacitinib) | AbbVie | JAK1 | Approved UC & CD | Oral efficacy benchmark (icotrokinra) |
| Entyvio (vedolizumab) | Takeda | α4β7 | IV + SC | Gut-selective safety positioning |
| Zeposia (ozanimod), Velsipity (etrasimod) | BMS, Pfizer | S1P | Oral UC | Oral competitor for icotrokinra |
| Stelara + ustekinumab biosimilars | J&J + multiple | IL-12/23 | Biosimilar entry 2025 | Price anchor, switch dynamics |
| Obefazimod | Abivax | miR-124 enhancer (oral) | Ph3 UC (ABTECT) | Oral novel MoA |
| Tulisokibart | Merck | TL1A | Ph3 UC/CD | Next-wave class |
| Duvakitug | Sanofi/Teva | TL1A | Ph3 | Next-wave class |
| Afimkibart | Roche | TL1A | Ph3 | Next-wave class |
| MORF-057 | Lilly | Oral α4β7 | Ph2/3 | Oral gut-selective |
| Other oral IL-23 pathway entrants | various | IL-23R/p19 oral | early | Direct icotrokinra threat |

---

## 7. Data sources and refresh

| Domain | Sources | Refresh | Prototype |
|---|---|---|---|
| Trials (J&J and competitor) | ClinicalTrials.gov API, EU CTIS, WHO ICTRP | Daily diff | Snapshot + simulated |
| Publications | PubMed/Europe PMC API, journal RSS | Weekly | Snapshot |
| Congresses | DDW, ECCO, UEGW, ACG, AGA abstract books | Per congress | Simulated calendar |
| Regulatory | FDA (Drugs@FDA, labels), EMA EPARs, PMDA | Weekly | Snapshot |
| HTA | NICE, G-BA, HAS, CADTH, PBAC | Monthly | Simulated |
| Guidelines | ACG, AGA, ECCO, BSG | Monthly check | Snapshot |
| Corporate | Press releases, earnings calls, 10-K/10-Q, investor days | Event-driven | Public snapshot |
| Market | IQVIA / claims / Symphony (internal licence) | Monthly | **Simulated** |
| Field insights | CRM medical insight module (Veeva) | Weekly | **Simulated** |
| Internal plans | Integrated Evidence Plan, publication plan (Datavision/iEnvision), budgets | On change | **Simulated** |
| News/social | Curated medical news, congress social | Daily | Simulated |

---

## 8. Governance and compliance

- **Medical/commercial firewall:** by default, views V3–V6 and the AI insights are Medical Affairs–only. The commercial role sees an aggregated version (no pre-publication data, no IIS details).
- **Pre-publication data** is embargoed and restricted by role, with an audit trail.
- **Competitive intelligence** comes from public and ethically obtained sources only, following SCIP-style ethics. There is no speculation about confidential competitor data.
- **No personal data on HCPs or patients.** Stakeholders are archetypes, and field insights are de-identified and aggregated.
- **AI outputs** are internal decision support, not promotional material, and need MLR review before any external use.
- **Simulated data** is watermarked on every tile ("SIMULATED") while the dashboard is a prototype.
- **Audit:** every score shows its formula, weights and input records (drill-through).

---

## 9. Open questions to settle before build

1. **What does "TCC" mean?** This spec assumes it is the *treatment/care continuum* (patient journey × line of therapy × disease segment). If it is a J&J-internal framework (for example a specific segmentation or customer model), send its definition and the `CareContinuumSegment` entity will be remapped.
2. **Tech target for the prototype:** a single-file HTML artifact (fast to share) or a React app (Vite plus a mock JSON API)?
3. **Scoring weights:** accept the defaults in §4 or supply team weights?
4. **Geographic granularity:** global plus 5 regions, or ~15 priority countries?
5. **AI in the prototype:** pre-generated insight text (static, simulated), or live calls to Claude against the seed data?
6. **Funder list and governance:** confirm the MAF entities (Global / US / EMEA / APAC / LATAM / Japan / Canada?), whether R&D and HEOR are separate funders, and the names of the governance forums that approve studies.
7. **Gap-closure weights** per publication type (§3.3, `gap_closure_weight`): accept the defaults or supply your own?
8. **Which personas to demo first?** Recommendation: Medical leadership (V1, V2, V3) plus CI (V7, V8, V9).

## 10. Addendum: product profiles and differentiation (added Sep 2026)

**Regimen** (`regimens`): reg_id, brand_id, indication, phase (induction / maintenance), regimen text, route, dose_mg, induction_weeks, maintenance_start_week, interval_weeks, devices_per_dose_min, device_options, setting, infusion_min_hours, status (label / filed), source. Values come from labels; a filed regimen stores only disclosed facts.

**Product attribute** (`product_attributes`): attr_id, indication, group (Administration, Monitoring, Safety, Efficacy, Evidence), attribute, stakeholders, J&J value, competitor value today, competitor value if a filed change is approved, verdict_now / verdict_if_approved (derived), why, changes_on_approval, note, sources.

**Year-1 burden** (`regimen_burden`, derived): per treatment path, events over weeks 0–51 (injection = one device; infusion with minimum hours), totals, and the label liver-test window. Undisclosed induction shows as a hatched band and is excluded from counts.

**Watch item** (`watch_items`): question, current status, resolving source, owner role, linked records. In the scaled system (SCALE_PLAN.md §6) the daily watchers close these and the verdicts re-score.

**Verdict rules:** bool (yes beats no), lower/higher (numeric from labels), cross (cross-trial efficacy: never a claim), different (formats differ, no preference evidence), pending (head-to-head ongoing), same (descriptive parity); "not disclosed" → Unknown. A **differentiation-shift** insight (AI-D01) is generated whenever a competitor event changes any verdict.

## 11. Addendum: lifecycle and loss of exclusivity (added Sep 2026)

| Table | Grain | Key fields |
|---|---|---|
| loe | product × market | first_approval, regulatory_floor (+basis), public_protection (+basis, source), planning_loe (+basis, kind: public signal / placeholder / LOE passed), range_low/high, status, years_to_loe |
| study_loe_window | J&J study | readout_date, paper_date, uptake_date (+basis each), planning_loe_us, protected_years, window, in_use_now, exception, successor_carry_over, suggested_action |
| loe_start_by | J&J brand × market × study type | typical_duration_months (+basis), readout/paper/uptake lags, min_years_before_loe, last_useful_start, months_left, years_if_started_now |

Rules:
- The planning LOE for J&J products is owned by J&J IP. Public filings give a floor or signal only.
- Exceptions (safety, regulatory obligations, paediatric) sit outside LOE-based prioritisation.
- Evidence that lands after a brand's LOE can still carry value to a successor (icotrokinra, JNJ-4804). Record that as a rationale; don't assume it.
- Proposed metrics for the catalogue:
  - Years of use before LOE per activity.
  - Share of spend landing after LOE without a stated exception.

## 12. Addendum: evidence depth (added Sep 2026)

| Table | Grain | Key fields |
|---|---|---|
| evidence_domains | evidence type | domain_code, name, rule |
| study_endpoints | registered outcome | study_id, side, role (primary/secondary/other), measure, time_frame, domains, max_weeks, horizon, review_status |
| study_evidence_profile | study | outcome_source, n_outcomes, domains {code: role, n, horizon}, delivers, not_registered, reported_in_publications, gap_checks {gap: analyst_fit, endpoint_coverage, missing, effective_fit} |
| evidence_depth_by_domain | indication × evidence type | jnj_studies, competitor_studies (running or reading out 2024+), study ids |
| evidence_gaps.needed_domains | gap | evidence types the gap needs ("A|B" = either; "@LT" = must reach >1 year) |
