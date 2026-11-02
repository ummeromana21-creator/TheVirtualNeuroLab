# Fly anatomy datasets

Gene catalog, coarse expression maps, and drug-target bridges for Maxime and
Hagrid — built from the held databases, not hand-written. Every row keeps its
source so the pages can cite it.

## Sources (read in place, never copied)

- `~/Desktop/Databases/fb_synonym_fb_2026_03.tsv` — FlyBase symbol/synonym map
- `~/Desktop/Databases/alliance/` — genes, orthology, disease (FB), expression
- `~/Desktop/Databases/ctd/CTD_chem_gene_ixns.csv` — chemical–gene rows
- `~/Desktop/Databases/gtopdb/` — ligand actions + target map
- `../ask/knowledge.json` — the lab's substance list (what to bridge)

## Outputs (built, committed)

- `genes.json` — fly genes: symbol, synonyms, human orthologs, disease links,
  chemicals, expression sites. Slim by design (see sizes in check.py).
- `drug_targets.json` — substance → mammalian targets → fly orthologs →
  expression sites, each leg cited.

## Rebuild

```bash
cd metaverse-lab/anatomy && python3 build.py && python3 check.py
```

Builds stream the big files; nothing is extracted. Disk stays untouched
apart from the two JSON outputs.

## Cell-type positions (embedded atlas viewer)

The 236 atlas cell types with real FlyWire positions, viewed inline in the
atlas detail view (`library/#/Mi1`) — there is no separate page.

```bash
cd metaverse-lab/anatomy && python3 build_celltypes.py \
  && python3 update_atlas_cards.py && python3 check_celltypes.py
```

Sources (read in place, never modified): `maxime_v783.npz` (type, side,
transmitter per neuron, cache order) and `coordinates.csv.gz` (one recorded
Codex point per neuron, nm). Outputs, all under `anatomy/celltypes/`:
`positions.bin` (Float32, µm, centred, no scaling — the orthographic scale
bar depends on it), `sides.bin` (0 unknown/central, 1 left, 2 right),
`rootids.bin` (click → Codex link), `types.json`, `stills/<type>.png`.

Assumptions, all verified in the build or the referee: coordinates.csv.gz
holds several rows per root; the recorded point is the FIRST row per root
(same rule as `flywire_brain.py`, reproduces the npz xyz exactly).
Export axes from the data: x left–right (left low), y dorsal–ventral
(dorsal low), z anterior–posterior (anterior low); front view = the fly
faces you, dorsal up. Transmitter shares are of predicted neurons; "mixed
— flagged" when no class exceeds 60%. BANC and Male CNS have no positions
and are never shown here. Licence wording is a placeholder until the
FlyWire text is pasted in.
