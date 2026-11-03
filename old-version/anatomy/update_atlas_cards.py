"""Atlas card wiring for the 236 cell types (run after build_celltypes.py).

Reads anatomy/celltypes/types.json (file counts) and library/celltypes.json.
Writes library/celltypes.json, same single-line compact format, adding:
  aliases  everyday name(s), "" when none exists (single deliberate gap today)
  nt       predicted-transmitter counts from FlyWire v783 (incl. "unknown")
  nt_mixed True when no predicted class exceeds 60% (ties count as mixed)
and rewriting per entry:
  desc     transmitter clause -> full predicted split
  img      -> ../anatomy/celltypes/stills/<name>.png

Sheet counts (fn/fs/...) are untouched: they already equal the file counts.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
TYPES = os.path.join(HERE, "celltypes", "types.json")
SHEET = os.path.join(HERE, "..", "library", "celltypes.json")

OVERRIDES = {
    # User-worded:
    "ORN_V": "CO2 receptor neurons, ab1C, Gr21a/Gr63a",
    "R1-6": "outer photoreceptors",
    "R7": "inner photoreceptor R7",
    "R8": "inner photoreceptor R8",
    "ocellar_retinula_cell": "ocellar photoreceptors, simple eyes",
    "T2a": "lobula relay neurons",
}
# (pattern, alias) in order; ORN/JO handled by function below.
RULES = [
    (r"^L[1-5]$", "lamina relay neurons"),
    (r"^Lai$", "lamina intrinsic neuron"),
    (r"^Lawf", "lamina wide-field neurons"),
    (r"^Mi\d", "medulla relay neurons"),
    (r"^Dm", "distal medulla neurons"),
    (r"^Pm\d", "proximal medulla neurons"),
    (r"^Sm\d", "serpentine medulla neurons"),
    (r"^Tm", "medulla-to-lobula relay neurons"),
    (r"^T[123]$", "lobula relay neurons"),
    (r"^T4", "ON motion detectors"),
    (r"^T5", "OFF motion detectors"),
    (r"^Tlp", "lobula plate relay neurons"),
    (r"^Li\d", "lobula neurons"),
    (r"^LPi", "lobula plate neurons"),
    (r"^(LMa|LMt|MLt|LLPt)", "lobula-medulla connecting neurons"),
    (r"^Y\d", "lobula Y neurons"),
    (r"^C[23]$", "centrifugal feedback neurons, brain to lamina"),
    (r"^(LC|LPC|LPLC|LLPC|cLP|LCe)", "visual projection neurons, lobula to brain"),
    (r"^(MeTu|MTe|aMe)", "medulla to tubercle neurons"),
    (r"^KC", "Kenyon cells, mushroom body memory neurons"),
    (r"^(PFN|FS|vDelta)", "central complex compass neurons"),
    (r"BM_InOm", "eye bristle touch neurons"),
    (r"BM_", "head bristle touch neurons"),
    (r"LB3", "sugar and water taste neurons"),
    (r"(claw_tpGRN|TPMN1)", "taste peg neurons"),
]
BANANA = {"DM2", "DM1", "DM4", "VM2", "DM3", "VA2"}  # flywire_brain.py, Hallem & Carlson 2006


def alias_for(e):
    name = e["name"]
    if name in OVERRIDES:
        return OVERRIDES[name]
    if name.startswith("ORN_"):
        g = name[4:]
        base = ("pheromone receptor neurons" if e.get("sub") == "pheromone"
                else "smell receptor neurons")
        extra = ", fruit odours" if g in BANANA else ""
        return f"{base}, glomerulus {g}{extra}"
    if name.startswith("JO-"):
        return {"JO-A": "Johnston's organ auditory neurons, hearing",
                "JO-B": "Johnston's organ auditory neurons, hearing",
                "JO-E": "Johnston's organ wind and gravity neurons"}.get(
                    name, "Johnston's organ neurons")
    for pat, alias in RULES:
        if re.search(pat, name):
            return alias
    return ""


def nt_clause(nt):
    known = sorted(((k, v) for k, v in nt.items() if k != "unknown"),
                   key=lambda kv: -kv[1])
    tot = sum(v for _, v in known)
    unk = nt.get("unknown", 0)
    if not tot:
        return "transmitters unpredicted."
    parts = [f"{k} {round(100 * v / tot)}%" for k, v in known if 100 * v / tot >= 0.5]
    s = "transmitters " + ", ".join(parts) + " (of predicted"
    if unk:
        s += f"; {round(100 * unk / (tot + unk))}% unpredicted"
    s += ")"
    if len(known) > 1 and known[1][1] == known[0][1]:
        s += "; tie — mixed prediction."
    elif known[0][1] / tot <= 0.60:
        s += "; mixed prediction."
    else:
        s += "."
    return s


def main():
    types = json.load(open(TYPES))
    sheet = json.load(open(SHEET))
    assert len(sheet) == 236, len(sheet)
    empty, bad_desc = [], []
    for e in sheet:
        name = e["name"]
        e["aliases"] = alias_for(e)
        if not e["aliases"]:
            empty.append(name)
        t = types[name]
        assert t["in_file"], name
        e["nt"] = t["nt"]
        known = {k: v for k, v in t["nt"].items() if k != "unknown"}
        tot = sum(known.values())
        e["nt_mixed"] = bool(tot and max(known.values()) / tot <= 0.60)
        head, sep, _tail = e["desc"].partition(" · transmitter")
        if not sep:
            bad_desc.append(name)
            continue
        e["desc"] = head + " · " + nt_clause(t["nt"])
        e["img"] = f"../anatomy/celltypes/stills/{name}.png"
    print("entries without an everyday name:", empty)
    print("descs without a transmitter clause:", bad_desc)
    with open(SHEET, "w") as f:
        f.write(json.dumps(sheet))  # same compact single-line format
    print("wrote", SHEET)


if __name__ == "__main__":
    main()
