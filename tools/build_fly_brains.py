"""Each fly's OWN measured 3D nervous system (brain + nerve cord) for the Vivarium and Fly Atlas.

Inputs (measured cell-body positions, published by each scan's team):
  Maxime  BANC   banc_888_meta.feather  (Lee lab compiled release v888; `position` = soma anchor, voxels 4x4x45 nm)
  Hagrid  male CNS body-annotations-male-cns-v1.0-minconf-0.5.feather (Janelia FlyEM; `somaLocation`, 8 nm voxels)
Matched to the lab's own exports by ID (BANC root_888 = Codex Root ID; male CNS bodyId = Codex Root ID).
Only neurons in the lab's exports are kept; glia, trachea and non-neurons are left out.
Neurons without a recorded cell body (mostly sensory neurons, whose bodies sit outside the CNS) are not drawn.

Frame: each scan is turned into a fly-centred frame
  +x = fly's left, +y = DOWN (the page flips it), +z = towards the head
  (note: the older FlyWire region clouds and the lab's earlier estimates use a different frame, +x = fly's right
  and front = -z; compare_estimate_vs_real.py lines them up with a fitted rotation),
  scaled so the brain's width matches the FlyWire reference (about 2 units across).
Axes are found from the data itself: left/right from soma sides, up/down from the gnathal ganglia (bottom of the
brain) to the superior protocerebrum (top), and front/back from where the nerve cord lies (behind the brain).

Usage: python3 tools/build_fly_brains.py <banc.feather> <mcns.feather> <ids_BANC.csv> <ids_Male_CNS.csv>
                                         <main_np_banc.csv.gz> <main_np_malecns.csv.gz> <out library dir>
"""
import json, os, sys
import numpy as np, pandas as pd

banc_f, mcns_f, ids_b, ids_m, np_b, np_m, OUT = sys.argv[1:8]
CLASSES = ['optic', 'central', 'sensory', 'visual_projection', 'descending', 'ascending',
           'visual_centrifugal', 'motor', 'endocrine', 'nerve_cord']
NOT_NEURON = {'glia', 'trachea', 'not_a_neuron'}


def cls_banc(s):
    s = str(s)
    return {'optic_lobe_intrinsic': 'optic', 'central_brain_intrinsic': 'central', 'ventral_nerve_cord_intrinsic': 'nerve_cord',
            'visual_projection': 'visual_projection', 'visual_centrifugal': 'visual_centrifugal', 'descending': 'descending',
            'ascending': 'ascending', 'motor': 'motor'}.get(s, 'sensory' if 'sensory' in s else
                                                          'endocrine' if 'visceral' in s else 'central')


def cls_mcns(s):
    s = str(s)
    if s.startswith('ol_') and 'sensory' not in s: return 'optic'
    if 'sensory' in s: return 'sensory'
    if s.startswith('vnc_') and ('intrinsic' in s or 'tbc' in s): return 'nerve_cord'
    for k, v in (('visual_projection', 'visual_projection'), ('visual_centrifugal', 'visual_centrifugal'), ('descending', 'descending'),
                 ('ascending', 'ascending'), ('motor', 'motor'), ('efferent', 'motor'), ('endocrine', 'endocrine')):
        if k in s: return v
    return 'central'


def load(fly):
    if fly == 'maxime':
        b = pd.read_feather(banc_f)
        b = b[b['root_888'].notna()].copy()
        ids = pd.read_csv(ids_b)
        b['rid'] = b['root_888'].astype('int64')
        b = b[b['rid'].isin(set(ids['Root ID']))]
        b = b[~b['super_class'].isin(NOT_NEURON)]
        p = np.array([[float(v) for v in str(s).split(',')] for s in b['position']]) * np.array([4, 4, 45]) / 1000.0
        side = b['side'].map({'left': 'L', 'right': 'R'}).fillna('M').to_numpy()
        region = b['region'].astype(str).to_numpy()
        cls = np.array([cls_banc(s) for s in b['super_class']])
        # cells without a recorded nucleus in the CNS (almost all sensory neurons) have their anchor out in a
        # nerve, not a cell body: leave those out, as for Hagrid (no somaLocation)
        has = (b['nucleus_id'].notna() | ~b['super_class'].astype(str).str.contains('sensory')).to_numpy()
        return b['rid'].to_numpy(), p, side, cls, region, has, len(ids)
    m = pd.read_feather(mcns_f)
    ids = pd.read_csv(ids_m)
    m = m[m['bodyId'].isin(set(ids['Root ID']))].copy()
    loc = m['somaLocation'].where(m['somaLocation'].notna(), m['tosomaLocation'])
    has = loc.notna().to_numpy()
    p = np.full((len(m), 3), np.nan)
    p[has] = np.array([list(v) for v in loc[has]], dtype=float) * 8 / 1000.0
    side = m['somaSide'].fillna('M').astype(str).to_numpy()
    sc = m['superclass'].astype(str)
    cls = np.array([cls_mcns(s) for s in sc])
    region = np.where(sc.str.startswith('vnc_') | sc.str.contains('ascending'), 'ventral_nerve_cord',
                      np.where(sc.str.startswith('ol_') | (sc == 'visual_projection'), 'optic_lobe', 'central_brain'))
    return m['bodyId'].to_numpy(), p, side, cls, region, has, len(ids)


summary = {}
for fly, npf in (('maxime', np_b), ('hagrid', np_m)):
    rid, p, side, cls, region, has, n_export = load(fly)
    mainnp = pd.read_csv(npf).set_index('root_id')['neuropil'].reindex(rid).fillna('').astype(str).str.replace(r'_(L|R)$', '', regex=True).to_numpy()
    ok = has & ~np.isnan(p[:, 0])
    brain = ok & (region != 'ventral_nerve_cord')
    vnc = ok & (region == 'ventral_nerve_cord') & (cls != 'descending')
    # axes from the data
    L = p[brain & (side == 'L')].mean(0) - p[brain & (side == 'R')].mean(0); L /= np.linalg.norm(L)
    top = p[ok & np.isin(mainnp, ['SMP', 'SLP', 'SIP'])].mean(0); bottom = p[ok & (mainnp == 'GNG')].mean(0)
    U = top - bottom; U -= U.dot(L) * L; U /= np.linalg.norm(U)
    F = np.cross(L, U)
    centre = np.median(p[brain], 0)
    if (p[vnc].mean(0) - centre).dot(F) > 0:      # the nerve cord lies BEHIND the brain
        F = -F
    R = np.stack([L, -U, F])                       # rows: +x left, +y down, +z front
    q = (p - centre) @ R.T
    span = np.nanpercentile(np.abs(q[brain, 0]), 99)
    q = q / span
    stray = ok & (np.linalg.norm(q, axis=1) > 4)   # a handful of anchors far outside the nervous system
    ok = ok & ~stray
    keep = np.where(ok)[0]
    xyz = q[keep].astype('<f4')
    xyz.tofile(os.path.join(OUT, 'points', f'{fly}_somas.bin'))
    np.asarray(rid[keep], dtype='<i8').tofile(os.path.join(OUT, 'points', f'{fly}_ids.bin'))
    np.array([CLASSES.index(c) for c in cls[keep]], dtype='u1').tofile(os.path.join(OUT, 'points', f'{fly}_classes.bin'))
    pd.DataFrame({'np': mainnp[keep]}).to_csv(os.path.join(OUT, 'points', f'{fly}_mainnp.csv.gz'), index=False)
    summary[fly] = dict(neurons_in_export=int(n_export), neurons_drawn=int(len(keep)),
                        brain=int(brain.sum()), nerve_cord=int(vnc.sum()),
                        no_cell_body=int(n_export - len(keep) - stray.sum()), stray_points_dropped=int(stray.sum()),
                        microns_per_unit=round(float(span), 1),
                        brain_width_um=round(float(2 * span), 1),
                        nerve_cord_length_um=round(float(np.ptp(q[vnc, 2]) * span), 1))
    print(fly, summary[fly])
json.dump(dict(classes=CLASSES, flies=summary,
               sources={'maxime': 'BANC v888 meta (position, 4x4x45 nm voxels), matched by root_888',
                        'hagrid': 'male CNS v1.0 body annotations (somaLocation, 8 nm voxels), matched by bodyId'}),
          open(os.path.join(OUT, 'points', 'flies_index.json'), 'w'), indent=1)
