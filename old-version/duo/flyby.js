/* Duo story page — Maxime and Hagrid fly over the page in live 3D.
   The models are the same procedural builds as the flies page (../flies/fly.js),
   small: about 80px on a desktop viewport. Each wanders the viewport on its own
   with a name tag; the pair keeps a little distance. Respects
   prefers-reduced-motion (parks both, no wandering). Fails silent without WebGL. */
import * as THREE from 'three';
import { buildFly } from '../flies/fly.js';

const mount = document.getElementById('flyby');
if (!mount) throw new Error('flyby mount missing');
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

let renderer;
try {
  renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
} catch {
  mount.remove(); // no WebGL: the page reads fine without the pair
  throw new Error('flyby: WebGL unavailable');
}
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.domElement.className = 'duo-flygl';
mount.appendChild(renderer.domElement);

const scene = new THREE.Scene();
// Orthographic: fly size in pixels stays put whatever the viewport.
const FRUSTUM_H = 24;
const camera = new THREE.OrthographicCamera(-1, 1, FRUSTUM_H / 2, -FRUSTUM_H / 2, 0.1, 50);
camera.position.set(0, 0, 10);
camera.lookAt(0, 0, 0);

// Lights copied from the flies page (day preset); dusk follows the page toggle.
const hemi = new THREE.HemisphereLight(0xfff6e8, 0x8a7a5f, 0.8);
const key = new THREE.DirectionalLight(0xfff4e2, 1.6);
key.position.set(2.5, 4, 5);
const rim = new THREE.DirectionalLight(0xbfd8ff, 0.7);
rim.position.set(-4, 2, -3);
scene.add(hemi, key, rim);
const DAY = { hemi: 0.8, key: 1.6, keyC: new THREE.Color(0xfff4e2), rim: 0.7, exp: 1.05 };
const DUSK = { hemi: 0.25, key: 2.6, keyC: new THREE.Color(0xffc98a), rim: 1.9, exp: 1.0 };
let duskW = 0, duskTarget = 0;
const hero = document.getElementById('hero');
const syncDusk = () => { duskTarget = hero && hero.dataset.light === 'dusk' ? 1 : 0; };
syncDusk();
if (hero) new MutationObserver(syncDusk).observe(hero, { attributes: true, attributeFilter: ['data-light'] });

const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const rnd = (a, b) => a + Math.random() * (b - a);

let vw = 1, vh = 1, ppu = 1; // viewport px + px-per-unit
function measure() {
  vw = innerWidth; vh = innerHeight;
  ppu = vh / FRUSTUM_H;
  renderer.setSize(vw, vh);
  camera.left = -(vw / ppu) / 2; camera.right = (vw / ppu) / 2;
  camera.top = FRUSTUM_H / 2; camera.bottom = -FRUSTUM_H / 2;
  camera.updateProjectionMatrix();
}
measure();
addEventListener('resize', () => { measure(); placeTags(); if (reduced) renderer.render(scene, camera); });

function makeTag(name) {
  const d = document.createElement('div');
  d.className = 'duo-flytag';
  d.textContent = name;
  mount.appendChild(d);
  return d;
}

function makeFlyer(male, name, x0, y0) {
  const model = buildFly(male);
  model.traverse((o) => { if (o.isMesh) o.frustumCulled = false; });
  scene.add(model);
  return {
    model, tag: makeTag(name), x: x0, y: y0, vx: 0, vy: 0,
    tx: x0, ty: y0, wait: rnd(0, 2), speed: rnd(42, 66),
    phase: rnd(0, Math.PI * 2), yaw: 0,
  };
}
const pair = [makeFlyer(false, 'Maxime', vw * 0.3, vh * 0.35),
              makeFlyer(true, 'Hagrid', vw * 0.65, vh * 0.5)];

function retarget(f) {
  const m = 70;
  f.tx = rnd(m, Math.max(m + 1, vw - m));
  f.ty = rnd(m, Math.max(m + 1, vh - m));
  f.wait = 0;
}

function stepFlyer(f, other, dt, t) {
  const dx = f.tx - f.x, dy = f.ty - f.y;
  const dist = Math.hypot(dx, dy);
  if (dist < 12) {
    f.wait += dt;
    if (f.wait > rnd(1.5, 4)) retarget(f);
  } else {
    f.wait = 0;
  }
  // steer toward the target, ease off when close; keep clear of the other fly
  let ax = dist > 1 ? (dx / dist) * 60 : 0;
  let ay = dist > 1 ? (dy / dist) * 60 : 0;
  const ox = f.x - other.x, oy = f.y - other.y;
  const od = Math.hypot(ox, oy);
  if (od > 1 && od < 150) { ax += (ox / od) * 90; ay += (oy / od) * 90; }
  f.vx = clamp(f.vx + ax * dt, -f.speed, f.speed);
  f.vy = clamp(f.vy + ay * dt, -f.speed, f.speed);
  f.x = clamp(f.x + f.vx * dt, 40, vw - 40);
  f.y = clamp(f.y + f.vy * dt, 40, vh - 40);
  // face the motion a little, bank into it, bob
  const yawT = Math.atan2(f.vx, 60);
  f.yaw += (yawT - f.yaw) * Math.min(1, dt * 3);
  const bob = Math.sin(t * 2.1 + f.phase) * 5;
  f.model.position.set((f.x - vw / 2) / ppu, (vh / 2 - f.y - bob) / ppu, 0);
  f.model.rotation.set(clamp(f.vy * 0.004, -0.35, 0.35), f.yaw, clamp(-f.vx * 0.004, -0.4, 0.4));
}

function placeTags() {
  for (const f of pair) {
    f.tag.style.transform =
      `translate(${clamp(f.x, 56, vw - 56)}px, ${Math.max(34, f.y - 56)}px) translate(-50%, -100%)`;
  }
}

let last = performance.now();
function tick(now) {
  requestAnimationFrame(tick);
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  duskW += (duskTarget - duskW) * Math.min(1, dt * 4);
  hemi.intensity = DAY.hemi + (DUSK.hemi - DAY.hemi) * duskW;
  key.intensity = DAY.key + (DUSK.key - DAY.key) * duskW;
  key.color.copy(DAY.keyC).lerp(DUSK.keyC, duskW);
  rim.intensity = DAY.rim + (DUSK.rim - DAY.rim) * duskW;
  renderer.toneMappingExposure = DAY.exp + (DUSK.exp - DAY.exp) * duskW;
  if (!reduced) {
    const t = now / 1000;
    stepFlyer(pair[0], pair[1], dt, t);
    stepFlyer(pair[1], pair[0], dt, t);
    placeTags();
  }
  renderer.render(scene, camera);
}

if (reduced) {
  // parked, spread across the hero; tags placed once
  pair[0].x = vw * 0.32; pair[0].y = vh * 0.32;
  pair[1].x = vw * 0.62; pair[1].y = vh * 0.44;
  for (const f of pair) {
    f.model.position.set((f.x - vw / 2) / ppu, (vh / 2 - f.y) / ppu, 0);
    f.model.rotation.set(0, 0.5, 0);
  }
  placeTags();
  renderer.render(scene, camera);
} else {
  retarget(pair[0]); retarget(pair[1]);
}
requestAnimationFrame(tick);
