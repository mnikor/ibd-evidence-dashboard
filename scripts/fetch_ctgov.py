"""Fetch IBD trial records for J&J and competitor assets from the ClinicalTrials.gov v2 API.

Raw responses are saved under data/raw/ctgov/<asset>.json with a retrieval timestamp,
so every registry-derived field in the dataset is traceable to its source.
"""
import json, time, urllib.parse, urllib.request, datetime, pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw" / "ctgov"
API = "https://clinicaltrials.gov/api/v2/studies"
IBD = "ulcerative colitis OR crohn OR inflammatory bowel disease OR pouchitis"

# asset_id -> intervention search terms
ASSETS = {
    "TRE": "guselkumab OR JNJ-78934804 OR JNJ-4804",
    "ICO": "icotrokinra OR JNJ-77242113 OR JNJ-2113 OR PN-235",
    "SKY": "risankizumab",
    "OMV": "mirikizumab",
    "RIN": "upadacitinib",
    "ENT": "vedolizumab",
    "VEL": "etrasimod",
    "ZEP": "ozanimod",
    "STE": "ustekinumab",
    "OBE": "obefazimod OR ABX464",
    "TUL": "tulisokibart OR MK-7240 OR PRA023",
    "DUV": "duvakitug OR TEV-48574 OR SAR447189",
    "AFI": "afimkibart OR RVT-3101 OR RO7790121",
    "MOR": "MORF-057 OR LY4100511",
}

def fetch(term):
    studies, token = [], None
    while True:
        q = {"query.intr": term, "query.cond": IBD, "pageSize": 100, "format": "json"}
        if token:
            q["pageToken"] = token
        with urllib.request.urlopen(f"{API}?{urllib.parse.urlencode(q)}", timeout=60) as r:
            d = json.load(r)
        studies += d.get("studies", [])
        token = d.get("nextPageToken")
        if not token:
            return studies
        time.sleep(0.3)

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for aid, term in ASSETS.items():
        s = fetch(term)
        (OUT / f"{aid}.json").write_text(json.dumps({"asset_id": aid, "query": term, "retrieved_at": now, "studies": s}))
        print(aid, len(s))
