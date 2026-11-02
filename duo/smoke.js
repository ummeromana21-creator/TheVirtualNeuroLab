/* Headless smoke for duo/flyby.js: runs the REAL overlay module plus the REAL
   shared fly builder against stub DOM + stub THREE (no WebGL here), pumps
   frames, and asserts the pair wanders with tags that follow. Also covers the
   reduced-motion park and the no-WebGL bailout via env. Run: node smoke.js */
const fs = require('fs');
const os = require('os');
const path = require('path');
const HERE = __dirname;

const fails = [];
const check = (name, cond, extra = '') => {
  console.log((cond ? 'PASS ' : 'FAIL ') + name + (extra && !cond ? ' — ' + extra : ''));
  if (!cond) fails.push(name);
};

// ---- stub THREE: every class constructs a chainable proxy; nothing draws ----
const threeStub = `
const inst = () => new Proxy(function(){}, {
  get: (t, p) => {
    if (typeof p !== 'string') return p === Symbol.toPrimitive ? () => 0 : undefined;
    if (p === 'length' || p === 'name' || p === 'prototype') return inst();
    if (!Object.prototype.hasOwnProperty.call(t, p)) t[p] = inst();
    return t[p];
  },
  set: (t, p, v) => { t[p] = v; return true; },
  apply: () => inst(),
});
class Stub { constructor(...a) { return inst(); } }
class WebGLRenderer {
  constructor(...a) {
    if (globalThis.__SMOKE_NOWEBGL) throw new Error('no webgl');
    const i = inst();
    i.domElement = { tag: 'canvas', className: '', style: {} };
    return i;
  }
}
export const Scene = Stub, Group = Stub, Mesh = Stub;
export const SphereGeometry = Stub, CylinderGeometry = Stub, LatheGeometry = Stub;
export const ConeGeometry = Stub, BoxGeometry = Stub, ShapeGeometry = Stub, Shape = Stub;
export const MeshStandardMaterial = Stub, CanvasTexture = Stub;
export const HemisphereLight = Stub, DirectionalLight = Stub, Color = Stub;
export const OrthographicCamera = Stub, PerspectiveCamera = Stub;
export const Vector3 = Stub, Vector2 = Stub;
export { WebGLRenderer };
export const SRGBColorSpace = 'srgb', DoubleSide = 2, ACESFilmicToneMapping = 4;
`;

// ---- stub DOM ----
function makeEnv({ reduced, nowebgl }) {
  const queue = [];
  const grad = { addColorStop() {} };
  const ctx2d = new Proxy({}, {
    get: (t, p) => {
      if (p in t) return t[p];
      if (p === 'createLinearGradient' || p === 'createRadialGradient') return () => grad;
      return (...a) => chain;
    },
    set: (t, p, v) => { t[p] = v; return true; },
  });
  const chain = new Proxy(function () {}, { get: () => (...a) => chain, apply: () => chain });
  const els = {};
  const mount = { tag: 'mount', children: [], removed: false,
    appendChild(c) { this.children.push(c); return c; }, remove() { this.removed = true; } };
  els.flyby = mount;
  els.hero = { dataset: { light: 'day' } };
  globalThis.__SMOKE_NOWEBGL = !!nowebgl;
  globalThis.innerWidth = 1280;
  globalThis.innerHeight = 800;
  globalThis.devicePixelRatio = 2;
  globalThis.matchMedia = () => ({ matches: !!reduced });
  globalThis.MutationObserver = class { observe() {} };
  globalThis.addEventListener = () => {};
  globalThis.requestAnimationFrame = (cb) => { queue.push(cb); return queue.length; };
  globalThis.document = {
    getElementById: (id) => els[id] || null,
    createElement: (tag) => ({ tag, width: 0, height: 0, style: {}, className: '', textContent: '',
      getContext: () => ctx2d, appendChild() {} }),
  };
  return { queue, mount };
}

async function stage() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'flysmoke-'));
  fs.writeFileSync(path.join(dir, 'three-stub.mjs'), threeStub);
  const fly = fs.readFileSync(path.join(HERE, '..', 'flies', 'fly.js'), 'utf8')
    .replace(`from 'three'`, `from './three-stub.mjs'`);
  fs.writeFileSync(path.join(dir, 'fly.mjs'), fly);
  const by = fs.readFileSync(path.join(HERE, 'flyby.js'), 'utf8')
    .replace(`from 'three'`, `from './three-stub.mjs'`)
    .replace(`from '../flies/fly.js'`, `from './fly.mjs'`);
  fs.writeFileSync(path.join(dir, 'flyby.mjs'), by);
  return dir;
}

function pump(queue, n, t0) {
  let now = t0;
  for (let i = 0; i < n; i++) {
    const cb = queue.shift();
    if (!cb) throw new Error(`rAF starved after ${i} frames`);
    now += 16.7;
    cb(now);
  }
  return now;
}

(async () => {
  // main run: wandering pair
  {
    const dir = await stage();
    const { queue, mount } = makeEnv({});
    await import(dir + '/flyby.mjs');
    check('boots without throwing', true);
    const canvas = mount.children.find((c) => c.tag === 'canvas');
    check('canvas appended', !!canvas);
    const tags = mount.children.filter((c) => c.className === 'duo-flytag');
    check('two name tags', tags.length === 2, tags.length);
    check('tags named', tags.map((t) => t.textContent).join() === 'Maxime,Hagrid',
      tags.map((t) => t.textContent).join());
    pump(queue, 20, 1000);
    const early = tags.map((t) => t.style.transform);
    check('tags placed', early.every(Boolean), JSON.stringify(early));
    pump(queue, 80, 1000 + 20 * 16.7);
    const late = tags.map((t) => t.style.transform);
    check('pair wanders (tags move)', late[0] !== early[0] && late[1] !== early[1],
      JSON.stringify({ early, late }));
    fs.rmSync(dir, { recursive: true, force: true });
  }
  // reduced motion: parked, static
  {
    const dir = await stage();
    const { queue, mount } = makeEnv({ reduced: true });
    await import(dir + '/flyby.mjs');
    const tags = mount.children.filter((c) => c.className === 'duo-flytag');
    pump(queue, 5, 1000);
    const a = tags.map((t) => t.style.transform);
    pump(queue, 45, 1000 + 5 * 16.7);
    const b = tags.map((t) => t.style.transform);
    check('reduced motion parks the pair', a[0] === b[0] && a[1] === b[1] && !!a[0]);
    fs.rmSync(dir, { recursive: true, force: true });
  }
  // no WebGL: mount removed, page unaffected
  {
    const dir = await stage();
    const { mount } = makeEnv({ nowebgl: true });
    let threw = false;
    try { await import(dir + '/flyby.mjs'); } catch { threw = true; }
    check('no-WebGL removes overlay', threw && mount.removed === true);
    fs.rmSync(dir, { recursive: true, force: true });
  }
  console.log(fails.length ? `SMOKE: ${fails.length} FAILING` : 'SMOKE: ALL PASS');
  process.exit(fails.length ? 1 : 0);
})().catch((e) => { console.log('SMOKE THREW: ' + (e && e.stack || e)); process.exit(1); });
