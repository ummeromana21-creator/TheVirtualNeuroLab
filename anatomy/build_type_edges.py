#!/usr/bin/env python3
"""Top-500 outgoing connections per atlas cell type, for the viewer wiring toggle.

Reads: Fly Brain/flywire/maxime_v783.npz (sparse W + primary_type, read-only),
       anatomy/celltypes/types.json (the 236 atlas types).
Writes: anatomy/celltypes/edges/<TYPE>.json {edges: [[pre, post], ...], n_out_full}.
Fails loudly on shape drift or an empty type.
"""
import json
import os

import numpy as np
from scipy import sparse

HERE = os.path.dirname(os.path.abspath(__file__))
CELL = os.path.join(HERE, "celltypes")
OUT = os.path.join(CELL, "edges")
NPZ = os.path.join(os.path.expanduser("~"), "Desktop", "Fly Brain", "flywire", "maxime_v783.npz")
TOP = 500


def main():
    types = json.load(open(os.path.join(CELL, "types.json")))
    meta = types.pop("_meta")
    z = np.load(NPZ, allow_pickle=True)
    n = int(z["n"])
    assert n == meta["n"] == 139255, (n, meta["n"])
    W = sparse.csr_matrix((z["data"], z["indices"], z["indptr"]), shape=(n, n))
    os.makedirs(OUT, exist_ok=True)
    done = 0
    for name, t in sorted(types.items()):
        idx = np.array(t["indices"], dtype=int)
        assert len(idx) > 0, f"{name}: empty type"
        sub = W[idx, :]
        coo = sub.tocoo()
        order = np.argsort(-np.abs(coo.data), kind="stable")[:TOP]
        edges = [[int(idx[coo.row[k]]), int(coo.col[k])] for k in order]
        assert edges, f"{name}: no outgoing edges"
        with open(os.path.join(OUT, f"{name}.json"), "w") as f:
            json.dump({"type": name, "edges": edges, "n_out_full": int(coo.nnz)}, f)
        done += 1
    print(f"edges: {done}/236 types, top {TOP} outgoing each -> {OUT}")


if __name__ == "__main__":
    main()
