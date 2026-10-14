/* Cadence web app: Home, Practice (mic permission → record → analyze), Report, Live demo, Evidence. */
"use strict";

const $ = (sel, el = document) => el.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtTime = (s) => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, "0")}`;
const main = $("#main");

const ICON = {
  mic: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3M9 21h6"/></svg>',
  micOff: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 3l18 18M9 9v2a3 3 0 0 0 5.1 2.1M15 9.3V6a3 3 0 0 0-5.7-1.3M19 11a7 7 0 0 1-1 3.6M5 11a7 7 0 0 0 10.6 6M12 18v3"/></svg>',
  check: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12l4 4 10-10"/></svg>',
  play: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><polygon points="6 4 20 12 6 20"/></svg>',
  arrow: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
  info: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>',
  clock: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2M9 2h6"/></svg>',
  book: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2zM4 19V5"/></svg>',
  alert: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l9 16H3z"/><path d="M12 10v4M12 17h.01"/></svg>',
  upload: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 21V9M7 14l5-5 5 5M4 3h16"/></svg>',
  download: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 3v12M7 10l5 5 5-5M4 21h16"/></svg>',
};

/* ---------- storage (this browser only) ---------- */
const store = {
  get(k, d) { try { const v = localStorage.getItem("cadence." + k); return v ? JSON.parse(v) : d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem("cadence." + k, JSON.stringify(v)); } catch { /* storage unavailable */ } },
};
const sessions = () => store.get("sessions", []);
function saveSession(s) {
  const all = sessions().filter((x) => x.id !== s.id);
  all.unshift(s);
  while (all.length) {
    try { localStorage.setItem("cadence.sessions", JSON.stringify(all)); break; } catch { all.pop(); }
  }
}
const settings = () => store.get("settings", { name: "", method: "envelope" });

function toast(msg) {
  const t = $("#toast");
  t.textContent = msg; t.hidden = false;
  clearTimeout(toast._t); toast._t = setTimeout(() => (t.hidden = true), 5000);
}

/* ---------- data ---------- */
let TEXTS = [];
async function loadTexts() {
  if (TEXTS.length) return TEXTS;
  const r = await fetch("/api/texts");
  TEXTS = await r.json();
  return TEXTS;
}
const textById = (id) => TEXTS.find((t) => t.id === id);

/* ---------- report maths ---------- */
const DIMS = [
  ["pacing", "Pacing", ["pace"]], ["pausing", "Pausing", ["missing_pause"]], ["pitch_variety", "Pitch variety", ["monotone"]],
  ["emphasis", "Emphasis", ["missed_emphasis"]], ["volume", "Volume", ["volume_fade"]], ["fluency", "Fluency", ["misplaced_pause"]],
];
const LANES = { rate: ["Rate", "syllables per second"], pause: ["Pauses", "seconds"], pitch_range: ["Pitch range", "semitones"], loud: ["Loudness", "dB re your median"] };

function wordStatus(rep) {
  const n = rep.words.length, st = new Array(n).fill("i");
  for (const f of Object.keys(rep.lanes)) {
    const l = rep.lanes[f];
    for (let i = 0; i < n; i++) {
      const v = l.value[i], lo = l.lo[i], hi = l.hi[i];
      if (v == null || lo == null || hi == null) continue;
      if (v < lo - 1e-9 || v > hi + 1e-9) st[i] = "b";
    }
  }
  for (const r of rep.regions) for (let i = r.w0; i <= r.w1 && i < n; i++) st[i] = "f";
  return st;
}
function summary(rep) {
  const st = wordStatus(rep);
  const c = { i: 0, b: 0, f: 0 };
  st.forEach((s) => c[s]++);
  return { st, inRange: c.i, border: c.b, flagged: c.f, pct: Math.round((100 * c.i) / Math.max(1, st.length)) };
}
function ringHTML(st, pct, small) {
  const box = small ? 200 : 240, R = small ? 84 : 100, n = st.length;
  let dots = "";
  for (let i = 0; i < n; i++) {
    const a = -Math.PI / 2 + (2 * Math.PI * i) / n, c = st[i];
    const size = c === "f" ? (small ? 7 : 8) : c === "b" ? (small ? 6 : 7) : i % 3 === 0 ? (small ? 5 : 6) : 4;
    const col = c === "f" ? "var(--bad)" : c === "b" ? "var(--warn)" : i % 3 === 0 ? "var(--ok)" : "var(--ok-soft)";
    const r = R + (i % 2 ? (small ? 5 : 6) : 0);
    const x = box / 2 + r * Math.cos(a) - size / 2, y = box / 2 + r * Math.sin(a) - size / 2;
    dots += `<span class="d" style="left:${x.toFixed(1)}px;top:${y.toFixed(1)}px;width:${size}px;height:${size}px;background:${col}"></span>`;
  }
  return `<div class="ring${small ? " small" : ""}" role="img" aria-label="${n} words in reading order, clockwise from the top">${dots}
    <div class="center"><span class="num">${pct}</span><span class="of">/100 in range</span></div></div>`;
}
const wordsText = (rep, r, max = 6) => {
  const ws = rep.words.slice(r.w0, r.w1 + 1).map((w) => w.word);
  return ws.length > max ? ws.slice(0, max).join(" ") + "…" : ws.join(" ");
};
function headline(rep, r) {
  const w = wordsText(rep, r), w0 = rep.words[r.w0]?.word ?? "";
  const nxt = rep.words[Math.min(r.w0 + 1, rep.words.length - 1)]?.word ?? "";
  switch (r.type) {
    case "pace": return r.side > 0 ? `You rushed “${w}”.` : `You dragged “${w}”.`;
    case "missing_pause": return `You didn’t pause after “${w0}”.`;
    case "misplaced_pause": return `You paused inside “${w0} ${nxt}”.`;
    case "monotone": return `Your pitch went flat on “${w}”.`;
    case "missed_emphasis": return `You didn’t stress “${w0}”.`;
    case "volume_fade": return `Your volume faded on “${w}”.`;
    default: return `Check “${w}”.`;
  }
}
const ISSUE = { pace: (r) => (r.side > 0 ? "Rushed pace" : "Dragging pace"), missing_pause: () => "Missing pause", misplaced_pause: () => "Pause in the wrong place", monotone: () => "Monotone", missed_emphasis: () => "Missed emphasis", volume_fade: () => "Volume fade" };
function explainParts(r) {
  const body = (r.explanation || "").split("): ").slice(1).join("): ") || r.explanation || "";
  const sentences = body.split(/(?<=\.)\s+/);
  const tip = sentences.length > 1 ? sentences.pop() : "";
  let what = sentences.join(" ");
  what = what.charAt(0).toUpperCase() + what.slice(1);
  return { what, tip };
}
const topRegion = (rep) => rep.regions.slice().sort((a, b) => (b.severity ?? b.d_mean) - (a.severity ?? a.d_mean))[0];

function dimsHTML(rep, grid) {
  return `<div class="dims${grid ? " grid" : ""}">` + DIMS.map(([key, label, types]) => {
    const n = rep.regions.filter((r) => types.includes(r.type)).length;
    const score = rep.scores[key];
    const extra = key === "emphasis" && !n ? `${rep.stress_points.length} stress point${rep.stress_points.length === 1 ? "" : "s"} checked` : n ? `${n} region${n > 1 ? "s" : ""} out of range` : "In range";
    return `<div class="dim${n ? " bad" : ""}"><div class="t"><span>${label}</span><span>${Number.isInteger(score) ? score : score.toFixed(1)}</span></div>
      <div class="s"><span class="sw ${n ? "bad" : "ok"}"></span>${extra}</div></div>`;
  }).join("") + "</div>";
}

function chartHTML(rep, lane, whole) {
  const L = rep.lanes[lane], W = rep.words, n = W.length;
  const top = topRegion(rep);
  let a = 0, b = n - 1;
  if (!whole && top) { a = Math.max(0, top.w0 - 22); b = Math.min(n - 1, top.w1 + 22); }
  const idx = [];
  for (let i = a; i <= b; i++) if (L.value[i] != null && L.lo[i] != null && L.hi[i] != null) idx.push(i);
  if (idx.length < 2) return `<p class="meta">Not enough measured words in this range for this feature.</p>`;
  const t0 = W[a].start, t1 = W[b].end;
  let ymin = Infinity, ymax = -Infinity;
  for (const i of idx) { ymin = Math.min(ymin, L.lo[i], L.value[i]); ymax = Math.max(ymax, L.hi[i], L.value[i]); }
  const pad = (ymax - ymin) * 0.12 || 1; ymin -= pad; ymax += pad;
  const X = (t) => (((t - t0) / (t1 - t0)) * 1000).toFixed(1);
  const Y = (v) => (240 - ((v - ymin) / (ymax - ymin)) * 240).toFixed(1);
  const mid = (i) => (W[i].start + W[i].end) / 2;
  const line = idx.map((i) => `${X(mid(i))},${Y(L.value[i])}`).join(" ");
  const band = idx.map((i) => `${X(mid(i))},${Y(L.hi[i])}`).concat(idx.slice().reverse().map((i) => `${X(mid(i))},${Y(L.lo[i])}`)).join(" ");
  const rects = rep.regions.filter((r) => r.end > t0 && r.start < t1).map((r) =>
    `<rect x="${X(Math.max(r.start, t0))}" y="0" width="${(X(Math.min(r.end, t1)) - X(Math.max(r.start, t0))).toFixed(1)}" height="240" fill="#D9473F" fill-opacity="0.10"/>`).join("");
  const ticks = [];
  const step = Math.max(1, Math.round((b - a) / 7));
  for (let i = a; i <= b; i += step) ticks.push(i);
  const hot = (i) => rep.regions.some((r) => i >= r.w0 && i <= r.w1);
  if (top && !whole) { ticks.push(top.w0); }
  const uniq = [...new Set(ticks)].sort((x, y) => x - y).filter((i, k, arr) => k === 0 || (mid(i) - mid(arr[k - 1])) / (t1 - t0) > 0.06);
  const yt = [0.15, 0.5, 0.85].map((f) => ymin + (ymax - ymin) * (1 - f));
  const fmt = (v) => (Math.abs(ymax - ymin) < 3 ? v.toFixed(2) : v.toFixed(1));
  return `<div class="chart"><div class="yax" style="height:240px">${yt.map((v) => `<span style="top:${((1 - (v - ymin) / (ymax - ymin)) * 240).toFixed(0)}px">${fmt(v)}</span>`).join("")}</div>
    <div class="plot"><svg viewBox="0 0 1000 240" preserveAspectRatio="none" role="img" aria-label="${esc(LANES[lane][0])}: your line against the good readers' band; flagged spans shaded">
      ${yt.map((v) => `<line x1="0" x2="1000" y1="${Y(v)}" y2="${Y(v)}" stroke="#EEF2F5" vector-effect="non-scaling-stroke"/>`).join("")}
      ${rects}<polygon points="${band}" fill="#DCE8F2" fill-opacity="0.85"/>
      <polyline points="${line}" fill="none" stroke="#2B6CA3" stroke-width="2.5" stroke-linejoin="round" vector-effect="non-scaling-stroke"/></svg>
      <div class="xax" aria-hidden="true">${uniq.map((i) => `<span class="${hot(i) ? "hot" : ""}" style="left:${(X(mid(i)) / 10).toFixed(1)}%">${esc(W[i].word)}</span>`).join("")}</div>
    </div></div>
    <div class="legend"><span><i style="height:3px;background:#2B6CA3"></i>You (${esc(LANES[lane][1])})</span><span><i style="background:#DCE8F2"></i>Range of ${rep.k} good reader${rep.k > 1 ? "s" : ""}</span><span><i style="background:var(--rose)"></i>Out of range</span></div>`;
}

/* ---------- report view (shared by Report and Live demo) ---------- */
function renderReport(el, sess, opts = {}) {
  const rep = sess.report, sm = summary(rep), top = topRegion(rep);
  const live = !!sess.server;
  const t = textById(rep.text_id);
  const fix = top ? (() => {
    const p = explainParts(top), i = rep.regions.indexOf(top);
    return `<section class="fix" aria-labelledby="h-fix">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:12px"><span class="eyebrow">${rep.regions.length > 1 ? `TOP PRIORITY · 1 OF ${rep.regions.length}` : "ONE THING TO FIX"}</span><span class="when">${top.start.toFixed(1)}–${top.end.toFixed(1)} s</span></div>
      <h2 id="h-fix">${esc(headline(rep, top))}</h2><p>${esc(p.what)}</p>${p.tip ? `<p class="tip">${esc(p.tip)}</p>` : ""}
      <div class="ab">${live ? `<button class="btn primary" data-play="${i}:you">${ICON.play}Play yours</button><button class="btn white" data-play="${i}:good">${ICON.play}Play a good reader</button>` : `<span class="meta">Audio playback is available right after an analysis.</span>`}</div></section>`;
  })() : `<section class="fix clean"><span class="eyebrow">ALL CLEAR</span><h2>Every word stayed inside the good readers’ range.</h2><p>Nothing was flagged. Try a harder passage, or read this one with a different interpretation.</p></section>`;
  const rows = rep.regions.map((r, i) => `<tr><td style="white-space:nowrap">${r.start.toFixed(1)}–${r.end.toFixed(1)} s</td>
      <td>${r.w0 + 1}–${r.w1 + 1} · “${esc(wordsText(rep, r, 8))}”</td><td><span class="tag">${esc(ISSUE[r.type](r))}</span></td>
      <td>${esc(explainParts(r).what)}</td><td>${(r.severity ?? 0).toFixed(1)} / 5</td>
      <td style="white-space:nowrap">${live ? `<button class="iconbtn" aria-label="Play yours" data-play="${i}:you">${ICON.play}</button> <button class="iconbtn" aria-label="Play a good reader" data-play="${i}:good" style="color:var(--ok-ink)">${ICON.play}</button>` : ""}</td></tr>`).join("");
  el.innerHTML = `
    ${opts.header ?? ""}
    <div class="row">
      <section class="card ringcard" style="flex:1 1 420px" aria-labelledby="h-ring">
        ${ringHTML(sm.st, sm.pct, true)}
        <div style="flex:1 1 180px;display:flex;flex-direction:column;gap:14px">
          <h2 id="h-ring">Words vs. good readers</h2>
          <div class="legend-row"><span><span class="sw ok"></span>In range</span><span>${sm.inRange}</span></div>
          <div class="legend-row"><span><span class="sw warn"></span>Borderline</span><span>${sm.border}</span></div>
          <div class="legend-row"><span><span class="sw bad"></span>Out of range</span><span>${sm.flagged}</span></div>
          <p class="meta">One dot per word, clockwise from the top. Borderline words left the range a little, not enough to flag.</p>
        </div>
      </section>
      <div style="flex:1 1 380px;display:flex;min-width:0">${fix}</div>
    </div>
    ${dimsHTML(rep, true)}
    <section class="card" style="display:flex;flex-direction:column;gap:18px" aria-labelledby="h-chart">
      <div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px">
        <div><h2 id="h-chart">Word by word</h2><p class="meta" id="chart-sub"></p></div>
        <div style="display:flex;flex-wrap:wrap;gap:10px">
          <div class="seg" role="tablist" aria-label="Measure">${Object.keys(LANES).map((k, i) => `<button role="tab" data-lane="${k}" aria-selected="${i === 0}">${LANES[k][0]}</button>`).join("")}</div>
          ${top ? `<div class="seg" aria-label="Range"><button data-whole="0" aria-pressed="true">Around the flag</button><button data-whole="1" aria-pressed="false">Whole reading</button></div>` : ""}
        </div>
      </div>
      <div id="chart"></div>
    </section>
    ${rep.regions.length ? `<section class="card" aria-labelledby="h-flags"><h2 id="h-flags" style="margin-bottom:14px">Flagged regions</h2>
      <div class="tablewrap"><table><thead><tr><th>Time</th><th>Words</th><th>Issue</th><th>What we measured</th><th>Severity</th><th><span class="sr">Listen</span></th></tr></thead><tbody>${rows}</tbody></table></div></section>` : ""}
    <div class="foot"><span>Compared with ${rep.k} good reading${rep.k > 1 ? "s" : ""} of ${esc(t ? t.title : rep.text_id)} · thresholds fitted on ${esc(rep.params_fitted_on)}</span><span>Report ${esc(rep.hash)} · same audio gives the same report</span></div>`;
  let lane = "rate", whole = !top;
  const draw = () => {
    $("#chart", el).innerHTML = chartHTML(rep, lane, whole);
    const W = rep.words, a = whole || !top ? 0 : Math.max(0, top.w0 - 22), b = whole || !top ? W.length - 1 : Math.min(W.length - 1, top.w1 + 22);
    $("#chart-sub", el).textContent = `${W[a].start.toFixed(1)}–${W[b].end.toFixed(1)} s · ${LANES[lane][0].toLowerCase()} against the good readers`;
  };
  draw();
  el.querySelectorAll("[data-lane]").forEach((b) => b.addEventListener("click", () => {
    lane = b.dataset.lane; el.querySelectorAll("[data-lane]").forEach((x) => x.setAttribute("aria-selected", x === b)); draw();
  }));
  el.querySelectorAll("[data-whole]").forEach((b) => b.addEventListener("click", () => {
    whole = b.dataset.whole === "1"; el.querySelectorAll("[data-whole]").forEach((x) => x.setAttribute("aria-pressed", x === b)); draw();
  }));
  el.querySelectorAll("[data-play]").forEach((b) => b.addEventListener("click", () => {
    const [i, who] = b.dataset.play.split(":");
    playClip(`/api/clip/${sess.server}/${i}/${who}`);
  }));
}
let player;
function playClip(url) {
  if (player) player.pause();
  player = new Audio(url);
  player.play().catch(() => toast("This audio is no longer available. Analyses are kept in memory until the app restarts."));
}

/* ---------- microphone ---------- */
const mic = { stream: null, ctx: null, analyser: null, raf: 0, recorder: null, chunks: [], t0: 0, timer: 0 };
function setChip(state) {
  const c = $("#mic-chip");
  c.classList.toggle("on", state === "on"); c.classList.toggle("rec", state === "rec");
  $(".label", c).textContent = state === "rec" ? "Recording" : state === "on" ? "Mic on" : "Mic off";
}
async function micPermissionState() {
  try { const p = await navigator.permissions.query({ name: "microphone" }); return p.state; } catch { return "prompt"; }
}
async function openMic() {
  mic.stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
  mic.ctx = new (window.AudioContext || window.webkitAudioContext)();
  const src = mic.ctx.createMediaStreamSource(mic.stream);
  mic.analyser = mic.ctx.createAnalyser(); mic.analyser.fftSize = 512;
  src.connect(mic.analyser);
  setChip("on");
}
function closeMic() {
  cancelAnimationFrame(mic.raf); clearInterval(mic.timer);
  mic.onClose?.(); mic.onClose = null;
  if (mic.recorder && mic.recorder.state !== "inactive") mic.recorder.stop();
  mic.stream?.getTracks().forEach((t) => t.stop());
  mic.ctx?.close().catch(() => {});
  Object.assign(mic, { stream: null, ctx: null, analyser: null, recorder: null });
  setChip("off");
}
function runMeter(el) {
  cancelAnimationFrame(mic.raf);
  const bars = [...el.querySelectorAll("span")], buf = new Uint8Array(512);
  const tick = () => {
    if (!mic.analyser || !el.isConnected) return;
    mic.analyser.getByteTimeDomainData(buf);
    let sum = 0; for (const v of buf) sum += ((v - 128) / 128) ** 2;
    const rms = Math.sqrt(sum / buf.length), lvl = Math.min(1, rms * 6);
    bars.forEach((b, i) => { const shape = 0.45 + 0.55 * Math.abs(Math.sin(i * 1.3 + performance.now() / 180)); b.style.height = `${6 + lvl * 42 * shape}px`; });
    mic.raf = requestAnimationFrame(tick);
  };
  tick();
}
const meterHTML = (rec) => `<div class="meter${rec ? " rec" : ""}" aria-hidden="true">${"<span></span>".repeat(14)}</div>`;

/* ---------- views ---------- */
function setNav(route, crumbs) {
  document.querySelectorAll(".nav").forEach((a) => {
    if (a.dataset.route === route) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
  });
  $("#crumbs").innerHTML = crumbs;
}
const greeting = () => { const h = new Date().getHours(); return h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening"; };

async function viewHome() {
  setNav("home", "Home");
  const all = sessions(), last = all[0], name = settings().name;
  const hello = `<h1 class="hello">${greeting()}${name ? `, <em>${esc(name)}</em>` : ""}</h1>`;
  if (!last) {
    main.innerHTML = `${hello}
      <div class="row"><section class="card" style="flex:2 1 420px;display:flex;flex-direction:column;gap:16px">
        <h2 style="font-size:26px">Record your first reading</h2>
        <p class="meta" style="font-size:16px;line-height:1.6">Read a short passage aloud. Cadence finds every word and compares your pace, pauses, pitch and loudness with six strong readers of the same text, then tells you exactly where, and by how much, you left their range.</p>
        <div style="display:flex;flex-wrap:wrap;gap:10px"><a class="btn primary big" href="#/practice">Start practising ${ICON.arrow}</a><a class="btn big" href="#/demo">See it catch a known flaw</a></div>
      </section>
      <section class="card" style="flex:1 1 260px;display:flex;flex-direction:column;gap:12px">
        <h2>How it judges you</h2>
        <ul class="checks"><li>${ICON.check}Not a generic “good speaker” score: only the range real readers of this text use.</li><li>${ICON.check}Voice type and mic level don’t count: pitch and loudness are relative to you.</li><li>${ICON.check}Every flag comes with seconds, words and measured numbers.</li></ul>
      </section></div>`;
    return;
  }
  const rep = last.report, sm = summary(rep), top = topRegion(rep);
  const mins = all.reduce((s, x) => s + (x.duration || 0), 0), words = all.reduce((s, x) => s + x.report.words.length, 0);
  const tile = (ico, k, v) => `<div class="tile"><span class="ico">${ico}</span><span class="k">${k}</span><span class="v">${v}</span></div>`;
  const trend = all.length >= 2 ? (() => {
    const ss = all.slice(0, 8).reverse();
    return `<div class="dims grid">${DIMS.map(([key, label]) => {
      const vals = ss.map((x) => x.report.scores[key]);
      const pts = vals.map((v, i) => `${((i / Math.max(1, vals.length - 1)) * 100).toFixed(1)},${(30 - (v / 10) * 26).toFixed(1)}`).join(" ");
      return `<div class="dim"><div class="t"><span>${label}</span><span>${vals[vals.length - 1].toFixed(1)}</span></div>
        <svg viewBox="0 0 100 32" preserveAspectRatio="none" style="width:100%;height:36px" role="img" aria-label="${label} over your last ${vals.length} sessions"><polyline points="${pts}" fill="none" stroke="#2B6CA3" stroke-width="2" vector-effect="non-scaling-stroke"/></svg></div>`;
    }).join("")}</div>`;
  })() : `<div class="empty"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6A7682" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M3 17l6-6 4 4 8-8M15 7h6v6"/></svg>Record one more session to see how each rubric dimension moves.</div>`;
  main.innerHTML = `${hello}
    <div class="row" style="align-items:flex-start">
      <div class="col" style="flex:3 1 600px">
        <div class="tiles">${tile(ICON.mic.replace('aria-hidden="true"', 'aria-hidden="true"'), "SESSIONS", all.length)}${tile(ICON.clock, "PRACTICE TIME", fmtTime(mins))}${tile(ICON.book, "WORDS READ", words)}${tile(ICON.alert, "TO FIX", rep.regions.length)}</div>
        <section class="card ringcard" aria-labelledby="h-latest">
          ${ringHTML(sm.st, sm.pct)}
          <div style="flex:1 1 280px;min-width:0;display:flex;flex-direction:column;gap:22px">
            <div style="display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-start;gap:16px">
              <div><h2 id="h-latest" style="font-size:22px">Latest session</h2><p class="meta">${esc(last.title)} · ${new Date(last.date).toLocaleString()}</p></div>
              <a class="btn primary" href="#/report/${esc(last.id)}">View report</a>
            </div>
            <div class="counts">
              <div class="count"><div class="n"><span class="sw ok"></span>${sm.inRange}</div><div class="l">IN RANGE</div></div>
              <div class="count"><div class="n"><span class="sw warn"></span>${sm.border}</div><div class="l">BORDERLINE</div></div>
              <div class="count"><div class="n"><span class="sw bad"></span>${sm.flagged}</div><div class="l">OUT OF RANGE</div></div>
            </div>
            <p class="meta" style="line-height:1.55">One dot per word, clockwise from the top. “In range” means inside what ${rep.k} strong readers of the same text did.</p>
          </div>
        </section>
        ${top ? `<section class="card" style="display:flex;flex-wrap:wrap;align-items:center;gap:20px"><span class="bigicon" style="width:52px;height:52px;background:var(--rose);color:var(--rose-ink)">${ICON.alert}</span>
          <div style="flex:1 1 300px;min-width:0"><h2 style="font-size:18px">Practise next: ${esc(headline(rep, top).replace(/\.$/, ""))}</h2><p class="meta">${esc(explainParts(top).tip)}</p></div>
          <a class="btn" href="#/practice?t=${esc(rep.text_id)}&w0=${top.w0}&w1=${top.w1}">Practise this line ${ICON.arrow}</a></section>` : ""}
        <section style="padding:0 8px"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px"><h2 style="font-size:20px">Trends</h2><a href="#/reports" style="font-size:14px;color:var(--muted);text-decoration:none">All reports</a></div>${trend}</section>
      </div>
      <aside class="col" style="flex:1 1 240px" aria-label="Rubric, latest session">${dimsHTML(rep, false)}</aside>
    </div>`;
}

async function viewPractice(params) {
  await loadTexts();
  setNav("practice", `<a href="#/home">Home</a> / Practice`);
  const last = sessions()[0];
  let tid = params.get("t") || (last && textById(last.report.text_id) ? last.report.text_id : (TEXTS.find((t) => t.id === "T4") || TEXTS[0]).id);
  let hw = params.has("w0") ? [Number(params.get("w0")), Number(params.get("w1"))] : null;
  if (!hw && last && last.report.text_id === tid) { const r = topRegion(last.report); if (r) hw = [r.w0, r.w1]; }
  let state = "permission", take = null, err = "";

  /* The passage as one element per scored word (same tokenizer as the server: letters and apostrophes). */
  const passageWordsHTML = (t) => {
    let out = "", pos = 0, k = 0;
    for (const m of t.display.matchAll(/[A-Za-z’']+/g)) {
      const core = m[0].replace(/^[’']+|[’']+$/g, "");
      if (!core) continue;
      out += esc(t.display.slice(pos, m.index));
      const flag = hw && k >= hw[0] && k <= hw[1] ? " flag" : "";
      out += `<span class="w${flag}" data-i="${k}">${esc(m[0])}</span>`;
      pos = m.index + m[0].length; k++;
    }
    return out + esc(t.display.slice(pos));
  };
  const passageHTML = () => {
    const t = textById(tid);
    return `<div style="display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:14px">
        <div><h2 id="h-passage" style="font-size:22px">${esc(t.title)}</h2><p class="meta">${esc(t.author)} · ${t.words} words · good readers take about ${fmtTime(t.typical_s)}</p></div>
        <label class="field">Passage<select id="passage">${TEXTS.map((x) => `<option value="${x.id}"${x.id === tid ? " selected" : ""}>${esc(x.title)}${x.group === "research" ? " (research)" : ""}</option>`).join("")}</select></label>
      </div>
      <div class="live-legend" id="live-legend" hidden><span><i class="lg-you"></i>You</span><span><i class="lg-ghost"></i>A typical good reader</span><span><i class="lg-done"></i>Read</span></div>
      <p class="passage" id="passage-text">${passageWordsHTML(t)}</p>
      <p class="note">${ICON.info}<span>${hw ? "Highlighted: the line flagged last time. " : ""}Read the whole passage from its first word to its last; the title isn’t part of it.${t.context ? " " + esc(t.context) : ""}</span></p>`;
  };

  /* ---- live read-along: Chrome's speech recognizer → position in the passage; ghost reader from good readers' timings ---- */
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const norm = (w) => w.toLowerCase().replace(/[’']/g, "").replace(/[^a-z]/g, "");
  const lev = (a, b) => {
    const d = Array.from({ length: a.length + 1 }, (_, i) => [i]);
    for (let j = 1; j <= b.length; j++) d[0][j] = j;
    for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++)
      d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    return d[a.length][b.length];
  };
  const similar = (a, b) => a === b || (a.length > 3 && b.length > 3 && (a.startsWith(b) || b.startsWith(a) || lev(a, b) <= (Math.max(a.length, b.length) > 6 ? 2 : 1)))
    || (a.length >= 5 && b.length <= 4 && a.startsWith(b));  // "cannot" heard for "can not"
  const follow = { rec: null, base: 0, fin: 0, ptr: 0, voiceAt: 0, words: [], on: false, note: "" };
  const advance = (from, tokens) => {
    let p = from;
    for (const tok of tokens) {
      const n = norm(tok); if (!n) continue;
      for (let j = p; j < Math.min(follow.words.length, p + 5); j++) if (similar(n, follow.words[j])) { p = j + 1; break; }
    }
    return p;
  };
  function startFollow() {
    const t = textById(tid);
    follow.words = [...t.display.matchAll(/[A-Za-z’']+/g)].map((m) => norm(m[0])).filter(Boolean);
    Object.assign(follow, { base: 0, fin: 0, ptr: 0, voiceAt: 0, on: true, note: "" });
    $("#passage-text").classList.add("live");
    $("#live-legend").hidden = false;
    if (!SR) { follow.note = "Live word-following needs Chrome or Edge. Recording still works; the ghost reader shows a typical pace."; return; }
    const rec = new SR();
    rec.lang = "en-US"; rec.continuous = true; rec.interimResults = true; rec.maxAlternatives = 1;
    rec.onresult = (e) => {
      let fin = [], all = [];
      for (let i = 0; i < e.results.length; i++) {
        const toks = e.results[i][0].transcript.split(/\s+/);
        all = all.concat(toks); if (e.results[i].isFinal) fin = fin.concat(toks);
      }
      follow.fin = advance(follow.base, fin);
      follow.ptr = Math.max(follow.fin, advance(follow.base, all), follow.ptr);
      paintFollow();
    };
    rec.onerror = (e) => {
      if (e.error === "no-speech" || e.error === "aborted") return;
      follow.note = e.error === "network" ? "Live word-following needs an internet connection (Chrome’s speech service). Recording continues."
        : e.error === "not-allowed" || e.error === "service-not-allowed" ? "Live word-following was blocked. Recording continues."
        : `Live word-following stopped (${e.error}). Recording continues.`;
      paintFollow();
    };
    rec.onend = () => {  // Chrome ends a session after a pause: carry on from the last confirmed word
      if (!follow.on) return;
      follow.base = follow.fin = follow.ptr;
      try { rec.start(); } catch { /* already restarting */ }
    };
    follow.rec = rec;
    try { rec.start(); } catch { follow.note = "Live word-following could not start. Recording continues."; }
  }
  mic.onClose = () => { follow.on = false; try { follow.rec?.stop(); } catch { /* not running */ } };
  function stopFollow() {
    follow.on = false;
    try { follow.rec?.stop(); } catch { /* not running */ }
    follow.rec = null;
    $("#passage-text")?.classList.remove("live");
    $("#passage-text")?.querySelectorAll(".w").forEach((w) => w.classList.remove("done", "cur", "ghost"));
    const lg = $("#live-legend"); if (lg) lg.hidden = true;
  }
  const LAG = 0.7;  // the recognizer reports a word ~0.7 s after it is spoken
  function paceNow() {
    const g = textById(tid).ghost, n = g.median.length;
    if (!follow.voiceAt) return { ghost: -1, state: "wait" };
    const el = (performance.now() - follow.voiceAt) / 1000;
    let gi = 0; while (gi + 1 < n && g.median[gi + 1] <= el) gi++;
    const k = Math.min(follow.ptr, n - 1);
    if (!SR || follow.ptr < 3) return { ghost: gi, state: follow.ptr ? "early" : "wait" };
    const e = el - LAG, fast = g.fast[k], slow = g.slow[k];
    const pos = slow > fast ? (slow - e) / (slow - fast) : 0.5;  // 1 = as early as the fastest good reader
    const x = pos > 1 ? 70 + Math.min(30, (pos - 1) * 60) : pos < 0 ? 30 - Math.min(30, -pos * 60) : 30 + pos * 40;
    return { ghost: gi, state: e < fast - 0.5 ? "fast" : e > slow + 0.5 ? "slow" : "ok", x };
  }
  const PACE_TEXT = {
    wait: ["Start reading", "The highlight follows your voice."], early: ["Listening…", "Pace appears after a few words."],
    ok: ["On pace", "Inside the range of the good readers."], fast: ["Faster than every good reader", "Ease off a little; let the words land."],
    slow: ["Slower than every good reader", "Keep going, a little quicker."],
  };
  function paintFollow() {
    const box = $("#passage-text"); if (!box || !follow.on) return;
    const p = paceNow();
    box.querySelectorAll(".w").forEach((w) => {
      const i = Number(w.dataset.i);
      w.classList.toggle("done", SR && i < follow.ptr);
      w.classList.toggle("cur", SR && i === follow.ptr && follow.voiceAt > 0);
      w.classList.toggle("ghost", i === p.ghost);
    });
    const cur = box.querySelector(".w.cur") || box.querySelector(".w.ghost");
    if (cur) { const r = cur.getBoundingClientRect(); if (r.bottom > innerHeight - 140 || r.top < 80) window.scrollBy({ top: r.top - innerHeight * 0.4, behavior: "smooth" }); }
    const g = $("#gauge"); if (!g) return;
    const [h, s] = PACE_TEXT[p.state];
    g.dataset.state = p.state;
    $("#pace-h").textContent = h; $("#pace-s").textContent = follow.note || s;
    const dot = $("#pace-dot"); dot.hidden = p.x == null; if (p.x != null) dot.style.left = `${p.x}%`;
    const n = textById(tid).ghost.median.length;
    $("#wc").textContent = SR ? `${Math.min(follow.ptr, n)} / ${n} words` : `${n} words`;
    $("#wprog").style.width = `${(100 * Math.min(follow.ptr, n)) / n}%`;
  }
  const stepsHTML = () => {
    const idx = { permission: 1, denied: 1, unsupported: 1, ready: 2, recording: 2, review: 3, analyzing: 4, error: 3 }[state];
    return ["Microphone", "Record", "Review", "Analyze"].map((l, i) => {
      const cls = i + 1 === idx ? "cur" : i + 1 < idx ? "done" : "";
      return `<li class="${cls}"><span class="n">${i + 1 < idx ? "✓" : i + 1}</span>${l}</li>`;
    }).join("");
  };
  const recorderHTML = () => {
    const t = textById(tid);
    switch (state) {
      case "permission": return `<div class="recorder"><div class="bigicon">${ICON.mic}</div>
        <div><h2 id="h-rec" style="font-size:24px;margin-bottom:8px">Turn on your microphone</h2><p class="meta" style="font-size:15px;line-height:1.6">Cadence listens only while you record. Your score is computed on this computer.</p></div>
        <ul class="checks"><li>${ICON.check}A quiet room works best; 20–30 cm from the mic.</li><li>${ICON.check}Your voice type and mic level don’t affect the score: pitch and loudness are compared with your own.</li><li>${ICON.check}To highlight words as you read, Chrome’s speech recognition sends the live audio to Google while you record. Your saved recording stays here.</li></ul>
        <button class="btn primary big block" id="allow">Allow microphone</button>
        <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:6px 18px"><button class="btn link" id="notnow">Not now</button><button class="btn link" data-upload>Upload a recording instead</button></div></div>`;
      case "denied": return `<div class="recorder"><div class="bigicon sand">${ICON.micOff}</div>
        <div><h2 style="font-size:24px;margin-bottom:8px">The microphone is off</h2><p class="meta" style="font-size:15px;line-height:1.6">No problem. To record, allow the microphone for this page in your browser:</p></div>
        <ol style="margin:0;padding-left:20px;font-size:14px;line-height:1.8;color:#34495C"><li>Click the icon at the left of the address bar.</li><li>Set Microphone to Allow.</li><li>Come back and choose Try again.</li></ol>
        <button class="btn primary big block" id="retry">Try again</button><button class="btn block" data-upload>Upload a recording instead</button></div>`;
      case "unsupported": return `<div class="recorder"><div class="bigicon sand">${ICON.micOff}</div>
        <div><h2 style="font-size:24px;margin-bottom:8px">Recording isn’t available here</h2><p class="meta" style="font-size:15px;line-height:1.6">Browsers only allow the microphone on localhost or HTTPS. Open <b>http://localhost:8000</b> on this computer, or upload a recording.</p></div>
        <button class="btn primary big block" data-upload>Upload a recording</button></div>`;
      case "ready": return `<div class="recorder center"><div class="okbar">${ICON.check.replace("<svg", '<svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2"')}<span>Microphone on. Say a few words: the bars should move.</span></div>
        ${meterHTML(false)}<button class="recbtn" id="rec" aria-label="Start recording">${ICON.mic}</button>
        <div><div style="font-size:18px">Ready when you are</div><div class="meta" style="margin-top:4px">Press record, then read the whole passage.</div></div>
        <button class="btn link" data-upload>Upload a recording instead</button></div>`;
      case "recording": return `<div class="recorder center"><div style="align-self:stretch;display:flex;justify-content:space-between;align-items:center;font-size:14px;color:var(--muted)"><span style="display:flex;align-items:center;gap:8px;color:#A23B48;font-weight:600"><span class="sw bad" style="width:10px;height:10px"></span>Recording</span><span id="timer" style="font-size:18px;color:var(--ink)">0:00</span></div>
        <div class="gauge" id="gauge" data-state="wait" aria-live="polite">
          <div class="pace-h" id="pace-h">Start reading</div><div class="meta" id="pace-s">The highlight follows your voice.</div>
          <div class="track" aria-hidden="true"><span class="zone">Slower</span><span class="band">Good readers</span><span class="zone">Faster</span><i id="pace-dot" hidden></i></div>
        </div>
        <div style="align-self:stretch"><div style="display:flex;justify-content:space-between;font-size:13px;color:var(--muted);margin-bottom:6px"><span id="wc"></span><span>Good readers ≈ ${fmtTime(t.typical_s)}</span></div><div class="progress"><div id="wprog"></div></div></div>
        <button class="stopbtn" id="stop" aria-label="Stop recording"><span></span></button><div class="meta">Stop when you reach the last word.</div></div>`;
      case "review": return `<div class="recorder"><h2 style="font-size:24px">${take.name ? "File ready" : `Nice. Recorded ${fmtTime(take.seconds)}.`}</h2>
        <audio controls src="${take.url}"></audio>
        <p class="meta" style="line-height:1.55">Analysis finds each word, measures pace, pauses, pitch and loudness, and compares them with the good readers. It takes about half a minute.</p>
        <label class="field">Compare with<select id="method"><option value="envelope"${settings().method === "envelope" ? " selected" : ""}>Six good readers (recommended)</option><option value="single"${settings().method === "single" ? " selected" : ""}>One reference reader</option></select></label>
        <button class="btn primary big block" id="analyze">Analyze my reading ${ICON.arrow}</button><button class="btn block" id="redo">Record again</button></div>`;
      case "analyzing": return `<div class="recorder center" style="padding:40px 0"><div class="spinner" aria-hidden="true"></div><h2 style="font-size:22px">Analysing your reading…</h2><p class="meta" id="phase">Finding each word in the recording</p></div>`;
      case "error": return `<div class="recorder"><h2 style="font-size:24px">We couldn’t analyse that take</h2><div class="errbar">${esc(err)}</div>
        <button class="btn primary big block" id="redo">Record again</button><button class="btn block" data-upload>Upload a different file</button></div>`;
    }
  };
  main.innerHTML = `<h1 class="hello" style="font-size:40px">Read it aloud, <em>start to finish.</em></h1>
    <ol class="steps" id="steps" aria-label="Progress"></ol>
    <div class="row"><section class="card" style="flex:3 1 460px;display:flex;flex-direction:column;gap:18px" aria-labelledby="h-passage" id="passage-card"></section>
    <section class="card" style="flex:2 1 340px" aria-live="polite" id="recorder"></section></div>
    <input type="file" id="file" accept="audio/*,video/*" hidden>`;
  const paint = () => {
    $("#steps").innerHTML = stepsHTML();
    $("#recorder").innerHTML = recorderHTML();
    bind();
  };
  const go = (s) => { state = s; paint(); };
  $("#passage-card").innerHTML = passageHTML();
  $("#passage").addEventListener("change", (e) => { tid = e.target.value; hw = null; $("#passage-card").innerHTML = passageHTML(); bindPassage(); });
  const bindPassage = () => $("#passage").addEventListener("change", (e) => { tid = e.target.value; hw = null; $("#passage-card").innerHTML = passageHTML(); bindPassage(); });
  const fileInput = $("#file");
  fileInput.addEventListener("change", () => {
    const f = fileInput.files[0]; if (!f) return;
    take = { blob: f, name: f.name, url: URL.createObjectURL(f), seconds: 0 }; go("review");
  });
  async function allow() {
    if (!navigator.mediaDevices?.getUserMedia || !window.isSecureContext) return go("unsupported");
    try { await openMic(); go("ready"); } catch (e) { go(e && e.name === "NotAllowedError" ? "denied" : "denied"); if (e && e.name !== "NotAllowedError") toast(`Microphone error: ${e.message || e.name}`); }
  }
  function startRec() {
    const types = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg"];
    const mime = types.find((m) => window.MediaRecorder && MediaRecorder.isTypeSupported(m)) || "";
    mic.chunks = [];
    mic.recorder = new MediaRecorder(mic.stream, mime ? { mimeType: mime } : undefined);
    mic.recorder.ondataavailable = (e) => e.data.size && mic.chunks.push(e.data);
    mic.recorder.onstop = () => {
      const blob = new Blob(mic.chunks, { type: mic.recorder?.mimeType || mime || "audio/webm" });
      const secs = (performance.now() - mic.t0) / 1000;
      take = { blob, url: URL.createObjectURL(blob), seconds: secs, ext: (blob.type.includes("mp4") ? ".m4a" : blob.type.includes("ogg") ? ".ogg" : ".webm") };
      setChip("on"); go("review");
    };
    mic.recorder.start(250); mic.t0 = performance.now(); setChip("rec"); go("recording");
    startFollow(); paintFollow();
    mic.timer = setInterval(() => {
      const el = $("#timer"); if (el) el.textContent = fmtTime((performance.now() - mic.t0) / 1000);
      paintFollow();
    }, 250);
    // voice level: a ring around the stop button, and the moment you start speaking starts the ghost reader
    const buf = new Uint8Array(512);
    const loop = () => {
      if (!mic.analyser || state !== "recording") return;
      mic.analyser.getByteTimeDomainData(buf);
      let sum = 0; for (const v of buf) sum += ((v - 128) / 128) ** 2;
      const lvl = Math.min(1, Math.sqrt(sum / buf.length) * 6);
      if (!follow.voiceAt && lvl > 0.22 && performance.now() - mic.t0 > 300) { follow.voiceAt = performance.now(); paintFollow(); }
      const b = $("#stop"); if (b) b.style.boxShadow = `0 0 0 ${(6 + lvl * 26).toFixed(1)}px rgba(217,71,63,${(0.12 + lvl * 0.18).toFixed(2)})`;
      mic.raf = requestAnimationFrame(loop);
    };
    loop();
  }
  function stopRec() { clearInterval(mic.timer); cancelAnimationFrame(mic.raf); stopFollow(); mic.recorder?.stop(); }
  async function analyzeTake() {
    const method = $("#method")?.value || "envelope";
    store.set("settings", { ...settings(), method });
    go("analyzing");
    const phases = ["Finding each word in the recording", "Measuring pace, pauses, pitch and loudness", "Comparing with the good readers", "Writing your report"];
    let k = 0; const ph = setInterval(() => { const el = $("#phase"); if (el) el.textContent = phases[Math.min(++k, phases.length - 1)]; }, 6000);
    const fd = new FormData();
    fd.append("file", take.blob, take.name || `take${take.ext || ".webm"}`);
    fd.append("text_id", tid); fd.append("method", method);
    try {
      const r = await fetch("/api/analyze", { method: "POST", body: fd });
      const body = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(body.detail || `The server returned ${r.status}.`);
      const id = `${Date.now().toString(36)}`;
      saveSession({ id, date: new Date().toISOString(), title: body.text_title, duration: body.duration_s, server: body.session, good_reader: body.good_reader, report: body.report });
      clearInterval(ph); closeMic();
      location.hash = `#/report/${id}`;
    } catch (e) { clearInterval(ph); err = e.message; go("error"); }
  }
  function bind() {
    $("#allow")?.addEventListener("click", allow);
    $("#retry")?.addEventListener("click", allow);
    $("#notnow")?.addEventListener("click", () => go("denied"));
    $("#rec")?.addEventListener("click", startRec);
    $("#stop")?.addEventListener("click", stopRec);
    $("#analyze")?.addEventListener("click", analyzeTake);
    $("#redo")?.addEventListener("click", () => { take = null; mic.stream ? go("ready") : go("permission"); });
    document.querySelectorAll("[data-upload]").forEach((b) => b.addEventListener("click", () => fileInput.click()));
    const m = $(".meter"); if (m && mic.analyser) runMeter(m);
  }
  if (!navigator.mediaDevices?.getUserMedia || !window.isSecureContext) state = "unsupported";
  else if (mic.stream) state = "ready";
  else {
    const p = await micPermissionState();
    if (p === "granted") { try { await openMic(); state = "ready"; } catch { state = "permission"; } }
    else if (p === "denied") state = "denied";
  }
  paint();
}

async function viewReport(id) {
  await loadTexts();
  const sess = sessions().find((s) => s.id === id);
  setNav("reports", `<a href="#/home">Home</a> / <a href="#/reports">Reports</a> / ${sess ? new Date(sess.date).toLocaleDateString() : "Not found"}`);
  if (!sess) { main.innerHTML = `<section class="card"><h2>Report not found</h2><p class="meta">Reports are saved in this browser only.</p></section>`; return; }
  const rep = sess.report;
  const header = `<div style="display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:16px">
      <div><h1 class="hello" style="font-size:40px">${esc(sess.title)}</h1><p class="sub">${fmtTime(sess.duration || 0)} · ${rep.words.length} words · compared with ${rep.k} good reading${rep.k > 1 ? "s" : ""} of the same text</p></div>
      <div style="display:flex;flex-wrap:wrap;gap:10px"><button class="btn" id="dl">${ICON.download}Download report</button><a class="btn primary" href="#/practice?t=${esc(rep.text_id)}">Practise again</a></div></div>`;
  renderReport(main, sess, { header });
  $("#dl").addEventListener("click", () => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([JSON.stringify(rep, null, 1)], { type: "application/json" }));
    a.download = `cadence_report_${rep.hash}.json`; a.click();
  });
}

function viewReports() {
  setNav("reports", `<a href="#/home">Home</a> / Reports`);
  const all = sessions();
  main.innerHTML = `<h1 class="hello" style="font-size:40px">Reports</h1>` + (all.length ? `<div class="list">${all.map((s) => {
    const sm = summary(s.report);
    return `<a class="listitem" href="#/report/${esc(s.id)}"><div class="grow"><div class="t">${esc(s.title)}</div><div class="m">${new Date(s.date).toLocaleString()} · ${fmtTime(s.duration || 0)}</div></div>
      <span class="chip" style="height:36px"><span class="sw ok"></span>${sm.pct}/100 in range</span><span class="chip" style="height:36px"><span class="sw ${s.report.regions.length ? "bad" : "ok"}"></span>${s.report.regions.length} to fix</span></a>`;
  }).join("")}</div>
    <div><button class="btn" id="clear">Clear history</button></div>` : `<div class="empty">No reports yet. <a href="#/practice">Record your first reading</a>.</div>`);
  $("#clear")?.addEventListener("click", () => { if (confirmClear()) { store.set("sessions", []); viewReports(); } });
}
function confirmClear() { return window.confirm("Delete every saved report from this browser?"); }

async function viewPassages() {
  await loadTexts();
  setNav("passages", `<a href="#/home">Home</a> / Passages`);
  const group = (g, title) => `<h2 style="font-size:20px;margin:8px 8px 0">${title}</h2><div class="list">${TEXTS.filter((t) => t.group === g).map((t) => `
    <div class="listitem"><div class="grow"><div class="t">${esc(t.title)}</div><div class="m">${esc(t.author)} · ${t.words} words · good readers ${fmtTime(t.range_s[0])}–${fmtTime(t.range_s[1])}</div></div>
    <a class="btn primary" href="#/practice?t=${t.id}">Practise</a></div>`).join("")}</div>`;
  main.innerHTML = `<h1 class="hello" style="font-size:40px">Passages</h1>${group("speech", "Speeches")}${group("research", "Research texts (poetry and accent benchmarks)")}`;
}

async function viewDemo() {
  await loadTexts();
  setNav("demo", `<a href="#/home">Home</a> / Live demo`);
  main.innerHTML = `<h1 class="hello" style="font-size:40px">Live demo: <em>a known flaw</em></h1>
    <section class="banner"><h2 style="font-size:20px">Same speaker, same words, one labelled edit</h2>
      <p class="meta" style="font-size:15px;line-height:1.6">We take a good public-domain reading and change one phrase by a known amount (here: speed it up). The original reading is removed from the comparison, so Cadence has to find the edit using the other good readers only. Running it re-analyses the clip live.</p>
      <div><button class="btn primary big" id="run">Run the demo</button></div></section><div id="demo-out"></div>`;
  $("#run").addEventListener("click", async () => {
    const out = $("#demo-out");
    $("#run").disabled = true;
    out.innerHTML = `<section class="card recorder center" style="padding:40px"><div class="spinner" aria-hidden="true"></div><h2>Analysing the clip…</h2></section>`;
    try {
      const r = await fetch("/api/demo", { method: "POST" });
      const body = await r.json();
      if (!r.ok) throw new Error(body.detail || r.status);
      const d = body.demo, lab = d.label, hit = d.matched_region != null ? body.report.regions[d.matched_region] : null;
      const b = d.baselines;
      const bl = (k, label) => b[k] ? `<li>${esc(label)}: ${b[k].matched ? "caught it" : "missed it"}${b[k].n_flags != null ? `, ${b[k].n_flags} flag${b[k].n_flags === 1 ? "" : "s"} in total` : ""}</li>` : "";
      const header = `<section class="banner ${hit && d.iou >= 0.5 ? "good" : ""}">
        <h2 style="font-size:22px">${hit && d.iou >= 0.5 ? "Caught it." : "Not caught in this run."}</h2>
        <p style="font-size:15px;line-height:1.6">Known edit: <b>${esc(lab.type.replace("_", " "))}${lab.subtype ? ` (${esc(lab.subtype)})` : ""}</b>, severity ${lab.severity} of 5, on “${esc(d.label_words)}” at ${lab.start.toFixed(2)}–${lab.end.toFixed(2)} s, in ${esc(d.source_speaker)}’s reading.
        ${hit ? `Cadence flagged ${hit.start.toFixed(2)}–${hit.end.toFixed(2)} s: onset error ${Math.round(Math.abs(hit.start - lab.start) * 1000)} ms, offset error ${Math.round(Math.abs(hit.end - lab.end) * 1000)} ms, overlap (IoU) ${d.iou.toFixed(2)}.` : ""}</p>
        <ul style="margin:0;padding-left:20px;font-size:14px;line-height:1.7;color:#34495C">${bl("B2 consensus envelope (K=all)", "Cadence, six good readers")}${bl("B1 single reference (K=1)", "One reference reader")}${bl("B0 generic norms", "Generic speaking rules")}</ul></section>`;
      const sess = { server: body.session, report: body.report, title: body.text_title, duration: body.duration_s };
      renderReport(out, sess, { header });
    } catch (e) { out.innerHTML = `<div class="errbar">${esc(e.message)}</div>`; }
    $("#run").disabled = false;
  });
}

async function viewEvidence() {
  setNav("evidence", `<a href="#/home">Home</a> / Evidence`);
  main.innerHTML = `<h1 class="hello" style="font-size:40px">Evidence</h1><div id="ev"><div class="spinner"></div></div>`;
  const ev = await (await fetch("/api/evidence")).json();
  const texts = [...new Set(ev.rows.map((r) => r.text))];
  const methods = [...new Set(ev.rows.map((r) => r.method))];
  const cell = (m, t) => { const r = ev.rows.find((x) => x.method === m && x.text === t); return r ? `${Math.round(r.matching_score * 100)}%<div class="meta" style="font-size:12px">${r.fa_per_min.toFixed(2)} FA/min</div>` : ""; };
  const cap = { "gradient_matching_by_severity.png": "Detection vs injected severity, pooled over held-out texts.", "gradient_by_type.png": "Size of the injected change at each severity, per flaw type.", "false_alarms_null_edit.png": "False alarms on good readings and on processed-but-unchanged clips.", "label_timing_error.png": "Timing error of the labels and of the detector." };
  $("#ev").innerHTML = `<section class="card"><h2>Matching Score on synthetic flaws</h2><p class="meta" style="margin-bottom:14px">Thresholds fitted on T1 only. Each method at its own calibrated operating point; false alarms per minute on good-vs-good pairs below each score.</p>
    <div class="tablewrap"><table><thead><tr><th>Method</th>${texts.map((t) => `<th>${esc(t)}${t === "T1" ? " (calibration)" : ""}</th>`).join("")}</tr></thead><tbody>${methods.map((m) => `<tr><td>${esc(m)}</td>${texts.map((t) => `<td>${cell(m, t)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>
    ${ev.ship_decision ? `<p class="note" style="margin-top:16px">${ICON.info}<span>Detector choice (pre-registered rule): ${esc(ev.ship_decision)}</span></p>` : ""}</section>
    <div class="figs">${ev.figures.map((f) => `<figure><img src="/figures/${esc(f)}" alt="${esc(cap[f] || f)}" loading="lazy"><figcaption>${esc(cap[f] || f)}</figcaption></figure>`).join("")}</div>`;
}

async function viewDataset() {
  setNav("dataset", `<a href="#/home">Home</a> / Dataset`);
  const ev = await (await fetch("/api/evidence")).json();
  const inv = ev.inventory;
  main.innerHTML = `<h1 class="hello" style="font-size:40px">Dataset</h1>
    <section class="banner"><p style="font-size:15px;line-height:1.6">Good readings of the same texts, plus synthetic flawed versions (6 flaw types × 5 severities) with exact time labels. Public at <a href="${esc(ev.dataset_url)}" target="_blank" rel="noopener">Hugging Face</a>.</p></section>
    <section class="card"><div class="tablewrap"><table><thead><tr><th>Text</th><th>Title</th><th>Role</th><th>Readings</th><th>Synthetic clips</th></tr></thead><tbody>
    ${Object.entries(inv).map(([k, v]) => { const c = v.synthetic_clips || {}; const n = Object.values(c).reduce((s, x) => s + x, 0); return `<tr><td>${esc(k)}</td><td>${esc(v.title)}</td><td>${esc(v.role)}</td><td>${v.recordings ?? ""}</td><td>${n || ""}</td></tr>`; }).join("")}
    </tbody></table></div></section>`;
}

function viewSettings() {
  setNav("settings", `<a href="#/home">Home</a> / Settings`);
  const s = settings();
  main.innerHTML = `<h1 class="hello" style="font-size:40px">Settings</h1><section class="card" style="display:flex;flex-direction:column;gap:18px;max-width:560px">
    <label class="field">Your name (shown in the greeting)<input type="text" id="name" value="${esc(s.name)}" autocomplete="given-name"></label>
    <label class="field">Compare with<select id="method"><option value="envelope"${s.method === "envelope" ? " selected" : ""}>Six good readers (recommended)</option><option value="single"${s.method === "single" ? " selected" : ""}>One reference reader</option></select></label>
    <p class="meta">Saved in this browser only.</p><div><button class="btn primary" id="save">Save</button></div></section>`;
  $("#save").addEventListener("click", () => { store.set("settings", { name: $("#name").value.trim(), method: $("#method").value }); toast("Saved."); });
}

/* ---------- router ---------- */
async function route() {
  const [path, query] = (location.hash.slice(1) || "/home").split("?");
  const params = new URLSearchParams(query || "");
  const parts = path.split("/").filter(Boolean);
  if (parts[0] !== "practice" && mic.stream) closeMic();
  try {
    switch (parts[0]) {
      case "practice": await viewPractice(params); break;
      case "report": await viewReport(parts[1]); break;
      case "reports": viewReports(); break;
      case "passages": await viewPassages(); break;
      case "demo": await viewDemo(); break;
      case "evidence": await viewEvidence(); break;
      case "dataset": await viewDataset(); break;
      case "settings": viewSettings(); break;
      default: await viewHome();
    }
  } catch (e) { main.innerHTML = `<div class="errbar">Something went wrong: ${esc(e.message)}</div>`; }
  main.focus({ preventScroll: true });
  window.scrollTo(0, 0);
}
window.addEventListener("hashchange", route);
loadTexts().catch(() => {}).finally(route);
