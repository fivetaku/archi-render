#!/usr/bin/env python3
"""Compose a render prompt from a stylepack + per-shot options.

Pack files live in ``assets/stylepacks/<id>/pack.yaml`` (schema: 30-docs / design §7).
Loading: ``import yaml`` when available; otherwise a minimal built-in YAML subset parser
(block mappings/lists, quoted scalars, inline ``{}``/``[]``, ``#`` comments). A
``pack.json`` next to (or instead of) ``pack.yaml`` is also accepted and preferred when
PyYAML is missing and the mini parser cannot read the file.

Prompt structure (proven in trial_20260914, merged axes 2026-09-15):
  1. geometry lock sentence(s)
  2. mood + shot type + camera (one sentence; lens_mm/camera_height_m/tilt override preset fields)
  3. materials
  4. lighting  (+ sky + interior_lights merged in; sky clause replaces sky/cloud clauses of the lighting text)
  5. season    (+ vegetation_age merged in)
  6. entourage (+ people_density/people_activity/car_density/car_type merged into the people/cars items)
  7. context   (context + material_wear; only emitted when one of them is set)
  8. grading   (tone + post)
  9. keep_fixed lines, then the references note        10. "Avoid: ..."        11. aspect ratio hint
Slots 2-8 are capped at MAX_SLOT_SENTENCES (7); lock/keep_fixed/references/avoid/aspect are extra.

Precedence per key: explicit --option > pack slot (slots.<key> or top-level <key>) > preset default.
Vocabulary mirrors 20-knowledge/stylepacks/OPTIONS.md; ``--list-options`` prints it as JSON for the webtool.
Entourage whitelist: if the pack defines ``entourage_allowed``, items outside it are dropped.

CLI: python3 scripts/prompt_compose.py --pack <id-or-path> [--option k=v ...] [--print|--json]
     python3 scripts/prompt_compose.py --list-options
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
SKY_CLAUSE_RE = re.compile(r"\b(sky|skies|clouds?|cumulus|cumulonimbus|cloudless)\b", re.I)
INTERIOR_CLAUSE_RE = re.compile(r"\binterior\b.*\blights?\b|\blights?\b.*\binterior\b|\bglazing\b.*\b(lit|dark)\b", re.I)
PEOPLE_ITEM_RE = re.compile(r"\b(people|person|pedestrians?|figures?|crowd)\b", re.I)
PEOPLE_OFF_RE = re.compile(r"\bno (added |additional |extra )?(people|pedestrians|figures)\b", re.I)
CARS_ITEM_RE = re.compile(r"\b(cars?|vehicles?|bicycles?)\b", re.I)
CARS_OFF_RE = re.compile(r"\bno (added |additional |extra )?(cars|vehicles)\b", re.I)

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
    "dawn": "first light 10 minutes after sunrise, sun at 3 degrees elevation camera-right, 2800K, pale pink-grey sky, very long soft shadows stretching left, interior lights on at 2700K",
    "morning_side": "morning sun from camera-right at 30 degrees elevation, 4500K, crisp medium-length shadows raking across the facade to reveal texture, clear sky, interior lights off",
    "afternoon_backlit": "afternoon sun behind the building at 35 degrees elevation, 5000K, facade in open shade with a bright rim of light on roof edges and parapets, shadows stretching toward the camera, no lens flare",
    "night_signs_only": "night, sky #0B1526 with no stars or moon, all interior lights off with glazing reading dark, only sign lights at 3000K and low pathway bollards at 3000K, one cool 4000K street lamp per 15 m, soft shadowless ground",
    "night_full": "night, sky #0B1526 with no stars or moon, every interior light on at 2700K glowing through all glazing, sign lights at 3000K, one cool 4000K street lamp per 15 m, soft shadowless ground",
}
SEASON = {
    "spring": "late spring, fresh mid-green foliage, dry ground, thin high cloud",
    "summer": "early summer, clear sky with a few soft white cumulus, saturated green foliage, dry ground",
    "autumn": "mid autumn, amber and rust foliage on deciduous trees, a few fallen leaves at kerbs, dry ground, clear air",
    "winter": "midwinter, bare deciduous branches, pale low-contrast sky, dry cold ground, no snow",
    "rain": "after rain, puddled and wet-look ground with mirror reflections of lights and sky, dark saturated paving, dramatic broken clouds, no falling rain visible",
    "snow": "midwinter, 3 cm fresh snow on horizontal surfaces only, wet dark asphalt where ploughed, bare branches with snow, light snowfall visible only near the camera",
    "early_spring_blossom": "early spring, cherry and magnolia trees in full pale-pink blossom with a few petals on the paving, lawns just turning green, dry ground, thin high cloud",
    "monsoon_rain": "monsoon downpour, heavy rain falling in visible grey streaks, water sheeting down the glass, gutters overflowing, puddled dark paving with rippled reflections, low uniform grey sky",
    "late_autumn": "late autumn, mostly bare deciduous branches with a few dry brown leaves left, thick leaf litter at kerbs and lawn edges, low pale sun, dry ground",
    "heavy_snow": "midwinter, heavy snowfall, 15 cm of fresh snow on every horizontal surface and roof, flakes falling across the whole frame, snow-laden branches, flat white overcast sky",
    "haze": "fine-dust haze, distant buildings low-contrast and desaturated fading toward the horizon, sky uniform pale grey-beige, soft diffuse light, near facades at full contrast",
    "fog": "dense morning fog, visibility about 80 m, background dissolving to white, soft shadowless light, wet dark paving, drops on railings",
}
PEOPLE_DENSITY = {  # applies only when the people toggle is on
    "none": "no people",
    "sparse": "one or two people",
    "moderate": "five to eight people spread across the drawn walkways and entrance",
    "busy": "a busy crowd of fifteen or more people in groups of three to five",
}
PEOPLE_ACTIVITY = {
    "walking": "walking along the drawn paths, mid-stride",
    "standing_talking": "standing in pairs talking, turned toward each other",
    "seated": "seated on the drawn benches, steps and terraces",
    "mixed": "in a mix of walking, standing in conversation and sitting",
}
CAR_DENSITY = {
    "none": "no cars",
    "few": "one to three cars parked in the drawn bays with the remaining bays empty",
    "full": "a car in every drawn parking bay",
}
CAR_TYPE = {
    "passenger": "passenger cars only, sedans and compact SUVs in white, grey and black",
    "mixed_commercial": "a mix of passenger cars and one delivery van or small box truck",
    "bicycles_only": "bicycles only in the drawn racks, no motor vehicles",
}
VEGETATION_AGE = {
    "young": "newly planted 2 m saplings with timber stakes and ties, thin open canopies, bare mulch beds",
    "mature": "mature trees with 8 to 10 m canopies casting broad soft shade, established clipped shrubs",
    "lush": "lush planting with a dense understory of ferns and grasses, climbers on walls and pergolas, mature 8 to 10 m canopies",
}
SKY = {
    "clear": "clear cloudless sky",
    "scattered_cumulus": "sky with scattered soft white cumulus covering about a third of it",
    "overcast": "uniformly overcast grey-white sky with no visible sun disc",
    "dramatic": "towering cumulonimbus with dark grey bases and sunlit white tops, sun breaking through gaps in distinct shafts",
    "haze": "hazy pale grey-beige sky with no cloud detail and a low-contrast horizon",
}
CONTEXT = {
    "as_drawn": "Do not add surroundings beyond what is drawn",
    "urban_dense": "dense urban surroundings, 5 to 8 storey neighbouring buildings tight to the site boundary, street with kerbs, lamp posts and parked cars beyond the site",
    "suburban": "suburban surroundings, two-storey houses with front gardens set back across the street, hedges and evenly spaced street trees",
    "rural": "rural surroundings, open fields and a low tree line at the horizon, gravel access track, no neighbouring buildings",
    "waterfront": "waterfront setting, calm water along one edge of the site with a timber boardwalk and mirror reflections of the building",
    "forest": "forest surroundings, dense pine and deciduous trees 15 to 20 m tall closing in at the site edge, dappled light on the ground",
}
MATERIAL_WEAR = {
    "new": "all materials brand new, clean and unweathered, crisp edges and unmarked paving",
    "lived_in": "materials lightly lived-in, faint staining under window sills, gentle patina on metal, clean glass",
    "weathered": "weathered materials, dark streaking below sills and copings, moss and algae at grade, faded chalky paint and rust bloom on steel fixings",
}
INTERIOR_LIGHTS = {
    "off": "all interior lights off, glazing reflecting the sky only",
    "partial": "interior lights on at 2700K in about half the rooms, the rest dark",
    "all_on": "every interior light on at 2700K glowing through all glazing",
}
TONE = {
    "editorial_magazine": "editorial architecture-magazine photograph, single considered frame, restrained composition, true-to-life color",
    "real_estate_ad": "real-estate listing photograph, brightly and evenly exposed, open shadows, clean blue sky, entrance clearly readable",
    "competition_panel": "competition-panel render, slightly desaturated palette, clean edges, uncluttered foreground, emphasis on the building silhouette",
    "documentary": "documentary photograph, available light only, no staging, natural imperfections and everyday clutter kept",
}
TILT = {
    "level": "camera level, straight vertical uprights, no keystoning",
    "slight_up": "camera pitched up about 5 degrees, verticals converging slightly toward the top",
    "slight_down": "camera pitched down about 5 degrees, horizon in the upper third of the frame",
}
REFERENCES_NOTE = "Match the attached reference images for materials and mood."
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


def _drop_clauses(text: str, pattern: re.Pattern) -> str:
    """Remove comma-separated clauses of `text` that match `pattern` (used when sky/interior override)."""
    kept = [c for c in re.split(r",\s*", str(text)) if not pattern.search(c)]
    return ", ".join(c.strip() for c in kept if c.strip()).rstrip(" ,")


def _lookup(table: dict, value):
    """Preset name → fixed sentence; unknown values pass through as free text; empty → None."""
    if value in (None, "", []):
        return None
    v = str(value).strip()
    return table.get(v, v)


def _people_phrase(density, activity) -> str | None:
    d, a = _lookup(PEOPLE_DENSITY, density), _lookup(PEOPLE_ACTIVITY, activity)
    if d == PEOPLE_DENSITY["none"]:
        return d
    if d and a:
        return f"{d} {a}, realistic everyday clothing"
    if d:
        return f"{d} in the drawn positions, realistic everyday clothing"
    if a:
        return f"people kept in the drawn positions {a}, realistic everyday clothing"
    return None


def _cars_phrase(density, ctype) -> str | None:
    d, t = _lookup(CAR_DENSITY, density), _lookup(CAR_TYPE, ctype)
    if d == CAR_DENSITY["none"]:
        return d
    if t == CAR_TYPE["bicycles_only"]:
        return t
    if d and t:
        return f"{d}, {t}"
    if d:
        return d
    if t:
        return f"real cars only in the drawn parking bays or lanes, {t}"
    return None


def _merge_entourage(items: list[str], people_phrase, cars_phrase, cars_requested: bool) -> list[str]:
    """Replace the people / cars items of an entourage list with the merged phrases.

    people options apply only when people are on (no "no people" item); if no people item exists the phrase
    is appended. cars: car_density is an explicit override of a "no cars" item; car_type alone is ignored
    when cars are off.
    """
    out = list(items)
    people_on = not any(PEOPLE_OFF_RE.search(i) for i in out)
    if people_phrase and people_on:
        idx = [i for i, it in enumerate(out) if PEOPLE_ITEM_RE.search(it)]
        if idx:
            out[idx[0]] = people_phrase
            for i in reversed(idx[1:]):
                del out[i]
        else:
            out.append(people_phrase)
    cars_on = not any(CARS_OFF_RE.search(i) for i in out)
    if cars_phrase and (cars_on or cars_requested):
        idx = [i for i, it in enumerate(out) if CARS_ITEM_RE.search(it)]
        if idx:
            out[idx[0]] = cars_phrase
            for i in reversed(idx[1:]):
                del out[i]
        else:
            out.append(cars_phrase)
    return out


def _apply_camera_overrides(camera_obj, options: dict):
    """lens_mm / camera_height_m / tilt override the matching camera preset fields."""
    lens, height, tilt = options.get("lens_mm"), options.get("camera_height_m"), options.get("tilt")
    if not any(v not in (None, "") for v in (lens, height, tilt)):
        return camera_obj
    cam = dict(camera_obj) if isinstance(camera_obj, dict) else {"perspective": str(camera_obj or "").strip() or None}
    if lens not in (None, ""):
        cam["lens_mm"] = int(float(lens))
    if height not in (None, ""):
        h = float(height)
        cam["height"] = f"{h:g} m"
    if tilt not in (None, ""):
        cam["perspective"] = _lookup(TILT, tilt)
    return cam


def compose_parts(pack: dict, options: dict, source_note: str = "SketchUp") -> dict:
    """Compose and return the prompt in parts: {lock:[], slots:[], keeps:[], tail:[], prompt:str}.

    Option values may be OPTIONS.md preset names (lighting=golden_hour, materials=timber_glass,
    camera=drone, entourage=people:on,cars:off, post=bw, sky=dramatic ...) or free text. Presets expand
    to their fixed sentences; free text is used verbatim. aspect=auto suppresses the aspect hint.
    Precedence per key: explicit option > pack slot > preset default.
    """
    options = dict(options or {})
    slots = dict(pack.get("slots") or {})
    src = options.pop("source_note", None) or source_note

    def pick(key, default=None):
        v = options.get(key)
        if v in (None, "", []):
            v = slots.get(key, pack.get(key, default))
        return v

    mood = str(pick("mood", "photoreal")).strip()
    mood_words = MOOD_WORDS.get(mood, mood)
    comp_materials, comp_post = MOOD_COMPANION.get(mood, (None, None)) if options.get("mood") else (None, None)

    # 2. shot + camera (one sentence)
    cam_opt = options.get("camera")
    if isinstance(cam_opt, str) and cam_opt in CAMERA:
        camera_obj, shot = CAMERA[cam_opt]
        shot = options.get("shot_type") or shot
    else:
        camera_obj, shot = pick("camera"), str(pick("shot_type", "exterior view") or "").strip()
    camera = _camera_text(_apply_camera_overrides(camera_obj, {k: pick(k) for k in ("lens_mm", "camera_height_m", "tilt")}))

    # 3. materials
    mats = options.get("materials")
    if mats in (None, "", []) and comp_materials:
        materials = list(comp_materials)
    else:
        materials = _as_list(pick("materials"))
        if len(materials) == 1 and materials[0] in MATERIALS:
            materials = list(MATERIALS[materials[0]])

    # 4. lighting + sky + interior_lights
    lighting = _lookup(LIGHTING, pick("lighting"))
    sky = _lookup(SKY, pick("sky"))
    interior = _lookup(INTERIOR_LIGHTS, pick("interior_lights"))
    if lighting and sky:
        lighting = _drop_clauses(lighting, SKY_CLAUSE_RE)          # sky option overrides the sky part of lighting
    if lighting and interior:
        lighting = _drop_clauses(lighting, INTERIOR_CLAUSE_RE)
    lighting_bits = [b for b in (lighting, sky, interior) if b]

    # 5. season + vegetation_age
    season = _lookup(SEASON, pick("season_weather"))
    if season and sky:
        season = _drop_clauses(season, SKY_CLAUSE_RE) or None      # sky option also wins over season's sky clause
    veg = _lookup(VEGETATION_AGE, pick("vegetation_age"))
    season_bits = [b for b in (season, veg) if b]

    # 6. entourage + people/cars axes
    entourage = _entourage(pick("entourage"))
    people_phrase = _people_phrase(pick("people_density"), pick("people_activity"))
    cars_phrase = _cars_phrase(pick("car_density"), pick("car_type"))
    if people_phrase or cars_phrase:
        entourage = _merge_entourage(entourage, people_phrase, cars_phrase, pick("car_density") not in (None, ""))
    allowed = pack.get("entourage_allowed")
    if allowed is not None:
        allowed_set = {str(a).strip().lower() for a in _as_list(allowed)}
        entourage = [e for e in entourage if e.lower() in allowed_set or e in (people_phrase, cars_phrase)]

    # 7. context + material_wear (emitted only when set; implicit default as_drawn stays silent)
    context = _lookup(CONTEXT, pick("context"))
    wear = _lookup(MATERIAL_WEAR, pick("material_wear"))
    if wear and not context:
        context = CONTEXT["as_drawn"]
    context_bits = [b for b in (context, wear) if b]

    # 8. grading = tone + post
    post = options.get("post") or comp_post or pick("post")
    post = _lookup(POST, post)
    tone = _lookup(TONE, pick("tone"))
    grading_bits = [b for b in (tone, post) if b]

    keep_fixed = _as_list(options.get("keep_fixed")) or _as_list(pack.get("keep_fixed"))
    references = _as_list(options.get("references")) or _as_list(pack.get("references"))
    negative = pick("negative")
    aspect = options.get("aspect") or pack_aspect(pack)
    if str(aspect).lower() == "auto":
        aspect = None

    lock = [LOCK.format(src=src)]
    if pack.get("geometry_lock"):
        lock.append(_sentence(pack["geometry_lock"]))

    shot_sentence = f"Produce a {mood_words} of this exact scene: {shot}"
    if camera:
        shot_sentence += f"; camera {camera}"
    slot_sentences = [_sentence(shot_sentence)]
    if materials:
        slot_sentences.append(f"Materials: {', '.join(materials)}.")
    if lighting_bits:
        slot_sentences.append(_sentence("Lighting: " + "; ".join(lighting_bits)))
    if season_bits:
        slot_sentences.append(_sentence("Season and weather: " + "; ".join(season_bits)))
    if entourage:
        slot_sentences.append(_sentence("Entourage: " + "; ".join(entourage)))
    if context_bits:
        slot_sentences.append(_sentence("Context: " + "; ".join(context_bits)))
    if grading_bits:
        slot_sentences.append(_sentence("Post-processing: " + "; ".join(grading_bits)))
    slot_sentences = slot_sentences[:MAX_SLOT_SENTENCES]

    keeps = [_sentence(k if k.lower().startswith("keep") else f"Keep {k}") for k in keep_fixed]
    if references:
        keeps.append(REFERENCES_NOTE)
    tail = []
    if negative:
        tail.append(_sentence(f"Avoid: {negative}"))
    if aspect:
        tail.append(f"Aspect ratio {aspect}.")
    return {"lock": lock, "slots": slot_sentences, "keeps": keeps, "tail": tail,
            "prompt": " ".join(lock + slot_sentences + keeps + tail)}


def compose(pack: dict, options: dict, source_note: str = "SketchUp") -> str:
    """Return the final prompt string for one render (see compose_parts)."""
    return compose_parts(pack, options, source_note)["prompt"]


# ---------------------------------------------------------------- vocabulary export
def list_options() -> dict:
    """Vocabulary as JSON-able dict (webtool syncs from this). enum keys carry `values`; free keys carry `type`."""
    enum = lambda table, **kw: {"type": "enum", "values": list(table), **kw}  # noqa: E731
    opts = {
        "mood": enum(MOOD_WORDS, companion=list(MOOD_COMPANION)),
        "lighting": enum(LIGHTING, merged_into="lighting"),
        "sky": enum(SKY, merged_into="lighting", note="overrides sky/cloud clauses of lighting and season text"),
        "interior_lights": enum(INTERIOR_LIGHTS, merged_into="lighting"),
        "season_weather": enum(SEASON, merged_into="season"),
        "vegetation_age": enum(VEGETATION_AGE, merged_into="season"),
        "camera": enum(CAMERA, merged_into="shot"),
        "lens_mm": {"type": "int", "merged_into": "shot", "overrides": "camera.lens_mm"},
        "camera_height_m": {"type": "float", "merged_into": "shot", "overrides": "camera.height"},
        "tilt": enum(TILT, merged_into="shot", overrides="camera.perspective"),
        "materials": {"type": "enum_or_list", "values": list(MATERIALS), "sep": ","},
        "entourage": {"type": "toggles", "values": list(ENTOURAGE_TOGGLES), "format": "people:on,cars:off,..."},
        "people_density": enum(PEOPLE_DENSITY, merged_into="entourage", requires="entourage.people=on"),
        "people_activity": enum(PEOPLE_ACTIVITY, merged_into="entourage", requires="entourage.people=on"),
        "car_density": enum(CAR_DENSITY, merged_into="entourage"),
        "car_type": enum(CAR_TYPE, merged_into="entourage"),
        "context": enum(CONTEXT, merged_into="context", default="as_drawn"),
        "material_wear": enum(MATERIAL_WEAR, merged_into="context"),
        "tone": enum(TONE, merged_into="grading"),
        "post": enum(POST, merged_into="grading"),
        "keep_fixed": {"type": "text_list", "sep": ";"},
        "references": {"type": "path_list", "sep": ","},
        "aspect": {"type": "enum", "values": ["4:3", "16:9", "3:2", "1:1", "2:1", "auto"]},
    }
    return {
        "source": "20-knowledge/stylepacks/OPTIONS.md",
        "max_slot_sentences": MAX_SLOT_SENTENCES,
        "precedence": "explicit option > pack slot > preset default",
        "slots_order": ["shot", "materials", "lighting", "season", "entourage", "context", "grading"],
        "options": opts,
        "values": {k: v["values"] for k, v in opts.items() if "values" in v},
        "free": {k: v["type"] for k, v in opts.items() if "values" not in v},
    }


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
    # merged axes: maximal option set stays within the slot cap and every merged axis lands in its sentence
    pack3 = {"slots": {"shot_type": "eye-level exterior", "lighting": LIGHTING["golden_hour"],
                       "season_weather": SEASON["summer"],
                       "entourage": ["two people seated on the balcony", "no cars", "existing trees kept"],
                       "post": POST["neutral"]}, "negative": "text"}
    maximal = {"people_density": "busy", "people_activity": "mixed", "car_density": "few", "car_type": "passenger",
               "sky": "dramatic", "vegetation_age": "mature", "context": "urban_dense", "material_wear": "lived_in",
               "interior_lights": "all_on", "tone": "editorial_magazine", "lens_mm": "50", "camera_height_m": "2.5",
               "tilt": "slight_up", "materials": "timber_glass", "references": "refs/a.jpg"}
    parts = compose_parts(pack3, maximal)
    s = parts["slots"]
    assert len(s) <= MAX_SLOT_SENTENCES and len(s) == 7, s
    assert s[0].startswith("Produce a") and "50mm lens" in s[0] and "2.5 m camera height" in s[0] and "pitched up" in s[0], s[0]
    assert s[2].startswith("Lighting:") and SKY["dramatic"] in s[2] and INTERIOR_LIGHTS["all_on"] in s[2], s[2]
    assert "cumulus" not in s[2].split(SKY["dramatic"])[0] and "interior lights on at 2700K" not in s[2], s[2]
    assert s[3].startswith("Season and weather:") and VEGETATION_AGE["mature"] in s[3] and "cumulus" not in s[3], s[3]
    assert s[4].startswith("Entourage:") and "fifteen or more" in s[4] and "one to three cars" in s[4] and "no cars" not in s[4], s[4]
    assert "existing trees kept" in s[4] and s[4].count("people") == 1, s[4]
    assert s[5].startswith("Context:") and CONTEXT["urban_dense"] in s[5] and MATERIAL_WEAR["lived_in"] in s[5], s[5]
    assert s[6].startswith("Post-processing:") and TONE["editorial_magazine"] in s[6] and POST["neutral"] in s[6], s[6]
    assert REFERENCES_NOTE in parts["keeps"] and parts["prompt"].endswith("Avoid: text."), parts
    # people axes are ignored when the people toggle is off; car_density overrides "no cars"; as_drawn sentence
    p4 = compose_parts(pack3, {"entourage": "people:off,cars:off", "people_density": "busy", "car_density": "full"})["slots"]
    ent = [x for x in p4 if x.startswith("Entourage:")][0]
    assert "no people" in ent and "fifteen" not in ent and CAR_DENSITY["full"] in ent, ent
    p5 = compose_parts(pack3, {"context": "as_drawn"})["slots"]
    assert "Context: Do not add surroundings beyond what is drawn." in p5, p5
    assert not any(x.startswith("Context:") for x in compose_parts(pack3, {})["slots"])   # implicit default is silent
    lo = list_options()
    assert len(lo["options"]) >= 20 and set(lo["values"]) | set(lo["free"]) == set(lo["options"]), lo
    json.dumps(lo)
    print("prompt_compose selftest OK")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pack", help="stylepack id or path to pack.yaml/pack.json")
    ap.add_argument("--option", action="append", default=[], help="k=v override (repeatable)")
    ap.add_argument("--source-note", default="SketchUp")
    ap.add_argument("--print", action="store_true", help="print prompt (default behaviour)")
    ap.add_argument("--json", action="store_true", help="print prompt parts as JSON (lock/slots/keeps/tail/prompt)")
    ap.add_argument("--list-options", action="store_true", help="print the option vocabulary as JSON and exit")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if a.list_options:
        print(json.dumps(list_options(), ensure_ascii=False, indent=2))
        return 0
    if not a.pack:
        ap.error("--pack required")
    parts = compose_parts(load_pack(a.pack), parse_options(a.option), a.source_note)
    print(json.dumps(parts, ensure_ascii=False, indent=2) if a.json else parts["prompt"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
