"""Build the atlas cell-type position store from the FlyWire v783 export.

Reads (in place, never modified):
  maxime_v783.npz .... root_id, primary_type, side, nt_type in cache order
  coordinates.csv.gz  root_id -> one recorded Codex point per neuron, nanometres
  ../../library/celltypes.json  the atlas's 236 cell-type entries (names only)

Writes (all under anatomy/celltypes/):
  positions.bin  Float32 x,y,z per neuron, micrometres, centred (cache order)
  sides.bin      UInt8 per neuron: 0 unknown/central, 1 left, 2 right
  rootids.bin    int64 per neuron (click -> Codex link; same order)
  types.json     per-type indices/counts/side split/transmitters (+ _meta)
  stills/<type>.png  front-view still per in-file type for the atlas cards

Conventions (see README "Cell-type positions"):
  - nm -> um by /1000; centred by subtracting the all-neuron mean. No scaling,
    so the viewer's orthographic scale bar is exact.
  - coordinates.csv.gz holds several rows per root; the recorded point is the
    FIRST row per root_id (same rule as flywire_brain.py; verified to reproduce
    the npz xyz exactly for all 139,255 neurons).
  - axes of the raw export, determined from the data: axis0 = left-right
    (left low), axis1 = dorsal-ventral (dorsal low), axis2 = anterior-posterior
    (anterior low). Front view = fly facing the viewer, dorsal up.
"""
import csv
import gzip
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "celltypes")
STILLS = os.path.join(OUT, "stills")

HOME = os.path.expanduser("~")
NPZ_CANDS = [
    os.path.join(HERE, "maxime_v783.npz"),
    os.path.join(HOME, "Desktop", "Fly Brain", "flywire", "maxime_v783.npz"),
]
COORD_CANDS = [
    os.path.join(HOME, "Desktop", "Databases", "Flywire ", "coordinates.csv.gz"),
    os.path.join(HOME, "Desktop", "Databases", "Flywire", "coordinates.csv.gz"),
]
SHEET = os.path.join(HERE, "..", "library", "celltypes.json")

TEAL = "#0f766e"   # left (Feather-day readable)
AMBER = "#b45309"  # right (Feather-day readable)
GREY_LIT = "#64748b"  # central/unknown side, still part of the type
BG = "#fbf8f1"  # Feather day panel, so card thumbs blend in
BGDOT = "#b9c2cf"
TEXT = "#6d685d"


def first_hit(cands, what):
    for c in cands:
        if os.path.exists(c):
            return c
    raise FileNotFoundError(f"no {what}; tried: " + ", ".join(cands))


def load_coords(path):
    """First row per root_id -> (x, y, z) nanometres."""
    pts = {}
    with gzip.open(path, "rt", newline="") as f:
        for row in csv.DictReader(f):
            r = int(row["root_id"])
            if r not in pts:
                pts[r] = tuple(int(v) for v in row["position"].strip("[]").split())
    return pts


def main():
    npz_path = first_hit(NPZ_CANDS, "maxime_v783.npz")
    coord_path = first_hit(COORD_CANDS, "coordinates.csv.gz")
    sheet = json.load(open(SHEET))
    names = [e["name"] for e in sheet]
    func = {e["name"]: e.get("func") for e in sheet}
    print(f"sheet types: {len(names)}")

    z = np.load(npz_path, allow_pickle=True)
    rid = np.array(z["root_id"]).astype(np.int64)
    ptype = np.array(z["primary_type"]).astype(str)
    side = np.array(z["side"]).astype(str)
    nt = np.array(z["nt_type"]).astype(str)
    n = len(rid)
    print(f"npz neurons: {n} from {npz_path}")

    pts = load_coords(coord_path)
    print(f"coord roots: {len(pts)} from {coord_path}")
    missing = [int(r) for r in rid if int(r) not in pts]
    if missing:
        raise SystemExit(f"{len(missing)} npz neurons lack coordinates, e.g. {missing[:3]}")

    P = np.array([pts[int(r)] for r in rid], dtype=np.float64) / 1000.0  # um
    centre = P.mean(axis=0)
    Pc = (P - centre).astype(np.float32)

    smap = {"left": 1, "right": 2}
    S = np.array([smap.get(s, 0) for s in side], dtype=np.uint8)

    os.makedirs(STILLS, exist_ok=True)
    Pc.tofile(os.path.join(OUT, "positions.bin"))
    S.tofile(os.path.join(OUT, "sides.bin"))
    rid.tofile(os.path.join(OUT, "rootids.bin"))

    by_type = {}
    for i, t in enumerate(ptype):
        by_type.setdefault(t, []).append(i)
    print(f"file types: {len(by_type)}")

    NT_ORDER = ["ACH", "GABA", "GLUT", "DA", "SER", "OCT"]
    types = {}
    absent = []
    for name in names:
        idx = by_type.get(name)
        if not idx:
            # FlyWire FAFB covers the brain only; motor/cord-flavoured names
            # are absent for that reason, others are simply not labelled.
            low = name.lower()
            reason = ("brain-only dataset" if any(k in low for k in ("motor", "vnc", "leg", "wing", "haltere", "neck"))
                      else "not labelled in v783")
            types[name] = {"in_file": False, "reason": reason}
            absent.append(name)
            continue
        idx = np.array(idx)
        sd = side[idx]
        ntc = {k: int(np.sum(nt[idx] == k)) for k in NT_ORDER}
        ntc = {k: v for k, v in ntc.items() if v}
        unk = int(np.sum(nt[idx] == ""))
        if unk:
            ntc["unknown"] = unk
        types[name] = {
            "in_file": True,
            "indices": [int(i) for i in idx],
            "n": len(idx),
            "left": int(np.sum(sd == "left")),
            "right": int(np.sum(sd == "right")),
            "nt": ntc,
            "func": func.get(name),
        }
    types["_meta"] = {
        "n": n,
        "unit": "micrometre",
        "centre_um": [round(float(v), 3) for v in centre],
        "bbox_um": [[round(float(v), 1) for v in P.min(axis=0)],
                    [round(float(v), 1) for v in P.max(axis=0)]],
        "side_counts": {"unknown": int(np.sum(S == 0)), "left": int(np.sum(S == 1)),
                        "right": int(np.sum(S == 2))},
        "axes": "x left-right (left low), y dorsal-ventral (dorsal low), "
                "z anterior-posterior (anterior low)",
        "sources": {"npz": os.path.basename(npz_path), "coords": "coordinates.csv.gz"},
    }
    with open(os.path.join(OUT, "types.json"), "w") as f:
        json.dump(types, f)
    print(f"types.json: {len(names) - len(absent)} in file, {len(absent)} absent {absent}")

    # ---- stills: front view, fly facing viewer, dorsal up ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rng = np.random.default_rng(783)
    bg = rng.choice(n, size=min(n, 50000), replace=False)
    bx, by = -Pc[bg, 0], -Pc[bg, 1]
    lo = Pc.min(axis=0)
    span = Pc.max(axis=0) - lo
    for name in names:
        t = types[name]
        if not t["in_file"]:
            continue
        idx = np.array(t["indices"])
        fig, ax = plt.subplots(figsize=(6.4, 4.8), facecolor=BG)
        ax.set_facecolor(BG)
        ax.scatter(bx, by, s=1, c=BGDOT, alpha=0.5, linewidths=0, rasterized=True)
        sd = side[idx]
        for mask, col in ((sd == "left", TEAL), (sd == "right", AMBER),
                          (~np.isin(sd, ("left", "right")), GREY_LIT)):
            if np.any(mask):
                ax.scatter(-Pc[idx[mask], 0], -Pc[idx[mask], 1], s=4, c=col,
                           alpha=0.9, linewidths=0, rasterized=True)
        ax.set_xlim(-(lo[0] + span[0]) - 10, -lo[0] + 10)
        ax.set_ylim(-(lo[1] + span[1]) - 10, -lo[1] + 10)
        ax.set_aspect("equal")
        ax.axis("off")
        known = {k: v for k, v in t["nt"].items() if k != "unknown"}
        tot = sum(known.values())
        unk = t["nt"].get("unknown", 0)
        if not tot:
            tops = "unpredicted"
        else:
            best = max(known.values())
            winners = sorted(k for k, v in known.items() if v == best)
            tops = ("/".join(winners) + f" tie {round(100 * best / tot)}%"
                    if len(winners) > 1 else f"{winners[0]} {round(100 * best / tot)}%")
            if best / tot <= 0.60:
                tops += " — mixed prediction"
        if unk:
            tops += f" · {round(100 * unk / t['n'])}% unpredicted"
        fig.text(0.04, 0.02,
                 f"{name}  ·  {t['n']} neurons ({t['left']}L/{t['right']}R)  ·  {tops}\n"
                 f"FlyWire FAFB v783 · one recorded point per neuron · front view, dorsal up · "
                 f"Not simulated. Anatomy only.",
                 color=TEXT, fontsize=7, va="bottom", ha="left")
        fig.savefig(os.path.join(STILLS, f"{name}.png"), dpi=100, facecolor=BG)
        plt.close(fig)
    print(f"stills: {sum(1 for nm in names if types[nm]['in_file'])} written")
    print("done.")


if __name__ == "__main__":
    main()
