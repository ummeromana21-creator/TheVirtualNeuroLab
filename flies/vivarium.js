// Vivarium: Fly. Choose what she senses, watch what she does, see the brain activity behind it.
import * as T from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { loadFly } from './body/fly_body.js?v=1';
const $ = id => document.getElementById(id);
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const f1 = x => (Math.round(x * 10) / 10).toLocaleString('en-US');
const [B, R1, SPARK] = await Promise.all([fetch('behaviour.json?v=3').then(r => r.json()), fetch('../experiments/round1.json?v=1').then(r => r.json()),
  fetch('../experiments/bench_narration.json?v=1').then(r => r.ok ? r.json() : null).catch(() => null)]);
const REG = new Uint8Array(await (await fetch('regions.bin?v=1')).arrayBuffer());
const POS = new Float32Array(await (await fetch('../anatomy/celltypes/positions.bin')).arrayBuffer());
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const RN = Object.fromEntries(B.regions.map(r => [r.code, r]));
const RIDX = Object.fromEntries(B.regions.map((r, i) => [r.code, i + 1]));

// ---------- trust strip ----------
const cal = R1.calibration;
$('trustTxt').innerHTML = `The FlyWire brain ${cal.passed ? '<b>passed its calibration test</b>' : 'did not pass its calibration test'} and matched
  <b>${R1.totals.matched} of ${R1.totals.total}</b> results already known from real flies, with nothing adjusted to pass.`;

// ---------- the body ----------
function makeRenderer(el, clear) { const r = new T.WebGLRenderer({ antialias: true, alpha: clear == null }); r.setPixelRatio(Math.min(2, devicePixelRatio));
  if (clear != null) r.setClearColor(clear); el.prepend(r.domElement); return r; }
const bv = $('bodyView'), br = makeRenderer(bv); br.toneMapping = T.ACESFilmicToneMapping; br.toneMappingExposure = .9; br.shadowMap.enabled = true; br.shadowMap.type = T.PCFSoftShadowMap;
const bs = new T.Scene();
bs.add(new T.HemisphereLight(0xffffff, 0x6a5a46, .9));
const sun = new T.DirectionalLight(0xfff4e6, 1.7); sun.position.set(3, 7, 4); sun.castShadow = true; sun.shadow.mapSize.set(1024, 1024);
Object.assign(sun.shadow.camera, { left: -4, right: 4, top: 4, bottom: -4, near: .5, far: 20 }); bs.add(sun);
const fill = new T.DirectionalLight(0xc8dbff, .7); fill.position.set(-4, 2, -3); bs.add(fill);
const ground = new T.Mesh(new T.CircleGeometry(6, 64), new T.ShadowMaterial({ opacity: .18 })); ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; bs.add(ground);
const F = await loadFly(T, './body/');
const fly = new T.Group(); fly.add(F.root); fly.rotation.x = -Math.PI / 2; bs.add(fly);
const bb = new T.Box3().setFromObject(fly); fly.position.y = -bb.min.y;
const bc = new T.Box3().setFromObject(fly).getCenter(new T.Vector3());
fly.updateMatrixWorld(true); const head = F.parts['c_head'].getWorldPosition(new T.Vector3()); bc.lerp(head, .35);
const bcam = new T.PerspectiveCamera(30, 1, .05, 100); bcam.position.set(bc.x + 3.0, bc.y + 0.55, bc.z + 4.6);
const bctl = new OrbitControls(bcam, br.domElement); bctl.target.copy(bc); bctl.enableDamping = true; bctl.minDistance = 2; bctl.maxDistance = 14; bctl.enablePan = false;
const TONGUE = { 'c_head-c_rostrum-pitch': -0.9, 'c_rostrum-c_haustellum-pitch': -0.7 };
const GROOM = { 'c_thorax-lf_coxa-pitch': -0.4, 'c_thorax-lf_coxa-roll': -0.8, 'lf_coxa-lf_trochanterfemur-pitch': -0.8, 'lf_trochanterfemur-lf_tibia-pitch': 0.5,
  'c_thorax-rf_coxa-pitch': -0.4, 'c_thorax-rf_coxa-roll': -0.8, 'rf_coxa-rf_trochanterfemur-pitch': -0.8, 'rf_trochanterfemur-rf_tibia-pitch': 0.5, 'c_thorax-c_head-pitch': 0.15 };
let mode = { tongue: false, groom: false }, tMove = Infinity;
function bodyPose(t) {
  const a = {}; if (t < tMove) { F.pose(a); return; }
  const e = t - tMove;
  if (mode.tongue) { const k = reduce ? 1 : Math.min(1, Math.max(0, Math.sin(Math.PI * ((e * .55) % 1)) * 1.6)); for (const j in TONGUE) a[j] = TONGUE[j] * k; }
  if (mode.groom) { const k = Math.min(1, e * 1.5); for (const j in GROOM) a[j] = GROOM[j] * k;
    if (!reduce && k >= 1) { const w = Math.sin(e * 2 * Math.PI * 2.2), w2 = -w;
      a['lf_trochanterfemur-lf_tibia-pitch'] += .28 * w; a['rf_trochanterfemur-rf_tibia-pitch'] += .28 * w2;
      a['lf_coxa-lf_trochanterfemur-pitch'] += .12 * w2; a['rf_coxa-rf_trochanterfemur-pitch'] += .12 * w; } }
  F.pose(a);
}

// ---------- the brain ----------
const rv = $('brainView'), rr = makeRenderer(rv); const rs = new T.Scene();
const N = POS.length / 3, pa = new Float32Array(3 * N);
const V = (x, y, z) => new T.Vector3(x, -y, z);
const c0 = new T.Vector3(); for (let i = 0; i < N; i++) { pa[3 * i] = POS[3 * i]; pa[3 * i + 1] = -POS[3 * i + 1]; pa[3 * i + 2] = POS[3 * i + 2]; c0.x += pa[3 * i]; c0.y += pa[3 * i + 1]; c0.z += pa[3 * i + 2]; }
c0.multiplyScalar(1 / N);
const dot = (() => { const c = document.createElement('canvas'); c.width = c.height = 32; const g = c.getContext('2d'); const r = g.createRadialGradient(16, 16, 0, 16, 16, 16);
  r.addColorStop(0, 'rgba(255,255,255,1)'); r.addColorStop(.5, 'rgba(255,255,255,.6)'); r.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = r; g.fillRect(0, 0, 32, 32); return new T.CanvasTexture(c); })();
{ const g = new T.BufferGeometry(); g.setAttribute('position', new T.BufferAttribute(pa, 3));
  rs.add(new T.Points(g, new T.PointsMaterial({ size: 2.2, map: dot, color: 0x7d8a9b, transparent: true, opacity: .38, depthWrite: false }))); }
const layer = (size, order) => { const g = new T.BufferGeometry(); const p = new T.Points(g, new T.PointsMaterial({ size, map: dot, vertexColors: true, transparent: true, opacity: 0, depthWrite: false, depthTest: false }));
  p.renderOrder = order; rs.add(p); return p; };
const regPts = layer(6.5, 2), inPts = layer(10, 3), decPts = layer(44, 4);
const setPts = (p, idx, col) => { const a = new Float32Array(3 * idx.length), c = new Float32Array(3 * idx.length);
  idx.forEach((i, j) => { a.set([pa[3 * i], pa[3 * i + 1], pa[3 * i + 2]], 3 * j); c.set(typeof col === 'function' ? col(i, j) : col, 3 * j); });
  p.geometry.setAttribute('position', new T.BufferAttribute(a, 3)); p.geometry.setAttribute('color', new T.BufferAttribute(c, 3)); p.geometry.computeBoundingSphere(); };
const rcam = new T.PerspectiveCamera(32, 1, 1, 8000); rcam.position.set(c0.x, c0.y, c0.z + 950);
const rctl = new OrbitControls(rcam, rr.domElement); rctl.target.copy(c0); rctl.enableDamping = true; rctl.enablePan = false;
const ramp = f => { const s = [[.55, .7, .95], [0, .39, .88], [1, .6, .1], [.85, .2, .1]], x = Math.min(1, Math.max(0, f)) * 3, k = Math.min(2, Math.floor(x)), u = x - k;
  return s[k].map((v, j) => v + (s[k + 1][j] - v) * u); };
// hover: name the part of the brain under the pointer (a region, where the signal enters, or the deciding neuron)
const tip = document.createElement('div'); tip.className = 'tip'; tip.hidden = true; $('tags').appendChild(tip);
const centroid = idx => { const v = new T.Vector3(); idx.forEach(i => v.add(new T.Vector3(pa[3 * i], pa[3 * i + 1], pa[3 * i + 2]))); return v.multiplyScalar(1 / Math.max(1, idx.length)); };
const SAMPLE = []; for (let i = 0; i < N; i += 7) if (REG[i]) SAMPLE.push(i);
let hoverAt = null, keys = [];
rv.addEventListener('pointermove', e => { const r = rv.getBoundingClientRect(); hoverAt = [e.clientX - r.left, e.clientY - r.top]; });
rv.addEventListener('pointerleave', () => { hoverAt = null; tip.hidden = true; });
rv.addEventListener('click', () => { if (hovered && hovered.code) pick(hovered.code); });
let hovered = null;
const pv = new T.Vector3();
function hoverPick(w, h) {
  if (!hoverAt) return null; const [mx, my] = hoverAt;
  for (const k of keys) { if (!k.show()) continue; for (const i of k.idx) { pv.set(pa[3 * i], pa[3 * i + 1], pa[3 * i + 2]).project(rcam);
    if (Math.hypot((pv.x + 1) / 2 * w - mx, (1 - pv.y) / 2 * h - my) < k.r) return { html: k.html(), x: mx, y: my }; } }
  let best = 1e9, bi = -1;
  for (const i of SAMPLE) { pv.set(pa[3 * i], pa[3 * i + 1], pa[3 * i + 2]).project(rcam); const d = Math.hypot((pv.x + 1) / 2 * w - mx, (1 - pv.y) / 2 * h - my); if (d < best) { best = d; bi = i; } }
  if (best > 14) return null;
  const code = B.regions[REG[bi] - 1].code, r = RN[code], a = cur && cur.st.regions.find(x => x.code === code);
  return { code, x: mx, y: my, html: `<b>${esc(r.name)}</b>${r.role ? `<small>${esc(r.role)}</small>` : ''}<small>${a ? `${a.active} of ${r.total.toLocaleString('en-US')} neurons fired` : 'quiet in this run'}</small>` };
}

// ---------- choices ----------
const CH = [['Sugar', 's100_b0_w0'], ['Water', 's0_b0_w200'], ['Bitter', 's0_b200_w0'], ['Sugar + bitter', 's100_b200_w0'], ['Touch her antennae', 'touch'], ['Nothing', 's0_b0_w0']];
$('choose').insertAdjacentHTML('afterbegin', CH.map(([l, k]) => `<button class="c" data-k="${k}" aria-pressed="false">${l}</button>`).join(''));
const LV = { s: [0, 50, 100, 200], b: [0, 100, 200], w: [0, 200] }; const sel = { s: 100, b: 0, w: 0 };
document.querySelectorAll('.seg').forEach(seg => { const k = seg.dataset.k;
  seg.innerHTML = LV[k].map(v => `<button data-v="${v}" aria-pressed="false">${v === 0 ? 'none' : v}</button>`).join('');
  seg.addEventListener('click', ev => { const b = ev.target.closest('button'); if (!b) return; sel[k] = +b.dataset.v; run(`s${sel.s}_b${sel.b}_w${sel.w}`); }); });
$('choose').addEventListener('click', e => { const b = e.target.closest('button.c'); if (!b) return; const k = b.dataset.k;
  if (k !== 'touch') { const m = k.match(/s(\d+)_b(\d+)_w(\d+)/); Object.assign(sel, { s: +m[1], b: +m[2], w: +m[3] }); } run(k); });
$('adj').addEventListener('click', () => { const k = $('knobs'); k.hidden = !k.hidden; $('adj').setAttribute('aria-expanded', String(!k.hidden)); $('adj').textContent = k.hidden ? 'Adjust strengths' : 'Hide strengths'; });

// ---------- one run, in three beats: signal in → processing → decision (and then she moves) ----------
let cur = null, beatT0 = 0, picked = null;
function sentence(st, key) {
  const tastes = key === 'touch' ? [] : ['s', 'b', 'w'].filter(k => sel[k] > 0);
  if (st.groom) return 'She cleans her antennae with her front legs.';
  if (st.tongue) return sel.s > 0 ? 'She sticks out her tongue to feed.' : 'She sticks out her tongue to drink.';
  if (!tastes.length && key !== 'touch') return 'She does nothing: there is nothing to sense.';
  if (sel.b > 0 && (sel.s > 0 || sel.w > 0)) return 'She keeps her tongue in: she refuses.';
  return 'She keeps her tongue in.';
}
function run(key) {
  const st = B.stimuli.find(s => s.key === key); cur = { st, key };
  document.querySelectorAll('#choose button.c').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.k === key)));
  document.querySelectorAll('.seg').forEach(seg => seg.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', String(key !== 'touch' && +x.dataset.v === sel[seg.dataset.k]))));
  // inputs
  const inIdx = key === 'touch' ? B.inputs.touch : ['sugar', 'bitter', 'water'].filter(k => sel[k[0]] > 0).flatMap(k => B.inputs[k]);
  const inCol = { sugar: [.85, .55, .1], bitter: [.55, .4, .85], water: [.25, .55, .95], touch: [.06, .75, .62] };
  const roleOf = {}; for (const k of ['sugar', 'bitter', 'water', 'touch']) for (const i of B.inputs[k]) roleOf[i] = k;
  setPts(inPts, inIdx, i => inCol[key === 'touch' ? 'touch' : roleOf[i]]);
  // regions
  const mx = Math.max(1e-9, ...st.regions.map(r => r.frac)); const fr = new Float32Array(B.regions.length + 1);
  for (const r of st.regions) fr[RIDX[r.code]] = r.frac / mx;
  const ri = []; for (let i = 0; i < N; i++) if (REG[i] && fr[REG[i]] >= .04) ri.push(i);
  setPts(regPts, ri, i => ramp(.2 + .8 * fr[REG[i]]));
  // decision neuron
  const decIs = key === 'touch' ? 'abn1' : 'mn9', fires = key === 'touch' ? st.groom : st.tongue;
  setPts(decPts, B.deciders[decIs], fires ? [.96, .66, 0] : [.45, .5, .58]);
  // labels
  picked = null;
  keys = [
    { idx: B.deciders[decIs], r: 22, show: () => decPts.material.opacity > .5, html: () => decIs === 'mn9' ? `<b>Decision: MN9</b><small>the neuron that pushes the tongue out · ${f1(st.mn9)} firings/s (line: 10)</small>`
      : `<b>Decision: aBN1</b><small>the neuron that starts antennal grooming · ${f1(st.abn1)} firings/s (line: 5)</small>` },
    { idx: inIdx, r: 10, show: () => inIdx.length > 0, html: () => key === 'touch' ? '<b>Signal enters here</b><small>69 neurons that sense the antennae moving</small>' : '<b>Signal enters here</b><small>the taste neurons we switched on</small>' }];
  // beats text
  const regName = r => `${RN[r.code].name.toLowerCase()}${RN[r.code].role ? ` (${RN[r.code].role})` : ''}`;
  const parts = key === 'touch' ? '69 antenna neurons that sense the antennae being moved' :
    ['sugar', 'bitter', 'water'].filter(k => sel[k[0]] > 0).map(k => `${B.inputs[k].length} ${k}-taste neurons`).join(' and ');
  const beats = [
    ['#0f9d8a', inIdx.length ? `<b>Signal in.</b> We switch on ${parts}. That is all we do; the rest is the brain's own wiring.` : '<b>Signal in.</b> Nothing is switched on.'],
    ['#ffb547', st.active ? `<b>Processing.</b> ${st.active.toLocaleString('en-US')} of 139,255 neurons fire, mostly in the ${regName(st.regions[0])}.` : '<b>Processing.</b> No neurons fire.'],
    ['#1c2b33', decIs === 'mn9' ? `<b>Decision.</b> MN9, the neuron that pushes the tongue out, fires ${f1(st.mn9)} times a second: ${st.tongue ? 'above' : 'below'} the line of 10, so the tongue ${st.tongue ? 'comes out' : 'stays in'}.`
      : `<b>Decision.</b> aBN1, the neuron that starts antennal grooming, fires ${f1(st.abn1)} times a second: above the line of 5, so she grooms.`]];
  $('beats').innerHTML = beats.map(([c, t], j) => `<li data-j="${j}"><span class="k" style="background:${c}">${j + 1}</span><div>${t}</div></li>`).join('');
  // the verdict and why, under the fly
  $('verdict').textContent = ''; $('why').innerHTML = '';
  mode = { tongue: st.tongue, groom: st.groom };
  beatT0 = performance.now() / 1000; tMove = beatT0 + (reduce ? 0 : 2.4);
  const nb = key !== 'touch' && (sel.b > 0) ? B.stimuli.find(s => s.key === `s${sel.s}_b0_w${sel.w}`) : null;
  cur.why = key === 'touch' ? 'Moving her antennae switches on aBN1, the brain neuron that starts antennal grooming in real flies too.'
    : nb && (sel.s > 0 || sel.w > 0) ? (st.tongue ? `Bitter weakened the push on her tongue neuron (${f1(nb.mn9)} → ${f1(st.mn9)} per second) but didn't stop it.`
      : `Bitter overruled the sweet signal: her tongue neuron dropped from ${f1(nb.mn9)} to ${f1(st.mn9)} firings a second. Real flies refuse bitter food too.`)
    : sel.b > 0 ? 'Bitter on its own never tells the tongue to come out. Real flies behave the same way.'
    : st.tongue ? `Her tongue neuron, MN9, fired ${f1(st.mn9)} times a second; 10 or more brings the tongue out.` : !st.active ? '' : `Her tongue neuron fired ${f1(st.mn9)} times a second, below the line of 10.`;
  cur.sent = sentence(st, key);
  $('rinfo').textContent = 'Hover over the brain to name a part; click to keep its details here.';
}
function pick(code) {
  picked = picked === code ? null : code; const r = RN[code], a = cur && cur.st.regions.find(x => x.code === code);
  $('rinfo').innerHTML = picked ? `<b>${esc(r.name)}</b>${r.role ? `: ${esc(r.role)}` : ''}. ${a ? `${a.active} of its ${r.total.toLocaleString('en-US')} neurons fired.` : `None of its ${r.total.toLocaleString('en-US')} neurons fired.`}` : 'Hover over the brain to name a part; click to keep its details here.';
}
run('s100_b0_w0');

// ---------- Round 1 (inside "See the evidence") ----------
$('r1lead').textContent = `Pass marks written down ${R1.prereg.written.split(',')[0].replace('T', ' at ').replace('Z', ' UTC')}, before the runs. Each card shows what was already known from real flies, the pass mark, and what the simulated brain did.`;
$('score').innerHTML = `<span class="n">${R1.totals.matched} of ${R1.totals.total}</span><span class="lead" style="font-size:15px">real-fly results matched by the untouched brain wiring</span>`;
$('cards').innerHTML = R1.experiments.map(e => {
  const cls = e.matched === e.total ? 'b-ok' : e.matched === 0 ? 'b-miss' : 'b-mix';
  const word = e.matched === e.total ? 'Matches real flies' : e.matched === 0 ? 'Miss' : `Partly matches (${e.matched}/${e.total})`;
  return `<article class="card"><div class="top"><div><div class="id">${e.id}</div><h3>${e.title}</h3></div><span class="badge ${cls}">${word}</span></div>
    <div class="row"><span class="t">Already known from real flies</span>${e.real} <span style="color:var(--muted)">(${e.ref})</span></div>
    <div class="row"><span class="t">Pass mark (written before the run)</span>${e.rule}</div>
    <div class="row"><span class="t">What the simulated brain did</span><ul class="parts">${e.parts.map(p => `<li class="${p.ok ? 'y' : 'x'}"><b>${p.ok ? '✓' : '✗'}</b>${p.label}</li>`).join('')}</ul></div>
    ${e.note ? `<div class="row" style="font-size:13.5px;color:var(--muted)">${e.note}</div>` : ''}
    <div class="fp" title="${R1.fingerprint_note}">fingerprint ${R1.fingerprint}</div></article>`;
}).join('');
$('r1note').innerHTML = R1.note_html || '';
if (location.hash === '#r1' || location.hash === '#infer') { $('evidence').open = true; setTimeout(() => document.querySelector(location.hash).scrollIntoView(), 300); }

// ---------- render loop ----------
const tmp = new T.Vector3();
function fit(r, el, cam) { const w = el.clientWidth, h = el.clientHeight; if (r.domElement.width !== Math.round(w * r.getPixelRatio())) { r.setSize(w, h, false); cam.aspect = w / h; cam.updateProjectionMatrix(); } }
(function loop(now) {
  const t = now / 1000; fit(br, bv, bcam); fit(rr, rv, rcam);
  // beats: 0-0.8 s signal in, 0.8-2.4 s processing, 2.4 s decision, then she moves
  const e = reduce ? 99 : t - beatT0, beat = e < .8 ? 0 : e < 2.4 ? 1 : 2;
  inPts.material.opacity = Math.min(1, e / .4); regPts.material.opacity = Math.max(0, Math.min(1, (e - .8) / 1.2)); decPts.material.opacity = e >= 2.4 ? 1 : 0;
  document.querySelectorAll('#beats li').forEach(li => li.classList.toggle('on', +li.dataset.j <= beat));
  if (cur && e >= 2.4 && !$('verdict').textContent) { $('verdict').textContent = cur.sent; $('why').innerHTML = cur.why; }
  bodyPose(t); bctl.update(); rctl.update(); br.render(bs, bcam); rr.render(rs, rcam);
  const w = rv.clientWidth, h = rv.clientHeight;
  hovered = hoverPick(w, h);
  if (hovered) { tip.innerHTML = hovered.html; tip.style.left = hovered.x + 'px'; tip.style.top = hovered.y + 'px'; tip.hidden = false; rv.style.cursor = hovered.code ? 'pointer' : 'default'; }
  else { tip.hidden = true; rv.style.cursor = ''; }
  requestAnimationFrame(loop);
})(performance.now());
