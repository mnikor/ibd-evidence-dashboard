"""Generate the simplified dashboard (dashboard/simple.html) from dashboard/index.html.

  python3 scripts/build_simple.py

Both versions share the same code and data (data.js); the simplified one only sets window.IBD_SIMPLE = true,
which switches on six sections with tabs, page summaries with folded detail cards, names instead of codes,
Start here + top 3 briefing + top 5 actions, and a Tester view switch for provenance labels.
Run after every change to index.html (build_standalone.py and build_dashboard_data.py call it).
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DASH = ROOT / "dashboard"


def simple_html(html, alt_url="index.html"):
    flag = f'<script>window.IBD_SIMPLE = true; window.IBD_ALT_URL = "{alt_url}";</script>\n'
    html, n = re.subn(r'(<script src="data\.js[^"]*"></script>)', lambda m: flag + m.group(1), html, count=1)
    if n != 1:  # standalone file: data is inline, put the flag before the first script
        html = html.replace("<script>", flag + "<script>", 1)
    return html.replace("<title>IBD Evidence Intelligence</title>", "<title>IBD Evidence Intelligence · Simplified</title>", 1)


def main():
    out = DASH / "simple.html"
    out.write_text(simple_html((DASH / "index.html").read_text()))
    print(f"{out.relative_to(ROOT)} written")


if __name__ == "__main__":
    main()
