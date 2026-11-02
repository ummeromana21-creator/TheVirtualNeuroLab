#!/usr/bin/env python3
"""Real neuron shapes for 25 most-studied atlas types.

Reads one traced skeleton (SWC, LOD1 healed) per type from the FlyWire
sk_lod1_783_healed.zip archive -- no full extraction, only 25 files --
collapses straight chains to branch points (shape-preserving), converts
nm -> um with the same centre as positions.bin, and writes one compact
JSON per type for the celltype viewer.

Outputs (all under anatomy/celltypes/skeletons/):
  <TYPE>.json  {root_id, side, nodes, edges, n_full, n_kept, check_um}

Self-check per skeleton: the neuron's recorded point must sit within
30 um of its own traced arbor (same cell, two views of it).
Fails loudly on any miss.
"""
import json
import os
import zipfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CELL = os.path.join(HERE, "celltypes")
OUT = os.path.join(CELL, "skeletons")
ZIP = os.path.expanduser("~/Desktop/Databases/Flywire /sk_lod1_783_healed.zip")

# One per row: vision column, motion, feature detectors, smell, memory,
# central complex, taste/hearing, centrifugal. All must be in_file.
TYPES = [
    "R1-6", "R7", "R8", "L1", "L2", "L3", "Mi1", "Tm1", "Tm2", "Tm9",
    "T4a", "T5a", "LC10a", "LPLC2", "Dm8a", "ORN_V", "ORN_DM1",
    "ORN_VA1v", "KCab", "KCg-m", "PFNa", "BM_Taste", "JO-A", "T2", "C2",
]
assert len(TYPES) == 25, len(TYPES)

MAX_NODES = 20000  # representative must be under this, else next-closest


def parse_swc(text):
    ids, xyz, parent = [], [], []
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        p = line.split()
        if len(p) < 7:
            continue
        ids.append(int(p[0]))
        xyz.append([float(p[2]), float(p[3]), float(p[4])])
        parent.append(int(p[6]))
    return np.array(ids), np.array(xyz), np.array(parent)


def collapse(ids, xyz, parent):
    """Keep roots, terminals and branch points; re-link chains."""
    order = {v: i for i, v in enumerate(ids)}
    kids = {v: [] for v in ids}
    roots = []
    for v, p in zip(ids, parent):
        if p < 0 or p not in order:
            roots.append(v)
        else:
            kids[p].append(v)
    keep = set(roots)
    for v in ids:
        if len(kids[v]) != 1:
            keep.add(v)
    kept = sorted(keep)
    new_ix = {v: i for i, v in enumerate(kept)}
    nodes = np.array([xyz[order[v]] for v in kept])
    edges = []
    for v in kept:
        # nearest kept ancestor
        p = parent[order[v]]
        while p >= 0 and p in order and p not in keep:
            p = parent[order[p]]
        if p in keep:
            edges.append([new_ix[p], new_ix[v]])
    return nodes, np.array(edges, dtype=np.int64)


def main():
    types = json.load(open(os.path.join(CELL, "types.json")))
    meta = types["_meta"]
    centre = np.array(meta["centre_um"]) * 1000.0  # work in nm
    n = meta["n"]
    pos = np.fromfile(os.path.join(CELL, "positions.bin"),
                      dtype=np.float32).reshape(n, 3)
    roots = np.fromfile(os.path.join(CELL, "rootids.bin"),
                        dtype=np.uint64)
    zf = zipfile.ZipFile(ZIP)
    names = set(zf.namelist())
    os.makedirs(OUT, exist_ok=True)

    done = []
    for tname in TYPES:
        t = types.get(tname)
        assert t and t["in_file"], f"{tname} not in file"
        idx = np.array(t["indices"])
        med = np.median(pos[idx], axis=0)
        dist = np.linalg.norm(pos[idx] - med, axis=1)
        order = np.argsort(dist, kind="stable")
        picked = None
        for j in order:
            rid = str(int(roots[idx[j]])) + ".swc"
            if rid not in names:
                continue
            if zf.getinfo(rid).file_size > MAX_NODES * 45:
                continue
            picked = (idx[j], rid)
            break
        assert picked, f"{tname}: no usable skeleton in zip"
        j, rid = picked
        ids, xyz, par = parse_swc(zf.read(rid).decode())
        assert len(ids) > 5, f"{tname}: skeleton too small ({len(ids)})"
        nodes, edges = collapse(ids, xyz, par)
        um = nodes / 1000.0 - centre / 1000.0
        # recorded point is one point on the cell: it must sit near the
        # arbor (min distance), not near its middle (long cells fail that).
        check = float(np.linalg.norm(um - pos[j], axis=1).min())
        assert check < 30, f"{tname}: recorded point {check:.1f} um off arbor"
        assert len(edges) > 0, f"{tname}: no edges after collapse"
        out = {
            "type": tname,
            "root_id": int(rid[:-4]),
            "dataset": "FlyWire FAFB v783 LOD1 healed",
            "nodes": [[round(float(a), 2) for a in row] for row in um],
            "edges": [[int(a), int(b)] for a, b in edges],
            "n_full": int(len(ids)),
            "n_kept": int(len(um)),
            "check_um": round(check, 1),
        }
        with open(os.path.join(OUT, f"{tname}.json"), "w") as f:
            json.dump(out, f)
        done.append((tname, len(ids), len(um), check))
        print(f"{tname}: {len(ids)} -> {len(um)} nodes, "
              f"check {check:.1f} um")
    print(f"skeletons: {len(done)}/25 written to {OUT}")


if __name__ == "__main__":
    main()
