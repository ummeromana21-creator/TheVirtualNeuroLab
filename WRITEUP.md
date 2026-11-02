# Fly Lab — virtual organisms for pre-testing compounds

## Purpose

The Fly Lab is a discovery tool: a virtual fruit fly on which modelled
chemical compounds can be tested in a realistic anatomical environment before
they are ever given to a real animal or human. Type a question in plain words
— "what does caffeine do to the fly?" — and in about 40 seconds the lab
compiles it into a rigorous experiment, runs it on two whole-brain
simulations (a female brain, "Maxime", and a male brain, "Hagrid", wired from
real connectome data), and returns a pre-registered prediction with a verdict,
a replayable record, and its full methods.

## The problem we're solving

Testing a compound the real way costs weeks and animals per question:
breeding, assays, statistics, recording from tiny brains. So most ideas are
never tested, negative results vanish, and drug pipelines burn billions on
candidates that fail in animal trials — exactly the waste the 3Rs (replace,
reduce, refine animal testing) exist to prevent. What researchers lack is a
fast, honest first pass: a virtual organism that says "this can't reach
behaviour — the anatomy absorbs it at the first relay" before a single animal
is dosed, and tells them which ideas deserve real wet-lab spend.

## How our lab is a solution

Compounds here are probes, not contestants. The point was never "which drug
wins" — it's what each compound reveals about the organism: where its effect
lands, how far it travels through real wiring, where it fades, where the
sexes diverge. A compound that moves its target but not behaviour isn't a
failure; it's a discovery about the anatomy. Every question gets the same
fair trial — both flies, control and treatment boxes, repeats, a second
measure, a fixed verdict rule — and every card now carries its methods
section: receptor maps, dose mapping, every assumption graded, so a real
scientist can recreate the virtual experiment.

What makes the tool trustworthy is calibration, not wins. Seven model checks
run against known fly results; four match and three miss — and the misses
stay on the record with explanations. A discovery tool that never admits
error can't be believed; ours says exactly where it stands.

## Example: DEET, a where-story end to end

**Question.** What does DEET do to the fly — dull the smell receptors,
confuse steering, or both?

**Prediction (written before the run).** DEET quiets the banana-smell
receptors, so treated flies stay farther from bananas.

**Result.** Over 19 pooled runs, nose firing fell 42% in Maxime and 44% in
Hagrid — SUPPORTED, matching published fly work (Ditzen et al. 2008). But
steering stayed inconclusive: the effect fades before reaching the steering
centres. That's the spatial story the lab exists to produce — not "DEET
works", but where it lands and where it dies.

The pipeline already points at genuinely new tests: the caffeine relatives
theophylline and theobromine are predicted to rouse flies, flagged "not yet
tested" — a real fly lab could check them tomorrow.

## Roadmap: closing the gaps

Each known gap is an active build, not a footnote: receptor maps so drugs act
where receptors really are (live for dopamine, adenosine next), glial
modulation for brain-state effects (built), dose calibration against measured
fly dose–response curves, chronic-effect models. Every addition must survive
the same verdict rules as every compound.

## Honest limits

Today the sim compares shapes only (direction, rising or falling, reversible
or not); steps aren't milliseconds, doses aren't milligrams, one mechanism
per drug, acute effects only, fly only. A prediction becomes evidence only
when a real organism agrees. The lab's job is to prioritize the real
experiments — fewer animals, less money, better questions first.
