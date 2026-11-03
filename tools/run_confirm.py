"""Re-run every neuron the screen scored 'needed' (MN9 more than 20% lower) with 30 repeats, as the saved rules say.
Usage: python3 run_confirm.py <part> <of>"""
import json, sys, time, zlib, os
import numpy as np, pandas as pd
sys.path.insert(0, '.')
from lif_engine import Network
part, of = int(sys.argv[1]), int(sys.argv[2])
L = json.load(open('shiu_lists.json'))
scr = [json.load(open(f'screen_{p}.json')) for p in (0, 1)]
base10 = scr[0]['baseline']
todo = []
for s in scr:
    for cid, v in s['knockouts'].items():
        for cond in ('sugar', 'water'):
            if v[cond] < 0.8 * base10[cond]: todo.append((cid, cond))
todo = sorted(todo)[part::of]
comp = pd.read_csv('shiu/Completeness_783.csv', index_col=0)
c = pd.read_parquet('shiu/Connectivity_783.parquet', columns=['Presynaptic_Index', 'Postsynaptic_Index', 'Excitatory x Connectivity'])
net = Network(comp.index.values, c['Presynaptic_Index'].values, c['Postsynaptic_Index'].values, c['Excitatory x Connectivity'].values, np.ones(len(comp)))
del c
S = {'sugar': (net.idx(L['neu_sugar']), 100), 'water': (net.idx(L['neu_water']), 200)}
MN9 = net.idx([720575940660219265, 720575940618238523])
fn = f'confirm_{part}.json'
out = json.load(open(fn)) if os.path.exists(fn) else dict(repeats=30, baseline={}, knockouts={})
mn9 = lambda r: max(float(r[int(i)].mean()) for i in MN9)
t0 = time.time()
for cond, (g, hz) in S.items():
    if cond not in out['baseline']:
        out['baseline'][cond] = mn9(net.run([(g, hz)], seed=zlib.crc32(cond.encode()), p=dict(n_run=30), record=MN9))
print('baseline30', out['baseline'], 'todo', len(todo), flush=True)
for cid, cond in todo:
    k = f'{cid}|{cond}'
    if k in out['knockouts']: continue
    g, hz = S[cond]
    out['knockouts'][k] = mn9(net.run([(g, hz)], silence=net.idx([int(cid)]), seed=zlib.crc32(cond.encode()), p=dict(n_run=30), record=MN9))
    print(k, out['knockouts'][k], f'[{time.time()-t0:.0f}s]', flush=True)
    json.dump(out, open(fn, 'w'))
json.dump(out, open(fn, 'w')); print('done', flush=True)
