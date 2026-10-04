r"""Local dashboard server with a data-edit API.

  python3 scripts/serve.py [port]        macOS / Linux   (default 8765, this machine only)
  py -3 scripts\serve.py [port]         Windows         (or double-click start-dashboard.bat)
  ... --host 0.0.0.0                    also serve to other machines on the same network (no login!)

Static files are served from dashboard/. Manual edits are stored in data/overrides/overrides.json as an
append-only log of operations; scripts/build_dataset.py re-applies them on every rebuild and tags the
edited values with provenance "manual".

API
  GET  /api/overrides.js         window.IBD_OVR = [...active operations...]   (loaded by the dashboard)
  GET  /api/overrides            full log as JSON (including reverted operations)
  POST /api/overrides            {"ops": [...]} append operations (set | add | delete)
  POST /api/overrides/revert     {"id": "..."} mark an operation as reverted
  POST /api/rebuild              re-run build_dataset.py + build_dashboard_data.py
  GET  /api/chat/status          {"enabled": true|false, "model": ...} for the dashboard assistant
  POST /api/chat                 forwards {system, messages, tools} to Claude (Anthropic Messages API)

The assistant uses Claude only when the environment variable ANTHROPIC_API_KEY is set (optionally ANTHROPIC_MODEL);
without it the dashboard answers from built-in rules. The key stays on the server and is never sent to the browser.
"""
import datetime as dt
import json
import urllib.error
import urllib.request
import os
import pathlib
import subprocess
import sys
import threading
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parent.parent
DASH = ROOT / "dashboard"
OVR = ROOT / "data" / "overrides" / "overrides.json"
LOCK = threading.Lock()
_VENV = [ROOT / ".venv" / "bin" / "python", ROOT / ".venv" / "Scripts" / "python.exe"]  # POSIX / Windows
PY = next((str(v) for v in _VENV if v.exists()), sys.executable)
VALID_OPS = {"set", "add", "delete"}


def load_log():
    if not OVR.exists():
        return []
    try:
        return json.loads(OVR.read_text())
    except json.JSONDecodeError:
        return []


def save_log(log):
    OVR.parent.mkdir(parents=True, exist_ok=True)
    tmp = OVR.with_suffix(".tmp")
    tmp.write_text(json.dumps(log, indent=1, ensure_ascii=False))
    tmp.replace(OVR)  # atomic replace (POSIX and Windows)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(DASH), **kw)

    def log_message(self, fmt, *args):  # quieter console
        if "/api/" in str(args[0] if args else ""):
            super().log_message(fmt, *args)

    def end_headers(self):
        if self.path.startswith(("/api/", "/data.js")) or self.path.split("?")[0] in ("/", "/index.html", "/simple.html"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json(self, code, obj, ctype="application/json"):
        body = (obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False)).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        if self.path.split("?")[0] == "/api/overrides.js":
            active = [o for o in load_log() if not o.get("reverted")]
            return self._json(200, "window.IBD_OVR=" + json.dumps(active, ensure_ascii=False) + ";", "application/javascript")
        if self.path.split("?")[0] == "/api/overrides":
            return self._json(200, load_log())
        if self.path.split("?")[0] == "/api/chat/status":
            return self._json(200, {"enabled": bool(os.environ.get("ANTHROPIC_API_KEY")), "model": CHAT_MODEL})
        if self.path.split("?")[0] == "/download/dataset.xlsx":
            f = ROOT / "data" / "IBD_Evidence_Dataset.xlsx"
            data = f.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            self.send_header("Content-Disposition", 'attachment; filename="IBD_Evidence_Dataset.xlsx"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        return super().do_GET()

    def do_POST(self):
        path = self.path.split("?")[0]
        try:
            body = self._body()
        except json.JSONDecodeError:
            return self._json(400, {"error": "invalid JSON"})
        if path == "/api/overrides":
            ops = body.get("ops") or []
            clean = []
            for o in ops:
                if o.get("op") not in VALID_OPS or not o.get("table") or not (o.get("key") or o.get("op") == "add"):
                    return self._json(400, {"error": f"invalid operation: {o}"})
                if o["op"] == "set" and not o.get("field"):
                    return self._json(400, {"error": "set needs a field"})
                clean.append({
                    "id": uuid.uuid4().hex[:12], "ts": dt.datetime.now().isoformat(timespec="seconds"),
                    "editor": str(o.get("editor") or "unknown")[:80], "note": str(o.get("note") or "")[:500],
                    "op": o["op"], "table": o["table"], "key": o.get("key") or (o.get("row") or {}).get("_key"),
                    "field": o.get("field"), "old": o.get("old"), "new": o.get("new"), "row": o.get("row"),
                })
            with LOCK:
                log = load_log()
                log.extend(clean)
                save_log(log)
            return self._json(200, {"saved": len(clean), "ids": [c["id"] for c in clean]})
        if path == "/api/overrides/revert":
            with LOCK:
                log = load_log()
                hit = False
                for o in log:
                    if o["id"] == body.get("id") and not o.get("reverted"):
                        o["reverted"] = dt.datetime.now().isoformat(timespec="seconds")
                        hit = True
                save_log(log)
            return self._json(200 if hit else 404, {"reverted": hit})
        if path == "/api/rebuild":
            out = []
            for script in ("scripts/build_dataset.py", "scripts/build_dashboard_data.py"):
                r = subprocess.run([PY, script], cwd=ROOT, capture_output=True, text=True, timeout=600)
                out.append(f"$ {script}\n{r.stdout[-1500:]}{r.stderr[-1500:]}")
                if r.returncode:
                    return self._json(500, {"ok": False, "log": "\n".join(out)})
            return self._json(200, {"ok": True, "log": "\n".join(out)})
        if path == "/api/chat":
            if not os.environ.get("ANTHROPIC_API_KEY"):
                return self._json(503, {"error": "The assistant has no API key on this server (set ANTHROPIC_API_KEY)."})
            code, out = chat(body)
            return self._json(code, out)
        return self._json(404, {"error": "unknown endpoint"})


CHAT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
CHAT_URL = "https://api.anthropic.com/v1/messages"


def chat(body):
    """Forward one assistant turn to Claude. Tools are executed in the browser, on the dashboard's own data."""
    payload = {"model": CHAT_MODEL, "max_tokens": min(int(body.get("max_tokens") or 1500), 4000),
               "system": str(body.get("system") or "")[:20000], "messages": body.get("messages") or [], "tools": body.get("tools") or []}
    req = urllib.request.Request(CHAT_URL, data=json.dumps(payload).encode(), method="POST", headers={
        "content-type": "application/json", "anthropic-version": "2023-06-01", "x-api-key": os.environ["ANTHROPIC_API_KEY"]})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return 200, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read()).get("error", {}).get("message", "")
        except Exception:
            detail = ""
        return e.code, {"error": f"Claude API returned {e.code}. {detail}".strip()}
    except Exception as e:
        return 502, {"error": f"Could not reach the Claude API: {type(e).__name__}"}


def local_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # no packets sent; just picks the outbound interface
        return s.getsockname()[0]
    finally:
        s.close()


def ensure_data_js():
    """Bundles sent by email omit dashboard/data.js (mail filters block .js); rebuild it from data/json."""
    if (DASH / "data.js").exists():
        return
    print("dashboard/data.js is missing - generating it from data/json ...")
    r = subprocess.run([PY, "scripts/build_dashboard_data.py"], cwd=ROOT, capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip()[-500:])
    if not (DASH / "data.js").exists():
        print("Could not generate it. Check that the data/json folder is present.")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Serve the IBD dashboard with the data-edit API.")
    ap.add_argument("port", nargs="?", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1",
                    help="127.0.0.1 (default, this machine only) or 0.0.0.0 to share with other machines on your network")
    a = ap.parse_args()
    ensure_data_js()
    print(f"IBD dashboard + edit API → http://127.0.0.1:{a.port}   (edits saved to {OVR.relative_to(ROOT)})")
    if a.host != "127.0.0.1":
        try:
            print(f"Other machines on this network: http://{local_ip()}:{a.port}")
        except Exception:
            pass
        print("WARNING: no login. Anyone who can reach this port can read the dashboard AND edit the data.\n"
              "         Use it only on a trusted network, and stop the server (Ctrl+C) when you are done.")
    print("Press Ctrl+C to stop.")
    try:
        ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
