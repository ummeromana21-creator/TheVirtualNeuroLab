"""Assemble discover/screen.json and discover/runs/*.json for the Knockout Lab page.
Usage: python3 build_screen_json.py <skeleton dir> <flywire consolidated_cell_types.csv.gz> <streaks dir>"""
import json, sys, os, glob, pickle
import numpy as np, pandas as pd
SK, CT, ST = sys.argv[1:4]
P = json.load(open('preregistration_screen1.json'))
scr = [json.load(open(f'screen_{p}.json')) for p in (0, 1)]
conf = {}; base30 = None
for f in sorted(glob.glob('confirm_*.json')):
    c = json.load(open(f)); conf.update(c['knockouts']); base30 = base30 or c['baseline']
roots = np.fromfile(f'{SK}/anatomy/celltypes/rootids.bin', '<u8'); ix = {int(r): i for i, r in enumerate(roots)}
types = pd.read_csv(CT).set_index('root_id').primary_type
sez = pickle.load(open('shiu/sez_neurons.pickle', 'rb')); L = json.load(open('shiu_lists.json'))
shiu_name = {int(i): k for k, v in sez.items() for i in v}
NEED = 0.2
neurons = []
for s in scr:
    for cid, v in s['knockouts'].items():
        r = int(cid); n = dict(id=cid, idx=ix.get(r), type=None if pd.isna(types.get(r)) else str(types.get(r)))
        nm = shiu_name.get(r)
        n['label'] = (f'"{nm[0].upper() + nm[1:]}"' if nm else (n['type'] or 'unnamed')) + ('' if nm or not n['type'] else '')
        n['tested'] = bool(nm)
        n['repeats'] = s['repeats']
        for cond in ('sugar', 'water'):
            key = f'{cid}|{cond}'
            if key in conf:                      # confirmed with 30 repeats: report only that
                val, b = conf[key], base30[cond]; n[cond + '_rep'] = 30
            else:
                val, b = v[cond], s['baseline'][cond]; n[cond + '_rep'] = s['repeats']
            n[cond] = round(val, 1); n[cond + '_base'] = round(b, 1); n[cond + '_drop'] = round(1 - val / b, 3) if b > 0 else 0.0
            n[cond + '_needed'] = bool(key in conf and n[cond + '_drop'] > NEED)
        neurons.append(n)
# labels: make duplicates distinguishable (left/right copies etc.)
cnt = {}
for n in neurons: cnt[n['label']] = cnt.get(n['label'], 0) + 1
seen = {}
for n in neurons:
    if cnt[n['label']] > 1:
        seen[n['label']] = seen.get(n['label'], 0) + 1; n['label'] += f" #{seen[n['label']]}"
needed = [n for n in neurons if n['sugar_needed'] or n['water_needed']]
data = dict(written=P['written'], repeats_confirm=30, baseline={k: round(v, 1) for k, v in (base30 or scr[0]['baseline']).items()},
            inputs={k: [ix[i] for i in L['neu_' + k] if i in ix] for k in ('sugar', 'water')},
            mn9=[ix[i] for i in (720575940660219265, 720575940618238523)], neurons=neurons, prereg=P,
            summary=f"Discovery Screen 1: {len(neurons)} neurons switched off one at a time on the FlyWire brain. {len(needed)} predicted needed for eating or drinking "
                    f"(MN9 more than 20% lower, confirmed with 30 repeats); {sum(1 for n in needed if not n['tested'])} of them have no living-fly test known to the lab.",
            predictions=[dict(name=n['label'], type=n['type'], id=n['id'], eating=n['sugar_needed'], drinking=n['water_needed'],
                              sugar=f"{n['sugar']} ({-round(100*n['sugar_drop'])}%)", water=f"{n['water']} ({-round(100*n['water_drop'])}%)",
                              tested_2024=n['tested']) for n in needed],
            caveat_html=("<b>How much to trust these predictions.</b> They come from wiring plus a simple neuron model. On known results this brain matched "
                         "10 of 15 checks, and the original study's predictions held up in 91% of 164 living-fly tests, but its misses were exactly the kind "
                         "of single-neuron question this screen asks. Treat each line as a well-founded hypothesis, not a fact. \"No test known to us\" means "
                         "we didn't find one; it doesn't mean no one ever tested it."))
os.makedirs(f'{SK}/discover/runs', exist_ok=True)
json.dump(data, open(f'{SK}/discover/screen.json', 'w'), ensure_ascii=False)
json.dump(P, open(f'{SK}/discover/screen_preregistration.json', 'w'), indent=1)
# compact runs: positions-file row numbers and times x10
n_runs = 0
for f in glob.glob(f'{ST}/*.json'):
    r = json.load(open(f))
    fs = sorted(((ix[int(k)], int(round(t * 10))) for k, t in r['first_spike'].items() if int(k) in ix), key=lambda x: x[1])
    ss = [[ix[int(a)], ix[int(b)], int(round(t * 10))] for a, b, t in r['streaks'] if int(a) in ix and int(b) in ix]
    json.dump(dict(f=fs, s=ss, mn9=[None if t is None else int(round(t * 10)) for t in r['mn9_first']]),
              open(f"{SK}/discover/runs/{os.path.basename(f)}", 'w'), separators=(',', ':'))
    n_runs += 1
print('neurons', len(neurons), 'needed', len(needed), 'untested needed', sum(1 for n in needed if not n['tested']), 'runs', n_runs)
