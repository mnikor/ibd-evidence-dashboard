"""Fetch IBD publications and congress abstracts (last 3 years) for J&J and competitor assets.

Sources
  PubMed E-utilities   peer-reviewed / indexed journal articles (with publication types and affiliations)
  Crossref REST API    congress abstract supplements with per-abstract DOIs (ECCO -> J Crohns Colitis,
                       DDW -> Gastroenterology, ACG -> Am J Gastroenterol, Crohn's & Colitis Congress -> Inflamm Bowel Dis)
Raw responses go to data/raw/pubs/ for audit. Known gap: UEG Week abstracts are not indexed per abstract.
"""
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw" / "pubs"
START, END = "2023-09-19", "2026-09-19"

# asset -> search terms (drug names, codes, brand names)
TERMS = {
    "TRE": ["guselkumab", "tremfya"],
    "JNJ4804": ["JNJ-4804", "JNJ-78934804"],
    "ICO": ["icotrokinra", "JNJ-2113", "JNJ-77242113"],
    "STE": ["ustekinumab"],
    "SKY": ["risankizumab"],
    "OMV": ["mirikizumab"],
    "RIN": ["upadacitinib"],
    "ENT": ["vedolizumab"],
    "VEL": ["etrasimod"],
    "ZEP": ["ozanimod"],
    "OBE": ["obefazimod", "ABX464"],
    "TUL": ["tulisokibart", "MK-7240", "PRA023"],
    "DUV": ["duvakitug", "TEV-48574"],
    "AFI": ["afimkibart", "RVT-3101", "RO7790121"],
}
IBD_TIAB = '("ulcerative colitis"[tiab] OR crohn*[tiab] OR "inflammatory bowel"[tiab] OR IBD[tiab] OR pouchitis[tiab])'


def get(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ibd-evidence-prototype/0.1"}), timeout=90) as r:
                return r.read()
        except Exception as e:  # network hiccups / 429
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


# ------------------------------------------------------------------ PubMed
def pubmed(asset, terms):
    q = "(" + " OR ".join(f'"{t}"[tiab]' for t in terms) + ") AND " + IBD_TIAB
    p = {"db": "pubmed", "term": q, "mindate": START.replace("-", "/"), "maxdate": END.replace("-", "/"),
         "datetype": "pdat", "retmax": 5000, "retmode": "json"}
    ids = json.loads(get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urllib.parse.urlencode(p)))["esearchresult"]["idlist"]
    recs = []
    for i in range(0, len(ids), 200):
        xml = get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urllib.parse.urlencode(
            {"db": "pubmed", "id": ",".join(ids[i:i + 200]), "retmode": "xml"}))
        root = ET.fromstring(xml)
        for art in root.findall(".//PubmedArticle"):
            mc = art.find("MedlineCitation")
            a = mc.find("Article")
            title = "".join(a.find("ArticleTitle").itertext()) if a.find("ArticleTitle") is not None else ""
            abstract = " ".join("".join(x.itertext()) for x in a.findall(".//AbstractText"))
            journal = a.findtext("Journal/Title") or ""
            pd = a.find("Journal/JournalIssue/PubDate")
            y = pd.findtext("Year") or (pd.findtext("MedlineDate") or "")[:4]
            m = pd.findtext("Month") or ""
            ad = a.find("ArticleDate")
            edate = f'{ad.findtext("Year")}-{ad.findtext("Month")}-{ad.findtext("Day")}' if ad is not None else ""
            doi = ""
            for aid in art.findall(".//PubmedData/ArticleIdList/ArticleId"):
                if aid.get("IdType") == "doi":
                    doi = (aid.text or "").lower()
            recs.append({
                "source": "PubMed", "pmid": mc.findtext("PMID"), "doi": doi, "title": title, "journal": journal,
                "year": y, "month": m, "epub_date": edate,
                "pub_types": [x.text for x in a.findall("PublicationTypeList/PublicationType")],
                "affiliations": list({x.text for x in a.findall(".//AffiliationInfo/Affiliation") if x.text})[:40],
                "abstract": abstract[:2500], "query_asset": asset,
            })
        time.sleep(0.4)
    return recs


# ------------------------------------------------------------------ Crossref
def crossref(asset, term):
    recs, cursor, pages = [], "*", 0
    while pages < 8:
        p = {"query.bibliographic": term, "filter": f"from-pub-date:{START},until-pub-date:{END}", "rows": 500, "cursor": cursor,
             "select": "DOI,title,container-title,issued,type,page,author"}
        msg = json.loads(get("https://api.crossref.org/works?" + urllib.parse.urlencode(p)))["message"]
        items = msg.get("items", [])
        hits = [i for i in items if term.lower() in " ".join(i.get("title") or []).lower()]
        for i in hits:
            recs.append({
                "source": "Crossref", "doi": i["DOI"].lower(), "title": (i.get("title") or [""])[0],
                "journal": (i.get("container-title") or [""])[0], "page": i.get("page", ""),
                "issued": i.get("issued", {}).get("date-parts", [[None]])[0], "type": i.get("type"),
                "affiliations": list({a.get("name") for au in i.get("author", []) for a in au.get("affiliation", []) if a.get("name")})[:40],
                "query_asset": asset,
            })
        pages += 1
        if not hits or not items or not msg.get("next-cursor"):
            break
        cursor = msg["next-cursor"]
        time.sleep(0.3)
    return recs


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    import sys
    force = "--force" in sys.argv
    for asset, terms in TERMS.items():
        if (OUT / f"{asset}.json").exists() and not force:  # resumable
            continue
        pm = pubmed(asset, terms)
        cr = []
        for t in terms:
            try:
                cr += crossref(asset, t)
            except Exception as e:  # keep going; the log shows which term failed
                print(f"  crossref failed for {t}: {e}", flush=True)
        (OUT / f"{asset}.json").write_text(json.dumps({"asset": asset, "terms": terms, "window": [START, END], "pubmed": pm, "crossref": cr}))
        print(f"{asset:8s} pubmed {len(pm):4d}  crossref {len(cr):4d}", flush=True)
