"""Rebuild the Fly Atlas cell-type cards (library/celltypes.json) from the published FlyWire annotations.

Sources
  FlyWire annotations, v783 (Schlegel et al. 2024 Nature; optic lobe types from Matsliah et al. 2024),
    github.com/flyconnectome/flywire_annotations  supplemental_files/Supplemental_file1_neuron_annotations.tsv
    -> counts, sides, flow/class, and the EXPERIMENTALLY KNOWN transmitter (known_nt) where recorded.
  Codex export (Databases/Flywire), via tools/type_top.json -> each type's top regions by synapse count.
  Function glosses: GLOSS below, written per cell family from the literature (see README).
Usage: python3 tools/build_celltypes.py <annotations.tsv> <type_top.json>
"""
import collections, csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, '..', 'library')
ann_path, top_path = sys.argv[1], sys.argv[2]
old = json.load(open(os.path.join(LIB, 'celltypes.json')))
top = json.load(open(top_path))
by = collections.defaultdict(list)
for r in csv.DictReader(open(ann_path), delimiter='\t'):
    by[r['cell_type']].append(r)

ORN = {  # receptor and best-known ligand, only where well established
    'DA1': 'Or67d; senses the male pheromone cVA', 'DL3': 'Or65a; senses the pheromone cVA',
    'VA1d': 'Or88a; pheromone-sensing', 'VA1v': 'Or47b; pheromone-sensing',
    'V': 'Gr21a/Gr63a; senses carbon dioxide', 'DL4': 'Or49a/Or85f; senses odours of parasitic wasps',
}
GLOSS = [  # (regex, plain name, what it does)
    (r'^R1-6$', 'outer photoreceptors', 'eye cells that sense light with the Rh1 pigment, used for motion and brightness vision; they end in the lamina'),
    (r'^R7$', 'inner photoreceptor R7', 'UV-sensitive eye cells used for colour vision; they end in the medulla'),
    (r'^R8$', 'inner photoreceptor R8', 'blue- or green-sensitive eye cells used for colour vision; they end in the medulla'),
    (r'^ocellar_retinula_cell$', 'ocellus photoreceptors', 'light-sensing cells of the three simple eyes (ocelli) on top of the head, which help keep flight stable'),
    (r'^L1$', 'lamina monopolar neuron L1', 'takes photoreceptor input in the lamina and starts the ON (brightening) pathway that feeds motion detection'),
    (r'^L2$', 'lamina monopolar neuron L2', 'takes photoreceptor input in the lamina and starts the OFF (dimming) pathway that feeds motion detection'),
    (r'^L3$', 'lamina monopolar neuron L3', 'carries brightness signals from the lamina to the medulla, also used in colour and OFF pathways'),
    (r'^L4$', 'lamina monopolar neuron L4', 'links neighbouring lamina cartridges and feeds the OFF pathway'),
    (r'^L5$', 'lamina monopolar neuron L5', 'relays lamina signals into the medulla'),
    (r'^Lawf\d', 'lamina wide-field neuron', 'feedback neuron that spreads across many columns between the medulla and the lamina'),
    (r'^Lai$', 'lamina amacrine cell', 'a local cell inside the lamina'),
    (r'^C[23]$', 'centrifugal neuron', 'carries feedback from the medulla back to the lamina'),
    (r'^T1$', 'T1 neuron', 'connects the lamina and the medulla (it does not reach the lobula); no classic transmitter has been found in it'),
    (r'^T2a?$|^T3$', 'T neuron', 'columnar neuron carrying visual signals from the medulla to the lobula'),
    (r'^T4[a-d]$', 'T4 motion detector', 'ON motion detector: responds to brightening edges moving in one of four directions; runs from the medulla to one layer of the lobula plate'),
    (r'^T5[a-d]$', 'T5 motion detector', 'OFF motion detector: responds to darkening edges moving in one of four directions; runs from the lobula to one layer of the lobula plate'),
    (r'^Mi(1|4|9)$', 'medulla intrinsic neuron', 'local columnar cell inside the medulla and one of the main inputs to the T4 (ON) motion detectors'),
    (r'^Mi\d', 'medulla intrinsic neuron', 'local columnar cell inside the medulla'),
    (r'^Tm(1|2|4|9)$', 'transmedullary neuron', 'carries signals from the medulla to the lobula and is one of the main inputs to the T5 (OFF) motion detectors'),
    (r'^Tm(5[a-c]|20)$', 'transmedullary neuron', 'carries colour signals from photoreceptors R7/R8 onward from the medulla to the lobula'),
    (r'^Tm5[d-f]$', 'transmedullary neuron (Tm5 family)', 'a newer Tm5-family type related to the colour pathway; its photoreceptor inputs are not yet described'),
    (r'^Tm\d', 'transmedullary neuron', 'carries signals from the medulla to the lobula'),
    (r'^TmY', 'TmY neuron', 'carries signals from the medulla to both the lobula and the lobula plate'),
    (r'^Dm8[ab]$', 'distal medulla neuron Dm8', 'collects UV signals from R7 photoreceptors across several columns (colour preference)'),
    (r'^Dm\d', 'distal medulla neuron', 'local cell that spreads across several columns of the outer medulla'),
    (r'^Pm\d', 'proximal medulla neuron', 'local cell that spreads across several columns of the inner medulla'),
    (r'^Sm\d', 'serpentine-layer medulla neuron', 'cell that spreads through the medulla\'s serpentine layer across many columns'),
    (r'^Li\d', 'lobula intrinsic neuron', 'local cell inside the lobula'),
    (r'^LPi\d', 'lobula plate intrinsic neuron', 'local cell linking lobula-plate layers, part of how opposite motion directions are compared'),
    (r'^LC4$', 'lobula columnar neuron LC4', 'detects looming objects and drives escape'),
    (r'^LC11$', 'lobula columnar neuron LC11', 'detects small moving objects'),
    (r'^LC10a$', 'lobula columnar neuron LC10a', 'carries visual signals to the anterior optic tubercle and helps track a moving target such as a female during courtship pursuit'),
    (r'^LC10[b-e]$', 'lobula columnar neuron LC10', 'carries visual signals from the lobula to the anterior optic tubercle'),
    (r'^LC\d|^LCe\d', 'lobula columnar neuron', 'carries one visual feature from the lobula to its own glomerulus in the central brain'),
    (r'^LPLC2$', 'lobula-plate/lobula columnar neuron LPLC2', 'detects looming (an approaching object) and helps trigger escape'),
    (r'^LPLC\d', 'lobula-plate/lobula columnar neuron', 'carries motion-related visual features from the lobula and lobula plate to the central brain'),
    (r'^LLPC\d|^LPC\d', 'lobula plate columnar neuron', 'carries motion signals from the lobula plate to the central brain'),
    (r'^LLPt$', 'lobula/lobula plate tangential neuron', 'spreads across the lobula and lobula plate'),
    (r'^LM[at]\d', 'lobula-medulla neuron', 'connects the lobula and the medulla'),
    (r'^MLt\d', 'medulla-lobula tangential neuron', 'spreads across the medulla and lobula'),
    (r'^Tlp\d', 'Tlp neuron', 'connects the lobula plate and the lobula'),
    (r'^Y\d', 'Y neuron', 'connects the medulla, lobula and lobula plate'),
    (r'^MeTu', 'medulla-tubercle neuron', 'carries visual signals (including colour and polarised light) from the medulla to the anterior optic tubercle'),
    (r'^MTe\d', 'medulla tangential neuron', 'connects the medulla with the central brain; individual roles are mostly unknown'),
    (r'^aMe\d', 'accessory medulla neuron', 'neuron of the accessory medulla, a small optic region where clock neurons branch'),
    (r'^cLP\d', 'centrifugal lobula plate neuron', 'carries signals from the central brain back into the lobula plate'),
    (r'^KCab', 'Kenyon cell (alpha/beta)', 'mushroom-body learning cell of the alpha/beta lobes, important for long-term memory'),
    (r'^KCapbp', "Kenyon cell (alpha'/beta')", "mushroom-body learning cell of the alpha'/beta' lobes, important for forming memories"),
    (r'^KCg-d$', 'Kenyon cell (gamma, dorsal)', 'mushroom-body learning cell of the gamma lobe that receives visual input'),
    (r'^KCg', 'Kenyon cell (gamma)', 'mushroom-body learning cell of the gamma lobe, important for short-term memory'),
    (r'^ORN_', 'olfactory receptor neuron', 'smell neuron in the antenna or palp; all neurons of one type carry the same odour receptor and meet in one antennal-lobe glomerulus'),
    (r'^JO-A$', "Johnston's organ neuron", 'sound- and vibration-sensing neuron in the antenna (tuned to faster vibrations)'),
    (r'^JO-B$', "Johnston's organ neuron", 'sound-sensing neuron in the antenna (e.g. courtship song)'),
    (r'^JO-E$', "Johnston's organ neuron", 'antenna neuron sensing sustained deflections such as wind and gravity'),
    (r'^JO-F', "Johnston's organ neuron", 'antenna mechanosensory neuron of the F group; its role is less well characterised'),
    (r'^BM_', 'bristle mechanosensory neuron', 'touch-sensing neuron of bristles on the head'),
    (r'^LB3$', 'labellar taste neurons (LB3a–d combined)', 'taste neurons of the labellum; the four subtypes sense water, sugar, sugar and low salt, or high salt and heavy metals'),
    (r'^claw_tpGRN$', 'taste-peg taste neuron', 'taste neuron of the taste pegs on the inner labellum'),
    (r'^SA_', 'sensory ascending neuron', 'sensory neuron whose signal enters from the nerve cord and rises through the neck connective to the brain'),
    (r'^TPMN', 'taste-peg mechanosensory neuron', 'touch-sensing neuron of the taste pegs on the inner labellum'),
    (r'^PFN[amp]$', 'PFN neuron (central complex)', 'columnar neuron that combines heading (from the protocerebral bridge) with self-motion (from the noduli) and sends the result to the fan-shaped body'),
    (r'^FS\d', 'FS neuron (central complex)', 'columnar neuron of the fan-shaped body'),
    (r'^vDelta', 'vDelta neuron (central complex)', 'local columnar neuron of the fan-shaped body'),
]
NT_WORDS = ['acetylcholine', 'glutamate', 'gaba', 'histamine', 'dopamine', 'serotonin', 'octopamine', 'tyramine']
PRED = {'ACH': 'acetylcholine', 'GLUT': 'glutamate', 'GABA': 'GABA', 'SER': 'serotonin', 'DA': 'dopamine', 'OCT': 'octopamine'}


def gloss(name):
    for pat, plain, what in GLOSS:
        if re.search(pat, name):
            if name.startswith('ORN_'):
                g = name[4:]
                extra = f' ({ORN[g]})' if g in ORN else ''
                return f'olfactory receptor neuron, glomerulus {g}', what + extra
            return plain, what
    return None, None


CLASSIC = ['acetylcholine', 'glutamate', 'gaba', 'dopamine', 'serotonin', 'octopamine']


def known_nt(rows):
    """-> (text or None, ruled_out list). 'none' only when all classic transmitters were tested negative."""
    vals, neg = collections.Counter(), set()
    for r in rows:
        k = (r['known_nt'] or '').lower()
        if not k:
            continue
        negs = set(re.findall(r'(\w+)-negative', k))
        hit = [w for w in NT_WORDS if re.search(r'\b' + w + r'\b(?!-negative)', k)]
        if hit:
            vals[', '.join(dict.fromkeys(('GABA' if h == 'gaba' else h) for h in hit))] += 1
        elif negs >= set(CLASSIC):
            vals['none'] += 1
        else:
            neg |= negs
    if not vals:
        return None, sorted(neg)
    (best, n), total = vals.most_common(1)[0], sum(vals.values())
    if len(vals) > 1 and n < 0.8 * total:
        return 'mixed: ' + ' / '.join(f'{k} ({v} cell{"s" if v > 1 else ""})' for k, v in vals.most_common(3)) + ' (reported in experiments)', []
    if n < 5:
        return ('none of the classic transmitters' if best == 'none' else best) + f' (reported in experiments, {n} cell{"s" if n > 1 else ""} tested)', []
    return ('none of the classic transmitters (tested in experiments)' if best == 'none'
            else f'{best} (confirmed in experiments)'), []


def predicted(e, rows):
    if rows:
        c = collections.Counter(r['top_nt'] for r in rows if r['top_nt'])
        if c:
            k, n = c.most_common(1)[0]
            k = {'gaba': 'GABA'}.get(k, k)
            return f"{k} (predicted from images, {round(100 * n / sum(c.values()))}% of the cells that have a prediction)"
    nt = {k: v for k, v in (e.get('nt') or {}).items() if k != 'unknown'}
    if nt:
        k = max(nt, key=nt.get)
        return f"{PRED.get(k, k)} (predicted from images, {round(100 * nt[k] / sum(nt.values()))}% of the cells that have a prediction)"
    return 'not known'


def fmt(n):
    return f'{n:,}'


FLOW = {'afferent': 'Sensory: carries signals into the nervous system.',
        'efferent': 'Output: carries signals out to the body.',
        'intrinsic': 'Stays inside the brain (it can still connect several regions).'}
new = []
for e in old:
    name, rows = e['name'], by.get(e['name'], [])
    if name == 'LB3':
        rows = []  # published table splits LB3 into a-d; the card covers all four
    plain, what = gloss(name)
    if rows:
        side = collections.Counter(r['side'] for r in rows)
        n, L, R, C = len(rows), side.get('left', 0), side.get('right', 0), len(rows) - side.get('left', 0) - side.get('right', 0)
        src = 'published FlyWire annotations (v783)'
        flow, cls, sub = rows[0]['flow'], rows[0]['super_class'], rows[0]['cell_class'] or rows[0]['cell_sub_class']
        knt, ruled_out = known_nt(rows)
    else:
        t = top['count'].get(name, e['fn'])
        n, L, R, C, src = t, None, None, None, 'FlyWire Codex export (not in the published annotation table)'
        # left/right not given: the Codex side labels for these types are unreliable
        flow, cls, sub, knt, ruled_out = e.get('flow'), e.get('cls'), e.get('sub'), None, []
    if name in ('R1-6', 'R7', 'R8', 'ocellar_retinula_cell'):
        knt = 'histamine (confirmed in experiments)'
    if name.startswith('ORN_') and not knt:
        knt = 'acetylcholine (confirmed in experiments)'
    tops = [r for r, v in (top['top'].get(name) or []) if r != 'UNASGD']
    tot = sum(v for r, v in (top['top'].get(name) or []))
    tops = [r for r, v in (top['top'].get(name) or []) if r != 'UNASGD' and v >= 0.05 * max(tot, 1)][:3]
    nt_text = knt or predicted(e, rows)
    if not knt and ruled_out:
        nt_text += '; experiments show it is not ' + ' or '.join('GABA' if x == 'gaba' else x for x in ruled_out)
    sides = '' if L is None else f' ({fmt(L)} left, {fmt(R)} right' + (f', {fmt(C)} on the midline or unassigned' if C else '') + ')'
    desc = ' '.join(x for x in [
        f"{name}{' — ' + plain if plain else ''}: {what}." if what else f"{name}: a {cls or 'FlyWire'} cell type; its specific role is not described here yet.",
        f"The FlyWire reference brain has {fmt(n)} of these cells{sides}.",
        f"Most of their synapses are in {', '.join(tops)}." if tops else '',
        f"Transmitter: {nt_text}.",
        (f"(The 3D view shows the {fmt(top['count'][name])} cells that the Codex export labels {name}.)"
         if top['count'].get(name) and abs(top['count'][name] - n) > 0.05 * n else ''),
        FLOW.get(flow, ''),
    ] if x)
    d = dict(e)
    for k in ('mn', 'fe', 'me', 'ms', 'ratio'):
        d.pop(k, None)
    d.update(fn=n, left=L, right=R, flow=flow, cls=cls or e.get('cls'), sub=sub or e.get('sub'),
             top=tops, func=plain or 'cell type', aliases=plain or '', desc=desc, nt_text=nt_text,
             count_source=src)
    if name in ('LB3',):
        d['func'] = 'labellar taste neurons (LB3a–d combined)'
    new.append(d)
json.dump(new, open(os.path.join(LIB, 'celltypes.json'), 'w'), indent=1, ensure_ascii=False)
print(len(new), 'cell types;', sum(1 for x in new if x['count_source'].startswith('published')), 'from published table')
