#!/usr/bin/env python3
"""Compose a render prompt from a stylepack + per-shot options.

Pack files live in ``assets/stylepacks/<id>/pack.yaml`` (schema: 30-docs / design §7).
Loading: ``import yaml`` when available; otherwise a minimal built-in YAML subset parser
(block mappings/lists, quoted scalars, inline ``{}``/``[]``, ``#`` comments). A
``pack.json`` next to (or instead of) ``pack.yaml`` is also accepted and preferred when
PyYAML is missing and the mini parser cannot read the file.

Prompt structure (proven in trial_20260914):
  1. geometry lock sentence   2. mood + shot type + camera   3. materials
  4. lighting                 5. season/weather               6. entourage
  7. post/grading             8. keep_fixed lines             9. "Avoid: ..."
  10. aspect ratio hint
Slots 2-7 are capped at 7 sentences; lock/keep_fixed/avoid/aspect are extra.

Option keys override pack slots: mood, shot_type, lighting, season_weather, camera,
materials (list or comma string), entourage (list or comma string), post,
keep_fixed (list or ';'-separated string), aspect, source_note.
Entourage whitelist: if the pack defines ``entourage_allowed``, items outside it are dropped.

CLI: python3 scripts/prompt_compose.py --pack <id-or-path> [--option k=v ...] [--print]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKS_DIR = ROOT / "assets" / "stylepacks"
MAX_SLOT_SENTENCES = 7

LOCK = (
    "Use the attached {src} image as the exact source. Keep the geometry, camera angle, "
    "proportions, layout and all element positions exactly as shown. Do not add or remove "
    "buildings, floors or openings."
)
LIST_KEYS = {"materials", "entourage", "keep_fixed", "references", "samples"}

# ---- preset vocabulary: mirror of 20-knowledge/stylepacks/OPTIONS.md (source of truth; keep in sync).
# Unknown values pass through as free text, so packs and ad-hoc options keep working.
MOOD_WORDS = {
    "photoreal": "photorealistic architectural photograph",
    "cinematic": "cinematic, photorealistic architectural photograph",
    "clay": "clay-model white massing render",
    "watercolor": "loose architectural watercolor illustration",
    "diagram": "clean axonometric-style diagram render",
    "painterly": "painterly architectural illustration",
    "collage": "architectural collage",
}
MOOD_COMPANION = {  # mood → (materials list, post) replacements unless given explicitly
    "cinematic": (None, "teal_orange"),
    "clay": (["uniform matte white clay on every surface", "light grey ground plane",
              "clear glass shown as pale grey tinted panes"],
             "neutral, soft ambient occlusion in corners, no color grading, no vignetting"),
    "watercolor": (["washes of the drawn materials with visible paper grain and pigment bleed at edges",
                    "pencil underdrawing showing through"], "warm off-white paper, no photographic grading"),
    "diagram": (["flat white surfaces with thin 1 px dark grey edge lines",
                 "one accent color #FF6B35 only on the element under discussion"],
                "flat lighting, pure white background, no shadows, no grading"),
}
LIGHTING = {
    "overcast": "soft overcast daylight from a uniformly bright grey-white sky, no direct sun, low-contrast ambient shadows under overhangs only",
    "midday": "high sun near zenith, 5500K, hard short shadows directly below overhangs, strong texture read on facades",
    "golden_hour": "warm low sun from camera-left at 10 degrees elevation, 3200K, long soft-edged shadows stretching right, sunlit planes amber and shaded planes cool blue-grey, interior lights on at 2700K",
    "dusk": "sun just below the horizon camera-left, sky graded deep blue #1B2A49 at zenith to burnt orange #E8742A at horizon with lit cloud undersides, interior lights on at 2700K spilling onto the ground, long soft shadows",
    "night": "sky #0B1526 with no stars or moon, interior and sign lights at 3000K as the only warm sources, one cool 4000K street lamp per 15 m, soft shadowless ground",
    "blue_hour": "15 minutes after sunset, even cobalt sky #274B8F, no direct light, interior lights on at 2700K balanced to the sky, facades in soft cool shadow",
}
SEASON = {
    "spring": "late spring, fresh mid-green foliage, dry ground, thin high cloud",
    "summer": "early summer, clear sky with a few soft white cumulus, saturated green foliage, dry ground",
    "autumn": "mid autumn, amber and rust foliage on deciduous trees, a few fallen leaves at kerbs, dry ground, clear air",
    "winter": "midwinter, bare deciduous branches, pale low-contrast sky, dry cold ground, no snow",
    "rain": "after rain, puddled and wet-look ground with mirror reflections of lights and sky, dark saturated paving, dramatic broken clouds, no falling rain visible",
    "snow": "midwinter, 3 cm fresh snow on horizontal surfaces only, wet dark asphalt where ploughed, bare branches with snow, light snowfall visible only near the camera",
}
CAMERA = {  # value → (camera object, shot_type replacement)
    "eye_level": ({"lens_mm": 35, "height": "eye level, 1.6 m", "perspective": "straight vertical uprights, no keystoning, horizon at one-third height"}, "eye-level exterior view of THIS building"),
    "elevated": ({"lens_mm": 24, "height": "elevated, 3 m", "perspective": "straight vertical uprights, wide field of view"}, "slightly elevated exterior view of THIS building"),
    "drone": ({"lens_mm": 24, "height": "drone, 40 to 60 m", "perspective": "high oblique 45 to 60 degrees down, no lens distortion, site fills the frame"}, "aerial drone photograph of THIS site from the same angle"),
    "interior": ({"lens_mm": 24, "height": "1.4 m", "perspective": "straight vertical uprights, one-point or two-point perspective as drawn"}, "interior view of THIS room from THIS camera position"),
}
MATERIALS = {
    "white_stucco_oak": ["white fine-textured stucco", "dark anodized aluminum window frames", "warm oak deck boards", "black powder-coated steel railings", "clear low-iron glass"],
    "board_formed_concrete": ["board-formed concrete with visible plank grain, tie-hole grid and light weathering streaks", "exposed smooth concrete side walls", "glass storefront with sky reflections and visible interior", "asphalt with crisp painted white lines"],
    "brick_dark_metal": ["dark clinker brick with recessed grey mortar joints", "black standing-seam metal roof and fascia", "dark bronze anodized window frames", "clear glass"],
    "timber_glass": ["vertical larch cladding weathered to silver-grey", "exposed glulam beams", "floor-to-ceiling clear glass with slim black frames", "light concrete plinth"],
    "clay_massing": ["uniform matte white clay on every surface", "light grey ground plane", "clear glass shown as pale grey tinted panes"],
}
ENTOURAGE_TOGGLES = {  # toggle → (on sentence, off sentence); output order is fixed
    "people": ("people kept in the drawn positions with realistic clothing; if none drawn, two people near the entrance", "no people"),
    "cars": ("real cars only in the drawn parking bays or lanes", "no cars"),
    "vegetation": ("realistic trees, hedges and planting in the drawn positions with seasonally correct foliage", "vegetation exactly as drawn, no added planting"),
    "furniture": ("realistic outdoor furniture in the drawn positions, interior furniture visible through glass", "no added furniture"),
}
POST = {
    "neutral": "neutral color grading, white balance matched to the light source, no vignetting, no added contrast or saturation",
    "teal_orange": "cinematic grading with teal shadows and warm amber highlights, mild contrast lift, high dynamic range with no clipped windows, no vignetting",
    "warm_film": "warm film-like grading, slightly lifted blacks, gentle highlight roll-off, fine grain, no vignetting",
    "bw": "black and white, medium contrast, full tonal range from paper white to deep black without clipping, no toning",
}


# ---------------------------------------------------------------- mini YAML
def _strip_comment(s: str) -> str:
    out, q = [], None
    for i, ch in enumerate(s):
        if q:
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch
        elif ch == "#" and (i == 0 or s[i - 1] in " \t"):
            break
        out.append(ch)
    return "".join(out).rstrip()


def _scalar(tok: str):
    tok = tok.strip()
    if not tok or tok in ("null", "~"):
        return None
    if tok[0] in "\"'" and tok[-1] == tok[0] and len(tok) >= 2:
        return tok[1:-1]
    if tok in ("true", "True"):
        return True
    if tok in ("false", "False"):
        return False
    if re.fullmatch(r"-?\d+", tok):
        return int(tok)
    if re.fullmatch(r"-?\d+\.\d+", tok):
        return float(tok)
    return tok


def _split_flow(s: str) -> list[str]:
    """Split 'a, b: [c, d], e' at top-level commas."""
    parts, depth, q, cur = [], 0, None, []
    for ch in s:
        if q:
            cur.append(ch)
            if ch == q:
                q = None
            continue
        if ch in "\"'":
            q = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur))
    return parts


def _split_kv(s: str):
    """Split 'key: value' at the first ':' outside quotes/brackets; None if no key."""
    depth, q = 0, None
    for i, ch in enumerate(s):
        if q:
            if ch == q:
                q = None
            continue
        if ch in "\"'":
            q = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == ":" and depth == 0 and (i + 1 == len(s) or s[i + 1] in " \t"):
            return s[:i].strip(), s[i + 1:].strip()
    return None


def _flow(s: str):
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        return [_flow(p) for p in _split_flow(s[1:-1])]
    if s.startswith("{") and s.endswith("}"):
        d = {}
        for p in _split_flow(s[1:-1]):
            kv = _split_kv(p)
            if kv:
                d[_scalar(kv[0])] = _flow(kv[1])
        return d
    return _scalar(s)


def _parse_block(lines: list[tuple[int, str]], i: int, indent: int):
    """Parse lines[i:] at the given indent; return (value, next_index)."""
    if i >= len(lines):
        return None, i
    is_list = lines[i][1].startswith("- ") or lines[i][1] == "-"
    result: dict | list = [] if is_list else {}
    while i < len(lines):
        ind, text = lines[i]
        if ind < indent:
            break
        if ind > indent:
            raise ValueError(f"bad indent at line: {text!r}")
        if is_list:
            if not (text.startswith("- ") or text == "-"):
                break  # same-indent key after a block list → back to the parent mapping
            body = text[1:].strip()
            i += 1
            if not body:
                val, i = _parse_block(lines, i, _next_indent(lines, i, indent))
                result.append(val)
            elif _split_kv(body) and not body.startswith(("[", "{", "'", '"')):
                # "- key: v" → mapping item, possibly continued on deeper lines
                sub = [(indent + 2, body)]
                while i < len(lines) and lines[i][0] > indent:
                    sub.append((lines[i][0], lines[i][1]))
                    i += 1
                base = min(l[0] for l in sub)
                val, _ = _parse_block([(l[0] - base + indent + 2, l[1]) for l in sub], 0, indent + 2)
                result.append(val)
            else:
                result.append(_flow(body))
        else:
            kv = _split_kv(text)
            if not kv:
                raise ValueError(f"expected 'key: value': {text!r}")
            key, val = kv
            i += 1
            if val == "":
                if i < len(lines) and lines[i][0] > indent:
                    result[key], i = _parse_block(lines, i, lines[i][0])
                elif i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("-"):
                    result[key], i = _parse_block(lines, i, indent)  # list at same indent
                else:
                    result[key] = None
            else:
                result[key] = _flow(val)
    return result, i


def _next_indent(lines, i, indent):
    return lines[i][0] if i < len(lines) and lines[i][0] > indent else indent


def mini_yaml_load(text: str):
    """Minimal YAML subset loader (see module docstring)."""
    lines = []
    for raw in text.splitlines():
        s = _strip_comment(raw.replace("\t", "  "))
        if not s.strip() or s.strip() == "---":
            continue
        lines.append((len(s) - len(s.lstrip()), s.strip()))
    val, _ = _parse_block(lines, 0, lines[0][0] if lines else 0)
    return val


def _yaml_load(text: str):
    if os.environ.get("PROMPT_COMPOSE_NO_YAML") != "1":
        try:
            import yaml  # type: ignore

            return yaml.safe_load(text)
        except ImportError:
            pass
    return mini_yaml_load(text)


# ---------------------------------------------------------------- pack loading
def resolve_pack_path(id_or_path: str) -> Path:
    p = Path(id_or_path).expanduser()
    if p.is_file():
        return p
    if p.is_dir():
        for name in ("pack.yaml", "pack.yml", "pack.json"):
            if (p / name).is_file():
                return p / name
    d = PACKS_DIR / id_or_path
    for name in ("pack.yaml", "pack.yml", "pack.json"):
        if (d / name).is_file():
            return d / name
    raise FileNotFoundError(f"stylepack not found: {id_or_path} (looked in {PACKS_DIR})")


def load_pack(id_or_path: str) -> dict:
    path = resolve_pack_path(id_or_path)
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        pack = json.loads(text)
    else:
        try:
            pack = _yaml_load(text)
        except Exception as e:  # mini parser choked → try sibling json
            alt = path.with_name("pack.json")
            if alt.is_file():
                pack = json.loads(alt.read_text(encoding="utf-8"))
            else:
                raise ValueError(f"cannot parse {path}: {e}") from e
    if not isinstance(pack, dict):
        raise ValueError(f"pack is not a mapping: {path}")
    pack.setdefault("id", path.parent.name)
    pack["_path"] = str(path)
    return pack


# ---------------------------------------------------------------- compose
def _as_list(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return [str(x).strip() for x in v if str(x).strip()]
    s = str(v)
    sep = ";" if ";" in s else ","
    return [x.strip() for x in s.split(sep) if x.strip()]


def _sentence(s: str) -> str:
    s = str(s).strip()
    return s if s.endswith((".", "!", "?")) else s + "."


def _camera_text(cam) -> str:
    if isinstance(cam, dict):
        bits = []
        if cam.get("lens_mm"):
            bits.append(f"{cam['lens_mm']}mm lens")
        if cam.get("height"):
            bits.append(f"{cam['height']} camera height")
        if cam.get("perspective"):
            bits.append(str(cam["perspective"]))
        return ", ".join(bits)
    return str(cam or "").strip()


def _entourage(value) -> list[str]:
    """Toggle form 'people:on,cars:off' → 4 fixed sentences; anything else → plain list."""
    items = _as_list(value)
    toggles = {}
    for it in items:
        k, _, v = it.partition(":")
        k, v = k.strip().lower(), (v or "on").strip().lower()
        if k in ENTOURAGE_TOGGLES and v in ("on", "off"):
            toggles[k] = v == "on"
    if toggles and len(toggles) == len(items):
        return [ENTOURAGE_TOGGLES[k][0 if toggles.get(k, False) else 1] for k in ENTOURAGE_TOGGLES]
    return items


def pack_aspect(pack: dict):
    """Pack-level aspect: top-level `aspect`, else backends['gpt-image']['aspect_hint'] (schema §7)."""
    if pack.get("aspect"):
        return pack["aspect"]
    return ((pack.get("backends") or {}).get("gpt-image") or {}).get("aspect_hint")


def compose(pack: dict, options: dict, source_note: str = "SketchUp") -> str:
    """Return the final prompt string for one render.

    Option values may be OPTIONS.md preset names (lighting=golden_hour, materials=timber_glass,
    camera=drone, entourage=people:on,cars:off, post=bw ...) or free text. Presets expand to their
    fixed sentences; free text is used verbatim. aspect=auto suppresses the aspect hint.
    """
    options = dict(options or {})
    slots = dict(pack.get("slots") or {})
    src = options.pop("source_note", None) or source_note

    def pick(key, default=None):
        v = options.get(key)
        if v in (None, ""):
            v = slots.get(key, pack.get(key, default))
        return v

    mood = str(pick("mood", "photoreal")).strip()
    mood_words = MOOD_WORDS.get(mood, mood)
    comp_materials, comp_post = MOOD_COMPANION.get(mood, (None, None)) if options.get("mood") else (None, None)

    cam_opt = options.get("camera")
    if isinstance(cam_opt, str) and cam_opt in CAMERA:
        camera_obj, shot = CAMERA[cam_opt]
        shot = options.get("shot_type") or shot
    else:
        camera_obj, shot = pick("camera"), str(pick("shot_type", "exterior view") or "").strip()
    camera = _camera_text(camera_obj)

    mats = options.get("materials")
    if mats in (None, "", []) and comp_materials:
        materials = list(comp_materials)
    else:
        materials = _as_list(pick("materials"))
        if len(materials) == 1 and materials[0] in MATERIALS:
            materials = list(MATERIALS[materials[0]])

    lighting = pick("lighting")
    lighting = LIGHTING.get(str(lighting), lighting) if lighting else None
    season = pick("season_weather")
    season = SEASON.get(str(season), season) if season else None
    entourage = _entourage(pick("entourage"))
    allowed = pack.get("entourage_allowed")
    if allowed is not None:
        allowed_set = {str(a).strip().lower() for a in _as_list(allowed)}
        entourage = [e for e in entourage if e.lower() in allowed_set]
    post = options.get("post") or comp_post or pick("post")
    post = POST.get(str(post), post) if post else None
    keep_fixed = _as_list(options.get("keep_fixed")) or _as_list(pack.get("keep_fixed"))
    negative = pick("negative")
    aspect = options.get("aspect") or pack_aspect(pack)
    if str(aspect).lower() == "auto":
        aspect = None

    lock = [LOCK.format(src=src)]
    if pack.get("geometry_lock"):
        lock.append(_sentence(pack["geometry_lock"]))

    slot_sentences = [f"Produce a {mood_words} of this exact scene: {shot}."]
    if camera:
        slot_sentences.append(_sentence(f"Camera: {camera}"))
    if materials:
        slot_sentences.append(f"Materials: {', '.join(materials)}.")
    if lighting:
        slot_sentences.append(_sentence(f"Lighting: {lighting}"))
    if season:
        slot_sentences.append(_sentence(f"Season and weather: {season}"))
    if entourage:
        slot_sentences.append(f"Entourage: {', '.join(entourage)}.")
    if post:
        slot_sentences.append(_sentence(f"Post-processing: {post}"))
    slot_sentences = slot_sentences[:MAX_SLOT_SENTENCES]

    keeps = [_sentence(k if k.lower().startswith("keep") else f"Keep {k}") for k in keep_fixed]
    tail = []
    if negative:
        tail.append(_sentence(f"Avoid: {negative}"))
    if aspect:
        tail.append(f"Aspect ratio {aspect}.")
    return " ".join(lock + slot_sentences + keeps + tail)


def parse_options(pairs: list[str] | None) -> dict:
    """['k=v', ...] → dict; list keys split on ',' (keep_fixed on ';')."""
    out = {}
    for p in pairs or []:
        if "=" not in p:
            raise SystemExit(f"--option must be k=v, got {p!r}")
        k, v = p.split("=", 1)
        k = k.strip()
        out[k] = _as_list(v) if k in LIST_KEYS else v.strip()
    return out


# ---------------------------------------------------------------- selftest
_SAMPLE_YAML = """
id: t-pack
version: 1.0.0
mood: photoreal   # comment
slots:
  shot_type: "eye-level exterior"
  materials: ["white stucco", 'dark metal roof']
  camera: {lens_mm: 35, height: "eye level", perspective: "straight uprights"}
  lighting: overcast soft daylight
  entourage: [two pedestrians, no cars]
negative: "text, watermark"
entourage_allowed: [two pedestrians, bicycles]
changelog:
  - {date: 2026-09-11, note: "init"}
  - date: 2026-09-14
    note: second
"""


def _selftest() -> int:
    pack = mini_yaml_load(_SAMPLE_YAML)
    assert pack["slots"]["camera"]["lens_mm"] == 35, pack
    assert pack["slots"]["materials"] == ["white stucco", "dark metal roof"], pack
    assert pack["changelog"][1]["note"] == "second", pack["changelog"]
    p = compose(pack, {"aspect": "16:9", "keep_fixed": "the canopies white"})
    assert p.startswith("Use the attached SketchUp image"), p
    assert "Entourage: two pedestrians." in p, p          # "no cars" dropped by whitelist
    assert "Keep the canopies white." in p and p.endswith("Aspect ratio 16:9."), p
    assert "Avoid: text, watermark." in p
    p2 = compose(pack, {"materials": "brick, glass", "lighting": "golden hour"}, "Blender")
    assert "Blender image" in p2 and "Materials: brick, glass." in p2 and "golden hour" in p2
    # OPTIONS.md presets expand; entourage toggles give 4 sentences; aspect_hint fallback; auto suppresses
    pack2 = {"slots": {}, "backends": {"gpt-image": {"aspect_hint": "4:3"}}}
    p3 = compose(pack2, {"lighting": "golden_hour", "materials": "timber_glass", "camera": "drone",
                         "entourage": "people:on,cars:off", "post": "bw", "mood": "clay"})
    assert LIGHTING["golden_hour"] in p3 and "vertical larch cladding" in p3 and "aerial drone photograph" in p3, p3
    assert "no cars" in p3 and "no added furniture" in p3 and POST["bw"] in p3 and "clay-model" in p3, p3
    assert p3.endswith("Aspect ratio 4:3."), p3
    assert "Aspect ratio" not in compose(pack2, {"aspect": "auto"})
    # block list at the same indent as its key must not swallow the following keys (mini parser)
    y = mini_yaml_load("slots:\n  materials:\n  - a\n  - b\n  lighting: x\nsamples:\n- s.png\nchangelog:\n- date: '2026-09-14'\n  note: n\n")
    assert y["slots"] == {"materials": ["a", "b"], "lighting": "x"} and y["changelog"][0]["note"] == "n", y
    print("prompt_compose selftest OK")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pack", help="stylepack id or path to pack.yaml/pack.json")
    ap.add_argument("--option", action="append", default=[], help="k=v override (repeatable)")
    ap.add_argument("--source-note", default="SketchUp")
    ap.add_argument("--print", action="store_true", help="print prompt (default behaviour)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if not a.pack:
        ap.error("--pack required")
    print(compose(load_pack(a.pack), parse_options(a.option), a.source_note))
    return 0


if __name__ == "__main__":
    sys.exit(main())
