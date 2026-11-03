# Metaverse Fly Lab

A brand-new 3D lab for the validated connectome flies: **Maxime** (female,
BANC) and **Hagrid** (male, Male CNS) live together in a glass fly jar on the
bench. Positions, headings and firing rates stream live from the fly-lab
server over its WebSocket protocol; with no server it wanders ambiently so
the scene is never frozen. Desktop orbit + VR via WebXR.

No build step. Three.js r160 is vendored (`vendor/`), so the page is
self-contained apart from the live data feed.

## Run it

In one terminal, the fly lab (from the Fly Brain folder):

```bash
python3 server.py
```

In another, serve this folder (any free port; the page finds the lab's
WebSocket on its own):

```bash
cd metaverse-lab
python3 -m http.server 8123
```

Then open http://localhost:8123/lab.html in a browser. Drag to orbit,
scroll to zoom. On a headset, press VR.

## Fly Study (Ask bench + brains rail)

`study.html` (+ `study.css`, `study.js`) is the screen-first build: the
Ask the flies bench (question box, example questions, run button, cards,
results, follow-up thread) with the Maxime/Hagrid brain tabs on one
shared 3D stage in the right rail and live mini stats below. Same
servers as above, then open http://localhost:8123/study.html (serve
over http — modules don't load from file://). Ask anything testable;
`?q=` prefills a question. Requires the lab on ws://localhost:8765 for
live runs and replays. The page holds one socket for everything; runs
survive navigation (a finished-while-away run renders its record on
return). Every number is mean ± wobble with runs visible; verdicts come
from the lab's own rule. (The old nine-bench/tour build lives in git
history and the pre-strip GitHub push.)

Figures are generated offline (same engine, headless). Copy `compute/`
into Fly Brain, then:

```bash
python3 -m compute.figures all --out metaverse-lab/fig
python3 check_figures.py --out metaverse-lab/fig   # referee: existence + label blocks
```

A genuine figure set ships in `fig/` (check each label line for its
commit/seed/params); regenerate after any sim change with the command
printed under each figure. The brain-swap section reads the shipped
`cross_results.json` (genuine 3×400); regenerate with `run_cross.py` (see
`../fly-swap/run_cross.py`). Trials/experiments can record spikes +
group windows once patch `003-recorder` is applied (`rec_window` arg).
Shipped `rec/rec-*.json` recordings carry per-repeat seeds; live repeats
need patch `004-seed-runs` on the server (without it the footer says so).

## Experiments

The left jar is the CONTROL (never dosed); the right jar is the VARIABLE.
The Experiment panel acts on the variable jar only: pick a drug and amount,
Dose, then Run trial. Results compare every fly control-vs-variable
(activity, firing, bananas). Washout clears drugs; Restore resets the
variable flies.

## Files

- `lab.html` — the whole lab: room, bench, jar, flies, live link, HUD, VR.
- `vendor/three/` — three.js r160 + OrbitControls + VRButton (pinned local).
