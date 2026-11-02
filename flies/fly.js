/* Copied from flies/index.html (the 3D specimen builder): procedural Drosophila.
   Shared so the duo story page flies the same Maxime and Hagrid. Faces +Z, up +Y.
   buildFly(false) = Maxime (female, pointed abdomen); buildFly(true) = Hagrid (male). */
import * as THREE from 'three';

function makeTex(w, h, draw, srgb = true) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}
// Abdomen: cuticle base + transverse dark bands. Canvas bottom = rear tip
// (lathe v=0 at the first profile point).
function abdomenTex(male) {
  return makeTex(256, 256, (g, w, h) => {
    const base = g.createLinearGradient(0, 0, 0, h);
    base.addColorStop(0, '#d3ab74'); base.addColorStop(1, '#bd9260');
    g.fillStyle = base; g.fillRect(0, 0, w, h);
    g.fillStyle = '#2b2320';
    // bands widen toward the rear (larger y = rear)
    const bands = male  // fractions from the rear tip; male rear is solid dark
      ? [[0.00, 0.45], [0.52, 0.60], [0.68, 0.74], [0.84, 0.88]]
      : [[0.04, 0.17], [0.22, 0.32], [0.38, 0.46], [0.54, 0.60], [0.70, 0.74], [0.85, 0.88]];
    for (const [a, b] of bands) g.fillRect(0, h * (1 - b), w, h * (b - a));
    // speckle for cuticle variation
    g.fillStyle = 'rgba(60,40,20,0.08)';
    for (let i = 0; i < 700; i++) g.fillRect(Math.random() * w, Math.random() * h, 1.5, 1.5);
  });
}
// Thorax: tan with faint longitudinal stripes (constant-u lines).
const thoraxTex = () => makeTex(256, 256, (g, w, h) => {
  g.fillStyle = '#b28a5c'; g.fillRect(0, 0, w, h);
  g.fillStyle = 'rgba(70,50,28,0.35)';
  for (const x of [0.30, 0.42, 0.58, 0.70]) g.fillRect(w * x - 3, 0, 6, h);
  g.fillStyle = 'rgba(255,235,200,0.10)';
  for (const x of [0.24, 0.36, 0.48, 0.60, 0.72]) g.fillRect(w * x - 2, 0, 4, h);
  g.fillStyle = 'rgba(60,40,20,0.10)';
  for (let i = 0; i < 600; i++) g.fillRect(Math.random() * w, Math.random() * h, 1.5, 1.5);
});
// Compound eye: offset rows of ommatidia facets, shaded per facet.
const eyeTex = () => makeTex(256, 256, (g, w, h) => {
  g.fillStyle = '#7c1f1f'; g.fillRect(0, 0, w, h);
  const r = 7, dx = 13, dy = 11;
  for (let row = 0, y = 0; y < h + dy; y += dy, row++) {
    for (let x = (row % 2) * dx / 2; x < w + dx; x += dx) {
      const grad = g.createRadialGradient(x - 2, y - 2, 1, x, y, r);
      grad.addColorStop(0, '#d95f4a'); grad.addColorStop(0.55, '#b03227'); grad.addColorStop(1, '#6e1a14');
      g.fillStyle = grad;
      g.beginPath(); g.arc(x, y, r, 0, 7); g.fill();
    }
  }
});
// Wing membrane: faint tint + veins. Canvas bottom = leading edge,
// left = wing base (u=0), right = tip.
const wingTex = () => makeTex(256, 128, (g, w, h) => {
  g.clearRect(0, 0, w, h);
  g.fillStyle = 'rgba(240,240,235,0.22)'; g.fillRect(0, 0, w, h);
  g.strokeStyle = 'rgba(80,68,56,0.9)'; g.lineCap = 'round';
  g.lineWidth = 6;  // leading edge (costa)
  g.beginPath(); g.moveTo(2, h - 3); g.lineTo(w - 4, 6); g.stroke();
  g.lineWidth = 3.5;  // longitudinal veins fanning from the base
  const base = [6, h - 8];
  for (const ty of [0.10, 0.32, 0.54, 0.76, 0.94]) {
    g.beginPath(); g.moveTo(...base);
    g.quadraticCurveTo(w * 0.4, h * ty + 8, w - 3, h * ty); g.stroke();
  }
  g.lineWidth = 2;  // crossveins
  g.beginPath(); g.moveTo(w * 0.30, h * 0.72); g.lineTo(w * 0.30, h * 0.92); g.stroke();
  g.beginPath(); g.moveTo(w * 0.55, h * 0.42); g.lineTo(w * 0.55, h * 0.62); g.stroke();
});

// =====================================================================
// 4. FLY BUILDER (procedural Drosophila; faces +Z, up +Y)
// =====================================================================
const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
function limb(a, b, r1, r2, mat) {
  const dir = V3(0, 0, 0).subVectors(b, a);
  const len = dir.length();
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r2, r1, len, 10), mat);
  m.position.copy(a).addScaledVector(dir, 0.5);
  m.quaternion.setFromUnitVectors(V3(0, 1, 0), dir.normalize());
  return m;
}
function ball(r, mat, x, y, z, w = 32, h = 24) {
  const m = new THREE.Mesh(new THREE.SphereGeometry(r, w, h), mat);
  m.position.set(x, y, z);
  return m;
}

// Wing blade: Shape in XY (x = base→tip, +y = trailing), UVs remapped to
// the bounding box so the vein texture spans base→tip, leading→trailing.
function wingGeo(mirror) {
  const X = (v) => v * mirror;
  const s = new THREE.Shape();
  s.moveTo(X(0), 0.10);
  s.quadraticCurveTo(X(0.7), 0.30, X(1.25), 0.12);
  s.quadraticCurveTo(X(1.6), 0.02, X(1.7), -0.06);
  s.quadraticCurveTo(X(1.1), -0.20, X(0.5), -0.22);
  s.quadraticCurveTo(X(0.15), -0.22, X(0), -0.12);
  s.closePath();
  const g = new THREE.ShapeGeometry(s, 12);
  g.computeBoundingBox();
  const bb = g.boundingBox, sx = bb.max.x - bb.min.x, sy = bb.max.y - bb.min.y;
  const pos = g.attributes.position, uv = g.attributes.uv;
  for (let i = 0; i < uv.count; i++)
    uv.setXY(i, (pos.getX(i) - bb.min.x) / sx, (pos.getY(i) - bb.min.y) / sy);
  g.rotateX(-Math.PI / 2);   // lay flat: length ±X, leading edge +Z
  g.rotateX(-0.15);          // slight blade pitch, leading edge up
  return g;
}

function buildFly(male) {
  const model = new THREE.Group();
  // Shared material roles.
  const cuticle = new THREE.MeshStandardMaterial({ color: 0xbb9160, roughness: 0.6, metalness: 0.02 });
  const dark = new THREE.MeshStandardMaterial({ color: 0x241d18, roughness: 0.7 });
  const legMat = new THREE.MeshStandardMaterial({ color: 0x5a4630, roughness: 0.7 });
  const paleMat = new THREE.MeshStandardMaterial({ color: 0xd9c9a8, roughness: 0.5 });
  const eyeMap = eyeTex();
  const eyeMat = new THREE.MeshStandardMaterial({
    map: eyeMap, bumpMap: eyeMap, bumpScale: 0.6,
    roughness: 0.32, metalness: 0.05,
  });
  const abdomenMat = new THREE.MeshStandardMaterial({ map: abdomenTex(male), roughness: 0.55, metalness: 0.03 });
  const thoraxMat = new THREE.MeshStandardMaterial({ map: thoraxTex(), roughness: 0.6, metalness: 0.02 });
  const wingMat = new THREE.MeshStandardMaterial({
    map: wingTex(), transparent: true, opacity: 0.62, roughness: 0.15,
    metalness: 0, side: THREE.DoubleSide, depthWrite: false,
  });

  // Abdomen: lathe from a traced profile (female pointed, male blunt).
  const prof = male  // [0,0] first: closes the rear tip (open lathes show a hole)
    ? [[0, 0], [0.10, 0.02], [0.28, 0.10], [0.40, 0.35], [0.44, 0.65], [0.42, 0.95], [0.36, 1.20], [0.26, 1.35]]
    : [[0, 0], [0.18, 0.08], [0.34, 0.30], [0.44, 0.60], [0.47, 0.90], [0.42, 1.20], [0.34, 1.40], [0.22, 1.50]];
  const abd = new THREE.Mesh(
    new THREE.LatheGeometry(prof.map(([x, y]) => new THREE.Vector2(x, y)), 48), abdomenMat);
  abd.geometry.rotateX(Math.PI / 2);   // axis → +Z, tip at z=0
  abd.position.set(0, 0.02, male ? -1.22 : -1.32);
  model.add(abd);

  // Thorax + head.
  const thorax = ball(0.5, thoraxMat, 0, 0.06, 0.18);
  thorax.geometry.rotateX(Math.PI / 2);  // stripes run front-to-back
  thorax.scale.set(0.86, 0.86, 1.10);
  model.add(thorax);
  const head = ball(0.36, cuticle, 0, 0.10, 0.72);
  head.scale.set(1.12, 0.92, 0.88);
  model.add(head);

  // Compound eyes + ocelli + antennae + proboscis.
  for (const sx of [1, -1]) {
    const eye = ball(0.27, eyeMat, sx * 0.20, 0.15, 0.70);
    eye.scale.set(0.82, 1.0, 0.95);  // seated into the head, less googly
    model.add(eye);
    const fun = ball(0.055, legMat, sx * 0.11, 0.02, 1.00);
    fun.scale.set(1, 1.2, 0.8);
    model.add(fun, ball(0.03, legMat, sx * 0.09, 0.06, 0.96));
    model.add(limb(V3(sx * 0.11, 0.02, 1.03), V3(sx * 0.22, -0.08, 1.36), 0.011, 0.007, dark));
  }
  model.add(ball(0.028, dark, 0, 0.42, 0.62));
  model.add(ball(0.028, dark, 0.06, 0.40, 0.58), ball(0.028, dark, -0.06, 0.40, 0.58));
  const prob = new THREE.Mesh(new THREE.ConeGeometry(0.07, 0.2, 16), legMat);
  prob.position.set(0, -0.20, 0.92); prob.rotation.x = Math.PI * 0.75;
  model.add(prob);

  // Animation rig refs (rest pose unchanged; the page drives these).
  const rig = { legs: [], wings: [] };
  // Wings: dihedral group > yaw group > blade.
  for (const sx of [1, -1]) {
    const dihedral = new THREE.Group(), yaw = new THREE.Group();
    rig.wings.push(yaw);
    const blade = new THREE.Mesh(wingGeo(sx), wingMat);
    blade.renderOrder = 2;
    blade.scale.set(1.18, 1, 1.28);  // broader blade, past the abdomen tip
    yaw.add(blade);
    yaw.rotation.y = sx * 1.35;  // swept back over the abdomen
    dihedral.add(yaw);
    dihedral.rotation.z = sx * 0.06;  // lying flatter
    dihedral.position.set(sx * 0.13, 0.40, -0.10);
    model.add(dihedral);
    // Halteres (Diptera signature): stalk + knob behind each wing.
    model.add(limb(V3(sx * 0.26, 0.26, -0.30), V3(sx * 0.48, 0.30, -0.46), 0.018, 0.014, paleMat));
    model.add(ball(0.055, paleMat, sx * 0.48, 0.30, -0.46));
  }

  // Legs: femur / tibia / tarsus posed per pair; males get a sex comb.
  // Each segment hangs off a joint group at identity rotation, so the rest
  // pose matches the old static build exactly; gait rotates the joints.
  const pairs = [[0.38, 0.12], [0.14, 0.0], [-0.12, -0.14]];
  pairs.forEach(([z, dz], pi) => {
    for (const sx of [1, -1]) {
      const hip = V3(sx * 0.24, -0.20, z), knee = V3(sx * 0.60, -0.58, z + dz),
        ankle = V3(sx * 0.44, -1.00, z + dz * 1.5 + 0.05), foot = V3(sx * 0.42, -1.30, z + 0.14);
      const hipG = new THREE.Group(); hipG.position.copy(hip);
      hipG.add(limb(new THREE.Vector3(), knee.clone().sub(hip), 0.042, 0.034, legMat));
      const kneeG = new THREE.Group(); kneeG.position.copy(knee).sub(hip);
      kneeG.add(limb(new THREE.Vector3(), ankle.clone().sub(knee), 0.028, 0.022, legMat));
      const ankleG = new THREE.Group(); ankleG.position.copy(ankle).sub(knee);
      ankleG.add(limb(new THREE.Vector3(), foot.clone().sub(ankle), 0.016, 0.010, legMat));
      kneeG.add(ankleG); hipG.add(kneeG); model.add(hipG);
      // Alternating tripod: (L1, R2, L3) vs (R1, L2, R3). The fly faces +Z,
      // so +X is its left.
      rig.legs.push({ hip: hipG, knee: kneeG, ankle: ankleG,
        phase: ((pi + (sx > 0 ? 1 : 0)) % 2) * Math.PI });
      if (male && pi === 0) {  // foreleg sex comb, rides the hip joint
        const comb = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.16, 0.03), dark);
        comb.position.set(sx * 0.18, -0.19, 0.10);
        comb.rotation.z = sx * 0.7;
        hipG.add(comb);
      }
    }
  });
  model.userData.rig = rig;

  // Bristles (macrochaetae): thorax dorsum, scutellum, head.
  const bristle = (x, y, z) => {
    const b = new THREE.Mesh(new THREE.ConeGeometry(0.008, 0.16, 6), dark);
    b.position.set(x, y, z); b.rotation.x = -0.95;
    model.add(b);
  };
  for (const sx of [1, -1]) {
    bristle(sx * 0.12, 0.56, -0.05); bristle(sx * 0.18, 0.54, -0.25);
    bristle(sx * 0.10, 0.58, 0.15); bristle(sx * 0.08, 0.46, -0.38);
    bristle(sx * 0.15, 0.40, 0.72);
  }

  if (male) model.scale.setScalar(0.82);  // true relative size (≈2.0 vs 2.5 mm)
  model.traverse((o) => { if (o.isMesh) o.frustumCulled = false; });
  return model;
}

export { buildFly };
