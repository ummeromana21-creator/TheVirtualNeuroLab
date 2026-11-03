"""Per-fly counts for the Fly Lab skeleton: each fly from its OWN connectome export only.

    Maxime  = BANC (female brain + nerve cord), Codex export in ~/Desktop/Databases/BANC
    Hagrid  = male CNS (brain + nerve cord),    Codex export in ~/Desktop/Databases/Male CNS

Same counting rule for both flies: a "connection" is one pair of neurons joined by at least
MIN_SYN synapses in total (the BANC export already drops pairs under 3, the male export pairs
under 5, so 5 is the strictest common rule). Synapses are summed over those connections only.

Run from the skeleton folder:  python3 tools/build_fly_counts.py  -> library/flies.json
"""
import json, os, re, sys
import pandas as pd

DB = os.path.expanduser(os.environ.get('FLY_DB', '~/Desktop/Databases'))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'library', 'flies.json')
MIN_SYN = 5
NOT_NEURONS = {'glia', 'trachea', 'not_a_neuron'}

# Export neuropil labels -> standard names (Ito et al. 2014 brain; Court et al. 2020 nerve cord).
VNC_MAP = [
    (r'^(VNC_)?T1_ProNm$|^LegNp_T1$', 'ProNm'), (r'^(VNC_)?T2_MesoNm$|^LegNp_T2$', 'MesoNm'),
    (r'^(VNC_)?T3_MetaNm$|^LegNp_T3$', 'MetaNm'), (r'^ABDNM$|^ANm$', 'ANm'),
    (r'^VNC_HTct$|^HTct_UTct_T3$', 'HTct'), (r'^VNC_WTct$|^WTct_UTct_T2$', 'WTct'),
    (r'^VNC_NTct$|^NTct_UTct_T1$', 'NTct'), (r'^VNC_AMNp$|^AMNp$', 'AMNp'),
    (r'^(VNC_)?T\d_mVAC$|^mVAC_T\d$|^mVAC$', 'mVAC'), (r'^IntTct$', 'IntTct'), (r'^LTct$', 'LTct'),
    (r'^Ov$', 'AMNp'),  # 'ovoid' = accessory mesothoracic neuropil (VFB exact synonym)
    (r'^Tct$', 'Tct (unsplit)'),
]
NERVE = re.compile(r'^(ADMN|PDMN|AbN\d|AbNT|DMetaN|DProN|VProN|PrN|ProAN|MesoAN|ProLN|MesoLN|MetaLN|CvN|Xnerve)$')
UNASSIGNED = re.compile(r'UNASGD|^cervical_connective$')


def region(label):
    base = re.sub(r'_(L|R)$', '', str(label))
    for pat, name in VNC_MAP:
        if re.match(pat, base):
            return name
    if NERVE.match(base):
        return 'nerves'
    if UNASSIGNED.search(base):
        return 'unassigned'
    return base


def side(label):
    m = re.search(r'_(L|R)$', str(label))
    return m.group(1) if m else 'C'


def fly(folder):
    n = pd.read_csv(os.path.join(DB, folder, 'neurons.csv.gz'), usecols=['Root ID', 'Super Class'])
    sc = n['Super Class'].fillna('')
    neurons = int((~sc.isin(NOT_NEURONS)).sum())
    c = pd.read_csv(os.path.join(DB, folder, 'connections_princeton.csv.gz'),
                    usecols=['pre_root_id', 'post_root_id', 'neuropil', 'syn_count'])
    pair = c.groupby(['pre_root_id', 'post_root_id'], sort=False)['syn_count'].transform('sum')
    raw_rows, raw_pairs = len(c), int(c.groupby(['pre_root_id', 'post_root_id']).ngroups)
    c = c[pair >= MIN_SYN]
    c['region'] = c['neuropil'].map(region)
    c['side'] = c['neuropil'].map(side)
    regions = {}
    for r, g in c.groupby('region'):
        by_side = g.groupby('side').syn_count.sum().to_dict()
        ids = pd.unique(pd.concat([g.pre_root_id, g.post_root_id]))
        regions[r] = dict(synapses=int(g.syn_count.sum()), neurons=int(len(ids)),
                          left=int(by_side.get('L', 0)), right=int(by_side.get('R', 0)),
                          labels=sorted(set(g.neuropil.astype(str))))
    conns = int(c.groupby(['pre_root_id', 'post_root_id']).ngroups)
    return dict(folder=folder, neurons_in_file=int(len(n)), neurons=neurons,
                connections=conns, synapses=int(c.syn_count.sum()),
                export_rows=raw_rows, export_pairs=raw_pairs, regions=regions)


if __name__ == '__main__':
    out = dict(
        rule=f'connections = neuron pairs joined by >= {MIN_SYN} synapses; synapses counted only within those',
        maxime=dict(name='Maxime', sex='female', dataset='BANC (brain and nerve cord)', **fly('BANC')),
        hagrid=dict(name='Hagrid', sex='male', dataset='male CNS (brain and nerve cord)', **fly('Male CNS')),
    )
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, 'w'), indent=1)
    for k in ('maxime', 'hagrid'):
        f = out[k]
        print(k, f['neurons'], 'neurons;', f['connections'], 'connections;', f['synapses'], 'synapses;',
              len(f['regions']), 'regions')
