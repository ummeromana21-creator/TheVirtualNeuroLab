"""Nerve-cord card pictures for the Fly Atlas, drawn from each fly's OWN measured cell bodies.

Top view of the whole nervous system (head at the top). Grey dots = every neuron drawn for that fly;
pink = cell bodies of neurons whose synapses are mostly in this region (the same region names as the counts).
Writes library/img/regions/<CODE>_maxime.jpg and _hagrid.jpg, and adds img_maxime / img_hagrid to data.json rows.
Run from the skeleton folder after build_fly_brains.py and build_atlas.py:  python3 tools/render_vnc_cards.py
"""
import json, os, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_fly_counts import region  # same export-label -> region mapping as the counts

LIB = os.path.join(HERE, '..', 'library')
rows = json.load(open(os.path.join(LIB, 'data.json')))
VNC = [r for r in rows if r['hub'] == 'VNC']
BG, INK, MUTED, LIT, DOT = '#fbf8f1', '#1b1a17', '#6d685d', '#c2187a', '#9aa6b2'
NAME = {'maxime': 'Maxime (BANC scan)', 'hagrid': 'Hagrid (male CNS scan)'}

for fly in ('maxime', 'hagrid'):
    P = np.fromfile(os.path.join(LIB, 'points', f'{fly}_somas.bin'), dtype='<f4').reshape(-1, 3)
    reg = pd.read_csv(os.path.join(LIB, 'points', f'{fly}_mainnp.csv.gz'))['np'].fillna('').astype(str).map(
        lambda s: region(s) if s else '').to_numpy()
    rng = np.random.default_rng(0)
    bg = rng.random(len(P)) < 0.35
    for r in VNC:
        codes = r.get('members') or [r['name']]
        lit = np.isin(reg, codes)
        fig = plt.figure(figsize=(6, 3.45), dpi=100, facecolor=BG)
        title = f"{r['full']}  ·  {r['func']}" if r['level'] == 'family' else f"{r['name']}  ·  {r['full']}  ·  {r['func']}"
        fig.text(0.5, 0.94, title, ha='center', va='center', fontsize=11.5, color=INK)
        fig.text(0.5, 0.875, f"{NAME[fly]}: measured cell bodies, seen from above, head at left. "
                             f"Pink = {int(lit.sum()):,} neurons wired mainly here.", ha='center', va='center', fontsize=7, color=MUTED)
        ax = fig.add_axes([0.02, 0.02, 0.96, 0.80]); ax.set_facecolor(BG); ax.axis('off')
        # top view, rotated so the body runs left (head) to right (abdomen)
        ax.scatter(-P[bg, 2], P[bg, 0], s=0.25, c=DOT, alpha=0.45, linewidths=0)
        if lit.any():
            ax.scatter(-P[lit, 2], P[lit, 0], s=1.2, c=LIT, alpha=0.8, linewidths=0)
        ax.set_aspect('equal'); ax.set_xlim(-0.6, 2.4); ax.set_ylim(-1.1, 1.1)
        fn = f"{r['name']}_{fly}.jpg"
        fig.savefig(os.path.join(LIB, 'img', 'regions', fn), facecolor=BG, format='jpg', pil_kwargs={'quality': 86})
        plt.close(fig)
        r[f'img_{fly}'] = f'img/regions/{fn}'
json.dump(rows, open(os.path.join(LIB, 'data.json'), 'w'), indent=1, ensure_ascii=False)
print('cards:', len(VNC) * 2)
