"""Timed runs for the Neuron Silencing Screen viewer: one recorded trial per run, first 200 ms, with the real connections the
signal travelled along ("streaks"). A streak A->B is drawn when B fires and A, which is wired to B with an
excitatory connection, fired 1.8-7 ms earlier (the model's synaptic delay plus rise time). Paths and timings are
from the simulation; colours and glow are styling.
Usage: python3 run_streaks.py <list.json of root ids to knock out (may be empty)> <out dir> <part> <of>"""
import json, os, sys, time, zlib
import numpy as np, pandas as pd
sys.path.insert(0, '.')
from lif_engine import Network
ids_file, OUT, part, of = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
os.makedirs(OUT, exist_ok=True)
L = json.load(open('shiu_lists.json'))
comp = pd.read_csv('shiu/Completeness_783.csv', index_col=0)
c = pd.read_parquet('shiu/Connectivity_783.parquet', columns=['Presynaptic_Index', 'Postsynaptic_Index', 'Excitatory x Connectivity'])
net = Network(comp.index.values, c['Presynaptic_Index'].values, c['Postsynaptic_Index'].values, c['Excitatory x Connectivity'].values, np.ones(len(comp)))
del c
WT = net.W.T.tocsr()          # rows = postsynaptic neuron: who feeds it
S = {'sugar': (net.idx(L['neu_sugar']), 100), 'water': (net.idx(L['neu_water']), 200)}
MN9 = net.idx([720575940660219265, 720575940618238523])
WIN = 100.0
jobs = [None] + json.load(open(ids_file))
jobs = jobs[part::of]
t0 = time.time()
for ko in jobs:
    for cond, (g, hz) in S.items():
        fn = os.path.join(OUT, f"{ko or 'none'}_{cond}.json")
        if os.path.exists(fn): continue
        sil = net.idx([int(ko)]) if ko else ()
        times = []
        net.run([(g, hz)], silence=sil, seed=zlib.crc32(cond.encode()), p=dict(n_run=1, t_run=WIN), times=times)
        spikes = sorted(times, key=lambda x: x[1])
        by = {}
        for n, t in spikes: by.setdefault(n, []).append(t)
        streaks = []
        silenced = set(int(x) for x in sil) if len(sil) else set()
        for n, t in spikes:
            row = WT[n]
            for a, w in zip(row.indices, row.data):
                if w <= 0 or a in silenced or a not in by: continue
                if any(1.8 <= t - ta <= 7.0 for ta in by[a]):
                    streaks.append((int(a), int(n), t, round(float(w), 2)))
        # first time each real connection carried the signal; links between the switched-on sensors themselves are left out
        inp = set(int(x) for x in g)
        seen, keep = set(), []
        for a, b, t, w in streaks:
            if (a, b) in seen or (a in inp and b in inp): continue
            seen.add((a, b)); keep.append((a, b, t, w))
        keep = keep[:6000]
        first = {}
        for n, t in spikes: first.setdefault(n, t)
        rid = lambda i: str(int(net.ids[i]))
        json.dump(dict(knockout=ko, condition=cond, window_ms=WIN,
                       first_spike={rid(n): t for n, t in first.items()},
                       spikes=len(spikes),
                       mn9_first=[first.get(int(i)) for i in MN9],
                       streaks=[[rid(a), rid(b), t] for a, b, t, w in keep]),
                  open(fn, 'w'), separators=(',', ':'))
        print(ko, cond, 'neurons', len(first), 'streaks', len(keep), f'[{time.time()-t0:.0f}s]', flush=True)
print('done')
