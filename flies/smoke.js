/* Vivarium smoke: boots the real flies/index.html module with real three.js,
   a stub renderer, and a dependency-free stub DOM. Steps real animation frames
   and asserts both specimens, walk, tabs, keys, and picking.
   Run: node smoke.js (exit 1 on fail). */
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('node:url');
const { register } = require('node:module');

const HERE = __dirname;
register(pathToFileURL(path.join(HERE, 'smoke-loader.mjs')));

const html = fs.readFileSync(path.join(HERE, 'index.html'), 'utf8');
const modSrc = html.match(/<script type="module">(.*?)<\/script>/s)[1]
  .replace("from './fly.js'", `from '${pathToFileURL(path.join(HERE, 'fly.js')).href}'`)
  .replace('new THREE.WebGLRenderer', 'new __FakeGL')
  .replace("import * as THREE from 'three';",
    `import * as THREE from 'three';\nclass __FakeGL { setPixelRatio(){} setSize(){} render(){} }`)
  + `\n;globalThis.__t = { table, rigs, camera, scene, tabs, selectTab, partAt, setCuticle, Viv, bananas, stages, sprigs,` +
  ` active: () => active, detail: () => document.getElementById('detail') };`;
fs.writeFileSync('/tmp/vivarium-page.mjs', modSrc);

const fails = [];
const check = (name, cond, extra = '') => {
  console.log((cond ? 'PASS ' : 'FAIL ') + name + (extra && !cond ? ' — ' + extra : ''));
  if (!cond) fails.push(name);
};
const sleep = ms => new Promise(r => setTimeout(r, ms));

const grad = { addColorStop() {} };
const ctx2d = () => new Proxy({}, {
  get: (t, p) => (p === 'createLinearGradient' || p === 'createRadialGradient')
    ? () => grad : (typeof p === 'string' ? () => {} : undefined),
  set: () => true,
});

function makeDom() {
  const registry = {};
  const rects = {
    hero: { left: 0, top: 0, width: 1440, height: 900, right: 1440, bottom: 900 },
    stage: { left: 0, top: 120, width: 1060, height: 700, right: 1060, bottom: 820 },
  };
  const el = (id) => {
    if (registry[id]) return registry[id];
    const listeners = {};
    const e = {
      id, children: [], dataset: {}, style: {}, hidden: false,
      textContent: '', offsetWidth: 0, _html: '',
      classList: {
        _s: new Set(),
        add(...c) { c.forEach(x => this._s.add(x)); },
        remove(...c) { c.forEach(x => this._s.delete(x)); },
        toggle(x, f) { const on = f !== undefined ? f : !this._s.has(x); on ? this._s.add(x) : this._s.delete(x); return on; },
        contains: x => e.classList._s.has(x),
      },
      setAttribute(k, v) { e.dataset[k] = String(v); },
      getAttribute: k => (k in e.dataset ? e.dataset[k] : null),
      addEventListener: (t, f) => { (listeners[t] ??= []).push(f); },
      dispatchEvent: (ev) => { ev.target ??= e; (listeners[ev.type] || []).forEach(f => f(ev)); },
      click: () => e.dispatchEvent({ type: 'click', clientX: 1, clientY: 1 }),
      focus: () => {},
      querySelector: (sel) => {
        const m = sel.match(/^\[data-fly="(\d)"\]$/);
        if (m) return el(`tab${m[1]}`);
        if (sel === '.lens') return el(`${id}-lens`);
        return null;
      },
      querySelectorAll: () => [],
      getBoundingClientRect: () => rects[id] || { left: 0, top: 0, width: 0, height: 0, right: 0, bottom: 0 },
      setPointerCapture: () => {},
    };
    Object.defineProperty(e, 'innerHTML', {
      get: () => e._html,
      set: (v) => {
        e._html = String(v);
        for (const m of e._html.matchAll(/id="([^"]+)"/g)) el(m[1]);
      },
    });
    registry[id] = e;
    return e;
  };
  const winListeners = {};
  const window = {
    addEventListener: (t, f) => { (winListeners[t] ??= []).push(f); },
    dispatch: (t, ev) => (winListeners[t] || []).forEach(f => f(ev)),
  };
  const document = {
    getElementById: (id) => el(id),
    createElement: (tag) => tag === 'canvas'
      ? { width: 0, height: 0, getContext: (t) => (t === '2d' ? ctx2d() : null), style: {} }
      : el(`anon-${Math.random()}`),
    querySelector: () => null,
    querySelectorAll: () => [],
    body: el('body'),
  };
  return { window, document, el };
}

async function bootPass(reduced, live) {
  const { window, document, el } = makeDom();
  const rafQ = [];
  const errors = [];
  const wsInstances = [];
  if (live) {
    globalThis.WebSocket = class {
      constructor(url) { this.url = url; wsInstances.push(this); }
      close() { if (this.onclose) this.onclose(); }
    };
  } else { delete globalThis.WebSocket; }
  globalThis.fetch = async (url) => {
    const base = String(url).split('/').pop();
    const file = { 'somas.bin': 'somas.bin', 'classes.bin': 'classes.bin', 'index.json': 'index.json', 'photoreceptors.bin': 'photoreceptors.bin' }[base];
    if (!file) return { ok: false, status: 404, arrayBuffer: async () => { throw new Error('404'); }, json: async () => { throw new Error('404'); } };
    const buf = fs.readFileSync(path.join(HERE, '..', 'library', 'points', file));
    const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
    return { ok: true, status: 200, arrayBuffer: async () => ab, json: async () => JSON.parse(buf.toString('utf8')) };
  };
  window.addEventListener('error', e => errors.push('window.onerror: ' + (e.error?.stack || e.message)));
  window.addEventListener('unhandledrejection', e => errors.push('unhandled: ' + (e.reason?.stack || e.reason)));
  globalThis.window = window;
  globalThis.document = document;
  globalThis.location = { protocol: 'http:', hostname: 'localhost' };
  globalThis.navigator = {};
  globalThis.addEventListener = window.addEventListener;
  globalThis.matchMedia = () => ({ matches: reduced, addEventListener() {}, removeEventListener() {} });
  globalThis.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} };
  globalThis.devicePixelRatio = 1;
  globalThis.requestAnimationFrame = cb => { rafQ.push(cb); return rafQ.length; };
  const clk = { now: 10000 };
  Object.defineProperty(globalThis, 'performance', {
    value: { now: () => clk.now }, configurable: true, writable: true });
  await import(pathToFileURL('/tmp/vivarium-page.mjs').href + (reduced ? '?pass=r' : live ? '?pass=l' : '?pass=n'));
  const t = globalThis.__t;
  const step = (n, ms = 16.7) => { for (let i = 0; i < n; i++) { clk.now += ms; const cb = rafQ.shift(); if (!cb) break; cb(); } };
  for (let i = 0; i < 200 && !(t.rigs[0] && t.rigs[0].brain && t.rigs[1] && t.rigs[1].brain); i++) await sleep(10);
  return { t, step, errors, el, wsInstances };
}

(async () => {
  // ---- full-motion pass ----
  {
    const { t, step, errors, el } = await bootPass(false);
    step(5);
    check('boot without errors', errors.length === 0, errors[0]?.slice(0, 200));
    check('both rigs built', !!t.rigs[0] && !!t.rigs[1]);
    check('both pivots visible', t.rigs[0].pivot.visible && t.rigs[1].pivot.visible);
    check('specimens side by side', t.rigs[0].pivot.position.x < 0 && t.rigs[1].pivot.position.x > 0);
    check('six legs + two wings per fly',
      t.rigs.every(r => r.model.userData.rig.legs.length === 6 && r.model.userData.rig.wings.length === 2));
    const hip0 = t.rigs[0].model.userData.rig.legs[0].hip.rotation.x;
    step(300);
    const hip1 = t.rigs[0].model.userData.rig.legs[0].hip.rotation.x;
    check('legs walk across frames', hip0 !== hip1, `${hip0} vs ${hip1}`);
    const other = t.rigs[1].model.userData.rig.legs[0].hip.rotation.x;
    check('flies step out of sync', other !== hip1, `${other} vs ${hip1}`);
    const before = t.detail().innerHTML.includes('Hagrid');
    el('tab0').click();
    await sleep(350);
    step(5);
    check('tab switches sheet to Maxime', before && t.detail().innerHTML.includes('Maxime'));
    const q0 = t.table.quaternion.clone();
    el('stage').dispatchEvent({ type: 'keydown', key: 'ArrowLeft', preventDefault: () => {} });
    step(3);
    check('arrow key turns table', t.table.quaternion.angleTo(q0) > 0.01);
    t.scene.updateMatrixWorld(true);
    t.camera.updateMatrixWorld();
    const THREE = await import('three');
    const px = t.rigs[1].proxies[0];
    const v = px.getWorldPosition(new THREE.Vector3()).project(t.camera);
    const hit = t.partAt((v.x + 1) / 2 * 1440, (1 - v.y) / 2 * 900);
    check('pick routes part + fly', !!hit && hit.fly === 1 && typeof hit.part === 'string', JSON.stringify(hit));
    // brains + cuticle (offline)
    check('brains seated', !!t.rigs[0].brain && !!t.rigs[1].brain);
    check('brain points real', t.rigs[0].brain.soma.geometry.attributes.position.count === 139255 &&
      t.rigs[0].brain.photo.geometry.attributes.position.count === 11151);
    const op0 = t.rigs[0].brain.soma.material.opacity;
    step(120);
    check('offline glow pulses', t.rigs[0].brain.soma.material.opacity !== op0);
    check('photo overlay dark offline', t.rigs[0].brain.photo.material.opacity === 0);
    let mesh = null;
    t.rigs[0].model.traverse(o => { if (!mesh && o.isMesh && o.visible) mesh = o; });
    t.setCuticle(1);
    check('ghost thins cuticle', mesh.material.transparent === true && mesh.material.opacity === 0.22);
    t.setCuticle(2);
    check('hidden hides cuticle', mesh.visible === false);
    t.setCuticle(0);
    check('solid restores cuticle', mesh.visible === true && mesh.material.transparent === false && mesh.material.opacity === 1);
  }
  // ---- live pass (scripted sim states) ----
  {
    const { t, step, errors, el, wsInstances } = await bootPass(false, true);
    step(5);
    check('live boot without errors', errors.length === 0, errors[0]?.slice(0, 200));
    check('ws connects to lab', wsInstances.length === 1 && /:8765$/.test(wsInstances[0].url), wsInstances[0] && wsInstances[0].url);
    const send = (tStep, m, h) => wsInstances[0].onmessage({ data: JSON.stringify({
      type: 'state', t: tStep,
      flies: {
        'control:banc': Object.assign({ fly: { x: 0, y: 0, angle: 0 }, rates: { all: 0.02 }, legs: [0.02, 0.02], drugs: {}, stimuli: {}, banana: { x: 5, y: 0 } }, m),
        'treatment:malecns': Object.assign({ fly: { x: 0, y: 0, angle: 0 }, rates: { all: 0.02 }, legs: [0.02, 0.02], drugs: {}, stimuli: {}, banana: { x: 5, y: 0 } }, h),
      } }) });
    send(10, {}, {});
    step(30);
    check('status goes live', el('vivStatus').textContent.includes('Live from the sim'), el('vivStatus').textContent);
    send(11, { fly: { x: 10, y: -10, angle: 0 } }, {});
    step(250);
    check('true spot maps', Math.abs(t.rigs[0].pivot.position.x - (-1.5 + 10 * 0.11)) < 0.05 &&
      Math.abs(t.rigs[0].pivot.position.z - (-10 * 0.11)) < 0.05,
      `${t.rigs[0].pivot.position.x}, ${t.rigs[0].pivot.position.z}`);
    check('true heading maps', Math.abs(t.rigs[0].pivot.rotation.y - Math.PI / 2) < 0.08,
      t.rigs[0].pivot.rotation.y);
    check('live shrinks specimens', t.rigs[0].zoomK < 0.7, t.rigs[0].zoomK);
    send(12, { banana: { x: -3, y: 4 } }, {});
    check('banana follows slot', Math.abs(t.bananas[0].position.x - (-3 * 0.11)) < 1e-6 &&
      Math.abs(t.bananas[0].position.z - 4 * 0.11) < 1e-6);
    const census = {};
    t.table.traverse(o => { if (o.userData.env) census[o.userData.env] = (census[o.userData.env] || 0) + 1; });
    check('jar environment built', census.floor === 2 && census.glass === 8 && census.banana === 2 &&
      census.yeast === 2 && census.sprig === 2, JSON.stringify(census));
    check('floors ride the feet', Math.abs(t.stages[0].position.y - (-1.30 * t.rigs[0].holder.scale.x)) < 1e-6);
    check('fog set', !!t.scene.fog);
    const sw0 = t.sprigs[0].rotation.z;
    step(60);
    check('sprigs sway', t.sprigs[0].rotation.z !== sw0);
    send(13, { rates: { all: 0.09 }, legs: [0.09, 0.09, 0.09, 0.09], drugs: { caffeine: 0.5 }, stimuli: { light: [0.8, 0.2] } }, {});
    step(60);
    check('glow answers firing', t.rigs[0].brain.soma.material.opacity > 0.8,
      t.rigs[0].brain.soma.material.opacity);
    check('photoreceptors flash on light', t.rigs[0].brain.photo.material.opacity > 0.5,
      t.rigs[0].brain.photo.material.opacity);
    check('drugs listed', el('vivBoxes').textContent.includes('caffeine 0.50'), el('vivBoxes').textContent);
    send(15, { dist: 3.3 }, { dist: 7.7 });
    check('banana distance reads out', el('vivBoxes').textContent.includes('banana 3.3') &&
      el('vivBoxes').textContent.includes('banana 7.7'), el('vivBoxes').textContent);
    const s1 = t.rigs[0].stride;
    step(60);
    send(14, { rates: { all: 0.021 }, legs: [0.021, 0.021] }, {});
    step(120);
    const dHi = t.rigs[0].stride - s1;
    const s2 = t.rigs[0].stride;
    step(60);
    const dLo = t.rigs[0].stride - s2;
    check('walk quickens with leg drive', dHi > dLo * 1.5, `${dHi} vs ${dLo}`);
    wsInstances[0].close();
    step(5);
    check('disconnect falls back', t.Viv.live === false && el('vivStatus').textContent.includes('offline'));
  }
  // ---- reduced-motion pass ----
  {
    const { t, step, errors } = await bootPass(true);
    step(5);
    const h0 = t.rigs[0].model.userData.rig.legs[0].hip.rotation.x;
    const y0 = t.rigs[0].pivot.rotation.y;
    step(300);
    const h1 = t.rigs[0].model.userData.rig.legs[0].hip.rotation.x;
    const y1 = t.rigs[0].pivot.rotation.y;
    check('reduced motion freezes gait', h0 === 0 && h1 === 0 && y0 === 0 && y1 === 0,
      `${h0},${h1} / ${y0},${y1}`);
    check('reduced boot without errors', errors.length === 0, errors[0]?.slice(0, 200));
  }
  console.log(fails.length ? `SMOKE: ${fails.length} FAILING` : 'SMOKE: ALL PASS');
  process.exit(fails.length ? 1 : 0);
})().catch(e => { console.log('SMOKE THREW: ' + (e && e.stack || e)); process.exit(1); });
