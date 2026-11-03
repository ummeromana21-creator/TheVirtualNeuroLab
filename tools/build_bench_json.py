"""Turn bench_runs.json (FlyWire root id -> firing rate) into <skeleton>/experiments/bench.json, indexed by the
row order of anatomy/celltypes/positions.bin (the Fly Atlas FlyWire positions).
Usage: python3 build_bench_json.py <skeleton dir>"""
import json, sys
import numpy as np
SK = sys.argv[1]
roots = np.fromfile(f'{SK}/anatomy/celltypes/rootids.bin', '<u8')
ix = {int(r): i for i, r in enumerate(roots)}
L = json.load(open('shiu_lists.json'))
runs = json.load(open('bench_runs.json'))
out = dict(repeats=10, inputs={k: [ix[i] for i in L['neu_' + k] if i in ix] for k in ('sugar', 'bitter', 'water')},
           mn9=[ix[i] for i in (720575940660219265, 720575940618238523) if i in ix], runs={})
missing = 0
for k, r in runs.items():
    pairs = sorted(((ix[int(i)], v) for i, v in r['rates'].items() if int(i) in ix), key=lambda t: -t[1])
    missing += sum(1 for i in r['rates'] if int(i) not in ix)
    out['runs'][k] = dict(mn9=r['mn9'], idx=[p[0] for p in pairs], rate=[p[1] for p in pairs])
json.dump(out, open(f'{SK}/experiments/bench.json', 'w'), separators=(',', ':'))
print('runs', len(out['runs']), 'neurons without a position (not drawn):', missing)
