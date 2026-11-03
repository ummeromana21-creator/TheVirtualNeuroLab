"""Taste Bench: record every sugar x bitter x water combination on the calibrated FlyWire v783 brain (10 repeats each).
These are demo replays, not scored experiments. Output: bench_runs.json"""
import json, sys, time, zlib, itertools
import numpy as np, pandas as pd
sys.path.insert(0, '.')
from lif_engine import Network
L = json.load(open('shiu_lists.json'))
comp = pd.read_csv('shiu/Completeness_783.csv', index_col=0)
c = pd.read_parquet('shiu/Connectivity_783.parquet', columns=['Presynaptic_Index', 'Postsynaptic_Index', 'Excitatory x Connectivity'])
net = Network(comp.index.values, c['Presynaptic_Index'].values, c['Postsynaptic_Index'].values, c['Excitatory x Connectivity'].values, np.ones(len(comp)))
del c
S = {k: net.idx(L['neu_' + k]) for k in ('sugar', 'bitter', 'water')}
MN9 = net.idx([720575940660219265, 720575940618238523])
out_all = {}
t0 = time.time()
for s, b, w in itertools.product((0, 50, 100, 200), (0, 100, 200), (0, 200)):
    name = f's{s}_b{b}_w{w}'
    if s == b == w == 0:
        out_all[name] = dict(mn9=0.0, rates={}); continue
    groups = [(S['sugar'], s), (S['bitter'], b), (S['water'], w)]
    out = net.run([g for g in groups if g[1] > 0], seed=zlib.crc32(name.encode()), p=dict(n_run=10), record=MN9)
    rates = {str(int(net.ids[k])): round(float(v.mean()), 1) for k, v in out.items() if v.mean() > 0}
    out_all[name] = dict(mn9=round(max(float(out[int(i)].mean()) for i in MN9), 1), rates=rates)
    print(name, out_all[name]['mn9'], len(rates), f'[{time.time()-t0:.0f}s]', flush=True)
    json.dump(out_all, open('bench_runs.json', 'w'))
print('done')
