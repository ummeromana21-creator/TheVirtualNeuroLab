"""Build the Fly Atlas region data (library/data.json) and card images (library/img/regions/).

Inputs:  tools/regions_ref.json   curated names, families (Ito 2014 / Court 2020) and functions
         library/flies.json       per-fly counts from tools/build_fly_counts.py
         library/points/*.bin     FlyWire reference-brain points (cell bodies + region synapse samples)
Run from the skeleton folder:  python3 tools/build_atlas.py [--no-images]
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
LIB = os.path.join(ROOT, 'library')
ref = json.load(open(os.path.join(HERE, 'regions_ref.json')))
flies = json.load(open(os.path.join(LIB, 'flies.json')))
FLIES = ('maxime', 'hagrid')

CLASS_COL = ['#5f86c4', '#b89a5c', '#5fae86', '#8d78c8', '#c97070', '#cf8fa8', '#6fb0c6', '#8a8a8a', '#9a9a9a']


MERGED = ref.get('merged', {})
NOTES = ref.get('notes', {})


def fly_counts(fly, code):
    if code in MERGED.get(fly, {}) and code not in flies[fly]['regions']:
        return {'merged_into': MERGED[fly][code]}
    r = flies[fly]['regions'].get(code)
    if code == 'unassigned':  # fold tiny unsplit tectulum labels into unassigned
        extra = flies[fly]['regions'].get('Tct (unsplit)')
        if r and extra:
            r = dict(r, synapses=r['synapses'] + extra['synapses'])
        elif extra and not r:
            r = extra
    if not r:
        return None
    out = {k: r[k] for k in ('synapses', 'neurons', 'left', 'right')}
    if NOTES.get(fly, {}).get(code):
        out['note'] = NOTES[fly][code]
    return out


def has_points(code):
    return os.path.exists(os.path.join(LIB, 'points', code + '.bin'))


rows, n = [], 0
for fam in ref['families']:
    members = fam['members']
    single = len(members) == 1
    if not single:
        n += 1
        tot = {f: sum((fly_counts(f, m) or {}).get('synapses', 0) or 0 for m in members) for f in FLIES}
        rows.append(dict(row=n, level='family', hub=fam['id'], name=fam['id'], full=fam['name'],
                         func=fam['func'], desc=fam['desc'], members=members,
                         maxime={'synapses': tot['maxime']} if tot['maxime'] else None,
                         hagrid={'synapses': tot['hagrid']} if tot['hagrid'] else None,
                         img=f'img/regions/{fam["id"]}.jpg', has3d=any(has_points(m) for m in members)))
    for code in members:
        n += 1
        r = ref['regions'][code]
        rows.append(dict(row=n, level='region', hub=fam['id'], name=code, full=r['full'],
                         func=r['func'], desc=r['desc'],
                         maxime=fly_counts('maxime', code), hagrid=fly_counts('hagrid', code),
                         img=f'img/regions/{code}.jpg', has3d=has_points(code)))

json.dump(rows, open(os.path.join(LIB, 'data.json'), 'w'), indent=1, ensure_ascii=False)
print(len(rows), 'rows;', sum(r['level'] == 'region' for r in rows), 'regions;',
      sum(r['level'] == 'family' for r in rows), 'family rows')

if '--no-images' in sys.argv:
    sys.exit()

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

P = np.fromfile(os.path.join(LIB, 'points', 'somas.bin'), dtype='<f4').reshape(-1, 3)
C = np.fromfile(os.path.join(LIB, 'points', 'classes.bin'), dtype='u1')
cols = np.array([CLASS_COL[c] if c < len(CLASS_COL) else '#cccccc' for c in C])
rng = np.random.default_rng(0)
keep = rng.random(len(P)) < 0.45
out = os.path.join(LIB, 'img', 'regions')
os.makedirs(out, exist_ok=True)
BG, INK, MUTED, LIT = '#fbf8f1', '#1b1a17', '#6d685d', '#c2187a'


def card(path, title, sub, regions):
    fig = plt.figure(figsize=(6, 3.45), dpi=100, facecolor=BG)
    fig.text(0.5, 0.94, title, ha='center', va='center', fontsize=11.5, color=INK)
    fig.text(0.5, 0.875, sub, ha='center', va='center', fontsize=7, color=MUTED)
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.80]); ax.set_facecolor(BG); ax.axis('off')
    pts = [np.fromfile(os.path.join(LIB, 'points', r + '.bin'), dtype='<f4').reshape(-1, 3)
           for r in regions if has_points(r)]
    if pts:
        ax.scatter(P[keep, 0], -P[keep, 1], s=0.35, c=cols[keep], alpha=0.55, linewidths=0)
        L = np.concatenate(pts)
        ax.scatter(L[:, 0], -L[:, 1], s=0.6, c=LIT, alpha=0.75, linewidths=0)
        ax.set_xlim(-1.02, 1.02); ax.set_ylim(-0.52, 0.52); ax.set_aspect('equal')
    else:
        ax.text(0.5, 0.5, 'No 3D picture yet', ha='center', va='center', fontsize=13,
                color=MUTED, family='serif', style='italic', transform=ax.transAxes)
    fig.savefig(path, facecolor=BG, format='jpg', pil_kwargs={'quality': 86})
    plt.close(fig)


SUB = 'Reference brain: FlyWire female (FAFB v783), front view. Dots = 139,255 cells; pink = this region.'
for r in rows:
    regs = r['members'] if r['level'] == 'family' else [r['name']]
    title = f"{r['full']}  ·  {r['func']}" if r['level'] == 'family' else f"{r['name']}  ·  {r['full']}  ·  {r['func']}"
    sub = SUB if any(has_points(x) for x in regs) else \
        ('Nerve cord: no reference picture yet — each fly’s own 3D data will fill this in.'
         if r['hub'] == 'VNC' else
         'Too small or not separately labelled in the FlyWire reference brain.' if r['name'] == 'AB' else
         'Not a brain region — nothing to draw.')
    card(os.path.join(out, r['name'] + '.jpg'), title, sub, regs)
print('images:', len(rows))
