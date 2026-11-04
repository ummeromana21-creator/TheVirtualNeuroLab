// The lab fly's body: NeuroMechFly (Lobato-Rios et al. 2022, Nature Methods; flygym, Apache-2.0),
// a 3D body built from a micro-CT scan of a real adult Drosophila. Shapes and joint layout come from the scan;
// colours are added here. Lengths in mm.
export async function loadFly(T, base) {
  const meta = await (await fetch(base + 'fly_body.json')).json();
  const buf = await (await fetch(base + 'fly_body.bin')).arrayBuffer();
  const std = (o) => new T.MeshPhysicalMaterial(Object.assign({ roughness: .55, metalness: 0, clearcoat: .25, clearcoatRoughness: .5 }, o));
  const M = {
    eye: std({ color: 0x9a1c12, roughness: .32, clearcoat: .8, clearcoatRoughness: .25, sheen: .4, sheenColor: 0xff5a3c }),
    cuticle: std({ vertexColors: true }),
    leg: std({ vertexColors: true, roughness: .6 }),
    wing: new T.MeshPhysicalMaterial({ color: 0xe8ecf2, transparent: true, opacity: .16, roughness: .15, metalness: 0, side: T.DoubleSide,
      iridescence: .9, iridescenceIOR: 1.35, iridescenceThicknessRange: [180, 520], depthWrite: false }),
    arista: std({ color: 0x4a3626, roughness: .7 }),
    haltere: std({ color: 0xb08850 }),
  };
  const kind = n => n.endsWith('_eye') ? 'eye' : n.endsWith('_wing') ? 'wing' : n.endsWith('_arista') ? 'arista' : n.endsWith('_haltere') ? 'haltere'
    : /_(coxa|trochanterfemur|tibia|tarsus\d)$/.test(n) ? 'leg' : 'cuticle';
  // natural colouring: tan cuticle with fine speckle; dark rear band on each abdominal segment, dark tip
  function colourise(g, n) {
    const p = g.attributes.position, c = new Float32Array(p.count * 3); g.computeBoundingBox();
    const bb = g.boundingBox, len = Math.max(1e-6, bb.max.x - bb.min.x);
    let seed = 0; for (const ch of n) seed = (seed * 31 + ch.charCodeAt(0)) >>> 0;
    const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
    const tan = n.startsWith('c_abdomen') ? [.62, .42, .18] : /tarsus/.test(n) ? [.56, .38, .17] : /tibia|femur/.test(n) ? [.52, .34, .15] :
      n === 'c_thorax' ? [.42, .27, .11] : n === 'c_head' ? [.48, .31, .13] : [.46, .30, .13];
    const dark = [.07, .045, .03];
    for (let i = 0; i < p.count; i++) {
      let col = tan.slice();
      const s = 1 + (rnd() - .5) * .12; c.set(col.map(v => Math.min(1, v * s)), 3 * i);
    }
    g.setAttribute('color', new T.BufferAttribute(c, 3));
  }
  const root = new T.Group(), parts = {};
  for (const b of meta.bodies) {
    const node = new T.Group(); node.name = b.name;
    node.position.set(...b.pos); node.quaternion.set(b.quat[1], b.quat[2], b.quat[3], b.quat[0]);
    node.userData.rest = node.quaternion.clone(); node.userData.joints = b.joints;
    for (const g of b.geoms) {
      const geo = new T.BufferGeometry();
      geo.setAttribute('position', new T.BufferAttribute(new Float32Array(buf, g.v[0], g.v[1] * 3), 3));
      geo.setIndex(new T.BufferAttribute(new Uint32Array(buf, g.f[0], g.f[1] * 3), 1));
      geo.computeVertexNormals();
      const k = kind(b.name); if (k === 'cuticle' || k === 'leg') colourise(geo, b.name);
      const mat = M[k].clone(); mat.side = T.DoubleSide;
      const mesh = new T.Mesh(geo, mat); mesh.castShadow = k !== 'wing'; mesh.receiveShadow = true; node.add(mesh);
    }
    parts[b.name] = node;
    (b.parent ? parts[b.parent] : root).add(node);
  }
  // abdomen: dark band across the rear (posterior) part of each segment's upper side, as in a female fruit fly; pale underside; dark tip
  root.updateMatrixWorld(true); const inv = new T.Matrix4().copy(root.matrixWorld).invert(), v = new T.Vector3();
  for (const n of ['c_abdomen12', 'c_abdomen3', 'c_abdomen4', 'c_abdomen5', 'c_abdomen6']) {
    const mesh = parts[n] && parts[n].children.find(o => o.isMesh); if (!mesh) continue;
    const g = mesh.geometry, p = g.attributes.position, c = g.attributes.color, mw = new T.Matrix4().multiplyMatrices(inv, mesh.matrixWorld);
    let x0 = Infinity, x1 = -Infinity, z0 = Infinity, z1 = -Infinity; const xs = new Float32Array(p.count), zs = new Float32Array(p.count);
    for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i).applyMatrix4(mw); xs[i] = v.x; zs[i] = v.z; x0 = Math.min(x0, v.x); x1 = Math.max(x1, v.x); z0 = Math.min(z0, v.z); z1 = Math.max(z1, v.z); }
    for (let i = 0; i < p.count; i++) {
      const f = (xs[i] - x0) / (x1 - x0 + 1e-9), h = (zs[i] - z0) / (z1 - z0 + 1e-9);   // f: 0 rear .. 1 front; h: 0 belly .. 1 back
      let band = n === 'c_abdomen6' ? .9 : n === 'c_abdomen12' ? 0 : Math.max(0, Math.min(1, (.5 - f) / .2));
      band *= Math.max(0, Math.min(1, (h - .3) / .2));                                   // bands on the back and sides only
      const belly = Math.max(0, Math.min(1, (.35 - h) / .25)) * .55;
      const r = c.getX(i), gg = c.getY(i), b = c.getZ(i);
      let col = [r, gg, b].map((x, k) => x * (1 - band) + [.07, .045, .03][k] * band);
      col = col.map((x, k) => x * (1 - belly) + [.80, .68, .48][k] * belly);
      c.setXYZ(i, ...col);
    }
    c.needsUpdate = true;
  }
  // rotate a body segment about one of its own joint axes (radians), on top of the neutral standing pose
  const tmp = new T.Quaternion(), ax = new T.Vector3();
  function pose(angles) {
    for (const n in parts) parts[n].quaternion.copy(parts[n].userData.rest);
    for (const [jn, a] of Object.entries(angles)) {
      const seg = jn.split('-')[1], node = parts[seg]; if (!node) continue;
      const j = node.userData.joints.find(x => x.name === jn); if (!j) continue;
      ax.set(...j.axis); node.quaternion.multiply(tmp.setFromAxisAngle(ax, a));
    }
  }
  return { root, parts, pose, meta };
}
