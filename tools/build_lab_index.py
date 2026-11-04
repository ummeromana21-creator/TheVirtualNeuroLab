"""Build lab_index.json: everything the lab knows, as short searchable entries for the Ask Muse panel.
Each entry: id, title, page (link inside the lab), text. Run from the skeleton folder after any data changes:
    python3 tools/build_lab_index.py
"""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); SK = os.path.join(HERE, '..')
J = lambda p: json.load(open(os.path.join(SK, p)))
E = []
def add(title, page, text): E.append(dict(id=f'L{len(E)+1}', title=title, page=page, text=' '.join(re.sub(r'<[^>]+>', ' ', str(text)).split())))

add('What this lab is', 'index.html',
    'The Virtual Neuro Lab runs experiments on simulated fruit fly (Drosophila) nervous systems wired from real connectome '
    'scans. Pages: Neuron Silencing Screen (switch off one neuron; Discovery Screen predictions with confidence levels), Parkinson\'s (where the dopamine '
    'signal is lost as dopamine neurons die), Vivarium (Fly: a body from a micro-CT scan, NeuroMechFly, run by the FlyWire brain; mix tastes or touch her antennae to see feeding and antennal grooming and which brain regions respond; plus Round 1, the calibration test and the lab notebook), '
    'Fly Atlas (brain regions and cell types; the Prediction check is linked from it), The worm (C. elegans, 302 neurons), What\'s next (the plan: docking is the next step). '
    'The lab is a hypothesis generator on the road to drug discovery. Experiments run on the FlyWire brain (female, 139,255 neurons, v783) using the published leaky integrate-and-fire model of '
    'Shiu et al. 2024 (Nature 634:210) with its published settings; rules for passing are saved before every run.')
add('MN9 (tongue motor neuron)', 'flies/', 'MN9 is the motor neuron that extends the fly\'s proboscis (its tongue) to feed or drink. The lab reads MN9 firing as "tongue out" when it fires 10 or more times per second. There are two MN9s, one per side. Gordon & Scott 2009 (Neuron 61:373) showed it drives proboscis extension.')
add('Usnea, Phantom, Fudog, Bract, Roundup, G2N-1 (named feeding neurons)', 'flies/#r1', "Named neurons in the fly's gnathal ganglion (the feeding centre under the brain) studied by Shiu et al. 2024 and earlier work. Usnea responds to water; Fudog responds to water; Bract and Roundup are needed for drinking; G2N-1 is not; Usnea and Phantom can drive proboscis extension when switched on.")
add('Calibration test', 'experiments/calibration.html', 'Before any experiment, the simulated brain must reproduce a known result: sugar taste makes MN9 fire, more sugar more firing, bitter alone does not, bitter cancels sugar, water works, and activity stays contained. The FlyWire brain passed all six rules, so every experiment runs on it. Experiments on Maxime and Hagrid are in progress.')
add('Pre-registration (rules saved before the run)', 'flies/', 'For every test the lab saves the question, the real-fly result, and the pass/fail rule with a timestamp before running. Nothing is changed after the run, and misses stay on the page. A fingerprint code on each card changes if the engine, wiring or rules are edited.')
add('The simulation model (leaky integrate-and-fire)', 'experiments/calibration.html', "Each neuron adds up pushes from the neurons wired to it; when its voltage crosses a threshold it fires and resets. Every synapse gives the same small push (0.275 mV), positive or negative depending on the sending neuron's chemical (GABA and glutamate inhibit). Published by Shiu et al. 2024 (Nature 634:210); in that study 91% of 164 predictions tested in living flies held up. Limits: no graded (non-spiking) neurons, no neuromodulators, no body.")
add('Connectome, FlyWire, BANC, male CNS', 'flies/', "A connectome is a map of every neuron and synapse, traced from electron-microscope scans. FlyWire (female brain, 139,255 neurons) is the brain the experiments run on. BANC (Maxime, female brain and nerve cord) and the male CNS (Hagrid, male brain and nerve cord) are the lab's two flies.")
fi = J('library/points/flies_index.json')
bh = J('flies/behaviour.json')
add('Vivarium: Fly and her behaviours', 'flies/', "The Vivarium shows Fly, the lab's fly: a 3D body from NeuroMechFly (Lobato-Rios et al. 2022, Nature Methods), reconstructed from a micro-CT scan of a real fruit fly, "
    "run by the FlyWire brain. Choose a stimulus and see which brain regions respond and what she does. Only two behaviours are shown, because only their control neurons are read out and checked against real flies: "
    "feeding (tongue out when MN9 fires 10+ times per second) and antennal grooming (when aBN1 fires 5+ times per second; aBN1 starts antennal grooming in real flies, Hampel et al. 2015). "
    "Walking, escape, flight and courtship song are not modelled yet: walking and flight are coordinated in the nerve cord, which FlyWire does not include; escape needs visual input not yet tested; only males sing and FlyWire is female. "
    "The movements are animations of the behaviour the brain's output calls for; the body is not simulated. Results per stimulus: " +
    '; '.join(f"{s['label']}: MN9 {s['mn9']}/s, aBN1 {s['abn1']}/s, {s['active']} neurons fired, top regions " + ', '.join(f"{r['code']} {r['active']}" for r in s['regions'][:4]) for s in bh['stimuli']))
for r in J('library/data.json'):
    t = f"{r['name']} {r.get('full','')}: {r.get('func','')}. {r.get('desc','')} Counts: Maxime {r.get('maxime')}, Hagrid {r.get('hagrid')}."
    add(f"Region {r['name']} ({r.get('full','')})", f"library/#/{r['name']}", t)
for c in J('library/celltypes.json'):
    add(f"Cell type {c['name']}", f"library/#/{c['name']}", c.get('desc', ''))
pv = J('library/prediction_vs_real.json')
for fly in ('maxime', 'hagrid'):
    b = pv[fly]['brain']
    add(f'Prediction check: {fly}', 'prediction/', f"The lab's earlier wiring-only guess of where {fly}'s neurons sit overlapped the real brain shape "
        f"{b['shape_resemblance_pct']}% (Dice); median miss {b['median_distance_um']} micrometres vs {b['baseline_median_um']} at a random spot.")
cal = J('experiments/calibration.json')
add('Engine check', 'experiments/calibration.html', cal.get('engine_check_html', ''))
r1 = J('experiments/round1.json')
c1 = r1['calibration']
add('FlyWire calibration', 'flies/', f"FlyWire v783 passed calibration: rules {c1['criteria']}; MN9 to sugar 100/s {c1['mn9']['sugar_100']}/s; "
    f"neurons fired {c1['active']}. Weak sugar level {c1['weak_sugar']}/s.")
add('Round 1 summary', 'flies/#r1', "Round 1 is an exam on results already known from living flies, not a set of discoveries. The brain was not adjusted to pass: wiring from the scan, settings exactly as published in 2024, and each pass mark written down before the run. The score shows how far to trust the Neuron Silencing Screen's new predictions. " + f"Round 1 matched {r1['totals']['matched']} of {r1['totals']['total']} real-fly results. " + r1.get('note_html', '')
    + ' Selection rule: ' + r1['prereg']['selection_rule'] + ' Rules saved ' + r1['prereg']['written'])
for e in r1['experiments']:
    add(f"Experiment {e['id']}: {e['title']}", 'flies/#r1',
        f"Real flies: {e['real']} ({e['ref']}). Already known from real flies; pass mark written before the run: {e['rule']}. Result {e['matched']}/{e['total']}: "
        + ' | '.join(('MATCH ' if p['ok'] else 'MISS ') + p['label'] for p in e['parts']) + '. ' + e.get('note', ''))
for p in ('experiments/screen.json',):
    if os.path.exists(os.path.join(SK, p)):
        s = J(p)
        add('Discovery Screen summary', 'experiments/discovery.html', s.get('summary', ''))
        for n in s.get('predictions', []):
            add(f"Prediction: {n.get('name')}", 'experiments/discovery.html', json.dumps(n)[:800])
import html as _h
for page, path in (('flies/#infer', 'flies/index.html'), ('discover/#infer', 'discover/index.html')):
    t = open(os.path.join(SK, path)).read()
    i = t.find('id="infer"'); j = t.find('</div>\n    </div>', i)
    if i > 0 and j > 0:
        add('What we infer and why it matters (' + ('Vivarium' if 'flies' in page else 'Neuron Silencing Screen') + ')', page, _h.unescape(t[i:j]))
if os.path.exists(os.path.join(SK, 'worm/worm.json')):
    add('The worm (C. elegans), second organism', 'worm/', "The lab's second organism is the roundworm Caenorhabditis elegans, about 1 mm long, the first animal whose complete wiring diagram was mapped. Every adult hermaphrodite has the same 302 named neurons. The Worm page shows all 302 in 3D with every neuron-to-neuron connection: 2,973 chemical links and 849 pairs joined by electrical links (gap junctions). Neurons are sensory (blue), interneurons (amber), motor (pink) or role unknown. Click a neuron to see who it sends to and receives from. Famous circuits: gentle touch (Chalfie et al. 1985: front touch neurons ALM and AVM feed AVD and AVA, which drive backing up; back touch neurons PLM feed PVC and AVB, which drive forward movement) and the nerve ring hubs (AIB, AIY, AIZ, RIA, RIM, AVA, AVB). Data: neuron shapes from the Virtual Worm 3D model by Grove and Sternberg (WormBase, Caltech, public domain), converted to NeuroML by OpenWorm (c302, MIT licence); the shapes are a hand-built model matched to known anatomy, not traced from one scan. Wiring: Cook et al. 2019, Nature 571:63, as packaged by OpenWorm c302. Experiments on the worm are in progress; they need their own calibration test against real-worm results first.")
if os.path.exists(os.path.join(SK, 'experiments/notebook.json')):
    NB = J('experiments/notebook.json')
    for e in NB['entries']:
        add(f"Lab notebook {e['id']}: {e['title']}", f"experiments/notebook.html#{e['id']}",
            ' '.join(str(x) for x in [e.get('kind'), 'Question:', e.get('question'), 'Why:', e.get('why') or '', 'Known from real flies:', e.get('real') or '', 'Method:', ' '.join(e.get('method') or []),
            'Pass mark:', e.get('rule'), 'written', e.get('rule_written') or 'n/a', 'Results:', ' | '.join(('OK ' if r['ok'] else 'MISS ') + r['label'] for r in e['results']),
            'Conclusion:', e.get('conclusion'), 'How sure:', e.get('confidence'), 'Discovery:', e['discovery']['text']]))
    ds = next((e for e in NB['entries'] if e['id'] == 'DS1'), None)
    if ds and ds.get('confidence_rule'):
        cr = ds['confidence_rule']
        add('How sure are we about predictions (confidence levels)', 'experiments/notebook.html#how-sure',
            f"Each Neuron Silencing Screen prediction was re-run 30 times with paired random inputs; the 95% range of the drop comes from resampling those runs. {cr['sim']} {cr['size']} Levels: {'; '.join(cr['levels'].values())}. Track record: {cr['track']} Rule written {cr['written']}.")
if os.path.exists(os.path.join(SK, 'next/index.html')):
    add("What's next", 'next/', "The What's next page lists: predictions waiting for a real-fly test (the 8 Neuron Silencing Screen predictions with confidence levels; 3 new discovery candidates CB0051, CB0192, CB0501 with no real-fly test known to us), how a fly lab could test one (switch the neuron off genetically, offer water or sugar, count proboscis extensions, compare with controls), work in progress (experiments on Maxime and Hagrid; worm calibration test), planned fly experiments (more behaviours such as grooming, escape, walking and courtship song; switching single neurons on; adding chemical messengers to the model) and candidate organisms (fruit fly larva, Winding et al. 2023 Science; mouse visual cortex, MICrONS 2025 Nature; human cortex fragment, Shapson-Coe et al. 2024 Science).")
if os.path.exists(os.path.join(SK, 'disease/pd.json')):
    PD = J('disease/pd.json'); C = PD['counts']
    add("Parkinson's mechanisms (dopamine neuron loss)", 'disease/', f"The Parkinson's page maps, in the FlyWire brain's wiring, where the dopamine signal goes and what is cut off as dopamine neurons die, as in fly Parkinson's models (Feany and Bender 2000; Whitworth et al. 2005, PPL1 loss; Riemensperger et al. 2013, PAM loss). {C['dan']} dopamine neurons (FlyWire class DAN: PAM {C['pam']}, PPL1 {C['ppl1']}, PPL2 {C['ppl2']}) send {C['syn']} synapses to {C['targets']} neurons; about 69% land in the mushroom body (learning centre). The 16 PPL1 neurons reach {PD['per_cluster']['PPL1']['targets']} neurons; {PD['spof']['n']} of {PD['spof']['total']} receiving neurons get dopamine from 2 or fewer dopamine neurons (little backup). Removing all dopamine neurons did not change the taste reflex in the simulation (no dopamine neurons fire to taste in the model). Exploratory: it maps wiring, not disease chemistry; dopamine's slow effects are not yet simulated. PPM and PAL dopamine clusters are not included (not labelled DAN in FlyWire).")
json.dump(E, open(os.path.join(SK, 'lab_index.json'), 'w'), ensure_ascii=False)
print(len(E), 'entries', os.path.getsize(os.path.join(SK, 'lab_index.json')) // 1024, 'KB')
