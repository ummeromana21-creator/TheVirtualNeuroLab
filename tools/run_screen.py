"""Discovery Screen 1 (see preregistration_screen1.json). Usage: python3 run_screen.py <part 0|1> <of 2> [repeats]
Silences each candidate in turn and records MN9 for sugar 100/s and water 200/s. Same random seed for every run of a
condition (so knock-out and baseline see the same input spikes)."""
import json, sys, time, zlib
import numpy as np, pandas as pd
sys.path.insert(0, '.')
from lif_engine import Network
part, of = int(sys.argv[1]), int(sys.argv[2]); rep = int(sys.argv[3]) if len(sys.argv) > 3 else 10
P = json.load(open('preregistration_screen1.json')); L = json.load(open('shiu_lists.json'))
comp = pd.read_csv('shiu/Completeness_783.csv', index_col=0)
c = pd.read_parquet('shiu/Connectivity_783.parquet', columns=['Presynaptic_Index', 'Postsynaptic_Index', 'Excitatory x Connectivity'])
net = Network(comp.index.values, c['Presynaptic_Index'].values, c['Postsynaptic_Index'].values, c['Excitatory x Connectivity'].values, np.ones(len(comp)))
del c
S = {'sugar': (net.idx(L['neu_sugar']), 100), 'water': (net.idx(L['neu_water']), 200)}
MN9 = net.idx([720575940660219265, 720575940618238523])
cands = P['candidates_ids'][part::of]
import os
out = json.load(open(f'screen_{part}.json')) if os.path.exists(f'screen_{part}.json') else dict(repeats=rep, baseline={}, knockouts={})
t0 = time.time()
def mn9(r): return max(float(r[int(i)].mean()) for i in MN9)
for cond, (g, hz) in S.items():
    if cond in out['baseline']: continue
    out['baseline'][cond] = mn9(net.run([(g, hz)], seed=zlib.crc32(cond.encode()), p=dict(n_run=rep), record=MN9))
print('baseline', out['baseline'], flush=True)
for k, cid in enumerate(cands):
    if cid in out['knockouts']: continue
    ix = net.idx([int(cid)])
    out['knockouts'][cid] = {cond: mn9(net.run([(g, hz)], silence=ix, seed=zlib.crc32(cond.encode()), p=dict(n_run=rep), record=MN9))
                             for cond, (g, hz) in S.items()}
    if k % 5 == 0:
        print(k, len(cands), cid, out['knockouts'][cid], f'[{time.time()-t0:.0f}s]', flush=True)
        json.dump(out, open(f'screen_{part}.json', 'w'))
json.dump(out, open(f'screen_{part}.json', 'w')); print('done', flush=True)
