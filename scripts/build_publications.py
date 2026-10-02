"""Classify fetched publications and compute share of voice (SoV).

Input : data/raw/pubs/<asset>.json  (scripts/fetch_publications.py)
Output: data/raw/pubs/processed.json with
  publications  one row per unique publication (deduplicated by DOI / title)
  sov_congress  congress edition x brand counts and shares
  sov_journal   year x brand counts (peer-reviewed journals)
  sov_analysis  brand x analysis-type counts
Classification rules are keyword/pattern based (tagged 'derived' in the dataset) and should be spot-checked.
"""
import hashlib
import json
import pathlib
import re
from collections import Counter, defaultdict

RAW = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw" / "pubs"
sys_path = pathlib.Path(__file__).resolve().parent
import sys  # noqa: E402
sys.path.insert(0, str(sys_path))
from fetch_publications import TERMS, START, END  # noqa: E402

JNJ = {"TRE", "ICO", "JNJ4804", "STE"}
IBD_RE = re.compile(r"colitis|crohn|inflammatory bowel|\bibd\b|pouchitis|fistul|ileal|ileocolonic", re.I)
COMPANIES = {"Johnson & Johnson": r"janssen|johnson\s*&\s*johnson|johnson and johnson", "AbbVie": r"abbvie", "Eli Lilly": r"eli lilly|lilly (and|&) company",
             "Takeda": r"takeda", "Pfizer": r"pfizer", "BMS": r"bristol[- ]myers|celgene", "Abivax": r"abivax", "Merck": r"merck|\bmsd\b",
             "Roche": r"roche|genentech", "Sanofi": r"sanofi", "Teva": r"\bteva\b"}
TRIALS = r"JNJ-\d+|co-antibody|QUASAR|GALAXI|GRAVITI|ASTRO|FUZION|DUET|VEGA|ANTHEM|ICONIC|MACARONI|SEQUENCE|INSPIRE|COMMAND|ADVANCE|MOTIVATE|FORTIFY|AFFIRM|LUCENT|VIVID|SHINE|U-ACHIEVE|U-ACCOMPLISH|U-EXCEL|U-EXCEED|U-ENDURE|GEMINI|VISIBLE|VARSITY|ELEVATE|TRUE NORTH|YELLOWSTONE|ABTECT|ARTEMIS|APOLLO|ATLAS|RELIEVE|TUSCANY|UNIFI|UNITI|VIVID|SEAVUE|EXPEDITION|STARDUST|REVAMP|CHARGE|REASON"


CONGRESS_CONTAINERS = r"^posters?$|e-posters|poster presentations|oral presentations|libro de comunicaciones|congreso|clinical pharmacy services|^section \d|value in health|zeitschrift f.r gastroenterologie|abstracts?$|proceedings"
EXCLUDE_CONTAINERS = r"^$|isrctn|medicom conference report|clinicaltrials|reactions weekly|inpharma|pharmacoeconomics & outcomes news|pharmaceutical journal|journal of clinical oncology"


def clean_title(t):
    t = re.sub(r"<[^>]+>", "", t or "").strip()
    return re.sub(r"\s+", " ", t)


def norm(t):
    return re.sub(r"[^a-z0-9]", "", t.lower())[:120]


def venue_of(r):
    doi, j, page, title = r.get("doi", ""), (r.get("journal") or "").lower(), str(r.get("page") or ""), r["title"]
    year = r["year"]
    if r["source"] == "UEG Gutflix":
        return "UEGW", f"UEGW {year}", "congress"
    if r["source"] == "ACG programme":
        return "ACG", f"ACG {year}", "congress"
    if re.search(r"ecco-jcc/jj[a-z]{2}\d{3}\.\d+", doi):
        return "ECCO", f"ECCO {year}", "congress"
    if "gastroenterology" == j.strip() and (page.startswith("S-") or re.match(r"^(Sa|Su|Mo|Tu)\d+", title)):
        return "DDW", f"DDW {year}", "congress"
    # ACG abstracts in AJG supplements: "S1450 Title" (regular) or "130 Title" (numbered/late-breaking, some in a later issue)
    if "american journal of gastroenterology" in j and re.match(r"^S?\d+[\s\u2003]", title) and (page.upper().startswith("S") or re.match(r"^\d+\u2003", title)):
        return "ACG", f"ACG {year}", "congress"
    if "inflammatory bowel diseases" in j and re.search(r"ibd/iza[a-z]\d{3}\.\d+", doi):
        return "CCC", f"Crohn's & Colitis Congress {year}", "congress"
    if re.search(r"/[a-z]{3,6}\d{3}\.\d{3,4}$", doi):
        return "Other congress", f"Other congress {year}", "congress"
    if r["source"] == "Crossref" and (re.search(CONGRESS_CONTAINERS, j) or re.match(r"^[A-Z0-9]{1,6}-\d{1,4}\b|^\d?[A-Z]{2,5}-\d{2,4}\b|^P-\d+", title)):
        return "Other congress", f"Other congress {year}", "congress"
    return "Journal", r.get("journal") or "Journal", "journal"


def presentation_type(series, title, pub_types, source, r=None):
    if series == "UEGW":
        if r.get("uegw_format") == "presentation":
            return "Oral"
        return {"MP": "Moderated poster", "PP": "Poster", "CC": "Clinical case poster"}.get((r.get("uegw_code") or "")[:2], "Poster")
    if series == "ECCO":
        m = re.match(r"^(DOP|OP|P)\d+", title)
        return {"OP": "Oral", "DOP": "Digital oral", "P": "Poster"}.get(m.group(1) if m else "", "Abstract")
    if series == "DDW":
        if re.match(r"^(Sa|Su|Mo|Tu)\d+", title):
            return "Poster"
        if re.match(r"^\d{2,4}[a-z]?[\s:]", title):  # numbered orals; letter suffix = late-breaking
            return "Oral"
        return "Abstract"
    if series == "ACG":
        # ACG presents every accepted abstract as a poster unless the programme lists it as an oral paper.
        # The AJG number is no guide: plain-numbered items (e.g. 89, 112 in 2025) are not in the oral list.
        return r.get("acg_oral") or "Poster"
    if series in ("CCC", "Other congress"):
        return "Abstract"
    pt = " ".join(pub_types or [])
    if re.search(r"Network Meta|Meta-Analysis|Systematic Review", pt):
        return "Systematic review / meta-analysis"
    if "Case Reports" in pt:
        return "Case report"
    if re.search(r"Letter|Comment|Editorial", pt):
        return "Letter / editorial"
    if "Review" in pt:
        return "Review"
    if re.search(r"Randomized Controlled Trial|Clinical Trial", pt):
        return "Clinical trial report"
    if source == "Crossref":
        return "Article (not PubMed-indexed)"
    return "Original article"


def analysis_type(title, abstract, ptype):
    t = title.lower()
    a = (abstract or "").lower()
    if ptype == "Case report" or re.search(r"\bcase (report|series)\b|a case of|in a patient|a patient with|rare (adverse|case)|: a case", t):
        return "Case report"
    if ptype == "Letter / editorial":
        return "Commentary"
    if re.search(r"network meta|meta-analy|systematic (literature )?review|indirect (treatment )?comparison|matching-adjusted|\bmaic\b|bayesian", t):
        return "ITC / NMA / SLR"
    if (ptype == "Review" and not re.search(r"systematic|meta-analy", t)) or re.search(r"\breview\b|overview|update on|state of the art|place in therapy|drug profile|positioning of|current (and|&) (future|emerging)|second generation|new (drugs|therapies|treatment options)|emerging therap|: an update|in focus", t):
        return "Narrative review"
    if re.search(r"cost|economic|budget impact|pharmacoeconomic|healthcare resource|hcru|value[- ]based|price|projection|simulation model|markov|disease model", t):
        return "HEOR / economic"
    if re.search(r"design and rationale|study design|trial design|\brationale\b|protocol for|trial in progress", t):
        return "Trial in progress / design"
    if re.search(r"baseline (demographic|characteristic)", t):
        return "Baseline characteristics"
    if re.search(r"biosimilar|analytical|functional similarity|drug levels?|serum (levels?|concentrations?)|concentration|clearance|trough|drug monitoring|\btdm\b|pharmacokinetic|exposure[- ]response|\bpk\b|immunogenicity|antibod(y|ies) to|murine|mouse|mice|in vitro|mechanis|transcript|single[- ]cell|cytometry|plasma cells|biomarker|gene expression|microbio|organoid|collagen|signaling|immunoprofil", t):
        return "Mechanistic / biomarker / PK"
    if re.search(r"post[- ]hoc", t):
        return "Post-hoc analysis"
    if re.search(r"long[- ]term extension|\blte\b|week (9[0-9]|1[0-9]{2}|2[0-9]{2})|\b(2|3|4|5|two|three|four|five)[- ]year|through year", t) and not re.search(r"real[- ]world|retrospective|cohort", t):
        return "Long-term extension"
    if re.search(r"pooled|integrated (safety|analysis)", t):
        return "Pooled analysis"
    if re.search(r"\binterim\b", t) and not re.search(r"real[- ]world|retrospective|cohort|registry|observational|prospective|multicent(er|re)|non[- ]interventional|post[- ]marketing|surveillance", t) and (re.search(TRIALS, title) or re.search(r"phase (1|2|3|i|ii|iii|iib|iiib|2b|3b)\b|randomi[sz]ed|open[- ]label|single[- ]arm|trial", t)):
        return "Interim analysis"
    if re.search(TRIALS, title) or re.search(r"phase (1|2|3|i|ii|iii|iib|iiib|2b|3b)\b|randomi[sz]ed|placebo|participants|head-to-head", t):
        if re.search(r"subgroup|by prior|prior (advanced|biologic)|biologic[- ]na[iï]ve|inadequate response|\bby (baseline|age|sex|region)|east asian|japanese|chinese", t):
            return "Subgroup analysis"
        return "Trial analysis (primary / secondary)"
    if re.search(r"real[- ]world|retrospective|cohort|registry|claims|observational|experience|multicent(er|re)|trinetx|single[- ]cent(er|re)|nationwide|practice|effectiveness|comparative efficacy|switch|dose (escalation|intensification|optimi[sz]ation)|intensif|off[- ]label|predict|machine learning|persistence|drug survival|pregnan|elderly|older (adults|patients)|salvage|acute severe|outcomes (of|in|after|with|following)|in (children|pediatric|paediatric)|pediatric|paediatric|quality of life|patient[- ]reported|dose|combination|combining|dual (targeted|biologic|advanced)|sequential|after failure|refractory|postoperative|pouchitis|perianal|fistul", t):
        return "RWE"
    if re.search(r"subgroup|biologic[- ]na[iï]ve|inadequate response", t):
        return "Subgroup analysis"
    if re.search(r"moderately[- ]to[- ]severely active|efficacy and safety of", t):
        return "Trial analysis (primary / secondary)"
    if ptype == "Review":
        return "Narrative review"
    return "Other"


def companies(affs):
    text = " ".join(affs or [])
    return sorted(c for c, rx in COMPANIES.items() if re.search(rx, text, re.I))


def main():
    recs = {}
    for f in sorted(RAW.glob("*.json")):
        if f.name == "processed.json":
            continue
        d = json.loads(f.read_text())
        for r in d["pubmed"] + d["crossref"]:
            r["title"] = clean_title(r["title"])
            if r["source"] == "Crossref":
                iss = r.get("issued") or [None]
                r["year"] = str(iss[0]) if iss and iss[0] else ""
                r["month"] = str(iss[1]) if len(iss) > 1 else ""
            key = r.get("doi") or norm(r["title"])
            if not key:
                continue
            if key in recs:
                old = recs[key]
                if old["source"] == "Crossref" and r["source"] == "PubMed":  # prefer PubMed metadata, keep Crossref page
                    r["page"] = old.get("page", "")
                    r["affiliations"] = list(set(r.get("affiliations", []) + old.get("affiliations", [])))
                    recs[key] = r
                continue
            recs[key] = r
    # UEG Week abstracts collected via the browser from UEG's Gutflix library (data/raw/uegw)
    uegw = RAW.parent / "uegw" / "uegw_abstracts.tsv"
    if uegw.exists():
        for line in uegw.read_text().splitlines():
            parts = line.split("|")
            if len(parts) < 5 or parts[1] == "symposium":
                continue
            term, fmt, edition, code, title = parts[:5]
            key = "uegw:" + norm(title)
            if key in recs:
                continue
            recs[key] = {"source": "UEG Gutflix", "doi": "", "title": title, "journal": "UEG Week", "year": edition[-4:], "month": "10",
                         "uegw_format": fmt, "uegw_code": code, "uegw_edition": edition, "affiliations": []}

    # ACG oral papers, copied from the official ACG programme (acgYYYY.eventscribe.net, "Oral Abstracts")
    # into data/raw/programs/acg_orals.tsv. Matched to AJG abstracts by title; unmatched orals are added.
    prog = RAW.parent / "programs" / "acg_orals.tsv"
    if prog.exists():
        import difflib
        full = lambda t: re.sub(r"[^a-z0-9]", "", re.sub(r"\(late-breaking abstract\)", "", re.sub(r"^S?\d+[\s\u2003]+", "", t), flags=re.I).lower())
        acg = [(k, r["year"], full(r["title"])) for k, r in recs.items() if "american journal of gastroenterology" in (r.get("journal") or "").lower()]
        for line in prog.read_text().splitlines()[1:]:
            cong, year, code, title, lba, day, url = line.split("\t")
            label = "Late-breaking oral" if lba else "Oral"
            ft = full(title)
            # best single match on the whole title: UC and CD versions of one trial share long openings
            best = max(((difflib.SequenceMatcher(None, ft, t).ratio(), k) for k, y, t in acg if y == year), default=(0, None))
            if best[0] >= 0.9:
                recs[best[1]]["acg_oral"], recs[best[1]]["acg_code"] = label, code
            else:
                recs["acgprog:" + year + norm(title)] = {"source": "ACG programme", "doi": "", "title": re.sub(r"\s*\(Late-Breaking Abstract\)", "", title),
                    "journal": "ACG Annual Scientific Meeting", "year": year, "month": "10", "acg_oral": label, "acg_code": code, "url": url, "affiliations": []}

    # second dedupe pass on normalised title (PubMed without DOI vs Crossref)
    by_title = {}
    for k, r in list(recs.items()):
        nt = ("uegw:" if r["source"] == "UEG Gutflix" else "") + norm(r["title"])
        if nt in by_title and nt:
            keep = by_title[nt]
            if recs[keep]["source"] == "Crossref" and r["source"] == "PubMed":
                del recs[keep]; by_title[nt] = k
            else:
                del recs[k]
        else:
            by_title[nt] = k

    pubs = []
    for key, r in recs.items():
        title, abstract = r["title"], r.get("abstract", "")
        if r["source"] == "Crossref" and re.search(EXCLUDE_CONTAINERS, (r.get("journal") or "").strip().lower()):
            continue
        series, venue, kind = venue_of(r)
        in_title = sorted(a for a, terms in TERMS.items() if any(t.lower() in title.lower() for t in terms))
        in_abs = sorted(a for a, terms in TERMS.items() if any(t.lower() in abstract.lower() for t in terms)) if abstract else []
        if not in_title and not in_abs:
            continue
        ibd = bool(IBD_RE.search(title + " " + abstract)) or "crohn" in (r.get("journal") or "").lower() or "inflammatory bowel" in (r.get("journal") or "").lower()
        if not ibd:
            continue
        date = f'{r.get("year", "")}-{str(r.get("month") or "").zfill(2)}' if r.get("month") and str(r.get("month")).isdigit() else r.get("year", "")
        if not r.get("year") or not (START[:4] <= r["year"] <= END[:4]):
            continue
        ptype = presentation_type(series, title, r.get("pub_types"), r["source"], r)
        pubs.append({
            "pub_id": "PUB-" + hashlib.sha1((r.get("doi") or ({"UEG Gutflix": "uegw:", "ACG programme": "acgprog:"}.get(r["source"], "")) + norm(title)).encode()).hexdigest()[:10],
            "doi": r.get("doi", ""), "pmid": r.get("pmid", ""),
            "title": (title.capitalize() if r["source"] == "UEG Gutflix" else re.sub(r"^(DOP|OP|P|S|Sa|Su|Mo|Tu)?\d+[a-z]?[:\s]+", "", title)) if kind == "congress" else title,
            "abstract_code": r.get("uegw_code") or r.get("acg_code") or ((re.match(r"^((DOP|OP|P|S|Sa|Su|Mo|Tu)?\d+[a-z]?)(?=[:\s])", title) or [None])[0] if kind == "congress" else ""),
            "kind": kind, "series": series, "venue": venue, "journal": r.get("journal", ""), "year": r["year"], "date": date,
            "presentation_type": ptype, "analysis_type": analysis_type(title, abstract, ptype),
            "brands_title": in_title, "brands_any": sorted(set(in_title) | set(in_abs)),
            "focus": bool(in_title), "multi_brand": len(in_title) > 1,
            "industry_affiliation": companies(r.get("affiliations")), "affiliation_known": bool(r.get("affiliations")),
            "source": r["source"], "url": f'https://doi.org/{r["doi"]}' if r.get("doi") else (f'https://pubmed.ncbi.nlm.nih.gov/{r["pmid"]}/' if r.get("pmid") else
                   ("https://gutflix.eu/browse/poster/search?q=" + "+".join(title.split()[:8]) if r["source"] == "UEG Gutflix" else r.get("url", ""))),
        })

    # ---------------- share of voice (title-level attribution; a multi-brand item counts for each brand named)
    def counts(rows, keyf):
        c = defaultdict(Counter)
        for p in rows:
            for b in p["brands_title"]:
                c[keyf(p)][b] += 1
        return c

    cong = [p for p in pubs if p["kind"] == "congress"]
    jour = [p for p in pubs if p["kind"] == "journal" and p["presentation_type"] not in ("Letter / editorial",)]
    sov_congress = []
    for venue, c in counts(cong, lambda p: p["venue"]).items():
        tot = sum(c.values())
        orals = Counter(b for p in cong if p["venue"] == venue and p["presentation_type"] in ("Oral", "Digital oral") for b in p["brands_title"])
        for b, n in c.items():
            sov_congress.append({"venue": venue, "series": venue.rsplit(" ", 1)[0], "year": venue.rsplit(" ", 1)[1], "brand_id": b, "n": n,
                                 "n_orals": orals.get(b, 0), "share_pct": round(100 * n / tot, 1), "venue_total_mentions": tot})
    sov_journal = []
    for year, c in counts(jour, lambda p: p["year"]).items():
        tot = sum(c.values())
        for b, n in c.items():
            sov_journal.append({"year": year, "brand_id": b, "n": n, "share_pct": round(100 * n / tot, 1)})
    sov_analysis = []
    for b in TERMS:
        mine = [p for p in pubs if b in p["brands_title"]]
        for at, n in Counter(p["analysis_type"] for p in mine).items():
            sov_analysis.append({"brand_id": b, "analysis_type": at, "n": n, "share_pct": round(100 * n / len(mine), 1)})
    symposia = []
    sf = RAW.parent / "uegw" / "uegw_symposia.tsv"
    if sf.exists():
        for line in sf.read_text().splitlines():
            ed, company, title = line.split("|", 2)
            symposia.append({"venue": f"UEGW {ed[-4:]}", "company": company, "title": title})
    out = {"window": [START, END], "publications": pubs, "symposia": symposia, "sov_congress": sov_congress, "sov_journal": sov_journal, "sov_analysis": sov_analysis}
    (RAW / "processed.json").write_text(json.dumps(out, ensure_ascii=False))
    print(len(pubs), "publications;", Counter(p["kind"] for p in pubs), Counter(p["series"] for p in pubs))
    tot = Counter(b for p in pubs for b in p["brands_title"])
    print("title mentions by brand:", dict(tot.most_common()))


if __name__ == "__main__":
    main()
