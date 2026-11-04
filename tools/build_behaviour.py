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
STIM = [('nothing', 'Nothing', 'No stimulus', bench['s0_b0_w0']), ('sugar', 'Sugar', 'Sugar on the tongue (taste neurons at 100/s)', bench['s100_b0_w0']),
        ('water', 'Water', 'Water on the tongue (water-taste neurons at 200/s)', bench['s0_b0_w200']),
        ('bitter', 'Bitter', 'Bitter on the tongue, like caffeine (bitter-taste neurons at 200/s)', bench['s0_b200_w0']),
        ('sugar_bitter', 'Sugar + bitter', 'Sugar mixed with something bitter (100/s and 200/s)', bench['s100_b200_w0']),
        ('touch', 'Touch the antennae', "Antennae moved (Johnston's organ CE neurons at 100/s)", dict(mn9=None, rates=r1['jo_ce_100']['rates']))]
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
json.dump(out, open(f'{OUT}/behaviour.json', 'w'), separators=(',', ':'))
