// Minimal Chrome DevTools Protocol client (Node 22 has a global WebSocket; no npm packages needed).
import { spawn } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";

const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const sleep = ms => new Promise(r => setTimeout(r, ms));

export async function launch({ width = 1600, height = 900, scale = 2, port = 9333 } = {}) {
  const profile = mkdtempSync(path.join(tmpdir(), "ibd-video-"));
  const proc = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, "--hide-scrollbars",
    "--no-first-run", "--no-default-browser-check", "--disable-extensions", `--window-size=${width},${height}`, "about:blank"], { stdio: "ignore" });
  let targets;
  for (let i = 0; i < 50; i++) {
    try { targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); if (targets.some(t => t.type === "page")) break; } catch {}
    await sleep(200);
  }
  const ws = new WebSocket(targets.find(t => t.type === "page").webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let id = 0; const pending = new Map(); const listeners = [];
  ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { const { res, rej } = pending.get(d.id); pending.delete(d.id); d.error ? rej(new Error(d.error.message)) : res(d.result); } else listeners.forEach(f => f(d)); };
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); });
  await send("Page.enable"); await send("Runtime.enable");
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: scale, mobile: false });
  const api = {
    send, sleep,
    async goto(url, wait = 1500) { await send("Page.navigate", { url }); await sleep(wait); },
    async eval(expr) {
      const r = await send("Runtime.evaluate", { expression: `(async () => { ${expr} })()`, awaitPromise: true, returnByValue: true });
      if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
      return r.result.value;
    },
    // full-page screenshot; returns image size in CSS px
    async shot(file, { full = true, quality = 92 } = {}) {
      const m = await send("Page.getLayoutMetrics"); const w = width, h = full ? Math.ceil(m.cssContentSize.height) : height;
      // viewport shots take what is on screen; a clip is in document coordinates and would ignore the scroll position
      const r = await send("Page.captureScreenshot", full ? { format: "jpeg", quality, captureBeyondViewport: true, clip: { x: 0, y: 0, width: w, height: h, scale: 1 } } : { format: "jpeg", quality });
      (await import("node:fs")).writeFileSync(file, Buffer.from(r.data, "base64"));
      return { w, h };
    },
    async close() { try { await send("Browser.close"); } catch {} ws.close(); proc.kill(); },
  };
  return api;
}
