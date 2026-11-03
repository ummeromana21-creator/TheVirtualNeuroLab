"""Maintained check for the region library page. Run from this folder: python3 check.py"""
import json, os, re, shutil, struct, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
fails = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f" [{extra}]" if extra and not cond else ""))
    if not cond:
        fails.append(name)


d = json.load(open(os.path.join(HERE, "data.json")))
check("66 entries", len(d) == 66, len(d))
req = {"row", "level", "hub", "name", "fn", "mn", "fe", "me", "fs", "ms",
       "ratio", "func", "desc", "img"}
check("entry schema", all(set(e) == req for e in d))
check("hub F syn total", sum(e["fs"] or 0 for e in d if e["level"] == "hub") == 23556214)
check("hub M syn total", sum(e["ms"] or 0 for e in d if e["level"] == "hub") == 89860280)
missing = [e["img"] for e in d if not os.path.exists(os.path.join(HERE, e["img"]))]
check("card images resolve", not missing, missing[:3])
need = {e["name"] for e in d if e["level"] == "neuropil"
        and e["hub"] not in ("VNC", "unassigned", "nowire")}
idx = json.load(open(os.path.join(HERE, "points", "index.json")))
check("points cover brain neuropils", need == set(idx["regions"]),
      sorted(need ^ set(idx["regions"]))[:5])
nobin = [r for r in idx["regions"] if not os.path.exists(os.path.join(HERE, "points", f"{r}.bin"))]
check("region bins present", not nobin, nobin[:3])
for f in ("points/somas.bin", "points/classes.bin"):
    check(f"{f} present", os.path.exists(os.path.join(HERE, f)))

ct = json.load(open(os.path.join(HERE, "celltypes.json")))
check("236 cell types", len(ct) == 236, len(ct))
creq = {"row", "level", "hub", "name", "cls", "sub", "flow", "fn", "mn",
        "fe", "me", "fs", "ms", "ratio", "top", "func", "desc", "img",
        "aliases", "nt", "nt_mixed"}
check("celltype schema", all(set(e) == creq for e in ct))
check("celltype levels", all(e["level"] == "celltype" and e["hub"] == "celltypes" for e in ct))
check("celltype names unique", len({e["name"] for e in ct}) == len(ct))
check("celltype neurons covered", sum(e["fn"] for e in ct) == 102490, sum(e["fn"] for e in ct))
rendered = [e for e in ct if e["img"] != "img/celltype.svg"]
check("celltype renders built", len(rendered) == 236, len(rendered))
check("celltype imgs resolve",
      all(os.path.exists(os.path.join(HERE, e["img"])) for e in rendered))
check("celltype bins resolve",
      all(os.path.exists(os.path.join(HERE, "points", e["name"] + ".bin")) for e in rendered))
r1 = next(e for e in ct if e["name"] == "R1-6")
check("R1-6 pinned", r1["fn"] == 8456 and r1["fs"] == 200627 and r1["top"] == ["LA"], r1["fn"])
check("celltype sorted by neurons", all(ct[i]["fn"] >= ct[i + 1]["fn"] for i in range(len(ct) - 1)))
check("celltype images resolve", all(os.path.exists(os.path.join(HERE, e["img"])) for e in ct))
check("celltype descs non-empty", all(e["desc"] and e["func"] for e in ct))
ov = next(e for e in ct if e["name"] == "ORN_V")
check("ORN_V alias exact", ov["aliases"] == "CO2 receptor neurons, ab1C, Gr21a/Gr63a", ov["aliases"])
check("aliases filled", sum(1 for e in ct if e["aliases"]) == 235,
      [e["name"] for e in ct if not e["aliases"]])
check("nt_mixed flags", ov["nt_mixed"] is True and
      next(e for e in ct if e["name"] == "T1")["nt_mixed"] is True and
      next(e for e in ct if e["name"] == "Mi1")["nt_mixed"] is False and
      next(e for e in ct if e["name"] == "R1-6")["nt_mixed"] is False)
check("desc carries full split", "transmitters ACH 47%, SER 47%, GABA 6% (of predicted" in ov["desc"] and
      "tie — mixed prediction" in ov["desc"], ov["desc"][-80:])
check("card imgs are celltype stills",
      all(e["img"] == f"../anatomy/celltypes/stills/{e['name']}.png" for e in ct))

sd = json.load(open(os.path.join(HERE, "sides.json")))
ss = json.load(open(os.path.join(HERE, "subsets.json")))
sg = json.load(open(os.path.join(HERE, "sensegroups.json")))
check("94 sides", len(sd) == 94, len(sd))
check("47 regions split", len({e["base"] for e in sd}) == 47)
check("65 subsets", len(ss) == 65, len(ss))
mel = next(e for e in sd if e["name"] == "ME_L")
mer = next(e for e in sd if e["name"] == "ME_R")
check("ME_L pinned", mel["fs"] == 1672003 and mel["ms"] == 8358660, (mel["fs"], mel["ms"]))
check("ME_R pinned", mer["fs"] == 2471832 and mer["ms"] == 10323123, (mer["fs"], mer["ms"]))
check("ME sides sum to parent", mel["fs"] + mer["fs"] == 4143835 and mel["ms"] + mer["ms"] == 18681783)
sub_me = next(e for e in ss if e["name"] == "ME_R (male optic)")
check("subset ME_R pinned", sub_me["ms"] == 15267641, sub_me["ms"])
allnames = [e["name"] for e in d + ct + sd + ss + sg]
dupes = [n for n in set(allnames) if allnames.count(n) > 1]
# GNG hub + GNG neuropil share a name in the original 66 rows (pre-existing);
# every new card file must add zero further collisions.
check("names unique across all card files", dupes == ["GNG"], dupes)
sreq = {"row", "level", "hub", "name", "base", "fn", "mn", "fe", "me",
        "fs", "ms", "ratio", "func", "desc", "img"}
check("side schema", all(set(e) == sreq for e in sd))
check("side levels", all(e["level"] == "side" for e in sd))
check("side names sided", all(e["name"].endswith(("_L", "_R")) for e in sd))
nameset = {x["name"] for x in sd}
check("side pairs complete", all((e["name"][:-2] + ("_L" if e["name"].endswith("_R") else "_R")) in nameset for e in sd))
dbyname = {e["name"]: e for e in d}
check("side bases are neuropils", all(e["base"] in dbyname and dbyname[e["base"]]["level"] == "neuropil" for e in sd))
check("side hubs match parent", all(e["hub"] == dbyname[e["base"]]["hub"] for e in sd))
check("side images match parent", all(e["img"] == dbyname[e["base"]]["img"] for e in sd))
sums = {}
for e in sd:
    a, b = sums.get(e["base"], (0, 0))
    sums[e["base"]] = (a + (e["fs"] or 0), b + (e["ms"] or 0))
ok = True
for base, (fs, ms) in sums.items():
    p = dbyname[base]
    if fs > (p["fs"] or 0) or ms > (p["ms"] or 0):
        ok = False
check("side sums within parent", ok)
need_note = [b for b, (fs, ms) in sums.items()
             if fs < (dbyname[b]["fs"] or 0) or ms < (dbyname[b]["ms"] or 0)]
noted = all(any("unpaired" in x["desc"] or "unavailable" in x["desc"] for x in sd if x["base"] == b) for b in need_note)
check("side shortfalls explained", noted, [b for b in need_note if not any("unpaired" in x["desc"] or "unavailable" in x["desc"] for x in sd if x["base"] == b)][:3])
ureq = {"row", "level", "hub", "name", "code", "fn", "mn", "fe", "me",
        "fs", "ms", "ratio", "func", "desc", "img"}
check("subset schema", all(set(e) == ureq for e in ss))
check("subset levels", all(e["level"] == "subset" and e["hub"] == "subsets" for e in ss))
check("subset male-only", all(e["fs"] is None and e["ms"] and e["ratio"] == "M-only" for e in ss))
check("subset names unique", len({e["name"] for e in ss}) == len(ss))
check("subset images resolve", all(os.path.exists(os.path.join(HERE, e["img"])) for e in ss))
greq = {"row", "level", "hub", "name", "fn", "mn", "fe", "me",
        "fs", "ms", "ratio", "func", "desc", "img"}
check("3 sense groups", len(sg) == 3, len(sg))
check("sense schema", all(set(e) == greq for e in sg))
check("sense levels", all(e["level"] == "sense" and e["hub"] == "senses" for e in sg))
check("sense rows 4000+", sorted(e["row"] for e in sg) == [4000, 4001, 4002])
check("sense counts pinned",
      {e["name"]: e["fn"] for e in sg} == {"photoreceptors": 11151, "taste": 408, "visual-targets": 6861})
check("sense honesty nulls",
      all(e["mn"] is None and e["fs"] is None and e["ms"] is None and e["ratio"] is None for e in sg))
check("sense sim counts in desc", all("Maxime" in e["desc"] and "Hagrid" in e["desc"] for e in sg))
check("sense images resolve", all(os.path.exists(os.path.join(HERE, e["img"])) for e in sg))


def sense_bin_ok(e):
    p = os.path.join(HERE, "points", e["name"] + ".bin")
    if not os.path.exists(p):
        return False
    raw = open(p, "rb").read()
    if len(raw) // 12 != e["fn"]:
        return False
    xs = struct.unpack("<%df" % (len(raw) // 4), raw)[0::3]
    return max(abs(x) for x in xs) <= 1.001


check("sense bins normalized", all(sense_bin_ok(e) for e in sg))

sxd = json.load(open(os.path.join(HERE, "sexdiff.json")))
check("42 sexdiff regions", len(sxd) == 42, len(sxd))
check("sexdiff schema", all(set(v) == {"hub", "n", "fru", "dsx"} for v in sxd.values()))
check("sexdiff neurons assigned", sum(v["n"] for v in sxd.values()) == 133905)
check("sexdiff fru total", sum(v["fru"] for v in sxd.values()) == 1140)
check("sexdiff dsx total", sum(v["dsx"] for v in sxd.values()) == 120)
check("SMP top fru region", sxd["SMP"]["fru"] == 196 and sxd["SMP"]["hub"] == "lateral")
check("sexdiff regions are atlas regions",
      set(sxd) <= {e["name"] for e in d})

pw = json.load(open(os.path.join(HERE, "pathways.json")))
check("200 pathways", len(pw) == 200, len(pw))
check("pathway schema", all(set(e) == {"a", "b", "f", "m"} for e in pw))
check("pathways sorted desc", all(pw[i]["f"] + pw[i]["m"] >= pw[i + 1]["f"] + pw[i + 1]["m"] for i in range(len(pw) - 1)))
check("top pathway ME self-loop", pw[0]["a"] == "ME" and pw[0]["b"] == "ME" and pw[0]["f"] + pw[0]["m"] == 20474216)
top_ns = next(e for e in pw if e["a"] != e["b"])
check("top link ME->LO", (top_ns["a"], top_ns["b"]) == ("ME", "LO") and top_ns["f"] == 524087 and top_ns["m"] == 3375625)
check("pathway endpoints are atlas regions",
      {e["a"] for e in pw} | {e["b"] for e in pw} <= {e["name"] for e in d})

html = open(os.path.join(HERE, "index.html")).read()
js = open(os.path.join(HERE, "app.js")).read()
ids_html = set(re.findall(r'id="([^"]+)"', html)) | {"closeup"}  # rendered dynamically
used = set(re.findall(r'(?:getElementById|\$\()\s*["\']([^"\']+)["\']', js))
check("js ids exist in html", used <= ids_html, sorted(used - ids_html)[:5])
for ref in ("style.css", "app.js", "data.json", "meta.json", "celltypes.json",
            "sides.json", "subsets.json", "sexdiff.json", "pathways.json",
            "../study.html", "../vendor/three/three.module.js",
            "../vendor/three/addons/controls/OrbitControls.js",
            "../anatomy/celltype_logic.js"):
    check(f"ref {ref}", os.path.exists(os.path.join(HERE, ref)))
check("single topbar (no hub repeat)", "Feather.topbar(" not in js and html.count("Feather.topbar(") == 1)
check("celltypes embed viewer", "showCell" in js and "cellwrap" in js and 'img === "img/celltype.svg"' not in js)
check("cell viewer ortho+scale", "OrthographicCamera" in js and "100 µm" in html)
check("cell viewer follows theme", "cellPaint" in js and "CELLC" in js and "alpha: true" in js)
check("cell viewer click-to-codex", "codex.flywire.ai/app/cell_details" in js)
check("cell viewer logic import (cache-busted)", 'from "../anatomy/celltype_logic.js?v=1"' in js)
check("region 3D failure message", "3D failed to load (" in js)
check("cellwrap in stage", 'id="cellwrap"' in html and "three/addons/" in html)
check("celltype lit color", "celltypes: 0x0e7490" in js and "celltypes: 0x22d3ee" in js)
check("toolbar keeps search+filter", all(s in html for s in ('class="topsearch"', 'id="filterBtn"', 'id="lightBtn"', 'id="sub"')))
check("celltypes hub chip", '"celltypes"' in js)
check("celltypes fetch", 'fetch("celltypes.json?v=1")' in js)
check("celltypes level option", 'value="celltype"' in html)
check("celltypes fallback caption gone", "open the cell viewer for the 3D dots" not in js)
check("alias search", 'e.aliases || ""' in js)
check("card v783 line", "counts: FlyWire v783" in js)
check("no cell-viewer link-out", "anatomy/celltype.html#" not in js)
check("provenance collapsed", '<details class="fine"><summary>Data sources</summary>' in js)
check("no placeholder copy", "placeholder" not in js)
check("hub titles use full names", "HUBNAME" in js and "Smell centres" in js and "Lateral / premotor zone" in js)
check("subset titles normalized", r"\(male (VNC|optic)\)" in js)
check("card art cache-busted", 'IMGV = "?v=' in js and "${IMGV}" in js and "e.img + IMGV" in js)
check("asklink keeps region+level", "&region=" in js and "&level=" in js)
check("subsets hub chip", '"subsets"' in js)
check("sides fetch", 'fetch("sides.json")' in js)
check("subsets fetch", 'fetch("subsets.json")' in js)
check("side level option", 'value="side"' in html)
check("subset level option", 'value="subset"' in html)
check("sense level option", 'value="sense"' in html)
check("senses hub chip", '"senses"' in js)
check("senses fetch", 'fetch("sensegroups.json")' in js)
check("senses lit color", "senses: 0xb941a0" in js and "senses: 0xd86fc0" in js)
check("sense closeup text", "Zoom to this group in 3D" in js)
check("hyphen display names", "visual-targets -> Visual targets" in js)
check("side caption", "render shows the whole region" in js)
check("subset caption", "Male-only subset file" in js)
check("side display names", r'/^(.+)_([LR])$/' in js)
check("pathways fetch", 'fetch("pathways.json")' in js)
check("pathways toggle", 'id="pathways"' in js)
check("pathways lines", "LineSegments" in js)
check("cache-busted assets", "style.css?v=" in html and "app.js?v=" in html)
check("citation footer", "doi:10.13140" in html)
css = open(os.path.join(HERE, "style.css")).read()
check("loader hidden rule", ".loader[hidden]" in css)
check("tooltip element", 'id="partTip"' in html)
check("tooltip hidden rule", ".parttip[hidden]" in css)
m = re.search(r"const EXP = \{(.*?)\};", js, re.S)
keys = set(re.findall(r"([A-Za-z_]\w*): \"", m.group(1))) if m else set()
plain = {"lateral", "nowire", "olfactory", "optic", "unassigned", "Abdomen", "nerves"}
need = {e["name"] for e in d} - plain
check("expansions cover coded names", need == keys, sorted(need ^ keys)[:5])
for pin in ("Inframedial bridge", "Lower tectulum", "Cantle",
            "Medial ventral association center", "Antennal mechanosensory and motor center"):
    check(f"expansion {pin}", pin in js)
check("no stale .Detail class selectors", ".Detail" not in css)
m = re.search(r"#cellgl canvas \{(.*?)\}", css)
check("cell canvas fills box (retina)", bool(m) and "width:100%" in m.group(1) and "height:100%" in m.group(1))

if shutil.which("node"):
    # --check needs an ESM suffix for module syntax; copy aside
    shutil.copyfile(os.path.join(HERE, "app.js"), "/tmp/libcheck.mjs")
    r = subprocess.run(["node", "--check", "/tmp/libcheck.mjs"], capture_output=True)
    check("app.js syntax", r.returncode == 0, r.stderr.decode()[:200])
else:
    print("SKIP app.js syntax (no node)")

print()
print("RESULT:", "ALL CHECKS PASSED" if not fails else f"FAILURES: {fails}")
sys.exit(1 if fails else 0)
