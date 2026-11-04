"""Knockout maps built from many simulation runs (replaces the one-run maps).
For every map (normal brain, and each of the 286 neurons switched off; sugar and water), run the simulation 20 times
with different random input (seeds 1-20), 100 ms each. A line A->B is kept only if the signal crossed that real,
excitatory connection (B fired 1.8-7 ms after A) in at least 10 of the 20 runs. Times are medians over the runs in which
the event happened. Neurons are kept if they fired in at least 10 of 20 runs. Rule written before the run; it does not
change any prediction (those come from the 30-repeat averages).
Usage: python3 run_maps.py <ids.json> <out dir> <part> <of>"""
import json, os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, '.')
from lif_engine import Network
ids_file, OUT, part, of = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
os.makedirs(OUT, exist_ok=True)
SEEDS, NEED, WIN = range(1, 21), 10, 100.0
L = json.load(open('shiu_lists.json'))
comp = pd.read_csv('shiu/Completeness_783.csv', index_col=0)
c = pd.read_parquet('shiu/Connectivity_783.parquet', columns=['Presynaptic_Index', 'Postsynaptic_Index', 'Excitatory x Connectivity'])
net = Network(comp.index.values, c['Presynaptic_Index'].values, c['Postsynaptic_Index'].values, c['Excitatory x Connectivity'].values, np.ones(len(comp)))
del c
WT = net.W.T.tocsr()
S = {'sugar': (net.idx(L['neu_sugar']), 100), 'water': (net.idx(L['neu_water']), 200)}
MN9 = [int(i) for i in net.idx([720575940660219265, 720575940618238523])]
roots = np.fromfile('../check/anatomy/celltypes/rootids.bin', '<u8'); pos = {int(r): i for i, r in enumerate(roots)}
P = lambda i: pos.get(int(net.ids[i]))
jobs = ([None] + json.load(open(ids_file)))[part::of]
t0 = time.time()
for ko in jobs:
    for cond, (g, hz) in S.items():
        fn = os.path.join(OUT, f"{ko or 'none'}_{cond}.json")
        if os.path.exists(fn): continue
        sil = net.idx([int(ko)]) if ko else ()
        silenced = set(int(x) for x in sil) if len(sil) else set()
        inp = set(int(x) for x in g)
        pair_t, first_t, mn9_t, route_n = {}, {}, {i: [] for i in MN9}, {}
        for seed in SEEDS:
            times = []
            net.run([(g, hz)], silence=sil, seed=seed, p=dict(n_run=1, t_run=WIN), times=times)
            by = {}
            for n, t in times: by.setdefault(n, []).append(t)
            seen = set()
            for n, t in sorted(times, key=lambda x: x[1]):
                row = WT[n]
                for a, w in zip(row.indices, row.data):
                    a = int(a)
                    if w <= 0 or a in silenced or a not in by or (a, n) in seen or (a in inp and n in inp): continue
                    if any(1.8 <= t - ta <= 7.0 for ta in by[a]):
                        seen.add((a, n)); pair_t.setdefault((a, n), []).append(t)
            # route to MN9 in THIS run: walk back from MN9's first spike along connections crossed no later than the cell they fed
            run_pairs = {}
            for (a, b2), ts in pair_t.items():
                if (a, b2) in seen: run_pairs[(a, b2)] = ts[-1]
            into = {}
            for (a, b2), t in run_pairs.items(): into.setdefault(b2, []).append((a, t))
            fst = {n: min(ts) for n, ts in by.items()}
            on, stack, done = set(), [(i, fst[i]) for i in MN9 if i in fst], set()
            while stack:
                node, t = stack.pop()
                for a, ta in into.get(node, []):
                    if ta <= t and (a, node) not in on:
                        on.add((a, node)); k = (a, ta)
                        if k not in done: done.add(k); stack.append((a, min(fst.get(a, ta), ta)))
            for e in on: route_n[e] = route_n.get(e, 0) + 1
            for n, ts in by.items(): first_t.setdefault(n, []).append(min(ts))
            for i in MN9: mn9_t[i].append(min(by[i]) if i in by else None)
        f = sorted(((P(n), int(round(10 * np.median(ts)))) for n, ts in first_t.items() if len(ts) >= NEED and P(n) is not None), key=lambda x: x[1])
        s = sorted(([P(a), P(b), int(round(10 * np.median(ts))), len(ts), route_n.get((a, b), 0)] for (a, b), ts in pair_t.items()
                    if len(ts) >= NEED and P(a) is not None and P(b) is not None), key=lambda x: x[2])
        s = [e for e in s if e[4] >= NEED] + [e for e in s if e[4] < NEED][:max(0, 6000 - sum(e[4] >= NEED for e in s))]
        s.sort(key=lambda x: x[2])
        m = []
        for i in MN9:
            v = [t for t in mn9_t[i] if t is not None]
            m.append(int(round(10 * np.median(v))) if len(v) >= NEED else None)
        json.dump(dict(f=f, s=s, mn9=m, runs=len(SEEDS), rule=f'[a,b,t10,runs crossed,runs on route to MN9]; kept if crossed in >= {NEED} of {len(SEEDS)} runs; on route if on the route in >= {NEED} runs; times are medians',
                       mn9_reached=[sum(t is not None for t in mn9_t[i]) for i in MN9]), open(fn, 'w'), separators=(',', ':'))
    print(ko, f'[{time.time()-t0:.0f}s]', flush=True)
print('done', flush=True)
