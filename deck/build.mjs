// Renders the deck: standalone HTML (icons inlined), PDF, and one PNG per slide for review.
import { launch } from "./cdp.mjs";
import { writeFileSync, mkdirSync } from "node:fs";
import path from "node:path";
const OUT = path.resolve("../dist");
mkdirSync("png", { recursive: true });
const b = await launch({ port: 9360, width: 1600, height: 900, scale: 1 });
await b.goto("file://" + path.resolve("deck_src.html"), 3500);
await b.eval("await document.fonts.ready; return true");
const missing = await b.eval(`return [...document.querySelectorAll('i[data-lucide]')].map(i => i.dataset.lucide)`);
console.log("icons not rendered:", [...new Set(missing)]);
// standalone HTML: drop the icon library and the builders, keep the rendered DOM and the viewer
const html = await b.eval(`
  const d = document.documentElement.cloneNode(true);
  d.querySelector('#lucide-lib')?.remove(); d.querySelector('#build')?.remove();
  d.querySelectorAll('.slide').forEach(s => { s.style.transform = ''; s.classList.remove('cur'); });
  return '<!doctype html>\\n' + d.outerHTML;`);
writeFileSync(path.join(OUT, "Evidence-Impact-Metrics.html"), html);
// print layout: all slides stacked
await b.eval(`document.body.classList.remove('view'); document.body.classList.add('print'); document.querySelectorAll('.slide').forEach(s => { s.style.transform=''; }); return true`);
await b.sleep(400);
const n = await b.eval(`return document.querySelectorAll('.slide').length`);
for (let i = 0; i < n; i++) {
  const r = await b.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: i * 900, width: 1600, height: 900, scale: 1 } });
  writeFileSync(`png/slide${String(i + 1).padStart(2, "0")}.png`, Buffer.from(r.data, "base64"));
}
const pdf = await b.send("Page.printToPDF", { printBackground: true, preferCSSPageSize: true, paperWidth: 1600 / 96, paperHeight: 900 / 96, marginTop: 0, marginBottom: 0, marginLeft: 0, marginRight: 0 });
writeFileSync(path.join(OUT, "Evidence-Impact-Metrics.pdf"), Buffer.from(pdf.data, "base64"));
console.log("slides:", n);
await b.close();
