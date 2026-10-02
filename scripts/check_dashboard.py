"""Syntax-check the dashboard's inline script before packaging.

  python3 scripts/check_dashboard.py

A broken script leaves the page shell rendering with an empty body, which is easy to miss,
so build_standalone.py runs this first. Needs node; skips with a warning if node is absent.
"""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    html = (ROOT / "dashboard" / "index.html").read_text()
    blocks = re.findall(r"<script>(.*?)</script>", html, re.S)
    if not blocks:
        raise SystemExit("no inline script found in dashboard/index.html")
    node = shutil.which("node")
    if not node:
        print("node not found - skipping the JavaScript syntax check")
        return 0
    bad = 0
    for i, b in enumerate(blocks):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(b)
            tmp = f.name
        r = subprocess.run([node, "--check", tmp], capture_output=True, text=True)
        if r.returncode:
            bad += 1
            print(f"script block {i + 1}/{len(blocks)} has a syntax error:\n{r.stderr.strip()[:800]}")
    if bad:
        raise SystemExit(f"{bad} script block(s) failed the syntax check")
    print(f"dashboard/index.html: {len(blocks)} script block(s) OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
