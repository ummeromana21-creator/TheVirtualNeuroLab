"""Behaviour lab data: for each stimulus, which brain regions are active and what the fly does.
Region = the FlyWire neuropil where a neuron has most of its synapses (connections of >= 5 synapses), sides merged.
Taste runs: the Taste Bench runs (10 repeats each). Antenna touch: Round 1 run jo_ce_100 (Johnston's organ CE neurons at 100/s).
Behaviour readouts (rules already written for the calibration test): tongue out if MN9 fires >= 10/s (Taste Bench rule);
antennal grooming command if aBN1 fires >= 5/s (Round 1, experiment E7)."""
import json, numpy as np, pandas as pd, sys
OUT = sys.argv[1]
NAME = {'ME': 'Medulla', 'LO': 'Lobula', 'LOP': 'Lobula plate', 'LA': 'Lamina', 'AME': 'Accessory medulla', 'GNG': 'Gnathal ganglia', 'PRW': 'Prow',
  'FLA': 'Flange', 'SAD': 'Saddle', 'AMMC': 'Antennal mechanosensory and motor centre', 'AL': 'Antennal lobe', 'LH': 'Lateral horn',
  'MB_CA': 'Mushroom body calyx', 'MB_ML': 'Mushroom body medial lobe', 'MB_VL': 'Mushroom body vertical lobe', 'MB_PED': 'Mushroom body peduncle',
  'SMP': 'Superior medial protocerebrum', 'SLP': 'Superior lateral protocerebrum', 'SIP': 'Superior intermediate protocerebrum',
  'AVLP': 'Anterior ventrolateral protocerebrum', 'PVLP': 'Posterior ventrolateral protocerebrum', 'PLP': 'Posterior lateral protocerebrum',
  'AOTU': 'Anterior optic tubercle', 'LAL': 'Lateral accessory lobe', 'CRE': 'Crepine', 'VES': 'Vest', 'IPS': 'Inferior posterior slope',
  'SPS': 'Superior posterior slope', 'ICL': 'Inferior clamp', 'SCL': 'Superior clamp', 'IB': 'Inferior bridge', 'ATL': 'Antler', 'GOR': 'Gorget',
  'EPA': 'Epaulette', 'WED': 'Wedge', 'OCG': 'Ocellar ganglion', 'FB': 'Fan-shaped body', 'EB': 'Ellipsoid body', 'PB': 'Protocerebral bridge',
  'NO': 'Noduli', 'BU': 'Bulb', 'GA': 'Gall', 'CAN': 'Cantle', 'UNASGD': 'Not assigned'}
ROLE = {'GNG': 'taste and feeding centre', 'PRW': 'part of the feeding centre', 'AMMC': 'touch and hearing on the antennae', 'SAD': 'next to the antennal touch centre',
  'AL': 'smell', 'LH': 'smell', 'MB_CA': 'learning and memory', 'MB_ML': 'learning and memory', 'MB_VL': 'learning and memory', 'MB_PED': 'learning and memory',
  'ME': 'vision', 'LO': 'vision', 'LOP': 'vision', 'LA': 'vision', 'AME': 'vision', 'FB': 'navigation', 'EB': 'navigation', 'PB': 'navigation', 'NO': 'navigation'}
prim = pd.read_csv('primary_neuropil.csv', index_col=0).np.str.rsplit('_', n=1).str[0]
prim = prim.where(prim.isin(NAME.keys()), prim.str.rsplit('_', n=1).str[0])
codes = sorted(set(prim.unique()) & set(NAME))
cidx = {c: i + 1 for i, c in enumerate(codes)}
roots = np.fromfile('../check2/anatomy/celltypes/rootids.bin', '<u8')
reg = np.array([cidx.get(prim.get(int(r)), 0) for r in roots], np.uint8)
reg.tofile(f'{OUT}/regions.bin')
total = {c: int((reg == cidx[c]).sum()) for c in codes}
bench = json.load(open('bench_runs.json')); r1 = json.load(open('round1_B.json'))['conditions']
ABN1 = '720575940630907434'
NM = {0: 'none'}
STIM = []
for sv in (0, 50, 100, 200):
    for bv in (0, 100, 200):
        for wv in (0, 200):
            k = f's{sv}_b{bv}_w{wv}'
            parts = [f'sugar {sv}/s' if sv else '', f'bitter {bv}/s' if bv else '', f'water {wv}/s' if wv else '']
            STIM.append((k, k, ('Taste neurons switched on: ' + ', '.join(p for p in parts if p)) if any(parts) else 'Nothing on the tongue', bench[k]))
STIM.append(('touch', 'Touch the antennae', "Antennae moved (Johnston's organ CE neurons at 100/s)", dict(mn9=None, rates=r1['jo_ce_100']['rates'])))
out = dict(regions=[dict(code=c, name=NAME[c], role=ROLE.get(c), total=total[c]) for c in codes], stimuli=[],
           source=__doc__.strip(), rules=dict(tongue='MN9 >= 10 firings/s', groom='aBN1 >= 5 firings/s'))
rk = {int(r): i for i, r in enumerate(roots)}
for key, label, desc, run in STIM:
    rates = {int(k): float(v) for k, v in run['rates'].items() if float(v) > 0}
    act = {}
    for r in rates:
        i = rk.get(r)
        if i is None or reg[i] == 0: continue
        act[codes[reg[i] - 1]] = act.get(codes[reg[i] - 1], 0) + 1
    if key == 'touch':
        mn9 = max(r1['jo_ce_100']['readouts']['mn9'].values())
    else:
        mn9 = float(run['mn9'])
    abn1 = float(run['rates'].get(ABN1, 0)) if key != 'touch' else max(r1['jo_ce_100']['readouts']['aBN1'].values())
    out['stimuli'].append(dict(key=key, label=label, desc=desc, mn9=round(mn9, 1), abn1=round(abn1, 1), active=len(rates),
        tongue=mn9 >= 10, groom=abn1 >= 5,
        regions=sorted([dict(code=c, active=n, frac=round(n / total[c], 4)) for c, n in act.items()], key=lambda x: -x['active'])))
    print(key, 'MN9', round(mn9, 1), 'aBN1', round(abn1, 1), 'active', len(rates), out['stimuli'][-1]['regions'][:4])
# where things are in the brain: label anchors for each region (centroid of its larger side), the stimulated input neurons, and the two decision neurons
pos = np.fromfile('../check2/anatomy/celltypes/positions.bin', '<f4').reshape(-1, 3)
mid = pos[:, 0].mean()
anch = {}
for c in codes:
    m = reg == cidx[c]
    if not m.any(): continue
    P = pos[m]; L, R = P[P[:, 0] < mid], P[P[:, 0] >= mid]
    side = P if min(len(L), len(R)) < .25 * len(P) else (L if len(L) >= len(R) else R)
    anch[c] = [round(float(x), 1) for x in np.median(side, axis=0)]
for r in out['regions']: r['anchor'] = anch.get(r['code'])
L = json.load(open('shiu_lists.json'))
pidx = lambda ids: [rk[int(i)] for i in ids if int(i) in rk]
out['inputs'] = dict(sugar=pidx(L['neu_sugar']), bitter=pidx(L['neu_bitter']), water=pidx(L['neu_water']), touch=pidx(L['neu_JON_CE']))
out['deciders'] = dict(mn9=pidx([720575940660219265, 720575940618238523]), abn1=pidx([int(ABN1)]))
json.dump(out, open(f'{OUT}/behaviour.json', 'w'), separators=(',', ':'))
print({k: len(v) for k, v in out['inputs'].items()}, out['deciders'])
