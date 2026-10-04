"""Build the IBD Evidence Intelligence prototype dataset.

Inputs
  data/raw/ctgov/*.json      registry extracts (scripts/fetch_ctgov.py)
  scripts/curated_public.py  hand-curated public facts with sources
Outputs
  data/json/<table>.json               one file per table, rows carry _provenance
  data/IBD_Evidence_Dataset.xlsx        one sheet per table, cells colour-coded by provenance

Every field of every row has a provenance tag:
  public_verified    registry or web source checked on the build date
  public_unverified  public knowledge not re-checked; verify before use
  derived            calculated from other fields by a rule stated in the table notes
  simulated          invented for the prototype; replace with real data
  reference          taxonomy / configuration defined by the team
Simulation is deterministic (seed 42), so rebuilding gives the same dataset.
"""
import datetime as dt
import json
import math
import pathlib
import random
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import curated_public as cp  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "ctgov"
TODAY = dt.date(2026, 9, 19)
rng = random.Random(42)

PV, PU, DE, SI, RF = "public_verified", "public_unverified", "derived", "simulated", "reference"
MN = "manual"  # value edited by the team in the Data Editor (data/overrides/overrides.json)
AIX = "ai_inferred"  # judgement written by AI (classification, estimate, interpretation, assumption); plausible, not checked by a person

# ---------------------------------------------------------------- manual edits (Data Editor)
OVR_FILE = ROOT / "data" / "overrides" / "overrides.json"
try:
    OVERRIDES = [o for o in json.loads(OVR_FILE.read_text()) if not o.get("reverted")]
except (FileNotFoundError, json.JSONDecodeError):
    OVERRIDES = []
OVR_BY = defaultdict(list)
for _o in OVERRIDES:
    OVR_BY[(_o["table"], str(_o["key"]))].append(_o)
APPLIED = set()


# =============================================================== table helper
class Table:
    def __init__(self, name, description, key_fields=()):
        self.name, self.description = name, description
        self.key_fields = set(key_fields)
        self.rows = []
        self.key_count = Counter()

    def _row_key(self, fields):
        """Stable row key: first field value, suffixed #n when it repeats (build order is deterministic)."""
        kv = str(next(iter(fields.values()), ""))
        self.key_count[kv] += 1
        return kv if self.key_count[kv] == 1 else f"{kv}#{self.key_count[kv]}"

    def apply_overrides(self, row, skip_add=False):
        for o in OVR_BY.get((self.name, row["key"]), []):
            if o["op"] == "set":
                row["fields"][o["field"]] = o["new"]
                row["prov"][o["field"]] = MN
            elif o["op"] == "delete":
                row["deleted"] = True
            elif o["op"] == "add" and skip_add:
                continue
            else:
                continue
            APPLIED.add(o["id"])
            if "SRC-MANUAL" not in row["src"]:
                row["src"].append("SRC-MANUAL")
            stamp = f'[{o.get("editor", "?")} {str(o.get("ts", ""))[:10]}] {o.get("note", "")}'.strip()
            row["note"] = (row["note"] + " | " if row["note"] else "") + stamp

    def add(self, origin, fields, src=(), sim=(), der=(), unv=(), ver=(), ref=(), note=""):
        prov = {k: origin for k in fields}
        for group, tag in ((sim, SI), (der, DE), (unv, PU), (ver, PV), (ref, RF)):
            for k in group:
                if k not in fields:
                    raise KeyError(f"{self.name}: provenance for unknown field {k}")
                prov[k] = tag
        row = {"fields": fields, "prov": prov, "src": list(dict.fromkeys(src)), "note": note, "key": self._row_key(fields), "deleted": False}
        self.apply_overrides(row)
        self.rows.append(row)
        return fields

    def origin_summary(self, row):
        tags = {t for k, t in row["prov"].items() if k not in self.key_fields}
        return tags.pop() if len(tags) == 1 else ("mixed" if tags else RF)


TABLES = {}


def table(name, description, key_fields=()):
    TABLES[name] = Table(name, description, key_fields)
    return TABLES[name]


# =============================================================== date helpers
def pdate(s):
    """Parse YYYY-MM-DD or YYYY-MM (mid-month) into a date; None if not parseable."""
    if not s:
        return None
    m = re.match(r"^(\d{4})-(\d{2})(?:-(\d{2}))?$", s)
    if not m:
        return None
    return dt.date(int(m[1]), int(m[2]), int(m[3] or 15))


def add_months(d, months):
    y, m = divmod(d.month - 1 + int(months), 12)
    return dt.date(d.year + y, m + 1, min(d.day, 28))


def iso(d):
    return d.isoformat() if isinstance(d, dt.date) else d


def months_between(a, b):
    return (b.year - a.year) * 12 + (b.month - a.month)


# =============================================================== registry parsing
def parse(study):
    p = study["protocolSection"]
    ident, st, des = p["identificationModule"], p["statusModule"], p.get("designModule", {})
    spons = p["sponsorCollaboratorsModule"]
    locs = p.get("contactsLocationsModule", {}).get("locations", [])
    by_country = defaultdict(lambda: {"sites": 0})
    for loc in locs:
        by_country[loc.get("country", "Unknown")]["sites"] += 1
    arms = p.get("armsInterventionsModule", {}).get("armGroups", [])
    prim = p.get("outcomesModule", {}).get("primaryOutcomes", [])
    sec = p.get("outcomesModule", {}).get("secondaryOutcomes", [])
    elig = p.get("eligibilityModule", {})
    di = des.get("designInfo", {})

    def dget(key):
        v = st.get(key, {})
        return v.get("date"), (v.get("type") or "").lower()

    start, start_t = dget("startDateStruct")
    pcd, pcd_t = dget("primaryCompletionDateStruct")
    comp, comp_t = dget("completionDateStruct")
    return {
        "nct_id": ident["nctId"],
        "acronym": ident.get("acronym") or "",
        "brief_title": ident.get("briefTitle", ""),
        "official_title": ident.get("officialTitle", ""),
        "lead_sponsor": spons["leadSponsor"]["name"],
        "sponsor_class": spons["leadSponsor"].get("class", ""),
        "collaborators": "; ".join(c["name"] for c in spons.get("collaborators", [])),
        "study_type_raw": des.get("studyType", ""),
        "phases": "/".join(x.replace("PHASE", "Ph") for x in des.get("phases", []) or []) or "n/a",
        "status": st.get("overallStatus", ""),
        "n": des.get("enrollmentInfo", {}).get("count"),
        "n_type": (des.get("enrollmentInfo", {}).get("type") or "").lower(),
        "start": start, "start_type": start_t,
        "pcd": pcd, "pcd_type": pcd_t,
        "completion": comp, "completion_type": comp_t,
        "last_update": st.get("lastUpdatePostDateStruct", {}).get("date"),
        "has_results": bool(study.get("hasResults")),
        "conditions": "; ".join(p.get("conditionsModule", {}).get("conditions", [])),
        "countries": dict(by_country),
        "n_sites": len(locs),
        "allocation": di.get("allocation", ""),
        "masking": di.get("maskingInfo", {}).get("masking", ""),
        "intervention_model": di.get("interventionModel", ""),
        "obs_model": "; ".join(di.get("observationalModel", []) if isinstance(di.get("observationalModel"), list) else [di.get("observationalModel", "")]),
        "time_perspective": "; ".join(di.get("timePerspective", []) if isinstance(di.get("timePerspective"), list) else [di.get("timePerspective", "")]),
        "arms": [{"label": a.get("label", ""), "type": a.get("type", ""),
                  "interventions": "; ".join(a.get("interventionNames", [])),
                  "description": (a.get("description") or "")[:240]} for a in arms],
        "primary_outcomes": [{"measure": o.get("measure", "")[:200], "time_frame": o.get("timeFrame", "")[:120]} for o in prim],
        "secondary_outcomes": [o.get("measure", "")[:200] for o in sec],
        "outcomes_full": [{"role": role, "measure": o.get("measure", "")[:300], "time_frame": o.get("timeFrame", "")[:160]}
                          for role, lst in (("primary", prim), ("secondary", sec), ("other", p.get("outcomesModule", {}).get("otherOutcomes", []))) for o in lst],
        "min_age": elig.get("minimumAge", ""),
        "max_age": elig.get("maximumAge", ""),
    }


def load(asset):
    f = RAW / f"{asset}.json"
    if not f.exists():
        return []
    return [parse(s) for s in json.loads(f.read_text())["studies"]]


def indication_of(r):
    t = (r["conditions"] + " " + r["brief_title"]).lower()
    uc, cd = "colitis" in t, "crohn" in t
    if "pouchitis" in t:
        return "Pouchitis"
    if uc and cd or "inflammatory bowel" in t:
        return "UC+CD"
    return "UC" if uc else ("CD" if cd else "Other")


def is_pediatric(r):
    t = (r["brief_title"] + r["official_title"]).lower()
    return "pediatric" in t or "paediatric" in t or "children" in t or r["max_age"] in ("17 Years", "18 Years")


# =============================================================== sources
t_src = table("sources", "Every source referenced by source_ids across the dataset.", ["source_id"])
for sid, typ, title, pub, date, url, rel in cp.SOURCES:
    origin = SI if typ == "simulated" else PV
    t_src.add(origin, {"source_id": sid, "type": typ, "title": title, "publisher": pub, "publish_date": date,
                       "url": url, "reliability_grade": rel, "retrieved_at": cp.RETRIEVED})

# =============================================================== reference tables
t_moa = table("moa", "Mechanisms of action.", ["moa_id"])
for mid, name, pathway, origin in cp.MOAS:
    t_moa.add(origin, {"moa_id": mid, "name": name, "pathway": pathway})

t_ind = table("indications", "Indications in scope.", ["indication_id"])
for iid, name in [("UC", "Ulcerative colitis"), ("CD", "Crohn's disease"), ("PFCD", "Perianal fistulizing Crohn's disease"),
                  ("POUCH", "Pouchitis"), ("PED-UC", "Pediatric UC"), ("PED-CD", "Pediatric CD"), ("PSO", "Plaque psoriasis (cross-indication)")]:
    t_ind.add(RF, {"indication_id": iid, "name": name})

t_geo = table("geographies", "Regions and priority countries. Tier, prevalence and biologic penetration are simulated.", ["geo_id", "parent_geo_id"])
GEOS = [
    ("GLOBAL", "Global", "global", "", "", ""), ("NA", "North America", "region", "GLOBAL", "", ""),
    ("EMEA", "Europe, Middle East & Africa", "region", "GLOBAL", "", ""), ("APAC", "Asia-Pacific", "region", "GLOBAL", "", ""),
    ("LATAM", "Latin America", "region", "GLOBAL", "", ""),
    ("USA", "United States", "country", "NA", "none (payer-driven)", "free-pricing"), ("CAN", "Canada", "country", "NA", "CDA-AMC", "HTA-driven"),
    ("GBR", "United Kingdom", "country", "EMEA", "NICE", "HTA-driven"), ("DEU", "Germany", "country", "EMEA", "G-BA / IQWiG", "HTA-driven"),
    ("FRA", "France", "country", "EMEA", "HAS", "HTA-driven"), ("ITA", "Italy", "country", "EMEA", "AIFA", "budget-driven"),
    ("ESP", "Spain", "country", "EMEA", "AEMPS / CIPM", "budget-driven"), ("NLD", "Netherlands", "country", "EMEA", "ZIN", "HTA-driven"),
    ("POL", "Poland", "country", "EMEA", "AOTMiT", "budget-driven"), ("CHE", "Switzerland", "country", "EMEA", "BAG/FOPH", "HTA-driven"),
    ("SAU", "Saudi Arabia", "country", "EMEA", "SFDA / NUPCO", "budget-driven"), ("JPN", "Japan", "country", "APAC", "Chuikyo", "HTA-driven"),
    ("CHN", "China", "country", "APAC", "NHSA (NRDL)", "budget-driven"), ("KOR", "South Korea", "country", "APAC", "HIRA", "HTA-driven"),
    ("AUS", "Australia", "country", "APAC", "PBAC", "HTA-driven"), ("BRA", "Brazil", "country", "LATAM", "CONITEC", "budget-driven"),
]
TIER = {"USA": "T1", "DEU": "T1", "JPN": "T1", "GBR": "T1", "FRA": "T1", "CHN": "T2", "ITA": "T2", "ESP": "T2", "CAN": "T2",
        "AUS": "T2", "KOR": "T2", "NLD": "T3", "POL": "T3", "CHE": "T3", "SAU": "T3", "BRA": "T3"}
for gid, name, level, parent, hta, arche in GEOS:
    row = {"geo_id": gid, "name": name, "level": level, "parent_geo_id": parent, "hta_body": hta, "payer_archetype": arche,
           "market_priority_tier": TIER.get(gid, ""),
           "ibd_prevalence_per_100k": rng.randint(150, 480) if level == "country" else None,
           "biologic_penetration_pct": round(rng.uniform(18, 45), 1) if level == "country" else None}
    t_geo.add(PU, row, sim=("market_priority_tier", "ibd_prevalence_per_100k", "biologic_penetration_pct"),
              ref=("name", "level"))

COUNTRY_ISO = {"United States": "USA", "Canada": "CAN", "United Kingdom": "GBR", "Germany": "DEU", "France": "FRA", "Italy": "ITA",
               "Spain": "ESP", "Netherlands": "NLD", "Poland": "POL", "Switzerland": "CHE", "Saudi Arabia": "SAU", "Japan": "JPN",
               "China": "CHN", "Korea, Republic of": "KOR", "South Korea": "KOR", "Australia": "AUS", "Brazil": "BRA",
               "Argentina": "ARG", "Austria": "AUT", "Belarus": "BLR", "Belgium": "BEL", "Bosnia and Herzegovina": "BIH", "Bulgaria": "BGR",
               "Chile": "CHL", "Colombia": "COL", "Croatia": "HRV", "Czechia": "CZE", "Denmark": "DNK", "Dominican Republic": "DOM",
               "Egypt": "EGY", "Estonia": "EST", "Finland": "FIN", "Georgia": "GEO", "Greece": "GRC", "Hong Kong": "HKG", "Hungary": "HUN",
               "India": "IND", "Ireland": "IRL", "Israel": "ISR", "Jordan": "JOR", "Latvia": "LVA", "Lebanon": "LBN", "Lithuania": "LTU",
               "Malaysia": "MYS", "Mexico": "MEX", "Moldova": "MDA", "New Zealand": "NZL", "North Macedonia": "MKD", "Norway": "NOR",
               "Peru": "PER", "Portugal": "PRT", "Puerto Rico": "PRI", "Romania": "ROU", "Russia": "RUS", "Serbia": "SRB",
               "Singapore": "SGP", "Slovakia": "SVK", "Slovenia": "SVN", "South Africa": "ZAF", "Sweden": "SWE", "Taiwan": "TWN",
               "Thailand": "THA", "Tunisia": "TUN", "Turkey (Türkiye)": "TUR", "Turkey": "TUR", "Ukraine": "UKR", "United Arab Emirates": "ARE"}

t_seg = table("care_segments", "Care-continuum segments (the assumed 'TCC' axis). patient_share_pct is simulated.", ["segment_id"])
SEGMENTS = [
    ("UC-1L", "UC", "moderate-severe", "1L advanced", "bio-naive", "first advanced therapy"),
    ("UC-2L", "UC", "moderate-severe", "2L", "TNF-IR", "switch"),
    ("UC-3L", "UC", "moderate-severe", "3L+", "multi-class-IR", "switch"),
    ("UC-MAINT", "UC", "moderate-severe", "any", "any", "long-term remission"),
    ("UC-PED", "UC", "moderate-severe", "any", "any", "pediatric"),
    ("CD-1L", "CD", "moderate-severe", "1L advanced", "bio-naive", "first advanced therapy"),
    ("CD-2L", "CD", "moderate-severe", "2L", "TNF-IR", "switch"),
    ("CD-3L", "CD", "moderate-severe", "3L+", "multi-class-IR", "switch"),
    ("CD-MAINT", "CD", "moderate-severe", "any", "any", "long-term remission"),
    ("CD-PFCD", "CD", "any", "any", "any", "perianal fistulizing"),
    ("CD-PED", "CD", "moderate-severe", "any", "any", "pediatric"),
    ("CD-POSTOP", "CD", "any", "any", "any", "post-surgical"),
    ("IBD-POUCH", "UC", "any", "any", "any", "pouchitis"),
    ("IBD-PREG", "UC+CD", "any", "any", "any", "pregnancy / lactation"),
    ("IBD-EIM", "UC+CD", "any", "any", "any", "extra-intestinal manifestations (SpA/PsO)"),
]
for sid, dis, sev, lot, prior, stage in SEGMENTS:
    t_seg.add(RF, {"segment_id": sid, "disease": dis, "severity": sev, "line_of_therapy": lot, "prior_exposure": prior,
                   "journey_stage": stage, "patient_share_pct": round(rng.uniform(3, 30), 1)}, sim=("patient_share_pct",))

t_stk = table("stakeholders", "Stakeholder archetypes (no named individuals). Weights are simulated.", ["stakeholder_id"])
for sid, typ, prefs in [
    ("STK-GI-ACAD", "Gastroenterologist (academic IBD centre)", "RCT; H2H; endoscopy; histology; transmural"),
    ("STK-GI-COMM", "Gastroenterologist (community)", "RCT; convenience; safety; RWE"),
    ("STK-NURSE", "IBD nurse specialist", "convenience; PROs; administration"),
    ("STK-SURG", "Colorectal surgeon", "fistula outcomes; post-op recurrence"),
    ("STK-PAYER", "Payer / HTA body", "H2H; ITC/NMA; cost-effectiveness; RWE persistence"),
    ("STK-GUIDE", "Guideline committee", "RCT; H2H; NMA; long-term safety"),
    ("STK-REG", "Regulator", "RCT; pediatric; safety"),
    ("STK-PAT", "Patient / advocacy organisation", "PROs; oral route; fatigue; QoL"),
    ("STK-PEDGI", "Pediatric gastroenterologist", "pediatric RCT; growth; PK"),
]:
    t_stk.add(RF, {"stakeholder_id": sid, "type": typ, "evidence_preferences": prefs, "influence_weight": rng.randint(2, 5)},
              sim=("influence_weight",))

t_fund = table("funders", "Funding entities (team-defined list; confirm names with J&J governance).", ["funder_id"])
FUNDERS = [("F-GMAF", "Global MAF", "global"), ("F-USMAF", "US MAF", "regional"), ("F-EMEAMAF", "EMEA MAF", "regional"),
           ("F-APACMAF", "APAC MAF", "regional"), ("F-JPMAF", "Japan MAF", "regional"), ("F-LATAMMAF", "LATAM MAF", "regional"),
           ("F-RD", "Global R&D / Clinical Development", "global"), ("F-HEOR", "Global HEOR / Market Access", "global"),
           ("F-LOCAL", "Local operating company", "local"), ("F-EXT", "External co-funder / partner", "external")]
for fid, name, level in FUNDERS:
    t_fund.add(RF, {"funder_id": fid, "name": name, "level": level})

t_ladder = table("publication_ladder_template", "Expected dissemination sequence per study type (reference configuration for the prototype; replace with J&J publication planning standards).", ["template_id"])
LADDER = {
    "Interventional-registrational": [
        ("Trial in progress", "Poster", "FPI", 9, True), ("Baseline characteristics", "Poster", "LPI", 5, False),
        ("Interim analysis", "Poster or oral", "IA", 3, False),
        ("Primary analysis", "Press release (topline)", "TLR", 0, True), ("Primary analysis", "Late-breaking oral", "TLR", 4, True),
        ("Primary analysis", "Primary manuscript", "TLR", 12, True), ("Secondary analysis", "Oral presentation", "ABS1", 6, True),
        ("Secondary analysis", "Secondary manuscript", "ABS1", 15, False), ("Primary analysis", "Encore (regional)", "ABS1", 6, False),
        ("Post-hoc analysis", "Poster", "ABS1", 9, False), ("Long-term extension", "Oral presentation", "LTE-cut", 12, False)],
    "Non-interventional (RWE)": [
        ("Trial in progress", "Poster", "FPI", 6, False), ("RWE data cut", "Poster", "DATACUT1", 3, True),
        ("RWE data cut", "Primary manuscript", "DATACUT1", 12, True), ("RWE data cut", "Oral presentation", "DATACUT2", 3, False)],
}
LADDER_NOTE = {"Interim analysis": "Optional. Fits open-label, single-arm and extension studies, or a pre-specified interim analysis that is made public (e.g. stopping early). Blinded randomised trials usually do not publish interim efficacy before the primary readout.",
               "Baseline characteristics": "Describes who was enrolled; no outcome data, so it does not unblind the trial."}
for tid, steps in LADDER.items():
    for i, (an, pub, trig, off, mand) in enumerate(steps, 1):
        t_ladder.add(RF, {"template_id": tid, "step": i, "analysis_type": an, "publication_type": pub,
                          "trigger_milestone": trig, "target_offset_months": off, "mandatory": mand,
                          "note": LADDER_NOTE.get(an, "")})

# gap-closure weight matrix (configuration used for realised closure)
CLOSURE_WEIGHT = {("peer-reviewed journal", "Primary analysis"): 1.0, ("peer-reviewed journal", "Secondary analysis"): 0.7,
                  ("peer-reviewed journal", "Post-hoc analysis"): 0.4, ("peer-reviewed journal", "RWE data cut"): 0.6,
                  ("peer-reviewed abstract", "Primary analysis"): 0.6, ("peer-reviewed abstract", "Secondary analysis"): 0.4,
                  ("peer-reviewed abstract", "Post-hoc analysis"): 0.2, ("peer-reviewed abstract", "RWE data cut"): 0.3,
                  ("not peer-reviewed", "Primary analysis"): 0.3,
                  ("peer-reviewed journal", "Interim analysis"): 0.5, ("peer-reviewed abstract", "Interim analysis"): 0.3}


def closure_weight(peer, analysis):
    if analysis in ("Trial in progress", "Baseline characteristics"):
        return 0.0
    return CLOSURE_WEIGHT.get((peer, analysis), 0.2)


# =============================================================== brands
t_brand = table("brands", "J&J and competitor assets. Commercial-strength and evidence-profile scores are simulated (AI-estimated).", ["brand_id", "moa_id"])
EVIDENCE_DIMS = ["efficacy", "endoscopic_histologic_depth", "transmural", "h2h_evidence", "durability", "onset_speed",
                 "safety_database", "convenience", "special_populations", "rwe_volume", "guideline_standing", "hta_acceptance"]
PROFILE_SEED = {  # 1-5, simulated analyst scoring
    "TRE": [4, 4, 3, 3, 3, 4, 4, 5, 4, 2, 4, 4], "ICO": [3, 3, 1, 1, 1, 3, 2, 5, 1, 1, 1, 1], "JNJ4804": [4, 4, 1, 2, 1, 3, 1, 3, 2, 1, 1, 1],
    "SKY": [4, 4, 3, 4, 4, 4, 4, 3, 3, 4, 4, 4], "OMV": [4, 3, 2, 3, 4, 3, 3, 3, 2, 2, 4, 3], "RIN": [5, 4, 2, 1, 4, 5, 4, 5, 2, 4, 4, 3],
    "ENT": [3, 3, 2, 2, 5, 2, 5, 3, 3, 5, 4, 4], "VEL": [3, 2, 1, 1, 3, 3, 3, 5, 1, 2, 3, 3], "ZEP": [3, 2, 1, 1, 3, 3, 3, 5, 1, 3, 3, 3],
    "STE": [3, 3, 2, 2, 5, 3, 5, 3, 3, 5, 4, 5], "OBE": [3, 3, 1, 1, 2, 2, 2, 5, 1, 1, 1, 1], "TUL": [3, 3, 2, 1, 1, 3, 2, 3, 1, 1, 1, 1],
    "DUV": [3, 3, 2, 1, 1, 3, 1, 3, 1, 1, 1, 1], "AFI": [3, 3, 2, 1, 1, 3, 1, 3, 1, 1, 1, 1], "MOR": [2, 2, 1, 1, 1, 2, 1, 5, 1, 1, 1, 1],
}
COMMERCIAL = {"TRE": 5, "ICO": 5, "JNJ4804": 4, "STE": 3, "SKY": 5, "OMV": 4, "RIN": 5, "ENT": 4, "VEL": 3, "ZEP": 3,
              "OBE": 2, "TUL": 4, "DUV": 4, "AFI": 4, "MOR": 4}
for aid, brand, inn, co, is_jnj, moa, modality, routes, stage, srcs, origin in cp.ASSETS:
    row = {"brand_id": aid, "brand_name": brand, "inn": inn, "company": co, "is_jnj": is_jnj, "moa_id": moa,
           "modality": modality, "routes": routes, "lifecycle_stage": stage,
           "commercial_strength_1to5": COMMERCIAL[aid],
           "evidence_profile": dict(zip(EVIDENCE_DIMS, PROFILE_SEED[aid]))}
    t_brand.add(origin, row, src=srcs + ["SRC-AI"], sim=("commercial_strength_1to5", "evidence_profile"))

# =============================================================== strategy layer (all simulated)
t_si = table("strategic_imperatives", "SIMULATED J&J strategic imperatives (replace with the real brand plan).", ["imperative_id", "brand_id"])
IMPERATIVES = [
    ("SI-TRE-01", "TRE", "UC; CD", "Establish TREMFYA as the preferred IL-23 in bio-naive moderate-severe UC and CD", "differentiation", "1-3y", 1),
    ("SI-TRE-02", "TRE", "UC; CD", "Own 'deep healing': endoscopic, histologic and transmural remission", "differentiation", "1-3y", 2),
    ("SI-TRE-03", "TRE", "UC; CD", "Defend fully-SC flexibility leadership as SC-induction competitors arrive", "convenience", "0-12m", 3),
    ("SI-TRE-04", "TRE", "UC; CD", "Demonstrate long-term durability and consistent safety (>=3-5y)", "durability", "1-3y", 4),
    ("SI-TRE-05", "TRE", "UC; CD", "Win access vs IL-23 peers and ustekinumab biosimilars", "access", "0-12m", 5),
    ("SI-TRE-06", "TRE", "CD; UC", "Expand into special populations: perianal fistula, pediatric, pouchitis, pregnancy", "expand population", "1-3y", 6),
    ("SI-TRE-07", "JNJ4804", "UC; CD", "Raise the efficacy ceiling in refractory IBD with JNJ-4804 (guselkumab + golimumab)", "lifecycle", "3-5y", 7),
    ("SI-ICO-01", "ICO", "UC", "Establish oral IL-23R blockade as biologic-level efficacy in UC", "differentiation", "1-3y", 1),
    ("SI-ICO-02", "ICO", "UC; CD", "Position icotrokinra as the first advanced therapy of choice ahead of JAK/S1P/obefazimod", "differentiation", "3-5y", 2),
    ("SI-ICO-03", "ICO", "CD", "Generate CD efficacy via ICONIC-CD Ph2b/3", "expand population", "3-5y", 3),
    ("SI-ICO-04", "ICO", "UC; CD", "Define the TREMFYA-icotrokinra portfolio story (sequencing, preference) without cannibalisation", "lifecycle", "1-3y", 4),
    ("SI-ICO-05", "ICO", "UC", "Leverage psoriasis ICONIC safety/efficacy to build IBD confidence", "safety", "0-12m", 5),
    ("SI-ICO-06", "ICO", "UC", "Launch readiness: payer value story for an oral peptide vs generic/biosimilar options", "launch readiness", "3-5y", 6),
]
# What success looks like for each imperative (simulated targets, written as outcomes, not claims)
DESIRED_IMPACT = {
    "SI-TRE-01": "Recommended as a first-line advanced therapy in ECCO, ACG and AGA guidelines, supported by a head-to-head result against SKYRIZI",
    "SI-TRE-02": "Endoscopic, histologic and transmural outcomes cited in guidelines and used by HCPs as treatment targets",
    "SI-TRE-03": "Fully subcutaneous induction recognised in guidelines and HTA decisions, and still chosen after SC-induction competitors launch",
    "SI-TRE-04": "Long-term (3-5 year) efficacy and safety published and cited by guidelines and payers",
    "SI-TRE-05": "Reimbursement in priority markets against IL-23 peers and ustekinumab biosimilars",
    "SI-TRE-06": "Label or guideline support for perianal fistulizing disease, children, pouchitis and pregnancy",
    "SI-TRE-07": "Phase 3 evidence that JNJ-4804 helps patients who failed several drug classes",
    "SI-ICO-01": "Phase 3 UC results accepted by regulators, guidelines and HCPs as comparable to injectable biologics",
    "SI-ICO-02": "Placed by HCPs and guidelines as a first advanced therapy option ahead of other oral drugs",
    "SI-ICO-03": "Positive Phase 2b/3 Crohn's disease results ready for filing",
    "SI-ICO-04": "An evidence-based story on who starts on icotrokinra and who on TREMFYA, used by field teams",
    "SI-ICO-05": "Psoriasis safety data accepted as supportive by IBD experts and regulators",
    "SI-ICO-06": "A payer value dossier ready at launch, with cost-effectiveness against oral and biosimilar options",
}
for iid, bid, ind, title, theme, hor, prio in IMPERATIVES:
    t_si.add(SI, {"imperative_id": iid, "brand_id": bid, "indication_scope": ind, "title": title, "theme": theme,
                  "time_horizon": hor, "priority_rank": prio, "desired_impact": DESIRED_IMPACT[iid],
                  "required_by_date": iso(add_months(TODAY, {"0-12m": 12, "1-3y": 30, "3-5y": 54}[hor]))}, src=["SRC-SIM"])

t_kq = table("key_questions", "SIMULATED key questions per imperative.", ["kq_id", "imperative_id"])
KQS = [
    ("KQ-01", "SI-TRE-01", "Is guselkumab at least as effective as risankizumab in CD?", "guideline; formulary"),
    ("KQ-02", "SI-TRE-01", "How does guselkumab compare with other advanced therapies in bio-naive UC?", "guideline; prescribing"),
    ("KQ-03", "SI-TRE-02", "Does guselkumab achieve transmural healing and disease modification in CD?", "guideline; prescribing"),
    ("KQ-04", "SI-TRE-03", "Does a fully SC regimen improve real-world persistence and patient experience?", "prescribing; access"),
    ("KQ-05", "SI-TRE-04", "Are efficacy and safety maintained beyond 3 years?", "guideline; prescribing"),
    ("KQ-06", "SI-TRE-05", "Is guselkumab cost-effective vs biosimilar ustekinumab and IL-23 peers?", "HTA; formulary"),
    ("KQ-07", "SI-TRE-06", "Is guselkumab effective in perianal fistulizing CD and pediatric IBD?", "label; guideline"),
    ("KQ-08", "SI-TRE-07", "Does JNJ-4804 outperform monotherapy in multi-class refractory IBD?", "label"),
    ("KQ-09", "SI-ICO-01", "Does icotrokinra deliver Ph3 efficacy comparable to injectable IL-23s in UC?", "label"),
    ("KQ-10", "SI-ICO-02", "Where does icotrokinra sit vs JAK, S1P and obefazimod (efficacy/safety)?", "guideline; formulary"),
    ("KQ-11", "SI-ICO-03", "Is icotrokinra effective in CD?", "label"),
    ("KQ-12", "SI-ICO-04", "Which patients prefer oral vs SC IL-23 and how should they be sequenced?", "prescribing"),
    ("KQ-13", "SI-ICO-06", "What is the payer value of an oral IL-23R antagonist?", "HTA; formulary"),
    ("KQ-14", "SI-ICO-05", "Does the psoriasis (ICONIC) safety experience translate to IBD patients on long-term therapy?", "label; guideline"),
]
for kid, iid, q, dec in KQS:
    t_kq.add(SI, {"kq_id": kid, "imperative_id": iid, "question": q, "decision_it_informs": dec}, src=["SRC-SIM"])

# gap_id, brand, kq, title, type, segments, geos, stakeholders, competitor_has_evidence, scores(stk,align,unc,hta,urg), competitor refs
GAPS = [
    ("GAP-01", "TRE", "KQ-01", "No head-to-head data vs risankizumab in CD", "comparative", "CD-1L; CD-2L", "GLOBAL", "STK-GI-ACAD; STK-PAYER; STK-GUIDE", True, (5, 5, 4, 5, 5), "NCT04524611"),
    ("GAP-02", "TRE", "KQ-02", "No head-to-head data vs IL-23 or vedolizumab in UC", "comparative", "UC-1L", "GLOBAL", "STK-GI-ACAD; STK-PAYER", True, (4, 5, 4, 4, 4), "NCT06880744"),
    ("GAP-03", "TRE", "KQ-03", "Limited transmural healing / disease-modification data in CD", "endpoint", "CD-1L; CD-2L; CD-MAINT", "GLOBAL", "STK-GI-ACAD; STK-GUIDE", False, (4, 5, 4, 3, 3), ""),
    ("GAP-04", "TRE", "KQ-07", "Perianal fistulizing CD: primary data presented, manuscript and label pending", "population", "CD-PFCD", "GLOBAL", "STK-SURG; STK-GI-ACAD; STK-REG", False, (4, 4, 2, 3, 3), ""),
    ("GAP-05", "TRE", "KQ-07", "Pediatric UC and CD efficacy/dosing", "pediatric", "UC-PED; CD-PED", "USA; EMEA", "STK-PEDGI; STK-REG", True, (3, 3, 4, 2, 3), "NCT07071519"),
    ("GAP-06", "TRE", "KQ-05", "Long-term (>=3y) durability and safety", "durability", "UC-MAINT; CD-MAINT", "GLOBAL", "STK-GI-ACAD; STK-GUIDE", True, (4, 4, 3, 3, 3), ""),
    ("GAP-07", "TRE", "KQ-04", "Real-world persistence and effectiveness after ustekinumab (incl. biosimilar) switch", "RWE", "UC-2L; CD-2L", "USA; DEU; GBR", "STK-GI-COMM; STK-PAYER", True, (4, 4, 4, 4, 4), ""),
    ("GAP-08", "TRE", "KQ-06", "Cost-effectiveness vs biosimilar ustekinumab and IL-23 peers", "HEOR", "UC-1L; CD-1L", "GBR; DEU; FRA; CAN; AUS", "STK-PAYER", True, (5, 5, 3, 5, 4), ""),
    ("GAP-09", "JNJ4804", "KQ-08", "Efficacy ceiling in multi-class refractory IBD", "population", "UC-3L; CD-3L", "GLOBAL", "STK-GI-ACAD; STK-REG", True, (4, 4, 4, 3, 3), "NCT06227910"),
    ("GAP-10", "TRE", "KQ-04", "Real-world use and preference of the fully SC regimen as SC-induction competitors launch", "RWE", "UC-1L; CD-1L", "USA; EMEA", "STK-NURSE; STK-PAT; STK-GI-COMM", False, (3, 5, 4, 2, 5), "NCT06063967"),
    ("GAP-11", "TRE", "KQ-07", "Pouchitis efficacy", "population", "IBD-POUCH", "EMEA", "STK-GI-ACAD; STK-SURG", False, (2, 2, 5, 1, 1), ""),
    ("GAP-12", "TRE", "KQ-07", "Pregnancy and lactation safety", "safety", "IBD-PREG", "GLOBAL", "STK-GI-ACAD; STK-PAT; STK-REG", True, (3, 3, 4, 2, 2), ""),
    ("GAP-13", "TRE", "KQ-02", "Local data in China and Asia", "population", "UC-1L; CD-1L", "CHN; JPN; KOR", "STK-REG; STK-PAYER", True, (3, 3, 3, 4, 3), ""),
    ("GAP-14", "TRE", "KQ-03", "Mechanistic differentiation (dual-acting / CD64) translated to outcomes", "mechanistic", "CD-1L; UC-1L", "GLOBAL", "STK-GI-ACAD", False, (3, 4, 4, 1, 2), ""),
    ("GAP-15", "TRE", "KQ-02", "Dose optimisation / treat-to-target strategy data", "dosing & convenience", "CD-MAINT", "EMEA", "STK-GI-ACAD; STK-GUIDE", False, (3, 3, 4, 2, 2), ""),
    ("GAP-16", "ICO", "KQ-09", "Phase 3 efficacy and safety in UC (adults and adolescents)", "efficacy", "UC-1L; UC-2L", "GLOBAL", "STK-REG; STK-GI-ACAD", False, (5, 5, 3, 4, 4), ""),
    ("GAP-17", "ICO", "KQ-11", "Efficacy in Crohn's disease", "efficacy", "CD-1L; CD-2L", "GLOBAL", "STK-REG; STK-GI-ACAD", True, (5, 5, 5, 4, 3), ""),
    ("GAP-18", "ICO", "KQ-10", "Comparative positioning vs oral advanced therapies (JAK, S1P, obefazimod)", "comparative", "UC-1L", "GLOBAL", "STK-GUIDE; STK-PAYER", True, (4, 5, 4, 5, 4), "NCT05535946"),
    ("GAP-19", "ICO", "KQ-12", "Patient preference oral vs injectable IL-23", "PRO", "UC-1L; CD-1L", "USA; EMEA", "STK-PAT; STK-GI-COMM", False, (3, 4, 4, 2, 3), ""),
    ("GAP-20", "ICO", "KQ-12", "Sequencing TREMFYA and icotrokinra (portfolio positioning)", "sequencing & positioning", "UC-1L; UC-2L", "GLOBAL", "STK-GI-ACAD; STK-GUIDE", False, (3, 5, 5, 2, 2), ""),
    ("GAP-21", "ICO", "KQ-13", "Payer value of an oral IL-23R antagonist", "HEOR", "UC-1L", "USA; GBR; DEU", "STK-PAYER", True, (4, 5, 4, 5, 3), ""),
    ("GAP-22", "ICO", "KQ-14", "Long-term safety of oral IL-23R peptide in IBD (bridging from psoriasis)", "safety", "UC-MAINT", "GLOBAL", "STK-REG; STK-GUIDE", False, (4, 4, 3, 3, 3), ""),
]

# study -> [(gap, fit)] (simulated analyst mapping)
STUDY_GAPS = {
    "NCT07499232": [("GAP-01", 0.95)], "NCT06408935": [("GAP-03", 0.8), ("GAP-14", 0.3)], "NCT05347095": [("GAP-04", 0.9)],
    "NCT05923073": [("GAP-05", 0.5)], "NCT06260163": [("GAP-05", 0.5)], "NCT06663332": [("GAP-05", 0.3), ("GAP-06", 0.2)],
    "NCT03466411": [("GAP-06", 0.5), ("GAP-03", 0.2)], "NCT04033445": [("GAP-06", 0.5)], "NCT05528510": [("GAP-06", 0.3), ("GAP-10", 0.3)],
    "NCT05197049": [("GAP-06", 0.2), ("GAP-10", 0.3)],
    "NCT07245394": [("GAP-07", 0.5)], "NCT07102368": [("GAP-07", 0.4), ("GAP-10", 0.3)], "NCT07242248": [("GAP-07", 0.3)],
    "NCT07822529": [("GAP-07", 0.4), ("GAP-06", 0.2)], "NCT07532213": [("GAP-06", 0.1)], "NCT07606339": [("GAP-07", 0.1)],
    "NCT07541261": [("GAP-07", 0.1)], "NCT07746765": [("GAP-06", 0.1)],
    "NCT07577856": [("GAP-09", 0.6)], "NCT07577843": [("GAP-09", 0.6)], "NCT05242471": [("GAP-09", 0.3)], "NCT05242484": [("GAP-09", 0.3)],
    "NCT06916390": [("GAP-11", 0.7)], "NCT07654751": [("GAP-12", 0.4)], "NCT02103361": [("GAP-12", 0.5)],
    "NCT07310095": [("GAP-13", 0.5)], "NCT07302360": [("GAP-13", 0.4)], "NCT07616687": [("GAP-15", 0.7)],
    "NCT07196748": [("GAP-16", 0.95), ("GAP-22", 0.4)], "NCT07196722": [("GAP-17", 0.9)], "NCT06049017": [("GAP-16", 0.3)],
    "SIM-RWE-01": [("GAP-07", 0.6), ("GAP-10", 0.4)], "SIM-HEOR-01": [("GAP-08", 0.7)], "SIM-ITC-01": [("GAP-18", 0.6)],
    "SIM-DCE-01": [("GAP-19", 0.8), ("GAP-10", 0.3)], "SIM-MECH-01": [("GAP-14", 0.6)], "SIM-ITC-02": [("GAP-02", 0.4)],
    "SIM-HEOR-02": [("GAP-21", 0.6)],
}

# =============================================================== J&J studies
t_study = table("studies", "J&J and J&J-product studies. Registry fields are public_verified; strategy/impact/cost fields are simulated.",
                ["study_id", "nct_id", "brand_ids"])
t_design = table("study_design", "Arms, design and all registered outcomes (primary, secondary, other/exploratory) from the registry.", ["study_id"])
t_country = table("study_country_sites", "Sites per study x country from registry location lists (J&J studies and competitor Ph3).", ["study_id", "geo_id"])
t_ms = table("study_milestones", "Study milestones with baseline / forecast / actual dates. See 'date_basis' for how each date was obtained.",
             ["milestone_id", "study_id"])
t_enr = table("study_enrollment", "SIMULATED monthly enrollment curves for J&J interventional studies (anchored to registry N and dates).",
              ["study_id"])
t_fundrow = table("study_funding", "SIMULATED funding split per study x funder. Replace with finance data.", ["study_id", "funder_id"])
t_rwe = table("rwe_study_detail", "RWE study details. Registry N/dates public; data source, method and outcomes largely simulated.", ["study_id"])
t_base = table("study_baseline", "SIMULATED baseline characteristics for key trials (placeholders; replace from publications).", ["study_id"])
t_res = table("study_results", "Published efficacy results (public). Cross-trial comparisons are not head-to-head.", ["result_id", "study_id"])
t_saf = table("study_safety", "SIMULATED safety summaries (placeholders; replace from publications/CSRs).", ["study_id"])

EXCLUDE = {"NCT07138898", "NCT07177209", "NCT06274554", "NCT06089590", "NCT07198113"}
REG_INTENT = {"NCT04033445": "registrational", "NCT03466411": "registrational", "NCT05197049": "registrational", "NCT05528510": "registrational",
              "NCT07196748": "registrational", "NCT07196722": "registrational", "NCT07577856": "registrational", "NCT07577843": "registrational",
              "NCT05923073": "registrational (pediatric)", "NCT06260163": "registrational (pediatric)", "NCT05347095": "registrational (label expansion)",
              "NCT06663332": "label-supportive", "NCT07499232": "medical (H2H, label-supportive)", "NCT06408935": "medical",
              "NCT06049017": "registrational (dose-finding)", "NCT05242471": "registrational (dose-finding)", "NCT05242484": "registrational (dose-finding)",
              "NCT03662542": "medical (proof of concept)", "NCT04397263": "registrational (Japan)", "NCT07654751": "post-marketing commitment"}
IMPACT_IF_POS = {"NCT07499232": 5, "NCT07196748": 5, "NCT07196722": 5, "NCT06408935": 4, "NCT05347095": 4, "NCT07577856": 4,
                 "NCT07577843": 4, "SIM-HEOR-01": 4, "SIM-ITC-01": 4, "SIM-RWE-01": 3}
PRIMARY_TIMEPOINT_WK = {"NCT04033445": 44, "NCT03466411": 48, "NCT05197049": 48, "NCT05528510": 24, "NCT05347095": 24,
                        "NCT07196748": 52, "NCT07196722": 48, "NCT07577856": 48, "NCT07577843": 48, "NCT07499232": 48,
                        "NCT06408935": 48, "NCT05923073": 52, "NCT06260163": 52, "NCT06663332": 156}
KNOWN_POSITIVE = {"NCT04033445", "NCT03466411", "NCT05197049", "NCT05528510", "NCT05347095", "NCT06049017", "NCT03662542"}

raw_jnj = load("TRE") + load("ICO") + [r for r in load("TRE_extra") if r["nct_id"] == "NCT05347095"]
seen, jnj = set(), []
for r in raw_jnj:
    if r["nct_id"] in seen or r["nct_id"] in EXCLUDE:
        continue
    seen.add(r["nct_id"])
    jnj.append(r)
ICO_IDS = {r["nct_id"] for r in load("ICO")}


def jnj_sponsor(name):
    return "janssen" in name.lower() or "johnson" in name.lower()


def classify(r):
    if r["study_type_raw"] == "INTERVENTIONAL":
        ph = r["phases"]
        t = (r["brief_title"] + r["official_title"]).lower()
        if "long-term extension" in t or "(lte)" in t:
            st = "LTE"
        elif ph == "Ph2/Ph3":
            st = "Ph2b/3"
        elif ph == "Ph2":
            st = "Ph2b" if (r["n"] or 0) > 150 else "Ph2a"
        elif ph == "Ph3":
            st = "Ph3 pediatric" if is_pediatric(r) else ("Ph3b" if "versus" in t or "compared" in t else "Ph3")
        elif ph == "Ph4":
            st = "Ph4"
        else:
            st = ph
        return "Interventional", st
    tp = r["time_perspective"].lower()
    t = r["brief_title"].lower()
    if "registry" in t:
        st = "registry"
    elif "retrospective" in tp:
        st = "retrospective database"
    else:
        st = "prospective observational cohort"
    return "Non-interventional (RWE)", st


def brand_ids_of(r):
    t = (r["brief_title"] + " " + r["official_title"] + " " + r["acronym"]).lower()
    if r["nct_id"] in ICO_IDS:
        return "ICO"
    if "jnj-78934804" in t or "duet encore" in t:
        return "JNJ4804"
    if "golimumab" in t:
        return "TRE; JNJ4804"
    return "TRE"


def segments_of(r, ind):
    t = (r["brief_title"] + " " + r["official_title"]).lower()
    if "fistul" in t:
        return "CD-PFCD"
    if "pouchitis" in t:
        return "IBD-POUCH"
    if "breast milk" in t or "pregnan" in t:
        return "IBD-PREG"
    if "spondyloarthritis" in t:
        return "IBD-EIM"
    if is_pediatric(r):
        return {"UC": "UC-PED", "CD": "CD-PED"}.get(ind, "UC-PED; CD-PED")
    if "surgical" in t or "resection" in t:
        return "CD-POSTOP"
    if "ustekinumab" in t or "switch" in t:
        return {"UC": "UC-2L", "CD": "CD-2L"}.get(ind, "UC-2L; CD-2L")
    base = {"UC": "UC-1L; UC-2L", "CD": "CD-1L; CD-2L"}.get(ind, "UC-1L; CD-1L")
    if "refractory" in t or "jnj-78934804" in t or "golimumab" in t:
        base = {"UC": "UC-3L", "CD": "CD-3L"}.get(ind, "UC-3L; CD-3L")
    return base


def country_rows(sid, r):
    for cname, v in r["countries"].items():
        t_country.add(PV, {"study_id": sid, "geo_id": COUNTRY_ISO.get(cname, cname), "country_name": cname,
                           "n_sites_registry": v["sites"]}, src=["SRC-CTGOV"])


def status_label(s):
    return s.replace("_", " ").lower()


study_index = {}
for r in jnj:
    sid = r["nct_id"]
    ind = indication_of(r)
    ev_class, st_type = classify(r)
    j_sp = jnj_sponsor(r["lead_sponsor"])
    j_col = jnj_sponsor(r["collaborators"])
    sponsorship = "J&J-sponsored" if j_sp else ("collaborative (J&J collaborator)" if j_col else "external investigator/academic (J&J support unknown)")
    gaps = STUDY_GAPS.get(sid, [])
    if sid in KNOWN_POSITIVE:
        pos, pos_basis = 1.0, "read out positive (public)"
    elif r["status"] in ("TERMINATED", "WITHDRAWN"):
        pos, pos_basis = 0.0, "terminated (registry)"
    else:
        pos = {"Ph3": 0.7, "Ph3b": 0.6, "Ph2b/3": 0.55, "Ph3 pediatric": 0.75, "LTE": 0.9, "Ph4": 0.85, "Ph2b": 0.45, "Ph2a": 0.4}.get(st_type, 0.9)
        pos_basis = "simulated benchmark by phase"
    impact = IMPACT_IF_POS.get(sid, 3 if j_sp and ev_class == "Interventional" else 2)
    row = {
        "study_id": sid, "nct_id": sid, "acronym": r["acronym"], "title": r["brief_title"], "brand_ids": brand_ids_of(r),
        "indication": ind, "evidence_class": ev_class, "study_type": st_type, "phase_registry": r["phases"],
        "sponsorship_model": sponsorship, "lead_sponsor": r["lead_sponsor"],
        "regulatory_intent": REG_INTENT.get(sid, "medical" if ev_class == "Interventional" else "medical / HTA-supportive"),
        "status": status_label(r["status"]), "n_planned_or_actual": r["n"], "n_type": r["n_type"],
        "n_countries": len(r["countries"]), "n_sites_registry": r["n_sites"],
        "start_date": r["start"], "primary_completion_date": r["pcd"], "pcd_date_type": r["pcd_type"],
        "completion_date": r["completion"], "has_registry_results": r["has_results"], "registry_last_update": r["last_update"],
        "care_segment_ids": segments_of(r, ind),
        "gap_ids_addressed": "; ".join(g for g, _ in gaps), "gap_fit": {g: f for g, f in gaps},
        "probability_of_success": pos, "pos_basis": pos_basis, "impact_if_positive_1to5": impact,
    }
    simulated_pos = pos_basis.startswith("simulated")
    t_study.add(
        PV, row, src=["SRC-CTGOV", "SRC-SIM"],
        der=("indication", "evidence_class", "study_type", "sponsorship_model", "regulatory_intent", "care_segment_ids") +
            (() if simulated_pos else ("probability_of_success", "pos_basis")),
        sim=("gap_ids_addressed", "gap_fit", "impact_if_positive_1to5") + (("probability_of_success", "pos_basis") if simulated_pos else ()),
        note="derived fields use keyword rules on registry titles/conditions; verify")
    study_index[sid] = {"r": r, "row": row, "jnj_sponsored": j_sp}
    t_design.add(PV, {"study_id": sid, "allocation": r["allocation"], "masking": r["masking"],
                      "intervention_model": r["intervention_model"], "observational_model": r["obs_model"],
                      "time_perspective": r["time_perspective"], "min_age": r["min_age"], "max_age": r["max_age"],
                      "arms": r["arms"], "n_arms": len(r["arms"]), "primary_outcomes": r["primary_outcomes"],
                      "secondary_outcomes": r["secondary_outcomes"],
                      "other_outcomes": [o["measure"] for o in r["outcomes_full"] if o["role"] == "other"]}, src=["SRC-CTGOV"], der=("n_arms",))
    country_rows(sid, r)

# simulated (not in registry) J&J studies that close orphan gaps
SIM_STUDIES = [
    ("SIM-RWE-01", "US claims: persistence after ustekinumab/biosimilar switch", "TRE", "UC+CD", "Non-interventional (RWE)", "retrospective database", "UC-2L; CD-2L", "planned", 12000, "2026-11", "2027-06"),
    ("SIM-HEOR-01", "Cost-effectiveness model vs biosimilar ustekinumab and IL-23 peers (EU5)", "TRE", "UC+CD", "Evidence synthesis & modelling", "cost-effectiveness", "UC-1L; CD-1L", "in development", None, "2026-07", "2027-01"),
    ("SIM-ITC-01", "NMA of oral advanced therapies in UC (icotrokinra vs JAK/S1P/obefazimod)", "ICO", "UC", "Evidence synthesis & modelling", "NMA", "UC-1L", "planned", None, "2027-03", "2028-06"),
    ("SIM-ITC-02", "NMA of IL-23 and vedolizumab in bio-naive UC", "TRE", "UC", "Evidence synthesis & modelling", "NMA", "UC-1L", "proposed", None, "2027-01", "2027-07"),
    ("SIM-DCE-01", "Discrete-choice experiment: oral vs SC IL-23 preference", "ICO", "UC+CD", "Non-interventional (RWE)", "PRO / patient-preference (DCE)", "UC-1L; CD-1L", "planned", 800, "2026-12", "2027-05"),
    ("SIM-MECH-01", "Translational study: CD64-mediated IL-23 capture and mucosal outcomes", "TRE", "CD", "Interventional", "mechanistic", "CD-1L", "proposed", 60, "2027-04", "2028-10"),
    ("SIM-HEOR-02", "Early payer value model for oral IL-23R antagonist in UC", "ICO", "UC", "Evidence synthesis & modelling", "budget impact", "UC-1L", "proposed", None, "2027-06", "2027-12"),
]
for sid, title, bid, ind, cls, st_type, segs, status, n, start, pcd in SIM_STUDIES:
    gaps = STUDY_GAPS.get(sid, [])
    row = {"study_id": sid, "nct_id": "", "acronym": "", "title": title, "brand_ids": bid, "indication": ind, "evidence_class": cls,
           "study_type": st_type, "phase_registry": "n/a", "sponsorship_model": "J&J-sponsored", "lead_sponsor": "Johnson & Johnson (simulated)",
           "regulatory_intent": "HTA-supportive" if "HEOR" in sid or "ITC" in sid else "medical", "status": status,
           "n_planned_or_actual": n, "n_type": "planned", "n_countries": None, "n_sites_registry": None,
           "start_date": start, "primary_completion_date": pcd, "pcd_date_type": "planned", "completion_date": pcd,
           "has_registry_results": False, "registry_last_update": None, "care_segment_ids": segs,
           "gap_ids_addressed": "; ".join(g for g, _ in gaps), "gap_fit": {g: f for g, f in gaps},
           "probability_of_success": 0.9, "pos_basis": "simulated", "impact_if_positive_1to5": IMPACT_IF_POS.get(sid, 3)}
    t_study.add(SI, row, src=["SRC-SIM"], note="Entire study is simulated to illustrate orphan-gap closure")
    study_index[sid] = {"r": None, "row": row, "jnj_sponsored": True}

# =============================================================== evidence depth: what each study will (and won't) deliver
# Every registered outcome is sorted into an evidence type by keyword rules (reviewable in the Data Editor). A study only
# "delivers" a type it registers; "not registered" means not promised, since exploratory endpoints are often unregistered.
DOMAINS = [  # code, name, rule
    ("CLIN", "Clinical remission / response", r"clinical (remission|response)|disease clearance|symptomatic worsening|\bcdai\b|\bpro-?2\b|mayo score|modified mayo|partial mayo|symptomatic (remission|response)|stool frequency|rectal bleeding|abdominal pain|\bpucai\b|\bpcdai\b|harvey|\bhbi\b|disease activity"),
    ("ENDO", "Endoscopic", r"endoscop|ses-?cd|mucosal healing|mayo endoscopic|\buceis\b|\bmes\b"),
    ("HIST", "Histologic", r"histolog|geboes|nancy|robarts|\brhi\b|histo-?endoscopic|\bhemi\b"),
    ("TRAN", "Transmural / bowel imaging", r"transmural|intestinal ultrasound|bowel ultrasound|\bius\b|magnetic resonance enterograph|\bmre\b|\bmaria\b|bowel wall|bowel damage|lemann"),
    ("FIST", "Fistula / perianal", r"fistul|\bpdai\b|magnifi|perianal"),
    ("STER", "Steroid-free", r"(cortico)?steroid-?free|corticosteroid.{0,25}(free|sparing)"),
    ("BIOM", "Biomarkers (CRP, calprotectin)", r"c-reactive|\bcrp\b|calprotectin|\bfcal\b|biomarker|biochemical remission|lactoferrin"),
    ("PRO", "Patient-reported / quality of life", r"\bibdq\b|facit|wpai|eq-?5d|quality of life|quality-of-life|ibd-?di|disability index|patient-reported|patient reported|sf-36|fatigue|promis|\bsibdq\b|satisfaction|preference|urgency|incontinence|wexner"),
    ("PERS", "Persistence / treatment patterns", r"persisten|discontinu|treatment pattern|switch|dose (escalation|intensification|optimi)|drug survival|retention|adherence"),
    ("HCRU", "Healthcare use, surgery, cost", r"hospitali|surger|surgical|resection|colectomy|healthcare resource|health care resource|utili[sz]ation|\bcosts?\b|emergency"),
    ("SAFE", "Safety", r"adverse event|\bsafety\b|\bteaes?\b|infection|malignan|laboratory abnormal|abnormalit|suicid|\baes?\b|\bsaes?\b|malformation|spontaneous abortion|stillbirth|preterm|infant follow"),
    ("PK", "Drug levels / immunogenicity", r"pharmacokinetic|serum concentration|trough|antibod(y|ies) to|anti-drug|immunogenic|\bauc\b|\bcmax\b|(drug|serum|systemic|apparent) clearance|breast milk|infant dosage"),
    ("COMP", "Comparison vs another drug", None),   # from the design: active-comparator arm (direct) or network meta-analysis (indirect)
]
DNAME = {c: n for c, n, _ in DOMAINS}
t_dom = table("evidence_domains", "Reference: the evidence types used to describe what a study will deliver, with the keyword rule that assigns registry outcomes to each.", ["domain_code"])
for c, n, rx in DOMAINS:
    t_dom.add(RF, {"domain_code": c, "name": n, "rule": rx or "design: active-comparator arm (direct) or network meta-analysis (indirect)"})
OTHER_DRUGS = r"ustekinumab|risankizumab|vedolizumab|adalimumab|infliximab|upadacitinib|tofacitinib|mirikizumab|etrasimod|ozanimod|golimumab|certolizumab|filgotinib|guselkumab"
def horizon(tf):
    """longest timepoint in a registry time frame, in weeks, and its horizon bucket.
    Handles '52 weeks', 'Weeks 12, 48 and 96', 'Week I-12' / 'Week M-40' (induction / maintenance: M counts after a 12-week induction), 'LTE Year 4'."""
    t = re.sub(r"\(baseline\)", "", (tf or "").lower()); wk = []
    for n, u in re.findall(r"(\d+(?:\.\d+)?)\s*(weeks?|wks?|months?|years?|days?)\b", t):
        n = float(n); wk.append(n if u.startswith("w") else n * 4.35 if u.startswith("mo") else n * 52 if u.startswith("y") else n / 7)
    for m in re.finditer(r"\bw(?:ee)?ks?\s*((?:[im]-)?\d+(?:\s*(?:,|and|to|through|or|-)\s*(?:[im]-)?\d+)*)", t):
        for pre, n in re.findall(r"([im]-)?(\d+)", m.group(1)): wk.append(float(n) + (12 if pre == "m-" else 0))
    for n in re.findall(r"\byears?\s*(\d+)", t): wk.append(float(n) * 52)
    for n in re.findall(r"\bmonths?\s*(\d+)", t): wk.append(float(n) * 4.35)
    if not wk: return None, "unspecified"
    w = max(wk)
    return round(w), "early (≤12 wk)" if w <= 12 else "1 year (13–52 wk)" if w <= 60 else "long term (>1 y)"
def classify_outcome(measure):
    return [c for c, _, rx in DOMAINS if rx and re.search(rx, measure, re.I)]
def comparator_of(r, own_rx):
    """'direct' if any registry arm gives another advanced therapy without the study's own drug (arm types vary: CHARGE registers both as experimental)"""
    for a in r["arms"]:
        iv = a["interventions"].lower()
        if re.search(OTHER_DRUGS, iv) and not re.search(own_rx, iv): return "direct" if r["study_type_raw"] == "INTERVENTIONAL" else "cohort"
    return None
# declared deliverables for studies with no registry record (simulated studies): what the protocol concept says it will produce
DECLARED = {"SIM-RWE-01": ["PERS", "HCRU"], "SIM-HEOR-01": ["HCRU", "COMP"], "SIM-ITC-01": ["CLIN", "ENDO", "COMP"], "SIM-ITC-02": ["CLIN", "ENDO", "COMP"],
            "SIM-DCE-01": ["PRO"], "SIM-MECH-01": ["BIOM", "HIST", "ENDO"], "SIM-HEOR-02": ["HCRU"]}
# what each gap needs to be answered (proposed by the prototype; the evidence team confirms). "@LT" = must reach long term (>1 year)
GAP_NEEDS = {"GAP-01": ["COMP", "CLIN", "ENDO"], "GAP-02": ["COMP", "CLIN", "ENDO"], "GAP-03": ["TRAN"], "GAP-04": ["FIST"], "GAP-05": ["CLIN", "PK"],
             "GAP-06": ["CLIN@LT", "SAFE@LT"], "GAP-07": ["PERS", "CLIN"], "GAP-08": ["HCRU", "COMP"], "GAP-09": ["CLIN", "ENDO"], "GAP-10": ["PERS", "PRO"],
             "GAP-11": ["CLIN", "ENDO"], "GAP-12": ["SAFE|PK"], "GAP-13": ["CLIN"], "GAP-14": ["BIOM", "HIST"], "GAP-15": ["CLIN", "BIOM"],
             "GAP-16": ["CLIN", "ENDO", "SAFE"], "GAP-17": ["CLIN", "ENDO"], "GAP-18": ["COMP", "CLIN"], "GAP-19": ["PRO"], "GAP-20": ["CLIN", "PERS"],
             "GAP-21": ["HCRU"], "GAP-22": ["SAFE@LT"]}
ROLE_CREDIT = {"primary": 1.0, "secondary": 1.0, "reported": 1.0, "other": 0.6, "declared": 0.8, "indirect": 0.6, "direct": 1.0, "cohort": 0.7}
ROLE_RANK = {"primary": 0, "direct": 0, "reported": 0, "secondary": 1, "cohort": 2, "declared": 2, "indirect": 3, "other": 4}
HZ_RANK = {"unspecified": 0, "early (≤12 wk)": 1, "1 year (13–52 wk)": 2, "long term (>1 y)": 3}
t_end = table("study_endpoints", "Every registered outcome of J&J and competitor studies, with the evidence type(s) a keyword rule assigns. Correct a misclassified row in the Data Editor; the study profiles follow.", ["endpoint_id"])
t_prof = table("study_evidence_profile", "Derived: which evidence types each study registers (delivers) and which it does not, and how well that matches the gaps it is mapped to.", ["study_id"])
PROFILE = {}
def build_profile(sid, side, brand, indication, r, declared=None, own_rx=r"guselkumab|golimumab|jnj-?7|icotrokinra"):
    dom = {}
    def hit(code, role, hz, wk):
        d = dom.setdefault(code, {"role": role, "n": 0, "horizon": "unspecified", "max_weeks": None})
        d["n"] += 1
        if ROLE_RANK[role] < ROLE_RANK[d["role"]]: d["role"] = role
        if HZ_RANK[hz] > HZ_RANK[d["horizon"]]: d["horizon"], d["max_weeks"] = hz, wk
    n_out = 0
    if r is not None:
        for k, o in enumerate(r["outcomes_full"], 1):
            wk, hz = horizon(o["time_frame"]); n_out += 1
            f = t_end.add(PV, {"endpoint_id": f"{sid}-O{k:02d}", "study_id": sid, "side": side, "brand_id": brand, "role": o["role"],
                               "measure": o["measure"], "time_frame": o["time_frame"], "domains": "; ".join(classify_outcome(o["measure"])),
                               "max_weeks": wk, "horizon": hz, "classified_by": "keyword rule", "review_status": "auto (review)"},
                          src=["SRC-CTGOV"], der=("domains", "max_weeks", "horizon", "classified_by", "review_status"))
            for c in [x.strip() for x in (f["domains"] or "").split(";") if x.strip() in DNAME]:
                hit(c, o["role"], f["horizon"], f["max_weeks"])
        cmp_ = comparator_of(r, own_rx)
        if cmp_: hit("COMP", cmp_, "unspecified", None)
    for c in declared or []:
        hit(c, "indirect" if c == "COMP" else "declared", "unspecified", None)
    source = "registry outcomes" if n_out else ("declared (simulated study)" if declared else "no outcomes registered")
    delivers = [c for c, _, _ in DOMAINS if c in dom]
    prof = {"study_id": sid, "side": side, "brand_id": brand, "indication": indication, "outcome_source": source, "n_outcomes": n_out,
            "domains": dom, "delivers": "; ".join(delivers), "not_registered": "; ".join(c for c, _, _ in DOMAINS if c not in dom) if source != "no outcomes registered" else ""}
    PROFILE[sid] = prof
    return prof
def coverage(prof, gid):
    """share of what the gap needs that the study registers (credit by role; long-term needs need a >1 year timepoint)"""
    needs = GAP_NEEDS.get(gid) or []
    if not needs or prof["outcome_source"] == "no outcomes registered": return None, []
    got, missing = 0.0, []
    for nd in needs:
        alts, lt = nd.split("@")[0].split("|"), nd.endswith("@LT")   # "SAFE|PK": either answers the need
        c = next((a for a in alts if a in prof["domains"]), alts[0])
        d = prof["domains"].get(c)
        if not d: missing.append(" or ".join(DNAME[a] for a in alts)); continue
        cr = ROLE_CREDIT[d["role"]]
        if lt and d["horizon"] != "long term (>1 y)": cr *= 0.5; missing.append(DNAME[c] + " beyond 1 year")
        got += cr
    return round(got / len(needs), 2), missing
for sid, info in study_index.items():   # registry profile now; gap check after publications are linked (they show what was delivered)
    row = info["row"]
    build_profile(sid, "J&J", next((b for b in ("JNJ4804", "ICO", "TRE") if b in (row["brand_ids"] or "")), row["brand_ids"]), row["indication"], info["r"], DECLARED.get(sid))

# ---------------------------------------------------------------- milestones
MS_OFFSETS = {"DBL": 2, "TLR": 3}
public_ms = defaultdict(dict)
for nct, code, date, src in cp.PUBLIC_MILESTONES:
    public_ms[nct][code] = (date, src)
ms_counter = 0


def add_ms(sid, code, name, forecast, actual, basis, origin, src, critical=False, sim_fields=(), der_fields=()):
    global ms_counter
    ms_counter += 1
    fd = pdate(forecast) if isinstance(forecast, str) else forecast
    ad = pdate(actual) if isinstance(actual, str) else actual
    ref = ad or fd
    slip = rng.choice([0, 0, 0, 30, 45, 60, 90, 120, 150]) if ref else None
    base = ref - dt.timedelta(days=slip) if ref else None
    row = {"milestone_id": f"MS-{ms_counter:05d}", "study_id": sid, "code": code, "milestone": name,
           "baseline_date": iso(base), "forecast_date": iso(fd) if fd and not ad else None, "actual_date": iso(ad) if ad else None,
           "slippage_days": slip, "date_basis": basis, "is_critical_path": critical}
    t_ms.add(origin, row, src=src, sim=("baseline_date", "slippage_days") + tuple(sim_fields), der=tuple(der_fields))


for sid, info in study_index.items():
    r, row = info["r"], info["row"]
    if r is None:
        start = pdate(row["start_date"])
        add_ms(sid, "FPI" if row["evidence_class"] != "Evidence synthesis & modelling" else "START", "Start", start, None,
               "simulated plan", SI, ["SRC-SIM"])
        add_ms(sid, "PCD", "Primary completion / analysis complete", pdate(row["primary_completion_date"]), None, "simulated plan", SI, ["SRC-SIM"], True)
        continue
    if not info["jnj_sponsored"]:
        continue
    started = r["start_type"] == "actual"
    pcd_d, comp_d, start_d = pdate(r["pcd"]), pdate(r["completion"]), pdate(r["start"])
    add_ms(sid, "FPI", "First patient in (registry study start)", None if started else start_d, start_d if started else None,
           "registry start date (actual = first participant enrolled)" if started else "registry estimated start", PV, ["SRC-CTGOV"], False)
    tp = PRIMARY_TIMEPOINT_WK.get(sid, 12 if row["evidence_class"] == "Interventional" else 26)
    if pcd_d:
        lpi = pcd_d - dt.timedelta(weeks=tp)
        enrol_done = r["status"] in ("ACTIVE_NOT_RECRUITING", "COMPLETED", "TERMINATED") and r["n_type"] == "actual"
        if enrol_done and lpi >= TODAY:
            add_ms(sid, "LPI", "Last patient in", None, None,
                   "enrollment complete per registry (actual N); LPI date not public - registry PCD likely covers a later analysis", DE, ["SRC-CTGOV"], True)
        else:
            add_ms(sid, "LPI", "Last patient in", None if enrol_done else lpi, lpi if enrol_done else None,
                   f"derived: PCD minus primary timepoint ({tp} wk)", DE, ["SRC-CTGOV"], True)
        add_ms(sid, "PCD", "Primary completion", None if r["pcd_type"] == "actual" else pcd_d, pcd_d if r["pcd_type"] == "actual" else None,
               f"registry ({r['pcd_type']})", PV, ["SRC-CTGOV"], True)
        dbl = add_months(pcd_d, MS_OFFSETS["DBL"])
        if dbl > TODAY:
            add_ms(sid, "DBL", "Database lock", dbl, None, "derived: PCD + 2 months", DE, ["SRC-CTGOV"])
        elif r["pcd_type"] == "actual":
            add_ms(sid, "DBL", "Database lock", None, dbl, "derived: PCD + 2 months (assumed achieved)", DE, ["SRC-CTGOV"])
        pub = public_ms.get(sid, {})
        if "TLPR" in pub:
            add_ms(sid, "TLR", "Topline results (public)", None, pub["TLPR"][0], "public press release", PV, [pub["TLPR"][1]], True)
        elif row["evidence_class"] == "Interventional":
            tl = add_months(pcd_d, MS_OFFSETS["TLR"])
            add_ms(sid, "TLR", "Topline results", tl if tl > TODAY else None, tl if tl <= TODAY else None,
                   "derived: PCD + 3 months (no public topline date found)", DE, ["SRC-CTGOV"], True)
    if comp_d:
        add_ms(sid, "LPO", "Last patient out (registry study completion)", None if r["completion_type"] == "actual" else comp_d,
               comp_d if r["completion_type"] == "actual" else None, f"registry ({r['completion_type']})", PV, ["SRC-CTGOV"])
    for code, (date, src) in public_ms.get(sid, {}).items():
        if code == "TLPR":
            continue
        name = {"ABS1": "First congress presentation", "MS1": "Primary manuscript", "APP": "Approval / label (US)"}[code]
        add_ms(sid, code, name, None, date, "public source", PV, [src], code == "APP")

# ---------------------------------------------------------------- enrollment curves (simulated)
for sid, info in study_index.items():
    r = info["r"]
    if r is None or not info["jnj_sponsored"] or r["study_type_raw"] != "INTERVENTIONAL" or not r["n"] or r["n"] < 10:
        continue
    start, pcd = pdate(r["start"]), pdate(r["pcd"])
    if not start or not pcd or start > TODAY or start.year < 2022:
        continue
    tp = PRIMARY_TIMEPOINT_WK.get(sid, 12)
    lpi = pcd - dt.timedelta(weeks=tp)
    total = max(1, months_between(start, lpi))
    lag = rng.uniform(0.85, 1.05)  # actual pace relative to plan
    sites_total = max(r["n_sites"], 1)
    m, d = 0, start
    while d <= min(TODAY, lpi) and m <= total:
        frac = m / total
        planned = r["n"] * (3 * frac ** 2 - 2 * frac ** 3)
        actual = min(r["n"], planned * lag) if r["status"] == "RECRUITING" else min(r["n"], planned)
        screened = actual / rng.uniform(0.55, 0.7)
        t_enr.add(SI, {"study_id": sid, "period": d.strftime("%Y-%m"), "geo_id": "GLOBAL",
                       "sites_planned": sites_total, "sites_activated": round(sites_total * min(1, 0.15 + frac * 1.6)),
                       "patients_screened_cum": round(screened), "patients_randomized_cum": round(actual),
                       "patients_planned_cum": round(planned), "n_target": r["n"]},
                  src=["SRC-SIM", "SRC-CTGOV"], ver=("n_target",), note="curve shape simulated; n_target from registry")
        m += 1
        d = add_months(start, m)

# ---------------------------------------------------------------- funding (simulated)
# simulated cost model: interventional = N x cost per patient; RWE/synthesis = fixed range (USD millions)
COST_PER_PATIENT_K = {"Ph3": (110, 170), "Ph2b/3": (110, 170), "Ph3b": (90, 140), "Ph3 pediatric": (150, 250), "LTE": (40, 70),
                      "Ph4": (30, 60), "Ph2b": (100, 160), "Ph2a": (100, 160), "mechanistic": (80, 130)}
COST_FIXED_M = {"prospective observational cohort": (1.5, 6), "retrospective database": (0.2, 0.8), "registry": (0.5, 2),
                "cost-effectiveness": (0.2, 0.5), "NMA": (0.1, 0.3), "budget impact": (0.1, 0.25), "PRO / patient-preference (DCE)": (0.3, 0.8)}


def simulated_cost(row):
    if row["status"] in ("terminated", "withdrawn"):
        return rng.uniform(0.5, 3) * 1e6
    if row["study_type"] in COST_PER_PATIENT_K and row["n_planned_or_actual"]:
        lo, hi = COST_PER_PATIENT_K[row["study_type"]]
        return row["n_planned_or_actual"] * rng.uniform(lo, hi) * 1e3 + rng.uniform(2, 6) * 1e6
    lo, hi = COST_FIXED_M.get(row["study_type"], (1, 5))
    return rng.uniform(lo, hi) * 1e6


def funding_split(row):
    st, intent, cls = row["study_type"], row["regulatory_intent"], row["evidence_class"]
    if intent.startswith("registrational"):
        return [("F-RD", 100)]
    if st in ("Ph3b", "LTE", "Ph4", "mechanistic"):
        return [("F-GMAF", 60), ("F-USMAF", 20), ("F-EMEAMAF", 20)]
    if cls == "Evidence synthesis & modelling":
        return [("F-HEOR", 70), ("F-EMEAMAF", 30)]
    if cls == "Non-interventional (RWE)":
        return [(regional_funder(row), 70), ("F-GMAF", 30)]
    return [("F-GMAF", 100)]


REGION_OF = {"USA": "NA", "CAN": "NA", "JPN": "JPN", "CHN": "APAC", "KOR": "APAC", "AUS": "APAC", "TWN": "APAC", "HKG": "APAC",
             "BRA": "LATAM", "ARG": "LATAM", "MEX": "LATAM", "COL": "LATAM", "CHL": "LATAM", "PER": "LATAM"}
REGION_FUNDER = {"NA": "F-USMAF", "EMEA": "F-EMEAMAF", "APAC": "F-APACMAF", "JPN": "F-JPMAF", "LATAM": "F-LATAMMAF"}


def regional_funder(row):
    """Lead regional funder = region with most registry sites; sponsor-name fallback for studies without sites."""
    r = study_index.get(row["study_id"], {}).get("r")
    sites = Counter()
    for cname, v in (r["countries"] if r else {}).items():
        sites[REGION_OF.get(COUNTRY_ISO.get(cname, ""), "EMEA")] += v["sites"]
    if sites:
        return REGION_FUNDER[sites.most_common(1)[0][0]]
    sp = row["lead_sponsor"]
    if "Xian" in sp:
        return "F-APACMAF"
    if "K.K." in sp:
        return "F-JPMAF"
    return "F-EMEAMAF" if any(k in sp for k in ("Cilag", "GmbH", "A.G.", "Ireland")) else "F-USMAF"


BENEFIT = {"F-USMAF": "USA", "F-EMEAMAF": "EMEA", "F-APACMAF": "APAC", "F-JPMAF": "JPN"}
for sid, info in study_index.items():
    row = info["row"]
    if not info["jnj_sponsored"] or row["status"] in ("withdrawn",):
        continue
    total = round(simulated_cost(row), -3)
    prog = 1.0 if row["status"] in ("completed",) else (0.0 if row["status"] in ("planned", "proposed", "not yet recruiting") else rng.uniform(0.3, 0.9))
    s, e = pdate(row["start_date"]) or TODAY, pdate(row["completion_date"] or row["primary_completion_date"] or "") or add_months(TODAY, 24)
    years = list(range(s.year, max(e.year, s.year) + 1))
    for fid, share in funding_split(row):
        committed = total * share / 100
        fy = {str(y): round(committed / len(years)) for y in years}
        overrun = rng.choice([0, 0, 0, 0.05, 0.1, 0.25])
        benefit = "GLOBAL" if fid in ("F-GMAF", "F-RD", "F-HEOR") else BENEFIT.get(fid, "GLOBAL")
        benefit_extra = rng.choice(["", "; EMEA", "; USA", "; APAC"]) if fid in ("F-USMAF", "F-EMEAMAF") else ""
        t_fundrow.add(SI, {"study_id": sid, "funder_id": fid, "funding_role": "lead funder" if share == max(x[1] for x in funding_split(row)) else "co-funder",
                           "share_pct": share, "committed_usd": round(committed), "spent_to_date_usd": round(committed * prog),
                           "forecast_at_completion_usd": round(committed * (1 + overrun)),
                           "approval_status": "approved" if row["status"] not in ("proposed",) else "in governance",
                           "governance_body": "Global Evidence Council" if fid in ("F-GMAF", "F-RD", "F-HEOR") else f"{fid[2:].replace('MAF', '')} Evidence Committee",
                           "benefiting_geo_ids": benefit + benefit_extra, "fiscal_year_split": fy}, src=["SRC-SIM"])

# ---------------------------------------------------------------- RWE detail
for sid, info in study_index.items():
    row, r = info["row"], info["r"]
    if row["evidence_class"] != "Non-interventional (RWE)":
        continue
    prospective = "prospective" in row["study_type"] or (r and "prospective" in r["time_perspective"].lower())
    src_type = "prospective cohort" if prospective else rng.choice(["claims", "EHR", "linked claims-EHR"])
    t_rwe.add(SI, {"study_id": sid, "data_source_type": src_type,
                   "data_source_names": "site-collected eCRF" if prospective else rng.choice(["Optum Clinformatics", "IQVIA PharMetrics", "national IBD registry"]),
                   "n_expected": row["n_planned_or_actual"], "follow_up_months": rng.choice([12, 24, 36]),
                   "comparator_cohorts": rng.choice(["none (single-arm)", "risankizumab", "ustekinumab / biosimilar", "vedolizumab"]),
                   "analytic_method": rng.choice(["descriptive", "PSM", "IPTW", "target-trial emulation"]),
                   "outcomes": "persistence; steroid-free remission; dose escalation; HCRU",
                   "protocol_registration": row["nct_id"] or "EU PAS (to be registered)",
                   "first_data_cut": iso(add_months(pdate(row["start_date"]) or TODAY, 12))},
              src=["SRC-SIM"] + (["SRC-CTGOV"] if r else []),
              ver=("n_expected", "protocol_registration") if r else (), der=("first_data_cut",))

# ---------------------------------------------------------------- baseline + safety placeholders (simulated)
for sid in ["NCT04033445", "NCT03466411", "NCT05197049", "NCT05528510", "NCT05347095", "NCT06049017", "NCT07196748"]:
    t_base.add(SI, {"study_id": sid, "mean_age": round(rng.uniform(36, 44), 1), "pct_female": round(rng.uniform(38, 50), 1),
                    "mean_disease_duration_yrs": round(rng.uniform(6, 11), 1), "pct_bio_naive": round(rng.uniform(40, 60), 1),
                    "pct_prior_tnf_failure": round(rng.uniform(30, 50), 1), "pct_prior_jak_failure": round(rng.uniform(0, 8), 1),
                    "pct_multi_class_failure": round(rng.uniform(10, 25), 1), "pct_concomitant_steroids": round(rng.uniform(30, 45), 1)},
               src=["SRC-SIM"], note="PLACEHOLDER: replace with published baseline tables")
    t_saf.add(SI, {"study_id": sid, "pct_any_ae": round(rng.uniform(45, 70), 1), "pct_sae": round(rng.uniform(3, 9), 1),
                   "pct_ae_discontinuation": round(rng.uniform(1.5, 5), 1), "serious_infections_per_100py": round(rng.uniform(0.8, 3), 2),
                   "malignancy_per_100py": round(rng.uniform(0.1, 0.6), 2)}, src=["SRC-SIM"], note="PLACEHOLDER: replace with published safety data")

# ---------------------------------------------------------------- results (public)
for i, (nct, ep, wk, arm, comp, rate, crate, pop, prim, src, origin) in enumerate(cp.RESULTS, 1):
    t_res.add(origin, {"result_id": f"RES-{i:03d}", "study_id": nct, "endpoint": ep, "timepoint_wk": wk, "arm": arm,
                       "comparator_arm": comp, "rate_pct": rate, "comparator_rate_pct": crate,
                       "delta_pct": round(rate - crate, 1) if crate is not None else None, "population_set": pop,
                       "is_primary": prim, "caveat": "cross-trial comparison, not head-to-head" if comp not in ("Ustekinumab", "Guselkumab mono") else ""},
              src=[src], der=("delta_pct", "caveat"))

# =============================================================== evidence gaps (+ derived metrics)
t_gap = table("evidence_gaps", "SIMULATED evidence gaps with derived criticality, coverage and closure (recomputed by the build).",
              ["gap_id", "brand_id", "kq_id"])
t_out = table("evidence_outputs", "Publications / communications. Public outputs are real; planned outputs are simulated.",
              ["output_id", "study_id"])

# outputs first (needed for realised closure)
outputs = []
for oid, nct, an, pubt, venue, date, title, peer, src, origin in cp.OUTPUTS_PUBLIC:
    outputs.append(dict(output_id=oid, study_id=nct, analysis_type=an, analysis_prespecified=an != "Post-hoc analysis",
                        publication_type=pubt, peer_review_status=peer, target_venue_id=venue, title=title, status="published" if "manuscript" in pubt.lower() else "presented",
                        planned_date=None, actual_date=date, _origin=origin, _src=[src]))
PLANNED = [  # study, analysis, publication type, venue, planned date, status, peer, title
    ("NCT05347095", "Primary analysis", "Primary manuscript", "J-GASTRO", "2027-02", "in development", "peer-reviewed journal", "FUZION CD primary manuscript"),
    ("NCT05347095", "Primary analysis", "Encore (regional)", "C-UEGW26", "2026-10-18", "accepted", "peer-reviewed abstract", "FUZION CD encore"),
    ("NCT05347095", "Secondary analysis", "Poster", "C-ECCO27", "2027-03-04", "planned", "peer-reviewed abstract", "FUZION CD MRI outcomes"),
    ("NCT05242471", "Primary analysis", "Primary manuscript", "J-LANCET", "2027-04", "in development", "peer-reviewed journal", "DUET-CD primary manuscript"),
    ("NCT05242484", "Primary analysis", "Primary manuscript", "J-LGH", "2027-05", "in development", "peer-reviewed journal", "DUET-UC primary manuscript"),
    ("NCT05242484", "Subgroup analysis", "Oral presentation", "C-ECCO27", "2027-03-05", "planned", "peer-reviewed abstract", "DUET-UC multi-class refractory subgroup"),
    ("NCT06049017", "Primary analysis", "Primary manuscript", "J-LGH", "2026-12", "submitted", "peer-reviewed journal", "ANTHEM-UC primary manuscript"),
    ("NCT07196748", "Trial in progress", "Poster", "C-UEGW26", "2026-10-19", "accepted", "peer-reviewed abstract", "ICONIC-UC design and rationale"),
    ("NCT07196722", "Trial in progress", "Poster", "C-ACG26", "2026-10-12", "accepted", "peer-reviewed abstract", "ICONIC-CD design and rationale"),
    ("NCT07196748", "Baseline characteristics", "Poster", "C-DDW27", "2027-05-16", "planned", "peer-reviewed abstract", "ICONIC-UC baseline characteristics"),
    ("NCT07499232", "Trial in progress", "Poster", "C-ECCO27", "2027-03-04", "planned", "peer-reviewed abstract", "CHARGE design (GUS vs RZB)"),
    ("NCT06408935", "Primary analysis", "Late-breaking oral", "C-UEGW27", "2027-10", "planned", "peer-reviewed abstract", "REASON transmural healing primary"),
    ("NCT06408935", "Baseline characteristics", "Poster", "C-ECCO27", "2027-03-05", "planned", "peer-reviewed abstract", "REASON baseline IUS/MRE characteristics"),
    ("NCT05528510", "Long-term extension", "Oral presentation", "C-UEGW26", "2026-10-19", "accepted", "peer-reviewed abstract", "ASTRO week 96"),
    ("NCT03466411", "Long-term extension", "Poster", "C-ACG26", "2026-10-12", "accepted", "peer-reviewed abstract", "GALAXI LTE 3-year outcomes"),
    ("NCT03466411", "Post-hoc analysis", "Poster", "C-UEGW26", "2026-10-19", "accepted", "peer-reviewed abstract", "GALAXI post-hoc: endoscopic remission by prior therapy"),
    ("NCT04033445", "Long-term extension", "Oral presentation", "C-ECCO27", "2027-03-05", "planned", "peer-reviewed abstract", "QUASAR LTE 3-year outcomes"),
    ("NCT05197049", "Long-term extension", "Poster", "C-DDW27", "2027-05-16", "planned", "peer-reviewed abstract", "GRAVITI week 96"),
    ("NCT07102368", "Trial in progress", "Poster", "C-ECCO27", "2027-03-04", "planned", "peer-reviewed abstract", "GORGEOUS RWE design"),
    ("NCT07102368", "RWE data cut", "Poster", "C-UEGW27", "2027-10", "planned", "peer-reviewed abstract", "GORGEOUS first data cut"),
    ("NCT07245394", "RWE data cut", "Poster", "C-DDW27", "2027-05-17", "planned", "peer-reviewed abstract", "SHIFT-IBD interim (external)"),
    ("SIM-RWE-01", "RWE data cut", "Poster", "C-ISPOR27", "2027-05-10", "planned", "peer-reviewed abstract", "US persistence after ustekinumab switch"),
    ("SIM-RWE-01", "RWE data cut", "Primary manuscript", "J-APT", "2028-01", "planned", "peer-reviewed journal", "US persistence manuscript"),
    ("SIM-HEOR-01", "HEOR / economic", "HTA dossier", "", "2027-02", "in development", "not peer-reviewed", "EU5 cost-effectiveness dossier"),
    ("SIM-ITC-01", "ITC / NMA", "Poster", "C-ECCO27", "2027-03-05", "planned", "peer-reviewed abstract", "Oral advanced-therapy NMA in UC (interim)"),
    ("SIM-DCE-01", "Secondary analysis", "Poster", "C-DDW27", "2027-05-17", "planned", "peer-reviewed abstract", "Oral vs SC preference DCE"),
    ("NCT05923073", "Baseline characteristics", "Poster", "C-DDW27", "2027-05-16", "planned", "peer-reviewed abstract", "MACARONI-23 baseline (pediatric CD)"),
]
for i, (sid, an, pubt, venue, date, status, peer, title) in enumerate(PLANNED, 1):
    outputs.append(dict(output_id=f"OUT-S{i:03d}", study_id=sid, analysis_type=an, analysis_prespecified=an != "Post-hoc analysis",
                        publication_type=pubt, peer_review_status=peer, target_venue_id=venue, title=title, status=status,
                        planned_date=date, actual_date=None, _origin=SI, _src=["SRC-SIM"]))
# add simulated 2027 UEGW venue used above
t_tmp_venue_extra = ("C-UEGW27", "UEG Week 2027", "congress", "EMEA", "2027-10", "2027-10", "", 1, "SRC-SIM", SI)

# ---------------------------------------------------------------- real publications -> studies & gaps (derived)
PUBDATA_FILE = ROOT / "data" / "raw" / "pubs" / "processed.json"
PUBDATA = json.loads(PUBDATA_FILE.read_text()) if PUBDATA_FILE.exists() else {"publications": [], "sov_congress": [], "sov_journal": [], "sov_analysis": [], "symposia": []}
PUBLIST = PUBDATA["publications"]
JNJ_PUB = {"TRE", "ICO", "JNJ4804"}
for _p in PUBLIST:
    _p["_bt"] = _p["brands_title"] if isinstance(_p["brands_title"], list) else [b for b in str(_p["brands_title"]).split("; ") if b]
    _p["_date"] = pdate(_p.get("date") or "") or (dt.date(int(_p["year"]), 7, 1) if str(_p.get("year", "")).isdigit() else None)

# distinctive trial names only (generic words such as REASON/VOICE would create false links)
TRIAL_LINKS = [
    (r"quasar[\s-]*jr", "NCT06260163"), (r"\bquasar\b", "NCT04033445"), (r"\bgalaxi", "NCT03466411"), (r"\bgraviti\b", "NCT05197049"),
    (r"\bastro\b", "NCT05528510"), (r"\bfuzion\b", "NCT05347095"), (r"\bvega\b", "NCT03662542"), (r"\banthem", "NCT06049017"),
    (r"iconic[\s-]*uc", "NCT07196748"), (r"iconic[\s-]*cd", "NCT07196722"), (r"\bmacaroni", "NCT05923073"), (r"\btrilogy\b", "NCT06663332"),
    (r"\bgorgeous\b", "NCT07102368"), (r"shift[\s-]*ibd", "NCT07245394"), (r"\bgusto", "NCT07242248"),
]


def link_studies(p):
    t = p["title"].lower()
    out = [sid for rx, sid in TRIAL_LINKS if re.search(rx, t)]
    if "NCT06260163" in out and "NCT04033445" in out:
        out.remove("NCT04033445")
    if re.search(r"\bduet\b|jnj-?78934804|jnj-?4804|co-antibody", t):
        out.append("NCT05242471" if "crohn" in t else "NCT05242484")
    elif re.search(r"guselkumab and golimumab|golimumab and guselkumab|combination.*golimumab", t) and "colitis" in t:
        out.append("NCT03662542")  # unnamed GUS+GOL combination in UC = VEGA (phase 2a)
    if not out and "ICO" in p["_bt"] and "colitis" in t and re.search(r"phase 2b|week (12|28)|dose-ranging", t):
        out.append("NCT06049017")  # icotrokinra UC phase 2b without the trial name = ANTHEM-UC
    return list(dict.fromkeys(out))


# gap -> (brands required in title, title regex, analysis types that also qualify)
GAP_TOPICS = {
    "GAP-01": ({"TRE"}, r"risankizumab", set()),
    "GAP-02": ({"TRE"}, r"(colitis).*(versus|\bvs\b|compar|network|indirect|maic|meta-analy)|(versus|\bvs\b|compar|network|indirect|maic|meta-analy).*(colitis)", set()),
    "GAP-03": ({"TRE"}, r"transmural|ultraso|\bius\b|enterograph|\bmre\b|bowel wall", set()),
    "GAP-04": ({"TRE"}, r"fistul|perianal|fuzion", set()),
    "GAP-05": ({"TRE"}, r"pediatric|paediatric|children|adolescen|quasar[\s-]*jr|macaroni", set()),
    "GAP-06": ({"TRE"}, r"long[- ]term extension|\blte\b|week (9\d|1\d\d)|\b(2|3|4|two|three|four)[- ]year", {"Long-term extension"}),
    "GAP-07": ({"TRE"}, r"(real[- ]world|real-life|retrospective|cohort).*(ustekinumab|switch)|(ustekinumab|switch).*(real[- ]world|real-life|retrospective|cohort)", {"RWE"}),
    "GAP-08": ({"TRE"}, r"cost|economic|budget|projected|projection|disease model", {"HEOR / economic"}),
    "GAP-09": ({"TRE", "JNJ4804"}, r"\bduet\b|jnj-?78934804|co-antibody|golimumab|refractory|multi-?class", set()),
    "GAP-10": ({"TRE"}, r"subcutaneous.*(real[- ]world|preference|persistence|patient)|(real[- ]world|preference|persistence).*subcutaneous", set()),
    "GAP-11": ({"TRE"}, r"pouchitis|pouch", set()),
    "GAP-12": ({"TRE"}, r"pregnan|lactat|breast milk|maternal", set()),
    "GAP-13": ({"TRE"}, r"japan|china|chinese|east asian|korea|\basia", set()),
    "GAP-14": ({"TRE"}, r"cd64|mechanis|myeloid|molecular|transcript|single[- ]cell", set()),
    "GAP-15": ({"TRE"}, r"dose|dosing|optimi[sz]|treat[- ]to[- ]target|interval|escalat", set()),
    "GAP-16": ({"ICO"}, r"colitis", set()),
    "GAP-17": ({"ICO"}, r"crohn", set()),
    "GAP-18": ({"ICO"}, r"\bjak|s1p|etrasimod|ozanimod|upadacitinib|obefazimod|network|indirect|compar", set()),
    "GAP-19": ({"ICO", "TRE"}, r"preference|oral versus|oral vs", set()),
    "GAP-20": ({"ICO"}, r"sequenc|guselkumab", set()),
    "GAP-21": ({"ICO"}, r"cost|economic|budget", set()),
    "GAP-22": ({"ICO"}, r"safety|long[- ]term", set()),
}
# competitor voice on the same topic (brand-agnostic topics only)
COMP_TOPIC = {g: rx for g, (b, rx, _) in GAP_TOPICS.items() if g in ("GAP-03", "GAP-04", "GAP-05", "GAP-06", "GAP-10", "GAP-11", "GAP-12", "GAP-13", "GAP-15", "GAP-19")}


def pub_weight(p):
    pt, an = p["presentation_type"], p["analysis_type"]
    if an in ("Case report", "Commentary", "Narrative review"):
        return 0.02, "other"
    if p["kind"] == "journal":
        return (0.35, "journal") if pt in ("Original article", "Clinical trial report", "Systematic review / meta-analysis", "Article (not PubMed-indexed)") else (0.05, "other")
    return (0.15 if pt in ("Oral", "Digital oral") else 0.07), "congress"


pub_by_gap, pub_by_study = defaultdict(list), defaultdict(list)
for p in PUBLIST:
    p["linked_study_ids"] = link_studies(p) if set(p["_bt"]) & JNJ_PUB else []
    for sid in p["linked_study_ids"]:
        pub_by_study[sid].append(p)
    gl = []
    for g, (brands, rx, ans) in GAP_TOPICS.items():
        if set(p["_bt"]) & brands and (re.search(rx, p["title"], re.I) or p["analysis_type"] in ans):
            gl.append(g)
            pub_by_gap[g].append(p)
    p["linked_gap_ids"] = gl

comp_voice = Counter()
for p in PUBLIST:
    if set(p["_bt"]) & JNJ_PUB or not p["_bt"] or not p["_date"] or p["_date"] < add_months(TODAY, -12):
        continue
    for g, rx in COMP_TOPIC.items():
        if re.search(rx, p["title"], re.I):
            comp_voice[g] += 1


# some gaps can only be closed by a specific kind of evidence; published items of other kinds count only up to a cap
GAP_PUB_CAP = {
    "GAP-01": (0.35, "needs a randomised head-to-head (CHARGE); MAIC / switch data are supportive only"),
    "GAP-02": (0.6, "indirect comparisons support HTA but not guideline-grade head-to-head claims"),
    "GAP-07": (0.8, "independent RWE is strong but not J&J-controlled in design or populations"),
    "GAP-08": (0.5, "disease/remission models are not a cost-effectiveness analysis vs biosimilar ustekinumab"),
    "GAP-09": (0.5, "phase 2b DUET data; phase 3 DUET ENCORE required for label"),
    "GAP-10": (0.5, "trial data on SC regimens; real-world persistence and preference still needed"),
    "GAP-15": (0.6, "trial dose-regimen analyses; treat-to-target / optimisation strategy data still needed"),
    "GAP-16": (0.4, "phase 2b ANTHEM-UC data; phase 3 ICONIC-UC required"),
    "GAP-17": (0.4, "no phase 3 CD data yet"),
    "GAP-22": (0.4, "long-term IBD safety needs ICONIC long-term data"),
}


def published_closure(g):
    cong = jour = 0.0
    for p in pub_by_gap[g]:
        w, kind = pub_weight(p)
        if kind == "congress":
            cong += w
        else:
            jour += w
    return min(GAP_PUB_CAP.get(g, (1.0, ""))[0], min(0.6, cong) + jour)  # congress-only evidence caps at 60%


gap_rows = {}
# outputs only count toward a gap when their analysis type can answer it (configuration)
GAP_ANALYSIS_FILTER = {"GAP-06": {"Long-term extension"}, "GAP-07": {"RWE data cut"},
                       "GAP-10": {"RWE data cut", "Secondary analysis"}, "GAP-12": {"RWE data cut", "Safety update"}}

# ---- evidence depth, part 2: what publications already report ("delivered"), then gap fit = min(analyst mapping, endpoint coverage)
LT_RX = r"\b([2-9]|10)[- ]year|\byear [2-9]\b|long-term|\bweek (9[6-9]|1\d\d|2\d\d|3\d\d)\b|\b(96|1\d\d|2\d\d|3\d\d)[- ]week"
for sid, prof in PROFILE.items():
    if prof["side"] != "J&J": continue
    rep = {}
    for p in pub_by_study.get(sid, []):
        lt = bool(re.search(LT_RX, p["title"], re.I))
        for c in classify_outcome(p["title"]) + (["CLIN", "SAFE"] if re.search(r"efficacy and safety", p["title"], re.I) else []):
            r_ = rep.setdefault(c, {"n": 0, "long_term": False}); r_["n"] += 1; r_["long_term"] |= lt
    prof["reported_in_publications"] = rep
    for c, r_ in rep.items():   # published evidence counts as delivered, whatever the registry listed
        d = prof["domains"].setdefault(c, {"role": "reported", "n": 0, "horizon": "unspecified", "max_weeks": None})
        if ROLE_RANK.get(d["role"], 9) > ROLE_RANK["reported"]: d["role"] = "reported"
        if r_["long_term"]: d["horizon"] = "long term (>1 y)"
    if rep and prof["outcome_source"] == "no outcomes registered": prof["outcome_source"] = "publications only"
    prof["delivers"] = "; ".join(c for c, _, _ in DOMAINS if c in prof["domains"])
    prof["not_registered"] = "; ".join(c for c, _, _ in DOMAINS if c not in prof["domains"]) if prof["outcome_source"] != "no outcomes registered" else ""
for sid, info in study_index.items():
    row = info["row"]
    prof = PROFILE[sid]
    checks, capped = {}, []
    trow = next(x for x in t_study.rows if x["fields"] is row)
    manual_fit = trow["prov"].get("gap_fit") == MN
    for g, fit in list(row["gap_fit"].items()):
        cov, miss = coverage(prof, g)
        eff = fit if cov is None or manual_fit else round(min(fit, cov), 2)
        checks[g] = {"analyst_fit": fit, "endpoint_coverage": cov, "missing": miss, "effective_fit": eff}
        if eff < fit: capped.append(g); row["gap_fit"][g] = eff
    prof["gap_checks"] = checks
    if capped:   # gap fit now = min(analyst mapping, what the registered endpoints can answer)
        trow["prov"]["gap_fit"] = DE
        trow["note"] = (trow["note"] + " | " if trow["note"] else "") + "gap fit capped by registered endpoints: " + ", ".join(capped)

realised = defaultdict(float)
for o in outputs:
    for g, fit in study_index.get(o["study_id"], {"row": {"gap_fit": {}}})["row"]["gap_fit"].items():
        if o["status"] in ("published", "presented") and o["analysis_type"] in GAP_ANALYSIS_FILTER.get(g, {o["analysis_type"]}):
            realised[g] += fit * closure_weight(o["peer_review_status"], o["analysis_type"])

for gid, bid, kq, title, gtype, segs, geos, stks, comp_has, sc, comp_ref in GAPS:
    stk, align, unc, hta, urg = sc
    gcs = min(5, 0.25 * stk + 0.25 * align + 0.15 * unc + 0.15 * hta + 0.20 * urg + (1 if comp_has else 0))
    closing = [(sid, info["row"]) for sid, info in study_index.items() if gid in info["row"]["gap_fit"]]
    prod = 1.0
    for sid, row in closing:
        prod *= 1 - row["gap_fit"][gid] * row["probability_of_success"]
    coverage_studies = 1 - prod if closing else 0.0
    pubc = published_closure(gid)
    coverage = 1 - (1 - coverage_studies) * (1 - min(0.9, pubc))  # evidence already public counts toward closure
    jp = pub_by_gap[gid]
    latest_pub = max((p["_date"] for p in jp if p["_date"]), default=None)
    # expected close = earliest future (PCD + 6 months) among closing studies; else latest past one
    close_dates = sorted(add_months(pdate(row["primary_completion_date"]), 6) for _, row in closing if pdate(row["primary_completion_date"] or ""))
    future = [d for d in close_dates if d >= TODAY]
    exp_close = future[0] if future else (close_dates[-1] if close_dates else None)
    real = min(1.0, realised[gid] + pubc)
    if pubc >= 0.6 and latest_pub:  # evidence largely public already
        exp_close = min(exp_close, latest_pub) if exp_close else latest_pub
    status = ("closed" if real >= 0.9 else "partially closed" if real >= 0.3 else "open-orphan" if not closing else "in progress")
    n_j = sum(1 for p in jp if pub_weight(p)[1] == "journal")
    n_c = sum(1 for p in jp if pub_weight(p)[1] == "congress")
    evidence_note = (f"{n_j} journal + {n_c} congress items name {'/'.join(sorted({b for p in jp for b in p['_bt'] if b in JNJ_PUB}))} on this topic"
                     + (f"; latest {latest_pub.strftime('%b %Y')}" if latest_pub else "") if jp else "No J&J publications on this topic")
    if comp_voice[gid] and not jp:
        evidence_note += f"; competitors published {comp_voice[gid]} items in the last 12 months (J&J silent)"
    row = {"gap_id": gid, "brand_id": bid, "kq_id": kq, "title": title, "gap_type": gtype, "care_segment_ids": segs, "geo_ids": geos,
           "stakeholder_ids": stks, "competitor_has_evidence": comp_has, "competitor_evidence_ref": comp_ref,
           "stakeholder_importance": stk, "imperative_alignment": align, "uncertainty_magnitude": unc,
           "hta_guideline_relevance": hta, "urgency": urg,
           "gap_criticality_score": round(gcs, 2), "closing_study_ids": "; ".join(s for s, _ in closing),
           "planned_coverage_pct": round(coverage * 100), "realised_closure_pct": round(real * 100),
           "expected_close_date": iso(exp_close), "status": status,
           "coverage_from_studies_pct": round(coverage_studies * 100), "published_closure_pct": round(pubc * 100),
           "pubs_jnj_journal": n_j, "pubs_jnj_congress": n_c, "latest_pub_date": iso(latest_pub) if latest_pub else None,
           "competitor_pubs_12m": comp_voice[gid], "evidence_on_record": evidence_note,
           "publication_cap_reason": GAP_PUB_CAP.get(gid, (1.0, ""))[1],
           "linked_pub_ids": "; ".join(p["pub_id"] for p in sorted(jp, key=lambda p: p["_date"] or dt.date(1900, 1, 1), reverse=True)[:25]),
           "needed_domains": "; ".join(GAP_NEEDS.get(gid, []))}
    gap_rows[gid] = row
    t_gap.add(SI, row, src=["SRC-SIM"] + (["SRC-CTGOV"] if comp_ref else []),
              der=("gap_criticality_score", "closing_study_ids", "planned_coverage_pct", "realised_closure_pct", "expected_close_date", "status",
                   "coverage_from_studies_pct", "published_closure_pct", "pubs_jnj_journal", "pubs_jnj_congress", "latest_pub_date",
                   "competitor_pubs_12m", "evidence_on_record", "linked_pub_ids", "publication_cap_reason"),
              ver=("competitor_evidence_ref",) if comp_ref else (), ref=("needed_domains",))
    if t_gap.rows[-1]["prov"].get("gap_criticality_score") != MN:  # recompute from edited inputs
        num = lambda k: float(row.get(k) or 0)
        row["gap_criticality_score"] = round(min(5, 0.25 * num("stakeholder_importance") + 0.25 * num("imperative_alignment") + 0.15 * num("uncertainty_magnitude")
                                                 + 0.15 * num("hta_guideline_relevance") + 0.20 * num("urgency") + (1 if row.get("competitor_has_evidence") in (True, "true", "True", 1) else 0)), 2)

for o in outputs:
    gaps = study_index.get(o["study_id"], {"row": {"gap_fit": {}}})["row"]["gap_fit"]
    row = {k: v for k, v in o.items() if not k.startswith("_")}
    row["gap_ids"] = "; ".join(gaps)
    row["gap_closure_weight"] = closure_weight(o["peer_review_status"], o["analysis_type"])
    row["is_competitor_output"] = o["study_id"] == "NCT04524611"
    der = ("gap_ids", "gap_closure_weight", "is_competitor_output")
    t_out.add(o["_origin"], row, src=o["_src"], der=der)

# ERI per imperative (derived)
kq_to_si = {k: s for k, s, _, _ in KQS}
si_req = {iid: add_months(TODAY, {"0-12m": 12, "1-3y": 30, "3-5y": 54}[hor]) for iid, _, _, _, _, hor, _ in IMPERATIVES}
eri = {}
for iid in si_req:
    num = den = 0
    for g in gap_rows.values():
        if kq_to_si[g["kq_id"]] != iid:
            continue
        w = g["gap_criticality_score"]
        ec = pdate(g["expected_close_date"] or "")
        timeliness = 1 if ec and ec <= si_req[iid] else (max(0, 1 - months_between(si_req[iid], ec) / 24) if ec else 0)
        num += w * g["planned_coverage_pct"] / 100 * timeliness
        den += w
    eri[iid] = round(100 * num / den) if den else None
for row in t_si.rows:
    f = row["fields"]
    f["evidence_readiness_index"] = eri[f["imperative_id"]]
    f["status_rag"] = None if eri[f["imperative_id"]] is None else ("green" if eri[f["imperative_id"]] >= 70 else "amber" if eri[f["imperative_id"]] >= 45 else "red")
    row["prov"]["evidence_readiness_index"] = DE
    row["prov"]["status_rag"] = DE

# primary papers published before the 3-year search window (public knowledge, not re-checked)
PRIOR_PAPERS = {"NCT03662542": "Feagan BG et al., Lancet Gastroenterol Hepatol 2023 (VEGA primary results; PMID 36738762)"}
# study publication status from real publications (derived)
for srow in t_study.rows:
    f = srow["fields"]
    ps = pub_by_study.get(f["study_id"], [])
    jr = [p for p in ps if pub_weight(p)[1] == "journal"]
    cg = [p for p in ps if p["kind"] == "congress"]
    first = min((p["_date"] for p in ps if p["_date"]), default=None)
    first_cong = min((p["_date"] for p in cg if p["_date"]), default=None)
    f.update({"pubs_total": len(ps), "pubs_journal": len(jr), "pubs_congress": len(cg), "first_public_date": iso(first) if first else None,
              "first_congress_date": iso(first_cong) if first_cong else None,
              "peer_reviewed_paper": any(p["analysis_type"] in ("Trial analysis (primary / secondary)", "Long-term extension", "Subgroup analysis", "Post-hoc analysis", "Pooled analysis") for p in jr),
              "linked_pub_ids": "; ".join(p["pub_id"] for p in sorted(ps, key=lambda p: p["_date"] or dt.date(1900, 1, 1), reverse=True)[:40]),
              "prior_primary_paper": PRIOR_PAPERS.get(f["study_id"], "")})
    for k in ("pubs_total", "pubs_journal", "pubs_congress", "first_public_date", "first_congress_date", "peer_reviewed_paper", "linked_pub_ids"):
        srow["prov"][k] = DE
    srow["prov"]["prior_primary_paper"] = PV if f["prior_primary_paper"] else DE
    if f["prior_primary_paper"]:
        srow["src"].append("SRC-VEGA-LGH")
        f["peer_reviewed_paper"] = True

# simulated planned outputs: flag where a real publication of the same kind already exists
AN_FAMILY = {"Long-term extension": "lte", "Post-hoc analysis": "sec", "Secondary analysis": "sec", "Subgroup analysis": "sec", "Primary analysis": "prim",
             "Trial analysis (primary / secondary)": "prim", "RWE data cut": "rwe", "RWE": "rwe", "Trial in progress": "tip", "Trial in progress / design": "tip",
             "Baseline characteristics": "base", "Interim analysis": "int"}
for orow in t_out.rows:
    f = orow["fields"]
    if orow["prov"].get("title") != SI or f.get("status") in ("published", "presented"):
        continue
    fam = AN_FAMILY.get(f["analysis_type"])
    want_journal = "manuscript" in f["publication_type"].lower()
    eq = [p for p in pub_by_study.get(f["study_id"], []) if AN_FAMILY.get(p["analysis_type"]) == fam and (pub_weight(p)[1] == "journal") == want_journal]
    f["real_equivalent_pub_ids"] = "; ".join(p["pub_id"] for p in eq[:5])
    orow["prov"]["real_equivalent_pub_ids"] = DE

# study impact score + cost per impact point (derived)
fund_by_study = defaultdict(float)
for fr in t_fundrow.rows:
    fund_by_study[fr["fields"]["study_id"]] += fr["fields"]["committed_usd"]
si_prio = {iid: 1 / prio for iid, _, _, _, _, _, prio in IMPERATIVES}
for srow in t_study.rows:
    f = srow["fields"]
    imps = {kq_to_si[gap_rows[g]["kq_id"]] for g in f["gap_fit"] if g in gap_rows}
    sis = f["probability_of_success"] * sum(f["impact_if_positive_1to5"] * si_prio[i] for i in imps)
    f["study_impact_score"] = round(sis, 2)
    f["total_cost_usd"] = round(fund_by_study.get(f["study_id"], 0)) or None
    f["cost_per_impact_point_usd"] = round(f["total_cost_usd"] / sis) if f["total_cost_usd"] and sis else None
    for k in ("study_impact_score", "total_cost_usd", "cost_per_impact_point_usd"):
        srow["prov"][k] = DE

# =============================================================== dissemination
t_venue = table("venues", "Congresses and journals. Dates for ACG/UEGW 2026, ECCO/DDW 2027 verified; others simulated.", ["venue_id"])
for vid, name, typ, reg, s, e, city, tier, src, origin in cp.VENUES + [t_tmp_venue_extra]:
    sd = pdate(s)
    t_venue.add(origin, {"venue_id": vid, "name": name, "type": typ, "region": reg, "start_date": s, "end_date": e, "city": city,
                         "tier": tier, "abstract_deadline": iso(add_months(sd, -5)) if sd and typ == "congress" else None,
                         "late_breaker_deadline": iso(add_months(sd, -2)) if sd and typ == "congress" else None},
                src=[src] if src else [], sim=("abstract_deadline", "late_breaker_deadline"), ref=("tier",))

t_msg = table("key_messages", "Scientific key messages. Statements reflect public data; MLR status is simulated.", ["msg_id", "brand_id"])
for mid, bid, pillar, stmt, outs in [
    ("MSG-01", "TRE", "efficacy", "In GALAXI 2/3, guselkumab showed higher week-48 endoscopic remission than ustekinumab.", "OUT-P003"),
    ("MSG-02", "TRE", "convenience", "Guselkumab offers SC or IV induction in UC and CD (fully SC regimen in UC and CD).", "OUT-P004; OUT-P006"),
    ("MSG-03", "TRE", "special populations", "In FUZION CD, guselkumab achieved higher combined fistula remission than placebo at week 24.", "OUT-P008"),
    ("MSG-04", "TRE", "deep healing", "Guselkumab demonstrated endoscopic response with SC induction in CD (GRAVITI).", "OUT-P004"),
    ("MSG-05", "ICO", "efficacy", "In ANTHEM-UC, once-daily oral icotrokinra met its primary endpoint of clinical response at week 12.", "OUT-P011"),
    ("MSG-06", "ICO", "durability", "ANTHEM-UC responses were maintained or improved through week 28.", "OUT-P012"),
    ("MSG-07", "JNJ4804", "efficacy", "JNJ-4804 showed numerically higher week-48 remission than monotherapies in DUET-CD.", "OUT-P009"),
]:
    t_msg.add(PV, {"msg_id": mid, "brand_id": bid, "pillar": pillar, "statement": stmt, "substantiating_output_ids": outs,
                   "mlr_status": rng.choice(["approved", "approved", "in review"]), "valid_geos": "GLOBAL"},
              src=["SRC-SIM"], sim=("mlr_status",), ref=("valid_geos",))

t_tac = table("dissemination_tactics", "SIMULATED dissemination tactics.", ["tactic_id"])
CHANNELS = ["congress presentation", "industry symposium", "MSL scientific exchange", "advisory board", "med-ed (CME)",
            "medical website", "HTA submission", "payer dossier", "patient-org briefing", "webinar"]
AUDIENCES = ["STK-GI-ACAD", "STK-GI-COMM", "STK-NURSE", "STK-PAYER", "STK-GUIDE", "STK-PAT", "STK-SURG"]
for i in range(1, 29):
    o = rng.choice(outputs)
    ch = rng.choice(CHANNELS)
    reach = rng.randint(80, 2500)
    date = o["actual_date"] or o["planned_date"]
    done = bool(o["actual_date"])
    t_tac.add(SI, {"tactic_id": f"TAC-{i:03d}", "output_id": o["output_id"], "channel": ch,
                   "audience_ids": "; ".join(rng.sample(AUDIENCES, 2)), "geo_ids": rng.choice(["USA", "EMEA", "GLOBAL", "APAC", "DEU; FRA; GBR"]),
                   "planned_date": date, "wave": rng.choice(["readout", "post-readout amplification", "sustain", "pre-readout"]),
                   "reach_target": reach, "reach_actual": round(reach * rng.uniform(0.6, 1.2)) if done else None,
                   "owner_function": rng.choice(["Publications", "Medical Education", "Field Medical", "HEOR"]),
                   "status": "completed" if done else "planned"}, src=["SRC-SIM"])

# ---------------------------------------------------------------- publications (real, last 3 years) + share of voice
PUBS = ROOT / "data" / "raw" / "pubs" / "processed.json"
if PUBS.exists():
    P = json.loads(PUBS.read_text())
    t_pub = table("publications", f"All IBD publications and congress abstracts naming tracked assets, {P['window'][0]}..{P['window'][1]} (PubMed + Crossref). "
                  "Classification fields are rule-based (derived); brands_title = assets named in the title.", ["pub_id"])
    for r in PUBLIST:
        row = {k: ("; ".join(v) if isinstance(v, list) else v) for k, v in r.items() if not k.startswith("_")}
        src = [{"PubMed": "SRC-PUBMED", "UEG Gutflix": "SRC-UEG", "ACG programme": "SRC-ACGPROG"}.get(r["source"], "SRC-CROSSREF")]
        if r["series"] == "ACG" and "SRC-ACGPROG" not in src:
            src.append("SRC-ACGPROG")  # oral vs poster status comes from the ACG programme
        t_pub.add(PV, row, src=src,
                  der=("kind", "series", "venue", "presentation_type", "analysis_type", "brands_title", "brands_any", "focus", "multi_brand", "industry_affiliation", "abstract_code",
                       "linked_study_ids", "linked_gap_ids"))
    t_sovc = table("sov_congress", "Share of voice per congress edition: abstracts naming each asset in the title / all tracked-asset mentions at that congress.", ["venue", "brand_id"])
    for r in P["sov_congress"]:
        t_sovc.add(DE, r, src=["SRC-CROSSREF"])
    t_sovj = table("sov_journal", "Share of voice in journals per year (title mentions; letters excluded).", ["year", "brand_id"])
    for r in P["sov_journal"]:
        t_sovj.add(DE, r, src=["SRC-PUBMED", "SRC-CROSSREF"])
    t_sym = table("industry_symposia", "Industry-sponsored symposia at UEG Week 2023-2025 (UEG Gutflix listing).", ["venue"])
    for r in P.get("symposia", []):
        t_sym.add(PV, r, src=["SRC-UEG"])
    t_sova = table("sov_analysis", "Analysis-type mix per asset across all publications (title mentions).", ["brand_id"])
    for r in P["sov_analysis"]:
        t_sova.add(DE, r, src=["SRC-PUBMED", "SRC-CROSSREF"])

# =============================================================== competitive layer
t_cst = table("competitor_studies", "Competitor IBD trials (industry, Ph2-4, primary completion 2022+). Registry fields public; readout estimate derived; threat mapping simulated.",
              ["study_id", "brand_id"])
ASSET_SPONSOR = {"SKY": "AbbVie", "RIN": "AbbVie", "OMV": "Lilly", "MOR": "Lilly", "ENT": "Takeda", "VEL": "Pfizer", "ZEP": ("Bristol", "Celgene"),
                 "OBE": "Abivax", "TUL": ("Merck", "Prometheus"), "DUV": ("Sanofi", "Teva"), "AFI": ("Roche", "Hoffmann")}
PUBLIC_READOUTS = {"NCT06052059": ("2026-06-22", "positive (ATLAS-UC induction-only study within this programme)", "SRC-021"),
                   "NCT05535946": ("2026-06-01", "positive", "SRC-022"), "NCT04524611": ("2024", "positive (published NEJM)", "SRC-026"),
                   "NCT06063967": ("2026", "positive topline (AFFIRM); filed FDA Apr 2026", "SRC-024")}
THREAT = {"NCT06880744": "GAP-02", "NCT04524611": "GAP-01", "NCT06063967": "GAP-10", "NCT06227910": "GAP-09", "NCT05535946": "GAP-18",
          "NCT06052059": "GAP-18", "NCT07071519": "GAP-05", "NCT06937086": "GAP-09", "NCT06937099": "GAP-09", "NCT07415044": "GAP-18",
          "NCT05507203": "GAP-18", "NCT05507216": "GAP-18", "NCT07185009": "GAP-17", "NCT07184931": "GAP-17", "NCT06430801": "GAP-17",
          "NCT06548542": "GAP-09", "NCT07697456": "GAP-09", "NCT07186101": "GAP-09"}
COMPARATOR_JNJ = {"NCT04524611": "ustekinumab (J&J Stelara)", "NCT03926130": "ustekinumab (J&J Stelara)"}
seen_c = set()
comp_studies = []
# The registry leaves some trials without an acronym although the sponsor names them publicly.
# Only names confirmed in a cited source go here (checked 2026-09-22); the source is added to the row.
ACRONYM_FROM_SOURCE = {
    "NCT06052059": ("ATLAS-UC", "SRC-021"),   # Merck release 2026-06-22 names NCT06052059 as ATLAS-UC
    "NCT06430801": ("ARES-CD", "SRC-021"),    # same release names NCT06430801 as ARES-CD
    "NCT05507203": ("ABTECT-1", "SRC-CTGOV"), # registry brief title begins "ABTECT-1 - ABX464 ..."
    "NCT05507216": ("ABTECT-2", "SRC-CTGOV"), # registry brief title begins "ABTECT-2 - ABX464 ..."
    "NCT05535946": ("ABTECT maintenance", "SRC-CTGOV"),  # registry brief title "ABTECT - Maintenance"
}
# A trial found under one asset's search can belong to another: TOPAZ-UC tests MORF-057 (LY4268989)
# co-administered with mirikizumab, so it is a MORF-057 study, not an OMVOH one.
BRAND_FROM_TITLE = {"NCT07186101": "MOR"}
for aid0 in ["SKY", "OMV", "RIN", "ENT", "VEL", "ZEP", "OBE", "TUL", "DUV", "AFI", "MOR"]:
    for r in load(aid0):
        aid = BRAND_FROM_TITLE.get(r["nct_id"], aid0)
        if r["nct_id"] in seen_c or r["study_type_raw"] != "INTERVENTIONAL" or r["sponsor_class"] != "INDUSTRY":
            continue
        if not any(p in r["phases"] for p in ("Ph2", "Ph3", "Ph4")) or jnj_sponsor(r["lead_sponsor"]):
            continue
        if r["pcd"] and r["pcd"][:4] < "2022":
            continue
        keys = ASSET_SPONSOR[aid] if isinstance(ASSET_SPONSOR[aid], tuple) else (ASSET_SPONSOR[aid],)
        if not any(k.lower() in r["lead_sponsor"].lower() for k in keys):
            continue
        seen_c.add(r["nct_id"])
        _, st_type = classify(r)
        pcd = pdate(r["pcd"])
        pub = PUBLIC_READOUTS.get(r["nct_id"])
        exp = pub[0] if pub else (iso(add_months(pcd, 3)) if pcd else None)
        row = {"study_id": r["nct_id"], "nct_id": r["nct_id"], "brand_id": aid, "acronym": r["acronym"], "title": r["brief_title"],
               "company": r["lead_sponsor"], "indication": indication_of(r), "study_type": st_type, "phase_registry": r["phases"],
               "status": status_label(r["status"]), "n": r["n"], "n_countries": len(r["countries"]), "n_sites_registry": r["n_sites"],
               "start_date": r["start"], "primary_completion_date": r["pcd"], "pcd_date_type": r["pcd_type"],
               "expected_readout": exp, "readout_status": pub[1] if pub else ("reported/complete" if r["status"] == "COMPLETED" else "pending"),
               "readout_confidence": "confirmed" if pub else ("high" if r["pcd_type"] == "actual" else "medium"),
               "comparator_is_jnj_asset": COMPARATOR_JNJ.get(r["nct_id"], ""),
               "threatens_jnj_gap_id": THREAT.get(r["nct_id"], ""),
               "care_segment_ids": segments_of(r, indication_of(r))}
        named = ACRONYM_FROM_SOURCE.get(r["nct_id"])
        if named and not row["acronym"]:
            row["acronym"] = named[0]
        comp_studies.append(row)
        t_cst.add(PV, row, src=["SRC-CTGOV"] + ([pub[2]] if pub else []) + ([named[1]] if named and named[1] != "SRC-CTGOV" else []),
                  der=("indication", "study_type", "care_segment_ids", "readout_confidence") + (() if pub else ("expected_readout", "readout_status")),
                  sim=("threatens_jnj_gap_id",), note="expected_readout = PCD + 3 months unless a public topline exists")
        if r["phases"] in ("Ph3", "Ph2/Ph3") and r["status"] in ("RECRUITING", "ACTIVE_NOT_RECRUITING", "NOT_YET_RECRUITING"):
            country_rows(r["nct_id"], r)

t_cev = table("competitive_events", "Competitor and market events. Public events verified; projected events simulated.", ["event_id", "brand_id"])
for eid, aid, typ, date, cert, desc, src, origin in cp.EVENTS:
    t_cev.add(origin, {"event_id": eid, "brand_id": aid, "type": typ, "date": date, "date_certainty": cert, "description": desc,
                       "probability_positive": 1.0 if cert == "confirmed" else None}, src=[src], der=("probability_positive",))
PROJECTED = [
    ("EV-102", "SKY", "approval", "2027-Q3", "AI-predicted", "Projected EC decision on Skyrizi SC induction in CD", 0.8),
    ("EV-103", "OBE", "approval", "2027-Q4", "AI-predicted", "Projected FDA decision on obefazimod in UC (standard review after Q4-2026 NDA)", 0.7),
    ("EV-104", "TUL", "topline readout", "2026-12", "AI-predicted", "Projected ATLAS-UC maintenance / programme primary completion topline", 0.65),
    ("EV-105", "TUL", "filing", "2027-H1", "AI-predicted", "Projected tulisokibart UC filing", 0.6),
    ("EV-106", "AFI", "topline readout", "2027-Q2", "AI-predicted", "Projected AMETRINE-1/2 Ph3 UC topline (PCD Jan 2027)", 0.6),
    ("EV-107", "SKY", "topline readout", "2027-Q4", "AI-predicted", "Projected REVAMP topline: risankizumab vs vedolizumab in targeted-therapy-naive UC (PCD Aug 2027)", 0.65),
    ("EV-108", "DUV", "topline readout", "2028-Q3", "AI-predicted", "Projected SUNSCAPE-1 UC induction topline (PCD May 2028)", 0.55),
    ("EV-109", "OMV", "topline readout", "2028-Q2", "AI-predicted", "Projected COMMIT-UC (mirikizumab + tirzepatide) topline", 0.5),
    ("EV-110", "MOR", "topline readout", "2027-Q3", "AI-predicted", "Projected TOPAZ-UC (MORF-057 + mirikizumab) Ph2 topline", 0.5),
    ("EV-111", "TRE", "topline readout", "2029-Q1", "AI-predicted", "CHARGE (GUS vs RZB) topline, PCD Nov 2028", 0.6),
    ("EV-112", "ICO", "topline readout", "2028-Q2", "AI-predicted", "ICONIC-UC topline, PCD Jan 2028", 0.7),
]
# EV-101 timing is company guidance, not our projection: AbbVie (27 Apr 2026) "anticipates FDA approval ... later this year".
# Only the probability is simulated.
t_cev.add(PV, {"event_id": "EV-101", "brand_id": "SKY", "type": "approval", "date": "2026-Q4", "date_certainty": "company guidance",
               "description": "FDA decision on Skyrizi SC induction in CD, expected later in 2026 (AbbVie guidance, Apr 2026)", "probability_positive": 0.85},
          src=["SRC-024"], sim=("probability_positive",))
for eid, aid, typ, date, cert, desc, p in PROJECTED:
    t_cev.add(SI, {"event_id": eid, "brand_id": aid, "type": typ, "date": date, "date_certainty": cert, "description": desc,
                   "probability_positive": p}, src=["SRC-AI", "SRC-CTGOV"])

t_cgap = table("competitor_gaps", "SIMULATED (AI-inferred) competitor evidence gaps; rationale cites public facts.", ["cgap_id", "brand_id"])
for cid, aid, gtype, desc, sev, exploit, jnj_ev, window, closing in [
    ("CG-01", "SKY", "dosing & convenience", "No approved SC induction yet (filed Apr-2026 FDA / Sep-2026 EMA)", 4, True, "ASTRO; GRAVITI (fully SC)", "until approval, expected late 2026 (US)", "NCT06063967"),
    ("CG-02", "SKY", "population", "No RCT in perianal fistulizing CD", 3, True, "FUZION CD", "open", ""),
    ("CG-03", "SKY", "comparative", "No H2H vs guselkumab (CHARGE will answer; J&J-controlled)", 5, True, "CHARGE (J&J)", "until ~2029", "NCT07499232"),
    ("CG-04", "OMV", "dosing & convenience", "IV-only induction", 3, True, "SC induction label", "open", ""),
    ("CG-05", "OMV", "comparative", "VIVID-1 did not show superiority vs ustekinumab on key endpoints (verify)", 3, True, "GALAXI vs ustekinumab", "open", ""),
    ("CG-06", "RIN", "safety", "JAK class boxed warning limits 1L positioning; restricted to TNF-IR", 4, True, "IL-23 class safety profile", "structural", ""),
    ("CG-07", "TUL", "durability", "ATLAS-UC was induction-only; maintenance and long-term data pending", 4, False, "", "until maintenance readout", "NCT06052059"),
    ("CG-08", "TUL", "safety", "New MoA: limited long-term safety database", 3, True, "multi-year IL-23 safety", "3-5y", ""),
    ("CG-09", "OBE", "population", "No CD efficacy yet (ENHANCE-CD topline mid-2027)", 3, True, "GALAXI; GRAVITI", "until mid-2027", "NCT06456593"),
    ("CG-10", "OBE", "comparative", "No active-comparator data vs biologics", 3, True, "", "open", ""),
    ("CG-11", "ENT", "efficacy", "Slower onset perceived vs IL-23 / JAK", 2, True, "early response data", "structural", ""),
    ("CG-12", "DUV", "evidence volume", "Ph3 readouts not before 2028", 2, False, "", "until 2028", ""),
    ("CG-13", "VEL", "efficacy", "Oral S1P efficacy ceiling lower in refractory patients", 2, True, "icotrokinra ANTHEM-UC", "structural", ""),
]:
    t_cgap.add(SI, {"cgap_id": cid, "brand_id": aid, "gap_type": gtype, "description": desc, "severity_1to5": sev,
                    "jnj_can_exploit": exploit, "jnj_evidence_refs": jnj_ev, "exploitation_window": window,
                    "competitor_closing_study_id": closing}, src=["SRC-AI"], ver=("competitor_closing_study_id",) if closing else ())

t_strat = table("competitor_strategies", "SIMULATED AI-inferred competitor strategies. Hypotheses, not facts; evidence chain cites public sources.",
                ["strategy_id", "brand_id"])
STRATS = [
    ("STR-SKY", "SKY", "Defend IL-23 leadership in 1L IBD with H2H data (SEQUENCE vs ustekinumab, REVAMP vs vedolizumab) and close the SC-induction convenience gap (AFFIRM).",
     "H2H superiority; convenience; breadth of label", "UC-1L; CD-1L; CD-2L",
     [("SRC-026", "SEQUENCE: superior endoscopic remission vs ustekinumab", "Uses H2H to claim efficacy leadership"),
      ("SRC-CTGOV", "REVAMP (NCT06880744): RZB vs vedolizumab in targeted-therapy-naive UC", "Extending H2H strategy into 1L UC"),
      ("SRC-024", "SC induction filed in CD", "Neutralising Tremfya's fully-SC differentiator"),
      ("SRC-027", "75% in-play capture among IL-23s in front-line IBD", "Commercial scale reinforces 1L focus")],
     0.8, "Focus on psoriasis-to-IBD portfolio bundling; pricing/contracting as main lever",
     "REVAMP readout (~2027); FDA decision on SC induction; contracting announcements"),
    ("STR-OMV", "OMV", "Differentiate on durable 2-year CD data and simplified maintenance; build combination platform (mirikizumab + tirzepatide, + MORF-057, + eltrekibart).",
     "durability; combination; convenience", "CD-2L; UC-3L",
     [("SRC-028", "CD approval with 2-year Ph3 data", "Durability messaging"),
      ("SRC-CTGOV", "COMMIT-UC/CD (+tirzepatide), TOPAZ-UC (+MORF-057), eltrekibart combo trials", "Combination/obesity-IBD platform play")],
     0.7, "Combinations may be exploratory hedges rather than core strategy", "COMMIT and TOPAZ readouts 2027-2028"),
    ("STR-RIN", "RIN", "Own 'speed and depth' in refractory patients as oral efficacy benchmark; test dual-targeted therapy with vedolizumab (VICTRIVA, Takeda-sponsored).",
     "onset speed; efficacy in refractory; oral", "UC-2L; UC-3L; CD-2L; CD-3L",
     [("SRC-045", "Approved in TNF-IR CD", "Positioned after TNF"), ("SRC-CTGOV", "VICTRIVA vedolizumab + upadacitinib Ph3b", "Combination in refractory CD")],
     0.7, "May push earlier lines if label/guideline allows", "Guideline repositioning; VICTRIVA readout 2027"),
    ("STR-TUL", "TUL", "Establish TL1A as next-generation class with anti-fibrotic narrative, first to Ph3 success; move fast to filing in UC and CD.",
     "new MoA; breadth of label; fibrosis narrative", "UC-1L; UC-2L; CD-1L; CD-2L",
     [("SRC-021", "ATLAS-UC positive (first anti-TL1A Ph3)", "First-mover in class"),
      ("SRC-CTGOV", "CD Ph3 (NCT06430801) PCD 2028; LTE to 2037", "Long-term commitment to both indications")],
     0.75, "May target biomarker-selected population (diagnostic)", "Maintenance data; filing announcement; companion diagnostic news"),
    ("STR-OBE", "OBE", "Enter UC as first oral with novel MoA and durable maintenance, targeting advanced-therapy-naive and refractory patients; potential partnering/M&A target.",
     "oral; durability; new MoA", "UC-1L; UC-2L; UC-3L",
     [("SRC-022", "ABTECT maintenance positive", "Durability claim"), ("SRC-023", "NDA Q4 2026; CD topline mid-2027", "Near-term launch 2027-28")],
     0.7, "Could be acquired by a large pharma, changing commercial muscle", "NDA acceptance; partnering news"),
    ("STR-DUV", "DUV", "Fast-follow TL1A with large parallel Ph3 programme in UC and CD; Teva external financing to accelerate.",
     "new MoA; speed", "UC-1L; CD-1L",
     [("SRC-032", "SUNSCAPE/STARSCAPE Ph3 started and accelerated", "Fast-follower")], 0.6, "", "Enrollment speed; interim data"),
]
for sid, aid, stmt, pillars, segs, chain, conf, alt, watch in STRATS:
    t_strat.add(SI, {"strategy_id": sid, "brand_id": aid, "inferred_strategy_statement": stmt, "strategic_pillars": pillars,
                     "target_segments": segs, "evidence_chain": [{"source_id": s, "observation": o, "inference": i} for s, o, i in chain],
                     "confidence": conf, "alternative_hypotheses": alt, "leading_indicators_to_watch": watch,
                     "human_validated": False, "last_reassessed": iso(TODAY)}, src=[s for s, _, _ in chain] + ["SRC-AI"])

# publication themes per asset (derived from real titles): what each competitor keeps talking about
THEMES = {"bowel urgency": r"urgency", "fatigue & patient-reported outcomes": r"fatigue|quality of life|patient[- ]reported|promis|ibdq",
          "histologic / deep healing": r"histolog|mucosal healing|disease clearance|endoscopic remission|molecular",
          "transmural / intestinal ultrasound": r"transmural|ultraso|\bius\b", "real-world effectiveness": r"real[- ]world|real-life|retrospective|registry|cohort",
          "head-to-head / comparative": r"versus|\bvs\b|compar|head-to-head|superior", "long-term durability": r"long[- ]term|open-label extension|week (9\d|1\d\d)|\d[- ]year",
          "IV-to-SC switching": r"subcutaneous|switch", "pediatric": r"pediatric|paediatric|children", "safety": r"safety|adverse|infection|malignan|cardiovascular"}
PIVOTALS = ["SEQUENCE", "INSPIRE", "COMMAND", "FORTIFY", "ADVANCE", "MOTIVATE", "AFFIRM", "LUCENT", "VIVID", "SHINE", "U-ACHIEVE", "U-ACCOMPLISH", "U-EXCEL",
            "U-EXCEED", "U-ENDURE", "U-ACTIVATE", "ELEVATE", "TRUE NORTH", "ABTECT", "ARTEMIS", "APOLLO", "ATLAS", "RELIEVE", "AMETRINE", "GEMINI", "VISIBLE", "VARSITY", "SEAVUE"]
recent_pubs = [p for p in PUBLIST if p["_date"] and p["_date"] >= add_months(TODAY, -36)]
base_share = {th: sum(1 for p in recent_pubs if re.search(rx, p["title"], re.I)) / max(1, len(recent_pubs)) for th, rx in THEMES.items()}
t_theme = table("publication_themes", "Share of each asset's publication titles (3 years) per theme vs all tracked IBD assets (lift). Derived from real titles.", ["brand_id"])
for aid in ["TRE", "ICO", "SKY", "OMV", "RIN", "ENT", "VEL", "ZEP", "OBE", "TUL", "DUV", "AFI", "STE"]:
    mine = [p for p in recent_pubs if aid in p["_bt"]]
    for th, rx in THEMES.items():
        n = sum(1 for p in mine if re.search(rx, p["title"], re.I))
        if not mine:
            continue
        t_theme.add(DE, {"brand_id": aid, "theme": th, "n": n, "share_pct": round(100 * n / len(mine), 1),
                         "lift_vs_all": round((n / len(mine)) / base_share[th], 2) if base_share[th] else None, "n_asset_pubs": len(mine)},
                    src=["SRC-PUBMED", "SRC-CROSSREF", "SRC-UEG"])
for srow in t_strat.rows:
    f = srow["fields"]
    aid = f["brand_id"]
    bname = next((a[1] for a in cp.ASSETS if a[0] == aid), aid)  # readers know "SKYRIZI", not "SKY"
    mine = [p for p in recent_pubs if aid in p["_bt"]]
    sig = []
    lifts = sorted(((th, sum(1 for p in mine if re.search(rx, p["title"], re.I))) for th, rx in THEMES.items()), key=lambda x: -(x[1] / max(1, len(mine))) / max(1e-9, base_share[x[0]]))
    for th, n in lifts[:3]:
        if n >= 4 and (n / len(mine)) / max(1e-9, base_share[th]) >= 1.25:
            sig.append({"observation": f"{n} of {len(mine)} {bname} titles ({round(100 * n / len(mine))}%) are about {th} vs {round(100 * base_share[th])}% across tracked IBD assets",
                        "inference": f"Deliberate emphasis on {th} in scientific messaging", "source_id": "SRC-CROSSREF"})
    trials = Counter(t for p in mine for t in PIVOTALS if re.search(r"\b" + re.escape(t) + r"\b", p["title"], re.I))
    for t_name, n in trials.most_common(2):
        ph = sum(1 for p in mine if re.search(re.escape(t_name), p["title"], re.I) and p["analysis_type"] in ("Post-hoc analysis", "Subgroup analysis", "Pooled analysis", "Long-term extension"))
        sig.append({"observation": f"{t_name} named in {n} {bname} titles ({ph} post-hoc / subgroup / LTE)", "inference": f"{t_name} is being mined as a sustained evidence stream", "source_id": "SRC-CROSSREF"})
    n_cong = sum(1 for p in mine if p["kind"] == "congress")
    sig.append({"observation": f"{len(mine)} IBD items in 3 years ({n_cong} congress, {len(mine) - n_cong} journal)", "inference": "Share-of-voice context", "source_id": "SRC-PUBMED"})
    f["publication_signals"] = sig
    srow["prov"]["publication_signals"] = DE
    for s_id in ("SRC-PUBMED", "SRC-CROSSREF", "SRC-UEG"):
        if s_id not in srow["src"]:
            srow["src"].append(s_id)

t_imp = table("competitive_impact", "SIMULATED impact of competitor events on J&J brands (derived CTI).", ["impact_id", "event_id", "jnj_brand_id"])
IMPACTS = [
    ("IMP-01", "EV-101", "TRE", "SI-TRE-03", "GAP-10", "differentiation eroded", 4, 3, 0.9, 5,   # ~3 months: AbbVie expects approval later in 2026
     "Generate fully-SC real-world evidence (SIM-RWE-01; ask whether GORGEOUS can report an SC-induction cohort); publish ASTRO/GRAVITI long-term data; patient-experience evidence"),
    ("IMP-02", "EV-107", "TRE", "SI-TRE-01", "GAP-02", "guideline repositioning", 4, 13, 0.7, 5,
     "Commission UC NMA (SIM-ITC-02); consider UC H2H concept; prepare reactive scientific exchange"),
    ("IMP-03", "EV-001", "ICO", "SI-ICO-02", "GAP-18", "new class entrant", 3, 12, 0.6, 4,
     "Position oral convenience + IL-23 safety; oral NMA; monitor TL1A maintenance data"),
    ("IMP-04", "EV-003", "ICO", "SI-ICO-02", "GAP-18", "new class entrant", 3, 15, 0.8, 2,
     "Oral competitor arrives before icotrokinra UC; emphasise IL-23 efficacy/safety heritage and ICONIC-UC"),
    ("IMP-05", "EV-001", "TRE", "SI-TRE-01", "GAP-06", "new class entrant", 2, 18, 0.5, 4,
     "Long-term durability data (QUASAR/GALAXI LTE) as counter to new MoA"),
    ("IMP-06", "EV-106", "TRE", "SI-TRE-01", "GAP-02", "new class entrant", 2, 9, 0.5, 4, "Monitor; include TL1A in NMA updates"),
]
for iid, eid, bid, si, gap, mech, mag, months, pos, cs, resp in IMPACTS:
    overlap = rng.uniform(0.5, 0.95)
    cti = pos * overlap * (mag / 5) * (1 / (1 + months / 12)) * (cs / 5)
    t_imp.add(SI, {"impact_id": iid, "event_id": eid, "jnj_brand_id": bid, "affected_imperative_ids": si, "affected_gap_ids": gap,
                   "impact_direction": "negative", "impact_mechanism": mech, "impact_magnitude_1to5": mag,
                   "time_to_impact_months": months, "segment_overlap": round(overlap, 2),
                   "competitive_threat_index": round(cti * 100), "jnj_response_options": resp,
                   "preparedness_status": rng.choice(["ready", "in progress", "not started"])}, src=["SRC-AI"], der=("competitive_threat_index",))

# =============================================================== environment
t_gl = table("guidelines", "Clinical guidelines (public).", ["guideline_id"])
for gid, body, ind, date, summ, src, origin in cp.GUIDELINES:
    t_gl.add(origin, {"guideline_id": gid, "body": body, "indication": ind, "version_date": date, "summary": summ,
                      "next_update_expected": iso(add_months(pdate(date) or TODAY, 24))}, src=src.split(";"), sim=("next_update_expected",))

t_gp = table("guideline_positions", "How each main guideline positions TREMFYA and competitors, read from the full texts (paraphrased).", ["position_id"])
GL_SRC = {gid: src for gid, body, ind, date, summ, src, origin in cp.GUIDELINES}
for i, (gid, b, setting, position, note) in enumerate(cp.GUIDELINE_POSITIONS, 1):
    t_gp.add(PV, {"position_id": f"GP-{i:03d}", "guideline_id": gid, "brand_id": b, "setting": setting, "position": position, "note": note},
             src=GL_SRC[gid].split(";"))

t_hta = table("hta_decisions", "HTA decisions for TREMFYA in IBD, from the HTA bodies' public decisions (UK, Germany, France, Canada). Other markets not yet checked.", ["hta_id", "geo_id", "brand_id"])
for hid, geo, body, bid, ind, dec, restr, date, src, origin in cp.HTA_PUBLIC:
    t_hta.add(origin, {"hta_id": hid, "geo_id": geo, "body": body, "brand_id": bid, "indication": ind, "decision": dec,
                       "restriction_text": restr, "decision_date": date}, src=src.split(";"))
# The simulated placeholders for other markets were replaced by real decisions (Sep 2026). The random draws they used are
# kept so the rest of the simulated data stays the same.
for _ in range(12):
    rng.choice(["recommended", "recommended (restricted)", "pending", "no added benefit proven"]); rng.choice(["2025", "2026"])

t_reg = table("regulatory_events", "Approvals and filings.", ["reg_id", "brand_id"])
for i, (aid, agency, ind, typ, date, desc, src, origin) in enumerate(cp.REGULATORY, 1):
    t_reg.add(origin, {"reg_id": f"REG-{i:03d}", "brand_id": aid, "agency": agency, "indication": ind, "type": typ, "date": date,
                       "description": desc}, src=src.split(";") if src else [])

t_mkt = table("market_metrics", "Market metrics. Company-reported figures public; segment shares simulated.", ["brand_id", "geo_id"])
for per, geo, seg, aid, metric, val, desc, src, origin in cp.MARKET_PUBLIC:
    t_mkt.add(origin, {"period": per, "geo_id": geo, "segment_id": seg, "brand_id": aid, "metric": metric, "value": val,
                       "description": desc}, src=[src])
# SIMULATED new-patient share. Independent random draws per quarter produced impossible series
# (TREMFYA 22% -> 3% in one quarter, next to a real +72% sales quarter) and UC-only drugs in CD.
# Instead: a plausible starting mix per segment, a per-quarter drift that follows the public
# direction of travel (IL-23s up, ustekinumab down on biosimilars), small noise, and only brands
# labelled for that indication. Still a placeholder: replace with IQVIA/claims.
NBRX_BASE = {  # segment -> brand -> starting share (points, before normalising)
    "UC-1L": {"ENT": 24, "STE": 18, "SKY": 14, "TRE": 14, "RIN": 12, "OMV": 8, "VEL": 6},
    "UC-2L": {"RIN": 22, "STE": 16, "ENT": 14, "SKY": 14, "TRE": 13, "OMV": 10, "VEL": 8},
    "CD-1L": {"SKY": 26, "STE": 22, "ENT": 16, "TRE": 10, "RIN": 8, "OMV": 4},
    "CD-2L": {"SKY": 24, "RIN": 20, "STE": 16, "TRE": 10, "ENT": 10, "OMV": 6},
}
NBRX_DRIFT = {"TRE": 1.6, "SKY": 1.0, "OMV": 0.4, "RIN": 0.2, "VEL": 0.1, "ENT": -0.6, "STE": -2.6}  # points per quarter
mrng = random.Random(4242)  # own stream, so this block does not shift other simulated tables
for _ in range(84):  # the draws the previous version took from the main stream; keeps downstream values unchanged
    rng.uniform(2, 30)
for qi, q in enumerate(["2025-Q4", "2026-Q1", "2026-Q2"]):
    for seg, base in NBRX_BASE.items():
        raw = {b: max(0.5, v + NBRX_DRIFT[b] * qi + mrng.uniform(-0.8, 0.8)) for b, v in base.items()}
        tot = sum(raw.values())
        for b, v in raw.items():
            t_mkt.add(SI, {"period": q, "geo_id": "USA", "segment_id": seg, "brand_id": b, "metric": "new_patient_share_pct",
                           "value": round(100 * v / tot, 1), "description": "SIMULATED placeholder; replace with IQVIA/claims"}, src=["SRC-SIM"])

t_fi = table("field_insights", "SIMULATED de-identified, aggregated MSL insights.", ["insight_id", "geo_id"])
THEMES = [("competitor claim heard", "HCPs cite SEQUENCE when asked about IL-23 choice in CD", "GAP-01"),
          ("data request", "Requests for H2H or NMA data in bio-naive UC", "GAP-02"),
          ("unmet need", "Surgeons ask for fistula healing data beyond 24 weeks", "GAP-04"),
          ("efficacy question", "Questions on transmural healing and IUS monitoring", "GAP-03"),
          ("access", "Payers push biosimilar ustekinumab first in 2L", "GAP-08"),
          ("competitor claim heard", "Awareness of Skyrizi SC induction filing; questions on remaining Tremfya differentiation", "GAP-10"),
          ("efficacy question", "Interest in oral IL-23 for patients refusing injections", "GAP-19"),
          ("data request", "Requests for icotrokinra vs JAK safety comparison", "GAP-18"),
          ("competitor claim heard", "TL1A 'anti-fibrotic' narrative raised by academic KOLs", "GAP-03")]
for i in range(1, 41):
    theme, summ, gap = rng.choice(THEMES)
    t_fi.add(SI, {"insight_id": f"FI-{i:03d}", "date": iso(TODAY - dt.timedelta(days=rng.randint(1, 180))),
                  "geo_id": rng.choice(["USA", "DEU", "FRA", "GBR", "ITA", "ESP", "JPN", "CAN"]),
                  "stakeholder_type": rng.choice(["STK-GI-ACAD", "STK-GI-COMM", "STK-PAYER", "STK-SURG", "STK-NURSE"]),
                  "theme": theme, "summary": summ, "mapped_gap_id": gap, "frequency_count": rng.randint(1, 25),
                  "sentiment": rng.choice(["positive", "neutral", "negative"])}, src=["SRC-SIM"])

t_sig = table("signals", "Signal feed. Headlines are public events and registry changes; materiality scores are simulated (AI).", ["signal_id"])
n = 0
for eid, aid, typ, date, cert, desc, src, origin in cp.EVENTS:
    n += 1
    t_sig.add(origin, {"signal_id": f"SIG-{n:03d}", "detected_at": date, "signal_type": typ, "brand_id": aid, "headline": desc,
                       "materiality_score": round(rng.uniform(0.4, 0.95), 2), "status": rng.choice(["triaged", "actioned", "new"])},
              src=[src], sim=("materiality_score", "status"))
for row in comp_studies:
    d = None
    for sd in [row.get("primary_completion_date")]:
        d = pdate(sd or "")
    r_upd = [c for c in comp_studies if c["study_id"] == row["study_id"]]
    if row["status"] in ("recruiting", "active not recruiting") and row["pcd_date_type"] == "estimated" and d and TODAY <= d <= add_months(TODAY, 15):
        n += 1
        t_sig.add(DE, {"signal_id": f"SIG-{n:03d}", "detected_at": iso(TODAY), "signal_type": "upcoming readout (registry)",
                       "brand_id": row["brand_id"], "headline": f"{row['acronym'] or row['nct_id']}: primary completion {row['primary_completion_date']} ({row['title'][:70]})",
                       "materiality_score": round(rng.uniform(0.3, 0.9), 2), "status": "new"},
                  src=["SRC-CTGOV"], sim=("materiality_score",), note="derived: competitor study with PCD in next 15 months")

# =============================================================== AI layer (simulated)
t_ai = table("ai_insights", "AI insights generated from the dataset (publications, registry, labels, LOE, endpoints). Each cites entities in this dataset; review before use.", ["insight_id"])
AI = []   # former simulated examples AI-001..006 are rebuilt from data in the insight review block (after LOE and evidence depth)
for iid, typ, scope, head, body, cites, conf in AI:
    t_ai.add(SI, {"insight_id": iid, "insight_type": typ, "scope_entity_ids": scope, "headline": head, "body": body,
                  "cited_entity_ids": cites, "confidence": conf, "review_status": "auto", "generated_at": iso(TODAY)}, src=["SRC-AI"])

# data-driven insights from the real publication record (derived; replace the earlier simulated examples where they conflict)
def _sov(series, brand):
    rows = [r for r in PUBDATA["sov_congress"] if r["venue"].startswith(series + " ")]
    by = defaultdict(dict)
    for r in rows:
        by[r["venue"][-4:]][r["brand_id"]] = r["share_pct"]
    yrs = sorted(by)
    return [(y, by[y].get(brand, 0.0)) for y in yrs]


derived_ai = []
trend = [(ser, _sov(ser, "TRE")) for ser in ("ECCO", "DDW", "UEGW", "ACG")]
# half-up, so this reads the same as the dashboard's Math.round on the same share_pct
def _r(x): return math.floor(x + 0.5)


trend_txt = "; ".join(f"{ser} {_r(v[0][1])}% → {_r(v[-1][1])}% ({v[0][0]}–{v[-1][0]})" for ser, v in trend if len(v) >= 2)
cong3 = Counter(b for p in PUBLIST if p["kind"] == "congress" for b in p["_bt"] if b != "STE")
rank = [b for b, _ in cong3.most_common()].index("TRE") + 1 if "TRE" in cong3 else None
derived_ai.append(("AI-P01", "summary", "GLOBAL", f"TREMFYA's share of congress abstracts rose at all four major congresses; #{rank} by volume over 3 years",
                   f"Share of voice: {trend_txt}. Over 3 years TREMFYA has {cong3['TRE']} congress abstracts vs {', '.join(f'{b} {n}' for b, n in cong3.most_common(4) if b != 'TRE')}.",
                   "SRC-CROSSREF; SRC-UEG", 0.9))
mix = {b: Counter(p["analysis_type"] for p in PUBLIST if b in p["_bt"]) for b in ("TRE", "SKY", "RIN")}
rwe = {b: round(100 * m["RWE"] / max(1, sum(m.values()))) for b, m in mix.items()}
derived_ai.append(("AI-P02", "so-what", "SI-TRE-05", f"Publication mix: TREMFYA {rwe['TRE']}% real-world vs Skyrizi {rwe['SKY']}%",
                   f"{rwe['TRE']}% of TREMFYA publications are real-world evidence vs {rwe['SKY']}% for Skyrizi and {rwe['RIN']}% for Rinvoq (analysis type assigned from titles). TREMFYA's US IBD approvals are recent (UC Sep 2024, CD Mar 2025). J&J real-world studies are running (GAP-07, GAP-10); whether more are needed depends on which questions trials cannot answer.",
                   "GAP-07; GAP-10", 0.85))
g02 = [p for p in pub_by_gap["GAP-02"] if p["analysis_type"] == "ITC / NMA / SLR" or re.search(r"network|indirect|maic", p["title"], re.I)]
if g02:
    derived_ai.append(("AI-P03", "opportunity", "SI-TRE-01", "Comparative UC evidence already exists; publish it before REVAMP",
                       f"{len(g02)} J&J-named comparative analys{'is is' if len(g02) == 1 else 'es are'} on record (e.g. '{g02[0]['title'][:90]}…'), but not as peer-reviewed papers. REVAMP (risankizumab vs vedolizumab) has primary completion Aug 2027. Suggested action: publish it and extend it to vedolizumab before REVAMP reports.",
                       "GAP-02; NCT06880744; " + "; ".join(p["pub_id"] for p in g02[:3]), 0.8))
silent = [(g, comp_voice[g]) for g in COMP_TOPIC if comp_voice[g] and not pub_by_gap[g]]
for i, (g, n) in enumerate(sorted(silent, key=lambda x: -x[1])[:2]):
    derived_ai.append((f"AI-P0{4 + i}", "risk alert", g, f"{g}: competitors published {n} items in 12 months, J&J none",
                       f"Competitors published {n} items on this topic in the last 12 months; J&J has none. Suggested action: an interim or baseline output from the closing study, or a post-hoc analysis of existing trial data.",
                       g, 0.75))
debt = [r["fields"] for r in t_study.rows if r["fields"].get("pubs_congress") and not r["fields"].get("peer_reviewed_paper") and r["fields"]["lead_sponsor"].startswith("Janssen")]
if debt:
    derived_ai.append(("AI-P06", "risk alert", "GLOBAL", f"{len(debt)} J&J trials presented at congresses but without a peer-reviewed trial paper",
                       "Congress-only: " + ", ".join(f"{d['acronym'] or d['study_id']} ({d['pubs_congress']} abstract{'s' if d['pubs_congress'] != 1 else ''} since {str(d['first_congress_date'])[:7]})" for d in sorted(debt, key=lambda d: -d['pubs_congress'])[:6]) + ". None has a peer-reviewed primary paper yet.",
                       "; ".join(d["study_id"] for d in debt[:6]), 0.85))
jumps = [(g, r) for g, r in gap_rows.items() if r["published_closure_pct"] >= 30]
if jumps:
    derived_ai.append(("AI-P07", "change-since-last", "GLOBAL", f"{len(jumps)} gaps are partly closed by evidence already public",
                       "Published evidence now counts toward: " + ", ".join(f"{g} ({r['published_closure_pct']}%: {r['pubs_jnj_journal']} journal / {r['pubs_jnj_congress']} congress)" for g, r in sorted(jumps, key=lambda x: -x[1]['published_closure_pct'])[:6]) + ". Recommendations for these gaps shift from 'generate' to 'publish / consolidate'.",
                       "; ".join(g for g, _ in jumps[:8]), 0.8))
# =============================================================== product profiles (label-based)
t_reg2 = table("regimens", "Dosing regimens copied from US labels (public, verified). Filed regimens show only what the sponsor has disclosed; blank = not disclosed.", ["reg_id"])
for (rid, bid, ind, phase, lab, route, dose, wks, start, every, dev, devopt, setting, inf_h, status, src) in cp.REGIMENS:
    t_reg2.add(PV, {"reg_id": rid, "brand_id": bid, "indication": ind, "phase": phase, "regimen": lab, "route": route, "dose_mg": dose,
                    "induction_weeks": "; ".join(map(str, wks)) if wks else None, "maintenance_start_week": start, "interval_weeks": every,
                    "devices_per_dose_min": dev, "device_options": devopt, "setting": setting, "infusion_min_hours": inf_h, "status": status}, src=[src])

# year-1 burden per treatment path (weeks 0-51): derived from the regimen rows above
REG = {r[0]: r for r in cp.REGIMENS}
def path_events(ind_id, mnt_id):
    ind, mnt = REG[ind_id], REG[mnt_id]; ev = []
    if ind[7]:
        for w in ind[7]: ev.append({"w": w, "t": "iv" if ind[5] == "IV" else "sc", "n": ind[10], "h": ind[13]})
    else:
        ev.append({"w": 0, "w1": 12, "t": "unknown"})                       # filed SC induction: dose and schedule not disclosed
    w = mnt[8]
    while w < 52: ev.append({"w": w, "t": "sc", "n": mnt[10]}); w += mnt[9]
    return ev
PATHS = []
for ind in ("CD", "UC"):
    PATHS += [(f"P-{ind}-TRE-SC-100", "TRE", ind, f"TRE-{ind}-IND-SC", f"TRE-{ind}-MNT-100", "SC induction → 100 mg every 8 weeks"),
              (f"P-{ind}-TRE-SC-200", "TRE", ind, f"TRE-{ind}-IND-SC", f"TRE-{ind}-MNT-200", "SC induction → 200 mg every 4 weeks"),
              (f"P-{ind}-TRE-IV-100", "TRE", ind, f"TRE-{ind}-IND-IV", f"TRE-{ind}-MNT-100", "IV induction → 100 mg every 8 weeks"),
              (f"P-{ind}-SKY-IV-Q8", "SKY", ind, f"SKY-{ind}-IND-IV", f"SKY-{ind}-MNT-180", "IV induction → 180 or 360 mg every 8 weeks")]
PATHS.append(("P-CD-SKY-SC-Q8", "SKY", "CD", "SKY-CD-IND-SC", "SKY-CD-MNT-180", "SC induction (filed) → 180 or 360 mg every 8 weeks"))
LFT = {"TRE": 16, "SKY": 12}
t_burden = table("regimen_burden", "Year-1 treatment burden per path, derived from label regimens. Unknown = filed regimen not yet disclosed.", ["path_id"])
BURDEN = {}
for pid, bid, ind, i_id, m_id, lab in PATHS:
    ev = path_events(i_id, m_id); unk = any(e["t"] == "unknown" for e in ev)
    inj = sum(e["n"] for e in ev if e["t"] == "sc"); inf = sum(1 for e in ev if e["t"] == "iv"); hrs = sum(e.get("h") or 0 for e in ev if e["t"] == "iv")
    days = len({e["w"] for e in ev if e["t"] != "unknown"})
    row = {"path_id": pid, "brand_id": bid, "indication": ind, "path": lab, "status": REG[i_id][14], "injections_min": inj, "infusions": inf,
           "infusion_hours_min": hrs, "dosing_days": days, "has_undisclosed": unk, "lft_window_weeks": LFT[bid],
           "note": "induction not disclosed; counts cover maintenance only" if unk else "", "events": ev}
    BURDEN[pid] = row
    t_burden.add(DE, row, src=["SRC-LBL-TRE" if bid == "TRE" else "SRC-LBL-SKY"] + (["SRC-024"] if unk else []))

# verdicts: TREMFYA vs SKYRIZI per attribute, today and if SKYRIZI SC induction is approved as filed
def verdict(kind, tre, comp):
    c = str(comp)
    if kind == "cross": return "No claim (cross-trial)", "Different trials and populations; only a head-to-head trial can compare"
    if kind == "pending": return "Pending (head-to-head ongoing)", "CHARGE will answer this; no claim before it reads out"
    if kind == "different": return "Different, no preference data", "Formats differ; no published evidence that patients prefer either"
    if "not disclosed" in c: return "Unknown (not disclosed)", "Wait for the label; do not assume"
    if c.startswith("n/a"): return "Not applicable", c[4:].strip("() ")
    if kind == "same": return "Parity", "Same on both labels" if str(tre) == c or c == "same" else "Both have one"
    if kind == "bool":
        t, k = str(tre).startswith("yes"), c.startswith("yes")
        return ("Parity", "Both labels") if t == k else (("TREMFYA advantage", "TREMFYA only") if t else ("SKYRIZI advantage", "SKYRIZI only"))
    if kind in ("lower", "higher"):
        a, b = float(tre), float(comp)
        if a == b: return "Parity", "Same on both labels"
        better_tre = a < b if kind == "lower" else a > b
        return ("TREMFYA advantage" if better_tre else "SKYRIZI advantage"), f"{tre:g} vs {float(comp):g} on the labels"
    return "Parity", ""
t_attr = table("product_attributes", "TREMFYA vs SKYRIZI attribute values from labels, trials and filings, with the verdict under today's labels and if SKYRIZI SC induction is approved as filed.", ["attr_id"])
DIFF = {"CD": [], "UC": []}
for (aid, grp, name, ind, kind, who, tre, sky_now, sky_filed, tsrc, ssrc, note) in cp.ATTRIBUTES:
    v_now, why_now = verdict(kind, tre, sky_now); v_filed, why_filed = verdict(kind, tre, sky_filed)
    row = {"attr_id": aid, "indication": ind, "group": grp, "attribute": name, "stakeholders": who, "tremfya": tre, "skyrizi_now": sky_now, "skyrizi_if_approved": sky_filed,
           "verdict_now": v_now, "why_now": why_now, "verdict_if_approved": v_filed, "why_if_approved": why_filed, "changes_on_approval": v_now != v_filed, "note": note}
    DIFF[ind].append(row)
    t_attr.add(PV, row, src=sorted({tsrc, *ssrc.split(";")}), der=("verdict_now", "why_now", "verdict_if_approved", "why_if_approved", "changes_on_approval"))
t_watch = table("watch_items", "Open questions the monthly/daily watchers check; each resolves when the named source publishes.", ["watch_id"])
WATCH_SRC = {"W-005": ["SRC-LOE-AVT", "SRC-LOE-TAKSUIT"], "W-006": ["SRC-LOE-JNJ"]}
for wid, bid, q, st, src_chk, owner, links in cp.WATCH:
    t_watch.add(RF, {"watch_id": wid, "brand_id": bid, "question": q, "status_now": st, "resolves_when": src_chk, "owner_role": owner, "linked_ids": links, "state": "open"}, src=WATCH_SRC.get(wid, ["SRC-024"]))
# differentiation-shift insight (CD, where the filing applies)
cd = DIFF["CD"]
adv_now = [r for r in cd if r["verdict_now"] == "TREMFYA advantage"]; adv_then = [r for r in cd if r["verdict_if_approved"] == "TREMFYA advantage"]
lost = [r["attribute"] for r in adv_now if r["verdict_if_approved"] != "TREMFYA advantage"]
kept = [r["attribute"] for r in adv_then]
unknown = [r["attribute"] for r in cd if r["verdict_if_approved"].startswith("Unknown")]
sky_adv = [r["attribute"] for r in cd if r["verdict_if_approved"] == "SKYRIZI advantage"]
uc_adv = [r["attribute"] for r in DIFF["UC"] if r["verdict_now"] == "TREMFYA advantage"]
lc = lambda x: x if x[:2].isupper() else x[0].lower() + x[1:]   # keep acronyms ("SC induction")
sky_rows = [r for r in cd if r["verdict_if_approved"] == "SKYRIZI advantage"]
derived_ai.append(("AI-D01", "risk alert", "SI-TRE-03",
                   f"If SKYRIZI SC induction is approved in Crohn's, TREMFYA's label advantages in CD fall from {len(adv_now)} to {len(adv_then)}; UC keeps {len(uc_adv)}",
                   "What changes in CD: " + " and ".join(lc(x) for x in lost) + " become parity. "
                   + ("Still different in CD: " + "; ".join(lc(x) for x in kept) + ". " if kept else "")
                   + "Unknown until the label: " + "; ".join(lc(x) for x in unknown) + " (TREMFYA itself gives each 400 mg SC induction dose as two 200 mg injections). "
                   + "".join(f"SKYRIZI's label is lighter on {lc(r['attribute']).replace(' (weeks)', '')} ({r['skyrizi_if_approved']} vs {r['tremfya']} weeks). " for r in sky_rows)
                   + "In UC nothing changes: TREMFYA remains the only IL-23 with a fully subcutaneous option, and its IV induction infusion is shorter (1 vs 2 hours minimum). "
                   + "Efficacy stays cross-trial (GRAVITI vs AFFIRM topline) until CHARGE reads out (primary completion Nov 2028). "
                   + "What it means: in CD the story moves from 'only fully SC IL-23' to UC breadth, established SC use and evidence depth. "
                   + "Actions: label-based scientific exchange on SC induction options; lead with UC fully-SC data; generate patient-experience and device-preference evidence (GAP-10); watch the SKYRIZI label (W-001).",
                   "EV-101; GAP-10; SI-TRE-03", 0.8))

# ---- evidence depth, part 3: competitor trials profiled the same way, then blind spots (types J&J will not have but competitors will)
INN = {a[0]: a[2].split(" ")[0].split("(")[0].lower() for a in cp.ASSETS}
RAWC = {}
for aid0 in ["SKY", "OMV", "RIN", "ENT", "VEL", "ZEP", "OBE", "TUL", "DUV", "AFI", "MOR"]:
    for r_ in load(aid0): RAWC.setdefault(r_["nct_id"], r_)
for cr in TABLES["competitor_studies"].rows:
    f = cr["fields"]; r_ = RAWC.get(f["study_id"])
    if r_ is None or f["study_id"] in PROFILE: continue
    own = INN.get(f["brand_id"], "x") + ("|mk-7240|pra023" if f["brand_id"] == "TUL" else "|tev-48574|sar447189" if f["brand_id"] == "DUV" else "|ro7790121|rvt-3101" if f["brand_id"] == "AFI" else "|abx464" if f["brand_id"] == "OBE" else "|morf-057|ly4268989" if f["brand_id"] == "MOR" else "")
    prof = build_profile(f["study_id"], "competitor", f["brand_id"], f["indication"], r_, own_rx=own)
    prof["gap_checks"] = {}; prof["reported_in_publications"] = {}
    t_prof.add(DE, prof, src=["SRC-CTGOV"], ref=("side",))
# J&J profiles are added here too so every profile sits in one table
for sid, prof in PROFILE.items():
    if prof["side"] == "J&J": t_prof.add(DE, prof, src=["SRC-CTGOV"] if prof["n_outcomes"] else ["SRC-SIM"], ref=("side",),
                                          sim=("delivers", "not_registered", "domains") if prof["outcome_source"].startswith("declared") else ())
# coming evidence: studies still running or reading out from 2024 on (terminated/withdrawn excluded)
def coming(sid, side):
    if side == "J&J":
        row = study_index[sid]["row"]; st, pcd = row["status"], row["primary_completion_date"]
    else:
        f = next(x["fields"] for x in TABLES["competitor_studies"].rows if x["fields"]["study_id"] == sid); st, pcd = f["status"], f["primary_completion_date"]
    return st not in ("terminated", "withdrawn", "TERMINATED", "WITHDRAWN") and (pcd or "9999")[:4] >= "2024"
def inds(x): x = x or ""; return [i for i in ("UC", "CD") if i in x or "UC+CD" in x or "IBD" in x]
DEPTH = {}
for sid, prof in PROFILE.items():
    if not coming(sid, prof["side"]): continue
    for ind in inds(prof["indication"]):
        for c in prof["domains"]:
            DEPTH.setdefault((ind, c), {"J&J": [], "competitor": []})[prof["side"]].append(sid)
t_depth = table("evidence_depth_by_domain", "Derived: how many running or recent (primary completion 2024+) studies register each evidence type, J&J vs competitors, by indication.", ["depth_id"])
for ind in ("UC", "CD"):
    for c, n, _ in DOMAINS:
        d = DEPTH.get((ind, c), {"J&J": [], "competitor": []})
        t_depth.add(DE, {"depth_id": f"{ind}-{c}", "indication": ind, "domain_code": c, "domain": n, "jnj_studies": len(d["J&J"]), "competitor_studies": len(d["competitor"]),
                         "jnj_study_ids": "; ".join(d["J&J"]), "competitor_study_ids": "; ".join(d["competitor"])}, src=["SRC-CTGOV"])

# ---- evidence depth insights (all numbers computed above)
dd = lambda ind, c: next(r["fields"] for r in t_depth.rows if r["fields"]["depth_id"] == f"{ind}-{c}")
lead = [(ind, c) for ind in ("UC", "CD") for c in ("TRAN", "HIST", "BIOM") if dd(ind, c)["jnj_studies"] > dd(ind, c)["competitor_studies"]]
nm = lambda sid: study_index[sid]["row"]["acronym"] or sid if sid in study_index else next((x["fields"]["acronym"] or sid for x in TABLES["competitor_studies"].rows if x["fields"]["study_id"] == sid), sid)
derived_ai.append(("AI-E01", "opportunity", "SI-TRE-01",
                   f"J&J's coming IBD evidence goes deeper than competitors': transmural imaging in {dd('CD', 'TRAN')['jnj_studies']} J&J Crohn's studies vs {dd('CD', 'TRAN')['competitor_studies']}, histology in {dd('CD', 'HIST')['jnj_studies']} vs {dd('CD', 'HIST')['competitor_studies']}",
                   "Counting running or recent studies (primary completion 2024+) that register each evidence type: "
                   + "; ".join(f"{ind} {DNAME[c].split(' (')[0].lower()} {dd(ind, c)['jnj_studies']} J&J vs {dd(ind, c)['competitor_studies']} competitor" for ind, c in lead) + ". "
                   + "Competitors register more safety and drug-level endpoints because their programmes are larger registrational trials, and they have a randomised head-to-head in each indication (REVAMP in UC, SEQUENCE in CD) where J&J has CHARGE in CD and only indirect or real-world comparisons in UC. "
                   + "What it means: depth (transmural, histologic, biomarker) is where TREMFYA's coming evidence differs most from competitors'; "
                   + "plan papers and congress slots so these data are seen, starting with REASON (transmural) and the RWE studies that register bowel ultrasound.",
                   "GAP-03; GAP-14", 0.7))
gapp = {r["fields"]["gap_id"]: r["fields"] for r in t_gap.rows}
def gap_delivered(gid, code, lt=False):
    cl = [x.strip() for x in (gapp[gid]["closing_study_ids"] or "").split(";") if x.strip()]
    return [s for s in cl if code in PROFILE[s]["domains"] and (not lt or PROFILE[s]["domains"][code]["horizon"] == "long term (>1 y)")]
g22 = gap_delivered("GAP-22", "SAFE", True)
g02 = [PROFILE[s]["domains"]["COMP"]["role"] for s in gap_delivered("GAP-02", "COMP")]
g03 = gap_delivered("GAP-03", "TRAN")
fz = PROFILE["NCT05347095"]
capped_all = [(sid, g, c) for sid, p in PROFILE.items() if p["side"] == "J&J" for g, c in p.get("gap_checks", {}).items() if c["effective_fit"] < c["analyst_fit"]]
revamp = next((x["fields"] for x in TABLES["competitor_studies"].rows if x["fields"]["study_id"] == "NCT06880744"), None)
derived_ai.append(("AI-E02", "risk alert", "SI-TRE-02",
                   "What our studies will not answer: " + "; ".join(x for x in [
                       "no J&J study registers icotrokinra IBD safety beyond one year" if not g22 else "",
                       "UC head-to-head rests on an indirect comparison only" if g02 and set(g02) <= {"indirect"} else "",
                       f"transmural healing rests on {nm(g03[0])} alone" if len(g03) == 1 else ""] if x),
                   ("GAP-22 (long-term icotrokinra safety in IBD): ICONIC-UC registers safety to week 52 only, and no other J&J study covers it. " if not g22 else "")
                   + (f"GAP-02 (UC head-to-head): the only J&J evidence planned is a network meta-analysis, while AbbVie's REVAMP (risankizumab vs vedolizumab, UC) is a direct comparison with primary completion {pdate(revamp['primary_completion_date']).strftime('%b %Y')}. " if revamp and g02 and set(g02) <= {'indirect'} else "")
                   + (f"GAP-03 (transmural healing in CD): only {nm(g03[0])} registers it among the closing studies; GALAXI does not, so its fit was reduced to zero. " if len(g03) == 1 else "")
                   + f"FUZION CD registers fistula (clinical and MRI), clinical, steroid-free, quality-of-life and safety endpoints, but no endoscopic, histologic or biomarker endpoint: it answers perianal disease (GAP-04) and will not add to the luminal endoscopic story. "
                   + (f"Gap fits reduced because the registered endpoints cannot answer the gap: " + "; ".join(f"{nm(sid)} → {g} ({c['analyst_fit']:.0%} → {c['effective_fit']:.0%}, missing {', '.join(c['missing']).lower()})" for sid, g, c in capped_all) + ". " if capped_all else "")
                   + "Caveat: 'not registered' means not promised; exploratory endpoints are often unregistered, so confirm with study teams before acting.",
                   "GAP-22; GAP-02; GAP-03; NCT05347095", 0.7))

# =============================================================== lifecycle: loss of exclusivity (LOE) and value windows
# Evidence pays off when guidelines and payers use it; if that happens after the product loses exclusivity, the brand
# captures little of the value. Public LOE signals come from company filings (see curated_public.LOE); J&J planning dates
# that are not public are placeholders (simulated) until J&J IP confirms them.
t_loe = table("loe", "Loss of exclusivity per product and market: first approval, regulatory floor, public patent/settlement signal and the planning date the dashboard calculates with. Placeholders are simulated; J&J dates need IP confirmation.", ["loe_id", "brand_id", "market"])
LOE_PLAN = {}
for L in cp.LOE:
    lid = f"LOE-{L['b']}-{L['m']}"
    plan_prov = {"public": DE, "passed": DE, "sim": SI}[L["kind"]]
    status = ("generic/biosimilar on market" if L["kind"] == "passed" else "not yet approved" if not L["appr"] or pdate(L["appr"]) > TODAY
              else "biosimilar filed; exclusivity at risk" if L["b"] == "ENT" else "exclusive")
    row = {"loe_id": lid, "brand_id": L["b"], "market": L["m"], "product_type": L["type"], "first_approval": L["appr"],
           "approval_status": "expected (simulated)" if L["appr_src"] == "SRC-SIM" else "expected (derived)" if L["appr"] and pdate(L["appr"]) > TODAY else ("actual" if L["appr"] else "not approved"),
           "regulatory_floor": L["floor"], "floor_basis": L["floor_basis"], "public_protection": L["protect"], "protection_basis": L["protect_basis"],
           "planning_loe": L["plan"], "planning_basis": L["plan_basis"], "planning_kind": {"public": "public signal", "passed": "LOE passed", "sim": "placeholder"}[L["kind"]],
           "range_low": L["lo"], "range_high": L["hi"], "status": status,
           "years_to_loe": round((pdate(L["plan"]) - TODAY).days / 365.25, 1)}
    unv = ("first_approval",) if L["appr"] and not L["appr_ok"] and L["appr_src"] != "SRC-SIM" else ()
    sim = ("first_approval", "approval_status") if L["appr_src"] == "SRC-SIM" else ()
    if L["kind"] == "sim": sim += ("planning_loe", "range_low", "range_high", "years_to_loe")
    else: sim += ("range_low", "range_high") if L["lo"] != L["hi"] else ()
    if not L.get("protect_ok", True): unv += ("public_protection",)
    der = tuple(k for k in ("regulatory_floor", "status", "years_to_loe") if k not in sim) + (("planning_loe",) if L["kind"] != "sim" else ())
    srcs = [x for x in (L["protect_src"], L["appr_src"] if L["appr_src"] != "SRC-SIM" else None, "SRC-EXCL-RULES") if x] + (["SRC-SIM"] if L["kind"] == "sim" or L["appr_src"] == "SRC-SIM" else [])
    t_loe.add(PV, row, src=srcs, sim=sim, der=der, unv=unv)
    LOE_PLAN[(L["b"], L["m"])] = pdate(L["plan"])

# value timing per archetype: typical duration (from our own studies where we have >= 2), and reference lags
def archetype(row):
    st, ec = row["study_type"] or "", row["evidence_class"]
    if ec == "Evidence synthesis & modelling": return "Evidence synthesis / HEOR"
    if ec.startswith("Non-interventional"): return "Retrospective RWE" if "retrospective" in st else "Prospective RWE"
    if any(k in st for k in ("Ph4", "LTE")): return "Phase 4 / extension"
    if st.startswith("Ph3") or "Ph2b/3" in st: return "Phase 3 RCT"
    return "Phase 2"
ARCH = {  # readout lag after primary completion, paper lag after readout, default duration (months)
    "Phase 3 RCT": (3, 12, 42), "Phase 4 / extension": (3, 12, 36), "Phase 2": (3, 12, 30),
    "Prospective RWE": (2, 9, 36), "Retrospective RWE": (2, 6, 9), "Evidence synthesis / HEOR": (0, 6, 6)}
UPTAKE_LAG, MIN_YEARS = 18, 2   # months from paper to guideline/HTA use; minimum years of value wanted before LOE
dur = defaultdict(list)
jnj_of = lambda ids: next((b for b in ("JNJ4804", "ICO", "TRE") if b in (ids or "")), None)
for sid, info in study_index.items():
    row = info["row"]; s0, s1 = pdate(row["start_date"]), pdate(row["primary_completion_date"])
    if jnj_of(row["brand_ids"]) and s0 and s1 and s1 > s0: dur[archetype(row)].append(months_between(s0, s1))
ms_rows = defaultdict(dict)
for r_ in t_ms.rows:
    f = r_["fields"]; ms_rows[f["study_id"]][f["code"]] = pdate(f["actual_date"] or f["forecast_date"]), bool(f["actual_date"])

PUBS = {r_["fields"]["pub_id"]: r_["fields"] for r_ in TABLES["publications"].rows}
t_win = table("study_loe_window", "Derived: when each J&J study's evidence can be used by guidelines and payers, and how many years of exclusivity remain after that (US planning LOE). Lags are reference assumptions; change them in the Lifecycle view.", ["study_id"])
WIN = []
for sid, info in study_index.items():
    row = info["row"]; b = jnj_of(row["brand_ids"])
    if not b or row["status"] in ("terminated", "withdrawn"): continue
    a = archetype(row); rl, pl, _ = ARCH[a]; ms = ms_rows.get(sid, {})
    pcd = pdate(row["primary_completion_date"])
    if not pcd: continue
    if "TLR" in ms and ms["TLR"][0]: rd, rd_basis = ms["TLR"][0], "topline milestone" + (" (actual)" if ms["TLR"][1] else " (forecast)")
    else: rd, rd_basis = add_months(pcd, rl), f"primary completion + {rl} months"
    ydate = lambda d: pdate(d) or (dt.date(int(d), 7, 1) if re.fullmatch(r"\d{4}", str(d or "")) else None)   # year-only dates: mid-year
    jdates = sorted(ydate(PUBS[x]["date"]) for x in (row.get("linked_pub_ids") or "").split("; ") if x in PUBS and PUBS[x]["kind"] == "journal" and ydate(PUBS[x]["date"]))
    if "MS1" in ms and ms["MS1"][0]: pp, pp_basis = ms["MS1"][0], "primary paper (actual)" if ms["MS1"][1] else "primary paper (forecast)"
    elif row.get("peer_reviewed_paper") and jdates: pp, pp_basis = jdates[0], "first linked journal publication"
    elif row.get("peer_reviewed_paper"): pp, pp_basis = pdate(row["first_public_date"]) or rd, "peer-reviewed paper (published; date approximate)"
    else:
        pp, pp_basis = add_months(rd, pl), f"readout + {pl} months ({a})"
        if pp < TODAY: pp, pp_basis = add_months(TODAY, 6), "paper overdue: assumed within 6 months"
    up = add_months(pp, UPTAKE_LAG)
    loe = LOE_PLAN[(b, "US")]
    yrs = round((loe - max(up, TODAY)).days / 365.25, 1)   # evidence already in use counts from today
    win = "well before LOE" if yrs >= 3 else "tight" if yrs >= 1 else "at LOE" if yrs >= 0 else "after LOE"
    in_use = up <= TODAY
    ri, st = (row.get("regulatory_intent") or ""), row["study_type"] or ""
    exc = ("Paediatric: US paediatric exclusivity can add 6 months to regulatory exclusivity" if "pediatric" in (ri + st).lower()
           else "Regulatory obligation" if "post-marketing" in ri else "Registrational: label value" if ri.startswith("registrational") else "")
    carry = "IL-23 pathway findings may also support icotrokinra and JNJ-4804 (judge per question)" if b == "TRE" and yrs < 1 else ""
    act = {"well before LOE": "On track: value lands with years of exclusivity left",
           "tight": "Protect the timeline: run the paper and HTA dossiers in parallel with the readout",
           "at LOE": "Accelerate: earlier data cut or a paper within 9 months, or narrow to markets with later LOE",
           "after LOE": "Needs a stated reason (obligation, patient need, successor value); otherwise narrow or stop"}[win]
    if exc and win in ("at LOE", "after LOE"): act = f"Exception applies ({exc.split(':')[0].lower()}); keep, but record the rationale"
    wrow = {"study_id": sid, "acronym": row["acronym"] or sid, "brand_id": b, "archetype": a, "status": row["status"], "readout_date": iso(rd), "readout_basis": rd_basis,
            "paper_date": iso(pp), "paper_basis": pp_basis, "uptake_date": iso(up), "uptake_basis": f"paper + {UPTAKE_LAG} months (guideline/HTA cycle, reference)",
            "planning_loe_us": iso(loe), "protected_years": yrs, "window": win, "in_use_now": in_use, "sponsorship": row["sponsorship_model"], "exception": exc, "successor_carry_over": carry, "suggested_action": act,
            "cost_usd": row.get("total_cost_usd")}
    WIN.append(wrow)
    t_win.add(DE, wrow, src=["SRC-CTGOV", "SRC-LOE-JNJ"] + (["SRC-SIM"] if b != "TRE" else []), ref=("uptake_basis",),
              sim=("cost_usd",) if row.get("total_cost_usd") is not None else ())

t_sb = table("loe_start_by", "Derived: the last month a new study of each type can start and still give at least 2 years of use by guidelines and payers before the planning LOE.", ["start_by_id"])
for b, m in (("TRE", "US"), ("TRE", "EU"), ("ICO", "US"), ("JNJ4804", "US")):
    loe = LOE_PLAN[(b, m)]
    for a, (rl, pl, d0) in ARCH.items():
        d = sorted(dur[a]); dm = d[len(d) // 2] if len(d) >= 2 else d0
        total = dm + rl + pl + UPTAKE_LAG + 12 * MIN_YEARS
        sb = add_months(loe, -total)
        t_sb.add(DE, {"start_by_id": f"SB-{b}-{m}-{a[:12].replace(' ', '')}", "brand_id": b, "market": m, "archetype": a, "typical_duration_months": dm,
                      "duration_basis": f"median of {len(d)} J&J studies" if len(d) >= 2 else "reference default", "readout_lag_months": rl, "paper_lag_months": pl,
                      "uptake_lag_months": UPTAKE_LAG, "min_years_before_loe": MIN_YEARS, "planning_loe": iso(loe), "last_useful_start": iso(sb),
                      "months_left": months_between(TODAY, sb), "years_if_started_now": round(months_between(add_months(TODAY, total - 12 * MIN_YEARS), loe) / 12, 1)},
                 src=["SRC-CTGOV", "SRC-LOE-JNJ"] + ([] if (b, m) == ("TRE", "US") else ["SRC-SIM"]),
                 ref=("readout_lag_months", "paper_lag_months", "uptake_lag_months", "min_years_before_loe"),
                 sim=() if (b, m) == ("TRE", "US") else ("planning_loe", "last_useful_start", "months_left", "years_if_started_now"))
SB = {(r_["fields"]["brand_id"], r_["fields"]["market"], r_["fields"]["archetype"]): r_["fields"] for r_ in t_sb.rows}

# insights
tre = [w for w in WIN if w["brand_id"] == "TRE"]
late = [w for w in tre if w["window"] in ("at LOE", "after LOE")]
late_noexc = [w for w in late if not w["exception"]]
tight = [w for w in tre if w["window"] == "tight"]
rct, rwe = SB[("TRE", "US", "Phase 3 RCT")], SB[("TRE", "US", "Prospective RWE")]
fm = lambda d: pdate(d).strftime("%b %Y")
cost_late = sum(w["cost_usd"] or 0 for w in late_noexc)
derived_ai.append(("AI-L01", "risk alert", "SI-TRE-01",
                   f"{len(late)} of {len(tre)} TREMFYA studies reach guidelines and payers within a year of, or after, the US LOE signal (mid-2031); {len(late_noexc)} have no exception on record",
                   f"Using the composition patent family J&J discloses (US, 2031; mid-year assumed) as the planning date, and readout, paper and an {UPTAKE_LAG}-month guideline/HTA lag: "
                   + "Less than a year of use, or none: " + ", ".join(f"{w['acronym']} ({w['protected_years']:+.1f} y)" for w in sorted(late, key=lambda w: w['protected_years'])) + ". "
                   + (f"Tight (1-3 years left): {', '.join(w['acronym'] for w in tight)}. " if tight else "")
                   + (f"Simulated spend on the studies without an exception: ${cost_late / 1e6:.0f}M. " if cost_late else "")
                   + "Paediatric studies are exceptions: US paediatric exclusivity can add 6 months to regulatory exclusivity. "
                   + "What it means: the date is a public floor, not J&J's confirmed LOE; other patent families may extend it. Confirm the planning date with J&J IP (W-006), "
                   + "then for each late study record the reason (obligation, patient need, value carried over to icotrokinra or JNJ-4804), accelerate the paper, or narrow the scope.",
                   "; ".join(w["study_id"] for w in late), 0.7))
syn, rrwe = SB[("TRE", "US", "Evidence synthesis / HEOR")], SB[("TRE", "US", "Retrospective RWE")]
yl = lambda r: f"{r['years_if_started_now']:+.1f} y"
derived_ai.append(("AI-L02", "decision", "SI-TRE-01",
                   f"A new TREMFYA study started today gives little time before the US LOE signal: evidence synthesis {yl(syn)}, retrospective RWE {yl(rrwe)}, Phase 3 RCT {yl(rct)}",
                   f"Years of guideline and payer use before a mid-2031 LOE if started this month: evidence synthesis {yl(syn)}, retrospective RWE {yl(rrwe)}, prospective RWE {yl(rwe)}, Phase 3 RCT {yl(rct)} "
                   f"(a Phase 3 RCT runs {rct['typical_duration_months']} months, {rct['duration_basis']}; then {rct['readout_lag_months']} months to topline, {rct['paper_lag_months']} to the paper, {UPTAKE_LAG} to guideline/HTA use). "
                   f"To keep {MIN_YEARS} years, a Phase 3 RCT had to start by {fm(rct['last_useful_start'])}. HTA dossiers can use data before the paper, so payer value can come earlier than guideline value. "
                   "What it means: new long TREMFYA trials should answer questions that also matter for icotrokinra and JNJ-4804, or be justified by patient need; "
                   "brand questions with a TREMFYA-only payoff move to fast RWE and evidence synthesis, planned now.", "GAP-07; GAP-08", 0.7))
derived_ai.append(("AI-L03", "risk alert", "SI-TRE-05",
                   "ENTYVIO biosimilars: first FDA decision expected Q1 2027; entry date depends on Takeda's patent suit (patents to 2032)",
                   "US biologic exclusivity for vedolizumab ended in May 2026. Alvotech/Teva's AVT16 (proposed interchangeable, IV) is under FDA review, and Takeda sued in September 2026 over six patents. "
                   "What it could mean (not verified): a cheaper vedolizumab could be placed ahead of IL-23s by payers; the dataset has no payer policy data to confirm this. "
                   "Suggested action: extend the cost-effectiveness work (GAP-08) to biosimilar vedolizumab prices, and track the case (W-005).", "GAP-08; W-005", 0.65))

# =============================================================== insight review: LOE, evidence depth and the J&J portfolio (TREMFYA, icotrokinra, JNJ-4804)
# Earlier insights are re-checked here, once LOE windows and endpoint profiles exist. Former simulated examples (AI-001..006) are rebuilt from data.
def _idx(iid): return next(i for i, x in enumerate(derived_ai) if x[0] == iid)
def revise(iid, head=None, body=None, add=None, cites=None):
    i = _idx(iid); x = list(derived_ai[i])
    if head: x[3] = head
    if body: x[4] = body
    if add: x[4] = x[4].rstrip() + " " + add
    if cites: x[5] = x[5] + "; " + cites
    derived_ai[i] = tuple(x)
WB = {w["study_id"]: w for w in WIN}
yu = lambda sid: WB[sid]["protected_years"]
mo = lambda d: pdate(d).strftime("%b %Y")
FUZ, GORG, CHG, REA, GUA = "NCT05347095", "NCT07102368", "NCT07499232", "NCT06408935", "NCT06916390"
ICU, ICD, DEU, DEC = "NCT07196748", "NCT07196722", "NCT07577856", "NCT07577843"
g10 = [s for s in (gap_rows["GAP-10"]["closing_study_ids"] or "").split("; ") if s]
derived_ai.append(("AI-001", "risk alert", "SI-TRE-03", "Fully-SC differentiation in Crohn's at risk from late 2026",
                   f"AbbVie filed SKYRIZI SC induction in CD (FDA Apr 2026, EMA Sep 2026); the FDA decision is expected late 2026 (AbbVie guidance). If approved, TREMFYA's CD label advantages fall from {len(adv_now)} to {len(adv_then)} (AI-D01); UC is unchanged. "
                   f"GAP-10 (real-world use of the SC regimen) now has {len(g10)} closing studies, but the largest real-world source, GORGEOUS, reads out {mo(WB[GORG]['readout_date'])} and gives {yu(GORG):+.1f} years of guideline/HTA use before TREMFYA's US LOE signal. "
                   "What it means: an earlier SC-induction data cut (REC-003) and the preference study (SIM-DCE-01) are the options that report before 2029.",
                   "EV-101; GAP-10; NCT07102368; REC-003", 0.8))
derived_ai.append(("AI-002", "opportunity", "SI-TRE-06", "FUZION CD: publish in 2027 to keep about 3 years of use before LOE",
                   f"FUZION CD is the only IL-23 randomised trial in perianal fistulising CD among the tracked industry trials (presented at DDW 2026). A paper by {mo(WB[FUZ]['paper_date'])} gives {yu(FUZ):+.1f} years of guideline/HTA use before TREMFYA's US LOE signal; each quarter of delay costs a quarter of that. "
                   "It answers perianal disease only: no endoscopic, histologic or biomarker endpoint is registered (AI-E02). Submission target Dec 2026 (REC-002).",
                   "NCT05347095; GAP-04; REC-002", 0.85))
derived_ai.append(("AI-004", "so-what", "SI-ICO-02", "Oral market gets crowded before icotrokinra's IBD launch",
                   f"Obefazimod's NDA (planned Q4 2026) and tulisokibart's positive ATLAS-UC mean at least one new oral and one new mechanism may launch before icotrokinra. ICONIC-UC topline is expected around {mo(WB[ICU]['readout_date'])} (primary completion Jan 2028) and ICONIC-CD around {mo(WB[ICD]['readout_date'])}; "
                   "with filing and review, IBD launches come around 2029 (estimate), about two years before TREMFYA's US LOE signal. What it means: evidence that takes years to pay back has more time to do so for icotrokinra than for TREMFYA (AI-PF01).",
                   "EV-002; EV-001; NCT07196748; NCT07196722", 0.75))
derived_ai.append(("AI-005", "summary", "SI-TRE-07", "JNJ-4804 moved to Phase 3 despite Phase 2b primary misses; its protection needs checking against guselkumab's LOE",
                   f"DUET-UC/CD missed their primary endpoints but showed numerically higher week-48 remission, especially in multi-class refractory subgroups; DUET ENCORE Phase 3 started May 2026 (topline around {mo(WB[DEC]['readout_date'])}–{mo(WB[DEU]['readout_date'])}). "
                   "Question for J&J IP: JNJ-4804 combines guselkumab and golimumab, so when guselkumab biosimilars can enter (US signal mid-2031) its protection rests on co-formulation and use patents, not on either antibody. Its planning LOE in the dashboard is a placeholder.",
                   "NCT05242471; NCT05242484; NCT07577856; NCT07577843; LOE-JNJ4804-US", 0.75))
derived_ai.append(("AI-006", "change-since-last", "GLOBAL", "Five material competitor and market events since June 2026; the newest is ENTYVIO biosimilar litigation",
                   "Tulisokibart ATLAS-UC positive (Jun); ABTECT maintenance positive, NDA planned Q4 2026 (Jun); STELARA Q2 sales down 55.7% on biosimilar erosion (Jul); SKYRIZI SC induction filed with the EMA (Sep); "
                   "Takeda sued Alvotech over the ENTYVIO biosimilar AVT16, with an FDA decision expected Q1 2027 (Sep; AI-L03).",
                   "EV-001; EV-002; EV-012; EV-102; W-005", 0.85))
# revisions of data-driven insights
revise("AI-P03", add="A network meta-analysis is also the fastest evidence type: started now it still gives about 2.3 years of use before TREMFYA's US LOE signal (AI-L02).")
for iid, x in [(x[0], x) for x in derived_ai if x[0] in ("AI-P04", "AI-P05")]:
    if x[2] == "GAP-03":
        nt = sum(1 for p in PROFILE.values() if p["side"] == "J&J" and p["brand_id"] == "TRE" and "TRAN" in p["domains"])
        revise(iid, add=f"J&J's pipeline here is the deepest ({nt} TREMFYA studies register transmural endpoints, AI-E01), but none has reported yet: REASON reads out around {mo(WB[REA]['readout_date'])} (REC-005). Suggested action: share design and baseline bowel-ultrasound data now.")
    if x[2] == "GAP-11":
        revise(iid, add=f"GUARDIAN, the J&J pouchitis study, reads out around {mo(WB[GUA]['readout_date'])} and gives {yu(GUA):+.1f} years of use before TREMFYA's US LOE signal. What it means: most of its value falls outside TREMFYA's exclusivity window; record the reason to continue (e.g. patient need) as an exception, or support it as investigator-led.")
revise("AI-P06", add=f"Order by LOE: FUZION CD first ({yu(FUZ):+.1f} years of use if published by {mo(WB[FUZ]['paper_date'])}); ANTHEM-UC and DUET papers have long runways but frame ICONIC and DUET ENCORE, so publish them before those Phase 3 readouts in 2028.")
revise("AI-D01", add=f"Timing: CHARGE's answer reaches guidelines around {mo(WB[CHG]['uptake_date'])}, about when TREMFYA's US LOE signal falls (AI-L01), so it will mostly serve class and portfolio positioning; review its business case (REC-004).")
nt = sum(1 for p in PROFILE.values() if p["side"] == "J&J" and p["brand_id"] == "TRE" and "TRAN" in p["domains"])
revise("AI-E01", add=f"Portfolio caveat: all {nt} J&J studies with transmural endpoints are TREMFYA studies, and most report close to its US LOE signal; icotrokinra and JNJ-4804 register no transmural or biomarker endpoints (AI-PF02).")
spend = defaultdict(float); cnt = Counter(); late_sp = sum(w["cost_usd"] or 0 for w in WIN if w["brand_id"] == "TRE" and w["protected_years"] < 1)
late_n = sum(1 for w in WIN if w["brand_id"] == "TRE" and w["protected_years"] < 1)
for w in WIN: spend[w["brand_id"]] += w["cost_usd"] or 0; cnt[w["brand_id"]] += 1
revise("AI-L01", add=f"Portfolio view: icotrokinra ({cnt['ICO']} studies) and JNJ-4804 ({cnt['JNJ4804']}) all give 8+ years of use on placeholder LOE dates (AI-PF01).")
# new portfolio insights
succ = {b: Counter(c for p in PROFILE.values() if p["side"] == "J&J" and p["brand_id"] == b and p["n_outcomes"] for c in p["domains"]) for b in ("ICO", "JNJ4804")}   # registered trials only
derived_ai.append(("AI-PF01", "decision", "SI-ICO-06",
                   "J&J portfolio: icotrokinra and JNJ-4804 arrive about two years before TREMFYA's US LOE signal, and no study positions the three against each other (GAP-20)",
                   f"Timelines (registry, derived): ICONIC-UC topline around {mo(WB[ICU]['readout_date'])}, DUET ENCORE around {mo(WB[DEC]['readout_date'])}–{mo(WB[DEU]['readout_date'])}, ICONIC-CD around {mo(WB[ICD]['readout_date'])}; TREMFYA's US LOE signal mid-2031. "
                   "All three act on the IL-23 pathway and are developed for the same UC and CD patients. "
                   f"GAP-20 (sequencing TREMFYA and icotrokinra) has no study ({gap_rows['GAP-20']['planned_coverage_pct']}% coverage); GAP-19 (oral vs injectable preference) rests on one planned choice study. "
                   f"Simulated evidence spend: TREMFYA ${spend['TRE'] / 1e6:.0f}M across {cnt['TRE']} studies (${late_sp / 1e6:.0f}M on {late_n} studies with under a year of use before LOE), icotrokinra ${spend['ICO'] / 1e6:.0f}M ({cnt['ICO']}), JNJ-4804 ${spend['JNJ4804'] / 1e6:.0f}M ({cnt['JNJ4804']}). "
                   "What it means: sequencing and switching (who starts on oral icotrokinra rather than TREMFYA, what works after an IL-23, where JNJ-4804 fits in refractory disease) are open questions with no study. Suggested action: build the portfolio evidence plan now so it is ready by the 2029 launches: IL-23-experienced subgroups in ICONIC and DUET ENCORE, a switching and sequencing real-world cohort, and new TREMFYA studies whose questions carry over to the successors (REC-010).",
                   "GAP-20; GAP-19; NCT07196748; NCT07196722; NCT07577856; NCT07577843; REC-010", 0.7))
derived_ai.append(("AI-PF02", "risk alert", "SI-ICO-02",
                   "Evidence depth does not transfer: icotrokinra and JNJ-4804 register no transmural or biomarker endpoints",
                   f"All {nt} J&J studies with transmural (bowel-ultrasound or MR) endpoints are TREMFYA studies. The registered icotrokinra trials cover "
                   + ", ".join(DNAME[c].split(' (')[0].lower() for c, _, _ in DOMAINS if succ['ICO'][c]) + "; JNJ-4804's cover "
                   + ", ".join(DNAME[c].split(' (')[0].lower() for c, _, _ in DOMAINS if succ['JNJ4804'][c]) + ". "
                   "What it means: unless the successors add these endpoints, the portfolio's transmural evidence (AI-E01) stays with the product that loses exclusivity first. "
                   "Suggested action: bowel-ultrasound and faecal calprotectin substudies in the ICONIC and DUET ENCORE long-term extensions, or post-launch real-world studies with bowel ultrasound (REC-011). Not registered means not promised; confirm with the study teams.",
                   "NCT07196748; NCT07196722; NCT07577856; NCT07577843; GAP-03; REC-011", 0.7))
LATE_RECS = [
    ("REC-010", "E1", "strategic", "plan", "GAP-20", "Build a portfolio evidence plan for TREMFYA, icotrokinra and JNJ-4804 (sequencing and switching): IL-23-experienced subgroups in ICONIC and DUET ENCORE, a switching real-world cohort, ready for the 2029 launches (AI-PF01)", 400000, "2027-03-31", "F-GMAF", 0.7),
    ("REC-011", "E3", "strategic", "add endpoints", "NCT07196722; NCT07577843", "Add bowel-ultrasound and faecal calprotectin to the icotrokinra and JNJ-4804 long-term extensions, so evidence depth carries over from TREMFYA (AI-PF02)", 250000, "2027-06-30", "F-GMAF", 0.6),
]

# =============================================================== AI assistants: how chat assistants answer patient and HCP questions about IBD drugs
# Each file in data/raw/llm/ is one run (assistant x date) of the fixed question bank. Monthly runs add files; the dashboard compares
# every run with the previous run of the same assistant.
LLM_DIR = ROOT / "data" / "raw" / "llm"
LLM_NAMES = {"TRE": "TREMFYA", "ICO": "icotrokinra", "JNJ4804": "JNJ-4804", "SKY": "SKYRIZI", "RIN": "RINVOQ", "OMV": "OMVOH", "ENT": "ENTYVIO",
             "STE": "STELARA", "IFX": "infliximab", "ADA": "adalimumab", "ZEP": "ZEPOSIA", "VEL": "VELSIPITY", "OBE": "obefazimod", "TL1A": "anti-TL1A", "TOF": "tofacitinib"}
JNJ_TRIALS = ("GALAXI", "GRAVITI", "QUASAR", "ASTRO", "FUZION", "CHARGE", "ANTHEM", "ICONIC", "VEGA", "DUET", "REASON")
t_lq = table("llm_questions", "Fixed question bank asked to AI chat assistants every run (patient, HCP and accuracy-check questions).", ["question_id"])
QBANK = {}
for qid, persona, q, tests in cp.LLM_QUESTIONS:
    QBANK[qid] = persona
    t_lq.add(RF, {"question_id": qid, "persona": persona, "question": q, "tests": tests, "branded": qid in ("P11",) or persona == "accuracy"})
t_lr = table("llm_runs", "One row per run of the question bank in an AI assistant (observed answers, scored by keyword rules plus analyst review).", ["run_id"])
t_la = table("llm_answers", "One row per question per run: drugs named in order, studies cited, web search, and the analyst finding.", ["answer_id"])
t_ls = table("llm_drug_share", "Derived: share of unbranded answers that name each drug, and name it first, per run and persona.", ["share_id"])
def issue_of(flag):
    f = flag.upper()
    return ("correct" if f.startswith("CORRECT") else "inaccurate" if re.search(r"^(INACCURATE|WRONG)", f) else "misleading" if re.search(r"^(MISLEADING|UNDERSTATES)", f)
            else "omission" if f.startswith("OMISSION") else "")
LLM_RUNS = []
for f in sorted(LLM_DIR.glob("*.json")) if LLM_DIR.exists() else []:
    d = json.loads(f.read_text()); run = d["run"]
    assistant = "ChatGPT" if f.stem.startswith("chatgpt") else "Claude" if f.stem.startswith("claude") else f.stem.split("_")[0].title()
    run_id = f"RUN-{run['date']}-{assistant.upper()}"
    web_list = set(d.get("web_search_used") or [])
    all_web = "web search on" in run["assistant"]
    answers = []
    for a in d["questions"]:
        qid = a["id"]; persona = QBANK.get(qid, a.get("persona", ""))
        drugs = [re.sub(r"\(.*?\)", "", x).strip() for x in (a.get("drugs") or "").split(">") if x.strip()]
        iss = issue_of(a.get("flags", ""))
        row = {"answer_id": f"{run_id}-{qid}", "run_id": run_id, "assistant": assistant, "date": run["date"], "question_id": qid, "persona": persona,
               "drugs_in_order": "; ".join(drugs), "first_drug": drugs[0] if drugs else "", "tremfya_named": "TRE" in drugs,
               "jnj_named": "; ".join(b for b in ("TRE", "ICO", "JNJ4804") if b in drugs), "studies_cited": a.get("studies", ""),
               "jnj_trials_cited": "; ".join(t for t in JNJ_TRIALS if re.search(t, a.get("studies", ""), re.I)),
               "sources": a.get("sources", ""), "web_search": all_web or qid in web_list, "issue_type": iss, "finding": a.get("flags", "")}
        answers.append(row)
        t_la.add(PV, row, src=["SRC-LLM"], der=("drugs_in_order", "first_drug", "tremfya_named", "jnj_named", "jnj_trials_cited", "issue_type", "finding"))
    unb = {"patient": [x for x in answers if x["persona"] == "patient" and x["question_id"] != "P11"], "HCP": [x for x in answers if x["persona"] == "HCP"]}
    for persona, rows in unb.items():
        for code, name in LLM_NAMES.items():
            n = sum(1 for x in rows if code in x["drugs_in_order"].split("; ")); first = sum(1 for x in rows if x["first_drug"] == code)
            if n or code in ("TRE", "ICO", "JNJ4804"):
                t_ls.add(DE, {"share_id": f"{run_id}-{persona}-{code}", "run_id": run_id, "assistant": assistant, "date": run["date"], "persona": persona,
                              "drug": code, "drug_name": name, "answers": len(rows), "named": n, "named_pct": round(100 * n / max(1, len(rows))), "named_first": first},
                         src=["SRC-LLM"])
    acc = [x for x in answers if x["persona"] == "accuracy"]
    rr = {"run_id": run_id, "assistant": assistant, "date": run["date"], "setup": run["assistant"], "method": run["method"],
          "questions": len(answers), "web_search_answers": sum(1 for x in answers if x["web_search"]),
          "tremfya_patient_pct": round(100 * sum(1 for x in unb["patient"] if x["tremfya_named"]) / max(1, len(unb["patient"]))),
          "tremfya_hcp_pct": round(100 * sum(1 for x in unb["HCP"] if x["tremfya_named"]) / max(1, len(unb["HCP"]))),
          "tremfya_named_first": sum(1 for x in unb["patient"] + unb["HCP"] if x["first_drug"] == "TRE"),
          "accuracy_correct": sum(1 for x in acc if x["issue_type"] == "correct"), "accuracy_total": len(acc),
          "issues": sum(1 for x in answers if x["issue_type"] in ("inaccurate", "misleading", "omission")),
          "previous_run_id": next((r["run_id"] for r in reversed(LLM_RUNS) if r["assistant"] == assistant), None)}
    LLM_RUNS.append(rr)
    t_lr.add(PV, rr, src=["SRC-LLM"], der=("questions", "web_search_answers", "tremfya_patient_pct", "tremfya_hcp_pct", "tremfya_named_first", "accuracy_correct", "accuracy_total", "issues", "previous_run_id"))
    LLM_RUNS[-1]["_answers"] = answers
if LLM_RUNS:
    latest = {}
    for r in LLM_RUNS: latest[r["assistant"]] = r
    L = list(latest.values())
    both = lambda qid, pred: all(pred(next((x for x in r["_answers"] if x["question_id"] == qid), {})) for r in L)
    p8 = both("P8", lambda x: not x.get("tremfya_named"))
    h16 = both("H16", lambda x: "ICO" not in (x.get("drugs_in_order") or ""))
    derived_ai.append(("AI-LLM01", "risk alert", "SI-TRE-03",
                       "AI assistants rarely surface TREMFYA's differentiators to patients: named in " + " and ".join(f"{r['tremfya_patient_pct']}% of {r['assistant']}'s" for r in L) + " unbranded patient answers, never first",
                       "Latest runs (" + ", ".join(f"{r['assistant']} {r['date']}" for r in L) + "; one run each): TREMFYA is named in " + ", ".join(f"{r['tremfya_hcp_pct']}% of {r['assistant']}'s" for r in L) + " HCP answers, where both describe its SC induction and FUZION CD correctly. "
                       + ("In the patient question about perianal fistula, neither names guselkumab. " if p8 else "")
                       + "ChatGPT leaves TREMFYA out of the home-injection question; Claude includes it last and hedged. "
                       + "What it means: patient-facing answers lean on patient-organisation pages and older knowledge (Claude searched the web for only one patient question). "
                       + "Suggested action: make accurate public information easy to find (peer-reviewed FUZION CD paper, plain-language summaries of GRAVITI, ASTRO and FUZION). Monitoring only: no attempt to steer AI answers.",
                       "GAP-04; GAP-10; SRC-LLM", 0.6))
    derived_ai.append(("AI-LLM02", "so-what", "SI-TRE-01",
                       "In AI answers the IBD 'head-to-head' story belongs to SEQUENCE; GALAXI's comparison with ustekinumab is dropped or called exploratory" + ("; icotrokinra is missing from pipeline answers" if h16 else ""),
                       "Asked which head-to-head trials exist, ChatGPT lists only the Phase 2 GALAXI-1 and Claude calls the GALAXI ustekinumab arms exploratory, while both, asked about GALAXI directly, report better endoscopic outcomes than ustekinumab. "
                       "SEQUENCE (risankizumab vs ustekinumab) is cited in 5 ChatGPT answers. " + ("Neither assistant lists icotrokinra in late-stage development; ChatGPT describes JNJ-4804 as 'Phase 2b positive'. " if h16 else "")
                       + "What it means: how a comparison is published and labelled shapes how assistants rank it. Suggested action: make sure the GALAXI 2/3 ustekinumab comparison and CHARGE are clearly described in peer-reviewed and public trial records.",
                       "GAP-01; GAP-02; SRC-LLM", 0.6))

# ---- oral podium: full oral slots (ECCO OP, DDW numbered, UEG Week presentation, ACG programme orals incl. late-breakers)
# at the four major congresses. Digital orals (ECCO DOP) are counted separately; they are not a podium slot.
BIG4 = ("ECCO", "DDW", "UEGW", "ACG")
ORAL_T = ("Oral", "Late-breaking oral")
c4 = [p for p in PUBLIST if p["kind"] == "congress" and p["series"] in BIG4]
pod = {}
for b in ("TRE", "ICO", "SKY", "RIN", "ENT", "OMV", "OBE", "TUL", "DUV", "AFI"):
    mine = [p for p in c4 if b in p["_bt"]]
    o = [p for p in mine if p["presentation_type"] in ORAL_T]
    pod[b] = {"abstracts": len(mine), "orals": len(o), "rwe_orals": sum(1 for p in o if p["analysis_type"] == "RWE"),
              "conv": round(100 * len(o) / max(1, len(mine)))}
BN = {"TRE": "TREMFYA", "ICO": "icotrokinra", "SKY": "Skyrizi", "RIN": "Rinvoq", "ENT": "Entyvio", "OMV": "Omvoh"}
ranked = sorted(("TRE", "SKY", "RIN", "ENT", "OMV"), key=lambda b: -pod[b]["orals"])
derived_ai.append(("AI-P08", "opportunity", "SI-TRE-01",
                   f"TREMFYA has the highest oral selection rate among IL-23, JAK and integrin brands ({pod['TRE']['conv']}%) and the most full orals ({pod['TRE']['orals']})",
                   f"Across ECCO, DDW, UEG Week and ACG (3 years), {pod['TRE']['conv']}% of TREMFYA abstracts were selected as full orals vs "
                   + ", ".join(f"{BN[b]} {pod[b]['conv']}%" for b in ("SKY", "RIN", "ENT", "OMV")) + ". TREMFYA had fewer abstracts (" + str(pod['TRE']['abstracts']) + " vs " + ", ".join(BN[b] + " " + str(pod[b]["abstracts"]) for b in ("SKY", "RIN", "ENT", "OMV")) + ") but a higher share became orals. "
                   "ACG orals from the official programme; ECCO digital orals excluded.",
                   "SI-TRE-01", 0.85))
rwe_o = {b: [p for p in c4 if b in p["_bt"] and p["presentation_type"] in ORAL_T and p["analysis_type"] == "RWE"] for b in ("TRE", "RIN", "SKY", "ENT")}
cmp_rx = r"compar|\bversus\b|\bvs\.?\b"
comp_n = {b: sum(1 for p in o if re.search(cmp_rx, p["title"], re.I)) for b, o in rwe_o.items()}
aff_unknown = sum(1 for b in ("RIN", "SKY", "ENT") for p in rwe_o[b] if not p.get("affiliation_known"))
aff_total = sum(len(rwe_o[b]) for b in ("RIN", "SKY", "ENT"))
tre_rwe = rwe_o["TRE"][0]["title"] if rwe_o["TRE"] else ""
derived_ai.append(("AI-P09", "so-what", "SI-TRE-05",
                   f"TREMFYA's orals come almost entirely from trials: {pod['TRE']['rwe_orals']} real-world oral vs {pod['RIN']['rwe_orals']} Rinvoq, {pod['SKY']['rwe_orals']} Skyrizi, {pod['ENT']['rwe_orals']} Entyvio",
                   f"{pod['TRE']['orals'] - pod['TRE']['rwe_orals']} of {pod['TRE']['orals']} TREMFYA full orals present trial-programme analyses (primary, extension, subgroup, post-hoc) or economic models; randomised trial data is the higher level of evidence, and this share is a strength. "
                   + (f"The one real-world oral is not a guselkumab study: it is an upadacitinib comparison that includes guselkumab as a comparator ('{tre_rwe[:80].title()}…'). " if re.search(r"upadacitinib", tre_rwe, re.I) else "")
                   + f"Of the competitors' real-world orals, {comp_n['RIN']} (Rinvoq), {comp_n['SKY']} (Skyrizi) and {comp_n['ENT']} (Entyvio) compare drugs in routine practice, by their titles. "
                   f"Who ran and funded them is not known for {aff_unknown} of {aff_total}, so this dataset cannot say whether they are independent. "
                   "Question to decide (not a conclusion): are there questions trials will not answer for guselkumab, such as comparisons with upadacitinib or sequencing, where real-world data would be needed (GAP-07, GAP-20)? "
                   "Real-world analysis type is assigned from titles, so counts are approximate.",
                   "GAP-07; GAP-20", 0.75))
tl1a = sum(pod[b]["orals"] for b in ("TUL", "DUV", "AFI"))
derived_ai.append(("AI-P10", "risk alert", "SI-ICO-02",
                   f"Anti-TL1A agents hold {tl1a} full orals vs {pod['ICO']['orals']} for icotrokinra",
                   f"{pod['ICO']['conv']}% of icotrokinra abstracts and "
                   f"{round(100 * tl1a / max(1, sum(pod[b]['abstracts'] for b in ('TUL', 'DUV', 'AFI'))))}% of anti-TL1A abstracts became orals. "
                   f"The TL1A class (tulisokibart, duvakitug, afimkibart) has {tl1a / max(1, pod['ICO']['orals']):.0f}x icotrokinra's full orals from {sum(pod[b]['abstracts'] for b in ('TUL', 'DUV', 'AFI'))} abstracts vs {pod['ICO']['abstracts']}; icotrokinra's selection rate is higher. "
                   "Suggested action: plan ICONIC-UC/CD design, baseline and oral-vs-injectable preference data for oral slots in 2026-27 (GAP-18, GAP-19).",
                   "GAP-18; GAP-19", 0.75))
for iid, typ, scope, head, body, cites, conf in derived_ai:
    t_ai.add(DE, {"insight_id": iid, "insight_type": typ, "scope_entity_ids": scope, "headline": head, "body": body,
                  "cited_entity_ids": cites, "confidence": conf, "review_status": "auto (data-driven)", "generated_at": iso(TODAY)},
             src=["SRC-PUBMED", "SRC-CROSSREF", "SRC-UEG"])

t_rec = table("recommendations", "SIMULATED decision-engine recommendations.", ["rec_id"])
RECS = [
    ("REC-001", "E2", "strategic", "publish", "GAP-02", "Publish the existing guselkumab vs risankizumab UC NMA (UEGW 2025) in a peer-reviewed journal and extend it to vedolizumab before REVAMP reads out", 150000, "2026-12-31", "F-HEOR", 0.8),
    ("REC-002", "T2", "tactical", "publish", "NCT05347095", "Prioritise FUZION CD primary manuscript submission (target Gastroenterology)", 60000, "2026-12-15", "F-GMAF", 0.85),
    ("REC-003", "E3", "strategic", "accelerate", "GAP-10", "Ask whether GORGEOUS (German guselkumab RWE, N=500) can report an SC-induction cohort at an earlier data cut, and partner with the independent groups already publishing guselkumab RWE (DDW 2026 propensity-matched studies) rather than starting a new claims study", 300000, "2026-11-30", "F-USMAF", 0.7),
    ("REC-004", "E4", "strategic", "review business case", "NCT07499232", "Review CHARGE's business case against the US LOE signal (its answer reaches guidelines around Aug 2031): value for EU HTA re-assessment, class positioning for icotrokinra, interim-analysis options; then decide EMEA MAF co-funding (AI-D01)", 0, "2026-11-30", "F-EMEAMAF", 0.6),
    ("REC-005", "T1", "tactical", "submit to venue", "NCT06408935", "Target REASON primary as late-breaker at UEGW 2027; pre-plan encore at ACG 2027", 0, "2027-06-30", "F-GMAF", 0.7),
    ("REC-006", "T3", "tactical", "reactive material", "EV-001", "Prepare TL1A scientific-exchange pack for MSLs ahead of ATLAS-UC full presentation at UEGW 2026", 40000, "2026-10-10", "F-GMAF", 0.8),
    ("REC-007", "E1", "strategic", "fund", "GAP-19", "Fund oral vs SC preference DCE (SIM-DCE-01) to support TREMFYA-icotrokinra portfolio story", 500000, "2027-01-15", "F-GMAF", 0.65),
    ("REC-008", "T6", "tactical", "encore", "OUT-P008", "Encore FUZION at APDW/JDDW 2027 for APAC markets", 20000, "2027-06-30", "F-APACMAF", 0.6),
    ("REC-009", "E1", "strategic", "decide", "LOE-TRE-US", "Confirm TREMFYA planning LOE (US, EU) with J&J IP, then review the TREMFYA studies that land at or after it (AI-L01)", 0, "2026-12-15", "F-GMAF", 0.75),
]
RECS += LATE_RECS
for rid, eng, lvl, act, target, stmt, cost, dl, fid, conf in RECS:
    t_rec.add(SI, {"rec_id": rid, "engine": eng, "decision_level": lvl, "action_type": act, "target_entity_ids": target,
                   "statement": stmt, "cost_usd": cost, "deadline": dl, "funder_id": fid, "confidence": conf, "status": "proposed"}, src=["SRC-AI"])

t_scn = table("scenarios", "SIMULATED scenarios for war-gaming.", ["scenario_id"])
for sid, name, typ, assumptions in [
    ("SCN-01", "Base case", "base", {"EV-101": "approved 2026-Q4", "EV-107": "positive 2027-Q4", "EV-103": "approved 2027-Q4"}),
    ("SCN-02", "Skyrizi SC induction delayed", "bull", {"EV-101": "CRL / delay 12m", "EV-107": "positive"}),
    ("SCN-03", "Competitive squeeze", "bear", {"EV-101": "approved", "EV-107": "superiority vs vedolizumab", "EV-104": "strong maintenance", "NCT07499232": "enrollment slips 6m"}),
]:
    t_scn.add(SI, {"scenario_id": sid, "name": name, "type": typ, "assumptions": assumptions}, src=["SRC-SIM"])

t_dec = table("decision_log", "SIMULATED decision log examples.", ["decision_id"])
t_dec.add(SI, {"decision_id": "DEC-001", "date": "2026-04-10", "forum": "Global Evidence Council",
               "question": "Proceed with H2H vs risankizumab in CD?", "decision": "Approved CHARGE (Ph3b, N=530)",
               "rationale": "Close GAP-01 before guideline updates; SEQUENCE sets precedent", "decided_by": "Global Medical Affairs head (role)"}, src=["SRC-SIM"])
t_dec.add(SI, {"decision_id": "DEC-002", "date": "2026-05-12", "forum": "IBD Portfolio Committee",
               "question": "Advance JNJ-4804 despite Ph2b primary misses?", "decision": "Advance to Ph3 DUET ENCORE",
               "rationale": "Numerical benefit in refractory subgroups; differentiated combination", "decided_by": "Portfolio committee (role)"}, src=["SRC-SIM"])

# =============================================================== export
def jsonable(v):
    return json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v


def apply_added_rows():
    for o in OVERRIDES:
        if o["op"] != "add" or o["table"] not in TABLES:
            continue
        t = TABLES[o["table"]]
        fields = {k: v for k, v in (o.get("row") or {}).items() if not k.startswith("_")}
        row = {"fields": fields, "prov": {k: MN for k in fields}, "src": ["SRC-MANUAL"], "deleted": False, "key": str(o["key"]),
               "note": f'[{o.get("editor", "?")} {str(o.get("ts", ""))[:10]}] added: {o.get("note", "")}'}
        APPLIED.add(o["id"])
        t.apply_overrides(row, skip_add=True)  # later edits / deletion of the added row
        t.rows.append(row)
    for name, t in TABLES.items():
        # re-assert manual values last, so later derivations cannot overwrite them
        for r in t.rows:
            for o in OVR_BY.get((name, r["key"]), []):
                if o["op"] == "set":
                    r["fields"][o["field"]] = o["new"]
                    r["prov"][o["field"]] = MN
        t.rows = [r for r in t.rows if not r["deleted"]]


# Fields that are AI judgement rather than found facts, calculations or placeholders. Tagged at export so the dashboard can
# show them apart from facts; a value edited in the Data Editor keeps its "manual" tag.
AI_INFERRED = {
    "ai_insights": ["headline", "body"],
    "competitor_strategies": ["inferred_strategy_statement", "strategic_pillars", "target_segments", "evidence_chain", "confidence",
                              "alternative_hypotheses", "leading_indicators_to_watch"],
    "competitor_gaps": ["gap_type", "description", "severity_1to5", "jnj_can_exploit"],
    "competitive_events": ["probability_positive"],
    "geographies": ["payer_archetype"],
    "llm_answers": ["issue_type", "finding"],
    "llm_runs": ["accuracy_correct", "issues"],
    "loe_start_by": ["readout_lag_months", "paper_lag_months", "uptake_lag_months", "min_years_before_loe"],
}


def tag_ai_inferred():
    for name, fields in AI_INFERRED.items():
        for r in TABLES[name].rows:
            for f in fields:
                if f in r["prov"] and r["prov"][f] != MN:
                    r["prov"][f] = AIX


def export():
    tag_ai_inferred()
    apply_added_rows()
    out_json = ROOT / "data" / "json"
    out_json.mkdir(parents=True, exist_ok=True)
    stats = {}
    unapplied = [o for o in OVERRIDES if o["id"] not in APPLIED]
    if unapplied:
        print(f"WARNING: {len(unapplied)} manual edit(s) did not match a row (table/key changed?):",
              ", ".join(f'{o["table"]}:{o["key"]}' for o in unapplied[:10]))
    for name, t in TABLES.items():
        rows = []
        for r in t.rows:
            prov = r["prov"]
            rec = dict(r["fields"])
            rec["_provenance"] = {
                "data_origin": t.origin_summary(r),
                "simulated_fields": [k for k, v in prov.items() if v == SI],
                "derived_fields": [k for k, v in prov.items() if v == DE],
                "unverified_fields": [k for k, v in prov.items() if v == PU],
                "manual_fields": [k for k, v in prov.items() if v == MN],
                "ai_inferred_fields": [k for k, v in prov.items() if v == AIX],
                "field_origin": prov,
            }
            rec["_key"] = r["key"]
            rec["_source_ids"] = r["src"]
            if r["note"]:
                rec["_note"] = r["note"]
            rows.append(rec)
        (out_json / f"{name}.json").write_text(json.dumps({"table": name, "description": t.description, "built": iso(TODAY), "rows": rows},
                                                          indent=1, ensure_ascii=False, default=str))
        cells = Counter(v for r in t.rows for k, v in r["prov"].items() if k not in t.key_fields)
        stats[name] = {"rows": len(t.rows), "cells": dict(cells)}
    (out_json / "_manifest.json").write_text(json.dumps({"built": iso(TODAY), "tables": stats}, indent=1))
    try:
        write_xlsx(stats)
    except ImportError:
        print("NOTE: openpyxl is not installed, so the Excel file was not rebuilt (JSON data is up to date).\n"
              "      Install it with:  python3 -m pip install --user openpyxl")
    return stats


def write_xlsx(stats):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    fills = {SI: PatternFill("solid", fgColor="FFD8A8"), DE: PatternFill("solid", fgColor="D0E4F7"),
             PU: PatternFill("solid", fgColor="FFF3B0"), RF: PatternFill("solid", fgColor="E8E8E8"),
             MN: PatternFill("solid", fgColor="C6EFCE")}
    wb = Workbook()
    ws = wb.active
    ws.title = "README"
    lines = [
        ("IBD Evidence Intelligence - prototype dataset", True),
        (f"Built {iso(TODAY)} by scripts/build_dataset.py from ClinicalTrials.gov and curated web sources.", False),
        ("", False),
        ("CELL COLOUR = PROVENANCE OF THAT VALUE", True),
        ("white   = public_verified   (registry / web source checked on build date)", False),
        ("yellow  = public_unverified (public knowledge not re-checked - verify)", False),
        ("blue    = derived           (calculated by a stated rule; recomputes when inputs change)", False),
        ("orange  = simulated         (invented for the prototype - REPLACE with real data)", False),
        ("grey    = reference         (taxonomy / configuration defined by the team)", False),
        ("green   = manual            (corrected / updated by the team in the Data Editor; see the note column)", False),
        ("", False),
        ("Every row also has: data_origin (row summary), simulated_fields, derived_fields, unverified_fields, ai_inferred_fields, source_ids.", False),
        ("To replace simulated data: filter 'simulated_fields' non-empty, update the value, and move the source into curated_public.py.", False),
        ("", False),
        ("TABLE SUMMARY", True),
    ]
    for text, bold in lines:
        ws.append([text])
        if bold:
            ws.cell(ws.max_row, 1).font = Font(bold=True)
    ws.append(["table", "rows", "public_verified cells", "public_unverified", "derived", "simulated", "reference", "manual", "description"])
    for c in ws[ws.max_row]:
        c.font = Font(bold=True)
    for name, s in stats.items():
        c = s["cells"]
        ws.append([name, s["rows"], c.get(PV, 0), c.get(PU, 0), c.get(DE, 0), c.get(SI, 0), c.get(RF, 0), c.get(MN, 0), TABLES[name].description])
    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["I"].width = 110
    for name, t in TABLES.items():
        sh = wb.create_sheet(name[:31])
        cols = list(dict.fromkeys(k for r in t.rows for k in r["fields"]))
        header = cols + ["data_origin", "simulated_fields", "derived_fields", "unverified_fields", "manual_fields", "source_ids", "note"]
        sh.append(header)
        for c in sh[1]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor="2F3B52")
            c.alignment = Alignment(wrap_text=True, vertical="top")
        for ri, r in enumerate(t.rows, start=2):
            prov = r["prov"]
            vals = [jsonable(r["fields"].get(k)) for k in cols]
            vals += [t.origin_summary(r), ", ".join(k for k, v in prov.items() if v == SI),
                     ", ".join(k for k, v in prov.items() if v == DE), ", ".join(k for k, v in prov.items() if v == PU),
                     ", ".join(k for k, v in prov.items() if v == MN),
                     ", ".join(r["src"]), r["note"]]
            sh.append(vals)
            for j, k in enumerate(cols, 1):
                tag = prov.get(k)
                if tag in fills:
                    sh.cell(ri, j).fill = fills[tag]
        sh.freeze_panes = "B2"
        sh.auto_filter.ref = sh.dimensions
        for j, k in enumerate(header, 1):
            width = max([len(str(k))] + [len(str(sh.cell(i, j).value or "")) for i in range(2, min(len(t.rows) + 1, 60) + 1)])
            sh.column_dimensions[get_column_letter(j)].width = min(max(10, width + 2), 60)
    wb.save(ROOT / "data" / "IBD_Evidence_Dataset.xlsx")


if __name__ == "__main__":
    s = export()
    tot = Counter()
    for v in s.values():
        tot.update(v["cells"])
    print(json.dumps({k: v["rows"] for k, v in s.items()}, indent=0))
    print("cells by provenance:", dict(tot))
