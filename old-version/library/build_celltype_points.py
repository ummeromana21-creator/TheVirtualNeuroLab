"""Build per-cell-type 3D points + fallback renders from the held FlyWire tables.

Reads (in place, never copied): ~/Desktop/Databases/Flywire /
  consolidated_cell_types.csv.gz  root_id -> primary_type (card names)
  neurons.csv.gz                  the 139,255-row normalization set (== somas.bin)
  coordinates.csv.gz              root_id -> FAFB voxel [x y z]
Writes:
  points/<type>.bin               float32 xyz, somas.bin convention
                                  (bbox-mid center, x-span mapped to [-1, 1])
  img/celltypes/<type>.jpg        600x345 3D-scatter fallback render
  celltypes.json                  e['img'] points at the render when built,
                                  else keeps img/celltype.svg (+ caption stays)
Run:  python3 build_celltype_points.py [--pilot N]
"""
import csv
import gzip
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.expanduser('~/Desktop/Databases/Flywire ')
MIN_PTS = 3
CAP = 6000  # biggest types render + store at most this many points


def open_gz(name):
    return gzip.open(os.path.join(DB, name), 'rt', newline='')


def load_points(want):
    """{type: (N,3) float32 normalized} for wanted card names."""
    keep_roots = {}
    with open_gz('consolidated_cell_types.csv.gz') as f:
        for r in csv.DictReader(f):
            if r['primary_type'] in want:
                keep_roots[r['root_id']] = r['primary_type']
    norm_roots = []
    with open_gz('neurons.csv.gz') as f:
        for r in csv.DictReader(f):
            norm_roots.append(r['root_id'])
    needed = set(norm_roots) | set(keep_roots)
    coords = {}
    with open_gz('coordinates.csv.gz') as f:
        for r in csv.DictReader(f):
            i = r['root_id']
            if i in needed:
                coords[i] = [float(x) for x in r['position'].strip('[]').split()]
    P = np.array([coords[i] for i in norm_roots if i in coords], dtype=np.float64)
    mid = (P.min(0) + P.max(0)) / 2
    s = (P.max(0) - P.min(0))[0] / 2
    by_type = {}
    for i, t in keep_roots.items():
        if i in coords:
            by_type.setdefault(t, []).append(coords[i])
    out = {}
    for t, pts in by_type.items():
        q = ((np.array(pts, dtype=np.float64) - mid) / s).astype(np.float32)
        if len(q) > CAP:
            q = q[np.linspace(0, len(q) - 1, CAP).astype(int)]
        out[t] = q
    return out


def render_jpg(pts, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(6, 3.45), dpi=100)
    ax = fig.add_subplot(111, projection='3d')
    fig.patch.set_facecolor('#0e1116')
    ax.set_facecolor('#0e1116')
    n = len(pts)
    ax.scatter(pts[:, 0], -pts[:, 1], pts[:, 2], s=30 if n < 300 else 8,
               c='#2ee6c8', alpha=0.75, linewidths=0, depthshade=True)
    ax.view_init(elev=12, azim=-60)
    lo = pts.min(0); hi = pts.max(0); pad = np.maximum((hi - lo) * 0.15, 1e-6)
    ax.set_xlim(lo[0] - pad[0], hi[0] + pad[0])
    ax.set_ylim(-(hi[1] + pad[1]), -(lo[1] - pad[1]))   # y renders flipped, like the live view
    ax.set_zlim(lo[2] - pad[2], hi[2] + pad[2])
    ax.set_axis_off()
    fig.tight_layout(pad=0.4)
    fig.savefig(path, facecolor=fig.get_facecolor(), dpi=100)
    plt.close(fig)


def main(argv):
    pilot = int(argv[argv.index('--pilot') + 1]) if '--pilot' in argv else None
    with open(os.path.join(HERE, 'celltypes.json')) as f:
        entries = json.load(f)
    names = [e['name'] for e in entries]
    if pilot:
        names = names[:pilot]
    pts = load_points(set(names))
    os.makedirs(os.path.join(HERE, 'img', 'celltypes'), exist_ok=True)
    made, skipped = 0, []
    for e in entries:
        if e['name'] not in names:
            continue
        q = pts.get(e['name'])
        if q is None or len(q) < MIN_PTS:
            skipped.append(e['name'])
            continue
        q.tofile(os.path.join(HERE, 'points', e['name'] + '.bin'))
        render_jpg(q, os.path.join(HERE, 'img', 'celltypes', e['name'] + '.jpg'))
        e['img'] = 'img/celltypes/%s.jpg' % e['name']
        made += 1
    if not pilot:
        with open(os.path.join(HERE, 'celltypes.json'), 'w') as f:
            json.dump(entries, f)   # compact, like build_celltypes.py
    print(f'types: {made} rendered, {len(skipped)} without positions'
          + (f' (pilot of {pilot}, json untouched)' if pilot else ''))
    if skipped:
        print('skipped:', ', '.join(skipped[:10]))


if __name__ == '__main__':
    main(sys.argv)
