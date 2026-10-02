"""Package the dashboard for another machine.

  python3 scripts/package.py viewer   dashboard only: open index.html, no Python needed (read-only)
  python3 scripts/package.py editor   dashboard + data + scripts: view, edit and rebuild (needs Python 3)
  python3 scripts/package.py full     everything including raw source data for refreshes
  python3 scripts/package.py email    editor bundle that passes mail filters (no .js / .bat inside)
  python3 scripts/build_standalone.py single HTML file to attach directly to an email (read-only)
Zips are written to dist/.
"""
import pathlib
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
SETS = {
    "viewer": ["dashboard/index.html", "dashboard/simple.html", "dashboard/data.js"],
    "editor": ["dashboard/index.html", "dashboard/simple.html", "dashboard/data.js", "start-dashboard.bat", "start-dashboard.command", "scripts/serve.py", "scripts/build_dataset.py", "scripts/build_dashboard_data.py",
               "scripts/build_publications.py", "scripts/fetch_ctgov.py", "scripts/fetch_publications.py", "scripts/curated_public.py",
               "scripts/package.py", "data/README.md", "DATA_SPEC.md", "data/IBD_Evidence_Dataset.xlsx", "data/overrides/overrides.json", "data/json"],
    "email": ["dashboard/index.html", "scripts/serve.py", "scripts/build_dataset.py", "scripts/build_dashboard_data.py",
              "scripts/build_publications.py", "scripts/build_standalone.py", "scripts/curated_public.py", "scripts/package.py",
              "data/README.md", "DATA_SPEC.md", "data/IBD_Evidence_Dataset.xlsx", "data/overrides/overrides.json", "data/json"],
    "full": ["dashboard/index.html", "dashboard/simple.html", "dashboard/data.js", "start-dashboard.bat", "start-dashboard.command", "scripts", "data", "DATA_SPEC.md"],
}
EMAIL_README = """IBD Evidence Intelligence - editor bundle (email-safe)

This zip deliberately contains no .js or .bat files, because mail systems block them.
Needs Python 3 (Windows: install from https://www.python.org/downloads/windows/, tick "Add python.exe to PATH").

WINDOWS
1. Right-click the zip > Extract All.
2. Rename  start-dashboard.bat.txt  to  start-dashboard.bat   (View > File name extensions must be ticked)
   ... or skip the rename and run this in a terminal opened in the folder:   py -3 scripts\\serve.py
3. Open http://127.0.0.1:8765

macOS / Linux
   python3 scripts/serve.py      then open http://127.0.0.1:8765

On first start the server regenerates dashboard/data.js from data/json automatically (takes a few seconds).
Edits are saved to data/overrides/overrides.json and survive rebuilds.
Excel rebuilds also need:   py -3 -m pip install --user openpyxl
"""

READMES = {
    "viewer": """IBD Evidence Intelligence - viewer bundle (no Python needed)
1. Unzip anywhere - keep index.html and data.js together in the same folder
   (on Windows: right-click the zip > Extract All; opening it from inside the zip will not work).
2. Double-click index.html (or right-click > Open With > your browser).
Read-only: the Data Editor cannot save, and the world map needs an internet connection.
For editing, ask for the 'editor' bundle.
""",
    "editor": """IBD Evidence Intelligence - editor bundle
Needs Python 3.
WINDOWS
1. Right-click the zip > Extract All (do not run it from inside the zip).
2. Double-click start-dashboard.bat. A browser opens at http://127.0.0.1:8765
   No Python? Install from https://www.python.org/downloads/windows/ and tick "Add python.exe to PATH".
   Keep the black window open while you use the dashboard.
macOS / Linux
1. Unzip anywhere.
2. Double-click start-dashboard.command, or run:  python3 scripts/serve.py
3. Open http://127.0.0.1:8765
Edits are saved to data/overrides/overrides.json and survive rebuilds.
"Rebuild dataset" in the Data Editor recalculates derived values; to rebuild the Excel file too:
   Windows:      py -3 -m pip install --user openpyxl
   macOS/Linux:  python3 -m pip install --user openpyxl
To let others on your network open it (no login - trusted networks only):
   python3 scripts/serve.py --host 0.0.0.0
""",
    "full": """IBD Evidence Intelligence - full bundle (includes raw source data)
Needs Python 3.   Start: double-click start-dashboard.bat (Windows) / start-dashboard.command (macOS),
or run:  python3 scripts/serve.py     then open http://127.0.0.1:8765
Refresh from source (internet required; use "py -3" instead of "python3" on Windows):
   python3 scripts/fetch_ctgov.py          # trial registry
   python3 scripts/fetch_publications.py --force && python3 scripts/build_publications.py
   python3 scripts/build_dataset.py && python3 scripts/build_dashboard_data.py
Excel export needs:  python3 -m pip install --user openpyxl
""",
}


def files_for(kind):
    if kind == "email":
        SETS["email"] = SETS["email"]
    out = []
    for item in SETS[kind]:
        p = ROOT / item
        if p.is_dir():
            out += [f for f in sorted(p.rglob("*")) if f.is_file() and ".venv" not in f.parts and not f.name.startswith(".")]
        elif p.exists():
            out.append(p)
        else:
            print(f"  (skipped, not found: {item})")
    return out


def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else "editor"
    if kind not in SETS:
        sys.exit(f"Usage: python3 scripts/package.py [{'|'.join(SETS)}]")
    DIST.mkdir(exist_ok=True)
    out = DIST / f"ibd-dashboard-{kind}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for f in files_for(kind):
            z.write(f, pathlib.Path("ibd-dashboard") / f.relative_to(ROOT))
        if kind == "email":
            z.writestr("ibd-dashboard/start-dashboard.bat.txt", (ROOT / "start-dashboard.bat").read_text())
            z.writestr("ibd-dashboard/START-HERE.txt", EMAIL_README)
        else:
            z.writestr("ibd-dashboard/START-HERE.txt", READMES[kind])
    print(f"{out.relative_to(ROOT)}  {out.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
