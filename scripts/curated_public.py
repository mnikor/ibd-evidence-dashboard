"""Hand-curated public facts gathered by web research on 2026-09-19.

Every fact carries a source_id pointing into SOURCES. Provenance tiers:
  public_verified   - checked in this session against the cited web source or registry
  public_unverified - public knowledge from before this session, NOT re-checked; verify before use
Replace or extend these lists as real data becomes available; build_dataset.py reads them as-is.
"""

RETRIEVED = "2026-09-19"

SOURCES = [
    # id, type, title, publisher, publish_date, url, reliability
    ("SRC-FDA-API", "regulator database", "Drugs@FDA via the openFDA API: application sponsor, generic name and approval dates of original and efficacy supplements", "U.S. FDA", "2026-09-30", "https://api.fda.gov/drug/drugsfda.json", "A"),
    ("SRC-VEGA-LGH", "journal", "Feagan BG et al. Guselkumab plus golimumab combination vs monotherapy in UC (VEGA). Lancet Gastroenterol Hepatol 2023 (PMID 36738762)", "Lancet Gastroenterol Hepatol", "2023-04", "https://pubmed.ncbi.nlm.nih.gov/36738762/", "A"),
    ("SRC-ACG-CD-2025", "guideline", "Lichtenstein GR et al. ACG Clinical Guideline: Management of Crohn's Disease in Adults. Am J Gastroenterol 2025 (PMID 40701562)", "Am J Gastroenterol", "2025-06", "https://pubmed.ncbi.nlm.nih.gov/40701562/", "A"),
    ("SRC-NICE-TA1094", "HTA", "NICE TA1094: Guselkumab for treating moderately to severely active ulcerative colitis (28 Aug 2025)", "NICE", "2025-08-28", "https://www.nice.org.uk/guidance/ta1094", "A"),
    ("SRC-NICE-TA1095", "HTA", "NICE TA1095: Guselkumab for previously treated moderately to severely active Crohn's disease (28 Aug 2025)", "NICE", "2025-08-28", "https://www.nice.org.uk/guidance/ta1095", "A"),
    ("SRC-GBA-UC", "HTA", "G-BA benefit assessment: guselkumab, ulcerative colitis (decision 20 Nov 2025)", "G-BA", "2025-11-20", "https://www.g-ba.de/bewertungsverfahren/nutzenbewertung/1230/", "A"),
    ("SRC-GBA-CD", "HTA", "G-BA benefit assessment: guselkumab, Crohn's disease (decision 20 Nov 2025)", "G-BA", "2025-11-20", "https://www.g-ba.de/bewertungsverfahren/nutzenbewertung/1231/", "A"),
    ("SRC-AMT-GBA", "news", "G-BA-Beschluss: Guselkumab (summary of both decisions)", "Arzneimitteltherapie", "2026", "https://www.arzneimitteltherapie.de/online-only/2026/g-ba-beschluss-guselkumab.html", "B"),
    ("SRC-HAS-UC", "HTA", "HAS Transparency Committee: TREMFYA (guselkumab), ulcerative colitis", "HAS", "2025-07-16", "https://www.has-sante.fr/jcms/p_4126732/fr/tremfya-guselkumab-rectocolite-hemorragique-rch", "A"),
    ("SRC-VIDAL-TRE", "news", "TREMFYA: prise en charge étendue dans les MICI (HAS opinions for UC and Crohn's disease)", "VIDAL", "2026-09", "https://www.vidal.fr/actualites/38304-tremfya-prise-en-charge-etendue-dans-les-mici.html", "B"),
    ("SRC-CDA-UC", "HTA", "CDA-AMC reimbursement recommendation: guselkumab (Tremfya), ulcerative colitis (PMID 41468487)", "Canada's Drug Agency", "2025-11", "https://www.cda-amc.ca/sites/default/files/DRR/2025/SR0874_Tremfya_UC.pdf", "A"),
    ("SRC-CDA-CD", "HTA", "CDA-AMC reimbursement recommendation: guselkumab (Tremfya), Crohn's disease (PMID 41401272)", "Canada's Drug Agency", "2025-09", "https://pubmed.ncbi.nlm.nih.gov/41401272/", "A"),
    ("SRC-ECCO-UC-2026", "guideline", "Gisbert JP et al. ECCO Guidelines on Therapeutics in Ulcerative Colitis: Medical Treatment. J Crohns Colitis 2026 (PMID 42413123)", "J Crohns Colitis", "2026-07-07", "https://pubmed.ncbi.nlm.nih.gov/42413123/", "A"),
    ("SRC-ECCO-CD-2024", "guideline", "Gordon H et al. ECCO Guidelines on Therapeutics in Crohn's Disease: Medical Treatment. J Crohns Colitis 2024 (PMID 38877997)", "J Crohns Colitis", "2024-10-15", "https://pubmed.ncbi.nlm.nih.gov/38877997/", "A"),
    ("SRC-AGA-UC-2024", "guideline", "AGA Living Clinical Practice Guideline on Pharmacological Management of Moderate-to-Severe Ulcerative Colitis. Gastroenterology 2024 (PMID 39572132)", "Gastroenterology", "2024-12", "https://pubmed.ncbi.nlm.nih.gov/39572132/", "A"),
    ("SRC-BSG-2025", "guideline", "Moran GW et al. British Society of Gastroenterology guidelines on inflammatory bowel disease in adults: 2025. Gut 2025 (PMID 40550582)", "Gut", "2025-06-23", "https://pubmed.ncbi.nlm.nih.gov/40550582/", "A"),
    ("SRC-CTGOV", "registry", "ClinicalTrials.gov API v2 extract (see data/raw/ctgov)", "NLM", RETRIEVED, "https://clinicaltrials.gov/api/v2/studies", "A"),
    ("SRC-001", "press release", "TREMFYA receives U.S. FDA approval for adults with moderately to severely active UC", "Johnson & Johnson", "2024-09", "https://www.jnj.com/media-center/press-releases/tremfya-guselkumab-receives-u-s-fda-approval-for-adults-with-moderately-to-severely-active-ulcerative-colitis-strengthening-johnson-johnsons-leadership-in-inflammatory-bowel-disease", "A"),
    ("SRC-002", "press release", "U.S. FDA approves TREMFYA for adults with moderately to severely active Crohn's disease (SC and IV induction)", "Johnson & Johnson", "2025-03", "https://www.jnj.com/media-center/press-releases/u-s-fda-approves-tremfya-guselkumab-the-first-and-only-il-23-inhibitor-offering-both-subcutaneous-and-intravenous-induction-options-for-adult-patients-with-moderately-to-severely-active-crohns-disease", "A"),
    ("SRC-003", "news", "FDA approves Tremfya for subcutaneous induction in adults with UC", "Healio", "2025-09-22", "https://www.healio.com/news/gastroenterology/20250922/fda-approves-tremfya-for-subcutaneous-induction-in-adults-with-ulcerative-colitis", "B"),
    ("SRC-004", "press release", "TREMFYA receives European Commission approval for adults with moderately to severely active UC", "Johnson & Johnson", "2025-04-25", "https://www.globenewswire.com/news-release/2025/04/25/3068097/0/en/TREMFYA-guselkumab-receives-European-Commission-approval-for-adults-with-moderately-to-severely-active-ulcerative-colitis-strengthening-Johnson-Johnson-s-leadership-in-inflammatory.html", "A"),
    ("SRC-005", "press release", "European Commission approves TREMFYA for Crohn's disease (SC and IV induction)", "Johnson & Johnson", "2025-05", "https://www.biospace.com/press-releases/european-commission-approves-tremfya-guselkumab-the-first-dual-acting-il-23-inhibitor-offering-both-subcutaneous-and-intravenous-induction-options-for-adult-patients-with-moderately-to-severely-active-crohns-disease", "A"),
    ("SRC-006", "press release", "TREMFYA receives EC approval for SC induction through maintenance in UC", "Johnson & Johnson", "2025-10-24", "https://www.globenewswire.com/news-release/2025/10/24/3172775/0/en/TREMFYA-guselkumab-receives-European-Commission-approval-for-subcutaneous-induction-through-to-maintenance-in-adults-with-ulcerative-colitis-now-the-first-IL-23-inhibitor-with-a-fu.html", "A"),
    ("SRC-007", "HTA", "NICE recommends guselkumab for ulcerative colitis and Crohn's disease", "Pharmaceutical Journal", "2025", "https://pharmaceutical-journal.com/article/news/nice-recommends-guselkumab-for-ulcerative-colitis-and-crohns-disease", "B"),
    ("SRC-008", "press release", "Icotrokinra meets primary endpoint of clinical response in UC study (ANTHEM-UC)", "Johnson & Johnson", "2025", "https://www.jnj.com/media-center/press-releases/icotrokinra-meets-primary-endpoint-of-clinical-response-in-ulcerative-colitis-study-and-shows-potential-to-transform-the-treatment-paradigm-for-patients", "A"),
    ("SRC-009", "press release", "Icotrokinra maintains therapeutic benefit and favorable safety through 28 weeks in UC", "Johnson & Johnson", "2025", "https://www.jnj.com/media-center/press-releases/icotrokinra-maintains-standout-combination-of-therapeutic-benefit-and-a-favorable-safety-profile-in-once-daily-pill-through-28-weeks-in-ulcerative-colitis", "A"),
    ("SRC-010", "press release", "FDA approval of ICOTYDE (icotrokinra) for plaque psoriasis", "Johnson & Johnson", "2026-03-18", "https://www.jnj.com/media-center/press-releases/fda-approval-of-icotyde-icotrokinra-ushers-in-new-era-for-first-line-systemic-treatment-of-plaque-psoriasis-with-a-targeted-oral-peptide", "A"),
    ("SRC-011", "news", "Guselkumab exhibits 'good efficacy' in perianal fistulizing Crohn's disease (FUZION, DDW 2026)", "Healio", "2026-05-14", "https://www.healio.com/news/gastroenterology/20260514/guselkumab-exhibits-good-efficacy-in-perianal-fistulizing-crohns-disease", "B"),
    ("SRC-012", "press release", "JNJ-4804 co-antibody therapy shows potential to raise the bar in refractory IBD (DUET-UC/CD)", "Johnson & Johnson", "2026-05-05", "https://www.jnj.com/media-center/press-releases/johnson-johnson-investigational-co-antibody-therapy-jnj-4804-shows-potential-to-raise-the-bar-for-clinical-efficacy-in-treating-refractory-inflammatory-bowel-disease", "A"),
    ("SRC-013", "news", "JNJ-4804 Phase 2b data show higher week-48 remission in refractory UC, CD", "HCPLive", "2026-05", "https://www.hcplive.com/view/jnj-4804-phase-2b-data-show-higher-week-48-remission-in-refractory-uc-crohn-disease", "B"),
    ("SRC-014", "journal", "GRAVITI: guselkumab SC induction and maintenance in Crohn's disease", "Gastroenterology", "2025", "https://www.gastrojournal.org/article/S0016-5085(25)00522-0/fulltext", "A"),
    ("SRC-015", "journal", "ASTRO: SC guselkumab induction in UC (Lancet Gastroenterol Hepatol)", "The Lancet Gastroenterology & Hepatology", "2025", "https://www.thelancet.com/journals/langas/article/PIIS2468-1253(25)00322-X/abstract", "A"),
    ("SRC-016", "news", "Guselkumab bests placebo in clinical remission for UC (ASTRO week 12)", "HCPLive", "2025", "https://www.hcplive.com/view/guselkumab-placebo-clinical-remission-ulcerative-colitis", "B"),
    ("SRC-017", "journal", "GALAXI-2 and GALAXI-3 48-week results (Lancet)", "The Lancet", "2025", "https://pubmed.ncbi.nlm.nih.gov/40684778/", "A"),
    ("SRC-018", "news", "GALAXI 2 & 3: guselkumab superior to ustekinumab for Crohn's disease", "HCPLive", "2024", "https://www.hcplive.com/view/galaxi-guselkumab-superior-ustekinumab-crohns-disease", "B"),
    ("SRC-019", "journal", "QUASAR phase 3 induction and maintenance (Lancet)", "The Lancet", "2025", "https://pubmed.ncbi.nlm.nih.gov/39706209/", "A"),
    ("SRC-020", "journal", "QUASAR phase 2b induction study (Gastroenterology)", "Gastroenterology", "2023", "https://pubmed.ncbi.nlm.nih.gov/37659673/", "A"),
    ("SRC-021", "press release", "Tulisokibart met primary and key secondary endpoints in Phase 3 ATLAS-UC induction-only study", "Merck", "2026-06-22", "https://www.merck.com/news/mercks-tulisokibart-met-primary-and-key-secondary-endpoints-in-the-phase-3-atlas-uc-induction-only-study-in-patients-with-moderately-to-severely-active-ulcerative-colitis-uc/", "A"),
    ("SRC-022", "press release", "Abivax announces Phase 3 ABTECT maintenance trial results (obefazimod)", "Abivax", "2026-06-01", "https://www.globenewswire.com/news-release/2026/06/01/3304711/0/en/abivax-announces-landmark-phase-3-abtect-maintenance-trial-results-evaluating-obefazimod-in-moderately-to-severely-active-ulcerative-colitis.html", "A"),
    ("SRC-023", "press release", "Abivax ABTECT Maintenance Part 2 results; NDA on track for Q4 2026", "Abivax", "2026", "https://ir.abivax.com/news-releases/news-release-details/abivax-reports-positive-abtect-maintenance-part-2-results/", "A"),
    ("SRC-024", "press release", "AbbVie submits FDA application for SKYRIZI SC induction in Crohn's disease (AFFIRM)", "AbbVie", "2026-04-27", "https://news.abbvie.com/2026-04-27-AbbVie-Submits-Regulatory-Application-to-FDA-for-SKYRIZI-R-risankizumab-rzaa-Subcutaneous-Induction-for-Adults-with-Moderately-to-Severely-Active-Crohns-Disease", "A"),
    ("SRC-025", "press release", "AbbVie submits EMA application for SKYRIZI SC induction in Crohn's disease", "AbbVie", "2026-09", "https://www.prnewswire.com/news-releases/abbvie-submits-regulatory-application-to-ema-for-skyrizi-risankizumab-subcutaneous-induction-for-adults-with-moderately-to-severely-active-crohns-disease-302861059.html", "A"),
    ("SRC-026", "journal", "Risankizumab versus ustekinumab for moderate-to-severe Crohn's disease (SEQUENCE, NEJM)", "NEJM", "2024", "https://www.nejm.org/doi/abs/10.1056/NEJMoa2314585", "A"),
    ("SRC-027", "news", "AbbVie hits record Skyrizi sales, holds its own in IBD despite J&J competition", "Fierce Pharma", "2026", "https://www.fiercepharma.com/pharma/abbvie-hitting-record-sales-high-skyrizi-gains-holds-its-own-growing-ibd-arena-despite-jj", "B"),
    ("SRC-028", "press release", "FDA approves Omvoh (mirikizumab) for Crohn's disease", "Eli Lilly", "2025-01-15", "https://investor.lilly.com/news-releases/news-release-details/fda-approves-lillys-omvohr-mirikizumab-mrkz-crohns-disease", "A"),
    ("SRC-029", "press release", "U.S. FDA approves SKYRIZI for ulcerative colitis", "AbbVie", "2024-06-18", "https://news.abbvie.com/2024-06-18-U-S-FDA-Approves-SKYRIZI-R-risankizumab-rzaa-for-Ulcerative-Colitis,-Expanding-AbbVies-Portfolio-Across-Inflammatory-Bowel-Disease", "A"),
    ("SRC-030", "news", "J&J Q2 2026 earnings: Tremfya growth, Stelara decline", "Yahoo Finance / Zacks", "2026-07", "https://finance.yahoo.com/healthcare/articles/j-j-q2-earnings-beat-145000775.html", "B"),
    ("SRC-031", "earnings call", "J&J Q2 2026 earnings call transcript (IL-23 UC induction share, CD NBRx)", "Investing.com", "2026-07", "https://www.investing.com/news/transcripts/earnings-call-transcript-johnson--johnson-tops-q2-2026-estimates-and-lifts-outlook-93CH-4793625", "B"),
    ("SRC-032", "news", "Teva and Sanofi's TL1A mAb shows durability in UC and CD; Phase 3 timelines", "Clinical Trials Arena", "2026", "https://www.clinicaltrialsarena.com/news/teva-and-sanofis-tl1a-mab-shows-durability-in-uc-and-cd/", "B"),
    ("SRC-033", "congress", "UEG Week 2026, Barcelona, 17-20 October 2026", "UEG", "2026", "https://ueg.eu/week", "A"),
    ("SRC-034", "congress", "ACG 2026 Annual Scientific Meeting, Nashville, 9-14 October 2026", "ACG", "2026", "https://acgmeetings.gi.org/", "A"),
    ("SRC-035", "congress", "ECCO'27, Copenhagen, 3-6 March 2027", "ECCO", "2026", "https://ecco-ibd.eu/ecco27/our-congress/overview", "A"),
    ("SRC-036", "congress", "DDW 2027, Washington DC, 15-18 May 2027", "DDW", "2026", "https://news.ddw.org/news/save-the-date-for-ddw-2027/", "A"),
    ("SRC-037", "guideline", "ACG Clinical Guideline Update: Ulcerative Colitis in Adults (2025)", "Am J Gastroenterol", "2025-06", "https://pubmed.ncbi.nlm.nih.gov/40701556/", "A"),
    ("SRC-038", "guideline", "AGA Living Clinical Practice Guideline: pharmacologic management of moderate-to-severe Crohn's disease", "Gastroenterology", "2025-11-20", "https://www.gastrojournal.org/article/S0016-5085(25)06091-3/fulltext", "A"),
    ("SRC-039", "guideline", "Updated 2025 ACG clinical guideline for the management of Crohn's disease (summary)", "ACG", "2025", "https://gi.org/journals-publications/ebgi/zhai_dalal_sep2025/", "B"),
    ("SRC-040", "congress abstract", "ASTRO week 48 results by week-12 response status (ECCO 2026, DOP105)", "J Crohns Colitis suppl.", "2026", "https://academic.oup.com/ecco-jcc/article/20/Supplement_1/jjaf231.142/8432650", "A"),
    ("SRC-041", "congress abstract", "ASTRO week 12 results (ECCO 2025, OP10)", "J Crohns Colitis suppl.", "2025", "https://academic.oup.com/ecco-jcc/article/19/Supplement_1/i19/7966978", "A"),
    ("SRC-042", "news", "AbbVie outlines Skyrizi defense against new J&J psoriasis rival Icotyde", "Fierce Pharma", "2026", "https://www.fiercepharma.com/pharma/abbvie-outlines-immunology-superstar-skyrizis-defense-against-new-jj-competition-icotyde", "B"),
    ("SRC-043", "news", "J&J pushes dual-antibody IBD therapy into Phase 3 despite mid-stage misses", "BioSpace", "2026", "https://www.biospace.com/drug-development/j-j-pushes-dual-antibody-ibd-therapy-into-phase-3-despite-mid-stage-fails", "B"),
    ("SRC-044", "news", "ANTHEM-UC: icotrokinra shows promise for UC (week 12 rates)", "HCPLive", "2025", "https://www.hcplive.com/view/anthem-uc-icotrokinra-jnj-2113-shows-promise-ulcerative-colitis", "B"),
    ("SRC-045", "news", "FDA approves upadacitinib for Crohn's disease", "ACCP", "2023-05", "https://www.accp.com/stunet/newsletter.aspx?art=176", "B"),
    ("SRC-PUBMED", "database", "PubMed E-utilities search: drug terms AND IBD terms, publication date 2023-09-19..2026-09-19", "NLM", RETRIEVED, "https://pubmed.ncbi.nlm.nih.gov/", "A"),
    ("SRC-CROSSREF", "database", "Crossref REST API: congress abstract supplements (ECCO/JCC, DDW/Gastroenterology, ACG/AJG, CCC/IBD) 2023-09-19..2026-09-19", "Crossref", RETRIEVED, "https://api.crossref.org/", "A"),
    ("SRC-ACGPROG", "congress programme", "ACG Annual Scientific Meeting 2023-2025: official oral abstract listings (eventscribe 'Oral Abstracts'); IBD orals copied to data/raw/programs/acg_orals.tsv", "American College of Gastroenterology", "2026-09-22", "https://acg2025.eventscribe.net/SearchByBucket.asp?f=CustomPresfield32&pfp=BrowsebyOrals", "A"),
    ("SRC-LBL-TRE", "label", "TREMFYA (guselkumab) US Prescribing Information, revised 05/2026 (text kept in data/raw/labels)", "Janssen Biotech / FDA", "2026-05", "https://www.jnjlabels.com/package-insert/product-monograph/prescribing-information/TREMFYA-pi.pdf", "A"),
    ("SRC-LBL-SKY", "label", "SKYRIZI (risankizumab-rzaa) US Prescribing Information, revised 6/2026 (text kept in data/raw/labels)", "AbbVie / FDA", "2026-06", "https://www.rxabbvie.com/pdf/skyrizi_pi.pdf", "A"),
    ("SRC-AFFIRM-TL", "press release", "AbbVie announces positive topline results from Phase 3 AFFIRM (SKYRIZI SC induction in CD)", "AbbVie", "2026-03-02", "https://news.abbvie.com/2026-03-02-AbbVie-Announces-Positive-Topline-Results-from-Phase-3-AFFIRM-Study-Evaluating-SKYRIZI-R-Risankizumab-Subcutaneous-Induction-in-Patients-with-Crohns-Disease", "A"),
    ("SRC-UEG", "congress library", "UEG Week 2023-2025 posters and presentations (UEG Gutflix library, collected via browser; titles only)", "UEG", RETRIEVED, "https://gutflix.eu/browse/poster", "A"),
    ("SRC-MANUAL", "manual edit", "Value corrected/updated by the team in the Data Editor (see row note and data/overrides/overrides.json)", "Team", RETRIEVED, "", "B"),
    ("SRC-SIM", "simulated", "Simulated by prototype generator (scripts/build_dataset.py, seed 42)", "Prototype", RETRIEVED, "", "D"),
    ("SRC-AI", "simulated", "AI-inferred hypothesis generated for the prototype; not a fact", "Prototype", RETRIEVED, "", "D"),
]

# ---------------------------------------------------------------- brands / assets
# asset_id, brand, inn, company, is_jnj, moa_id, modality, routes, lifecycle, source_ids, origin
ASSETS = [
    ("TRE", "TREMFYA", "guselkumab", "Johnson & Johnson", True, "IL23P19", "mAb", "IV induction; SC induction; SC maintenance", "launch/growth (IBD)", ["SRC-002", "SRC-003"], "public_verified"),
    ("ICO", "Icotrokinra", "icotrokinra", "Johnson & Johnson", True, "IL23R_ORAL", "oral peptide", "oral once daily", "Ph3 (UC), Ph2b/3 (CD); approved psoriasis", ["SRC-010", "SRC-009"], "public_verified"),
    ("JNJ4804", "JNJ-4804", "guselkumab + golimumab", "Johnson & Johnson", True, "COMBO_IL23_TNF", "mAb co-formulation", "SC", "Ph3 (DUET ENCORE)", ["SRC-012"], "public_verified"),
    ("STE", "STELARA", "ustekinumab", "Johnson & Johnson", True, "IL12_23P40", "mAb", "IV induction; SC maintenance", "LOE / biosimilar erosion", ["SRC-030"], "public_verified"),
    ("SKY", "SKYRIZI", "risankizumab", "AbbVie", False, "IL23P19", "mAb", "IV induction (SC induction filed in CD); SC maintenance (on-body injector)", "growth", ["SRC-029", "SRC-024"], "public_verified"),
    ("OMV", "OMVOH", "mirikizumab", "Eli Lilly", False, "IL23P19", "mAb", "IV induction; SC maintenance", "growth", ["SRC-028"], "public_verified"),
    ("RIN", "RINVOQ", "upadacitinib", "AbbVie", False, "JAK1", "small molecule", "oral", "growth", ["SRC-045", "SRC-FDA-API"], "public_verified"),
    ("ENT", "ENTYVIO", "vedolizumab", "Takeda", False, "A4B7", "mAb", "IV; SC maintenance", "mature", ["SRC-FDA-API"], "public_verified"),
    ("VEL", "VELSIPITY", "etrasimod", "Pfizer", False, "S1P", "small molecule", "oral", "launch", ["SRC-FDA-API"], "public_verified"),
    ("ZEP", "ZEPOSIA", "ozanimod", "Bristol Myers Squibb", False, "S1P", "small molecule", "oral", "mature (UC); CD program terminated per registry", ["SRC-CTGOV", "SRC-FDA-API"], "public_verified"),
    ("OBE", "obefazimod", "obefazimod", "Abivax", False, "MIR124", "small molecule", "oral", "pre-filing (NDA planned Q4 2026)", ["SRC-023"], "public_verified"),
    ("TUL", "tulisokibart", "tulisokibart (MK-7240)", "Merck & Co.", False, "TL1A", "mAb", "IV / SC", "Ph3 (ATLAS-UC Study 2 positive Jun 2026; ARES-CD ongoing)", ["SRC-021"], "public_verified"),
    ("DUV", "duvakitug", "duvakitug", "Sanofi / Teva", False, "TL1A", "mAb", "SC", "Ph3 (SUNSCAPE UC, STARSCAPE CD)", ["SRC-032", "SRC-CTGOV"], "public_verified"),
    ("AFI", "afimkibart", "afimkibart (RO7790121)", "Roche", False, "TL1A", "mAb", "IV / SC", "Ph3 (AMETRINE)", ["SRC-CTGOV"], "public_verified"),
    ("MOR", "MORF-057", "MORF-057", "Eli Lilly", False, "A4B7_ORAL", "small molecule", "oral", "Ph2b/3 (EMERALD-3, GARNET)", ["SRC-CTGOV"], "public_verified"),
]

MOAS = [
    ("IL23P19", "IL-23 p19 inhibitor", "IL-23/Th17", "public_unverified"),
    ("IL23R_ORAL", "Oral IL-23 receptor antagonist peptide", "IL-23/Th17", "public_verified"),
    ("COMBO_IL23_TNF", "IL-23 + TNF antibody combination", "IL-23 + TNF", "public_verified"),
    ("IL12_23P40", "IL-12/23 p40 inhibitor", "IL-12/IL-23", "public_unverified"),
    ("JAK1", "JAK1-selective inhibitor", "JAK-STAT", "public_unverified"),
    ("A4B7", "Anti-α4β7 integrin", "Gut-selective lymphocyte trafficking", "public_unverified"),
    ("A4B7_ORAL", "Oral α4β7 integrin inhibitor", "Gut-selective lymphocyte trafficking", "public_unverified"),
    ("S1P", "S1P receptor modulator", "Lymphocyte egress", "public_unverified"),
    ("MIR124", "miR-124 enhancer", "Anti-inflammatory miRNA", "public_unverified"),
    ("TL1A", "Anti-TL1A", "TL1A/DR3 (inflammation + fibrosis)", "public_unverified"),
]

# ---------------------------------------------------------------- regulatory events
# asset, agency, indication, event_type, date, description, source, origin
REGULATORY = [
    ("TRE", "FDA", "UC", "approval", "2024-09-11", "IV induction + SC maintenance, adults with mod-sev UC", "SRC-001;SRC-FDA-API", "public_verified"),
    ("TRE", "FDA", "CD", "approval", "2025-03", "SC and IV induction options, adults with mod-sev CD", "SRC-002", "public_verified"),
    ("TRE", "EC", "UC", "approval", "2025-04-25", "Adults with mod-sev UC", "SRC-004", "public_verified"),
    ("TRE", "EC", "CD", "approval", "2025-05", "SC and IV induction options, adults with mod-sev CD", "SRC-005", "public_verified"),
    ("TRE", "FDA", "UC", "label update", "2025-09-19", "SC induction in UC (ASTRO); first fully SC IL-23 regimen", "SRC-003", "public_verified"),
    ("TRE", "EC", "UC", "label update", "2025-10-24", "SC induction through maintenance in UC", "SRC-006", "public_verified"),
    ("ICO", "FDA", "Psoriasis", "approval", "2026-03-18", "ICOTYDE approved for mod-sev plaque psoriasis (adults, adolescents >=12y, >=40kg)", "SRC-010", "public_verified"),
    ("SKY", "FDA", "UC", "approval", "2024-06-18", "UC approval (INSPIRE/COMMAND)", "SRC-029", "public_verified"),
    ("SKY", "FDA", "CD", "approval", "2022-06-16", "CD approval (IV induction)", "SRC-FDA-API", "public_verified"),
    ("SKY", "FDA", "CD", "submission", "2026-04-27", "sBLA for SC induction in CD (AFFIRM)", "SRC-024", "public_verified"),
    ("SKY", "EMA", "CD", "submission", "2026-09", "Type II variation for SC induction in CD", "SRC-025", "public_verified"),
    ("OMV", "FDA", "UC", "approval", "2023-10-26", "UC approval (LUCENT)", "SRC-FDA-API", "public_verified"),
    ("OMV", "FDA", "CD", "approval", "2025-01-15", "CD approval (VIVID-1)", "SRC-028", "public_verified"),
    ("RIN", "FDA", "CD", "approval", "2023-05-18", "CD approval, TNF-IR adults", "SRC-045", "public_verified"),
    ("RIN", "FDA", "UC", "approval", "2022-03-16", "UC approval, TNF-IR adults", "SRC-FDA-API", "public_verified"),
    ("VEL", "FDA", "UC", "approval", "2023-10-12", "Etrasimod UC approval", "SRC-FDA-API", "public_verified"),
    ("ZEP", "FDA", "UC", "approval", "2021-05-27", "Ozanimod UC approval", "SRC-FDA-API", "public_verified"),
    ("OBE", "FDA", "UC", "submission (planned)", "2026-Q4", "NDA submission planned Q4 2026", "SRC-023", "public_verified"),
]

# ---------------------------------------------------------------- competitive / corporate events
# id, asset, type, date, certainty, description, source, origin
EVENTS = [
    ("EV-001", "TUL", "topline readout", "2026-06-22", "confirmed", "ATLAS-UC Study 2 (Ph3, induction-only) met primary endpoint (clinical remission wk12) and key secondaries; first anti-TL1A Ph3 success. ATLAS-UC Study 1 ongoing", "SRC-021", "public_verified"),
    ("EV-002", "OBE", "topline readout", "2026-06-01", "confirmed", "ABTECT maintenance (Ph3) positive; no new safety signals", "SRC-022", "public_verified"),
    ("EV-003", "OBE", "filing", "2026-Q4", "guided", "NDA submission to FDA planned Q4 2026", "SRC-023", "public_verified"),
    ("EV-004", "OBE", "topline readout", "2027-mid", "guided", "ENHANCE-CD Ph2b induction topline expected mid-2027", "SRC-023", "public_verified"),
    ("EV-005", "SKY", "filing", "2026-04-27", "confirmed", "FDA sBLA: SC induction in CD (AFFIRM)", "SRC-024", "public_verified"),
    ("EV-006", "SKY", "filing", "2026-09", "confirmed", "EMA filing: SC induction in CD", "SRC-025", "public_verified"),
    ("EV-007", "OMV", "approval", "2025-01-15", "confirmed", "Omvoh FDA approval in CD", "SRC-028", "public_verified"),
    ("EV-008", "ICO", "approval", "2026-03-18", "confirmed", "ICOTYDE FDA approval in psoriasis (cross-indication halo for IBD)", "SRC-010", "public_verified"),
    ("EV-009", "JNJ4804", "congress presentation", "2026-05", "confirmed", "DUET-UC/CD Ph2b week-48 data at DDW 2026; Ph3 DUET ENCORE started", "SRC-012", "public_verified"),
    ("EV-010", "TRE", "congress presentation", "2026-05", "confirmed", "FUZION CD Ph3 perianal fistula data at DDW 2026", "SRC-011", "public_verified"),
    ("EV-011", "TRE", "trial start", "2026-04-21", "confirmed", "CHARGE Ph3b H2H guselkumab vs risankizumab in CD started", "SRC-CTGOV", "public_verified"),
    ("EV-012", "STE", "market", "2026-07", "confirmed", "Stelara Q2 2026 sales $740M (-55.7%) on biosimilar erosion", "SRC-030", "public_verified"),
]

# ---------------------------------------------------------------- study results (public)
# study_ref(NCT), endpoint, timepoint_wk, arm, comparator_arm, rate, comp_rate, population, is_primary, source, origin
RESULTS = [
    ("NCT04033445", "Clinical response (Ph2b induction)", 12, "GUS 200 mg IV", "Placebo", 61.4, 27.6, "ITT (Ph2b)", True, "SRC-020", "public_verified"),
    ("NCT04033445", "Clinical response (Ph2b induction)", 12, "GUS 400 mg IV", "Placebo", 60.7, 27.6, "ITT (Ph2b)", True, "SRC-020", "public_verified"),
    ("NCT04033445", "Clinical remission (Ph3 induction)", 12, "GUS 200 mg IV", "Placebo", 22.6, 7.9, "ITT (Ph3 induction)", True, "SRC-019", "public_verified"),
    ("NCT04033445", "Clinical remission (maintenance)", 44, "GUS 100 mg SC q8w", "Placebo", 45.2, 18.9, "Induction responders", True, "SRC-019", "public_verified"),
    ("NCT04033445", "Clinical remission (maintenance)", 44, "GUS 200 mg SC q4w", "Placebo", 50.0, 18.9, "Induction responders", True, "SRC-019", "public_verified"),
    ("NCT03466411", "Clinical remission + endoscopic response (composite)", 48, "GUS 200 mg SC q4w", "Ustekinumab", 47.3, 33.7, "GALAXI 2+3 pooled", False, "SRC-018", "public_verified"),
    ("NCT03466411", "Clinical remission + endoscopic response (composite)", 48, "GUS 100 mg SC q8w", "Ustekinumab", 41.6, 33.7, "GALAXI 2+3 pooled", False, "SRC-018", "public_verified"),
    ("NCT03466411", "Endoscopic remission", 48, "GUS 200 mg SC q4w", "Ustekinumab", 37.2, 24.7, "GALAXI 2+3 pooled", False, "SRC-018", "public_verified"),
    ("NCT03466411", "Endoscopic remission", 48, "GUS 100 mg SC q8w", "Ustekinumab", 33.2, 24.7, "GALAXI 2+3 pooled", False, "SRC-018", "public_verified"),
    ("NCT05197049", "Clinical remission", 12, "GUS 400 mg SC induction", "Placebo", 56.1, 21.4, "ITT", True, "SRC-014", "public_verified"),
    ("NCT05197049", "Endoscopic response", 12, "GUS 400 mg SC induction", "Placebo", 41.3, 21.4, "ITT", True, "SRC-014", "public_verified"),
    ("NCT05528510", "Clinical remission", 12, "GUS 400 mg SC induction", "Placebo", 27.6, 6.5, "ITT", True, "SRC-016", "public_verified"),
    ("NCT05347095", "Combined fistula remission", 24, "GUS 100 mg SC q8w", "Placebo", 28.3, 10.3, "ITT", True, "SRC-011", "public_verified"),
    ("NCT05347095", "Combined fistula remission", 24, "GUS 200 mg SC q4w", "Placebo", 27.0, 10.3, "ITT", True, "SRC-011", "public_verified"),
    ("NCT05347095", "Clinical fistula response", 24, "GUS 100 mg SC q8w", "Placebo", 32.7, 13.8, "ITT", False, "SRC-011", "public_verified"),
    ("NCT05347095", "Clinical fistula response", 24, "GUS 200 mg SC q4w", "Placebo", 35.7, 13.8, "ITT", False, "SRC-011", "public_verified"),
    ("NCT06049017", "Clinical response", 12, "Icotrokinra highest dose", "Placebo", 63.5, 27.0, "ITT", True, "SRC-044", "public_verified"),
    ("NCT06049017", "Clinical remission", 12, "Icotrokinra highest dose", "Placebo", 30.2, 11.1, "ITT", False, "SRC-044", "public_verified"),
    ("NCT06049017", "Clinical remission", 28, "Icotrokinra highest dose", "", 31.7, None, "ITT", False, "SRC-009", "public_verified"),
    ("NCT06049017", "Endoscopic improvement", 28, "Icotrokinra highest dose", "", 38.1, None, "ITT", False, "SRC-009", "public_verified"),
    ("NCT05242471", "Clinical remission", 48, "JNJ-4804 (GUS+GOL)", "Guselkumab mono", 50.8, 42.5, "ITT", False, "SRC-013", "public_verified"),
    ("NCT05242471", "Endoscopic response", 48, "JNJ-4804 (GUS+GOL)", "Guselkumab mono", 38.1, 33.9, "ITT", False, "SRC-013", "public_verified"),
    ("NCT05242484", "Clinical remission", 48, "JNJ-4804 (GUS+GOL)", "", 41.0, None, "ITT", False, "SRC-012", "public_verified"),
    ("NCT04524611", "Clinical remission (CDAI)", 24, "Risankizumab", "Ustekinumab", 58.6, 39.5, "TNF-IR", True, "SRC-026", "public_verified"),
    ("NCT04524611", "Endoscopic remission", 48, "Risankizumab", "Ustekinumab", 31.8, 16.2, "TNF-IR", True, "SRC-026", "public_verified"),
    ("NCT05535946", "Clinical remission (Part 2, induction non-responders)", 44, "Obefazimod 50 mg", "", 37.2, None, "Induction non-responders", False, "SRC-023", "public_verified"),
]

# ---------------------------------------------------------------- publications already public
# output_id, study NCT, analysis_type, publication_type, venue_id, date, title, peer_review, source, origin
OUTPUTS_PUBLIC = [
    ("OUT-P001", "NCT04033445", "Primary analysis", "Primary manuscript", "J-LANCET", "2025", "QUASAR Ph3 induction and maintenance", "peer-reviewed journal", "SRC-019", "public_verified"),
    ("OUT-P002", "NCT04033445", "Primary analysis", "Primary manuscript", "J-GASTRO", "2023", "QUASAR Ph2b induction", "peer-reviewed journal", "SRC-020", "public_verified"),
    ("OUT-P003", "NCT03466411", "Primary analysis", "Primary manuscript", "J-LANCET", "2025", "GALAXI-2/3 48-week results", "peer-reviewed journal", "SRC-017", "public_verified"),
    ("OUT-P004", "NCT05197049", "Primary analysis", "Primary manuscript", "J-GASTRO", "2025", "GRAVITI SC induction in CD", "peer-reviewed journal", "SRC-014", "public_verified"),
    ("OUT-P005", "NCT05528510", "Primary analysis", "Oral presentation", "C-ECCO25", "2025-02", "ASTRO week 12 (OP10)", "peer-reviewed abstract", "SRC-041", "public_verified"),
    ("OUT-P006", "NCT05528510", "Primary analysis", "Primary manuscript", "J-LGH", "2025", "ASTRO Lancet Gastroenterol Hepatol", "peer-reviewed journal", "SRC-015", "public_verified"),
    ("OUT-P007", "NCT05528510", "Secondary analysis", "Oral presentation", "C-ECCO26", "2026-02", "ASTRO week 48 by week-12 response status (DOP105)", "peer-reviewed abstract", "SRC-040", "public_verified"),
    ("OUT-P008", "NCT05347095", "Primary analysis", "Oral presentation", "C-DDW26", "2026-05", "FUZION CD week 24 perianal fistula results", "peer-reviewed abstract", "SRC-011", "public_verified"),
    ("OUT-P009", "NCT05242471", "Primary analysis", "Oral presentation", "C-DDW26", "2026-05", "DUET-CD week 48", "peer-reviewed abstract", "SRC-012", "public_verified"),
    ("OUT-P010", "NCT05242484", "Primary analysis", "Oral presentation", "C-DDW26", "2026-05", "DUET-UC week 48", "peer-reviewed abstract", "SRC-012", "public_verified"),
    ("OUT-P011", "NCT06049017", "Primary analysis", "Press release (topline)", "", "2025", "ANTHEM-UC week 12 topline", "not peer-reviewed", "SRC-008", "public_verified"),
    ("OUT-P012", "NCT06049017", "Secondary analysis", "Press release (topline)", "", "2025", "ANTHEM-UC week 28 data", "not peer-reviewed", "SRC-009", "public_verified"),
    ("OUT-P013", "NCT04524611", "Primary analysis", "Primary manuscript", "J-NEJM", "2024", "SEQUENCE risankizumab vs ustekinumab (competitor)", "peer-reviewed journal", "SRC-026", "public_verified"),
]

# ---------------------------------------------------------------- venues
# venue_id, name, type, region, start, end, city, tier, source, origin
VENUES = [
    ("C-ECCO25", "ECCO 2025", "congress", "EMEA", "2025-02-19", "2025-02-22", "Berlin", 1, "", "public_unverified"),
    ("C-ECCO26", "ECCO 2026", "congress", "EMEA", "2026-02", "2026-02", "", 1, "SRC-040", "public_unverified"),
    ("C-DDW26", "DDW 2026", "congress", "North America", "2026-05", "2026-05", "Chicago", 1, "SRC-012", "public_verified"),
    ("C-ACG26", "ACG 2026", "congress", "North America", "2026-10-09", "2026-10-14", "Nashville", 1, "SRC-034", "public_verified"),
    ("C-UEGW26", "UEG Week 2026", "congress", "EMEA", "2026-10-17", "2026-10-20", "Barcelona", 1, "SRC-033", "public_verified"),
    ("C-AIBD26", "Advances in IBD 2026", "congress", "North America", "2026-12-10", "2026-12-12", "Orlando", 2, "SRC-SIM", "simulated"),
    ("C-ECCO27", "ECCO 2027", "congress", "EMEA", "2027-03-03", "2027-03-06", "Copenhagen", 1, "SRC-035", "public_verified"),
    ("C-DDW27", "DDW 2027", "congress", "North America", "2027-05-15", "2027-05-18", "Washington DC", 1, "SRC-036", "public_verified"),
    ("C-JDDW27", "JDDW 2027", "congress", "APAC", "2027-10-28", "2027-10-31", "Japan", 2, "SRC-SIM", "simulated"),
    ("C-APDW27", "APDW 2027", "congress", "APAC", "2027-11-18", "2027-11-21", "Asia-Pacific", 2, "SRC-SIM", "simulated"),
    ("C-ISPOR27", "ISPOR 2027", "congress", "North America", "2027-05-09", "2027-05-12", "USA", 2, "SRC-SIM", "simulated"),
    ("J-LANCET", "The Lancet", "journal", "Global", "", "", "", 1, "", "public_unverified"),
    ("J-NEJM", "New England Journal of Medicine", "journal", "Global", "", "", "", 1, "", "public_unverified"),
    ("J-GASTRO", "Gastroenterology", "journal", "Global", "", "", "", 1, "", "public_unverified"),
    ("J-LGH", "The Lancet Gastroenterology & Hepatology", "journal", "Global", "", "", "", 1, "", "public_unverified"),
    ("J-JCC", "Journal of Crohn's and Colitis", "journal", "Global", "", "", "", 1, "", "public_unverified"),
    ("J-AJG", "American Journal of Gastroenterology", "journal", "Global", "", "", "", 1, "", "public_unverified"),
    ("J-CGH", "Clinical Gastroenterology and Hepatology", "journal", "Global", "", "", "", 1, "", "public_unverified"),
    ("J-APT", "Alimentary Pharmacology & Therapeutics", "journal", "Global", "", "", "", 2, "", "public_unverified"),
    ("J-IBD", "Inflammatory Bowel Diseases", "journal", "Global", "", "", "", 2, "", "public_unverified"),
]

# ---------------------------------------------------------------- guidelines / HTA
GUIDELINES = [
    ("GL-ACG-UC-2025", "ACG", "UC", "2025-06", "Guselkumab, mirikizumab and risankizumab recommended together as one IL-23 class for induction and maintenance (strong, moderate); vedolizumab preferred over adalimumab", "SRC-037", "public_verified"),
    ("GL-AGA-CD-2025", "AGA (living)", "CD", "2025-11-20", "Recommends infliximab, adalimumab, ustekinumab, risankizumab, mirikizumab, guselkumab, upadacitinib over no treatment; emphasises early high-efficacy therapy over step-up", "SRC-038", "public_verified"),
    ("GL-ACG-CD-2025", "ACG", "CD", "2025-06", "Guselkumab recommended with IV or with SC induction (two strong recommendations); risankizumab also preferred over ustekinumab after anti-TNF (conditional); no IL-23p19 drug suggested for perianal fistulas", "SRC-ACG-CD-2025;SRC-039", "public_verified"),
    ("GL-AGA-UC-2024", "AGA (living)", "UC", "2024-12", "Recommends guselkumab and risankizumab over no treatment; for patients new to advanced therapy lists guselkumab among higher-efficacy options; after prior advanced therapy lists it as intermediate efficacy", "SRC-AGA-UC-2024", "public_verified"),
    ("GL-ECCO-UC-2026", "ECCO", "UC", "2026-07", "Guselkumab recommended for induction and maintenance (strong, moderate certainty for both); SC guselkumab induction noted as effective; no drug preferred first-line except vedolizumab over adalimumab", "SRC-ECCO-UC-2026", "public_verified"),
    ("GL-ECCO-CD-2024", "ECCO", "CD", "2024-10", "No guselkumab recommendation (only phase 2 GALAXI-1 and the DUET trial mentioned); risankizumab and upadacitinib recommended (strong, high certainty); mirikizumab not covered", "SRC-ECCO-CD-2024", "public_verified"),
    ("GL-BSG-UC-2025", "BSG", "UC", "2025-06", "Guselkumab not mentioned; risankizumab, mirikizumab and ustekinumab suggested; upadacitinib recommended; adalimumab not suggested", "SRC-BSG-2025", "public_verified"),
    ("GL-BSG-CD-2025", "BSG", "CD", "2025-06", "Guselkumab and mirikizumab not mentioned; risankizumab, ustekinumab and upadacitinib suggested; vedolizumab not suggested", "SRC-BSG-2025", "public_verified"),
]

HTA_PUBLIC = [
    ("HTA-001", "GBR", "NICE", "TRE", "CD", "recommended (restricted)", "TA1095: an option when conventional or biological treatment has not worked or is not tolerated, and a TNF-alpha inhibitor has not worked, is not tolerated or is not suitable", "2025-08-28", "SRC-NICE-TA1095;SRC-007", "public_verified"),
    ("HTA-002", "GBR", "NICE", "TRE", "UC", "recommended (restricted)", "TA1094: an option when conventional, biological or JAK treatment has not worked or is not tolerated, and a TNF-alpha inhibitor has not worked, is not tolerated or is not suitable", "2025-08-28", "SRC-NICE-TA1094;SRC-007", "public_verified"),
    ("HTA-003", "DEU", "G-BA", "TRE", "UC", "no added benefit proven", "Added benefit not proven: no usable data after biologics; no relevant differences after conventional therapy", "2025-11-20", "SRC-GBA-UC;SRC-AMT-GBA", "public_verified"),
    ("HTA-004", "DEU", "G-BA", "TRE", "CD", "minor added benefit (after biologics)", "Hint of minor added benefit after biologic therapy (vs ustekinumab); added benefit not proven after conventional therapy", "2025-11-20", "SRC-GBA-CD;SRC-AMT-GBA", "public_verified"),
    ("HTA-005", "FRA", "HAS", "TRE", "UC", "recommended (restricted)", "Clinical benefit moderate, no added benefit (no ASMR); reimbursed only after conventional treatment, at least one anti-TNF and vedolizumab", "2025-07-16", "SRC-HAS-UC;SRC-VIDAL-TRE", "public_verified"),
    ("HTA-006", "FRA", "HAS", "TRE", "CD", "recommended (restricted)", "Clinical benefit important, no added benefit (ASMR V); reimbursed after conventional treatment and at least one anti-TNF, or when these are contraindicated", "2025-11-19", "SRC-VIDAL-TRE", "public_verified"),
    ("HTA-007", "CAN", "CDA-AMC", "TRE", "UC", "recommended (restricted)", "Reimburse with conditions: same patients as other advanced UC therapies; not good value at the public list price, so a price reduction is needed", "2025-11", "SRC-CDA-UC", "public_verified"),
    ("HTA-008", "CAN", "CDA-AMC", "TRE", "CD", "recommended (restricted)", "Reimburse with conditions", "2025-09", "SRC-CDA-CD", "public_verified"),
]

# ---------------------------------------------------------------- market (public points)
MARKET_PUBLIC = [
    ("2026-Q2", "GLOBAL", "ALL", "TRE", "net_sales_usd_m", 2050, "Tremfya WW sales Q2 2026 (+72.5% YoY), all indications", "SRC-030", "public_verified"),
    ("2026-Q2", "GLOBAL", "ALL", "STE", "net_sales_usd_m", 740, "Stelara WW sales Q2 2026 (-55.7% YoY)", "SRC-030", "public_verified"),
    ("2026-Q2", "USA", "UC-induction-IL23", "TRE", "share_of_il23_induction_pct", 58, "Tremfya share of IL-23 induction in UC (company-reported)", "SRC-031", "public_verified"),
    ("2026-FY", "GLOBAL", "ALL", "SKY", "guided_net_sales_usd_m", 21600, "Skyrizi 2026 revenue expectation, all indications", "SRC-027", "public_verified"),
    ("2026-Q2", "USA", "IBD-1L-IL23-in-play", "SKY", "in_play_capture_rate_pct", 75, "Skyrizi capture rate among IL-23s in front-line IBD (company-reported)", "SRC-027", "public_verified"),
]

# NCT -> known public milestone dates beyond registry (topline / first presentation)
PUBLIC_MILESTONES = [
    ("NCT05242471", "TLPR", "2026-05-05", "SRC-012"),
    ("NCT05242484", "TLPR", "2026-05-05", "SRC-012"),
    ("NCT05242471", "ABS1", "2026-05", "SRC-012"),
    ("NCT05242484", "ABS1", "2026-05", "SRC-012"),
    ("NCT05347095", "ABS1", "2026-05", "SRC-011"),
    ("NCT05347095", "TLPR", "2026-05", "SRC-011"),
    ("NCT05528510", "ABS1", "2025-02", "SRC-041"),
    ("NCT05528510", "MS1", "2025", "SRC-015"),
    ("NCT05528510", "APP", "2025-09-19", "SRC-003"),
    ("NCT05197049", "MS1", "2025", "SRC-014"),
    ("NCT05197049", "APP", "2025-03", "SRC-002"),
    ("NCT03466411", "MS1", "2025", "SRC-017"),
    ("NCT03466411", "APP", "2025-03", "SRC-002"),
    ("NCT04033445", "MS1", "2025", "SRC-019"),
    ("NCT04033445", "APP", "2024-09", "SRC-001"),
    ("NCT06049017", "TLPR", "2025", "SRC-008"),
]


# ------------------------------------------------------------------ product profiles (label-based)
# Regimens copied from the US labels (SRC-LBL-*). "filed" rows carry what the sponsor has disclosed;
# None means NOT DISCLOSED, which is shown as unknown, never as "no".
# (reg_id, brand, indication, phase, label, route, dose_mg, induction_weeks, start_week, interval_weeks,
#  devices_per_dose_min, device_options, setting, infusion_min_hours, status, source)
REGIMENS = []
for ind in ("CD", "UC"):
    REGIMENS += [
        (f"TRE-{ind}-IND-IV", "TRE", ind, "induction", "200 mg IV at weeks 0, 4, 8", "IV", 200, [0, 4, 8], None, None, 1, "IV infusion by a healthcare professional", "infusion", 1.0, "label", "SRC-LBL-TRE"),
        (f"TRE-{ind}-IND-SC", "TRE", ind, "induction", "400 mg SC at weeks 0, 4, 8", "SC", 400, [0, 4, 8], None, None, 2, "two consecutive 200 mg injections (prefilled pen or syringe)", "self-injection after training", None, "label", "SRC-LBL-TRE"),
        (f"TRE-{ind}-MNT-100", "TRE", ind, "maintenance", "100 mg SC every 8 weeks from week 16", "SC", 100, None, 16, 8, 1, "prefilled pen, prefilled syringe or One-Press injector", "self-injection after training", None, "label", "SRC-LBL-TRE"),
        (f"TRE-{ind}-MNT-200", "TRE", ind, "maintenance", "200 mg SC every 4 weeks from week 12", "SC", 200, None, 12, 4, 1, "200 mg/2 mL prefilled pen or syringe", "self-injection after training", None, "label", "SRC-LBL-TRE"),
        (f"SKY-{ind}-MNT-180", "SKY", ind, "maintenance", "180 mg SC every 8 weeks from week 12", "SC", 180, None, 12, 8, 1, "on-body injector, one 180 mg syringe, or two 90 mg syringes", "self-injection after training", None, "label", "SRC-LBL-SKY"),
        (f"SKY-{ind}-MNT-360", "SKY", ind, "maintenance", "360 mg SC every 8 weeks from week 12", "SC", 360, None, 12, 8, 1, "on-body injector, two 180 mg syringes, or four 90 mg syringes", "self-injection after training", None, "label", "SRC-LBL-SKY"),
    ]
REGIMENS += [
    ("SKY-CD-IND-IV", "SKY", "CD", "induction", "600 mg IV at weeks 0, 4, 8", "IV", 600, [0, 4, 8], None, None, 1, "IV infusion (1 vial) by a healthcare professional", "infusion", 1.0, "label", "SRC-LBL-SKY"),
    ("SKY-UC-IND-IV", "SKY", "UC", "induction", "1,200 mg IV at weeks 0, 4, 8", "IV", 1200, [0, 4, 8], None, None, 1, "IV infusion (2 vials) by a healthcare professional", "infusion", 2.0, "label", "SRC-LBL-SKY"),
    ("SKY-CD-IND-SC", "SKY", "CD", "induction", "SC induction (filed; dose and schedule not disclosed)", "SC", None, None, None, None, None, "not disclosed", "not disclosed", None, "filed", "SRC-024"),
]

# Attribute values per brand x indication. scenario "now" = current labels; "filed" = if SKYRIZI SC induction is approved as filed.
# kind drives the verdict rule: bool (yes beats no), lower / higher (numeric), cross (cross-trial: never a claim),
# different (formats differ, no preference evidence), pending (answered by an ongoing trial), same (descriptive parity).
# (attr_id, group, attribute, indication, kind, stakeholders, tre_value, sky_now, sky_filed, tre_src, sky_src, note)
ATTRIBUTES = []
for ind in ("CD", "UC"):
    sky_sc = "yes (filed)" if ind == "CD" else "no (not filed)"
    ATTRIBUTES += [
        (f"A-{ind}-01", "Administration", "SC induction available", ind, "bool", "patient; IBD nurse; HCP", "yes", "no", sky_sc, "SRC-LBL-TRE", "SRC-LBL-SKY" if ind == "UC" else "SRC-LBL-SKY;SRC-024", ""),
        (f"A-{ind}-02", "Administration", "Fully subcutaneous regimen possible (no infusion)", ind, "bool", "patient; infusion centre; payer", "yes", "no", sky_sc, "SRC-LBL-TRE", "SRC-LBL-SKY" if ind == "UC" else "SRC-LBL-SKY;SRC-024", ""),
        (f"A-{ind}-03", "Administration", "IV induction available", ind, "bool", "HCP; hospital", "yes", "yes", "yes", "SRC-LBL-TRE", "SRC-LBL-SKY", ""),
        (f"A-{ind}-04", "Administration", "Minimum infusion time per IV induction dose (hours)", ind, "lower", "patient; infusion centre", 1.0, 1.0 if ind == "CD" else 2.0, 1.0 if ind == "CD" else 2.0, "SRC-LBL-TRE", "SRC-LBL-SKY", "label minimum"),
        (f"A-{ind}-05", "Administration", "Injections per SC induction dose", ind, "lower", "patient", 2, "n/a (no SC induction)", "not disclosed" if ind == "CD" else "n/a (no SC induction)", "SRC-LBL-TRE", "SRC-024", "TREMFYA: two consecutive 200 mg injections"),
        (f"A-{ind}-06", "Administration", "Longest maintenance interval (weeks)", ind, "higher", "patient; HCP", 8, 8, 8, "SRC-LBL-TRE", "SRC-LBL-SKY", "TREMFYA also offers 200 mg every 4 weeks"),
        (f"A-{ind}-07", "Administration", "Fewest devices per maintenance dose", ind, "lower", "patient", 1, 1, 1, "SRC-LBL-TRE", "SRC-LBL-SKY", ""),
        (f"A-{ind}-08", "Administration", "Maintenance device formats", ind, "different", "patient; IBD nurse", "pen, syringe, One-Press injector", "on-body injector or syringe", "on-body injector or syringe", "SRC-LBL-TRE", "SRC-LBL-SKY", "no published preference evidence between formats"),
        (f"A-{ind}-09", "Administration", "Self-injection after training", ind, "bool", "patient", "yes", "yes", "yes", "SRC-LBL-TRE", "SRC-LBL-SKY", ""),
        (f"A-{ind}-10", "Monitoring", "Liver tests before starting", ind, "same", "HCP; patient", "yes", "yes", "yes", "SRC-LBL-TRE", "SRC-LBL-SKY", "both labels: drug-induced liver injury warning in IBD"),
        (f"A-{ind}-11", "Monitoring", "Minimum liver-monitoring window (weeks)", ind, "lower", "HCP; patient", 16, 12, 12, "SRC-LBL-TRE", "SRC-LBL-SKY", "TREMFYA: at least 16 weeks, then periodically; SKYRIZI: at least 12 weeks of induction"),
        (f"A-{ind}-12", "Safety", "Boxed warning", ind, "same", "HCP; payer", "none", "none", "none", "SRC-LBL-TRE", "SRC-LBL-SKY", ""),
        (f"A-{ind}-13", "Safety", "Warnings and precautions", ind, "same", "HCP", "hypersensitivity, infections, TB, hepatotoxicity, live vaccines", "hypersensitivity, infections, TB, hepatotoxicity, live vaccines", "same", "SRC-LBL-TRE", "SRC-LBL-SKY", "same categories on both labels"),
    ]
ATTRIBUTES += [
    ("A-CD-20", "Efficacy", "SC induction: clinical remission at week 12 vs placebo", "CD", "cross", "HCP; guideline; payer", "56.1% vs 21.4% (GRAVITI)", "n/a (no SC induction)", "55% vs 30% (AFFIRM topline)", "SRC-014", "SRC-AFFIRM-TL", "different trials and populations (AFFIRM: 65% prior advanced-therapy failure)"),
    ("A-CD-21", "Efficacy", "SC induction: endoscopic response at week 12 vs placebo", "CD", "cross", "HCP; guideline; payer", "41.3% vs 21.4% (GRAVITI)", "n/a (no SC induction)", "44% vs 14% (AFFIRM topline)", "SRC-014", "SRC-AFFIRM-TL", "different trials and populations"),
    ("A-CD-22", "Evidence", "Head-to-head, guselkumab vs risankizumab", "CD", "pending", "HCP; guideline; payer", "CHARGE ongoing (primary completion Nov 2028)", "CHARGE ongoing", "CHARGE ongoing", "SRC-CTGOV", "SRC-CTGOV", "the only way to settle efficacy differences"),
    ("A-CD-23", "Evidence", "Head-to-head vs ustekinumab", "CD", "same", "HCP; guideline", "GALAXI 2/3", "SEQUENCE", "SEQUENCE", "SRC-CTGOV", "SRC-026", "both have one"),
    ("A-UC-20", "Efficacy", "SC induction: clinical remission at week 12 vs placebo", "UC", "cross", "HCP; guideline; payer", "27.6% vs 6.5% (ASTRO)", "n/a (no SC induction)", "n/a (not filed in UC)", "SRC-016", "SRC-LBL-SKY", ""),
]

# Open questions the watchers check (see SCALE_PLAN.md section 6)
WATCH = [
    ("W-001", "SKY", "SKYRIZI SC induction in CD: dose, injections per dose and schedule", "not disclosed", "US label on Drugs@FDA / DailyMed at approval", "CI lead", "A-CD-05; SKY-CD-IND-SC"),
    ("W-002", "SKY", "SKYRIZI SC induction in CD: FDA decision date", "AbbVie guidance: later in 2026", "FDA approval letter / AbbVie release", "CI lead", "EV-101"),
    ("W-003", "SKY", "SKYRIZI SC induction in CD: EU decision", "EMA filing Sep 2026", "EMA CHMP opinion / EC decision", "EU medical lead", "EV-102"),
    ("W-004", "SKY", "SKYRIZI SC induction in UC: any filing", "not filed", "AbbVie releases; ClinicalTrials.gov", "CI lead", "A-UC-01"),
]

# ---------------------------------------------------------------- loss of exclusivity (LOE), checked 2026-09-26
SOURCES += [
    ("SRC-LOE-JNJ", "annual report", "Johnson & Johnson Form 10-K FY2025: TREMFYA composition patent family projected to expire in the US in 2031; STELARA biosimilar competition", "Johnson & Johnson / SEC", "2026-02", "https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm", "A"),
    ("SRC-LOE-ABBV", "annual report", "AbbVie Form 10-K FY2025: US composition of matter patents for risankizumab and upadacitinib expire 2033; no generic Rinvoq tablets expected before April 2037 (settlements, assuming pediatric exclusivity)", "AbbVie / SEC", "2026-02", "https://www.sec.gov/Archives/edgar/data/1551152/000155115226000008/abbv-20251231.htm", "A"),
    ("SRC-LOE-LLY", "annual report", "Eli Lilly Form 10-K FY2025: Omvoh compound patent US 2037, major European countries 2038; biologics data protection US 2035, Europe 2033", "Eli Lilly / SEC", "2026-02", "https://www.sec.gov/Archives/edgar/data/59478/000005947826000013/lly-20251231.htm", "A"),
    ("SRC-LOE-BMS", "annual report", "Bristol Myers Squibb Form 10-K FY2025: Zeposia estimated minimum market exclusivity US 2033, EU 2034; generic patent litigation settled", "Bristol Myers Squibb / SEC", "2026-02", "https://www.sec.gov/Archives/edgar/data/14272/000001427226000004/bmy-20251231.htm", "A"),
    ("SRC-LOE-TAK", "annual report", "Takeda Form 20-F FY2025: Entyvio faces loss of regulatory exclusivity in the latter half of this decade; certain US/EU patents expire 2032; biosimilar timing uncertain", "Takeda / SEC", "2026-06", "https://www.sec.gov/Archives/edgar/data/1395064/000139506426000177/tak-20260331.htm", "A"),
    ("SRC-LOE-AVT", "press release", "Alvotech: FDA accepts BLA for AVT16, proposed interchangeable biosimilar to Entyvio (decision expected Q1 2027)", "Alvotech", "2026", "https://www.alvotech.com/newsroom/alvotech-announces-fda-acceptance-of-biologics-license-application-for-avt16-a-proposed-interchangeable-biosimilar-to-entyvio", "A"),
    ("SRC-LOE-TAKSUIT", "news", "Takeda files BPCIA action against Alvotech over AVT16 (vedolizumab), 1 Sep 2026", "Pearce IP", "2026-09-01", "https://www.pearceip.law/2026/09/01/takeda-files-second-vedolizumab-biosimilar-bpcia-action-with-alvotech-in-the-firing-line/", "B"),
    ("SRC-ICO-NDA", "press release", "J&J submits New Drug Application for icotrokinra in plaque psoriasis (21 Jul 2025)", "Johnson & Johnson", "2025-07-21", "https://www.jnj.com/media-center/press-releases/johnson-johnson-seeks-first-icotrokinra-u-s-fda-approval-aiming-to-revolutionize-treatment-paradigm-for-adults-and-adolescents-with-plaque-psoriasis", "A"),
    ("SRC-STE-BIOSIM", "news", "Stelara biosimilars entered the US market on 1 January 2025", "Fierce Pharma", "2025", "https://www.fiercepharma.com/pharma/jj-stands-sales-growth-ambitions-and-points-potential-tremfya-boon-stelara-biosimilars-take", "B"),
    ("SRC-LLM", "observation", "AI assistant answers to the fixed IBD question bank (ChatGPT logged out; Claude incognito), captured and scored by the prototype; see data/raw/llm", "Prototype (observed)", "2026-09-29", "", "B"),
    ("SRC-EXCL-RULES", "reference", "Exclusivity rules: US biologics 12 years from first licensure (BPCIA, +6 months paediatric); US new chemical entity 5 years; EU 8 years data + 2 years market protection (+1 for a significant new indication)", "FDA / EMA", "2026", "https://www.fda.gov/drugs/development-approval-process-drugs/frequently-asked-questions-patents-and-exclusivity", "A"),
]

# One row per product and market. Dates are YYYY-MM. 'protect' = the public patent/settlement signal; 'planning' = the date the
# dashboard calculates with. For J&J products the planning date must be confirmed by J&J IP; placeholders are marked simulated.
# keys: b brand, m market, type, appr first approval in that market, appr_src, appr_ok (True = checked source), floor regulatory
# floor + basis, protect date + basis + src, plan planning date + basis + kind ('public' | 'sim' | 'passed'), lo/hi planning range
LOE = [
    dict(b="TRE", m="US", type="biologic (BLA)", appr="2017-07", appr_src=None, appr_ok=False, floor="2029-07", floor_basis="12-year biologic exclusivity from first licensure (psoriasis, Jul 2017)",
         protect="2031-07", protect_basis="composition patent family projected to expire in 2031 (other patent families may extend protection)", protect_src="SRC-LOE-JNJ",
         plan="2031-07", plan_basis="mid-year of the disclosed composition-patent year (month not disclosed); J&J IP to confirm", kind="public", lo="2031-01", hi="2033-12"),
    dict(b="TRE", m="EU", type="biologic", appr="2017-11", appr_src=None, appr_ok=False, floor="2027-11", floor_basis="8+2 years EU data and market protection (+1 year possible)",
         protect=None, protect_basis="not disclosed (EU patents / SPCs)", protect_src=None,
         plan="2032-01", plan_basis="placeholder: SPC-extended patents usually outlast EU market protection; J&J IP to set", kind="sim", lo="2029-01", hi="2034-12"),
    dict(b="ICO", m="US", type="oral peptide (NDA)", appr="2026-03", appr_src="SRC-010", appr_ok=True, floor="2031-03", floor_basis="5-year new chemical entity exclusivity (approved in psoriasis Mar 2026)",
         protect=None, protect_basis="not disclosed", protect_src=None,
         plan="2040-01", plan_basis="placeholder: patent life of a 2026 launch; J&J IP to set", kind="sim", lo="2036-01", hi="2042-12"),
    dict(b="ICO", m="EU", type="oral peptide", appr=None, appr_src=None, appr_ok=False, floor=None, floor_basis="8+2 years from EU approval (not yet approved)",
         protect=None, protect_basis="not disclosed", protect_src=None,
         plan="2041-01", plan_basis="placeholder; J&J IP to set", kind="sim", lo="2037-01", hi="2043-12"),
    dict(b="JNJ4804", m="US", type="combination (guselkumab + golimumab)", appr="2029-06", appr_src="SRC-SIM", appr_ok=False, floor=None,
         floor_basis="unclear: a co-formulation of two licensed antibodies may not earn a new 12-year exclusivity",
         protect=None, protect_basis="not disclosed (co-formulation and use patents)", protect_src=None,
         plan="2040-01", plan_basis="placeholder (expected approval simulated); J&J IP to set", kind="sim", lo="2034-01", hi="2044-12"),
    dict(b="JNJ4804", m="EU", type="combination (guselkumab + golimumab)", appr=None, appr_src=None, appr_ok=False, floor=None, floor_basis="unclear (combination of authorised antibodies)",
         protect=None, protect_basis="not disclosed", protect_src=None, plan="2041-01", plan_basis="placeholder; J&J IP to set", kind="sim", lo="2035-01", hi="2044-12"),
    dict(b="STE", m="US", type="biologic (BLA)", appr="2009-09", appr_src=None, appr_ok=False, floor="2021-09", floor_basis="12-year biologic exclusivity (ended)",
         protect="2025-01", protect_basis="biosimilars launched 1 Jan 2025", protect_src="SRC-STE-BIOSIM",
         plan="2025-01", plan_basis="LOE passed: biosimilars on market", kind="passed", lo="2025-01", hi="2025-01"),
    dict(b="STE", m="EU", type="biologic", appr="2009-01", appr_src=None, appr_ok=False, floor="2019-01", floor_basis="10-year EU market protection (ended)",
         protect="2024-07", protect_basis="biosimilars launched mid-2024 (public knowledge, not re-checked)", protect_src="SRC-LOE-JNJ", protect_ok=False,
         plan="2024-07", plan_basis="LOE passed: biosimilars on market", kind="passed", lo="2024-07", hi="2024-07"),
    dict(b="SKY", m="US", type="biologic (BLA)", appr="2019-04", appr_src=None, appr_ok=False, floor="2031-04", floor_basis="12-year biologic exclusivity (psoriasis, Apr 2019)",
         protect="2033-07", protect_basis="US composition of matter patent expires 2033", protect_src="SRC-LOE-ABBV",
         plan="2033-07", plan_basis="mid-year of the disclosed patent year", kind="public", lo="2033-01", hi="2035-12"),
    dict(b="SKY", m="EU", type="biologic", appr="2019-04", appr_src=None, appr_ok=False, floor="2029-04", floor_basis="8+2 years (+1 possible)",
         protect=None, protect_basis="not disclosed", protect_src=None, plan="2033-07", plan_basis="placeholder: assumed in line with the US patent", kind="sim", lo="2030-01", hi="2035-12"),
    dict(b="OMV", m="US", type="biologic (BLA)", appr="2023-10", appr_src=None, appr_ok=False, floor="2035-10", floor_basis="biologics data protection 2035 (Lilly)",
         protect="2037-07", protect_basis="compound patent 2037", protect_src="SRC-LOE-LLY",
         plan="2037-07", plan_basis="mid-year of the disclosed patent year", kind="public", lo="2037-01", hi="2038-12"),
    dict(b="OMV", m="EU", type="biologic", appr="2023-05", appr_src=None, appr_ok=False, floor="2033-05", floor_basis="data protection 2033 (Lilly)",
         protect="2038-07", protect_basis="compound patent 2038 (major European countries)", protect_src="SRC-LOE-LLY",
         plan="2038-07", plan_basis="mid-year of the disclosed patent year", kind="public", lo="2038-01", hi="2039-12"),
    dict(b="RIN", m="US", type="small molecule (NDA)", appr="2019-08", appr_src=None, appr_ok=False, floor="2024-08", floor_basis="5-year new chemical entity exclusivity (ended)",
         protect="2037-04", protect_basis="no generic entry before Apr 2037 under settlements (assuming paediatric exclusivity); composition patent 2033", protect_src="SRC-LOE-ABBV",
         plan="2037-04", plan_basis="settlement date", kind="public", lo="2037-04", hi="2037-10"),
    dict(b="RIN", m="EU", type="small molecule", appr="2019-12", appr_src=None, appr_ok=False, floor="2029-12", floor_basis="8+2 years",
         protect=None, protect_basis="not disclosed", protect_src=None, plan="2034-01", plan_basis="placeholder: composition patent plus SPC assumed", kind="sim", lo="2030-01", hi="2037-12"),
    dict(b="ENT", m="US", type="biologic (BLA)", appr="2014-05", appr_src=None, appr_ok=False, floor="2026-05", floor_basis="12-year biologic exclusivity (ended May 2026)",
         protect="2032-05", protect_basis="formulation, dosing and manufacturing patents expire 2032; AVT16 biosimilar BLA under review (decision Q1 2027); Takeda sued Sep 2026", protect_src="SRC-LOE-TAK",
         plan="2032-05", plan_basis="patent expiry; earlier entry possible if the litigation fails", kind="public", lo="2027-04", hi="2032-05"),
    dict(b="ENT", m="EU", type="biologic", appr="2014-05", appr_src=None, appr_ok=False, floor="2024-05", floor_basis="10-year EU market protection (ended)",
         protect="2032-05", protect_basis="certain patents expire 2032; biosimilar timing uncertain", protect_src="SRC-LOE-TAK",
         plan="2032-05", plan_basis="patent expiry; earlier entry possible", kind="public", lo="2027-01", hi="2032-05"),
    dict(b="VEL", m="US", type="small molecule (NDA)", appr="2023-10", appr_src=None, appr_ok=False, floor="2028-10", floor_basis="5-year new chemical entity exclusivity",
         protect=None, protect_basis="not verified (Orange Book not checked)", protect_src=None, plan="2034-01", plan_basis="placeholder: patents assumed to outlast NCE exclusivity", kind="sim", lo="2028-10", hi="2037-12"),
    dict(b="VEL", m="EU", type="small molecule", appr="2024-02", appr_src=None, appr_ok=False, floor="2034-02", floor_basis="8+2 years",
         protect=None, protect_basis="not disclosed", protect_src=None, plan="2034-02", plan_basis="regulatory floor used (patents not checked)", kind="sim", lo="2034-02", hi="2037-12"),
    dict(b="ZEP", m="US", type="small molecule (NDA)", appr="2020-03", appr_src=None, appr_ok=False, floor="2025-03", floor_basis="5-year new chemical entity exclusivity (ended)",
         protect="2033-07", protect_basis="estimated minimum market exclusivity 2033; generic litigation settled", protect_src="SRC-LOE-BMS",
         plan="2033-07", plan_basis="mid-year of the disclosed year", kind="public", lo="2033-01", hi="2033-12"),
    dict(b="ZEP", m="EU", type="small molecule", appr="2020-05", appr_src=None, appr_ok=False, floor="2030-05", floor_basis="8+2 years",
         protect="2034-07", protect_basis="estimated minimum market exclusivity 2034", protect_src="SRC-LOE-BMS",
         plan="2034-07", plan_basis="mid-year of the disclosed year", kind="public", lo="2034-01", hi="2034-12"),
    dict(b="OBE", m="US", type="small molecule (NDA)", appr="2027-10", appr_src="SRC-023", appr_ok=False, floor="2032-10", floor_basis="5-year NCE exclusivity from expected approval (NDA planned Q4 2026 + standard review)",
         protect=None, protect_basis="not verified", protect_src=None, plan="2037-01", plan_basis="placeholder", kind="sim", lo="2032-10", hi="2040-12"),
    dict(b="OBE", m="EU", type="small molecule", appr=None, appr_src=None, appr_ok=False, floor=None, floor_basis="8+2 years from EU approval (not filed)",
         protect=None, protect_basis="not verified", protect_src=None, plan="2038-01", plan_basis="placeholder", kind="sim", lo="2034-01", hi="2040-12"),
    dict(b="TUL", m="US", type="biologic (investigational)", appr="2028-06", appr_src="SRC-SIM", appr_ok=False, floor="2040-06", floor_basis="12 years from expected approval (simulated)",
         protect=None, protect_basis="not verified", protect_src=None, plan="2040-06", plan_basis="placeholder: regulatory floor from simulated approval", kind="sim", lo="2039-01", hi="2043-12"),
    dict(b="TUL", m="EU", type="biologic (investigational)", appr=None, appr_src=None, appr_ok=False, floor=None, floor_basis="8+2 years from EU approval",
         protect=None, protect_basis="not verified", protect_src=None, plan="2039-01", plan_basis="placeholder", kind="sim", lo="2038-01", hi="2043-12"),
    dict(b="DUV", m="US", type="biologic (investigational)", appr="2029-06", appr_src="SRC-SIM", appr_ok=False, floor="2041-06", floor_basis="12 years from expected approval (simulated)",
         protect=None, protect_basis="not verified", protect_src=None, plan="2041-06", plan_basis="placeholder: regulatory floor from simulated approval", kind="sim", lo="2040-01", hi="2044-12"),
    dict(b="DUV", m="EU", type="biologic (investigational)", appr=None, appr_src=None, appr_ok=False, floor=None, floor_basis="8+2 years from EU approval",
         protect=None, protect_basis="not verified", protect_src=None, plan="2040-01", plan_basis="placeholder", kind="sim", lo="2039-01", hi="2044-12"),
    dict(b="AFI", m="US", type="biologic (investigational)", appr="2029-06", appr_src="SRC-SIM", appr_ok=False, floor="2041-06", floor_basis="12 years from expected approval (simulated)",
         protect=None, protect_basis="not verified", protect_src=None, plan="2041-06", plan_basis="placeholder: regulatory floor from simulated approval", kind="sim", lo="2040-01", hi="2044-12"),
    dict(b="AFI", m="EU", type="biologic (investigational)", appr=None, appr_src=None, appr_ok=False, floor=None, floor_basis="8+2 years from EU approval",
         protect=None, protect_basis="not verified", protect_src=None, plan="2040-01", plan_basis="placeholder", kind="sim", lo="2039-01", hi="2044-12"),
    dict(b="MOR", m="US", type="small molecule (investigational)", appr="2030-06", appr_src="SRC-SIM", appr_ok=False, floor="2035-06", floor_basis="5-year NCE exclusivity from expected approval (simulated)",
         protect=None, protect_basis="not verified", protect_src=None, plan="2040-01", plan_basis="placeholder", kind="sim", lo="2035-06", hi="2044-12"),
    dict(b="MOR", m="EU", type="small molecule (investigational)", appr=None, appr_src=None, appr_ok=False, floor=None, floor_basis="8+2 years from EU approval",
         protect=None, protect_basis="not verified", protect_src=None, plan="2041-01", plan_basis="placeholder", kind="sim", lo="2036-01", hi="2044-12"),
]
WATCH += [
    ("W-005", "ENT", "ENTYVIO biosimilar AVT16: FDA decision and outcome of Takeda's patent suit", "BLA under review (decision expected Q1 2027); BPCIA suit filed Sep 2026", "FDA Purple Book; court docket; Alvotech/Teva releases", "CI lead", "LOE-ENT-US"),
    ("W-006", "TRE", "TREMFYA planning LOE (US and EU) confirmed by J&J IP", "US: composition patent family 2031 (10-K); EU not disclosed", "J&J IP / brand plan", "Data owner", "LOE-TRE-US; LOE-TRE-EU"),
]

# ---------------------------------------------------------------- AI-assistant monitoring: question bank (fixed, so runs are comparable over time)
# id, persona, question, what it tests
LLM_QUESTIONS = [
    ("P1", "patient", "I was just diagnosed with ulcerative colitis and mesalamine isn't working. What are my options?", "Which drugs appear first in UC"),
    ("P2", "patient", "What is the best biologic for Crohn's disease?", "Positioning in Crohn's"),
    ("P3", "patient", "Which Crohn's medicines can I inject at home instead of going for infusions?", "Recognition of SC induction"),
    ("P4", "patient", "Are there pills instead of injections for moderate ulcerative colitis?", "Oral options (JAK, S1P, pipeline)"),
    ("P5", "patient", "Humira stopped working for my Crohn's. What should I try next?", "Sequencing after anti-TNF"),
    ("P6", "patient", "Which IBD biologics are safest? I'm worried about infections and cancer.", "Safety framing"),
    ("P7", "patient", "I want to get pregnant. Which IBD medicines are safe to stay on?", "Pregnancy data"),
    ("P8", "patient", "I have a fistula near my bottom from Crohn's. Which medicines help it heal?", "Perianal evidence"),
    ("P9", "patient", "How often do I need injections with the newer IBD drugs?", "Dosing burden"),
    ("P10", "patient", "My insurance switched me to a Stelara biosimilar. Is it as good?", "Biosimilar framing"),
    ("P11", "patient", "What's the difference between Skyrizi and Tremfya?", "Direct comparison, fair balance (branded)"),
    ("P12", "patient", "Which IBD medicine works fastest on urgency and other bad symptoms?", "Speed of onset"),
    ("H1", "HCP", "First-line advanced therapy for a bio-naive patient with moderate-to-severe ulcerative colitis: which agent and why? Cite evidence.", "UC positioning, evidence cited"),
    ("H2", "HCP", "Crohn's disease after anti-TNF failure: how do you choose between IL-23 inhibitors, ustekinumab and upadacitinib?", "Crohn's positioning"),
    ("H3", "HCP", "Compare risankizumab, guselkumab and mirikizumab in Crohn's disease: efficacy, induction route, head-to-head data.", "IL-23 class comparison"),
    ("H4", "HCP", "Which advanced therapies have subcutaneous induction in IBD?", "SC induction recognition"),
    ("H5", "HCP", "What evidence supports IL-23 inhibitors in perianal fistulising Crohn's disease?", "FUZION CD visibility"),
    ("H6", "HCP", "Which head-to-head trials exist in IBD and what did they show?", "GALAXI, SEQUENCE, VIVID-1 citations"),
    ("H7", "HCP", "Which agents have the strongest endoscopic and histologic data in ulcerative colitis?", "Evidence depth"),
    ("H8", "HCP", "Which drugs have transmural-healing data (bowel ultrasound or MR enterography) in Crohn's disease?", "Transmural evidence"),
    ("H9", "HCP", "How do current ACG and AGA guidelines position JAK inhibitors vs IL-23 inhibitors in ulcerative colitis?", "Guideline citation accuracy"),
    ("H10", "HCP", "What is known about the safety of IL-23 inhibitors in pregnancy and lactation?", "Safety data cited"),
    ("H11", "HCP", "What are the liver monitoring requirements for IL-23 inhibitors in IBD?", "Label accuracy"),
    ("H12", "HCP", "What long-term (3+ years) durability data exist for biologics in ulcerative colitis?", "Long-term extension citations"),
    ("H13", "HCP", "What are the oral options for ulcerative colitis, including agents in development such as obefazimod and icotrokinra?", "Pipeline positioning"),
    ("H14", "HCP", "What do you use after IL-23 inhibitor failure in ulcerative colitis?", "Sequencing (portfolio gap GAP-20)"),
    ("H15", "HCP", "What is the evidence for combination advanced therapy in refractory IBD?", "JNJ-4804 / DUET visibility"),
    ("H16", "HCP", "What is in late-stage development for ulcerative colitis and Crohn's disease?", "Pipeline visibility (TL1A, icotrokinra, JNJ-4804)"),
    ("A1", "accuracy", "What are the approved induction regimens for TREMFYA in Crohn's disease?", "US label: SC or IV induction"),
    ("A2", "accuracy", "Is SKYRIZI approved for subcutaneous induction in Crohn's disease?", "Filing status on the run date"),
    ("A3", "accuracy", "What did the GALAXI 2 and 3 studies show?", "Published results"),
    ("A4", "accuracy", "What is icotrokinra, and is it approved for ulcerative colitis?", "Psoriasis approval Mar 2026; UC in Phase 3"),
    ("A5", "accuracy", "What did the SEQUENCE trial compare?", "Published results"),
    ("A6", "accuracy", "What is the ASTRO study?", "Published results"),
]


# ---------------------------------------------------------------- guideline positions (read from full texts, 30 Sep 2026)
# Paraphrased, not quoted. position: recommended (strong) / suggested (conditional or weak) / not suggested / not covered
# (drug not named in a recommendation) / n/a (not approved for that disease). Settings: overall; naive = no prior advanced
# therapy; prior = after advanced therapy; vs = preferred over a named comparator; perianal; route.
_GP = []
def _gp(gid, setting, position, brands, note):
    for b in brands.split():
        _GP.append((gid, b, setting, position, note))

# ACG UC 2025 (full text, Am J Gastroenterol)
_gp("GL-ACG-UC-2025", "overall", "recommended", "TRE SKY OMV", "IL-23 class recommendation for induction and maintenance (strong, moderate)")
_gp("GL-ACG-UC-2025", "overall", "recommended", "RIN", "Induction (strong, high) and maintenance (strong, moderate)")
_gp("GL-ACG-UC-2025", "overall", "recommended", "ENT", "Induction and maintenance (strong, moderate)")
_gp("GL-ACG-UC-2025", "overall", "recommended", "STE ZEP VEL", "Maintenance after response to its own induction (strong, moderate)")
_gp("GL-ACG-UC-2025", "vs", "recommended", "ENT", "Preferred over adalimumab (strong, moderate; VARSITY)")
# ACG CD 2025
_gp("GL-ACG-CD-2025", "overall", "recommended", "TRE", "IV induction then SC maintenance (strong, moderate)")
_gp("GL-ACG-CD-2025", "route", "recommended", "TRE", "Fully subcutaneous induction and maintenance (strong, moderate)")
_gp("GL-ACG-CD-2025", "overall", "recommended", "SKY OMV STE", "Induction and maintenance (strong, moderate)")
_gp("GL-ACG-CD-2025", "overall", "recommended", "ENT", "IV induction and maintenance; SC maintenance option (strong, moderate)")
_gp("GL-ACG-CD-2025", "overall", "recommended", "RIN", "After anti-TNF exposure (strong, moderate)")
_gp("GL-ACG-CD-2025", "vs", "suggested", "SKY", "Preferred over ustekinumab after anti-TNF (conditional, low; SEQUENCE)")
_gp("GL-ACG-CD-2025", "perianal", "suggested", "STE RIN ENT", "Induction in perianal fistulizing disease (conditional, very low)")
_gp("GL-ACG-CD-2025", "overall", "n/a", "ZEP VEL", "Not approved in Crohn's disease")
# AGA UC 2024 (living; PMC full text)
_gp("GL-AGA-UC-2024", "overall", "recommended", "TRE SKY STE RIN ENT ZEP VEL", "Over no treatment (strong, moderate to high)")
_gp("GL-AGA-UC-2024", "overall", "suggested", "OMV", "Over no treatment (conditional)")
_gp("GL-AGA-UC-2024", "naive", "higher", "TRE SKY RIN ENT ZEP VEL", "Higher-efficacy group if new to advanced therapy (conditional, low)")
_gp("GL-AGA-UC-2024", "naive", "intermediate", "STE OMV", "Intermediate-efficacy group if new to advanced therapy (conditional, low)")
_gp("GL-AGA-UC-2024", "prior", "higher", "RIN STE", "Higher-efficacy group after advanced therapy (conditional, low)")
_gp("GL-AGA-UC-2024", "prior", "intermediate", "TRE SKY OMV", "Intermediate-efficacy group after advanced therapy (conditional, low)")
_gp("GL-AGA-UC-2024", "prior", "lower", "ENT ZEP VEL", "Lower-efficacy group after advanced therapy (conditional, low)")
# AGA CD 2025 (living; PMC full text)
_gp("GL-AGA-CD-2025", "overall", "recommended", "TRE SKY OMV STE RIN", "Over no treatment (strong, moderate to high)")
_gp("GL-AGA-CD-2025", "overall", "suggested", "ENT", "Over no treatment (conditional)")
_gp("GL-AGA-CD-2025", "naive", "higher", "TRE SKY OMV STE ENT", "Higher-efficacy group if new to advanced therapy (conditional)")
_gp("GL-AGA-CD-2025", "naive", "lower", "RIN", "Lower-efficacy group if new to advanced therapy (conditional)")
_gp("GL-AGA-CD-2025", "prior", "higher", "TRE SKY RIN", "Higher-efficacy group after advanced therapy (conditional, low to moderate)")
_gp("GL-AGA-CD-2025", "prior", "intermediate", "STE OMV", "Intermediate-efficacy group after advanced therapy (conditional)")
_gp("GL-AGA-CD-2025", "prior", "lower", "ENT", "Lower-efficacy group after advanced therapy (conditional)")
_gp("GL-AGA-CD-2025", "overall", "n/a", "ZEP VEL", "Not approved in Crohn's disease")
# ECCO UC 2026 (full text, J Crohns Colitis)
_gp("GL-ECCO-UC-2026", "overall", "recommended", "TRE", "Induction and maintenance (strong; moderate certainty for both)")
_gp("GL-ECCO-UC-2026", "overall", "recommended", "SKY", "Induction (strong, moderate) and maintenance (strong, low certainty)")
_gp("GL-ECCO-UC-2026", "overall", "recommended", "OMV STE RIN ZEP", "Induction and maintenance (strong, moderate)")
_gp("GL-ECCO-UC-2026", "overall", "recommended", "ENT", "Induction (strong, low) and maintenance (strong, moderate)")
_gp("GL-ECCO-UC-2026", "overall", "recommended", "VEL", "Induction and maintenance (strong, low)")
_gp("GL-ECCO-UC-2026", "route", "recommended", "TRE", "Text states SC guselkumab is also effective for induction (ASTRO)")
_gp("GL-ECCO-UC-2026", "vs", "suggested", "ENT", "Suggested over adalimumab (weak, low)")
# ECCO CD 2024 (full text, J Crohns Colitis)
_gp("GL-ECCO-CD-2024", "overall", "not covered", "TRE", "No recommendation; mentioned only as phase 2 GALAXI-1 and the DUET combination trial")
_gp("GL-ECCO-CD-2024", "overall", "recommended", "SKY RIN", "Induction and maintenance (strong, high / moderate)")
_gp("GL-ECCO-CD-2024", "overall", "recommended", "STE ENT", "Induction and maintenance (strong, moderate)")
_gp("GL-ECCO-CD-2024", "overall", "not covered", "OMV", "Not named in a recommendation")
_gp("GL-ECCO-CD-2024", "overall", "n/a", "ZEP VEL", "Not approved in Crohn's disease")
# BSG 2025 (full text, Gut)
_gp("GL-BSG-UC-2025", "overall", "not covered", "TRE", "Guselkumab not mentioned anywhere in the guideline")
_gp("GL-BSG-UC-2025", "overall", "suggested", "SKY OMV STE ENT ZEP VEL", "Induction and maintenance (conditional)")
_gp("GL-BSG-UC-2025", "overall", "suggested", "RIN", "Induction and maintenance; worded 'recommended' but conditional strength")
_gp("GL-BSG-CD-2025", "overall", "not covered", "TRE OMV", "Not named in a Crohn's recommendation")
_gp("GL-BSG-CD-2025", "overall", "suggested", "SKY STE RIN", "Induction and maintenance (conditional)")
_gp("GL-BSG-CD-2025", "overall", "not suggested", "ENT", "Not suggested for induction and maintenance (conditional)")
_gp("GL-BSG-CD-2025", "overall", "n/a", "ZEP VEL", "Not approved in Crohn's disease")
GUIDELINE_POSITIONS = _GP
