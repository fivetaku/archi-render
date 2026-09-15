#!/usr/bin/env bash
# scripts/selftest.sh — end-to-end self-verification of the render pipeline (no API calls).
# Convention: 30-docs/scripts-layer.md — every judging/converting script ships --selftest; this
# orchestrates them plus a dry-run render → QA → contact sheet on synthetic fixtures. Exit 0 = OK.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
S="$ROOT/scripts"
FIX="$ROOT/evals/fixtures"
TMP="$(mktemp -d -t archi-selftest.XXXXXX)"
PROJ="_selftest"
trap 'rm -rf "$TMP" "$ROOT/renders/$PROJ" "$ROOT/assets/captures/$PROJ" "$ROOT/50-output/$PROJ"' EXIT

step() { printf '\n== %s\n' "$*"; }

step "1/7 unit selftests"
python3 "$S/prompt_compose.py" --selftest
PROMPT_COMPOSE_NO_YAML=1 python3 "$S/prompt_compose.py" --selftest   # exercise the fallback YAML parser
python3 "$S/mask_convert.py" --selftest
python3 "$S/qa_geometry.py" --selftest

step "2/7 fixtures"
mkdir -p "$FIX"
python3 - "$FIX" "$TMP" <<'PY'
import sys
from pathlib import Path
from PIL import Image, ImageDraw
fix, tmp = Path(sys.argv[1]), Path(sys.argv[2])
cap = fix / "sample_capture.png"
if not cap.is_file():
    im = Image.new("RGB", (640, 360), (235, 235, 235)); d = ImageDraw.Draw(im)
    d.rectangle((120, 120, 520, 320), fill=(200, 200, 200), outline=(40, 40, 40), width=3)
    d.polygon([(120, 120), (320, 40), (520, 120)], fill=(170, 170, 170), outline=(40, 40, 40))
    for x in (160, 300, 440): d.rectangle((x, 170, x + 60, 240), fill=(120, 140, 160), outline=(40, 40, 40), width=2)
    d.rectangle((310, 250, 350, 320), fill=(90, 70, 50), outline=(40, 40, 40), width=2)
    im.save(cap)
# a "render": same geometry, warmer tones, +1px shift → should pass QA; a drifted one → should WARN
src = Image.open(cap).convert("RGB")
render = Image.new("RGB", src.size, (250, 240, 225)); render.paste(src.crop((0, 0, src.width - 1, src.height)), (1, 0))
render.save(tmp / "render_ok.png")
d = ImageDraw.Draw(render); d.ellipse((530, 150, 630, 330), fill=(60, 120, 60), outline=(20, 40, 20), width=3)
d.rectangle((120, 120, 520, 320), fill=(250, 240, 225)); render.save(tmp / "render_drift.png")
m = Image.new("L", src.size, 0); ImageDraw.Draw(m).rectangle((160, 170, 220, 240), fill=255); m.save(tmp / "mask_internal.png")
print("fixtures ok", cap)
PY

step "3/7 prompt_compose on fixture pack + every pack in assets/stylepacks (PyYAML and fallback parser)"
PACK="$FIX/sample_pack/pack.yaml"
for p in "$PACK" "$ROOT"/assets/stylepacks/*/pack.yaml; do
  [ -f "$p" ] || continue
  id="$(basename "$(dirname "$p")")"
  out="$(python3 "$S/prompt_compose.py" --pack "$p" --option aspect=16:9 --option 'keep_fixed=the canopies white')"
  out2="$(PROMPT_COMPOSE_NO_YAML=1 python3 "$S/prompt_compose.py" --pack "$p" --option aspect=16:9 --option 'keep_fixed=the canopies white')"
  grep -q "Use the attached SketchUp image" <<<"$out" && grep -q "Keep the canopies white." <<<"$out" || { echo "FAIL prompt for $id"; exit 1; }
  [ "$out" == "$out2" ] || { echo "FAIL fallback YAML parser disagrees with PyYAML for $id"; exit 1; }
  echo "  $id: ${#out} chars (parsers agree)"
done

step "3b/7 merged option axes: maximal set on every pack stays within the slot cap; --list-options is valid JSON"
python3 - "$S/prompt_compose.py" "$FIX/options_maximal.json" "$PACK" "$ROOT"/assets/stylepacks/*/pack.yaml <<'PY'
import json, subprocess, sys
from pathlib import Path
script, fixture, *packs = sys.argv[1:]
sys.path.insert(0, str(Path(script).parent)); import prompt_compose as pc
fx = json.loads(Path(fixture).read_text())
args = [f"--option={k}={v}" for k, v in fx["options"].items()]
for p in packs:
    if not Path(p).is_file(): continue
    parts = json.loads(subprocess.check_output([sys.executable, script, "--pack", p, "--json", *args], text=True))
    slots = parts["slots"]
    assert len(slots) <= 7, (p, len(slots), slots)
    pack = pc.load_pack(p)
    people_on = not any(pc.PEOPLE_OFF_RE.search(str(i)) for i in pc._as_list((pack.get("slots") or {}).get("entourage")))
    expect = dict(fx["expect_in_slots"])
    if people_on:
        expect["entourage"] = expect["entourage"] + fx["expect_in_slots_if_people_on"]["entourage"]
    for name, needles in expect.items():
        hits = [s for s in slots if all(n in s for n in needles)]
        assert hits, f"{Path(p).parent.name}: merged axis {name!r} missing {needles} in {slots}"
    joined = " ".join(slots)
    assert "no cars" not in joined and "no additional cars" not in joined, slots     # car_density=few overrode the cars item
    assert people_on == ("fifteen or more" in joined), (people_on, slots)            # people axes apply only when people are on
    assert "Keep the canopies white." in parts["keeps"] and parts["tail"][-1] == "Aspect ratio 16:9.", parts
    print(f"  {Path(p).parent.name}: {len(slots)} slot sentences, all merged axes present")
lo = json.loads(subprocess.check_output([sys.executable, script, "--list-options"], text=True))
assert len(lo["options"]) >= 20 and isinstance(lo["values"], dict) and isinstance(lo["free"], dict), lo.keys()
for k in ("people_density", "sky", "context", "material_wear", "tone", "interior_lights", "vegetation_age", "car_type"):
    assert k in lo["values"], k
for k in ("lens_mm", "camera_height_m", "keep_fixed", "references"):
    assert k in lo["free"], k
print(f"  --list-options: {len(lo['options'])} keys ({len(lo['values'])} enum, {len(lo['free'])} free)")
PY

step "4/7 render.py --dry-run (gpt + grok) and fix --dry-run"
python3 "$S/render.py" --input "$FIX/sample_capture.png" --project "$PROJ" --shot S01 --pack "$PACK" --option lighting=golden_hour --dry-run
python3 "$S/render.py" --input "$FIX/sample_capture.png" --project "$PROJ" --shot S01 --pack "$PACK" --backend grok --aspect 16:9 --dry-run
test -f "$ROOT/renders/$PROJ/S01/R00/meta.json" && test -f "$ROOT/renders/$PROJ/S01/R01/prompt.txt" && test -f "$ROOT/assets/captures/$PROJ/S01/capture.png"
cp "$TMP/render_ok.png" "$ROOT/renders/$PROJ/S01/R01/render.png"     # simulate a returned render for fix/QA/sheet
python3 "$S/render.py" fix --project "$PROJ" --shot S01 --mask "$TMP/mask_internal.png" --instruction "Replace the left window with an arched wooden window" --dry-run
test -f "$ROOT/renders/$PROJ/S01/R02/mask_grok.png"
if python3 "$S/render.py" fix --project "$PROJ" --shot S01 --mask "$TMP/mask_internal.png" --instruction x --backend gpt --dry-run 2>"$TMP/refuse.txt"; then
  echo "FAIL: fix --backend gpt must be refused"; exit 1; else echo "  fix --backend gpt refused as expected: $(head -c 80 "$TMP/refuse.txt")..."; fi
python3 - "$ROOT/renders/$PROJ/S01" <<'PY'
import json, sys
from pathlib import Path
from PIL import Image
d = Path(sys.argv[1])
m = json.loads((d / "R00/meta.json").read_text()); assert m["stage"] == "clay" and m["backend"] == "gpt" and m["input_sha1"] and "warm low sun" in m["prompt"] and m["aspect"] == "16:9"
m2 = json.loads((d / "R02/meta.json").read_text()); assert m2["mode"] == "fix" and m2["base_revision"] == "R01"
mk = Image.open(d / "R02/mask_grok.png"); assert mk.mode == "RGBA" and mk.size == Image.open(d / "R01/render.png").size
assert mk.getpixel((190, 200))[3] == 0 and mk.getpixel((10, 10))[3] == 255, "grok mask polarity alpha0=edit"
print("  meta/mask assertions ok")
PY

step "5/7 mask_convert CLI round trip"
python3 "$S/mask_convert.py" --in "$TMP/mask_internal.png" --out "$TMP/mask_grok.png" --vendor grok --match "$FIX/sample_capture.png" --dilate 12 --feather 6
python3 "$S/mask_convert.py" --in "$TMP/mask_grok.png" --out "$TMP/mask_flux.png" --vendor flux

step "6/7 qa_geometry (advisory)"
python3 "$S/qa_geometry.py" --capture "$FIX/sample_capture.png" --render "$TMP/render_ok.png" --json-out "$TMP/qa_ok.json"
drift_out="$(python3 "$S/qa_geometry.py" --capture "$FIX/sample_capture.png" --render "$TMP/render_drift.png" 2>&1)"
grep -q "WARN" <<<"$drift_out" || { echo "FAIL: drift case did not emit WARN"; echo "$drift_out"; exit 1; }
echo "  drift case emitted WARN as expected"

step "7/7 contact_sheet + revision"
python3 "$S/contact_sheet.py" --project "$PROJ" --latest --tile 256
python3 "$S/revision.py" approve --project "$PROJ" --shot S01 --revision R01 --stage internal --note "selftest"
python3 "$S/revision.py" list --project "$PROJ"
# keep 40-reports/approvals.md clean of selftest rows
[ -f "$ROOT/40-reports/approvals.md" ] && { grep -v "| $PROJ |" "$ROOT/40-reports/approvals.md" > "$TMP/appr" || true; mv "$TMP/appr" "$ROOT/40-reports/approvals.md"; }

echo
echo "SELFTEST OK"
