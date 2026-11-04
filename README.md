# The Virtual Neuro Lab

Experiments on a simulated fruit-fly brain, wired neuron by neuron from a real electron-microscope scan (FlyWire v783),
running the published brain model of Shiu et al. 2024 (*Nature* 634:210) with its published settings. Every pass mark is
written down before the run, nothing is tuned, and misses stay on the page. Built for the Meta (Muse) hackathon, November 2026.

**Pages:** Home · Neuron Silencing Screen (switch off one neuron, watch the signal; Discovery Screen predictions with confidence levels) ·
Vivarium (Fly: a micro-CT-scanned body run by the FlyWire brain; mix tastes or touch her antennae, watch her feed and groom, see which brain regions respond; Round 1)
· Calibration test and the **Lab notebook** (a full record of every experiment) · Fly Atlas · Prediction check · The worm (*C. elegans*, all 302 neurons) · Parkinson's (where the dopamine signal is lost as dopamine neurons die; exploratory) · What's next.
Ask Muse (Meta's AI) answers questions about the lab, with sources. Each page has a guided tour.

`old-version/` holds the earlier build of the lab from 2 November 2026, kept for reference.

---

## About this build

The current lab. (It started as the reference layer of the earlier build and grew the experiments back on top.)

## Run it

Double-click `start_skeleton.command`. It serves this folder on http://localhost:8200 (through `tools/server.py`, which also
runs the Ask Muse panel) and opens your browser. Close the Terminal window to stop it. For Muse, put `META_API_KEY=...`
in a `.env` file in this folder (or in `Fly Brain/.env`).

(Or from Terminal: `cd` into this folder, then `python3 -m http.server 8200` and open
http://localhost:8200.) The pages must be opened through the server, not by double-clicking
the .html files.

## What's inside

| Folder | Page | Built from |
|---|---|---|
| `index.html` | Home | — |
| `discover/` | Neuron Silencing Screen — switch off a neuron, watch the signal; Discovery Screen predictions | `tools/run_screen.py`, `run_confirm.py`, `run_streaks.py`, `build_screen_json.py` |
| `experiments/` | Data for the Vivarium (Taste Bench runs, Round 1) and the calibration test page; `experiments/index.html` forwards to the Vivarium | `tools/run_flywire_round1.py`, `run_bench.py`, `run_calibration.py` |
| `lab_index.json` | what Ask Muse can search | `tools/build_lab_index.py` |
| `flies/` | Vivarium — Fly: body from NeuroMechFly (micro-CT scan of a real fly), brain-region activity and two behaviours read from the brain (feeding: MN9; antennal grooming: aBN1) | NeuroMechFly (Lobato-Rios et al. 2022, flygym, Apache-2.0; licence in `flies/body/`), Taste Bench and Round 1 runs; `tools/export_fly_body.py`, `tools/build_behaviour.py` |
| `library/` | Fly Atlas — 54 brain and nerve-cord regions in 13 families, 236 cell types, per-fly counts | FlyWire v783 (pictures, cell types), BANC and male CNS (counts) |
| `experiments/notebook.html` | Lab notebook: every experiment's question, method, pass mark, results, confidence and discovery status | `tools/build_notebook.py` |
| `worm/` | The worm — *C. elegans*, 302 neurons in 3D with the Cook et al. 2019 wiring | OpenWorm c302 (Virtual Worm shapes; MIT licence) |
| `disease/` | Parkinson's mechanisms 1 — where the dopamine signal is lost as dopamine neurons die (exploratory) | `tools/build_pd.py`, `tools/run_pd_fast.py` |
| `next/` | What's next — predictions waiting for a real-fly test, work in progress, plans | `discover/screen.json` |
| `prediction/` | Prediction check — how closely the lab's earlier wiring-only position guesses matched each fly's real anatomy | `library/prediction_vs_real.json` |
| `anatomy/celltypes/` | data the Fly Atlas reads (cell-type positions, skeletons, edges) | FlyWire v783 |
| `vendor/` | three.js r160 and fonts, pinned locally | — |
| `feather.css`, `feather.js` | shared look and top bar | — |
| `tools/` | the Python scripts that rebuild every data file above (each explains its inputs at the top) | — |

Copied from `metaverse-lab/` on 2026-11-02, with the experiment, study, ask and account parts
removed. Since then the Prediction check page was added, and on 2026-11-03 the Vivarium's two flies
(Maxime and Hagrid, not ready for experiments) were replaced by one fly whose brain is FlyWire; the old
Vivarium is kept in `old-version/flies-maxime-hagrid/`. The Fly Atlas and Prediction check still use their scans.

## Next step

Docking (does a molecule fit a target such as the fly's dopamine pump?), with its own calibration test first. See `next/`.
