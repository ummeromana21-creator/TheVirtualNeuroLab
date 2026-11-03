"""Calibration test 1 (sugar -> MN9). Runs the pre-registered conditions on each fly. See experiments/calibration_preregistration*.json.
Usage (from a folder holding data/<flywire|banc|malecns>/ Codex exports and shiu/ = github.com/philshiu/Drosophila_brain_model):
  python3 run_calibration.py <flywire_paper|flywire_strong|maxime|hagrid> [repeats] [synapse-strength scale]
Then: python3 build_calibration_json.py <skeleton>/experiments
"""
import json, sys, time, zlib, numpy as np, pandas as pd
sys.path.insert(0, '.')
from lif_engine import Network, INHIBITORY
D = 'data'
S630 = dict(
 sugar=[720575940624963786,720575940630233916,720575940637568838,720575940638202345,720575940617000768,720575940630797113,720575940632889389,720575940621754367,720575940621502051,720575940640649691,720575940639332736,720575940616885538,720575940639198653,720575940620900446,720575940617937543,720575940632425919,720575940633143833,720575940612670570,720575940628853239,720575940629176663,720575940611875570],
 bitter=[720575940621778381,720575940602353632,720575940617094208,720575940619197093,720575940626287336,720575940618600651,720575940627692048,720575940630195909,720575940646212996,720575940610483162,720575940645743412,720575940627578156,720575940622298631,720575940621008895,720575940629146711,720575940610259370,720575940610481370,720575940619028208,720575940614281266,720575940613061118,720575940604027168],
 water=[720575940612950568,720575940631898285,720575940606002609,720575940612579053,720575940622902535,720575940616177458,720575940660292225,720575940622486922,720575940613786774,720575940629852866,720575940625861168,720575940613996959,720575940617857694,720575940644965399,720575940625203504,720575940630553415,720575940635172191,720575940634796536],
 mn9=[720575940660219265,720575940645521262])
TYPES = dict(sugar=['LB3b','LB3c'], bitter=['LB1a','LB1b','LB1c','LB1d'], water=['LB2d','LB3a'])

def flywire(strong):
    comp = pd.read_csv('shiu/2023_03_23_completeness_630_final.csv', index_col=0)
    c = pd.read_parquet('shiu/2023_03_23_connectivity_630_final.parquet')
    if strong:
        c = c[c['Connectivity'] >= 5]
    net = Network(comp.index.values, c['Presynaptic_Index'].values, c['Postsynaptic_Index'].values,
                  c['Excitatory x Connectivity'].values, np.ones(len(comp)))
    return net, {k: net.idx(v) for k, v in S630.items()}, {k: len(v) for k, v in S630.items()}

def codex(name):
    n = pd.read_csv(f'{D}/{name}/neurons.csv.gz')
    ids = n['Root ID'].values
    sign = np.where(n['Predicted NT type'].fillna('').str.upper().isin(INHIBITORY), -1.0, 1.0)
    c = pd.read_csv(f'{D}/{name}/connections.csv.gz', usecols=['pre_root_id', 'post_root_id', 'syn_count'])
    c = c.groupby(['pre_root_id', 'post_root_id'], as_index=False).syn_count.sum()
    c = c[c.syn_count >= 5]
    ix = pd.Index(ids)
    pre, post = ix.get_indexer(c.pre_root_id), ix.get_indexer(c.post_root_id)
    ok = (pre >= 0) & (post >= 0)
    net = Network(ids, pre[ok], post[ok], c.syn_count.values[ok], sign)
    t = n['Primary Cell Type'].astype(str); side = n['Soma side'].astype(str)
    sets = {k: net.idx(n.loc[t.isin(v) & (side == 'right'), 'Root ID']) for k, v in TYPES.items()}
    sets['mn9'] = net.idx(n.loc[t == 'MN9', 'Root ID'])
    nt_of_mn9_inputs = None
    return net, sets, {k: len(v) for k, v in sets.items()}

CONDS = [(f'sugar_{f}', [('sugar', f)]) for f in (10, 20, 40, 60, 80, 100, 150, 200)] + [
    ('bitter_200', [('bitter', 200)]), ('sugar_100_bitter_200', [('sugar', 100), ('bitter', 200)]),
    ('water_200', [('water', 200)]), ('nothing', [])]

fly = sys.argv[1]
RUNP = dict(n_run=int(sys.argv[2])) if len(sys.argv) > 2 and sys.argv[2] != '30' else {}
SCALE = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
if SCALE != 1.0:   # test 1b: synapse strength scaled; the stimulation kick (0.275 mV x 250) is kept the same
    RUNP.update(w_syn=0.275 * SCALE, f_poi=0.275 * 250 / (0.275 * SCALE))
TAG = '' if SCALE == 1.0 else '_1b'
t0 = time.time()
net, sets, counts = {'flywire_paper': lambda: flywire(False), 'flywire_strong': lambda: flywire(True),
                     'maxime': lambda: codex('banc'), 'hagrid': lambda: codex('malecns')}[fly]()
print(fly, 'neurons', net.N, 'connections', net.W.nnz, 'sets', counts, flush=True)
res = dict(fly=fly, n_run=RUNP.get('n_run', 30), neurons=int(net.N), connections=int(net.W.nnz), counts=counts,
           mn9_ids=[int(net.ids[i]) for i in sets['mn9']], conditions={})
for name, groups in CONDS:
    out = net.run([(sets[g], f) for g, f in groups], seed=zlib.crc32(name.encode()), record=sets["mn9"], p=RUNP)
    mn = {int(net.ids[i]): float(out[int(i)].mean()) for i in sets['mn9']}
    sd = {int(net.ids[i]): float(out[int(i)].std()) for i in sets['mn9']}
    active = sum(1 for k, v in out.items() if v.mean() > 0)
    top = sorted(((float(v.mean()), int(net.ids[k])) for k, v in out.items()), reverse=True)[:60]
    res['conditions'][name] = dict(mn9_hz=mn, mn9_sd=sd, neurons_active=active, top=top)
    print(f'{name:24s} MN9 {mn}  active {active}  [{time.time()-t0:.0f}s]', flush=True)
res['w_syn_scale'] = SCALE
json.dump(res, open(f'result_{fly}{TAG}.json', 'w'), indent=1)
