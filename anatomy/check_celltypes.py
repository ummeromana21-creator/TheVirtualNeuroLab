"""Referee for the atlas cell-type viewer.

Build first:
  cd metaverse-lab/anatomy && python3 build_celltypes.py \\
      && python3 update_atlas_cards.py && python3 check_celltypes.py
"""
import json
import os
import re
import shutil
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
fails = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        fails.append(name)


sheet = json.load(open(os.path.join(HERE, "..", "library", "celltypes.json")))
names = [e["name"] for e in sheet]
tj = json.load(open(os.path.join(HERE, "celltypes", "types.json")))
meta = tj.pop("_meta")

check("236 sheet types", len(names) == 236, len(names))
check("every sheet type in types.json", all(n in tj for n in names),
      [n for n in names if n not in tj][:3])
check("no extra types", set(tj) == set(names), sorted(set(tj) ^ set(names))[:3])

# ---- fresh count from the npz (read-only) ----
npz_path = os.path.join(os.path.expanduser("~"), "Desktop", "Fly Brain", "flywire", "maxime_v783.npz")
z = np.load(npz_path, allow_pickle=True)
rid = np.array(z["root_id"]).astype(np.int64)
ptype = np.array(z["primary_type"]).astype(str)
side = np.array(z["side"]).astype(str)
nt = np.array(z["nt_type"]).astype(str)
n = len(rid)
check("npz neuron count", n == meta["n"] == 139255, (n, meta["n"]))

bad_n, bad_idx, bad_side, bad_nt = [], [], [], []
for name in names:
    t = tj[name]
    if not t["in_file"]:
        continue
    want = np.nonzero(ptype == name)[0]
    if t["n"] != len(want) or t["indices"] != [int(i) for i in want]:
        bad_n.append(name)
        continue
    idx = np.array(t["indices"])
    if t["left"] != int(np.sum(side[idx] == "left")) or t["right"] != int(np.sum(side[idx] == "right")):
        bad_side.append(name)
    fresh = {}
    for k in ("ACH", "GABA", "GLUT", "DA", "SER", "OCT"):
        c = int(np.sum(nt[idx] == k))
        if c:
            fresh[k] = c
    u = int(np.sum(nt[idx] == ""))
    if u:
        fresh["unknown"] = u
    if t["nt"] != fresh:
        bad_nt.append(name)
infile = [nm for nm in names if tj[nm]["in_file"]]
check("counts equal fresh npz counts", not bad_n, bad_n[:3])
check("indices point at the type", not bad_idx)
check("left/right match file sides", not bad_side, bad_side[:3])
check("nt splits match file", not bad_nt, bad_nt[:3])

# ---- binaries ----
pos = np.fromfile(os.path.join(HERE, "celltypes", "positions.bin"), dtype=np.float32)
check("positions shape", pos.shape == (n * 3,), pos.shape)
check("positions finite", bool(np.isfinite(pos).all()))
check("positions are um-scale", 200 < pos.max() - pos.min() < 2000, float(pos.max() - pos.min()))
sides = np.fromfile(os.path.join(HERE, "celltypes", "sides.bin"), dtype=np.uint8)
check("sides shape+codes", sides.shape == (n,) and set(np.unique(sides)) <= {0, 1, 2}, sides.shape)
check("sides match file", bool(np.all(sides == np.array([{"left": 1, "right": 2}.get(s, 0) for s in side], dtype=np.uint8))))
roots = np.fromfile(os.path.join(HERE, "celltypes", "rootids.bin"), dtype=np.int64)
check("rootids match npz", roots.shape == (n,) and bool(np.all(roots == rid)), roots.shape)
P = pos.reshape(n, 3).astype(np.float64) + np.array(meta["centre_um"])  # bins are centred
bb = [[round(float(v), 1) for v in P.min(axis=0)], [round(float(v), 1) for v in P.max(axis=0)]]
check("meta bbox matches bins",
      all(abs(a - b) < 0.2 for row_a, row_b in zip(meta["bbox_um"], bb) for a, b in zip(row_a, row_b)),
      meta["bbox_um"])

# ---- stills ----
stills = [nm for nm in infile
          if os.path.exists(os.path.join(HERE, "celltypes", "stills", f"{nm}.png"))]
check("every in-file type has a still", len(stills) == len(infile), len(infile) - len(stills))
sizes = [os.path.getsize(os.path.join(HERE, "celltypes", "stills", f"{nm}.png")) for nm in stills]
check("stills non-trivial", all(s > 20000 for s in sizes), min(sizes) if sizes else 0)

# ---- viewer (embedded in the atlas detail view): assets, logic ----
check("standalone page dropped", not os.path.exists(os.path.join(HERE, "celltype.html")))
lib = os.path.join(HERE, "..", "library")
js = open(os.path.join(lib, "app.js")).read()
html = open(os.path.join(lib, "index.html")).read()
for ref in ("celltypes/types.json", "celltypes/positions.bin", "celltypes/sides.bin",
            "celltypes/rootids.bin"):
    check(f"embed fetches {ref}", f"../anatomy/{ref}" in js and
          os.path.exists(os.path.join(HERE, ref.split("?")[0])))
check("embed imports logic", 'from "../anatomy/celltype_logic.js?v=1"' in js and
      os.path.exists(os.path.join(HERE, "celltype_logic.js")))
check("embed importmap has addons", '"three/addons/": "../vendor/three/addons/"' in html)
check("no CDN scripts", 'src="http' not in js and "from \"http" not in js)
for feat in ("codex.flywire.ai/app/cell_details", "showCell",
             "setAnimationLoop", "OrthographicCamera", "cellwrap"):
    check(f"embed has {feat}", feat in js)
check("embed scale bar", "100 µm" in html and 'id="cvscale"' in html)

# ---- skeletons: one traced shape for 25 most-studied types ----
SKEL25 = ["R1-6", "R7", "R8", "L1", "L2", "L3", "Mi1", "Tm1", "Tm2", "Tm9",
          "T4a", "T5a", "LC10a", "LPLC2", "Dm8a", "ORN_V", "ORN_DM1",
          "ORN_VA1v", "KCab", "KCg-m", "PFNa", "BM_Taste", "JO-A", "T2", "C2"]
skdir = os.path.join(HERE, "celltypes", "skeletons")
have = [t for t in SKEL25 if os.path.exists(os.path.join(skdir, f"{t}.json"))]
check("25 skeleton files", len(have) == 25, sorted(set(SKEL25) - set(have)))
bad_sk, bad_edge, bad_box, bad_root, bad_check = [], [], [], [], []
lo = np.array(meta["bbox_um"][0]) - np.array(meta["centre_um"])
hi = np.array(meta["bbox_um"][1]) - np.array(meta["centre_um"])
rootset = set(int(r) for r in rid)
for t in have:
    s = json.load(open(os.path.join(skdir, f"{t}.json")))
    if (s.get("type") != t or not isinstance(s.get("root_id"), int)
            or s.get("dataset") != "FlyWire FAFB v783 LOD1 healed"):
        bad_sk.append(t)
        continue
    nd = np.array(s["nodes"], dtype=float)
    ed = np.array(s["edges"], dtype=int)
    if (nd.ndim != 2 or nd.shape[1] != 3 or len(nd) < 5
            or not np.isfinite(nd).all()
            or ed.ndim != 2 or ed.shape[1] != 2 or len(ed) == 0
            or ed.min() < 0 or ed.max() >= len(nd)):
        bad_edge.append(t)
        continue
    if bool((nd.min(axis=0) < lo - 1).any()) or bool((nd.max(axis=0) > hi + 1).any()):
        bad_box.append(t)
    if s["root_id"] not in rootset:
        bad_root.append(t)
    if not (s["n_kept"] == len(nd) and s["n_full"] >= len(nd)
            and s["check_um"] < 30):
        bad_check.append(t)
check("skeleton schema", not bad_sk, bad_sk[:3])
check("skeleton nodes+edges sane", not bad_edge, bad_edge[:3])
check("skeletons inside brain bbox", not bad_box, bad_box[:3])
check("skeleton roots real", not bad_root, bad_root[:3])
check("skeleton self-checks hold", not bad_check, bad_check[:3])
check("viewer draws skeletons", "celltypes/skeletons/" in js and "LineSegments" in js
      and "skeltoggle" in js)

# ---- wiring: strongest-500 outgoing edges per type ----
wdir = os.path.join(HERE, "celltypes", "edges")
whave = [t for t in names if os.path.exists(os.path.join(wdir, f"{t}.json"))]
check("236 wiring files", len(whave) == 236, sorted(set(names) - set(whave))[:3])
bad_w, bad_wix = [], []
for t in whave:
    s = json.load(open(os.path.join(wdir, f"{t}.json")))
    ed = s.get("edges", [])
    if (s.get("type") != t or not isinstance(s.get("n_out_full"), int)
            or not ed or len(ed) > 500 or s["n_out_full"] < len(ed)):
        bad_w.append(t)
        continue
    flat = [i for e in ed for i in e]
    if (any(not isinstance(i, int) for i in flat) or min(flat) < 0 or max(flat) >= n
            or any(len(e) != 2 for e in ed)):
        bad_wix.append(t)
check("wiring schema", not bad_w, bad_w[:3])
check("wiring indices valid", not bad_wix, bad_wix[:3])
check("viewer draws wiring", "celltypes/edges/" in js and "wiretoggle" in js
      and "braintoggle" in js and "bgPts.visible" in js)

if shutil.which("node"):
    shutil.copyfile(os.path.join(lib, "app.js"), "/tmp/ctview.mjs")
    shutil.copyfile(os.path.join(HERE, "celltype_logic.js"), "/tmp/ctlogic.mjs")
    r = subprocess.run(["node", "--check", "/tmp/ctlogic.mjs"], capture_output=True)
    check("logic syntax", r.returncode == 0, r.stderr.decode()[:200])
    r = subprocess.run(["node", "--check", "/tmp/ctview.mjs"], capture_output=True)
    check("viewer syntax", r.returncode == 0, r.stderr.decode()[:300])
    harness = """
import {stem, siblings, sideName, ntSummary, ntFull, parseHash, isCollapsed} from "/tmp/ctlogic.mjs";
import {readFileSync} from "fs";
const tj = JSON.parse(readFileSync("__HERE__/celltypes/types.json"));
delete tj._meta;
const NAMES = Object.keys(tj);
const fail = [];
const eq = (a, b, m) => { if (JSON.stringify(a) !== JSON.stringify(b)) fail.push(m + " got " + JSON.stringify(a)); };
// pinned rules
eq(stem("T4a"), "T4", "stem");
eq(stem("EPG"), "EPG", "stem-nostrip");
eq(siblings(NAMES, "T4a").sort(), ["T4b", "T4c", "T4d"], "sibs");
eq(sideName(1) + "/" + sideName(2) + "/" + sideName(0), "left/right/central/unknown", "sides");
eq(ntSummary(tj.ORN_V.nt, 67).text, "ACH/SER tie 47% — mixed prediction · 46% unpredicted", "ornv");
eq(ntSummary(tj.Mi1.nt, 1581).mixed, false, "mi1-nomix");
eq(parseHash("#ORN_V"), "ORN_V", "hash");
// three random types: lookup, split text, collapse rule run clean
let seed = 42; const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
for (let k = 0; k < 3; k++) {
  const nm = NAMES[Math.floor(rnd() * NAMES.length)];
  const t = tj[nm];
  if (!t.in_file || !t.indices.length) fail.push("empty " + nm);
  ntFull(t.nt); ntSummary(t.nt, t.n); siblings(NAMES, nm); isCollapsed(10, 900, t.n);
}
if (fail.length) { console.log("LOGIC FAIL " + fail.join(" | ")); process.exit(1); }
console.log("LOGIC ALL PASS");
""".replace("__HERE__", HERE)
    open("/tmp/ctlogic-test.mjs", "w").write(harness)
    r = subprocess.run(["node", "/tmp/ctlogic-test.mjs"], capture_output=True)
    check("viewer logic on real data", r.returncode == 0,
          (r.stdout.decode() + r.stderr.decode())[:300])
else:
    print("SKIP node checks (no node)")

print()
print("RESULT:", "ALL CHECKS PASSED" if not fails else f"FAILURES: {fails}")
print("NOTE: live browser rendering needs your pass at /library/#/Mi1 — no browser in this sandbox.")
sys.exit(1 if fails else 0)
