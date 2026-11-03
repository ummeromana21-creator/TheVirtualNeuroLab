import json, sys, zlib, numpy as np, pandas as pd
sys.path.insert(0, '.'); from lif_engine import Network
L = json.load(open('shiu_lists.json')); dan = pd.read_csv('dan.csv').root_id.astype(int).tolist()
comp = pd.read_csv('shiu/Completeness_783.csv', index_col=0)
c = pd.read_parquet('shiu/Connectivity_783.parquet', columns=['Presynaptic_Index', 'Postsynaptic_Index', 'Excitatory x Connectivity'])
net = Network(comp.index.values, c['Presynaptic_Index'].values, c['Postsynaptic_Index'].values, c['Excitatory x Connectivity'].values, np.ones(len(comp))); del c
S = {'sugar': (net.idx(L['neu_sugar']), 100), 'water': (net.idx(L['neu_water']), 200)}
MN9 = net.idx([720575940660219265, 720575940618238523]); D = net.idx(dan)
out = {}
for cond, (g, hz) in S.items():
    seed = zlib.crc32(cond.encode())
    b = net.run([(g, hz)], seed=seed, p=dict(n_run=30), record=MN9)
    k = net.run([(g, hz)], silence=D, seed=seed, p=dict(n_run=30), record=MN9)
    mb = max(float(b[int(i)].mean()) for i in MN9); mk = max(float(k[int(i)].mean()) for i in MN9)
    dan_active = sum(1 for i in D if int(i) in b and b[int(i)].mean() > 0)
    out[cond] = dict(normal=round(mb, 2), dopamine_removed=round(mk, 2), dan_firing_normal=dan_active, n_dan=len(D)); print(cond, out[cond], flush=True)
json.dump(out, open('pd_fast.json', 'w'))
