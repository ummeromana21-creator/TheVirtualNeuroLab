"""Maintained check for the Vivarium page. Run from this folder: python3 check.py"""
import json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
fails = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f" [{extra}]" if extra and not cond else ""))
    if not cond:
        fails.append(name)


html = open(os.path.join(HERE, "index.html")).read()
mods = re.findall(r'<script type="module">(.*?)</script>', html, re.S)
check("one inline module", len(mods) == 1, len(mods))
js = mods[0] if mods else ""

# ids referenced from JS must exist in the static HTML or be rendered dynamically
ids_html = set(re.findall(r'id="([^"]+)"', html)) | {"closeup"}  # rendered dynamically
used = set(re.findall(r'''(?:getElementById|\$\()\s*["']([^"']+)["']''', js))
check("js ids exist in html", used <= ids_html, sorted(used - ids_html)[:5])

for ref in ("index.html", "fly.js", "smoke.js", "smoke-loader.mjs",
            "../study.html", "../library/index.html",
            "../vendor/three/three.module.js"):
    check(f"ref {ref}", os.path.exists(os.path.join(HERE, ref)))

# portal nav: shared Feather.topbar mount + every hub href resolves to a real page
check("shared nav mount", 'id="navMount"' in html and "Feather.topbar" in html)
for href in ("duo/", "study.html", "library/", "experiments/", "duo/profile.html"):
    target = os.path.join(HERE, "..", href)
    ok = os.path.isdir(target) or os.path.exists(target)
    check(f"hub {href} resolves", ok)
shell = open(os.path.join(HERE, "..", "feather.js")).read()
check("hubs single-sourced", all(f"href: '{h}'" in shell for h in
      ("duo/", "flies/", "study.html", "library/", "experiments/", "duo/profile.html")))
check("ask hub removed", "href: 'ask/'" not in shell)

# pinned content: atlas numbers + taxonomy + both flies
for pin in ("157,789", "166,700", "23.6 million", "89.9 million",
            "66 entries", "DROSOPHILIDAE", "Diptera", "Drosophila",
            "Maxime", "Hagrid", "Compound eye", "Haltere", "labelBtn",
            "partTip", "partAt", "intersectObjects"):
    check(f"content {pin}", pin in html)

check("importmap vendored three", '"three": "../vendor/three/three.module.js"' in html)
check("no test hooks", "window.__" not in html)
urls = sorted(set(re.findall(r'https?://[^"\' )]+', html)))
ext = [u for u in urls if not any(h in u for h in
       ("fonts.googleapis.com", "fonts.gstatic.com", "www.w3.org"))]
check("only font CDN external", not ext, ext[:3])
check("canvas + stage + sheet", all(x in html for x in ('id="gl"', 'id="stage"', 'id="detail"')))

# vivarium: renamed page, shared builder, both specimens, tripod gait
fly = open(os.path.join(HERE, "fly.js")).read()
check("page renamed", "<title>Vivarium · Fly Lab</title>" in html)
check("nav renamed", "name: 'Vivarium'" in shell)
check("builder shared", "from './fly.js'" in html)
check("no inline builder", "function buildFly(" not in html)
check("table staging", "const table = new THREE.Group()" in html)
check("both pivots placed", "SPREAD" in html)
check("gait loop", "stepGait" in html and "Alternating tripod" in fly)
check("rig refs", "userData.rig" in fly and "phase:" in fly)
check("framing applied", "camera.updateProjectionMatrix();  // offsets apply only here" in html)
check("brain seated", "buildBrain" in html and "somas.bin" in html and "photoreceptors.bin" in html)
check("cuticle control", "setCuticle" in html and 'data-cut="2"' in html)
check("live link", "8765" in html and "control:banc" in html and "treatment:malecns" in html)
check("true spots", "ARENA_K" in html and "Math.PI / 2 - s.fly.angle" in html)
check("glow + gait follow sim", "stepGlow" in html and "s.rates.all" in html and "s.legs" in html)
check("light flashes receptors", "s.stimuli" in html and "stimuli.light" in html)
check("bananas per box", "bananas" in html and "s.banana" in html)
check("honesty note", "Not tracked motion" in html and "placed by eye" in html)
check("jar environment", all(x in html for x in ("agarTex", "CircleGeometry(1.55", "MeshPhysicalMaterial", "userData.env = 'sprig'")))
check("floors ride feet", "FOOT_Y * normScale * rig.zoomK" in html)
check("set-dressing labeled", "set-dressing" in html)
check("status line", "vivStatus" in html and "Live from the sim" in html)

if mods and shutil.which("node"):
    open("/tmp/fliescheck.mjs", "w").write(js)
    r = subprocess.run(["node", "--check", "/tmp/fliescheck.mjs"], capture_output=True)
    check("module syntax", r.returncode == 0, r.stderr.decode()[:200])
    for f in ("fly.js", "smoke.js"):
        r = subprocess.run(["node", "--check", os.path.join(HERE, f)], capture_output=True)
        check(f"{f} syntax", r.returncode == 0, r.stderr.decode()[:200])
    r = subprocess.run(["node", "smoke.js"], capture_output=True, text=True, cwd=HERE)
    tail = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()[-3:]
    check("vivarium smoke", r.returncode == 0, " | ".join(tail))
else:
    print("SKIP module syntax (no node)")

print()
print("RESULT:", "ALL CHECKS PASSED" if not fails else f"FAILURES: {fails}")
sys.exit(1 if fails else 0)
