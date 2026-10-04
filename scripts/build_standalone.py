"""Build a single self-contained HTML file (data embedded) for sharing.

  python3 scripts/build_standalone.py

Output: dist/IBD-Evidence-Dashboard.html — one file, no zip, no .js attachment, no Python on the
receiving machine. Email-friendly: Gmail and most filters block .js/.bat (even inside a zip) but allow .html.
Read-only: the Data Editor cannot save (no edit server); everything else works. The world map needs internet.
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DASH = ROOT / "dashboard"
OUT = ROOT / "dist" / "IBD-Evidence-Dashboard.html"
OUT_SIMPLE = ROOT / "dist" / "IBD-Evidence-Dashboard-Simple.html"


def main():
    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_dashboard.py")], check=True)
    html = (DASH / "index.html").read_text()
    data = (DASH / "data.js").read_text()
    # inline the data file and drop the edit-API script (not available in a standalone file)
    # a function replacement keeps backslashes in the data intact (re.sub would treat them as escapes)
    inline = "<script>\n/* dataset embedded by scripts/build_standalone.py */\n" + data.replace("</script", "<\\/script") + "\n</script>"
    html, n = re.subn(r'<script src="data\.js[^"]*"></script>', lambda m: inline, html, count=1)
    if n != 1:
        raise SystemExit("could not find the data.js script tag in dashboard/index.html")
    html = html.replace('<script src="api/overrides.js"></script>', "<!-- edit API not available in the standalone file -->")
    banner = ('<div style="position:fixed;bottom:10px;right:10px;z-index:99;background:var(--surface);border:1px solid var(--line);'
              'border-radius:10px;padding:6px 10px;font-size:calc(11.5px * var(--fs));color:var(--text-3);box-shadow:var(--shadow)">'
              'Standalone copy · read-only · data as of {built}</div>')
    manifest = json.loads((ROOT / 'data/json/_manifest.json').read_text())
    built = manifest.get('snapshot_date', manifest['built'])
    html = html.replace("</body>", banner.format(built=built) + "\n</body>")
    OUT.parent.mkdir(exist_ok=True)
    # the two standalone files link to each other
    OUT.write_text(html.replace("<script>", f'<script>window.IBD_ALT_URL = "{OUT_SIMPLE.name}";</script>\n<script>', 1))
    print(f"{OUT.relative_to(ROOT)}  {OUT.stat().st_size / 1e6:.1f} MB")
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_simple import main as build_simple, simple_html
    build_simple()
    OUT_SIMPLE.write_text(simple_html(html, OUT.name))
    print(f"{OUT_SIMPLE.relative_to(ROOT)}  {OUT_SIMPLE.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
