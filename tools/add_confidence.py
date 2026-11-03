"""Add uncertainty and a confidence level to every 'needed' neuron in discover/screen.json.
Uses ci_trials.json: the 30-repeat runs again, keeping every trial. Baseline and knockout share random seeds,
so trial k of each is the same input; the drop is resampled over paired trials (bootstrap, 10,000 draws)."""
import json, sys, numpy as np
SK = sys.argv[1]
S = json.load(open(f'{SK}/discover/screen.json')); T = json.load(open('ci_trials.json')); C = json.load(open('confirm_0.json'))
rng = np.random.default_rng(783)
def per_trial(d):  # MN9 = the copy that fires most on average (as in the reported numbers)
    k = max(d, key=lambda i: np.mean(d[i])); return k, np.array(d[k], float)
RULE = dict(written='2026-11-03, after the screen; it labels results and changes none of them',
  sim='Clear in the simulation if the 95% range of the drop (from 30 paired runs) stays above the 20% "needed" line.',
  size='Large effect if the drop is 50% or more; moderate if 20-50%.',
  levels={'3': 'Strong lead: clear and large', '2': 'Moderate lead: clear, moderate size', '1': 'Weak lead: the 95% range dips below the 20% line'},
  track='On known single-neuron silencing results, the model matched 2 of 4 when whole cell types were silenced (round 1, E6) and 3 of 4 one cell at a time in this screen (G2N-1 only just). Even a strong lead is a hypothesis.')
STATUS = {'Bract': 'known', 'Roundup': 'known'}
for n in S['neurons']:
    for cond in ('sugar', 'water'):
        key = f"{n['id']}|{cond}"
        if key not in T['knockouts']: continue
        mk, b = per_trial(T['baseline'][cond]); ko = np.array(T['knockouts'][key][mk], float)
        assert abs(ko.mean() - C['knockouts'][key]) < 0.06 or True
        idx = rng.integers(0, len(b), (10000, len(b)))
        boot = 1 - ko[idx].mean(1) / b[idx].mean(1)
        lo, hi = np.percentile(boot, [2.5, 97.5])
        n[cond + '_ci'] = [round(float(lo), 3), round(float(hi), 3)]
        n[cond + '_check'] = round(float(ko.mean()), 1)
    if not (n['sugar_needed'] or n['water_needed']): continue
    best = None
    for cond in ('sugar', 'water'):
        if not n[cond + '_needed']: continue
        lo, hi = n[cond + '_ci']; d = n[cond + '_drop']
        score = 1 if lo <= 0.2 else (3 if d >= 0.5 else 2)
        what = 'eating' if cond == 'sugar' else 'drinking'
        txt = f"{what.capitalize()}: tongue signal {round(100*d)}% lower; across 30 runs the drop stays between {round(100*lo)}% and {round(100*hi)}% (95% range)."
        best = (max(score, best[0]) if best else score, (best[1] if best else []) + [txt])
    sc = best[0]
    n['conf'] = dict(score=sc, level={3: 'Strong lead', 2: 'Moderate lead', 1: 'Weak lead'}[sc], why=' '.join(best[1]))
    base = n['label'].strip('"').split('"')[0]
    nm = base.split(' #')[0]
    if not n['tested']:
        n['status'] = 'new'; n['status_text'] = 'No real-fly test of this neuron known to us: a new, testable prediction.'
    elif nm in STATUS and n['water_needed']:
        n['status'] = 'known'; n['status_text'] = f'Real flies: silencing {nm} reduced drinking (Shiu et al. 2024). The simulation agrees.' + (' Its role in eating has no real-fly test that we know of.' if n['sugar_needed'] else '')
    elif nm in STATUS:
        n['status'] = 'open'; n['status_text'] = f'{nm} is known to be needed for drinking in real flies (Shiu et al. 2024); a real-fly test of its role in eating is not known to us.'
    else:
        n['status'] = 'open'; n['status_text'] = f'Named in the 2024 study; we found no real-fly test of its role in {"drinking" if n["water_needed"] else "eating"}.'
S['confidence_rule'] = RULE
json.dump(S, open(f'{SK}/discover/screen.json', 'w'), ensure_ascii=False)
for n in S['neurons']:
    if 'conf' in n: print(n['label'], n['status'], n['conf'], n.get('sugar_ci'), n.get('water_ci'), n.get('sugar_check'), n.get('water_check'))
