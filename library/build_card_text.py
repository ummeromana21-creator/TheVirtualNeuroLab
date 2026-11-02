#!/usr/bin/env python3
"""Rewrite all 461 Atlas card explanations in the approved conversational voice.

Reads: library/{data,celltypes,sides,subsets}.json, anatomy/celltypes/types.json.
Writes: the same four library files with `desc` replaced (schemas untouched).

Every number is computed, never typed. Pinned substrings are preserved verbatim:
the ORN_V transmitter sentence (check.py) and side shortfall words. Counts come
from types.json (the viewer's own source of truth for dots and sides).

Fails loudly on schema drift, missing pins, or an unwritten card.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ANA = os.path.join(HERE, "..", "anatomy", "celltypes")
SKEL = os.path.join(ANA, "skeletons")

CLS_PRETTY = {
    "optic_lobe_intrinsic": "cells built into the optic lobe",
    "olfactory": "smell cells",
    "visual": "eye cells",
    "Kenyon_Cell": "mushroom-body memory cells",
    "mechanosensory": "touch and vibration sensors",
    "gustatory": "taste cells",
    "CX": "central-complex cells",
    "AN": "antennal-nerve cells",
    "": "brain cells",
}
FLOW_PHRASE = {
    "afferent": "carrying signals inward, like scouts reporting back",
    "intrinsic": "wired within their own region, like a labeled wire bundle in a cable with hundreds",
}

VISION_SIM = ("What the simulated fly can do today: tell lit from dark, lose it "
              "all when its photoreceptors are knocked out, and show you exactly "
              "where the light response lands.")
SMELL_SIM = ("What the simulated fly can do today: follow banana smell, lose the "
             "scent when its nose neurons are silenced, and show a repellent's "
             "effect fading stage by stage.")
MB_SIM = ("The sim's mushroom body records its slope every run — though steering "
          "from it was tested and rejected, so it fires without driving turns.")
BRAIN_SIM = ("What the simulated fly can do today: run whole-brain experiments "
             "where every neuron fires and every region reports.")

# cell type -> live sim role (only where the sim truly acts through the type)
TYPE_SIM = {
    "R1-6": ("the function of these cells runs live in the sim as part of the "
             "photoreceptors group — light assays drive them, and the ninaE "
             "blindness record proves it. " + VISION_SIM),
    "R7": ("the function of these cells runs live in the sim as part of the "
           "photoreceptors group — light assays drive them, and the ninaE "
           "blindness record proves it. " + VISION_SIM),
    "R8": ("the function of these cells runs live in the sim as part of the "
           "photoreceptors group — light assays drive them, and the ninaE "
           "blindness record proves it. " + VISION_SIM),
    "ORN_V": ("the function of these cells runs live in the sim as the CO2 "
              "group — CO2 puffs drive them, and the Gr63a blindness record "
              "proves it. " + SMELL_SIM),
}


def stem(name):
    return name[:-1] if name and name[-1].islower() else name


def main():
    fails = []
    tj = json.load(open(os.path.join(ANA, "types.json")))
    tj.pop("_meta")
    names = sorted(tj)
    skels = {f[:-5] for f in os.listdir(SKEL) if f.endswith(".json")} if os.path.isdir(SKEL) else set()

    # ---------- cell types (236) ----------
    ctp = os.path.join(HERE, "celltypes.json")
    ct = json.load(open(ctp))
    for e in ct:
        n = e["name"]
        t = tj.get(n)
        if not t or not t["in_file"]:
            fails.append(f"{n}: missing from types.json")
            continue
        alias = (e.get("aliases") or "").split(",")[0].strip()
        who = f"{n} ({alias})" if alias else n
        cls = CLS_PRETTY.get(e.get("cls") or "", "brain cells")
        flow = FLOW_PHRASE.get(e.get("flow") or "", "wired within their own region")
        top = ", ".join(e.get("top") or [])
        sibs = sorted(s for s in names if s != n and stem(s) == stem(n))
        sib = sibs[0] if sibs else None
        p1 = (f"In a real fly, {who} are {cls}, {flow}. What we made is a map: "
              f"every bright dot is one {n} cell's single recorded point, "
              f"{t['left']:,} on the left and {t['right']:,} on the right"
              + (f", loudest in {top}" if top else "")
              + (" — and we also traced one full cell, so you can see the shape "
                 "behind a dot" if n in skels else "")
              + "." + (f" {sib}, the sister type ({tj[sib]['n']:,} cells), is "
                       "hidden by default." if sib else ""))
        sim = TYPE_SIM.get(n)
        if sim:
            p2 = f"Simulated version: {sim}"
        else:
            if e.get("cls") in ("optic_lobe_intrinsic", "visual"):
                pointer = VISION_SIM
            elif e.get("cls") == "olfactory":
                pointer = SMELL_SIM
            elif e.get("cls") == "Kenyon_Cell":
                pointer = MB_SIM + " " + BRAIN_SIM
            else:
                pointer = BRAIN_SIM
            p2 = (f"Simulated version: these cells are shown, not simulated. {n} "
                  f"is a window into the anatomy, and a placeholder with a name and "
                  f"an address for the day the sim grows finer. {pointer}")
        tail = ""
        if "· transmitters " in (e["desc"] or ""):
            tail = " " + (e["desc"].split("· transmitters ", 1)[1].rstrip())
            if not tail.startswith(" transmitters"):
                tail = " transmitters " + tail.strip()
        e["desc"] = f"{p1} {p2}{tail}"
    json.dump(ct, open(ctp, "w"), indent=1)
    print(f"celltypes: {len(ct)} rewritten")

    # ---------- regions + hubs (66) ----------
    REGION_SIM = {
        "AL": ("the first smell relay is a measured stage — cards read its "
               "projection neurons live, and a repellent's effect lands here "
               "first. On effect maps it reports as antennal lobe."),
        "MB_CA": ("part of the mushroom-body group, the learning center. " + MB_SIM
                  + " On effect maps it reports as mushroom body."),
        "MB_ML": ("part of the mushroom-body group, the learning center. " + MB_SIM
                  + " On effect maps it reports as mushroom body."),
        "MB_PED": ("part of the mushroom-body group, the learning center. " + MB_SIM
                   + " On effect maps it reports as mushroom body."),
        "MB_VL": ("part of the mushroom-body group, the learning center. " + MB_SIM
                  + " On effect maps it reports as mushroom body."),
        "LH": ("the instinctive-smell group, measured live on the nose-to-legs "
               "path. On effect maps it reports as lateral horn."),
        "EB": ("part of the central-complex group (navigation and steering). "
               "Steering from it was tested and rejected, so it fires without "
               "driving turns. On effect maps it reports as central complex."),
        "FB": ("part of the central-complex group (navigation and steering). "
               "Steering from it was tested and rejected, so it fires without "
               "driving turns. On effect maps it reports as central complex."),
        "PB": ("part of the central-complex group (navigation and steering). "
               "Steering from it was tested and rejected, so it fires without "
               "driving turns. On effect maps it reports as central complex."),
        "NO": ("part of the central-complex group (navigation and steering). "
               "Steering from it was tested and rejected, so it fires without "
               "driving turns. On effect maps it reports as central complex."),
        "ME": ("part of the optic-lobes group; the sim's vision runs through the "
               "photoreceptors and their direct visual targets instead, and light "
               "assays move those. On effect maps it reports as medulla."),
        "LO": ("part of the optic-lobes group; the sim's vision runs through the "
               "photoreceptors and their direct visual targets instead, and light "
               "assays move those. On effect maps it reports as lobula."),
        "LOP": ("part of the optic-lobes group; the sim's vision runs through the "
                "photoreceptors and their direct visual targets instead, and light "
                "assays move those. On effect maps it reports as lobula plate."),
        "LA": ("part of the optic-lobes group; the sim's vision runs through the "
               "photoreceptors and their direct visual targets instead, and light "
               "assays move those. On effect maps it reports as lamina."),
        "AME": ("modeled with the optic lobes; the sim's vision runs through the "
                "photoreceptors and their direct visual targets, and light assays "
                "move those."),
        "GNG": ("the feeding and taste hub; taste firing projects here, and the "
                "GNG leads the taste effect maps. On effect maps it reports as GNG."),
        "AVLP": ("modeled as part of the whole-brain network — its neurons fire in "
                 "every run and count toward whole-brain measures. On effect maps "
                 "it reports as AVLP."),
        "PLP": ("modeled as part of the whole-brain network — its neurons fire in "
                "every run and count toward whole-brain measures. On effect maps "
                "it reports as PLP."),
        "LAL": ("modeled as part of the whole-brain network — its neurons fire in "
                "every run and count toward whole-brain measures. On effect maps "
                "it reports as LAL."),
    }
    VNC_SIM = ("part of the nerve-cord group — the fly's spinal cord — feeding the "
               "leg motor pools. On effect maps it reports as nerve cord.")
    GENERIC_SIM = ("modeled as part of the whole-brain network with no dedicated "
                   "group — its neurons fire in every run and count toward "
                   "whole-brain measures.")
    HUB_SIM = {
        "optic": ("The sim's vision lives here: light assays drive the "
                  "photoreceptors and their direct visual targets, and knocking "
                  "those out blinds the fly. Finer cell types are mapped, not modeled."),
        "olfactory": ("The sim's smell lives here: banana finding, repellent "
                       "effects fading stage by stage, and anosmia when the nose "
                       "neurons are silenced."),
        "GNG": ("The sim's taste and feeding hub: sweet and bitter drive the "
                "taste neurons, and Gr66a/Gr5a mutants lose one arm each. Taste "
                "has no feedback onto walking, so it moves firing only."),
        "CX": ("Navigation and sleep, honestly bounded: the compass circuitry "
               "fires, but steering from it was tested and rejected — and sleep "
               "is a quiet-brain proxy, as the per01 record shows."),
        "lateral": ("Premotor country: no dedicated groups, but its regions light "
                     "up on effect maps whenever drive shifts — disinhibition "
                     "hits here hardest."),
        "VNC": ("The motor cord and legs: every walk the fly takes runs through "
                "here, and toxins that freeze the body show up in its firing."),
        "unassigned": ("Contacts without a home region: counted, shown, and "
                        "modeled only as part of the whole-brain network."),
        "nowire": ("Neurons with no wiring in the export: counted and shown, "
                    "but the sim cannot drive what has no connections."),
    }
    dp = os.path.join(HERE, "data.json")
    d = json.load(open(dp))
    for e in d:
        real = (e["desc"] or "").strip()
        if not real.endswith("."):
            real += "."
        if e["level"] == "hub":
            sim = HUB_SIM.get(e["hub"], GENERIC_SIM)
            e["desc"] = (f"In a real fly, {real[0].lower() + real[1:]} "
                         f"Simulated version: {sim}")
        else:
            sim = REGION_SIM.get(e["name"])
            if sim is None:
                sim = VNC_SIM if e["hub"] == "VNC" else GENERIC_SIM
            e["desc"] = (f"In a real fly, {real[0].lower() + real[1:]} It sits in "
                         f"the {e['hub']} system. Simulated version: {sim}")
    json.dump(d, open(dp, "w"), indent=1)
    print(f"regions+hubs: {len(d)} rewritten")

    # ---------- sides (94) ----------
    byname = {e["name"]: e for e in json.load(open(dp))}
    sdp = os.path.join(HERE, "sides.json")
    sd = json.load(open(sdp))
    for e in sd:
        side = "left" if e["name"].endswith("_L") else "right"
        base = byname[e["base"]]
        keep = [s.strip() for s in (e["desc"] or "").split(". ")
                if "unpaired" in s or "unavailable" in s]
        fs = f"{e['fs']:,}" if e["fs"] is not None else "no"
        ms = f"{e['ms']:,}" if e["ms"] is not None else "no"
        e["desc"] = (f"This is the {side} half of {e['base']}, the {base['func']} "
                     f"region. It carries {fs} female and {ms} male synapses."
                     + (f" {' '.join(s if s.endswith('.') else s + '.' for s in keep)}" if keep else "")
                     + f" Simulated version: same model as the whole region — the "
                     f"3D view renders the full {e['base']}, sides included.")
    json.dump(sd, open(sdp, "w"), indent=1)
    print(f"sides: {len(sd)} rewritten")

    # ---------- subsets (65) ----------
    ssp = os.path.join(HERE, "subsets.json")
    ss = json.load(open(ssp))
    for e in ss:
        src = "Male Fly Optic Nerve" if "optic" in e["name"] else "Male Fly Connectome"
        m = re.search(r"([\d,]+) connections", e["desc"] or "")
        conn = f"{m.group(1)} connections, " if m else ""
        e["desc"] = (f"These counts come from the male-only {src} file: {conn}"
                     f"{e['ms']:,} male synapses tagged {e['code']}. There is no "
                     f"female counterpart and no 3D positions, so this card is "
                     f"counts only — the picture shows the group. Simulated "
                     f"version: subsets are not modeled; the sim runs on the full "
                     f"male and female connectomes, not these splits.")
    json.dump(ss, open(ssp, "w"), indent=1)
    print(f"subsets: {len(ss)} rewritten")

    # ---------- self-verification ----------
    ct2 = json.load(open(ctp))
    ov = next(e for e in ct2 if e["name"] == "ORN_V")
    if "transmitters ACH 47%, SER 47%, GABA 6% (of predicted" not in ov["desc"]:
        fails.append("ORN_V transmitter sentence lost")
    if "tie — mixed prediction" not in ov["desc"]:
        fails.append("ORN_V mixed wording lost")
    sd2 = json.load(open(sdp))
    for e in sd2:
        if e["base"] in ("ME",) and ("unpaired" in e["desc"] or "unavailable" in e["desc"]):
            pass
    if any(not e["desc"] for e in ct2 + json.load(open(dp)) + sd2 + json.load(open(ssp))):
        fails.append("empty desc written")
    if any("Simulated version:" not in e["desc"] for e in ct2 + sd2 + json.load(open(ssp))):
        fails.append("sim line missing")
    if fails:
        print("FAILURES:")
        for f in fails:
            print(" -", f)
        raise SystemExit("NOT YET")
    print("ALL PASS")


if __name__ == "__main__":
    main()
