"""Re-run the 30-repeat confirmation runs (same seeds, so same averages) keeping every trial, to measure uncertainty."""
import json, sys, time, zlib
import numpy as np, pandas as pd
sys.path.insert(0, '.')
from lif_engine import Network
L = json.load(open('shiu_lists.json')); C = json.load(open('confirm_0.json'))
comp = pd.read_csv('shiu/Completeness_783.csv', index_col=0)
c = pd.read_parquet('shiu/Connectivity_783.parquet', columns=['Presynaptic_Index', 'Postsynaptic_Index', 'Excitatory x Connectivity'])
net = Network(comp.index.values, c['Presynaptic_Index'].values, c['Postsynaptic_Index'].values, c['Excitatory x Connectivity'].values, np.ones(len(comp))); del c
S = {'sugar': (net.idx(L['neu_sugar']), 100), 'water': (net.idx(L['neu_water']), 200)}
MN9 = net.idx([720575940660219265, 720575940618238523])
def trials(r): return {str(int(i)): [int(x) for x in r[int(i)]] for i in MN9}
out = dict(baseline={}, knockouts={}); t0 = time.time()
for cond, (g, hz) in S.items():
    out['baseline'][cond] = trials(net.run([(g, hz)], seed=zlib.crc32(cond.encode()), p=dict(n_run=30), record=MN9)); print(cond, f'{time.time()-t0:.0f}s', flush=True)
for k in sorted(C['knockouts']):
    cid, cond = k.split('|'); g, hz = S[cond]
    out['knockouts'][k] = trials(net.run([(g, hz)], silence=net.idx([int(cid)]), seed=zlib.crc32(cond.encode()), p=dict(n_run=30), record=MN9))
    print(k, f'{time.time()-t0:.0f}s', flush=True); json.dump(out, open('ci_trials.json', 'w'))
json.dump(out, open('ci_trials.json', 'w')); print('done', flush=True)
