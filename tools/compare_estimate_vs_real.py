"""Prediction vs reality: how closely did the lab's ESTIMATED neuron positions resemble each fly's REAL anatomy?

Before the measured positions arrived, the lab (cns_fly.py) placed each of Maxime's and Hagrid's neurons by
a rule: the synapse-weighted centre of the brain regions it is wired into (region centres measured on the FlyWire
reference fly), plus a random scatter; nerve-cord regions were laid out by hand ("schematic").
Now each fly's real cell-body positions are known (build_fly_brains.py), so the prediction can be graded.

Fair-comparison steps
 1. Same neurons only: matched by ID, kept only where both a prediction and a real cell body exist.
 2. Same ruler: both converted to micrometres.
 3. Same pose: the prediction lives in another fly's coordinate frame, so it is turned, moved and resized
    (one rigid rotation + one uniform scale + one shift, no bending) to line up best with the real BRAIN.
    This gives the prediction its best fair chance; the nerve cord is NOT used for the fit.
 4. Grades
    - shape resemblance: overlap between the 20-micrometre boxes holding real cell bodies and the boxes holding
      predicted dots (Dice score = 2 x shared boxes / (real boxes + predicted boxes), 0-100%), for brain, nerve
      cord and whole system; the nerve cord is carried along with the brain fit, not lined up on its own;
    - neuron placement: distance from each predicted dot to that neuron's real cell body
      (median, and % within 25 / 50 / 100 micrometres);
    - a 'no-knowledge' baseline: the same predicted cloud with neuron labels shuffled (across the whole brain /
      system for the headline grades, only within the region for each region row). The gap between the
      real score and the baseline is what the rule actually knew about individual neurons.
Note: the rule aimed at where a neuron is WIRED; the real data give where its CELL BODY sits (cell bodies sit
in the brain's outer rind). Part of every distance is that gap, and it is reported, not hidden.

Usage (from the skeleton folder): python3 tools/compare_estimate_vs_real.py <est_banc.csv.gz> <est_malecns.csv.gz>
"""
import json, os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_fly_counts import region

LIB = os.path.join(HERE, '..', 'library')
EST = {'maxime': sys.argv[1], 'hagrid': sys.argv[2]}
FLYWIRE_UM_PER_UNIT = 385.881   # lab's FlyWire-normalised frame -> micrometres (fit against FlyWire soma coordinates)
idx = json.load(open(os.path.join(LIB, 'points', 'flies_index.json')))
VOX = 20.0
TH = (25, 50, 100)


def umeyama(src, dst):
    """Best rotation R, scale c, shift t so that c*R@src + t ~ dst (no reflection)."""
    ms, md = src.mean(0), dst.mean(0)
    xs, xd = src - ms, dst - md
    U, S, Vt = np.linalg.svd(xd.T @ xs / len(src))
    D = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        D[2, 2] = -1
    R = U @ D @ Vt
    c = np.trace(np.diag(S) @ D) / xs.var(0).sum()
    return R, c, md - c * R @ ms


def dice(a, b):
    A = set(map(tuple, np.floor(a / VOX).astype(int)))
    B = set(map(tuple, np.floor(b / VOX).astype(int)))
    return round(100 * 2 * len(A & B) / max(1, len(A) + len(B)), 1)


def grades(e, r, rng):
    d = np.linalg.norm(e - r, axis=1)
    sh = np.linalg.norm(e[rng.permutation(len(e))] - r, axis=1)
    out = dict(neurons=int(len(d)), shape_resemblance_pct=dice(e, r), median_distance_um=round(float(np.median(d)), 1),
               baseline_median_um=round(float(np.median(sh)), 1))
    for t in TH:
        out[f'within_{t}um_pct'] = round(100 * float((d <= t).mean()), 1)
        out[f'baseline_within_{t}um_pct'] = round(100 * float((sh <= t).mean()), 1)
    return out


report = {}
for fly in ('maxime', 'hagrid'):
    ids = np.fromfile(os.path.join(LIB, 'points', f'{fly}_ids.bin'), dtype='<i8')
    real = np.fromfile(os.path.join(LIB, 'points', f'{fly}_somas.bin'), dtype='<f4').reshape(-1, 3).astype(float)
    real *= idx['flies'][fly]['microns_per_unit']
    cls = np.fromfile(os.path.join(LIB, 'points', f'{fly}_classes.bin'), dtype='u1')
    mainnp = pd.read_csv(os.path.join(LIB, 'points', f'{fly}_mainnp.csv.gz'))['np'].fillna('').astype(str)
    reg = np.array([region(s) if s else '' for s in mainnp])
    est = pd.read_csv(EST[fly]).set_index('root_id').reindex(ids)[['x', 'y', 'z']].to_numpy() * FLYWIRE_UM_PER_UNIT
    ok = ~np.isnan(est[:, 0])
    vnc_codes = {'ProNm', 'MesoNm', 'MetaNm', 'ANm', 'NTct', 'WTct', 'HTct', 'IntTct', 'LTct', 'AMNp', 'mVAC', 'Tct (unsplit)'}
    is_cord = real[:, 2] < -250.0   # real cell body lies in the nerve cord (behind the brain)
    fit = ok & ~is_cord
    R, c, t = umeyama(est[fit], real[fit])
    al = (c * (R @ est.T)).T + t
    rng = np.random.default_rng(0)
    rep = dict(matched=int(ok.sum()), drawn_real=int(len(ids)), fit_scale=round(float(c), 3),
               whole=grades(al[ok], real[ok], rng), brain=grades(al[fit], real[fit], rng),
               nerve_cord=grades(al[ok & is_cord], real[ok & is_cord], rng), regions={})
    for r_ in sorted(set(reg[ok])):
        mk = ok & (reg == r_)
        if r_ and mk.sum() >= 50:
            g = grades(al[mk], real[mk], rng)
            g['centre_offset_um'] = round(float(np.linalg.norm(al[mk].mean(0) - real[mk].mean(0))), 1)
            rep['regions'][r_] = g
    report[fly] = rep
    print(fly, 'whole', rep['whole']['shape_resemblance_pct'], '% shape;', 'brain', rep['brain'], '\n  cord', rep['nerve_cord'])
report['method'] = __doc__
json.dump(report, open(os.path.join(LIB, 'prediction_vs_real.json'), 'w'), indent=1)


# ---- overlay pictures: grey = real cell bodies, pink = the lab's earlier prediction (after fair alignment) ----
if '--images' in sys.argv:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    os.makedirs(os.path.join(LIB, 'img', 'prediction'), exist_ok=True)
    BG, INK, MUTED = '#fbf8f1', '#1b1a17', '#6d685d'
    for fly in ('maxime', 'hagrid'):
        ids = np.fromfile(os.path.join(LIB, 'points', f'{fly}_ids.bin'), dtype='<i8')
        real = np.fromfile(os.path.join(LIB, 'points', f'{fly}_somas.bin'), dtype='<f4').reshape(-1, 3).astype(float) * idx['flies'][fly]['microns_per_unit']
        est = pd.read_csv(EST[fly]).set_index('root_id').reindex(ids)[['x', 'y', 'z']].to_numpy() * FLYWIRE_UM_PER_UNIT
        cls = np.fromfile(os.path.join(LIB, 'points', f'{fly}_classes.bin'), dtype='u1')
        ok = ~np.isnan(est[:, 0]); fit = ok & (real[:, 2] >= -250.0)
        R, c, t = umeyama(est[fit], real[fit]); al = (c * (R @ est.T)).T + t
        s = np.random.default_rng(1).random(len(ids)) < 0.25
        fig, axs = plt.subplots(1, 2, figsize=(10, 4.2), dpi=110, facecolor=BG)
        for ax, (a, b, ttl) in zip(axs, [(0, 1, 'Seen from the front'), (2, 1, 'Seen from the side (head on the right)')]):
            ax.set_facecolor(BG); ax.axis('off')
            ax.scatter(real[s & ok, a], real[s & ok, b], s=0.2, c='#8a96a3', alpha=0.45, linewidths=0, label='real cell bodies')
            ax.scatter(al[s & ok, a], al[s & ok, b], s=0.2, c='#c2187a', alpha=0.35, linewidths=0, label='earlier prediction')
            ax.invert_yaxis(); ax.set_aspect('equal'); ax.set_title(ttl, color=INK, fontsize=10)
        fig.text(0.5, 0.02, f"{fly.capitalize()}: grey = real measured cell bodies; pink = where the lab had predicted them (lined up as fairly as possible).",
                 ha='center', color=MUTED, fontsize=8)
        fig.savefig(os.path.join(LIB, 'img', 'prediction', f'{fly}_overlay.png'), facecolor=BG)
        plt.close(fig)
    print('overlay images written')
