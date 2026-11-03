"""How good is the lab's position estimate?  Test it on the one fly where we know the answer (FlyWire).

The lab estimates where each neuron's wiring sits from WHICH brain regions its synapses are in
(cns_fly.py: synapse-weighted average of region centres, plus a random scatter the size of the region).
Here we run that exact method on the FlyWire fly, then compare with the real measured synapse positions.

Truth   = each neuron's real "wiring centre": the average position of all its synapses (synapse_coordinates.csv.gz).
Estimate = the lab's method, using the same region centres (neuropil_anchors.json) and the same scatter (seed 0).
Outputs  = per-neuron error in micrometres, summarised per region and overall, plus region shape overlap.
Run on the Mac:  python3 tools/test_estimates_flywire.py <Databases/Flywire dir> <Fly Brain dir> <out.json>
"""
import json, os, sys, time
import numpy as np, pandas as pd
from scipy import sparse

FW, FB, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
t0 = time.time()
say = lambda *a: print(f'[{time.time()-t0:5.0f}s]', *a, flush=True)

# 1. neuron order + the lab's normalised frame -> nanometres (affine fit against measured soma positions)
z = np.load(os.path.join(FB, 'flywire', 'maxime_v783.npz'))
ids = z['root_id']; n = len(ids); xyz_norm = z['xyz']
idx = pd.Index(ids)
co = pd.read_csv(os.path.join(FW, 'coordinates.csv.gz'), usecols=['root_id', 'position']).drop_duplicates('root_id')
soma = np.full((n, 3), np.nan)
k = idx.get_indexer(co['root_id'])
ok = k >= 0
soma[k[ok]] = np.array([[float(v) for v in p.strip('[]').split()] for p in co['position'][ok]])
good = ~np.isnan(soma[:, 0]) & ~np.isnan(xyz_norm[:, 0])
scale, offset = [], []
for a in range(3):
    s, o = np.polyfit(xyz_norm[good, a], soma[good, a], 1)
    scale.append(s); offset.append(o)
scale, offset = np.array(scale), np.array(offset)
say('frame: nm per unit', scale.round(0), 'offset', offset.round(0))

anchors = json.load(open(os.path.join(FB, 'flywire', 'neuropil_anchors.json')))

# 2. the lab's estimate, exactly as cns_fly.py does it
con = pd.read_csv(os.path.join(FW, 'connections_princeton.csv.gz'), usecols=['pre_root_id', 'post_root_id', 'neuropil', 'syn_count'])
names = sorted(set(con['neuropil']))
col = pd.Index(names).get_indexer(con['neuropil'])
rows = np.concatenate([idx.get_indexer(con['pre_root_id']), idx.get_indexer(con['post_root_id'])])
cols = np.concatenate([col, col]); vals = np.concatenate([con['syn_count'].to_numpy()] * 2).astype(np.float64)
m = rows >= 0
NPW = sparse.csr_matrix((vals[m], (rows[m], cols[m])), shape=(n, len(names)))
del con
A = np.zeros((len(names), 3)); SD = np.zeros((len(names), 3)); known = np.zeros(len(names), bool)
for i, nm in enumerate(names):
    if nm in anchors:
        A[i] = anchors[nm]['centre']; SD[i] = anchors[nm]['spread']; known[i] = True
tot = np.asarray(NPW.sum(1)).ravel()
has = tot > 0
est_c = np.full((n, 3), np.nan); est_c[has] = (NPW @ A)[has] / tot[has, None]
rng = np.random.default_rng(0)
est = est_c.copy()
est[has] += rng.normal(0, 1, (int(has.sum()), 3)) * ((NPW @ SD)[has] / tot[has, None]) * 0.8
to_nm = lambda p: p * scale + offset
est_nm, estc_nm = to_nm(est), to_nm(est_c)
main = np.asarray(NPW.argmax(1)).ravel()
main_name = np.array([names[j] if has[i] else '' for i, j in enumerate(main)])
say('estimates for', int(has.sum()), 'of', n, 'neurons')

# 3. truth: real wiring centre = mean of all the neuron's synapse positions
S = np.zeros((n, 3)); C = np.zeros(n)
last = {'pre_root_id': pd.NA, 'post_root_id': pd.NA}
for ch in pd.read_csv(os.path.join(FW, 'synapse_coordinates.csv.gz'), chunksize=4_000_000,
                      dtype={'pre_root_id': 'Int64', 'post_root_id': 'Int64'}):
    for c in ('pre_root_id', 'post_root_id'):   # blank = same neuron as the row above (carry across chunks)
        if pd.isna(ch[c].iloc[0]):
            ch.iloc[0, ch.columns.get_loc(c)] = last[c]
        ch[c] = ch[c].ffill()
        last[c] = ch[c].iloc[-1]
    ch = ch.dropna(subset=['pre_root_id', 'post_root_id'])
    p = ch[['x', 'y', 'z']].to_numpy(np.float64)
    for c in ('pre_root_id', 'post_root_id'):
        j = idx.get_indexer(ch[c].to_numpy(np.int64))
        g = j >= 0
        for a in range(3):
            S[:, a] += np.bincount(j[g], weights=p[g, a], minlength=n)
        C += np.bincount(j[g], minlength=n)
    say('synapse chunk', len(ch))
real = np.where(C[:, None] > 0, S / np.maximum(C, 1)[:, None], np.nan)

# 4. compare (against the real wiring centre, and - since the region centres were measured from
#    FlyWire cell-body positions - also against each neuron's real cell body)
soma_err = np.linalg.norm(est_nm - soma, axis=1) / 1000.0
somac_err = np.linalg.norm(estc_nm - soma, axis=1) / 1000.0
evs = has & ~np.isnan(soma[:, 0])
say('vs cell body: median', round(float(np.nanmedian(soma_err[evs])), 1), 'um; no scatter', round(float(np.nanmedian(somac_err[evs])), 1),
    '; within 20um', round(100 * float((soma_err[evs] <= 20).mean()), 1), '%; within 50um', round(100 * float((soma_err[evs] <= 50).mean()), 1), '%')
ev = has & (C > 0)
err = np.linalg.norm(est_nm - real, axis=1) / 1000.0       # micrometres
errc = np.linalg.norm(estc_nm - real, axis=1) / 1000.0     # without the random scatter
base = np.array([s.rsplit('_', 1)[0] if s.endswith(('_L', '_R')) else s for s in main_name])
TH = (10, 20, 30)


def summary(mask):
    e, ec = err[mask], errc[mask]
    return dict(neurons=int(mask.sum()), median_um=round(float(np.median(e)), 1),
                **{f'within_{t}um': round(100 * float((e <= t).mean()), 1) for t in TH},
                median_um_no_scatter=round(float(np.median(ec)), 1))


def dice(mask, voxel_um=10.0):
    a = np.floor(est_nm[mask] / (voxel_um * 1000)).astype(np.int64)
    b = np.floor(real[mask] / (voxel_um * 1000)).astype(np.int64)
    A_, B_ = set(map(tuple, a)), set(map(tuple, b))
    return round(100 * 2 * len(A_ & B_) / max(1, len(A_) + len(B_)), 1)


out = dict(method='cns_fly.py position estimate tested on FlyWire FAFB v783', truth='mean synapse position per neuron',
           thresholds_um=TH, overall=summary(ev), overall_shape_overlap=dice(ev), regions={},
           unplaced=int((~has).sum()), brain_neurons=n)
for r in sorted(set(base[ev])):
    mk = ev & (base == r)
    if mk.sum() >= 30 and r:
        out['regions'][r] = dict(summary(mk), shape_overlap=dice(mk))
# 5. alternative method B: place each neuron at a random REAL synapse location inside its main region
#    (same side), using the FlyWire region samples in library/points/<REGION>.bin (normalised frame).
PTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'library', 'points')
rngb = np.random.default_rng(1)
estb = np.full((n, 3), np.nan)
for r in sorted(set(base[has])):
    f = os.path.join(PTS, r + '.bin')
    if not r or not os.path.exists(f):
        continue
    pts = to_nm(np.fromfile(f, dtype='<f4').reshape(-1, 3).astype(np.float64))
    mid = offset[0]
    for sname in set(main_name[has & (base == r)]):
        mk = np.where(has & (main_name == sname))[0]
        side = sname.endswith('_L'), sname.endswith('_R')
        cx = to_nm(A[names.index(sname)])[0] if sname in names else mid
        pool = pts if not any(side) else pts[(pts[:, 0] < mid) == (cx < mid)]
        if len(pool) == 0:
            pool = pts
        estb[mk] = pool[rngb.integers(0, len(pool), len(mk))]
okb = ev & ~np.isnan(estb[:, 0])
eb = np.linalg.norm(estb - real, axis=1) / 1000.0


def dice_b(mask, voxel_um=10.0):
    a = np.floor(estb[mask] / (voxel_um * 1000)).astype(np.int64)
    b = np.floor(real[mask] / (voxel_um * 1000)).astype(np.int64)
    A_, B_ = set(map(tuple, a)), set(map(tuple, b))
    return round(100 * 2 * len(A_ & B_) / max(1, len(A_) + len(B_)), 1)


out['method_B'] = dict(neurons=int(okb.sum()), median_um=round(float(np.median(eb[okb])), 1),
                       **{f'within_{t}um': round(100 * float((eb[okb] <= t).mean()), 1) for t in TH},
                       shape_overlap=dice_b(okb), regions={})
for r in out['regions']:
    mk = okb & (base == r)
    if mk.sum() >= 30:
        out['method_B']['regions'][r] = dict(median_um=round(float(np.median(eb[mk])), 1),
                                              within_20um=round(100 * float((eb[mk] <= 20).mean()), 1), shape_overlap=dice_b(mk))
# 6. region-level check: is the drawn dot in the right region?  Nearest region centre (in nm) to the
#    estimate vs. nearest region centre to the neuron's REAL wiring centre.
known_idx = np.where(known)[0]
Anm = to_nm(A[known_idx])
def nearest(P):
    d = ((P[:, None, :] - Anm[None, :, :]) ** 2).sum(-1)
    return known_idx[np.argmin(d, 1)]
okr = ev & np.isin(main, known_idx)
ri = np.where(okr)[0]
hit_est, hit_c = np.zeros(n, bool), np.zeros(n, bool)
for s_ in range(0, len(ri), 20000):
    b_ = ri[s_:s_ + 20000]
    truth_r = nearest(real[b_])
    hit_est[b_] = nearest(est_nm[b_]) == truth_r
    hit_c[b_] = nearest(estc_nm[b_]) == truth_r
out['region_level'] = dict(neurons=int(okr.sum()), same_region_pct=round(100 * float(hit_est[okr].mean()), 1),
                           same_region_pct_no_scatter=round(100 * float(hit_c[okr].mean()), 1), regions={})
for r in out['regions']:
    mk = okr & (base == r)
    if mk.sum() >= 30:
        out['region_level']['regions'][r] = round(100 * float(hit_est[mk].mean()), 1)
say('region level', {k: v for k, v in out['region_level'].items() if k != 'regions'})
say('method B', {k: v for k, v in out['method_B'].items() if k != 'regions'})
json.dump(out, open(OUT, 'w'), indent=1)
say('overall', out['overall'], 'shape overlap', out['overall_shape_overlap'])
