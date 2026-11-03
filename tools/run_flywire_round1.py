"""FlyWire v783: calibration + experiments round 1, exactly as saved in preregistration_flywire_round1.json.
Usage: python3 run_flywire_round1.py <part: A|B>   (A = calibration then E1/E2; B = E4, E6, E7)
Needs shiu/ (github.com/philshiu/Drosophila_brain_model) and shiu_lists.json (neuron lists copied from its figures.ipynb).
"""
import json, sys, time, zlib, pickle
import numpy as np, pandas as pd
sys.path.insert(0, '.')
from lif_engine import Network

part = sys.argv[1]
L = json.load(open('shiu_lists.json'))
sez = pickle.load(open('shiu/sez_neurons.pickle', 'rb'))
comp = pd.read_csv('shiu/Completeness_783.csv', index_col=0)
c = pd.read_parquet('shiu/Connectivity_783.parquet', columns=['Presynaptic_Index', 'Postsynaptic_Index', 'Excitatory x Connectivity'])
net = Network(comp.index.values, c['Presynaptic_Index'].values, c['Postsynaptic_Index'].values,
              c['Excitatory x Connectivity'].values, np.ones(len(comp)))
del c
S = {k: net.idx(L['neu_' + k]) for k in ('sugar', 'bitter', 'water', 'ir94e', 'JON_CE', 'JON_F')}
for k in ('usnea', 'phantom', 'G2N_1', 'fudog', 'bract', 'roundup'):
    S[k] = net.idx([int(i) for i in sez[k]])
READ = {'mn9': net.idx([720575940660219265, 720575940618238523]), 'usnea': S['usnea'], 'fudog': S['fudog'],
        'aBN1': net.idx([L['id_aBN1']])}
counts = {k: int(len(v)) for k, v in S.items()}
print('neurons', net.N, 'connections', net.W.nnz, counts, flush=True)
t0 = time.time()
res = dict(part=part, neurons=int(net.N), connections=int(net.W.nnz), counts=counts, conditions={})


def run(name, groups, silence=()):
    sil = np.concatenate([S[s] for s in silence]) if silence else ()
    out = net.run([(S[g], f) for g, f in groups], silence=sil, seed=zlib.crc32(name.encode()),
                  record=np.concatenate(list(READ.values())))
    r = {k: {str(int(net.ids[i])): float(out[int(i)].mean()) for i in v} for k, v in READ.items()}
    rates = {str(int(net.ids[k])): round(float(v.mean()), 2) for k, v in out.items() if v.mean() > 0}
    res['conditions'][name] = dict(groups=groups, silence=list(silence), readouts=r, neurons_active=len(rates), rates=rates)
    print(f'{name:30s} MN9 {max(r["mn9"].values()):6.1f} usnea {max(r["usnea"].values()):5.1f} fudog {max(r["fudog"].values()):5.1f} '
          f'aBN1 {max(r["aBN1"].values()):5.1f} active {len(rates)} [{time.time()-t0:.0f}s]', flush=True)
    json.dump(res, open(f'round1_{part}.json', 'w'))
    return max(r['mn9'].values())


if part == 'A':
    mn = {}
    for f in (10, 20, 40, 60, 80, 100, 150, 200):
        mn[f] = run(f'sugar_{f}', [('sugar', f)])
    run('bitter_200', [('bitter', 200)])
    run('sugar_100_bitter_200', [('sugar', 100), ('bitter', 200)])
    run('water_200', [('water', 200)])
    run('nothing', [])
    weak = min([f for f in mn if mn[f] >= 10], default=None)
    res['weak_sugar'] = weak
    print('weak sugar =', weak, flush=True)
    if weak:
        run(f'sugar_{weak}_bitter_200', [('sugar', weak), ('bitter', 200)])
        run('sugar_200_bitter_200', [('sugar', 200), ('bitter', 200)])
        run(f'sugar_{weak}_ir94e_200', [('sugar', weak), ('ir94e', 200)])
        run('sugar_200_ir94e_200', [('sugar', 200), ('ir94e', 200)])
else:
    run('usnea_100', [('usnea', 100)])
    run('phantom_100', [('phantom', 100)])
    run('water_200_ref', [('water', 200)])
    for s in ('usnea', 'bract', 'roundup', 'G2N_1'):
        run(f'water_200_silence_{s}', [('water', 200)], silence=(s,))
    run('jo_ce_100', [('JON_CE', 100)])
    run('jo_f_100', [('JON_F', 100)])
json.dump(res, open(f'round1_{part}.json', 'w'))
print('done', flush=True)
