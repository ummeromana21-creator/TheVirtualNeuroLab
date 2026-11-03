"""Parkinson's mechanisms 1 (structural part): where the dopamine signal is lost when dopamine neurons die.
Usage: python3 tools/build_pd.py "<Databases/Flywire dir>"     (writes disease/pd.json)
Rules: disease/pd_preregistration.json (written before this was run)."""
import sys, os, json
import numpy as np, pandas as pd
FW = sys.argv[1]; SK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
cls = pd.read_csv(os.path.join(FW, 'classification.csv.gz'))
typ = pd.read_csv(os.path.join(FW, 'consolidated_cell_types.csv.gz'))
info = cls.merge(typ, on='root_id', how='left').set_index('root_id')
dan = info[info['class'] == 'DAN'].copy()
dan['cluster'] = dan.primary_type.fillna('').str.extract(r'^(PAM|PPL1|PPL2)')[0]
D = set(dan.index.astype(int))
con = pd.read_csv(os.path.join(FW, 'connections_princeton.csv.gz'), usecols=['pre_root_id', 'post_root_id', 'neuropil', 'syn_count'])
e = con[con.pre_root_id.isin(D)].copy()
e = e[~e.post_root_id.isin(D)]                     # dopamine-to-dopamine links are counted separately
dd = con[con.pre_root_id.isin(D) & con.post_root_id.isin(D)]
roots = np.fromfile(os.path.join(SK, 'anatomy/celltypes/rootids.bin'), '<u8'); ix = {int(r): i for i, r in enumerate(roots)}
# per target totals
tgt = e.groupby('post_root_id').agg(syn=('syn_count', 'sum'), n_dan=('pre_root_id', 'nunique'))
reg = e.groupby('post_root_id').apply(lambda g: g.groupby('neuropil').syn_count.sum().idxmax(), include_groups=False)
tgt['region'] = reg; tgt['class'] = info['class'].reindex(tgt.index).fillna('unlabelled').values
tgt['type'] = info.primary_type.reindex(tgt.index).fillna('').values
tgt = tgt[[int(r) in ix for r in tgt.index]]
# edges dopamine -> target (summed over regions)
E = e.groupby(['pre_root_id', 'post_root_id']).syn_count.sum().reset_index()
dlist = sorted(D, key=lambda r: (str(dan.loc[r, 'cluster']), str(dan.loc[r, 'primary_type']), r))
dpos = {r: k for k, r in enumerate(dlist)}; tlist = list(tgt.index); tpos = {r: k for k, r in enumerate(tlist)}
E = E[E.post_root_id.isin(tpos)]
# ---- scenarios (fixed seeds) ----
rng = np.random.default_rng(2026)
syn_tot = tgt.syn.values.astype(float)
M = np.zeros((len(dlist), len(tlist)))
for a, b, s in E[['pre_root_id', 'post_root_id', 'syn_count']].itertuples(index=False): M[dpos[a], tpos[b]] += s
def curve(order_list, steps):
    out = []
    for frac in steps:
        vals = []
        for order in order_list:
            k = int(round(frac * len(order))); lost = np.zeros(len(dlist), bool); lost[order[:k]] = True
            remain = 1 - M[lost].sum(0) / syn_tot
            vals.append(remain)
        V = np.array(vals); out.append(V)
    return out
steps = [i / 10 for i in range(11)]
allidx = np.arange(len(dlist)); pam = np.array([dpos[r] for r in dlist if dan.loc[r, 'cluster'] == 'PAM']); ppl1 = np.array([dpos[r] for r in dlist if dan.loc[r, 'cluster'] == 'PPL1'])
orders_all = [rng.permutation(allidx) for _ in range(10)]
orders_pam = [rng.permutation(pam) for _ in range(10)]
orders_ppl1 = [np.concatenate([rng.permutation(ppl1), rng.permutation(np.setdiff1d(allidx, ppl1))]) for _ in range(10)]
classes = [c for c, n in tgt['class'].value_counts().items() if n >= 15][:10]
def summarise(order_list, sel=None):
    res = []
    for frac, V in zip(steps, curve(order_list, steps)):
        half = (V <= 0.5).sum(1)
        row = dict(lost=frac, half_lost=[int(half.mean()), int(half.min()), int(half.max())], mean_remaining=round(float(V.mean()), 3),
                   by_class={c: round(float(V[:, (tgt['class'] == c).values].mean()), 3) for c in classes})
        res.append(row)
    return res
out = dict(prereg=json.load(open(os.path.join(SK, 'disease/pd_preregistration.json'))),
  dan=[dict(id=str(r), idx=ix.get(int(r)), cluster=dan.loc[r, 'cluster'], type=str(dan.loc[r, 'primary_type'])) for r in dlist],
  targets=[dict(id=str(r), idx=ix[int(r)], cls=tgt.loc[r, 'class'], type=tgt.loc[r, 'type'], region=tgt.loc[r, 'region'], syn=int(tgt.loc[r, 'syn']), n_dan=int(tgt.loc[r, 'n_dan'])) for r in tlist],
  edges=[[dpos[a], tpos[b], int(s)] for a, b, s in E[['pre_root_id', 'post_root_id', 'syn_count']].itertuples(index=False)],
  orders=dict(all=orders_all[0].tolist(), pam=orders_pam[0].tolist(), ppl1=orders_ppl1[0].tolist()),
  scenarios=dict(all=summarise(orders_all), pam=summarise(orders_pam), ppl1=summarise(orders_ppl1)),
  classes=classes,
  by_class=tgt.groupby('class').agg(n=('syn', 'size'), syn=('syn', 'sum')).sort_values('syn', ascending=False).head(12).reset_index().to_dict('records'),
  by_region=tgt.groupby('region').agg(n=('syn', 'size'), syn=('syn', 'sum')).sort_values('syn', ascending=False).head(12).reset_index().to_dict('records'),
  spof=dict(n=int((tgt.n_dan <= 2).sum()), total=len(tgt), by_class=tgt[tgt.n_dan <= 2]['class'].value_counts().head(8).to_dict(),
            examples=tgt[(tgt.n_dan <= 2)].sort_values('syn', ascending=False).head(10).reset_index().rename(columns={'post_root_id': 'id'}).astype({'id': str}).to_dict('records')),
  counts=dict(dan=len(dlist), pam=int(len(pam)), ppl1=int(len(ppl1)), ppl2=int((dan.cluster == 'PPL2').sum()), targets=len(tlist), edges=len(E), dd_edges=int(len(dd)), syn=int(syn_tot.sum())),
  per_cluster={c: dict(targets=int((M[[dpos[r] for r in dlist if dan.loc[r, 'cluster'] == c]].sum(0) > 0).sum()),
                       top_classes=pd.Series(M[[dpos[r] for r in dlist if dan.loc[r, 'cluster'] == c]].sum(0), index=tgt['class'].values).groupby(level=0).sum().sort_values(ascending=False).head(5).astype(int).to_dict(),
                       top_regions=pd.Series(M[[dpos[r] for r in dlist if dan.loc[r, 'cluster'] == c]].sum(0), index=tgt['region'].values).groupby(level=0).sum().sort_values(ascending=False).head(5).astype(int).to_dict())
               for c in ('PAM', 'PPL1', 'PPL2')})
json.dump(out, open(os.path.join(SK, 'disease/pd.json'), 'w'), separators=(',', ':'), default=lambda o: o.item() if hasattr(o, 'item') else str(o))
print(json.dumps(dict(counts=out['counts'], spof={k: out['spof'][k] for k in ('n', 'total', 'by_class')}, by_class=out['by_class'][:8], by_region=out['by_region'][:8], per_cluster=out['per_cluster']), default=str, indent=0)[:3500])
for sc in ('ppl1', 'pam', 'all'):
    print(sc, [(r['lost'], r['half_lost'][0], r['mean_remaining']) for r in out['scenarios'][sc]])
