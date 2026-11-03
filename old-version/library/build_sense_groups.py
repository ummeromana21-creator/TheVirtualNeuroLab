"""Build Atlas sense-group cards (photoreceptors / taste / visual targets).

Reads (never modified):
  anatomy/celltypes/sense_groups.json   indices, n, L/R, notes, sim counts
  anatomy/celltypes/positions.bin       139,255-point um frame (slice source)
  library/points/somas.bin              normalized stage frame (span check)
  library/points/classes.bin + index.json  dim background classes for renders
Writes:
  library/points/{photoreceptors,taste,visual-targets}.bin  group slices in
      the normalized stage frame (bbox-mid center, x-span -> [-1, 1]), the
      somas.bin convention from build_celltype_points.py. The raw um slices
      are regenerable via anatomy/build_sense_groups.py; these are the
      viewer-facing artifacts ("viewer mapping applied later").
  library/img/row40{00,01,02}_*.jpg     600x345 light row renders (front view,
      dim somas + lit group, baked header like the region rows)
  library/sensegroups.json              3 rows, data.json-shaped (level "sense",
      hub "senses", rows 4000+). Female neuron counts are v783 anatomy; male
      and synapse counts are null (unmapped / uncounted), stated in desc.

Run:  cd metaverse-lab/library && python3 build_sense_groups.py && python3 check.py
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CELL = os.path.join(HERE, "..", "anatomy", "celltypes")
N = 139255

GROUPS = [
    dict(key="photoreceptors", name="photoreceptors", row=4000,
         func="light sensing", head="photoreceptors \u00b7 R1-6, R7, R8 \u00b7 light sensing"),
    dict(key="taste", name="taste", row=4001,
         func="taste", head="taste \u00b7 gustatory neurons \u00b7 taste"),
    dict(key="visual_targets", name="visual-targets", row=4002,
         func="early vision", head="visual targets \u00b7 >25% photoreceptor input \u00b7 early vision"),
]
SUBLINE = ("Real FlyWire female brain, front view. Dots = all 139,255 cells; "
           "lit = this group, both sides. Not simulated.")
BG = "#fbf8f1"
LIT = "#b941a0"
SOMAC_DAY = {  # same palette as app.js, for the dim class-colored background
    "optic": 0x2f5da3, "central": 0x8a6d1a, "sensory": 0x1e7d4f,
    "visual_projection": 0x6a4fb3, "descending": 0xb03a3a,
    "ascending": 0xc26a8a, "visual_centrifugal": 0x2a7f9e,
    "motor": 0x555555, "endocrine": 0x888888,
}


def main():
    sg = json.load(open(os.path.join(CELL, "sense_groups.json")))
    pos = np.fromfile(os.path.join(CELL, "positions.bin"),
                      dtype=np.float32).reshape(N, 3).astype(np.float64)
    somas = np.fromfile(os.path.join(HERE, "points", "somas.bin"),
                        dtype=np.float32).reshape(N, 3)
    # normalization: same set as somas.bin, so its own bbox gives the same
    # frame (uniform scale + translation cancel out). Verify against somas.
    mid = (pos.min(0) + pos.max(0)) / 2
    s = (pos.max(0) - pos.min(0))[0] / 2
    q = (pos - mid) / s
    assert abs(q[:, 0].min() + 1) < 1e-6 and abs(q[:, 0].max() - 1) < 1e-6
    for a in range(3):
        ours = np.sort(q[:, a].astype(np.float32))
        ref = np.sort(somas[:, a])
        assert np.allclose(ours, ref, atol=2e-3), f"frame drift on axis {a}"
    print(f"frame ok: mid={mid.round(1)} s={s:.1f} (matches somas.bin distribution)")

    cls = np.fromfile(os.path.join(HERE, "points", "classes.bin"), dtype=np.uint8)
    names = json.load(open(os.path.join(HERE, "points", "index.json")))["classes"]
    def rgb(c):
        h = SOMAC_DAY.get(names[c], 0x888888) if c < len(names) else 0x888888
        return [((h >> 16) & 255) / 255, ((h >> 8) & 255) / 255, (h & 255) / 255]
    pal = np.array([rgb(c) for c in cls])

    rows = []
    for g in GROUPS:
        d = sg[g["key"]]
        idx = np.array(d["indices"], dtype=int)
        assert len(idx) == d["n"], g["key"]
        raw = np.fromfile(os.path.join(HERE, "points", g["name"] + ".bin"),
                          dtype=np.float32).reshape(-1, 3)
        assert raw.shape[0] == d["n"] and np.array_equal(
            raw, pos[idx].astype(np.float32)), f"{g['key']}: slice != positions[idx]"
        pts = ((pos[idx] - mid) / s).astype(np.float32)
        pts.tofile(os.path.join(HERE, "points", g["name"] + ".bin"))
        img = "img/row%d_%s.jpg" % (g["row"], g["name"])
        render_jpg(somas, pal, pts, g["head"], os.path.join(HERE, img))
        rows.append(descs(g, d, img))
        print("%s: n=%d L/R=%d/%d -> points/%s.bin + %s"
              % (g["key"], d["n"], d["left"], d["right"], g["name"], img))
    with open(os.path.join(HERE, "sensegroups.json"), "w") as f:
        f.write(json.dumps(rows))  # compact single-line, like the other card files
    print("wrote sensegroups.json")


def descs(g, d, img):
    sc = d["sim_counts"]
    L, R = d["left"], d["right"]
    if g["key"] == "photoreceptors":
        desc = (
            "In a real fly, the R1\u20136, R7 and R8 cells of each compound eye turn "
            "light into neural signals; %s are mapped here (%s left, %s right). "
            "Simulated version: the sim's light assays drive this group (%s neurons "
            "in Maxime, %s in Hagrid), and downstream vision reads their direct targets."
            % (num(d["n"]), num(L), num(R), num(sc["banc"]), num(sc["malecns"])))
    elif g["key"] == "taste":
        desc = (
            "In a real fly, gustatory neurons report sweet, water and bitter; %s are "
            "mapped here (%s left, %s right), covering sugar/water, taste-peg and "
            "bitter kinds without splitting them yet. Simulated version: the sim runs "
            "this group in both flies (%s in Maxime, %s in Hagrid); bitter stimuli "
            "and bitter contact (DEET) act here."
            % (num(d["n"]), num(L), num(R), num(sc["banc"]), num(sc["malecns"])))
    else:
        desc = (
            "In a real fly, the cells most strongly fed by the eyes \u2014 everything "
            "drawing over a quarter of its input current from photoreceptors; %s mapped "
            "here (%s left, %s right). Simulated version: exactly the sim's "
            "visual-targets group (%s in Maxime, %s in Hagrid); light assays move these."
            % (num(d["n"]), num(L), num(R), num(sc["banc"]), num(sc["malecns"])))
    desc += (" Male anatomy is unmapped and synapses uncounted, so those show \u2014.")
    return {"row": g["row"], "level": "sense", "hub": "senses", "name": g["name"],
            "fn": d["n"], "mn": None, "fe": None, "me": None,
            "fs": None, "ms": None, "ratio": None,
            "func": g["func"], "desc": desc, "img": img}


def num(n):
    return "%s" % f"{n:,}"


def render_jpg(somas, pal, pts, head, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(6, 3.45), dpi=100)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 0.80])
    ax.set_facecolor(BG)
    ax.scatter(somas[:, 0], -somas[:, 1], s=1, c=pal, alpha=0.28,
               linewidths=0, rasterized=False)
    n = len(pts)
    ax.scatter(pts[:, 0], -pts[:, 1], s=8 if n < 1000 else 2, c=LIT,
               alpha=0.85, linewidths=0)
    pad = 0.03
    ax.set_xlim(-1 - pad, 1 + pad)
    ax.set_ylim(-(0.48 + pad), 0.48 + pad)  # y renders flipped, like the live view
    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.text(0.5, 0.93, head, ha="center", va="center", fontsize=13,
             family="serif", color="#2b2620")
    fig.text(0.5, 0.865, SUBLINE, ha="center", va="center", fontsize=7.5,
             family="sans-serif", color="#6d685d")
    fig.savefig(path, facecolor=fig.get_facecolor(), dpi=100)
    plt.close(fig)


if __name__ == "__main__":
    main()
