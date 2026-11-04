// Vivarium: Fly. Body (NeuroMechFly), brain-region activity (FlyWire), behaviours read from the brain, and Round 1.
import * as T from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { loadFly } from './body/fly_body.js?v=1';
const $ = id => document.getElementById(id);
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const f1 = x => (Math.round(x * 10) / 10).toLocaleString('en-US');
const [B, R1, BENCH, SPARK] = await Promise.all([fetch('behaviour.json?v=2').then(r => r.json()), fetch('../experiments/round1.json?v=1').then(r => r.json()),
  fetch('../experiments/bench.json?v=1').then(r => r.json()), fetch('../experiments/bench_narration.json?v=1').then(r => r.ok ? r.json() : null).catch(() => null)]);
const REG = new Uint8Array(await (await fetch('regions.bin?v=1')).arrayBuffer());
const POS = new Float32Array(await (await fetch('../anatomy/celltypes/positions.bin')).arrayBuffer());
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const RN = Object.fromEntries(B.regions.map(r => [r.code, r]));

// ---------- calibration status ----------
const cal = R1.calibration;
$('status').innerHTML = `<a class="st ${cal.passed ? 'ok' : 'no'}" href="#r1"><span class="dot"></span><div><b>FlyWire brain · ${cal.passed ? 'calibrated ✓' : 'did not pass calibration'}</b>
  <span>Sugar → MN9 ${f1(cal.mn9.sugar_100)}/s, bitter alone ${f1(cal.mn9.bitter_200)}/s, bitter + sugar ${f1(cal.mn9.sugar_100_bitter_200)}/s;
  ${cal.active.sugar_100} neurons fired. All calibration rules met: ${Object.values(cal.criteria).every(Boolean) ? 'yes' : 'no'}.</span></div></a>`;

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
// behaviours, as angles on NeuroMechFly's own joints. Tongue out: the proboscis segments unfold. Grooming: both front legs reach the antennae and sweep.
const TONGUE = { 'c_head-c_rostrum-pitch': -0.9, 'c_rostrum-c_haustellum-pitch': -0.7 };
const GROOM = { 'c_thorax-lf_coxa-pitch': -0.4, 'c_thorax-lf_coxa-roll': -0.8, 'lf_coxa-lf_trochanterfemur-pitch': -0.8, 'lf_trochanterfemur-lf_tibia-pitch': 0.5,
  'c_thorax-rf_coxa-pitch': -0.4, 'c_thorax-rf_coxa-roll': -0.8, 'rf_coxa-rf_trochanterfemur-pitch': -0.8, 'rf_trochanterfemur-rf_tibia-pitch': 0.5, 'c_thorax-c_head-pitch': 0.15 };
let mode = { tongue: false, groom: false }, tMode = 0;
function bodyPose(t) {
  const a = {};
  if (mode.tongue) { const k = reduce ? 1 : Math.min(1, Math.max(0, Math.sin(Math.PI * ((t * .55) % 1)) * 1.6)); for (const j in TONGUE) a[j] = TONGUE[j] * k; }
  if (mode.groom) { const k = Math.min(1, (t - tMode) * 1.5);
    for (const j in GROOM) a[j] = GROOM[j] * k;
    if (!reduce && k >= 1) { const w = Math.sin(t * 2 * Math.PI * 2.2), w2 = Math.sin(t * 2 * Math.PI * 2.2 + Math.PI);
      a['lf_trochanterfemur-lf_tibia-pitch'] += .28 * w; a['rf_trochanterfemur-rf_tibia-pitch'] += .28 * w2;
      a['lf_coxa-lf_trochanterfemur-pitch'] += .12 * w2; a['rf_coxa-rf_trochanterfemur-pitch'] += .12 * w; } }
  F.pose(a);
}

// ---------- the brain: the whole brain in grey, the regions that responded in colour ----------
const rv = $('brainView'), rr = makeRenderer(rv, 0x101318); const rs = new T.Scene();
const N = POS.length / 3, pa = new Float32Array(3 * N);
const c0 = new T.Vector3(); for (let i = 0; i < N; i++) { pa[3 * i] = POS[3 * i]; pa[3 * i + 1] = -POS[3 * i + 1]; pa[3 * i + 2] = POS[3 * i + 2]; c0.x += pa[3 * i]; c0.y += pa[3 * i + 1]; c0.z += pa[3 * i + 2]; }
c0.multiplyScalar(1 / N);
const pg = new T.BufferGeometry(); pg.setAttribute('position', new T.BufferAttribute(pa, 3));
const dot = (() => { const c = document.createElement('canvas'); c.width = c.height = 32; const g = c.getContext('2d'); const r = g.createRadialGradient(16, 16, 0, 16, 16, 16);
  r.addColorStop(0, 'rgba(255,255,255,1)'); r.addColorStop(.5, 'rgba(255,255,255,.6)'); r.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = r; g.fillRect(0, 0, 32, 32); return new T.CanvasTexture(c); })();
rs.add(new T.Points(pg, new T.PointsMaterial({ size: 2.2, map: dot, color: 0x5d6b7c, transparent: true, opacity: .16, depthWrite: false })));
const ag = new T.BufferGeometry();
const actPts = new T.Points(ag, new T.PointsMaterial({ size: 6, map: dot, vertexColors: true, transparent: true, opacity: 1, depthWrite: false, depthTest: false })); actPts.renderOrder = 2; rs.add(actPts);
const rcam = new T.PerspectiveCamera(32, 1, 1, 8000); rcam.position.set(c0.x, c0.y, c0.z + 1500);
const rctl = new OrbitControls(rcam, rr.domElement); rctl.target.copy(c0); rctl.enableDamping = true; rctl.enablePan = false;
const ramp = f => { const s = [[.16, .2, .26], [.24, .44, .71], [1, .71, .28], [1, .95, .77]], x = Math.min(1, Math.max(0, f)) * 3, k = Math.min(2, Math.floor(x)), u = x - k;
  return s[k].map((v, j) => v + (s[k + 1][j] - v) * u); };
function paintBrain(st) {
  const frac = new Float32Array(B.regions.length + 1); const mx = Math.max(1e-9, ...st.regions.map(r => r.frac));
  for (const r of st.regions) frac[B.regions.findIndex(x => x.code === r.code) + 1] = r.frac / mx;
  const ap = [], ac = [];
  for (let i = 0; i < N; i++) { const f = REG[i] ? frac[REG[i]] : 0; if (!(f >= .04)) continue;   // regions under 4% of the top one stay grey (they are still in the table)
    ap.push(pa[3 * i], pa[3 * i + 1], pa[3 * i + 2]); ac.push(...ramp(.2 + .8 * f)); }
  ag.setAttribute('position', new T.BufferAttribute(new Float32Array(ap), 3)); ag.setAttribute('color', new T.BufferAttribute(new Float32Array(ac), 3));
}

// ---------- controls: the Taste Bench's 24 mixes, plus touching the antennae ----------
const LV = { s: [0, 50, 100, 200], b: [0, 100, 200], w: [0, 200] };
const sel = { s: 100, b: 0, w: 0 }; let touch = false;
document.querySelectorAll('.seg').forEach(seg => {
  const k = seg.dataset.k;
  seg.innerHTML = LV[k].map(v => `<button data-v="${v}" aria-pressed="false">${v === 0 ? 'none' : v}</button>`).join('');
  seg.addEventListener('click', ev => { const b = ev.target.closest('button'); if (!b) return; sel[k] = +b.dataset.v; touch = false; show(); });
});
const PRE = [['Sugar', { s: 100, b: 0, w: 0 }], ['Sugar + caffeine', { s: 100, b: 200, w: 0 }], ['Weak sugar', { s: 50, b: 0, w: 0 }],
  ['Water', { s: 0, b: 0, w: 200 }], ['Caffeine alone', { s: 0, b: 200, w: 0 }], ['Strong sugar + caffeine', { s: 200, b: 200, w: 0 }]];
$('presets').innerHTML = PRE.map(([l], i) => `<button data-i="${i}">${l}</button>`).join('');
$('presets').addEventListener('click', ev => { const b = ev.target.closest('button'); if (!b) return; Object.assign(sel, PRE[+b.dataset.i][1]); touch = false; show(); });
$('touch').addEventListener('click', () => { touch = !touch; show(); });

// ---------- one stimulus: behaviour, regions, story ----------
function show() {
  const key = touch ? 'touch' : `s${sel.s}_b${sel.b}_w${sel.w}`, st = B.stimuli.find(s => s.key === key);
  document.querySelectorAll('.seg').forEach(seg => seg.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', String(!touch && +x.dataset.v === sel[seg.dataset.k]))));
  $('touch').setAttribute('aria-pressed', String(touch));
  mode = { tongue: st.tongue, groom: st.groom }; tMode = performance.now() / 1000;
  $('bodySub').textContent = st.desc; $('brainSub').textContent = st.active ? `${st.active.toLocaleString('en-US')} of 139,255 neurons fired` : 'no neurons fired';
  $('act').innerHTML = `<span class="${st.tongue ? 'on' : ''}">${st.tongue ? 'Tongue out: feeding' : 'Tongue in'}</span><span class="${st.groom ? 'on' : ''}">${st.groom ? 'Grooming her antennae' : 'Not grooming'}</span>`;
  $('tBig').textContent = st.tongue ? 'Tongue out' : st.mn9 >= 1 ? 'A flicker, but the tongue stays in' : 'Tongue stays in'; $('tBar').style.width = Math.min(100, st.mn9 / 1.1) + '%';
  $('tTxt').innerHTML = `MN9, the motor neuron that pushes the tongue out, fired <b>${f1(st.mn9)}</b> times a second. The rule: tongue out at 10 or more.`;
  $('gBig').textContent = st.groom ? 'Grooming' : 'Not grooming'; $('gBar').style.width = Math.min(100, st.abn1 / 0.3) + '%';
  $('gTxt').innerHTML = `aBN1, a brain neuron that starts antennal grooming in real flies, fired <b>${f1(st.abn1)}</b> times a second. The rule: grooming at 5 or more.`;
  // regions
  $('regLead').textContent = st.regions.length ? `${st.regions.length} regions had at least one neuron fire. On the brain, colour shows each region's share of neurons that fired, compared with the most active region; regions below 4% of the top one stay grey.` : 'With nothing on the tongue, no neurons fire in the model.';
  $('regTab').innerHTML = st.regions.length ? '<thead><tr><th>Region</th><th>What it does</th><th>Neurons that fired</th><th>Share of the region</th></tr></thead><tbody>' +
    st.regions.slice(0, 12).map(r => `<tr><td>${esc(RN[r.code].name)} <span class="role">(${esc(r.code)})</span></td><td class="role">${esc(RN[r.code].role || '')}</td>
      <td>${r.active} of ${RN[r.code].total.toLocaleString('en-US')}</td><td><div class="rb"><i style="width:${Math.max(2, 100 * r.frac / st.regions[0].frac)}%"></i></div></td></tr>`).join('') +
    (st.regions.length > 12 ? `<tr><td colspan="4" class="role">and ${st.regions.length - 12} more regions with a few neurons each</td></tr>` : '') + '</tbody>' : '';
  paintBrain(st);
  // the story, from this run's numbers
  const top = st.regions[0], topTxt = top ? `, most of them in the ${esc(RN[top.code].name.toLowerCase())}${RN[top.code].role ? ` (${esc(RN[top.code].role)})` : ''}` : '';
  const S = [];
  let sum = '';
  if (touch) {
    S.push(['Antennae moved', `We switch on the 69 Johnston's organ CE neurons, which sense the antennae being moved. This is the only thing we do; everything after this is the brain's own wiring at work.`]);
    S.push(['The message spreads', `<b>${st.active.toLocaleString('en-US')}</b> neurons fire in response${topTxt}.`]);
    S.push(['The grooming neuron decides', `<b>aBN1</b> fires <b>${f1(st.abn1)}</b> times a second, above the line of 5, so <b>she grooms her antennae</b>. The tongue neuron stays silent (${f1(st.mn9)}).`]);
    sum = 'Real flies groom their antennae when this neuron is active (Hampel et al. 2015), and the untouched brain wiring reproduces it.';
  } else {
    const on = { sugar: sel.s > 0, bitter: sel.b > 0, water: sel.w > 0 }, tastes = ['sugar', 'bitter', 'water'].filter(k => on[k]);
    const tName = { sugar: 'sugar', bitter: 'bitter (like caffeine)', water: 'water' };
    if (!tastes.length) S.push(['Nothing on the tongue', 'No taste neurons are switched on, so there is nothing for the brain to react to.']);
    else {
      S.push(['Taste on the tongue', `We switch on the fly's ${tastes.map(k => `<b>${tName[k]}</b>`).join(' and ')} taste neurons: ${tastes.map(k => `${BENCH.inputs[k].length} ${k} neurons`).join(', ')}. This is the only thing we do; everything after this is the brain's own wiring at work.`]);
      S.push(['The message spreads', `<b>${st.active.toLocaleString('en-US')}</b> neurons fire in response, out of 139,255 in the brain${topTxt}.`]);
      S.push(['The tongue neuron decides', st.mn9 >= 10 ? `The signal reaches <b>MN9</b>, the motor neuron that moves the tongue. It fires <b>${f1(st.mn9)}</b> times a second, above the line of 10, so <b>the tongue comes out</b>.`
        : `<b>MN9</b>, the motor neuron that moves the tongue, fires only <b>${f1(st.mn9)}</b> times a second, below the line of 10, so <b>the tongue stays in</b>.`]);
      const nb = B.stimuli.find(s => s.key === `s${sel.s}_b0_w${sel.w}`).mn9;
      if (on.bitter && (on.sugar || on.water)) sum = (st.mn9 >= 10 ? `Bitter weakened the response (MN9 ${f1(nb)} → ${f1(st.mn9)} per second) but didn't stop it at this strength.`
        : `Bitter won: it cut MN9 from ${f1(nb)} to ${f1(st.mn9)} per second, so the fly refuses.`) + (on.sugar ? ' Real flies also refuse sugar mixed with bitter.' : '');
      else if (on.bitter) sum = 'Bitter alone never tells the tongue to come out. Real flies behave the same way.';
      else if (on.sugar && on.water) sum = 'Sugar and water both push MN9, so the response adds up.';
      else if (on.sugar) sum = sel.s >= 200 ? 'More sugar, stronger push on MN9.' : sel.s <= 50 ? 'Weak sugar still gets the tongue out, just with a softer push.' : 'Sugar is tasted, the signal travels through the feeding centre, and the tongue comes out, as in real flies.';
      else if (on.water) sum = 'Water is tasted by its own neurons, and they also reach MN9, so a thirsty fly drinks.';
    }
  }
  $('steps').innerHTML = S.map(([h, t], j) => `<li><span class="k" style="background:${j === 0 ? (touch ? '#0f9d8a' : '#c27c0e') : j === 1 ? '#c2187a' : '#111'}">${j + 1}</span><div><b>${h}.</b> ${t}</div></li>`).join('');
  $('ssum').innerHTML = sum; $('ssum').hidden = !sum;
  const line = !touch && SPARK && SPARK.lines[key];
  $('spark').hidden = !line;
  if (line) $('spark').innerHTML = `<b>Muse Spark:</b> ${esc(line)}<small>Written by ${esc(SPARK.model)} from the recorded numbers only, ${esc(SPARK.made)}. It doesn't affect any result.</small>`;
}
show();

// ---------- Round 1 ----------
const T1 = R1.totals;
$('r1lead').textContent = `Pass marks written down ${R1.prereg.written.split(',')[0].replace('T', ' at ').replace('Z', ' UTC')}, before the runs. Each card shows what was already known from real flies, the pass mark, and what the simulated brain did.`;
$('score').innerHTML = `<span class="n">${T1.matched} of ${T1.total}</span><span class="lead" style="font-size:15px">real-fly results matched by the untouched brain wiring</span>`;
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

// ---------- render loop ----------
function fit(r, el, cam) { const w = el.clientWidth, h = el.clientHeight; if (r.domElement.width !== Math.round(w * r.getPixelRatio())) { r.setSize(w, h, false); cam.aspect = w / h; cam.updateProjectionMatrix(); } }
(function loop(now) {
  const t = now / 1000; fit(br, bv, bcam); fit(rr, rv, rcam);
  bodyPose(t); bctl.update(); rctl.update(); br.render(bs, bcam); rr.render(rs, rcam);
  requestAnimationFrame(loop);
})(performance.now());
