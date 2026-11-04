"""Per-neuron facts for the Neuron Silencing Screen explanation panel. Everything comes from data files, nothing typed by hand:
FlyWire v783 annotations (classification, predicted neurotransmitter), FlyWire synapse table (>= 5 synapses per connection),
the Shiu et al. 2024 taste-neuron lists, the 30/10-run screen results (screen.json) and the 20-run maps (runs/).
Usage: python3 build_profiles.py <discover dir>"""
import json, sys, os
import pandas as pd

DISC = sys.argv[1]
L = json.load(open('shiu_lists.json'))
SUGAR, WATER = set(map(int, L['neu_sugar'])), set(map(int, L['neu_water']))
MN9 = {720575940660219265, 720575940618238523}
S = json.load(open(os.path.join(DISC, 'screen.json')))
ids = [int(n['id']) for n in S['neurons']]
cls = pd.read_csv('data/flywire/classification.csv.gz').set_index('root_id')
nt = pd.read_csv('data/flywire/neurons.csv.gz', usecols=['root_id', 'nt_type', 'nt_type_score']).set_index('root_id')
con = pd.read_csv('data/flywire/connections.csv.gz', usecols=['pre_root_id', 'post_root_id', 'neuropil', 'syn_count'])
ids_set = set(ids)
out = con[con.pre_root_id.isin(ids_set)]
inn = con[con.post_root_id.isin(ids_set)]
roots = __import__('numpy').fromfile(os.path.join(DISC, '..', 'anatomy', 'celltypes', 'rootids.bin'), '<u8')
pos = {int(r): i for i, r in enumerate(roots)}
# count taste inputs against the same taste neurons the page shows (those with a position in the anatomy files)
SUGAR, WATER = {r for r in SUGAR if pos.get(r) in set(S['inputs']['sugar'])}, {r for r in WATER if pos.get(r) in set(S['inputs']['water'])}

def route_set(fn):
    p = os.path.join(DISC, 'runs', fn)
    if not os.path.exists(p): return set()
    d = json.load(open(p)); return {x for e in d['s'] if e[4] >= 10 for x in e[:2]}
on_route = {c: route_set(f'none_{c}.json') for c in ('sugar', 'water')}
NTW = {'ACH': 'acetylcholine', 'GABA': 'GABA', 'GLUT': 'glutamate', 'DA': 'dopamine', 'SER': 'serotonin', 'OCT': 'octopamine'}
REG = {'GNG': 'the gnathal ganglia (the taste and feeding centre)', 'PRW': 'the prow (part of the feeding centre)', 'SAD': 'the saddle',
       'FLA': 'the flange (near the feeding centre)', 'AMMC': 'the antennal mechanosensory centre', 'SMP': 'the superior medial protocerebrum',
       'SLP': 'the superior lateral protocerebrum', 'VES': 'the vest', 'CAN': 'the cantle', 'IPS': 'the inferior posterior slope', 'SPS': 'the superior posterior slope', 'SCL': 'the superior clamp', 'ICL': 'the inferior clamp',
       'LH': 'the lateral horn (a smell-processing area)', 'AL': 'the antennal lobe (the first smell centre)'}
reg = lambda np_: REG.get(str(np_).rsplit('_', 1)[0], str(np_).rsplit('_', 1)[0])

prof = {}
for n in S['neurons']:
    r = int(n['id'])
    o, i = out[out.pre_root_id == r], inn[inn.post_root_id == r]
    c = cls.loc[r] if r in cls.index else None
    t = nt.loc[r] if r in nt.index else None
    top_out = o.groupby('neuropil').syn_count.sum().sort_values(ascending=False)
    top_in = i.groupby('neuropil').syn_count.sum().sort_values(ascending=False)
    same_type = sum(1 for m in S['neurons'] if m['type'] == n['type'])
    p = pos.get(r)
    prof[n['id']] = dict(
        super_class=None if c is None else (None if pd.isna(c.super_class) else c.super_class),
        cls=None if c is None else (None if pd.isna(c['class']) else c['class']),
        side=None if c is None else (None if pd.isna(c.side) else c.side),
        hemilineage=None if c is None else (None if pd.isna(c.hemilineage) else c.hemilineage),
        nt=None if t is None or pd.isna(t.nt_type) else NTW.get(t.nt_type, t.nt_type),
        nt_score=None if t is None or pd.isna(t.nt_type_score) else round(float(t.nt_type_score), 2),
        in_syn=int(i.syn_count.sum()), in_partners=int(i.pre_root_id.nunique()),
        out_syn=int(o.syn_count.sum()), out_partners=int(o.post_root_id.nunique()),
        from_sugar=int(i[i.pre_root_id.isin(SUGAR)].syn_count.sum()), from_sugar_n=int(i[i.pre_root_id.isin(SUGAR)].pre_root_id.nunique()),
        from_water=int(i[i.pre_root_id.isin(WATER)].syn_count.sum()), from_water_n=int(i[i.pre_root_id.isin(WATER)].pre_root_id.nunique()),
        to_mn9=int(o[o.post_root_id.isin(MN9)].syn_count.sum()),
        out_region=None if top_out.empty else reg(top_out.index[0]), in_region=None if top_in.empty else reg(top_in.index[0]),
        on_route_sugar=p in on_route['sugar'], on_route_water=p in on_route['water'], same_type_in_screen=same_type)
json.dump(dict(source='FlyWire v783 annotations and synapse table (connections of >= 5 synapses); predicted transmitter from Eckstein et al. 2024; '
                      'taste neurons from Shiu et al. 2024; route = on the signal\'s route to MN9 in >= 10 of 20 runs of the normal brain',
               neurons=prof), open(os.path.join(DISC, 'profiles.json'), 'w'), separators=(',', ':'))
print(len(prof), 'profiles')
