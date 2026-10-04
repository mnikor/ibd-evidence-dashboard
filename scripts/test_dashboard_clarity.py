"""Regression checks for delivery counts and publication-format ambiguity.

Run after rebuilding: python3 scripts/test_dashboard_clarity.py
"""
import json
import pathlib
import subprocess
import unittest

from build_publications import presentation_type

ROOT = pathlib.Path(__file__).resolve().parent.parent


class DashboardClarityTests(unittest.TestCase):
    def test_unmatched_acg_record_is_not_assumed_to_be_a_poster(self):
        self.assertEqual(presentation_type("ACG", "S100 Example", [], "Crossref"),
                         "Abstract (format unverified)")
        self.assertEqual(presentation_type("ACG", "Example", [], "ACG programme",
                                           {"acg_oral": "Late-breaking oral"}),
                         "Late-breaking oral")

    def test_full_oral_counts_include_late_breakers_and_exclude_digital(self):
        data = json.loads((ROOT / "data/raw/pubs/processed.json").read_text())
        pubs = data["publications"]
        self.assertTrue(any(p["presentation_type"] == "Late-breaking oral" for p in pubs))
        self.assertTrue(any(p["presentation_type"] == "Digital oral" for p in pubs))
        for row in data["sov_congress"]:
            expected = sum(p["venue"] == row["venue"] and row["brand_id"] in p["brands_title"]
                           and p["presentation_type"] in ("Oral", "Late-breaking oral") for p in pubs)
            self.assertEqual(row["n_orals"], expected, (row["venue"], row["brand_id"]))

    def test_delivery_counts_and_unknown_dates(self):
        html = (ROOT / "dashboard/index.html").read_text()
        code = html[html.index("function chainVerdict("):html.index("const CH_LVL")]
        fixture = r'''
const assert = require("node:assert/strict");
const pd = s => s ? new Date(s) : null;
const d3 = {max: (xs, f) => xs.map(f).filter(Boolean).sort((a,b) => b-a)[0]};
const si = {required_by_date: "2028-01-01"};
const act = (id, status) => ({s: {study_id:id}, status, fit:0.8, use:pd("2029-01-01")});
const chain = [
  {status:"ok", acts:[act("shared", "ontime"), act("missing-date", "unknown")]},
  {status:"ok", acts:[act("shared", "late"), act("published", "delivered")]},
  {status:"closed", acts:[act("support", "extra")]}
];
const result = chainVerdict(si, chain);
assert.equal(result.nActs,4);
assert.equal(result.nAssessed,3);
assert.equal(result.nInTime,1); // a study late on another gap cannot count as in time
assert.equal(result.nUnknown,1);
assert.equal(result.lvl,"bad");
assert.equal(chainVerdict(si,[{status:"ok",acts:[act("x","unknown")]}]).lvl,"warn");
assert.equal(chainVerdict(si,[]).lvl,"warn");
assert.equal(chainVerdict({},[{status:"ok",acts:[act("x","ontime")]}]).lvl,"warn");
assert.equal(chainVerdict(si,[{status:"ok",acts:[act("x","ontime"),act("x","ontime")]}]).nInTime,1);
'''
        subprocess.run(["node", "-e", code + "\n" + fixture], check=True)


if __name__ == "__main__":
    unittest.main()
