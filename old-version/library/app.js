// Fly Atlas: filterable library + 3D point-cloud detail view.
import { siblings, sideName, ntSummary, ntFull, isCollapsed } from "../anatomy/celltype_logic.js?v=1";
const HUBS = ["all", "optic", "VNC", "lateral", "olfactory", "GNG", "CX", "senses", "celltypes", "subsets", "unassigned", "nowire"];
const SEXES = [["both", "F + M"], ["F", "Female"], ["M", "Male"]];
const state = { q: "", hub: "all", level: "all", sex: "both", sort: "syn" };
let DATA = [];
const PATH = { data: [], cent: {} };  // pathways.json + per-region centroids
const byName = n => DATA.find(e => e.name === n);
// Full neuropil names (Ito et al. 2014 brain nomenclature; Court et al. 2020
// VNC nomenclature). Plain-word names need no entry and display as-is.
const EXP = {
  CX: "Central complex", GNG: "Gnathal ganglia", VNC: "Ventral nerve cord",
  FB: "Fan-shaped body", EB: "Ellipsoid body", PB: "Protocerebral bridge",
  ATL: "Antler", NO: "Noduli", GA: "Gall", BU: "Bulb",
  VES: "Vest", FLA: "Flange", AMMC: "Antennal mechanosensory and motor center",
  PRW: "Prow", SAD: "Saddle", EPA: "Epaulette", GOR: "Gorget",
  MesoNm: "Mesothoracic neuromere", ProNm: "Prothoracic neuromere",
  MetaNm: "Metathoracic neuromere", IntTct: "Intermediate tectulum",
  HTct: "Haltere tectulum", WTct: "Wing tectulum",
  AMNp: "Accessory mesothoracic neuropil", NTct: "Neck tectulum",
  LTct: "Lower tectulum", mVAC: "Medial ventral association center", Ov: "Ovoid",
  AVLP: "Anterior ventrolateral protocerebrum", SPS: "Superior posterior slope",
  IPS: "Inferior posterior slope", PLP: "Posterior lateral protocerebrum",
  LAL: "Lateral accessory lobe", SMP: "Superior medial protocerebrum",
  CRE: "Crepine", ICL: "Inferior clamp", PVLP: "Posterior ventrolateral protocerebrum",
  WED: "Wedge", IB: "Inframedial bridge", SLP: "Superior lateral protocerebrum",
  SCL: "Superior clamp", AOTU: "Anterior optic tubercle",
  SIP: "Superior intermediate protocerebrum", CAN: "Cantle",
  AL: "Antennal lobe", LH: "Lateral horn", MB_CA: "Mushroom body calyx",
  MB_VL: "Mushroom body vertical lobe", MB_PED: "Mushroom body pedunculus",
  MB_ML: "Mushroom body medial lobe",
  ME: "Medulla", LO: "Lobula", LOP: "Lobula plate", AME: "Accessory medulla",
  LA: "Lamina",
  CB_UNASGD: "Central brain (unassigned)", OL_UNASGD: "Optic lobe (unassigned)",
  VNC_UNASGD: "VNC (unassigned)",
};
// Hub display names, matching the baked card-image headers
// ("optic · optic lobes (hub) · …"). Hubs show the full name only —
// the code already appears in the HUB chip.
const HUBNAME = {
  optic: "Optic lobes", VNC: "Ventral nerve cord",
  lateral: "Lateral / premotor zone", olfactory: "Smell centres",
  CX: "Central complex",  // GNG keeps "GNG - Gnathal ganglia" via EXP (anatomical term)
  unassigned: "Unassigned contacts", nowire: "Neurons with no wiring",
};
const dispName = e => {
  if (e.level === "hub" && HUBNAME[e.name]) return HUBNAME[e.name];
  const sm = e.level === "subset" && e.name.match(/^(.*) \(male (VNC|optic)\)$/);
  if (sm) {  // "ME_R (male optic)" -> "ME (right, male, Optic) - Medulla"
    const code = e.code || sm[1];
    const side = code.match(/^(.*)_([LR])$/);
    const base = side ? side[1] : code;
    const quals = [
      side ? (side[2] === "L" ? "left" : "right") : null,
      "male", sm[2] === "optic" ? "Optic" : sm[2],
    ].filter(Boolean).join(", ");
    return `${base} (${quals})${EXP[base] ? " - " + EXP[base] : ""}`;
  }
  const pretty = s => /^[a-z]/.test(s)
    ? s.replace(/[-_]/g, " ").replace(/^\w/, c => c.toUpperCase()) : s;  // visual-targets -> Visual targets
  const m = e.name.match(/^(.+)_([LR])$/);
  if (m) {
    const side = m[2] === "L" ? "left" : "right";
    if (EXP[m[1]]) return `${m[1]} (${side}) - ${EXP[m[1]]}`;
    if (e.level === "side") return `${pretty(m[1])} (${side})`;  // Abdomen_L, nerves_L
  }
  if (EXP[e.name]) return `${e.name} - ${EXP[e.name]}`;
  // Cell-type ids display verbatim (they are lookup keys: cLP02, vDeltaM…).
  return e.level === "celltype" ? e.name : pretty(e.name);
};
// Null-safe DOM helpers: a stale cached page must degrade, never whitescreen.
const $ = id => document.getElementById(id);
const on = (id, ev, fn) => $(id)?.addEventListener(ev, fn);
const click = (id, fn) => { const e = $(id); if (e) e.onclick = fn; };

const fmt = n => n == null ? "—" : n.toLocaleString("en-US");
const IMGV = "?v=2";  // bump when card art is re-rendered (covers rows + stills)
const hay = e => `${e.name} ${EXP[e.name] || ""} ${e.hub} ${e.cls || ""} ${e.sub || ""} ${e.func} ${e.desc} ${e.aliases || ""}`.toLowerCase();
function sortKey(e) {
  switch (state.sort) {
    case "fsyn": return -(e.fs || 0);
    case "msyn": return -(e.ms || 0);
    case "neu": return -((e.fn || 0) + (e.mn || 0));
    case "name": return e.name;
    case "ratio": return typeof e.ratio === "number" ? -e.ratio : 1e9;
    default: return -((e.fs || 0) + (e.ms || 0));
  }
}
const filtered = () => DATA
  .filter(e => state.hub === "all" || e.hub === state.hub)
  .filter(e => state.level === "all" || e.level === state.level)
  .filter(e => !state.q || hay(e).includes(state.q))
  .sort((a, b) => { const ka = sortKey(a), kb = sortKey(b); return ka < kb ? -1 : ka > kb ? 1 : 0; });

// ---------- library view ----------
function statMini(e) {
  const r = [];
  if (e.fn != null && state.sex !== "M") r.push(`<dt>F neurons</dt><dd>${fmt(e.fn)}</dd>`);
  if (e.mn != null && state.sex !== "F") r.push(`<dt>M neurons</dt><dd>${fmt(e.mn)}</dd>`);
  if (state.sex !== "M") r.push(`<dt>F synapses</dt><dd>${fmt(e.fs)}</dd>`);
  if (state.sex !== "F") r.push(`<dt>M synapses</dt><dd>${fmt(e.ms)}</dd>`);
  r.push(`<dt>M/F ratio</dt><dd>${e.ratio == null ? "—" : e.ratio}</dd>`);
  return r.join("");
}
function renderLibrary() {
  const list = filtered();
  const grid = $("grid");
  if (!grid) return;
  grid.innerHTML = list.length ? list.map(e => `
    <article class="card" data-name="${e.name}" tabindex="0" role="link" aria-label="${dispName(e)}, open detail view">
      <img src="${e.img}${IMGV}" alt="" loading="lazy" decoding="async">
      <div class="body">
        <div class="hd"><h2>${dispName(e)}</h2><span class="tag">${e.level === "hub" ? e.hub + " hub" : e.hub}</span></div>
        <p class="func">${e.func}</p>
        ${e.hub === "celltypes" ? `<p class="vsrc">counts: FlyWire v783</p>` : ""}
        <dl class="stats">${statMini(e)}</dl>
      </div>
    </article>`).join("")
    : `<p class="empty">No regions match these filters.</p>`;
  const count = $("count");
  if (count) count.textContent = `${list.length} of ${DATA.length} entries`;
  document.querySelectorAll("#hubs button").forEach(b => b.classList.toggle("on", b.dataset.v === state.hub));
  document.querySelectorAll("#sex button").forEach(b => b.classList.toggle("on", b.dataset.v === state.sex));
}

// ---------- 3D stage (lazy three.js) ----------
let T = null; // three module
const stage = {
  on: false, renderer: null, scene: null, camera: null, soma: null, lit: null,
  theta: 0.6, phi: 1.25, dist: 3.4, home: { theta: 0.6, phi: 1.25, dist: 3.4 },
  target: null, targetGoal: null, vel: { x: 0, y: 0 }, lastT: 0, idle: 0,
  closeup: false, centroid: null, raf: 0,
};
const SOMAC = {
  day: { optic: 0x2f5da3, central: 0x8a6d1a, sensory: 0x1e7d4f, visual_projection: 0x6a4fb3, descending: 0xb03a3a, ascending: 0xc26a8a, visual_centrifugal: 0x2a7f9e, motor: 0x555555, endocrine: 0x888888 },
  dusk: { optic: 0x4c9be8, central: 0xf2b134, sensory: 0x3ec28f, visual_projection: 0x9b7bea, descending: 0xef5b5b, ascending: 0xff8fb1, visual_centrifugal: 0x7fd4e8, motor: 0xffffff, endocrine: 0xc0c0c0 },
};
const HUBC = {
  day: { optic: 0x1d4ed8, VNC: 0xdc2626, lateral: 0x92400e, olfactory: 0x15803d, GNG: 0xc2410c, CX: 0x0f766e, senses: 0xb941a0, celltypes: 0x0e7490 },
  dusk: { optic: 0x7ab8ff, VNC: 0xff7a7a, lateral: 0xffd23f, olfactory: 0x7dffb6, GNG: 0xffb066, CX: 0x5ef2ff, senses: 0xd86fc0, celltypes: 0x22d3ee },
};
const theme = () => $("hero")?.dataset.light ?? "day";
async function buf(path) { return new Float32Array(await (await fetch(path)).arrayBuffer()); }
async function u8(path) { return new Uint8Array(await (await fetch(path)).arrayBuffer()); }

async function initGL() {
  T = await import("three");
  const canvas = document.getElementById("gl");
  stage.renderer = new T.WebGLRenderer({ canvas, antialias: true, alpha: true });
  stage.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  stage.scene = new T.Scene();
  stage.camera = new T.PerspectiveCamera(40, 1, 0.1, 100);
  stage.target = new T.Vector3(0, 0, 0);
  stage.targetGoal = new T.Vector3(0, 0, 0);
  // somas (flip y: FAFB +y runs down, three.js +y runs up)
  const P = await buf("points/somas.bin"), C = await u8("points/classes.bin");
  const idx = JSON.parse(await (await fetch("points/index.json")).text());
  for (let i = 1; i < P.length; i += 3) P[i] = -P[i];
  const g = new T.BufferGeometry();
  g.setAttribute("position", new T.BufferAttribute(P, 3));
  const col = new Float32Array(P.length), tmp = new T.Color();
  const cls = C, names = idx.classes;
  stage.paintSomas = () => {
    const pal = SOMAC[theme()];
    for (let i = 0; i < cls.length; i++) {
      tmp.setHex(pal[names[cls[i]]] ?? 0x888888);
      col[i * 3] = tmp.r; col[i * 3 + 1] = tmp.g; col[i * 3 + 2] = tmp.b;
    }
    g.attributes.color.needsUpdate = true;
  };
  g.setAttribute("color", new T.BufferAttribute(col, 3));
  stage.paintSomas();
  stage.soma = new T.Points(g, new T.PointsMaterial({ size: 0.012, vertexColors: true, transparent: true, opacity: 0.55, sizeAttenuation: true, depthWrite: false }));
  stage.soma.frustumCulled = false;
  stage.scene.add(stage.soma);
  stage.lit = new T.Points(new T.BufferGeometry(), new T.PointsMaterial({ size: 0.02, transparent: true, opacity: 0.95, sizeAttenuation: true, depthWrite: false }));
  stage.lit.frustumCulled = false;
  stage.lit.renderOrder = 2;
  stage.scene.add(stage.lit);
  stage.on = true;
  new ResizeObserver(fitGL).observe(document.getElementById("stage"));
  fitGL();
  stage.lastT = performance.now();
  const loop = t => {
    if (!stage.on) return;
    const dt = Math.min(0.05, (t - stage.lastT) / 1000);
    stage.lastT = t;
    step(dt, t / 1000);
    stage.renderer.render(stage.scene, stage.camera);
    stage.raf = requestAnimationFrame(loop);
  };
  stage.raf = requestAnimationFrame(loop);
}
function fitGL() {
  if (!stage.on) return;
  const el = document.getElementById("stage");
  const w = el.clientWidth, h = el.clientHeight;
  if (!w || !h) return;
  stage.renderer.setSize(w, h, false);
  stage.camera.aspect = w / h;
  stage.camera.updateProjectionMatrix();
}
function paintLit(hub) {
  if (stage.lit) stage.lit.material.color.setHex(HUBC[theme()][hub] ?? 0x4d5a3d);
}
async function setLit(entry) {
  // regions to light: neuropil itself, hub merges its brain members.
  // (Cell types never reach here: they get the embedded ortho viewer.)
  let regs = entry.level === "hub"
    ? DATA.filter(e => e.hub === entry.hub && e.level === "neuropil").map(e => e.name)
    : [entry.name];
  regs = regs.filter(r => !["VNC", "unassigned", "nowire"].includes(byName(r)?.hub));
  const per = Math.max(1500, Math.floor(30000 / Math.max(1, regs.length)));
  const parts = [];
  for (const r of regs) {
    try {
      let a = await buf(`points/${r}.bin`);
      if (a.length / 3 > per) {
        const n = a.length / 3, keep = new Float32Array(per * 3), step = n / per;
        for (let i = 0; i < per; i++) keep.set(a.subarray(Math.floor(i * step) * 3, Math.floor(i * step) * 3 + 3), i * 3);
        a = keep;
      }
      parts.push(a);
    } catch { /* region file absent: skip */ }
  }
  const n = parts.reduce((s, a) => s + a.length, 0);
  const merged = new Float32Array(n);
  let o = 0;
  for (const a of parts) { merged.set(a, o); o += a.length; }
  for (let i = 1; i < merged.length; i += 3) merged[i] = -merged[i];
  stage.lit.geometry.dispose();
  stage.lit.geometry = new T.BufferGeometry();
  stage.lit.geometry.setAttribute("position", new T.BufferAttribute(merged, 3));
  // centroid for close-up
  const c = new T.Vector3();
  for (let i = 0; i < merged.length; i += 3) c.x += merged[i], c.y += merged[i + 1], c.z += merged[i + 2];
  c.multiplyScalar(1 / Math.max(1, merged.length / 3));
  stage.centroid = c;
  paintLit(entry.hub);
  paintPaths();
}
async function paintPaths() {
  if (stage.paths) { stage.scene.remove(stage.paths); stage.paths.geometry.dispose(); stage.paths = null; }
  const on = PATH.show && PATH.data.length && !fallbackMode;
  if (!on) return;
  const top = PATH.data.filter(e => e.a !== e.b).slice(0, 30);
  const names = [...new Set(top.flatMap(e => [e.a, e.b]))].filter(n => !(n in PATH.cent));
  await Promise.all(names.map(async n => {
    try {
      const a = await buf(`points/${n}.bin`);
      let x = 0, y = 0, z = 0;
      for (let i = 0; i < a.length; i += 3) { x += a[i]; y -= a[i + 1]; z += a[i + 2]; }
      const k = Math.max(1, a.length / 3);
      PATH.cent[n] = [x / k, y / k, z / k];
    } catch { PATH.cent[n] = null; }
  }));
  const pos = [];
  for (const e of top) {
    const A = PATH.cent[e.a], B = PATH.cent[e.b];
    if (A && B) pos.push(...A, ...B);
  }
  if (!pos.length || !PATH.show || fallbackMode) return;
  const g = new T.BufferGeometry();
  g.setAttribute("position", new T.BufferAttribute(new Float32Array(pos), 3));
  stage.paths = new T.LineSegments(g, new T.LineBasicMaterial({ color: 0x0f766e, transparent: true, opacity: 0.45 }));
  stage.paths.userData.lit = true;
  stage.scene.add(stage.paths);
}
function step(dt, t) {
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  stage.idle += dt;
  if (stage.idle > 2 && !reduced && !stage.closeup) stage.theta += dt * 0.15 * Math.min(1, (stage.idle - 2) / 1.5);
  stage.theta += stage.vel.x * dt; stage.phi += stage.vel.y * dt;
  stage.vel.x *= Math.exp(-dt * 4.5); stage.vel.y *= Math.exp(-dt * 4.5);
  stage.phi = Math.min(Math.PI - 0.15, Math.max(0.15, stage.phi));
  stage.target.lerp(stage.targetGoal, 1 - Math.exp(-dt * 6));
  const sp = Math.sin(stage.phi), y = Math.cos(stage.phi);
  stage.camera.position.set(
    stage.target.x + stage.dist * sp * Math.sin(stage.theta),
    stage.target.y + stage.dist * y,
    stage.target.z + stage.dist * sp * Math.cos(stage.theta));
  stage.camera.lookAt(stage.target);
}
function zoomBy(f) {
  stage.dist = Math.min(8.5, Math.max(0.85, stage.dist / f));
  stage.closeup = stage.dist < 2.2;
  document.getElementById("closeup")?.setAttribute("aria-pressed", String(stage.closeup));
  stage.idle = 0;
}
function resetView() {
  Object.assign(stage, { theta: stage.home.theta, phi: stage.home.phi, dist: stage.home.dist });
  stage.targetGoal.set(0, 0, 0);
  stage.closeup = false;
  document.getElementById("closeup")?.setAttribute("aria-pressed", "false");
  stage.idle = 0;
}
function bindStage() {
  const el = $("stage");
  if (!el) return;
  let drag = null, pinch = 0, tap = null, tipTimer = 0;
  const tip = $("partTip");
  const ray = { c: null };
  const hideTip = () => { if (tip) tip.hidden = true; };
  // Hover the lit region cloud (the part on the card), not the dim somas.
  function partHit(cx, cy) {
    if (!stage.on || fallbackMode || !current || !T) return null;
    const r = el.getBoundingClientRect();
    if (!ray.c) { ray.c = new T.Raycaster(); ray.c.params.Points.threshold = 0.04; }
    ray.c.setFromCamera(new T.Vector2(((cx - r.left) / r.width) * 2 - 1, -((cy - r.top) / r.height) * 2 + 1), stage.camera);
    return ray.c.intersectObject(stage.lit, false).length ? current : null;
  }
  function moveTip(cx, cy, e) {
    if (!tip) return;
    const r = el.getBoundingClientRect();
    tip.textContent = `${dispName(e)} · ${e.func}`;
    tip.hidden = false;
    tip.style.left = "0px";
    tip.style.top = `${cy - r.top}px`;
    const w = tip.offsetWidth;
    let x = cx - r.left + 14;
    if (x + w > r.width - 6) x = cx - r.left - 14 - w;
    tip.style.left = `${x}px`;
  }
  el.addEventListener("pointerdown", e => {
    if (e.target.closest("#cellwrap")) return; // embedded cell viewer has its own controls
    if (e.pointerType === "mouse" && e.button !== 0) return;
    if (!e.target.closest("button")) tap = { x: e.clientX, y: e.clientY, t: performance.now() };
    else tap = null;
    el.setPointerCapture(e.pointerId);
    drag = { x: e.clientX, y: e.clientY, t: performance.now() };
    el.classList.add("grabbing");
    hideTip();
  });
  el.addEventListener("pointermove", e => {
    if (!drag) return;
    const k = 0.005;
    const dx = (e.clientX - drag.x) * k, dy = (e.clientY - drag.y) * k;
    stage.theta -= dx; stage.phi -= dy;
    stage.vel.x = -dx * 60; stage.vel.y = -dy * 60;
    drag = { x: e.clientX, y: e.clientY };
    stage.idle = 0;
    document.getElementById("hint").classList.add("gone");
  });
  const up = e => {
    drag = null; el.classList.remove("grabbing");
    // Tap (no hover on touch): name the part briefly.
    if (tap && e && e.type === "pointerup" && e.clientX !== undefined &&
        Math.hypot(e.clientX - tap.x, e.clientY - tap.y) < 8 &&
        performance.now() - tap.t < 350) {
      const hit = partHit(e.clientX, e.clientY);
      if (hit) {
        moveTip(e.clientX, e.clientY, hit);
        clearTimeout(tipTimer);
        tipTimer = setTimeout(hideTip, 1600);
      }
    }
    tap = null;
  };
  el.addEventListener("pointerup", up);
  el.addEventListener("pointercancel", up);
  el.addEventListener("pointermove", e => {
    if (e.pointerType === "touch") return;
    if (drag) { hideTip(); return; }
    const hit = partHit(e.clientX, e.clientY);
    if (hit) moveTip(e.clientX, e.clientY, hit);
    else hideTip();
  });
  el.addEventListener("pointerleave", e => { if (e.pointerType !== "touch") hideTip(); });
  el.addEventListener("wheel", e => {
    e.preventDefault();
    hideTip();
    zoomBy(Math.exp(-e.deltaY * (e.ctrlKey ? 0.01 : 0.0016)));
    document.getElementById("hint").classList.add("gone");
  }, { passive: false });
  el.addEventListener("touchmove", e => {
    if (e.touches.length === 2) {
      e.preventDefault();
      const d = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY);
      if (pinch) zoomBy(d / pinch);
      pinch = d;
    }
  }, { passive: false });
  el.addEventListener("touchend", () => pinch = 0);
  el.addEventListener("dblclick", () => { hideTip(); resetView(); });
  el.addEventListener("keydown", e => {
    if (!$("cellwrap").hidden) return; // cell viewer interprets its own keys via OrbitControls
    const rot = 0.18;
    if (e.key === "ArrowLeft") stage.theta += rot;
    else if (e.key === "ArrowRight") stage.theta -= rot;
    else if (e.key === "ArrowUp") stage.phi -= rot;
    else if (e.key === "ArrowDown") stage.phi += rot;
    else if (e.key === "+" || e.key === "=") zoomBy(1.2);
    else if (e.key === "-" || e.key === "_") zoomBy(1 / 1.2);
    else if (e.key === "0") resetView();
    else return;
    e.preventDefault(); stage.idle = 0; hideTip();
  });
  document.getElementById("zin").onclick = () => zoomBy(1.35);
  document.getElementById("zout").onclick = () => zoomBy(1 / 1.35);
  document.getElementById("zreset").onclick = resetView;
}

// ---------- embedded cell viewer (celltypes hub) ----------
// The full cell viewer lives here, in the detail stage — not a separate
// page. Ortho camera, exact scale bar, sides in teal/amber, click-to-Codex.
const CELL = {
  on: false, renderer: null, scene: null, camera: null, controls: null, OC: null,
  types: null, meta: null, names: [], pos: null, side: null, roots: null,
  bgPts: null, litPts: null, sibPts: null, dot: null,
  current: null, showSibs: false, halfH: 230,
  skel: null, skelLines: null, showSkel: true,
  wire: null, wireLines: null, showWire: false, showBrain: true,
};
const CODEX = id => `https://codex.flywire.ai/app/cell_details?root_id=${id}&dataset=fafb`;
const CELLC = {
  day: { bg: 0x9aa7b8, left: 0x0f766e, right: 0xb45309, grey: 0x64748b, sib: 0x334155, skel: 0x7c3aed, wire: 0x475569 },
  dusk: { bg: 0x2a3342, left: 0x14b8a6, right: 0xf59e0b, grey: 0x9fb3c8, sib: 0xe2e8f0, skel: 0xa78bfa, wire: 0x94a3b8 },
};
function cellPaint() {
  const pal = CELLC[theme()] || CELLC.day;
  if (CELL.bgPts) CELL.bgPts.material.color.setHex(pal.bg);
  if (CELL.sibPts) CELL.sibPts.material.color.setHex(pal.sib);
  if (CELL.skelLines) CELL.skelLines.material.color.setHex(pal.skel ?? pal.left);
  if (CELL.wireLines) CELL.wireLines.material.color.setHex(pal.wire ?? pal.grey);
  if (CELL.litPts && T) {
    const col = CELL.litPts.geometry.attributes.color, idx = CELL.litPts.geometry.userData.neurons;
    const c = new T.Color();
    idx.forEach((ni, k) => {
      c.setHex(CELL.side[ni] === 1 ? pal.left : CELL.side[ni] === 2 ? pal.right : pal.grey);
      col.setXYZ(k, c.r, c.g, c.b);
    });
    col.needsUpdate = true;
  }
}
function cellPos(i, out) {
  out[0] = CELL.pos[3 * i]; out[1] = -CELL.pos[3 * i + 1]; out[2] = CELL.pos[3 * i + 2];
  return out;
}
async function cellEnsure() {
  if (CELL.renderer) return;
  T = T || await import("three");
  CELL.OC = CELL.OC || (await import("three/addons/controls/OrbitControls.js")).OrbitControls;
  const wrap = $("cellgl");
  CELL.renderer = new T.WebGLRenderer({ antialias: true, alpha: true });
  CELL.renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
  wrap.appendChild(CELL.renderer.domElement);
  CELL.scene = new T.Scene(); // transparent: the Feather panel behind shows through
  CELL.camera = new T.OrthographicCamera(-1, 1, CELL.halfH, -CELL.halfH, -1500, 1500);
  CELL.camera.position.set(0, 0, -700);
  CELL.camera.up.set(0, 1, 0);
  CELL.camera.lookAt(0, 0, 0);
  cellBind();
  const c = document.createElement("canvas"); c.width = c.height = 32;
  const g = c.getContext("2d");
  const grad = g.createRadialGradient(16, 16, 0, 16, 16, 16);
  grad.addColorStop(0, "rgba(255,255,255,1)");
  grad.addColorStop(0.5, "rgba(255,255,255,.9)");
  grad.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = grad; g.fillRect(0, 0, 32, 32);
  CELL.dot = new T.CanvasTexture(c);
  document.querySelectorAll("#cellwrap [data-cv]").forEach(b => b.onclick = () => cellView(b.dataset.cv));
  new ResizeObserver(cellFit).observe(wrap);
  // click a lit dot -> root id + Codex link in the right card
  const ray = new T.Raycaster();
  ray.params.Points = { threshold: 3 };
  let downAt = null;
  CELL.renderer.domElement.addEventListener("pointerdown", e => { downAt = [e.clientX, e.clientY]; });
  CELL.renderer.domElement.addEventListener("pointerup", e => {
    if (!downAt || Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > 4) return;
    const r = CELL.renderer.domElement.getBoundingClientRect();
    ray.setFromCamera(new T.Vector2(
      ((e.clientX - r.left) / r.width) * 2 - 1,
      -((e.clientY - r.top) / r.height) * 2 + 1), CELL.camera);
    const hit = ray.intersectObjects([CELL.litPts, CELL.sibPts].filter(Boolean), false)[0];
    const box = document.getElementById("detail")?.querySelector(".clickline");
    if (!box) return;
    if (!hit) { box.textContent = "No dot there — try zooming in and clicking a lit dot."; return; }
    const ni = hit.object.userData.neurons[hit.index];
    const root = CELL.roots.getBigInt64(8 * ni, true).toString();
    const p = [CELL.pos[3 * ni], CELL.pos[3 * ni + 1], CELL.pos[3 * ni + 2]].map(v => v.toFixed(1)).join(", ");
    box.innerHTML = `root id ${root} · ${CELL.current}${hit.object.userData.sib ? " (related)" : ""} · ` +
      `${sideName(CELL.side[ni])} · (${p}) µm, centred<br><a href="${CODEX(root)}" target="_blank" rel="noopener">open in Codex</a>`;
  });
}
function cellBind() {
  const zoom = CELL.controls ? CELL.controls.zoom : 1;
  const spin = CELL.controls ? CELL.controls.autoRotate : false;
  if (CELL.controls) CELL.controls.dispose();
  CELL.controls = new CELL.OC(CELL.camera, CELL.renderer.domElement);
  CELL.controls.enableDamping = false;
  CELL.controls.minZoom = 0.5; CELL.controls.maxZoom = 10;
  CELL.controls.zoom = zoom;
  CELL.controls.autoRotate = spin;
  CELL.controls.addEventListener("change", cellScale);
}
async function cellLoad() {
  if (CELL.types) return;
  const [tj, pb, sb, rb] = await Promise.all([
    fetch("../anatomy/celltypes/types.json?v=1").then(r => { if (!r.ok) throw new Error("types.json " + r.status); return r.json(); }),
    buf("../anatomy/celltypes/positions.bin"),
    u8("../anatomy/celltypes/sides.bin"),
    (await fetch("../anatomy/celltypes/rootids.bin")).arrayBuffer().then(b => new DataView(b)),
  ]);
  CELL.meta = tj._meta; delete tj._meta;
  CELL.types = tj; CELL.names = Object.keys(tj);
  CELL.pos = pb; CELL.side = sb; CELL.roots = rb;
  const n = CELL.meta.n, arr = new Float32Array(3 * n), v = [0, 0, 0];
  for (let i = 0; i < n; i++) { cellPos(i, v); arr.set(v, 3 * i); }
  const g = new T.BufferGeometry();
  g.setAttribute("position", new T.BufferAttribute(arr, 3));
  CELL.bgPts = new T.Points(g, new T.PointsMaterial({
    size: 2, sizeAttenuation: false, map: CELL.dot, transparent: true,
    opacity: 0.55, color: (CELLC[theme()] || CELLC.day).bg, depthWrite: false,
  }));
  CELL.bgPts.frustumCulled = false;
  CELL.scene.add(CELL.bgPts);
}
function cellPoints(geom, size, color, opacity = 1) {
  const p = new T.Points(geom, new T.PointsMaterial({
    size, sizeAttenuation: false, map: CELL.dot, transparent: true, opacity,
    vertexColors: color === "v", color: color === "v" ? 0xffffff : color,
    depthWrite: false,
  }));
  p.frustumCulled = false;
  return p;
}
function cellScale() {
  const hPx = $("cellgl").clientHeight || 600;
  const umPerPx = (2 * CELL.halfH / CELL.controls.zoom) / hPx;
  document.querySelector("#cvscale .bar").style.width = `${100 / umPerPx}px`;
}
function cellFit() {
  if (!CELL.renderer) return;
  const w = $("cellgl").clientWidth, h = $("cellgl").clientHeight;
  if (!w || !h) return;
  CELL.renderer.setSize(w, h, false);
  const a = w / h;
  CELL.camera.left = -CELL.halfH * a; CELL.camera.right = CELL.halfH * a;
  CELL.camera.updateProjectionMatrix();
  cellScale();
}
function cellView(v) {
  document.querySelectorAll("#cellwrap [data-cv]").forEach(b =>
    b.setAttribute("aria-pressed", String(b.dataset.cv === v)));
  CELL.controls.autoRotate = v === "turn" ? !CELL.controls.autoRotate : false;
  if (v === "turn") {
    document.querySelector('#cellwrap [data-cv="turn"]')
      .setAttribute("aria-pressed", String(CELL.controls.autoRotate));
    return;
  }
  const D = 700;
  if (v === "front") { CELL.camera.up.set(0, 1, 0); CELL.camera.position.set(0, 0, -D); }
  if (v === "top") { CELL.camera.up.set(0, 0, -1); CELL.camera.position.set(0, D, 0); }
  if (v === "side") { CELL.camera.up.set(0, 1, 0); CELL.camera.position.set(-D, 0, 0); }
  CELL.controls.target.set(0, 0, 0);
  CELL.camera.lookAt(0, 0, 0);
  cellBind(); // OrbitControls snapshots camera.up; rebind after changing it
  CELL.controls.update();
}
function cellLit(idx) {
  const pal = CELLC[theme()] || CELLC.day;
  const arr = new Float32Array(3 * idx.length), col = new Float32Array(3 * idx.length);
  const v = [0, 0, 0], c = new T.Color();
  idx.forEach((ni, k) => {
    cellPos(ni, v); arr.set(v, 3 * k);
    c.setHex(CELL.side[ni] === 1 ? pal.left : CELL.side[ni] === 2 ? pal.right : pal.grey);
    col.set([c.r, c.g, c.b], 3 * k);
  });
  const g = new T.BufferGeometry();
  g.setAttribute("position", new T.BufferAttribute(arr, 3));
  g.setAttribute("color", new T.BufferAttribute(col, 3));
  g.userData.neurons = idx;
  return cellPoints(g, 3.5, "v");
}
function cellSibs(sibs) {
  if (CELL.sibPts) { CELL.scene.remove(CELL.sibPts); CELL.sibPts.geometry.dispose(); CELL.sibPts = null; }
  if (!CELL.showSibs || !sibs.length) return;
  const idx = sibs.flatMap(n => CELL.types[n].in_file ? CELL.types[n].indices : []);
  const arr = new Float32Array(3 * idx.length), v = [0, 0, 0];
  idx.forEach((ni, k) => { cellPos(ni, v); arr.set(v, 3 * k); });
  const g = new T.BufferGeometry();
  g.setAttribute("position", new T.BufferAttribute(arr, 3));
  g.userData.neurons = idx;
  g.userData.sib = true;
  CELL.sibPts = cellPoints(g, 3, (CELLC[theme()] || CELLC.day).sib, 0.85);
  CELL.scene.add(CELL.sibPts);
}
async function cellSkel(name) {
  // One traced shape per type, for the 25 most-studied types. 404 = none.
  try {
    const r = await fetch(`../anatomy/celltypes/skeletons/${encodeURIComponent(name)}.json?v=1`);
    if (!r.ok) return null;
    return await r.json();
  } catch { return null; }
}
function drawSkel() {
  if (CELL.skelLines) { CELL.scene.remove(CELL.skelLines); CELL.skelLines.geometry.dispose(); CELL.skelLines = null; }
  if (!CELL.skel || !CELL.showSkel) return;
  const { nodes, edges } = CELL.skel;
  const arr = new Float32Array(6 * edges.length);
  edges.forEach(([a, b], k) => {
    // same mapping as cellPos: (x, y, z) -> (x, -y, z)
    arr.set([nodes[a][0], -nodes[a][1], nodes[a][2]], 6 * k);
    arr.set([nodes[b][0], -nodes[b][1], nodes[b][2]], 6 * k + 3);
  });
  const g = new T.BufferGeometry();
  g.setAttribute("position", new T.BufferAttribute(arr, 3));
  CELL.skelLines = new T.LineSegments(g, new T.LineBasicMaterial({
    color: (CELLC[theme()] || CELLC.day).skel ?? 0x7c3aed,
    transparent: true, opacity: 0.9, depthWrite: false,
  }));
  CELL.skelLines.frustumCulled = false;
  CELL.scene.add(CELL.skelLines);
}
async function cellWire(name) {
  // Strongest 500 outgoing connections, one file per type. 404 = none.
  try {
    const r = await fetch(`../anatomy/celltypes/edges/${encodeURIComponent(name)}.json?v=1`);
    if (!r.ok) return null;
    return await r.json();
  } catch { return null; }
}
function drawWire() {
  if (CELL.wireLines) { CELL.scene.remove(CELL.wireLines); CELL.wireLines.geometry.dispose(); CELL.wireLines = null; }
  if (!CELL.wire || !CELL.showWire) return;
  const { edges } = CELL.wire;
  const arr = new Float32Array(6 * edges.length);
  edges.forEach(([a, b], k) => {
    const pa = CELL.pos[3 * a], pb = CELL.pos[3 * a + 1], pc = CELL.pos[3 * a + 2];
    const qa = CELL.pos[3 * b], qb = CELL.pos[3 * b + 1], qc = CELL.pos[3 * b + 2];
    if ([pa, pb, pc, qa, qb, qc].some(x => !Number.isFinite(x))) return;
    arr.set([pa, -pb, pc], 6 * k);
    arr.set([qa, -qb, qc], 6 * k + 3);
  });
  const g = new T.BufferGeometry();
  g.setAttribute("position", new T.BufferAttribute(arr, 3));
  CELL.wireLines = new T.LineSegments(g, new T.LineBasicMaterial({
    color: (CELLC[theme()] || CELLC.day).wire ?? 0x475569,
    transparent: true, opacity: 0.55, depthWrite: false,
  }));
  CELL.wireLines.frustumCulled = false;
  CELL.scene.add(CELL.wireLines);
}
function drawBrain() {
  if (CELL.bgPts) CELL.bgPts.visible = CELL.showBrain;
}
async function showCell(name) {
  await cellEnsure(); await cellLoad();
  const t = CELL.types[name];
  CELL.current = name;
  if (CELL.litPts) { CELL.scene.remove(CELL.litPts); CELL.litPts.geometry.dispose(); CELL.litPts = null; }
  if (t && t.in_file) { CELL.litPts = cellLit(t.indices); CELL.scene.add(CELL.litPts); }
  CELL.skel = t && t.in_file ? await cellSkel(name) : null;
  drawSkel();
  CELL.wire = t && t.in_file ? await cellWire(name) : null;
  drawWire(); drawBrain();
  cellSibs(siblings(CELL.names, name));
  CELL.renderer.setAnimationLoop(() => { CELL.controls.update(); CELL.renderer.render(CELL.scene, CELL.camera); });
  CELL.on = true;
  cellFit();
  fillCellPanel(byName(name));
}
function hideCell() {
  if (!CELL.on) return;
  CELL.renderer.setAnimationLoop(null);
  CELL.on = false;
}
function cellTypeSpan(idx) {
  let lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9];
  for (const ni of idx) for (let a = 0; a < 3; a++) {
    const p = CELL.pos[3 * ni + a];
    if (p < lo[a]) lo[a] = p; if (p > hi[a]) hi[a] = p;
  }
  return Math.hypot(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]);
}
const SIM_TYPES = { "R1-6": "photoreceptors", "R7": "photoreceptors", "R8": "photoreceptors", "ORN_V": "CO2 group" };
function cellSmallPrint(t, name, cls) {
  const b = CELL.meta.bbox_um;
  const span = [b[1][0] - b[0][0], b[1][1] - b[0][1], b[1][2] - b[0][2]].map(v => Math.round(v));
  const optic = cls === "optic_lobe_intrinsic" || cls === "visual";
  const rows = [
    `Dataset: FlyWire FAFB v783 — ${CELL.meta.n.toLocaleString("en-US")} neurons, one recorded point each (nm → µm).`,
    `Brain size from the data: about ${span[0]} × ${span[1]} × ${span[2]} µm (left–right × dorsal–ventral × anterior–posterior).`,
    `Front view: the fly faces you, dorsal side up. A dot is a point on the cell, not its shape.`,
    `Type label: ${name} from the Codex cell-type column` + (optic ? ` (optic-lobe types after Matsliah, Yu et al. 2024 and Schlegel et al. 2024)` : ``) + `.`,
    t.in_file
      ? `${name}: ${t.n.toLocaleString("en-US")} neurons (${t.left} left, ${t.right} right). Predicted transmitters: ${ntFull(t.nt)}.`
      : `${name} is not in the FlyWire file (${t.reason}); no dots, counts from the atlas sheet.`,
    ...(CELL.skel && CELL.current === name
      ? [`Traced shape: one ${name} neuron (root id ${CELL.skel.root_id}, ${CELL.skel.n_kept} branch points from ${CELL.skel.n_full.toLocaleString("en-US")} traced points, FlyWire LOD1 healed). One cell's shape, not the whole type.`]
      : []),
    ...(CELL.wire && CELL.current === name
      ? [`Wiring: strongest ${CELL.wire.edges.length} of ${CELL.wire.n_out_full.toLocaleString("en-US")} outgoing connections, by weight (FlyWire v783). Capped for speed; toggle above.`]
      : []),
    `Positions: FlyWire (Dorkenwald et al. 2024; Schlegel et al. 2024) via Codex (Matsliah et al. 2023). Transmitters predicted (Eckstein, Bates et al. 2024).`,
    SIM_TYPES[name]
      ? `Simulated? Yes — as part of the sim's ${SIM_TYPES[name]}.`
      : `Simulated? No. Anatomy only. Nothing here comes from the simulation.`,
  ];
  return `<details class="fine"><summary>Data sources</summary>${rows.map(r => `<p>${r}</p>`).join("")}</details>`;
}
function fillCellPanel(e) {
  const t = CELL.types[e.name];
  const detail = document.getElementById("detail");
  if (!t || !t.in_file) {
    detail.insertAdjacentHTML("beforeend",
      `<p>${!t ? "Not one of the 236 atlas cell types." : "Absent from the FlyWire file: " + t.reason + "."}</p>` +
      (t ? cellSmallPrint(t, e.name, e.cls) : ""));
    return;
  }
  const sibs = siblings(CELL.names, e.name);
  const known = Object.entries(t.nt).filter(([k]) => k !== "unknown").sort((a, b) => b[1] - a[1]);
  const tot = known.reduce((a, [, v]) => a + v, 0);
  const b = CELL.meta.bbox_um;
  const collapsed = isCollapsed(cellTypeSpan(t.indices),
    Math.hypot(b[1][0] - b[0][0], b[1][1] - b[0][1], b[1][2] - b[0][2]), t.n);
  detail.insertAdjacentHTML("beforeend", `
    <h2>Left / right</h2>
    <div class="traits">
      ${traitRow('<span class="sw" style="background:#14b8a6"></span>Left', fmt(t.left))}
      ${traitRow('<span class="sw" style="background:#f59e0b"></span>Right', fmt(t.right))}
      ${traitRow("Transmitter", ntSummary(t.nt, t.n).text)}
    </div>
    ${known.map(([k, v]) => `<div class="ntsub">${k}: ${v.toLocaleString("en-US")} (${Math.round(100 * v / tot)}% of predicted)</div>`).join("")}
    ${collapsed ? `<p class="fine">These dots sit close together because each dot is the type's recorded point inside its shared neuropil, not the cell body's shape.</p>` : ""}
    ${sibs.length ? `<div class="sibline"><label><input type="checkbox" class="sibtoggle" ${CELL.showSibs ? "checked" : ""}> Show related by name, not by wiring: ${sibs.join(", ")}</label></div>` : ""}
    ${CELL.skel ? `<div class="sibline"><label><input type="checkbox" class="skeltoggle" ${CELL.showSkel ? "checked" : ""}> Show one traced shape (root id ${CELL.skel.root_id})</label></div>` : ""}
    ${CELL.wire ? `<div class="sibline"><label><input type="checkbox" class="wiretoggle" ${CELL.showWire ? "checked" : ""}> Show their wiring (strongest ${CELL.wire.edges.length} of ${CELL.wire.n_out_full.toLocaleString("en-US")} outgoing connections)</label></div>` : ""}
    <div class="sibline"><label><input type="checkbox" class="braintoggle" ${CELL.showBrain ? "checked" : ""}> Show the whole brain (${CELL.meta.n.toLocaleString("en-US")} dimmed neurons)</label></div>
    <p class="clickline">Click a lit dot for its root id and Codex link.</p>
    ${cellSmallPrint(t, e.name, e.cls)}`);
  const tg = detail.querySelector(".sibtoggle");
  if (tg) tg.onchange = () => { CELL.showSibs = tg.checked; cellSibs(sibs); };
  const sk = detail.querySelector(".skeltoggle");
  if (sk) sk.onchange = () => { CELL.showSkel = sk.checked; drawSkel(); };
  const wr = detail.querySelector(".wiretoggle");
  if (wr) wr.onchange = () => { CELL.showWire = wr.checked; drawWire(); };
  const br = detail.querySelector(".braintoggle");
  if (br) br.onchange = () => { CELL.showBrain = br.checked; drawBrain(); };
}

// ---------- detail view ----------
let current = null, sibs = [];
const pillFor = e => e.level === "hub"
  ? [e.hub + " hub", `${DATA.filter(x => x.hub === e.hub && x.level === "neuropil").length} regions`, e.func]
  : e.level === "celltype"
  ? [e.cls || "unclassified", e.flow || "", e.func].filter(Boolean)
  : [e.hub, e.level, e.func];
function traitRow(k, v) { return `<div class="trait"><span class="k">${k}</span><span class="v">${v}</span></div>`; }
const SIM_GROUPS = { AL: "antennal lobe PNs", LH: "lateral horn", EB: "central complex", FB: "central complex", PB: "central complex", NO: "central complex", ME: "optic lobes", LO: "optic lobes", LOP: "optic lobes", LA: "optic lobes", AME: "optic lobes", MB_CA: "mushroom body", MB_ML: "mushroom body", MB_PED: "mushroom body", MB_VL: "mushroom body" };
function regionSmallPrint(e) {
  const rows = [];
  if (e.level === "subset") {
    rows.push(`Dataset: male-only file (${e.name.includes("optic") ? "Male Fly Optic Nerve" : "Male Fly Connectome"}); no female counterpart.`);
    rows.push(`Positions: none — counts only, so the picture shows the group, not this split.`);
    rows.push(`Simulated? No. Subsets are not modeled; the sim runs on the full connectomes.`);
  } else {
    const base = e.level === "side" ? e.base : e.name;
    rows.push(`Dataset: BANC female brain and Male CNS male brain, Codex exports (Dorkenwald et al. 2024; Schlegel et al. 2024).`);
    rows.push(`Positions: 3D dots from recorded soma positions, binned per region; perspective stage, drag to turn, scroll to zoom.`);
    rows.push(`Region label: ${base} from the ${e.hub} sheet (row ${e.row}).`);
    if (e.level === "side") rows.push(`Side: the ${e.name.endsWith("_L") ? "left" : "right"} half; the 3D view renders the full ${e.base}.`);
    const g = e.level === "hub" ? null : SIM_GROUPS[base];
    rows.push(g
      ? `Simulated? Yes — fires in every run, measured live as firing.${g}.`
      : `Simulated? Yes — its neurons fire in every run as part of the whole-brain network.`);
  }
  return `<details class="fine"><summary>Data sources</summary>${rows.map(r => `<p>${r}</p>`).join("")}</details>`;
}
function renderDetail(e) {
  current = e;
  const sibEntries = e.level === "celltype" && e.cls
    ? DATA.filter(x => x.cls === e.cls)
    : e.level === "side"
    ? DATA.filter(x => x.name === e.base || x.name === e.base + "_L" || x.name === e.base + "_R")
    : DATA.filter(x => x.hub === e.hub);
  sibs = sibEntries.map(x => x.name);
  document.getElementById("sibNav").innerHTML =
    `<span class="cap">${e.level === "celltype" ? e.cls : e.level === "side" ? e.base : e.hub} · ${sibEntries.length}</span>` + sibEntries.map(x =>
      `<button data-n="${x.name}" class="${x.name === e.name ? "on" : ""}">${dispName(x)}<small>${x.func}</small></button>`).join("");
  const neurons = e.fn != null || e.mn != null;
  document.getElementById("detail").innerHTML = `
    <span class="eyebrow">${e.hub}${e.level === "hub" ? " · hub" : ""}</span>
    <h1>${dispName(e)}</h1>
    <div class="pills">${pillFor(e).map(p => `<span>${p}</span>`).join("")}</div>
    <p class="desc">${e.desc}</p>
    <h2>Key numbers</h2>
    <div class="traits">
      ${neurons ? traitRow("Female neurons", fmt(e.fn)) + traitRow("Male neurons", fmt(e.mn)) : ""}
      ${traitRow("Female synapses", fmt(e.fs))}${traitRow("Male synapses", fmt(e.ms))}
      ${traitRow("M/F ratio", e.ratio == null ? "—" : e.ratio)}
    </div>
    <button class="closeup" id="closeup" aria-pressed="false">
      <span><span class="t">Close-up Detail</span><span class="d" style="display:block">${e.level === "hub" ? "Zoom to every region in this hub" : e.level === "sense" ? "Zoom to this group in 3D" : "Zoom to this region in 3D"}</span></span>
      <svg class="ic"><use href="#i-chev"/></svg>
    </button>
    <button class="closeup" id="pathways" aria-pressed="false">
      <span><span class="t">Pathways</span><span class="d" style="display:block">Draw the 30 strongest between-region wires</span></span>
      <svg class="ic"><use href="#i-chev"/></svg>
    </button>
    <a class="asklink" href="../study.html?q=${encodeURIComponent("what does " + e.name + " do (" + e.func + ")")}&region=${encodeURIComponent(e.row)}&level=${encodeURIComponent(e.level)}">Ask about this region</a>
    ${e.level === "celltype" ? "" : regionSmallPrint(e)}`;
  document.getElementById("caption").textContent = e.func;
  document.getElementById("closeup").onclick = () => {
    if (!stage.on || fallbackMode) return;
    if (stage.closeup) { resetView(); return; }
    if (stage.centroid) stage.targetGoal.copy(stage.centroid);
    stage.dist = 1.4;
    stage.closeup = true;
    document.getElementById("closeup").setAttribute("aria-pressed", "true");
    stage.idle = 0;
  };
  document.getElementById("pathways").onclick = () => {
    if (!stage.on || fallbackMode) return;
    PATH.show = !PATH.show;
    document.getElementById("pathways").setAttribute("aria-pressed", String(!!PATH.show));
    stage.idle = 0;
    paintPaths();
  };
}
let fallbackMode = false;
async function openDetail(name, push = true) {
  const e = byName(name);
  if (!e || !$("detailView")) return;
  if (current && current.name === name) return; // hash echo of our own navigation: skip double load
  fallbackMode = ["VNC", "unassigned", "nowire", "subsets"].includes(e.hub) || e.level === "side";
  const isCell = e.hub === "celltypes"; // embedded ortho viewer, not the perspective stage
  hideCell();
  if ($("libraryView")) $("libraryView").hidden = true;
  $("detailView").hidden = false;
  if ($("partTip")) $("partTip").hidden = true;
  renderDetail(e);
  document.getElementById("fallback").hidden = true;
  document.getElementById("gl").style.display = (fallbackMode || isCell) ? "none" : "block";
  document.querySelector("#stage .rail").style.display = isCell ? "none" : "";
  document.getElementById("hint").style.display = isCell ? "none" : "";
  $("cellwrap").hidden = !isCell;
  if (isCell) {
    document.getElementById("closeup").style.display = "none";
    document.getElementById("pathways").style.display = "none";
    document.getElementById("loader").hidden = false;
    try {
      await showCell(e.name);
    } catch (err) {
      $("cellwrap").hidden = true; // positions failed: still render instead
      const fb = document.getElementById("fallback");
      fb.src = e.img + IMGV; fb.alt = `${e.name} render`;
      fb.hidden = false;
      document.getElementById("caption").textContent = "Cell positions failed to load — still render below";
    }
    document.getElementById("loader").hidden = true;
  } else if (fallbackMode) {
    const fb = document.getElementById("fallback");
    fb.src = e.img + IMGV; fb.alt = `${e.name} render`;
    fb.hidden = false;
    document.getElementById("caption").textContent =
      e.level === "side" ? "Side counts — render shows the whole region" :
      e.level === "subset" ? "Male-only subset file — counts only, no 3D position" :
      e.hub === "VNC" ? `${e.func} — schematic drawing, no cord coordinates` :
      e.hub === "nowire" ? "Absent from the wiring files — nothing to show" :
      "Scattered contacts with no consensus position";
    document.getElementById("closeup").style.display = "none";
    document.getElementById("pathways").style.display = "";
  } else {
    document.getElementById("closeup").style.display = "";
    document.getElementById("pathways").style.display = "";
    document.getElementById("loader").hidden = false;
    try {
      if (!stage.on) await initGL();
      resetView();
      await setLit(e);
      fitGL();
    } catch (err) {
      document.getElementById("gl").style.display = "none"; // 3D failed: still render + reason, never a hung loader
      const fb = document.getElementById("fallback");
      fb.src = e.img + IMGV; fb.alt = `${e.name} render`;
      fb.hidden = false;
      document.getElementById("caption").textContent = "3D failed to load (" + (err && err.message ? err.message : "unknown error") + ") — still render below";
    }
    document.getElementById("loader").hidden = true;
  }
  if (push) location.hash = "/" + encodeURIComponent(name);
  window.scrollTo(0, 0);
}
function closeDetail(push = true) {
  hideCell();
  if ($("detailView")) $("detailView").hidden = true;
  if ($("libraryView")) $("libraryView").hidden = false;
  if ($("partTip")) $("partTip").hidden = true;
  current = null;
  if (push) location.hash = "";
}
function stepDetail(d) {
  if (!current) return;
  const i = sibs.indexOf(current.name);
  openDetail(sibs[(i + d + sibs.length) % sibs.length]);
}

// ---------- boot ----------
// NOTE: no Feather.topbar here — the site bar in #navMount already carries the
// hubs. .top stays a slim toolbar (title + search + filter + light).
Feather.init({ onLight: () => { if (stage.on) { stage.paintSomas(); if (current) paintLit(current.hub); } if (CELL.renderer) cellPaint(); } });
Promise.all([fetch("data.json").then(r => r.json()), fetch("celltypes.json?v=1").then(r => r.json()).catch(() => []), fetch("sides.json").then(r => r.json()).catch(() => []), fetch("subsets.json").then(r => r.json()).catch(() => []), fetch("sensegroups.json").then(r => r.json()).catch(() => []), fetch("pathways.json").then(r => r.json()).catch(() => [])]).then(([d, ct, sd, ss, sg, pw]) => {
  DATA = d.concat(ct, sd, ss, sg);
  PATH.data = pw;
  const f = d.filter(e => e.level === "hub").reduce((s, e) => s + (e.fs || 0), 0);
  const m = d.filter(e => e.level === "hub").reduce((s, e) => s + (e.ms || 0), 0);
  const sub = document.querySelector("#libraryView #sub");
  if (sub) sub.textContent =
    `${d.length} hubs and neuropils + ${ct.length} cell types + ${sd.length} sides + ${ss.length} subsets + ${sg.length} sense groups · ${(f / 1e6).toFixed(1)}M female + ${(m / 1e6).toFixed(1)}M male synapses`;
  if ($("hubs")) $("hubs").innerHTML =
    HUBS.map(h => `<button data-v="${h}">${h === "all" ? "All" : h}</button>`).join("");
  if ($("sex")) $("sex").innerHTML =
    SEXES.map(([v, l]) => `<button data-v="${v}">${l}</button>`).join("");
  on("q", "input", e => { state.q = e.target.value.toLowerCase(); renderLibrary(); });
  on("level", "change", e => { state.level = e.target.value; renderLibrary(); });
  on("sort", "change", e => { state.sort = e.target.value; renderLibrary(); });
  on("hubs", "click", e => { if (e.target.dataset.v) { state.hub = e.target.dataset.v; renderLibrary(); } });
  on("sex", "click", e => { if (e.target.dataset.v) { state.sex = e.target.dataset.v; renderLibrary(); } });
  on("grid", "click", e => {
    const c = e.target.closest(".card");
    if (c) openDetail(c.dataset.name);
  });
  on("grid", "keydown", e => {
    const c = e.target.closest(".card");
    if (c && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); openDetail(c.dataset.name); }
  });
  click("filterBtn", () => $("filterPanel")?.classList.toggle("hidden"));
  if (matchMedia("(max-width: 760px)").matches) $("filterPanel")?.classList.add("hidden");
  click("backBtn", () => closeDetail());
  click("prevBtn", () => stepDetail(-1));
  click("nextBtn", () => stepDetail(1));
  on("sibNav", "click", e => {
    const b = e.target.closest("button");
    if (b) openDetail(b.dataset.n);
  });
  bindStage();
  renderLibrary();
  const open = () => {
    const m = location.hash.match(/^#\/(.+)$/);
    if (m && byName(decodeURIComponent(m[1]))) openDetail(decodeURIComponent(m[1]), false);
    else if (!location.hash) closeDetail(false);
  };
  addEventListener("hashchange", open);
  open();
});
