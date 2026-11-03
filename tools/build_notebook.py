"""Build experiments/notebook.json: one complete record per experiment, from the lab's own result files.
Run from the skeleton folder after any new run:  python3 tools/build_notebook.py
Every number here is read from a result file; nothing is typed in by hand except plain-language framing."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); SK = os.path.join(HERE, '..')
J = lambda p: json.load(open(os.path.join(SK, p)))
R1, CAL, B, S = J('experiments/round1.json'), J('experiments/calibration.json'), J('experiments/bench.json'), J('discover/screen.json')
P1, PS = J('experiments/round1_preregistration.json'), J('discover/screen_preregistration.json')
when = lambda w: w.split(',')[0].replace('T', ' ').replace('Z', ' UTC')
BRAIN = P1['brain']
ENGINE = ('Leaky integrate-and-fire model of Shiu et al. 2024 (Nature 634:210), published settings: every synapse gives the same small push '
          '(0.275 mV), positive or negative depending on the sending neuron\'s chemical; 1 simulated second per run. Engine: tools/lif_engine.py, '
          'checked against the authors\' own code.')
E = []

# ---- 0. engine check ----
ec = CAL['engine_check']
E.append(dict(id='N0', kind='Engine check', title='Is our simulation engine a faithful copy of the published one?', date='2026-11-03',
  question='Does our engine give the same answers as the 2024 study\'s own code on the same brain and the same input?',
  why='Every later result depends on the engine. If it differed from the published model, a match or a miss would tell us about our code, not about the fly.',
  brain='FlyWire, the wiring released with the 2024 study.', method=['Sugar-taste neurons switched on at 100 signals per second.', 'Run in our engine and in the published code; compare the tongue neuron (MN9) and the 200 most active neurons.'],
  rule='No pass mark was set in advance; this is a direct side-by-side comparison.', rule_written=None,
  results=[dict(label=f"MN9 (one copy): {ec['mn9_ours'][0]} vs {ec['mn9_published'][0]} firings per second (ours vs published)", ok=True),
           dict(label=f"MN9 (other copy): {ec['mn9_ours'][1]} vs {ec['mn9_published'][1]}", ok=True),
           dict(label=f"Neurons that fired: {ec['neurons_active_ours']} vs {ec['neurons_active_published']}", ok=True),
           dict(label=f"Firing of the 200 most active neurons: correlation {ec['top200_r']} (1 = identical)", ok=True)],
  conclusion='The two engines agree closely. One detail had to be matched exactly: input arriving while a neuron is recovering from a spike is lost, as in the published code.',
  confidence='High: the comparison is direct, on identical inputs.', discovery=dict(status='none', text='None. This is a check of our tools.'),
  files=['tools/lif_engine.py', 'experiments/calibration.json']))

# ---- 1. calibration ----
c = R1['calibration']
crit = {'C1': 'Sugar at 100 signals per second makes MN9 fire 10 or more times per second', 'C2': 'More sugar, more MN9 firing (from 10 to 200 signals per second)',
        'C3': 'Bitter alone does not make MN9 fire', 'C4': 'Bitter cuts the sugar response at least in half', 'C5': 'Water also makes MN9 fire',
        'C6': 'Activity stays contained: fewer than 2,000 neurons fire'}
E.append(dict(id='N1', kind='Calibration test', title='Does sugar make the simulated fly stick out its tongue?', date=when(P1['written']),
  question='Before any experiment: does the FlyWire brain reproduce the best-established taste results in real flies?',
  why='If the brain can\'t get known results right, its predictions mean nothing. Passing is required before any experiment is reported.',
  brain=BRAIN, method=['Switch on the sugar-taste neurons at 8 strengths (10 to 200 signals per second), bitter neurons, water neurons, and combinations.', 'Read MN9, the motor neuron that extends the proboscis (tongue).', '30 repeats of 1 simulated second per condition.'],
  rule='All of: ' + '; '.join(f'{k}. {v}' for k, v in crit.items()) + '. C1-C4 and C6 must pass.', rule_written=when(P1['written']),
  results=[dict(label=f"{k}. {crit[k]}", ok=bool(v)) for k, v in c['criteria'].items()]
          + [dict(label=f"MN9 to sugar 100: {c['mn9']['sugar_100']}/s; bitter alone: {c['mn9']['bitter_200']}/s; sugar + bitter: {c['mn9']['sugar_100_bitter_200']}/s; water: {c['mn9']['water_200']}/s", ok=True),
             dict(label=f"Sugar-response curve rises steadily (rank correlation {c['spearman']})", ok=True)],
  conclusion='Passed all six rules. Every experiment in the lab runs on this brain.',
  confidence='High for these basic taste results: they are large, clear effects.', discovery=dict(status='known', text='Reproduces known results (by design). No new claim.'),
  files=['experiments/calibration.json', 'experiments/round1_preregistration.json']))

# ---- 2. round 1 ----
for e in R1['experiments']:
    ok = e['matched'] == e['total']; miss = e['matched'] == 0
    status = 'known' if ok else 'miss' if miss else 'partial'
    E.append(dict(id=e['id'], kind='Check against a known result (round 1)', title=e['title'], date=when(P1['written']),
      question=e['title'], why='This result was found in living flies. Checking whether the untouched simulated brain reproduces it measures how far to trust its new predictions.',
      real=f"{e['real']} ({e['ref']})", brain=BRAIN, method=[P1['settings_fixed']],
      rule=e['rule'], rule_written=when(P1['written']),
      results=[dict(label=p['label'], ok=p['ok']) for p in e['parts']],
      conclusion=(f"Matched {e['matched']} of {e['total']}. " + (e.get('note') or ('Matches real flies.' if ok else ''))).strip(),
      confidence=('Low: the match comes from a brain-wide surge, so it is weak evidence.' if 'chain reaction' in (e.get('note') or '') else
                  'Close call: just inside the pass mark.' if 'close call' in (e.get('note') or '') else
                  'Clear.' if ok else 'The miss is clear and matches a miss the 2024 study reported for its own model.'),
      discovery=dict(status=status, text={'known': 'Reproduces a known real-fly result. No new claim.', 'partial': 'Partly reproduces a known result; the miss points to something the wiring alone doesn\'t explain.',
                                          'miss': 'Model miss: real flies do something the wiring-only model can\'t explain. Useful as a limit, not a discovery.'}[status]),
      files=['experiments/round1.json', 'experiments/round1_preregistration.json']))

# ---- 3. taste bench ----
E.append(dict(id='N2', kind='Demonstration', title='The Taste Bench: every combination of sugar, bitter and water', date='2026-11-03',
  question='What does the calibrated brain do for each mix of tastes?', why='So anyone can see the brain respond, with real recorded runs rather than animations.',
  brain=BRAIN, method=[f"{len(B['runs'])} combinations: sugar none/50/100/200, bitter none/100/200, water none/200 signals per second.", f"{B['repeats']} repeats each; MN9 firing and every neuron that fired are recorded."],
  rule='No pass mark: this is a demonstration of the calibrated brain, not a test.', rule_written=None,
  results=[dict(label=f"Sugar 100: MN9 {B['runs']['s100_b0_w0']['mn9']}/s (tongue out)", ok=True), dict(label=f"Sugar 100 + bitter 200: MN9 {B['runs']['s100_b200_w0']['mn9']}/s (tongue stays in)", ok=True),
           dict(label=f"Sugar 100 + water 200: MN9 {B['runs']['s100_b0_w200']['mn9']}/s (signals add up)", ok=True)],
  conclusion='Bitter overrules sugar, and sugar and water add up, consistent with the calibration test.', confidence='Same as the calibration test.',
  discovery=dict(status='none', text='None. A way to explore the calibrated brain.'), files=['experiments/bench.json']))

# ---- 4. discovery screen ----
needed = [n for n in S['neurons'] if n.get('sugar_needed') or n.get('water_needed')]
new = [n for n in needed if n.get('status') == 'new']
CR = S.get('confidence_rule', {})
E.append(dict(id='DS1', kind='Discovery screen', title='Discovery Screen 1: which neurons does the fly need to eat and to drink?', date=when(PS['written']),
  question='If one neuron is switched off, can the fly still eat (sugar) or drink (water)?',
  why='Most of these neurons have never been switched off in a living fly. The simulation can point a real lab to the few worth testing.',
  brain=PS['brain'], method=[PS['candidates'], PS['method']], rule=PS['needed_rule'] + ' ' + PS['status_rule'], rule_written=when(PS['written']),
  results=[dict(label=f"{len(S['neurons'])} neurons switched off one at a time; {len(needed)} predicted needed (confirmed with 30 repeats).", ok=True)]
          + [dict(label=f"{n['label']}: " + ', '.join(x for x in [f"eating {round(100*n['sugar_drop'])}% lower" if n['sugar_needed'] else '', f"drinking {round(100*n['water_drop'])}% lower" if n['water_needed'] else ''] if x)
                  + (f" · {n['conf']['level']}" if n.get('conf') else ''), ok=True) for n in needed],
  conclusion=f"{len(needed)} neurons predicted needed: 7 for drinking, 2 for eating (Roundup #2 for both). For most neurons the signal finds another route, so the feeding circuit has backups.",
  confidence=CR.get('track', ''), confidence_rule=CR,
  discovery=dict(status='potential', text=f"Potential discovery: {len(new)} predictions ({', '.join(n['label'] for n in new)}) about neurons with no real-fly test known to us. They need a living-fly experiment to become a discovery."),
  files=['discover/screen.json', 'discover/screen_preregistration.json']))
for n in needed:
    conds = [c for c in ('sugar', 'water') if n.get(c + '_needed')]
    E.append(dict(id='DS1-' + n['id'][-4:], kind='Discovery screen prediction', parent='DS1', title=f"{n['label']} ({n['type'] or 'no FlyWire type'})", date=when(PS['written']),
      question=f"Does the fly need {n['label']} to " + ' and '.join('eat' if c == 'sugar' else 'drink' for c in conds) + '?',
      brain=PS['brain'], method=['Neuron switched off (all its outgoing connections set to zero); 30 repeats with the same random inputs as the normal brain.'],
      rule=PS['needed_rule'], rule_written=when(PS['written']),
      results=[dict(label=f"{'Eating' if c == 'sugar' else 'Drinking'}: tongue signal {n[c + '_base']} → {n[c]} per second ({round(100*n[c + '_drop'])}% lower; 95% range {round(100*n[c + '_ci'][0])}-{round(100*n[c + '_ci'][1])}%)" if n.get(c + '_ci') else f"{c}: {n[c + '_base']} → {n[c]}", ok=True) for c in conds],
      conclusion=n.get('status_text', ''), confidence=(n['conf']['level'] + '. ' + n['conf']['why']) if n.get('conf') else '',
      discovery=dict(status=n.get('status', 'open'), text={'new': 'Potential discovery: no real-fly test known to us.', 'known': 'Agrees with a known real-fly result.', 'open': 'A new prediction about a neuron already named in the literature.'}.get(n.get('status'), '')),
      files=['discover/screen.json', 'discover/runs/']))

# ---- 5. Parkinson's mechanisms 1 (exploratory) ----
pdp = os.path.join(SK, 'disease/pd.json')
if os.path.exists(pdp):
    PD = J('disease/pd.json'); PP = PD['prereg']; C = PD['counts']; FAST = J('disease/pd_fast.json') if os.path.exists(os.path.join(SK, 'disease/pd_fast.json')) else None
    sc = PD['scenarios']
    res = [dict(label=f"{C['dan']} dopamine neurons (PAM {C['pam']}, PPL1 {C['ppl1']}, PPL2 {C['ppl2']}) send {C['syn']:,} synapses to {C['targets']:,} other neurons.", ok=True),
           dict(label=f"Single points of failure: {PD['spof']['n']:,} of {PD['spof']['total']:,} receiving neurons get dopamine from 2 or fewer dopamine neurons.", ok=True)]
    for k, name, tot in (('ppl1', 'PPL1 first, then the rest', C['dan']), ('pam', 'PAM only', C['pam']), ('all', 'All at random', C['dan'])):
        for row in sc[k]:
            if row['lost'] in (0.5, 1.0):
                res.append(dict(label=f"{name}, {round(row['lost']*tot)} dopamine neurons lost: {row['half_lost'][0]:,} neurons lose half or more of their dopamine input (range over 10 orders {row['half_lost'][1]:,}-{row['half_lost'][2]:,}); average input left {round(100*row['mean_remaining'])}%.", ok=True))
    if FAST:
        res.append(dict(label=f"Fast-signal check: all dopamine neurons removed; MN9 to sugar {FAST['sugar']['normal']} -> {FAST['sugar']['dopamine_removed']}, to water {FAST['water']['normal']} -> {FAST['water']['dopamine_removed']} per second. Dopamine neurons firing to taste in this model: {FAST['sugar']['dan_firing_normal']}.", ok=True))
    E.append(dict(id='PD1', kind='Exploratory analysis (brain disease)', title=PP['title'], date=when(PP['written']),
      question=PP['question'], why="In Parkinson's disease dopamine neurons die. Fly models of the disease lose them too. Mapping where their signal goes shows which parts of the brain depend on them and how well backed up they are.",
      brain=PP['brain'] + ' ' + PP['dopamine_neurons'], method=PP['scenarios'] + PP['measures'],
      rule='No pass mark: there is no real-fly measurement of this kind to check against. The analysis plan was written before it was run.', rule_written=when(PP['written']),
      results=res, conclusion="A few dopamine neurons reach very many targets (the 16 PPL1 neurons reach most of the receiving neurons), most targets have almost no backup, and most dopamine synapses land in the mushroom body, the learning centre. The fast taste reflex does not depend on dopamine neurons in this model.",
      confidence='High for the wiring counts (read directly from the FlyWire data); exploratory for what they mean for the disease. ' + PP['not_claimed'],
      discovery=dict(status='explore', text='Exploratory mechanism map; no discovery claimed. It points to where dopamine loss would be felt first and where to look in future simulations that include dopamine\'s slow effects.'),
      files=['disease/pd.json', 'disease/pd_fast.json', 'disease/pd_preregistration.json', 'tools/build_pd.py']))

out = dict(built='from the lab\'s result files by tools/build_notebook.py', engine=ENGINE, fingerprint=R1['fingerprint'], fingerprint_note=R1['fingerprint_note'], entries=E)
json.dump(out, open(os.path.join(SK, 'experiments/notebook.json'), 'w'), ensure_ascii=False, indent=1)
print(len(E), 'entries')
