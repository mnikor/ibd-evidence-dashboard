# From prototype to a multi-TA evidence intelligence platform

How the IBD prototype in this repo becomes a monthly, agent-run system that reads internal J&J
systems and the public domain, flags what looks wrong, and tells you what changed since last month.

Companion to [DATA_SPEC.md](DATA_SPEC.md) (the data model) and [data/README.md](data/README.md)
(what is real and what is simulated today).

---

## 0. The one design decision everything else follows from

**Agents fetch, extract, classify and explain. Deterministic code computes every number.
Humans approve anything that changes the golden record.**

Keep that line and the system is auditable, reproducible and defensible in a medical-affairs
context. Cross it — let a model compute a threat index or "estimate" an enrolment figure — and no
one can reconstruct why a decision was made six months later, which is the one thing this system
exists to support.

Two incidents from building this prototype are the evidence:

- **Fabrication.** While collecting UEG Week abstracts through a browser, titles arrived truncated
  at 150 characters and were completed from memory. Several were wrong — one said "FORTIFY" where
  the source said "SEQUENCE". A plausible, well-formatted, incorrect fact is the failure mode of a
  generative step over messy sources. Every extraction therefore needs the source span, and the
  verifier checks the span actually appears in the source.
- **Two implementations of one metric.** Share of voice was computed once in Python for the AI
  briefing and once in JavaScript for the Publications view. They disagreed (DDW 5% vs 6%) because
  Python rounds 5.5 down and JavaScript rounds it up. Nobody would have noticed for months. One
  metric = one implementation, called by everything.

---

## 1. Where we are and what the prototype already proves

| Proven | Not yet proven |
|---|---|
| The data model holds real data: 51 J&J studies, 93 competitor trials, 4,455 publications, 26 results | That internal systems can be read on a schedule |
| Per-field provenance (`public_verified` / `unverified` / `derived` / `simulated` / `manual`) survives rebuilds | That the strategy layer (imperatives, gaps, fit scores) can be sourced rather than simulated |
| Manual corrections as an append-only override log, re-applied on every rebuild | That a verification queue gets worked by busy people |
| Deterministic derived metrics (readiness, coverage, criticality, threat, impact) | Insight-over-time: every run today is standalone |
| Rule-based recommendations with a visible evidence chain | Multi-TA generalisation |
| A scenario model that re-runs the same formulas under different assumptions | Scale: single-machine Python + a static page |

Today's run is: `fetch_ctgov.py` → `fetch_publications.py` → `build_publications.py` →
`build_dataset.py` → `build_dashboard_data.py`, roughly 10 minutes, one therapeutic area, one
person's laptop.

---

## 2. Three stages

### Stage 1 — Prototype (done)
One TA, one brand pair, public data plus simulated strategy, file-based, manual refresh.
**Purpose:** prove the model and win the argument internally. It does that now.

### Stage 2 — Pilot (~2 quarters, IBD only)
Replace the simulated strategy layer with the real brand plan. Connect two or three internal
systems read-only. Run monthly, unattended. Turn on the verification queue and the change engine.
Ten to twenty named users.
**Exit criteria:** two consecutive unattended monthly runs; >70% of decision-grade fields
`public_verified` or `internal_verified`; verification queue cleared within the month; the "what
changed" brief judged useful by the brand team.

### Stage 3 — Scale (multi-TA platform)
TA config packs, agent fleet, proper storage and orchestration, SSO and role-based access,
attribution reporting. Onboard TA #2, then #3, measuring onboarding effort each time.
**Target:** a new TA live in under six weeks, ~80% of it configuration rather than code.

---

## 3. Target architecture

```
                         ┌──────────────── ORCHESTRATOR (monthly + event triggers) ─────────────────┐
                         │                                                                          │
  INTERNAL (read-only)   │   PUBLIC                        AGENT LAYER                              │
  ├ CTMS / study registry│   ├ ClinicalTrials.gov, EUCTR   ├ connector agents (1 per source)        │
  ├ budgets / MAF finance│   ├ PubMed, Crossref, Europe PMC├ research agents (public domain)        │
  ├ publication planning │   ├ congress libraries          ├ entity-resolution agent                │
  ├ MSL insights (CRM)   │   ├ FDA / EMA / HTA bodies      ├ classification agent                   │
  ├ HTA / value dossiers │   ├ IR decks, earnings calls    ├ data-quality agent  ──► VERIFICATION   │
  ├ market data (IQVIA)  │   └ guidelines bodies           ├ insight agent                          │
  └ MLR status           │                                 ├ change agent (run N vs N-1)            │
         │               │                                 └ critic agent (checks the above)        │
         ▼               │                                          │                               │
  L0 RAW SNAPSHOTS  ──►  L1 ENTITIES  ──►  L2 METRICS (deterministic)  ──►  L3 NARRATIVE + ACTIONS  │
  immutable, hashed      bitemporal,        one shared library,              insights, NBAs,        │
  per source per run     provenance         versioned formulas               deltas, briefs         │
         │                    ▲                                                     │               │
         │                    │                                                     ▼               │
         └──────────  OVERRIDE LOG (human corrections, append-only)  ◄──── VERIFICATION QUEUE ──────┘
```

**L0 raw** — every fetch stored verbatim with a content hash, source, timestamp and run ID. Never
edited. This is what makes "why did the number change?" answerable.

**L1 entities** — the model in DATA_SPEC.md, TA-agnostic. **Bitemporal**: each fact carries
`valid_from` / `valid_to` (when it was true) and `ingested_at` (when we learned it). That pair is
what makes month-over-month diffing possible, and it distinguishes *the world changed* from *we
found out*.

**L2 metrics** — one library, imported by the pipeline and served to the UI. Formula versions are
recorded on every run so a metric change is visible as a metric change, not mistaken for a data
change.

**L3 narrative** — insights, recommendations, deltas. Generated, always citing L1/L2 entity IDs.

---

## 4. The agents

Each has a narrow scope, declared tools, a schema for its output, and a confidence score. None
writes to L1 directly: they emit **proposals** that either pass automated verification or land in
the human queue.

| Agent | Job | Tools | Output |
|---|---|---|---|
| **Connector** (one per internal system) | Pull deltas since last run, map to L1 schema | System API, schema contract | Typed records + reject list |
| **Registry research** | Trials for the TA's asset set and competitors | CTGov/EUCTR APIs | Study records, milestone dates |
| **Literature research** | Journals and congress abstracts naming tracked assets | PubMed, Crossref, Europe PMC, congress libraries | Publications + source spans |
| **Regulatory & access** | Approvals, filings, label changes, HTA outcomes, guideline updates | Agency sites, HTA portals | Events with dates and certainty |
| **Competitive intel** | Press releases, IR decks, earnings-call statements, congress programmes | Web, IR feeds | Competitor events, inferred strategy + evidence chain |
| **Entity resolution** | Link publication ↔ trial ↔ asset ↔ gap; dedupe | Internal indices | Link proposals with confidence |
| **Classification** | Analysis type, presentation type, care segment, gap topic | Rules first, model fallback | Labels + confidence + rationale |
| **Data quality** | Run the check suite (§5) | L0/L1/L2 | Verification tasks |
| **Insight** | Narrative: what matters, what it means | L1/L2 read-only | Insights, each citing entity IDs |
| **Recommendation** | Next best actions with route, owner, cost, due date | L1/L2 + decision log | Ranked actions + evidence chain |
| **Change** | Compare this run with last (§7) | Two snapshots | Deltas, flips, movers |
| **Critic** | Re-derive every numeric claim; confirm every citation resolves; flag unsupported statements | L2 + L3 | Pass / rewrite / block |

Notes that matter in practice:

- **Rules first, model second.** Today's classification is keyword rules with an accuracy you can
  inspect. Add the model as the fallback for what rules miss, log which path fired, and measure.
- **The critic is not optional.** It is the only thing between a fluent sentence and a wrong number
  in front of a brand lead. It re-computes each figure from L2 and blocks anything that doesn't match.
- **Budget per run.** Token and time caps per agent, with partial results preferred over a hung run.
- **Every agent output carries provenance** in the existing tag set, plus `agent_id` and
  `prompt_version`, so a bad prompt release is traceable and reversible.

---

## 5. Spotting missing, inconsistent and wrong data

Eight check families, each producing a **verification task**, not a silent fix. All eight exist in
crude form in the prototype already; this makes them first-class.

| Family | Examples | Prototype precedent |
|---|---|---|
| **Completeness** | Required field null; gap with no closing study (orphan); result with no publication; study with no funder | `evidence_debt()`, orphan gaps |
| **Referential** | Dangling ID; publication linked to a non-existent trial; duplicate rows | VEGA was mis-linked as DUET-UC, making DUET-UC look 32 months overdue |
| **Cross-source contradiction** | Registry PCD ≠ CTMS PCD; N differs between systems; two sources for one sales figure | Registry vs curated facts |
| **Temporal implausibility** | LPI before FPI; readout before primary completion; milestone in the past still "planned"; evidence landing after the guideline cut-off | Guideline readiness view |
| **Outliers** | Cost per patient far off the TA benchmark; enrolment rate implausible for the site count; a share-of-voice jump that is more likely a scraping failure than reality | Value-for-money scatter |
| **Staleness** | Source not refreshed in N days; registry record untouched for 12 months while "recruiting" | `retrieved_at` on every source |
| **Provenance risk** | A decision-grade metric driven mostly by simulated or unverified fields | `data_origin`, `simulated_fields` per row |
| **Extraction risk** | Classification confidence below threshold; an extracted span that does not appear in the source text; a truncated title | The UEG Week fabrication |

**The verification task**

```json
{ "task_id": "...", "run_id": "2026-10", "check": "cross_source.pcd_mismatch",
  "severity": "high", "entity": "NCT05528510", "field": "primary_completion_date",
  "values": [ {"source": "CTMS", "value": "2026-04-30", "as_of": "2026-09-28"},
              {"source": "ClinicalTrials.gov", "value": "2026-07-31", "as_of": "2026-09-30"} ],
  "impact": "Moves GAP-06 closure past the ACG UC evidence cut-off; changes 2 recommendations",
  "suggested": "CTMS is the system of record for J&J-sponsored studies - adopt 2026-04-30",
  "owner_role": "study_manager", "due": "2026-10-14" }
```

Design points that decide whether this works:

- **Route by role, not to a mailbox.** Study dates → study manager. Publication status → pubs lead.
  Competitive events → CI lead. Funding → MAF finance. Strategy and gap scores → brand medical lead.
- **Show the consequence.** "This changes two recommendations" is what gets a task done; "field
  mismatch" is what gets it ignored.
- **Resolution is one click plus a reason**, written to the existing append-only override log with
  who, when, old → new, and why. It survives every rebuild — that already works today.
- **Measure the checks.** Track precision per check. A check whose tasks are dismissed 80% of the
  time is noise; retire or re-tune it. Queue volume is a KPI to drive *down*.
- **Cap the queue.** Rank by impact and cut to what a team can actually clear in a month — start
  around 20–30 tasks. An uncapped queue is an ignored queue.

---

## 6. The monthly cycle

Monthly for the full rebuild; **event-driven watchers in between**, because a competitor topline or
an approval cannot wait three weeks. Watchers run daily on a narrow set of high-value sources and
raise an alert plus a targeted mini-run.

| Day | What happens | Who |
|---|---|---|
| 1 | Connectors pull internal deltas; research agents sweep public sources; L0 snapshot sealed | automated |
| 1–2 | Entity resolution, classification, L1 build; data-quality suite; L2 metrics | automated |
| 2 | Insight, recommendation and change agents run; critic verifies; draft brief assembled | automated |
| 2 | Verification queue published, routed by role | automated |
| 3–10 | Owners resolve tasks; corrections enter the override log | humans |
| 11 | Re-run on corrected data (cheap: L0 cached, only L1→L3 recompute) | automated |
| 12 | Monthly brief released: what changed, what flipped, what to do | humans sign off |
| 12–30 | Recommendations worked; decision log records accept / reject / defer with reasons | humans |

Sign-off matters: the brief goes out with a named medical owner, not as "the AI says". Medical,
legal and privacy review the *template and the source list* once, not every run.

---

## 7. Insight memory: what changed since last month

This is the part that turns a dashboard into something people open every month, and it is mostly a
data-modelling problem rather than an AI problem.

**Stable subject keys.** An insight's identity is its subject, not its wording:
`insight_key = sha1(type + primary_entity + scope)` — e.g. `threat|EV-001|ICO`,
`coverage|GAP-06`, `debt|NCT05528510`. The text may be rewritten every month; the key persists, so
the system can say "this is the same concern, third month running".

**Per-run status.** Each insight gets: `new` · `persisting` · `strengthened` · `weakened` ·
`reversed` · `resolved`, plus the numeric drivers and their deltas, plus *which input moved*.

**Recommendation lifecycle.** `proposed → accepted → in_flight → done | expired | superseded`,
carried in the decision log that the prototype already writes. That enables the sentences people
actually want:

> "You accepted *Convert ANTHEM-UC into a manuscript* two months ago; it is still `proposed` in
> the pubs plan, while the gap it closes rose from criticality 4.2 to 4.7 after ATLAS-UC read out."

**Worked example — the ATLAS-UC card, three runs.**

| Run | Input change | Metric | Insight status | Recommendation |
|---|---|---|---|---|
| Sep 2026 | ATLAS-UC topline confirmed positive | Threat to icotrokinra 8/100 | `new` | Monitor TL1A maintenance data |
| Oct 2026 | Merck files; maintenance data at UEGW | Overlap 0.58 → 0.71, months-to-impact 12 → 9 → **13/100** | `strengthened` — driver: *time to impact* | Escalates: brief MSLs, start oral NMA |
| Nov 2026 | ICONIC-UC hits primary endpoint | Icotrokinra readiness 54 → 71 | `weakened` — driver: *own evidence landed* | Drops below the cut line; marked `superseded` |

The monthly brief is assembled from exactly this: top movers by absolute delta, flipped
recommendations, newly-crossed thresholds, resolved gaps, and the data-quality trend. **Anything
unchanged is not repeated** — the brief is the diff, and that is what makes it short enough to read.

**Attribution.** When an accepted recommendation is followed and the gap closes, record the link.
After three or four cycles the system can show its own hit rate, which is how it earns standing
in a planning meeting.

---

## 8. Scaling across therapeutic areas

The engine is TA-agnostic; the content is not. Split them.

**Shared platform:** entity model, provenance, connectors, agents, metric library, check suite,
change engine, UI, governance.

**Per-TA config pack** (versioned, owned by that TA's medical lead):

- asset set — own and competitor, with mechanisms and lifecycle stage
- care continuum / patient segmentation (IBD's UC/CD × line of therapy is not oncology's staging)
- evidence gap taxonomy and criticality rubric
- congress calendar and tiering, journal target list
- guideline and HTA bodies that matter
- benchmarks: cost per patient, PoS by phase, enrolment rates
- thresholds: what counts as critical, as a threat, as overdue

**Onboarding a new TA** — target six weeks: config pack drafted with the brand team (2 weeks,
their effort is the real constraint) · connectors re-pointed, mostly configuration (1 week) ·
first run and rule tuning (1 week) · verification queue worked and thresholds calibrated
(2 weeks). Track the effort each time; if TA #3 isn't meaningfully cheaper than TA #2, something
that should be configuration is still code.

**Governance that does not scale by itself:** one metric library owner, one prompt-and-agent
release process, a shared check registry, and a quarterly review of formulas and thresholds across
TAs. Access is role-based: brand teams see their TA, global medical sees all, finance sees funding.
The medical/commercial separation is a hard boundary in the data model, not a UI filter.

---

## 9. Build notes

**Stack** — Python pipeline; object storage for L0; Postgres for L1/L2 (bitemporal tables);
Dagster or Airflow for orchestration; the Claude Agent SDK for the agent layer with tool use and
structured outputs; the metric library as a versioned package imported by both pipeline and API;
the current static dashboard becomes a served app behind SSO. Nothing exotic — the difficulty is
access and data quality, not technology.

**Sequence** — (1) metric library extracted and versioned, (2) L0/L1 storage with bitemporal
history, (3) one internal connector end-to-end, (4) check suite and queue, (5) change engine,
(6) agentisation of the public-domain sweep, (7) second TA.

**Team** — one data engineer, one full-stack engineer, a part-time ML/agent engineer, and — the
part usually under-resourced — a medical-affairs data owner per TA who owns the config pack and
the queue. Without that last role the queue rots and the whole thing degrades to a nice-looking
dashboard of stale numbers.

**Things that will bite**

| Risk | Mitigation |
|---|---|
| Internal system access takes longer than the build | Start access requests before writing code; design for read-only service accounts |
| Congress abstract libraries restrict scraping and are copyrighted | Licence where needed; store IDs, titles and links rather than full text; honour robots and terms |
| Fluent, wrong insights | Critic agent; numbers only from L2; every claim cites an entity |
| Simulated values mistaken for real | Keep provenance visible in the UI as it is today; block decision-grade metrics dominated by simulated inputs |
| Queue ignored | Cap it, route by role, show consequence, report clear-rate as a KPI |
| Metric drift across TAs | One library, versioned formulas, quarterly review |
| Personal data in MSL insights | De-identified and aggregated at ingestion, as the prototype does; privacy review of the connector, not of each run |

---

## 10. What to confirm before Stage 2

1. **Which internal systems are the systems of record** for: study operations and dates, budgets and
   funder splits, publication planning and MLR status, MSL insights, HTA submissions and outcomes,
   market share. Each needs a named owner and an API or export path.
2. **Who owns the golden record** per TA, and who staffs the verification queue.
3. **Whether the strategy layer** (imperatives, gaps, criticality, study→gap fit) is maintained in a
   system or lives in slide decks. If it is decks, that is the first thing to give a home — the
   whole model hangs off it, and it is the largest simulated block today.
4. **Cadence per source.** Monthly is right for the rebuild; decide which sources get daily watchers.
5. **The compliance envelope:** medical vs commercial separation, what the system may infer about
   competitors, and who signs off the monthly brief.
