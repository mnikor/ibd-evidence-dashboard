"""Pack data/json into dashboard/data.js (window.IBD) for the static dashboard.

Keeps every table the dashboard uses, trims per-field provenance to the lists of
simulated / derived / unverified fields, and adds ISO numeric codes for the map.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "json"
OUT = ROOT / "dashboard" / "data.js"

TABLES = ["sources", "brands", "moa", "geographies", "care_segments", "stakeholders", "funders", "strategic_imperatives",
          "key_questions", "evidence_gaps", "studies", "study_design", "study_milestones", "study_funding", "study_results",
          "rwe_study_detail", "evidence_outputs", "venues", "key_messages", "competitor_studies",
          "competitive_events", "competitor_gaps", "competitor_strategies", "competitive_impact", "guidelines", "hta_decisions",
          "regulatory_events", "market_metrics", "field_insights", "signals", "ai_insights", "recommendations", "scenarios",
          "publication_ladder_template", "study_enrollment", "publications", "sov_congress", "sov_journal", "sov_analysis", "industry_symposia", "publication_themes",
          "regimens", "product_attributes", "regimen_burden", "watch_items",
          "loe", "study_loe_window", "loe_start_by",
          "evidence_domains", "study_endpoints", "study_evidence_profile", "evidence_depth_by_domain",
          "guideline_positions", "llm_questions", "llm_runs", "llm_answers", "llm_drug_share"]

ISO_NUM = {"USA": 840, "CAN": 124, "GBR": 826, "DEU": 276, "FRA": 250, "ITA": 380, "ESP": 724, "NLD": 528, "POL": 616, "CHE": 756,
           "SAU": 682, "JPN": 392, "CHN": 156, "KOR": 410, "AUS": 36, "BRA": 76, "ARG": 32, "AUT": 40, "BLR": 112, "BEL": 56,
           "BIH": 70, "BGR": 100, "CHL": 152, "COL": 170, "HRV": 191, "CZE": 203, "DNK": 208, "DOM": 214, "EGY": 818, "EST": 233,
           "FIN": 246, "GEO": 268, "GRC": 300, "HKG": 344, "HUN": 348, "IND": 356, "IRL": 372, "ISR": 376, "JOR": 400, "LVA": 428,
           "LBN": 422, "LTU": 440, "MYS": 458, "MEX": 484, "MDA": 498, "NZL": 554, "MKD": 807, "NOR": 578, "PER": 604, "PRT": 620,
           "PRI": 630, "ROU": 642, "RUS": 643, "SRB": 688, "SGP": 702, "SVK": 703, "SVN": 705, "ZAF": 710, "SWE": 752, "TWN": 158,
           "THA": 764, "TUN": 788, "TUR": 792, "UKR": 804, "ARE": 784}


def slim(row):
    p = row.pop("_provenance", {})
    row.pop("_note", None)
    row["_o"] = p.get("data_origin")
    row["_sim"] = p.get("simulated_fields", [])
    row["_der"] = p.get("derived_fields", [])
    row["_unv"] = p.get("unverified_fields", [])
    row["_man"] = p.get("manual_fields", [])
    row["_ai"] = p.get("ai_inferred_fields", [])
    row["_src"] = row.pop("_source_ids", [])
    return row


def main():
    data = {}
    for t in TABLES:
        f = SRC / f"{t}.json"
        data[t] = [slim(r) for r in json.loads(f.read_text())["rows"]] if f.exists() else []
        if t in ("publications", "sov_congress", "sov_journal", "sov_analysis"):  # provenance is uniform: keep origin only
            keep = {"pub_id", "doi", "pmid", "title", "abstract_code", "kind", "series", "venue", "journal", "year", "date", "presentation_type",
                    "analysis_type", "brands_title", "industry_affiliation", "affiliation_known", "url", "venue", "brand_id", "n", "n_orals",
                    "share_pct", "analysis_type", "_o", "_key", "_man", "company", "linked_study_ids", "linked_gap_ids"}
            data[t] = [{k: v for k, v in r.items() if k in keep} for r in data[t]]
    sites = json.loads((SRC / "study_country_sites.json").read_text())["rows"]
    data["sites"] = [[r["study_id"], r["geo_id"], r["n_sites_registry"]] for r in sites]
    data["iso_num"] = ISO_NUM
    data["country_names"] = {r["geo_id"]: r["country_name"] for r in sites}
    data["manifest"] = json.loads((SRC / "_manifest.json").read_text())
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("window.IBD=" + json.dumps(data, separators=(",", ":"), ensure_ascii=False, default=str) + ";\n")
    # cache-bust the data file reference so browsers pick up rebuilds
    import re, time
    html = OUT.parent / "index.html"
    if html.exists():
        html.write_text(re.sub(r'src="data\.js(\?v=\d+)?"', f'src="data.js?v={int(time.time())}"', html.read_text()))
    print(f"{OUT} {OUT.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
