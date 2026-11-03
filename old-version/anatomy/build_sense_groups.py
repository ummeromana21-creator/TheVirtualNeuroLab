#!/usr/bin/env python3
"""Sense-group positions for the Atlas renders (Rocky's spec).

Reads: anatomy/celltypes/{types,positions,sides,rootids}.bin,
       Fly Brain/flywire/maxime_v783.npz (W, read-only),
       Databases/Flywire /classification.csv.gz (gustatory roots, read-only).
Writes: anatomy/celltypes/sense_groups.json {group: {indices, n, left, right,
            note}} + library/points/{photoreceptors,visual-targets,taste}.bin
        (Float32 xyz slices of positions.bin, viewer mapping applied later).
Fails loudly on count drift or missing groups.
"""
import gzip
import json
import os

import numpy as np
from scipy import sparse

HERE = os.path.dirname(os.path.abspath(__file__))
CELL = os.path.join(HERE, "celltypes")
LIBP = os.path.join(HERE, "..", "library", "points")
NPZ = os.path.join(os.path.expanduser("~"), "Desktop", "Fly Brain", "flywire", "maxime_v783.npz")
CLS = os.path.join(os.path.expanduser("~"), "Desktop", "Databases", "Flywire ", "classification.csv.gz")

VIS_TYPES = ("R1-6", "R7", "R8")


def main():
    fails = []
    tj = json.load(open(os.path.join(CELL, "types.json")))
    meta = tj.pop("_meta")
    n = meta["n"]
    pos = np.fromfile(os.path.join(CELL, "positions.bin"), dtype=np.float32).reshape(n, 3)
    sides = np.fromfile(os.path.join(CELL, "sides.bin"), dtype=np.uint8)
    roots = np.fromfile(os.path.join(CELL, "rootids.bin"), dtype=np.int64)
    by_root = {int(r): i for i, r in enumerate(roots)}

    # photoreceptors: R-type union (viewer truth)
    photo = sorted({i for t in VIS_TYPES for i in tj[t]["indices"]})

    # taste: gustatory roots from the classification table -> npz indices
    want = set()
    with gzip.open(CLS, "rt") as f:
        hdr = f.readline().strip().split(",")
        ri, cl = hdr.index("root_id"), hdr.index("class")
        for line in f:
            row = line.strip().split(",")
            if row[cl] == "gustatory":
                want.add(int(row[ri]))
    taste = sorted(by_root[r] for r in want if r in by_root)
    missing = len(want) - len(taste)
    print(f"taste: {len(want)} gustatory roots, {len(taste)} in cache ({missing} outside v783)")

    # visual targets: >25% input current from photoreceptors (the sim's own rule)
    z = np.load(NPZ, allow_pickle=True)
    assert int(z["n"]) == n, (int(z["n"]), n)
    W = sparse.csr_matrix((z["data"], z["indices"], z["indptr"]), shape=(n, n))
    import sys
    sys.path.insert(0, os.path.join(os.path.expanduser("~"), "Desktop", "Fly Brain"))
    import groups as G

    class B:
        pass
    b = B()
    b.W = W
    vt = G.visual_targets(b, photo)
    print(f"visual targets: {len(vt)} neurons at >25% photoreceptor input")

    out = {}
    for name, idx in (("photoreceptors", photo), ("taste", taste), ("visual_targets", sorted(int(i) for i in vt))):
        idx = np.array(idx, dtype=int)
        if not len(idx):
            fails.append(f"{name}: empty")
            continue
        out[name] = {"indices": [int(i) for i in idx], "n": len(idx),
                     "left": int(np.sum(sides[idx] == 1)), "right": int(np.sum(sides[idx] == 2)),
                     "note": {"photoreceptors": "R1-6/R7/R8 union from types.json (viewer truth).",
                              "taste": "gustatory class roots from classification.csv.gz mapped to cache order.",
                              "visual_targets": "sim rule: >25% input current from photoreceptors (groups.visual_targets)."}[name]}
        arr = pos[idx].astype(np.float32)
        fn = os.path.join(LIBP, name.replace("visual_targets", "visual-targets") + ".bin")
        arr.tofile(fn)
        print(f"{name}: n={len(idx)} L/R={out[name]['left']}/{out[name]['right']} -> {fn}")
    if fails:
        print("FAILURES:")
        for f in fails:
            print(" -", f)
        raise SystemExit("NOT YET")
    json.dump(out, open(os.path.join(CELL, "sense_groups.json"), "w"))
    print("wrote sense_groups.json")


if __name__ == "__main__":
    main()
