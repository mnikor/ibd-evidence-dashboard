// Builds an editable PowerPoint of the deck: node build_pptx.mjs
// The HTML deck is laid out in headless Chrome with Arial (so line breaks match PowerPoint), every box, icon and
// text run is measured, and each becomes a native shape, picture or text box. Gradients are the only rasterised fills.
import { launch } from "./cdp.mjs";
import { createRequire } from "node:module";
import { writeFileSync } from "node:fs";
import path from "node:path";
const require = createRequire(import.meta.url);
const pptxgen = require("pptxgenjs");

const OUT = path.resolve("../dist/Evidence-Impact-Metrics.pptx");
const IN = v => v / 120;            // 1600 px canvas → 13.333 in (LAYOUT_WIDE)
const PT = v => Math.round(v * 0.6 * 10) / 10;   // px → pt on the same canvas

const b = await launch({ port: 9371, width: 1600, height: 900, scale: 1 });
await b.goto("file://" + path.resolve("deck_src.html"), 3500);
await b.eval(`await document.fonts.ready;
  document.body.classList.remove('view'); document.body.classList.add('print');
  document.querySelectorAll('.slide').forEach(s => s.style.transform = '');
  const st = document.createElement('style');
  st.textContent = '*{font-family:Arial,sans-serif!important} .chev li::before{display:none!important}';
  document.head.appendChild(st); document.querySelector('.hint')?.remove();
  // pseudo-element bullets become real elements so they can be measured
  document.querySelectorAll('.chev li').forEach(li => { const d = document.createElement('span');
    d.style.cssText = 'width:6px;height:6px;border-radius:50%;background:#fff;flex:none;transform:translateY(-2px)'; li.prepend(d); });
  return true`);
await b.sleep(600);

const slides = await b.eval(String.raw`
  const col = c => { const m = c && c.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(/[\s,\/]+/).filter(Boolean).map(Number); const a = p.length > 3 ? p[3] : 1; if (a === 0) return null;
    return { hex: p.slice(0, 3).map(v => Math.round(v).toString(16).padStart(2, '0')).join('').toUpperCase(), a }; };
  const opacityOf = el => { let o = 1; for (let e = el; e && !e.classList?.contains('slide'); e = e.parentElement) o *= parseFloat(getComputedStyle(e).opacity); return o; };
  const inlineDisp = d => d === 'inline' || d === 'contents';
  const evalLen = (s, dim) => { s = s.trim(); const m = s.match(/^calc\((.*)\)$/); if (m) s = m[1]; let t = 0, sg = 1;
    for (const k of s.split(/\s+/)) { if (k === '-') { sg = -1; continue; } if (k === '+') { sg = 1; continue; }
      t += sg * (k.endsWith('%') ? parseFloat(k) / 100 * dim : parseFloat(k)); sg = 1; } return t; };
  let gid = 0;
  const out = [];
  for (const slide of document.querySelectorAll('.slide')) {
    const S = slide.getBoundingClientRect(); const items = [];
    const R = r => ({ x: r.left - S.left, y: r.top - S.top, w: r.width, h: r.height });
    const runsOf = (el, acc) => { for (const n of el.childNodes) {
      if (n.nodeType === 3) { if (n.textContent.trim() || acc.length) acc.push(n); }
      else if (n.nodeType === 1 && n.tagName.toLowerCase() !== 'svg' && inlineDisp(getComputedStyle(n).display)) runsOf(n, acc); } return acc; };
    const visit = el => {
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') return;
      const r = el.getBoundingClientRect(); const op = opacityOf(el);
      if (el.tagName.toLowerCase() === 'svg') { items.push({ t: 'icon', ...R(r), color: col(cs.color).hex, svg: el.outerHTML, op }); return; }
      if (el !== slide) {
        const bg = col(cs.backgroundColor), bw = parseFloat(cs.borderTopWidth), bc = bw > 0 && cs.borderTopStyle !== 'none' ? col(cs.borderTopColor) : null;
        const rad = [cs.borderTopLeftRadius, cs.borderTopRightRadius, cs.borderBottomRightRadius, cs.borderBottomLeftRadius]
          .map(v => v.endsWith('%') ? parseFloat(v) / 100 * Math.min(r.width, r.height) : parseFloat(v) || 0);
        const radius = rad.every(v => Math.abs(v - rad[0]) < .5) ? Math.min(rad[0], Math.min(r.width, r.height) / 2) : 0;
        const ring = cs.boxShadow.match(/(rgba?\([^)]+\)) 0px 0px 0px ([\d.]+)px/);
        if (ring && bg) { const s = parseFloat(ring[2]);
          items.push({ t: 'shape', x: r.left - S.left - s, y: r.top - S.top - s, w: r.width + 2 * s, h: r.height + 2 * s, radius: radius + s, fill: col(ring[1]), op }); }
        const clip = cs.clipPath.match(/^polygon\((.*)\)$/);
        if (cs.backgroundImage.includes('gradient')) { el.dataset.grad = ++gid; items.push({ t: 'grad', id: gid, ...R(r), radius }); }
        else if (clip && bg) items.push({ t: 'poly', ...R(r), fill: bg, op, pts: clip[1].split(',').map(p => { const [a, c] = p.trim().split(/\s+(?![^(]*\))/); return [evalLen(a, r.width), evalLen(c, r.height)]; }) });
        else if (bg || bc) items.push({ t: 'shape', ...R(r), radius, fill: bg, line: bc ? { ...bc, w: bw, dash: cs.borderTopStyle === 'dashed' } : null, op });
        const af = getComputedStyle(el, '::after');
        if (af.content !== 'none' && parseFloat(af.borderLeftWidth) > 0) {   // CSS triangle (arrow head on the lead→lag bar)
          const w = parseFloat(af.borderLeftWidth), h = parseFloat(af.borderTopWidth) + parseFloat(af.borderBottomWidth);
          items.push({ t: 'tri', x: r.right - S.left - w - parseFloat(af.right), y: r.top - S.top + parseFloat(af.top), w, h, fill: col(af.borderLeftColor) });
        }
      }
      for (const c of el.children) visit(c);
      if (inlineDisp(cs.display)) return;
      // text directly owned by this block (its inline descendants), measured line by line
      const nodes = runsOf(el, []); if (!nodes.some(n => n.textContent.trim())) return;
      const m = new DOMMatrix(cs.transform === 'none' ? undefined : cs.transform); const rot = Math.round(Math.atan2(m.b, m.a) * 180 / Math.PI);
      // words in reading order with the line the browser put them on; PowerPoint gets the same breaks explicitly
      const toks = [], rects = [], rg = document.createRange();
      const rectOf = (n, a, z) => { rg.setStart(n, a); rg.setEnd(n, z); return [...rg.getClientRects()].filter(q => q.width > 0); };
      let line = 0, curTop = null, prevTailWs = false;
      nodes.forEach((n, ni) => { const tx = n.textContent; let last = 0;
        for (const wm of tx.matchAll(/\S+/g)) {
          const sep = wm.index > last ? /\s/.test(tx.slice(last, wm.index)) : (wm.index === 0 && prevTailWs);
          let pieces = [[wm.index, wm.index + wm[0].length]];
          let rs = rectOf(n, ...pieces[0]);
          if (!rot && rs.length > 1) {        // word broken across lines (e.g. after a hyphen): split where the line changes
            const t0 = rs[0].top, h0 = rs[0].height; let k = pieces[0][0] + 1;
            while (k < pieces[0][1] && rectOf(n, k, k + 1)[0]?.top <= t0 + h0 / 2) k++;
            pieces = [[pieces[0][0], k], [k, pieces[0][1]]];
          }
          pieces.forEach(([a, z], pi) => { const q = rectOf(n, a, z)[0]; if (!q) return; rects.push(q);
            let nl = false;
            if (!rot) { if (curTop === null) curTop = q.top; else if (q.top > curTop + q.height / 2) { line++; curTop = q.top; nl = true; } }
            toks.push({ ni, text: tx.slice(a, z), sep: pi === 0 && sep && toks.length > 0, nl }); });
          last = wm.index + wm[0].length; }
        if (tx.slice(last).match(/\s/) || (!tx.trim() && tx.length)) prevTailWs = true; else if (tx.trim()) prevTailWs = false;
      });
      if (!toks.length) return;
      const runs = nodes.map(n => { const pcs = getComputedStyle(n.parentElement);
        return { text: '', upper: pcs.textTransform === 'uppercase', size: parseFloat(pcs.fontSize), bold: parseInt(pcs.fontWeight) >= 600, italic: pcs.fontStyle === 'italic',
          color: col(pcs.color).hex, ls: parseFloat(pcs.letterSpacing) || 0, op: opacityOf(n.parentElement) }; });
      for (const t of toks) runs[t.ni].text += (t.nl ? '\n' : t.sep ? ' ' : '') + (runs[t.ni].upper ? t.text.toUpperCase() : t.text);
      const u = { l: Math.min(...rects.map(q => q.left)), t: Math.min(...rects.map(q => q.top)), r: Math.max(...rects.map(q => q.right)), b: Math.max(...rects.map(q => q.bottom)) };
      const lines = line + 1;
      const pl = parseFloat(cs.paddingLeft) + parseFloat(cs.borderLeftWidth), pr = parseFloat(cs.paddingRight) + parseFloat(cs.borderRightWidth);
      const lh = cs.lineHeight === 'normal' ? null : parseFloat(cs.lineHeight);
      const ta = cs.textAlign === 'center' ? 'center' : (cs.textAlign === 'right' || cs.textAlign === 'end') ? 'right' : 'left';
      items.push({ t: 'text', x: u.l - S.left, y: u.t - S.top, w: u.r - u.l, h: u.b - u.t, cx: r.left - S.left + pl, cw: r.width - pl - pr,
        lines, lh, align: ta, rot, runs });
    };
    visit(slide);
    out.push(items);
  }
  return out;`);

// icons → PNG (drawn in the page so stroke colours and geometry are exact)
const iconPng = await b.eval(String.raw`
  const svgs = [...document.querySelectorAll('.slide svg')]; const out = [];
  for (const s of svgs) { const c = s.cloneNode(true); const color = getComputedStyle(s).color;
    c.setAttribute('xmlns', 'http://www.w3.org/2000/svg'); c.setAttribute('width', 256); c.setAttribute('height', 256); c.removeAttribute('class'); c.removeAttribute('style');
    const src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(c.outerHTML.replaceAll('currentColor', color));
    const img = new Image(); await new Promise((res, rej) => { img.onload = res; img.onerror = rej; img.src = src; });
    const cv = document.createElement('canvas'); cv.width = cv.height = 256; cv.getContext('2d').drawImage(img, 0, 0, 256, 256);
    out.push(cv.toDataURL('image/png')); }
  return out;`);

// gradient fills → images (children hidden while capturing)
const grads = {};
const gcount = await b.eval(`return document.querySelectorAll('[data-grad]').length`);
for (let g = 1; g <= gcount; g++) {
  const box = await b.eval(`const e = document.querySelector('[data-grad="${g}"]'); [...e.children].forEach(c => c.style.visibility = 'hidden');
    const r = e.getBoundingClientRect(); return { x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height };`);
  await b.sleep(80);
  const shot = await b.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: box.x, y: box.y, width: box.w, height: box.h, scale: 2 } });
  grads[g] = "image/png;base64," + shot.data;
  await b.eval(`[...document.querySelector('[data-grad="${g}"]').children].forEach(c => c.style.visibility = ''); return 1`);
}
// reference render of the Arial layout, for side-by-side QA
const { mkdirSync } = await import("node:fs"); mkdirSync("png_arial", { recursive: true });
for (let i = 0; i < slides.length; i++) {
  const r = await b.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: i * 900, width: 1600, height: 900, scale: 1 } });
  writeFileSync(`png_arial/slide${String(i + 1).padStart(2, "0")}.png`, Buffer.from(r.data, "base64"));
}
await b.close();

// ------------------------------------------------------------------ PowerPoint
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.title = "Evidence Impact Metrics"; pres.subject = "Metrics framework for evidence generation and dissemination · proposal for discussion";
let icon = 0;
const tr = op => op < .995 ? Math.round((1 - op) * 100) : 0;
for (const items of slides) {
  const s = pres.addSlide(); s.background = { color: "FFFFFF" };
  for (const it of items) {
    if (it.t === "shape") {
      const inset = it.line ? it.line.w / 2 : 0;   // CSS borders sit inside the box, PowerPoint strokes are centred on it
      const x = it.x + inset, y = it.y + inset, w = it.w - 2 * inset, h = it.h - 2 * inset, rr = Math.max(0, it.radius - inset);
      const circle = rr >= Math.min(w, h) / 2 - .5 && Math.abs(w - h) < 1;
      const o = { x: IN(x), y: IN(y), w: IN(w), h: IN(h),
        fill: it.fill ? { color: it.fill.hex, transparency: tr(it.fill.a * it.op) } : { type: "none" },
        line: it.line ? { color: it.line.hex, width: PT(it.line.w), transparency: tr(it.line.a * it.op), dashType: it.line.dash ? "dash" : "solid" } : { type: "none" } };
      if (circle) s.addShape(pres.shapes.OVAL, o);
      else if (rr > .5) s.addShape(pres.shapes.ROUNDED_RECTANGLE, { ...o, rectRadius: IN(rr) });
      else s.addShape(pres.shapes.RECTANGLE, o);
    } else if (it.t === "poly") {
      s.addShape(pres.shapes.CUSTOM_GEOMETRY, { x: IN(it.x), y: IN(it.y), w: IN(it.w), h: IN(it.h), fill: { color: it.fill.hex }, line: { type: "none" },
        points: [...it.pts.map(([px, py]) => ({ x: IN(px), y: IN(py) })), { close: true }] });
    } else if (it.t === "tri") {   // right-pointing arrow head
      s.addShape(pres.shapes.CUSTOM_GEOMETRY, { x: IN(it.x), y: IN(it.y), w: IN(it.w), h: IN(it.h), fill: { color: it.fill.hex }, line: { type: "none" },
        points: [{ x: 0, y: 0 }, { x: IN(it.w), y: IN(it.h / 2) }, { x: 0, y: IN(it.h) }, { close: true }] });
    } else if (it.t === "grad") {
      s.addImage({ data: grads[it.id], x: IN(it.x), y: IN(it.y), w: IN(it.w), h: IN(it.h) });
    } else if (it.t === "icon") {
      s.addImage({ data: iconPng[icon++].replace(/^data:/, ""), x: IN(it.x), y: IN(it.y), w: IN(it.w), h: IN(it.h) });
    } else if (it.t === "text") {
      const maxSize = Math.max(...it.runs.map(r => r.size));
      const single = it.lines <= 1;
      // line breaks are explicit, so boxes get room to spare and never re-wrap
      let w = it.w * 1.06 + 8, x = it.align === "center" ? it.x - (w - it.w) / 2 : it.align === "right" ? it.x - (w - it.w) : it.x;
      let y = it.y, h = it.h;
      if (it.rot) { const cx = it.x + it.w / 2, cy = y + h / 2; [w, h] = [it.h * 1.06 + 8, it.w]; x = cx - w / 2; y = cy - h / 2; }
      const runs = [];
      for (const r of it.runs.filter(r => r.text)) {
        const o = { fontFace: "Arial", fontSize: PT(r.size), bold: r.bold, italic: r.italic, color: r.color, charSpacing: r.ls ? PT(r.ls) : undefined, transparency: tr(r.op) || undefined };
        r.text.split("\n").forEach((part, k, all) => { if (part) runs.push({ text: part, options: { ...o } });
          if (k < all.length - 1) { if (runs.length) runs[runs.length - 1].options.breakLine = true; } });
      }
      const opt = { x: IN(x), y: IN(y), w: IN(w), h: IN(Math.max(h, maxSize * 1.15)), margin: 0, valign: "top", align: it.align,
        isTextBox: true, fit: "none", wrap: false, rotate: it.rot ? (it.rot + 360) % 360 : undefined, paraSpaceBefore: 0, paraSpaceAfter: 0 };
      if (!single && it.lh) opt.lineSpacing = PT(it.lh);   // exact spacing: a fallback glyph (e.g. ★) must not stretch the line
      s.addText(runs, opt);
    }
  }
}
await pres.writeFile({ fileName: OUT });
console.log("wrote", OUT, "slides", slides.length, "icons", icon, "gradients", gcount);
