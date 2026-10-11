#!/usr/bin/env python3
"""archi-render local web tool — stdlib-only HTTP server.

Serves webtool/static/ plus read-only renders/ and assets/, and wraps the
scripts/ pipeline (prompt_compose.py, render.py) behind a small JSON API.

Run:  python3 webtool/server.py [--port 8765] [--root <workspace>] [--stub]
Open: http://127.0.0.1:8765
"""
import argparse
import base64
import json
import mimetypes
import os
import re
import struct
import subprocess
import sys
import time
import zlib
from datetime import date
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")
ROOT = os.path.dirname(HERE)          # overridden by --root
SCRIPTS_DIR = None                    # ROOT/scripts or webtool/stubs (--stub)
RENDER_TIMEOUT = 600                  # seconds; render is synchronous
COMPOSE_TIMEOUT = 30
SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
IMG_EXT = {"png", "jpg", "jpeg", "webp"}
REF_EXT = IMG_EXT | {"gif"}
MAX_REFS = 8                          # references per shot (refs/ref-<n>.<ext>)

# Option vocabulary fallback — used when `prompt_compose.py --list-options` is missing or fails.
# Source of truth: 20-knowledge/stylepacks/OPTIONS.md (keep in sync). Value order = UI order.
FALLBACK_OPTIONS = {
    "mood": ["photoreal", "cinematic", "clay", "watercolor", "diagram"],
    "tone": ["editorial_magazine", "real_estate_ad", "competition_panel", "documentary"],
    "post": ["neutral", "teal_orange", "warm_film", "bw"],
    "lighting": ["overcast", "midday", "golden_hour", "dusk", "night", "blue_hour",
                 "dawn", "morning_side", "afternoon_backlit", "night_signs_only", "night_full"],
    "sky": ["clear", "scattered_cumulus", "overcast", "dramatic", "haze"],
    "interior_lights": ["off", "partial", "all_on"],
    "season_weather": ["spring", "summer", "autumn", "winter", "rain", "snow",
                       "early_spring_blossom", "monsoon_rain", "late_autumn", "heavy_snow", "haze", "fog"],
    "vegetation_age": ["young", "mature", "lush"],
    "entourage": ["people", "cars", "vegetation", "furniture"],
    "people_density": ["none", "sparse", "moderate", "busy"],
    "people_activity": ["walking", "standing_talking", "seated", "mixed"],
    "car_density": ["none", "few", "full"],
    "car_type": ["passenger", "mixed_commercial", "bicycles_only"],
    "camera": ["eye_level", "elevated", "drone", "interior"],
    "lens_mm": [],
    "camera_height_m": [],
    "tilt": ["level", "slight_up", "slight_down"],
    "aspect": ["auto", "4:3", "16:9", "3:2", "1:1", "2:1"],
    "context": ["as_drawn", "urban_dense", "suburban", "rural", "waterfront", "forest"],
    "materials": ["white_stucco_oak", "board_formed_concrete", "brick_dark_metal", "timber_glass", "clay_massing"],
    "material_wear": ["new", "lived_in", "weathered"],
    "keep_fixed": [],
    "references": [],
}
FALLBACK_TYPES = {"lens_mm": "number", "camera_height_m": "number", "keep_fixed": "free",
                  "references": "files", "entourage": "toggles"}


# ---------------------------------------------------------------- helpers
def p(*parts):
    return os.path.join(ROOT, *parts)


def safe_id(value, field):
    if not isinstance(value, str) or not SAFE_ID.match(value) or value in (".", ".."):
        raise ApiError(400, f"invalid {field}: {value!r}")
    return value


class ApiError(Exception):
    def __init__(self, status, message, **extra):
        super().__init__(message)
        self.status, self.message, self.extra = status, message, extra


def script(name):
    path = os.path.join(SCRIPTS_DIR, name)
    if not os.path.isfile(path):
        raise ApiError(503, f"{name} not found — scripts layer not installed yet",
                       expected_path=path)
    return path


def run_script(args, timeout):
    """Run a pipeline script; return (stdout, stderr). Raises ApiError on failure."""
    try:
        proc = subprocess.run([sys.executable] + args, cwd=ROOT, capture_output=True,
                              text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise ApiError(504, f"script timed out after {timeout}s", cmd=args)
    if proc.returncode != 0:
        raise ApiError(502, "script failed", cmd=args, returncode=proc.returncode,
                       stderr=proc.stderr[-4000:], stdout=proc.stdout[-2000:])
    return proc.stdout, proc.stderr


def option_args(options):
    """Translate the UI options dict into repeated --option k=v flags."""
    args = []
    for key, val in (options or {}).items():
        if val is None or val == "" or val is False:
            continue
        key = safe_id(str(key), "option key")
        if isinstance(val, bool):
            val = "true"
        elif isinstance(val, (list, tuple)):
            val = ",".join(str(v) for v in val)
        args += ["--option", f"{key}={val}"]
    return args


def last_json_line(stdout):
    for line in reversed(stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    raise ApiError(502, "render.py printed no JSON line", stdout=stdout[-2000:])


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return default


def url_for(abs_path):
    """Map an absolute path inside ROOT to a served URL (renders/ or assets/)."""
    rel = os.path.relpath(abs_path, ROOT).replace(os.sep, "/")
    return "/" + rel if rel.startswith(("renders/", "assets/")) else None


def find_render_image(rev_dir):
    for name in ("render.png", "render.jpg", "render.jpeg", "render.webp"):
        if os.path.isfile(os.path.join(rev_dir, name)):
            return os.path.join(rev_dir, name)
    return None


def find_capture(project, shot):
    d = p("assets", "captures", project, shot)
    if os.path.isdir(d):
        for name in sorted(os.listdir(d)):
            if name.startswith("capture.") and name.rsplit(".", 1)[-1].lower() in IMG_EXT:
                return os.path.join(d, name)
    return None


def decode_data(data):
    """Accept raw base64 or a data: URL; return (bytes, mime or None)."""
    mime = None
    if isinstance(data, str) and data.startswith("data:"):
        head, _, data = data.partition(",")
        mime = head[5:].split(";")[0] or None
    try:
        return base64.b64decode(data, validate=False), mime
    except (ValueError, TypeError):
        raise ApiError(400, "invalid base64 payload")


def png_to_gray(raw, threshold=127):
    """Re-encode any 8-bit non-interlaced PNG (gray/RGB/RGBA/gray+alpha) as 8-bit grayscale,
    thresholded to hard 0/255 (internal mask standard: 255 = editable). stdlib only."""
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ApiError(400, "mask must be a PNG")
    pos, idat, ihdr = 8, [], None
    while pos + 8 <= len(raw):
        length, ctype = struct.unpack(">I4s", raw[pos:pos + 8])
        data = raw[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", data)
        elif ctype == b"IDAT":
            idat.append(data)
        elif ctype == b"IEND":
            break
        pos += 12 + length
    if not ihdr or not idat:
        raise ApiError(400, "malformed PNG mask")
    w, h, depth, color, _, _, interlace = ihdr
    channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(color)
    if depth != 8 or channels is None or interlace:
        raise ApiError(400, f"unsupported mask PNG (depth={depth}, color={color}, interlace={interlace})")
    stride = w * channels
    src = zlib.decompress(b"".join(idat))
    prev = bytearray(stride)
    gray_rows = []
    for y in range(h):
        off = y * (stride + 1)
        ftype, line = src[off], bytearray(src[off + 1:off + 1 + stride])
        for i in range(stride):                       # PNG filter reconstruction
            a = line[i - channels] if i >= channels else 0
            b = prev[i]
            c = prev[i - channels] if i >= channels else 0
            if ftype == 1: line[i] = (line[i] + a) & 255
            elif ftype == 2: line[i] = (line[i] + b) & 255
            elif ftype == 3: line[i] = (line[i] + (a + b) // 2) & 255
            elif ftype == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = line
        gray_rows.append(b"\x00" + bytes(255 if line[i] > threshold else 0 for i in range(0, stride, channels)))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"".join(gray_rows), 6)) + chunk(b"IEND", b""))


# ---------------------------------------------------------------- API handlers
def api_packs(_q, _body):
    base = p("assets", "stylepacks")
    out = []
    if not os.path.isdir(base):
        return out
    for pid in sorted(os.listdir(base)):
        pack = read_json(os.path.join(base, pid, "pack.json"))
        if not pack:
            continue
        sample = None
        for s in pack.get("samples") or []:
            cand = s if isinstance(s, str) else (s or {}).get("path") or (s or {}).get("file")
            if not cand:
                continue
            abs_s = cand if os.path.isabs(cand) else os.path.join(base, pid, cand)
            if not os.path.isfile(abs_s):
                abs_s = p(cand)
            if os.path.isfile(abs_s):
                sample = url_for(abs_s)
                break
        out.append({"id": pack.get("id", pid), "name": pack.get("name", pid),
                    "mood": pack.get("mood"), "sample": sample,
                    "slots": pack.get("slots") or {}})
    return out


def api_upload(_q, body):
    project = safe_id(body.get("project"), "project")
    shot = safe_id(body.get("shot"), "shot")
    raw, mime = decode_data(body.get("data", ""))
    if not raw:
        raise ApiError(400, "empty upload")
    ext = (body.get("ext") or (mimetypes.guess_extension(mime or "") or "").lstrip(".")
           or "png").lower()
    if ext == "jpe":
        ext = "jpg"
    if ext not in IMG_EXT:
        raise ApiError(400, f"unsupported image type: {ext}")
    d = p("assets", "captures", project, shot)
    os.makedirs(d, exist_ok=True)
    for old in os.listdir(d):                       # one capture per shot
        if old.startswith("capture."):
            os.remove(os.path.join(d, old))
    path = os.path.join(d, f"capture.{ext}")
    with open(path, "wb") as fh:
        fh.write(raw)
    return {"path": os.path.relpath(path, ROOT), "url": url_for(path), "size": len(raw)}


def _normalize_options(raw):
    """Accept the shapes `--list-options` may print and return
    {options: {key: {values: [...], type: enum|number|free|files|toggles}}, sentences: {key: {value: text}}}."""
    if not isinstance(raw, dict):
        raise ValueError("options JSON must be an object")
    body = raw.get("options") if isinstance(raw.get("options"), dict) else raw
    sentences = raw.get("sentences") if isinstance(raw.get("sentences"), dict) else {}
    flagged = {}
    for flag, typ in (("free_text", "free"), ("free", "free"), ("numeric", "number"), ("number", "number"),
                      ("files", "files"), ("toggles", "toggles")):
        for k in raw.get(flag) or []:
            flagged[str(k)] = typ
    out = {}
    for key, spec in body.items():
        if key in ("sentences", "free_text", "free", "numeric", "number", "files", "toggles"):
            continue
        typ, values = None, []
        if isinstance(spec, dict):
            values = spec.get("values") or spec.get("choices") or []
            typ = spec.get("type") or spec.get("kind")
            if isinstance(spec.get("sentences"), dict):
                sentences.setdefault(key, {}).update(spec["sentences"])
            if spec.get("free") or spec.get("free_text"):
                typ = typ or "free"
            if spec.get("numeric") or spec.get("number"):
                typ = typ or "number"
        elif isinstance(spec, list):
            values = spec
        elif isinstance(spec, str):
            typ = spec
        typ = flagged.get(key) or typ or FALLBACK_TYPES.get(key) or ("enum" if values else "free")
        if typ in ("string", "text"):
            typ = "free"
        if typ in ("int", "float", "numeric"):
            typ = "number"
        out[key] = {"values": [str(v) for v in values], "type": typ}
    return {"options": out, "sentences": sentences}


def api_options(_q, _body):
    """Option vocabulary for the panel. Real: prompt_compose.py --list-options; else built-in fallback."""
    try:
        stdout, _ = run_script([script("prompt_compose.py"), "--list-options"], COMPOSE_TIMEOUT)
        norm = _normalize_options(json.loads(stdout.strip() or "{}"))
        if not norm["options"]:
            raise ValueError("empty option list")
        norm["source"] = "prompt_compose"
        return norm
    except (ApiError, ValueError, json.JSONDecodeError) as e:
        norm = _normalize_options(dict(FALLBACK_OPTIONS))
        norm["source"] = "fallback"
        norm["fallback_reason"] = getattr(e, "message", None) or str(e)
        return norm


def list_refs(project, shot):
    d = p("assets", "captures", project, shot, "refs")
    out = []
    if os.path.isdir(d):
        for name in sorted(os.listdir(d)):
            if name.startswith("ref-") and name.rsplit(".", 1)[-1].lower() in REF_EXT:
                full = os.path.join(d, name)
                out.append({"path": os.path.relpath(full, ROOT), "url": url_for(full), "name": name})
    return out


def api_upload_ref(_q, body):
    """Attach a reference image: assets/captures/<P>/<S>/refs/ref-<n>.<ext>. Returns the new ref + full list."""
    project = safe_id(body.get("project"), "project")
    shot = safe_id(body.get("shot"), "shot")
    raw, mime = decode_data(body.get("data", ""))
    if not raw:
        raise ApiError(400, "empty upload")
    ext = (body.get("ext") or (mimetypes.guess_extension(mime or "") or "").lstrip(".") or "png").lower()
    if ext == "jpe":
        ext = "jpg"
    if ext not in REF_EXT:
        raise ApiError(400, f"unsupported reference type: {ext}")
    d = p("assets", "captures", project, shot, "refs")
    os.makedirs(d, exist_ok=True)
    existing = list_refs(project, shot)
    if len(existing) >= MAX_REFS:
        raise ApiError(400, f"at most {MAX_REFS} references per shot", refs=existing)
    n = 1
    while any(r["name"].startswith(f"ref-{n}.") for r in existing):
        n += 1
    path = os.path.join(d, f"ref-{n}.{ext}")
    with open(path, "wb") as fh:
        fh.write(raw)
    return {"path": os.path.relpath(path, ROOT), "url": url_for(path), "size": len(raw), "n": n,
            "refs": list_refs(project, shot)}


def api_ref_delete(_q, body):
    project = safe_id(body.get("project"), "project")
    shot = safe_id(body.get("shot"), "shot")
    name = safe_id(body.get("name"), "name")
    if not name.startswith("ref-"):
        raise ApiError(400, "not a reference file")
    full = p("assets", "captures", project, shot, "refs", name)
    if os.path.isfile(full):
        os.remove(full)
    return {"refs": list_refs(project, shot)}


def api_options(_q, _body):
    """Option schema from `prompt_compose.py --list-options` (values/options/free/slots_order)."""
    stdout, _ = run_script([script("prompt_compose.py"), "--list-options"], COMPOSE_TIMEOUT)
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        raise ApiError(502, "--list-options did not print JSON", stdout=stdout[-1000:])


def api_compose(_q, body):
    pack = safe_id(body.get("pack"), "pack")
    args = [script("prompt_compose.py"), "--pack", pack] + option_args(body.get("options")) + ["--print"]
    stdout, _ = run_script(args, COMPOSE_TIMEOUT)
    return {"prompt": stdout.strip()}


def api_render(_q, body):
    project = safe_id(body.get("project"), "project")
    shot = safe_id(body.get("shot"), "shot")
    pack = safe_id(body.get("pack"), "pack")
    backend = body.get("backend") or "gpt"
    if backend not in ("gpt", "grok"):
        raise ApiError(400, "backend must be gpt|grok")
    capture = find_capture(project, shot)
    if not capture:
        raise ApiError(400, "no capture uploaded for this project/shot")
    args = [script("render.py"), "--input", capture, "--project", project, "--shot", shot,
            "--pack", pack, "--backend", backend] + option_args(body.get("options"))
    aspect = body.get("aspect")
    if aspect and aspect != "auto":
        if not re.match(r"^\d+:\d+$", aspect):
            raise ApiError(400, "aspect must look like 16:9")
        args += ["--aspect", aspect]
    t0 = time.time()
    stdout, stderr = run_script(args, RENDER_TIMEOUT)
    result = last_json_line(stdout)
    result.setdefault("elapsed_s", round(time.time() - t0, 1))
    result["url"] = _result_url(project, shot, result)
    result["log"] = stderr[-2000:]
    return result


def _result_url(project, shot, result):
    path = result.get("path")
    if path:
        abs_path = path if os.path.isabs(path) else p(path)
        if os.path.isfile(abs_path):
            return url_for(abs_path)
    rev = result.get("revision")
    if rev:
        img = find_render_image(p("renders", project, shot, rev))
        if img:
            return url_for(img)
    return None


def api_fix(_q, body):
    project = safe_id(body.get("project"), "project")
    shot = safe_id(body.get("shot"), "shot")
    base_rev = safe_id(body.get("base"), "base")
    instruction = (body.get("instruction") or "").strip()
    if not instruction:
        raise ApiError(400, "instruction is required")
    backend = body.get("backend") or "grok"
    if backend not in ("gpt", "grok"):
        raise ApiError(400, "backend must be gpt|grok")
    rev_dir = p("renders", project, shot, base_rev)
    if not os.path.isdir(rev_dir):
        raise ApiError(404, f"base revision not found: {base_rev}")
    raw, _ = decode_data(body.get("mask_png_base64", ""))
    raw = png_to_gray(raw)                               # normalise to internal standard: 8-bit L, 255 = edit
    n = 1
    while os.path.exists(os.path.join(rev_dir, f"mask_{n}.png")):
        n += 1
    mask_path = os.path.join(rev_dir, f"mask_{n}.png")
    with open(mask_path, "wb") as fh:
        fh.write(raw)
    args = [script("render.py"), "fix", "--project", project, "--shot", shot, "--base", base_rev,
            "--mask", mask_path, "--instruction", instruction, "--backend", backend]
    t0 = time.time()
    stdout, stderr = run_script(args, RENDER_TIMEOUT)
    result = last_json_line(stdout)
    result.setdefault("elapsed_s", round(time.time() - t0, 1))
    result["mask"] = os.path.relpath(mask_path, ROOT)
    result["url"] = _result_url(project, shot, result)
    result["log"] = stderr[-2000:]
    return result


def api_revisions(q, _body):
    project = safe_id((q.get("project") or [""])[0], "project")
    shot = safe_id((q.get("shot") or [""])[0], "shot")
    base = p("renders", project, shot)
    out = []
    if os.path.isdir(base):
        for rev in sorted(os.listdir(base)):
            rev_dir = os.path.join(base, rev)
            img = find_render_image(rev_dir)
            if not os.path.isdir(rev_dir) or not img:
                continue
            meta = read_json(os.path.join(rev_dir, "meta.json"), {})
            out.append({"revision": rev, "url": url_for(img), "meta": meta,
                        "masks": sorted(m for m in os.listdir(rev_dir) if m.startswith("mask_"))})
    capture = find_capture(project, shot)
    return {"project": project, "shot": shot, "capture": url_for(capture) if capture else None,
            "revisions": out, "refs": list_refs(project, shot)}


def api_pack_save(_q, body):
    pid = safe_id(body.get("id"), "id")
    name = (body.get("name") or pid).strip()
    options = body.get("options") or {}
    base = p("assets", "stylepacks")
    # 화면에서 고른 팩을 바탕으로 저장한다. 예전에는 알파벳 첫 팩(aerial-drone)을 늘 바탕으로 써서
    # 눈높이 샷을 저장해도 드론 조감 프롬프트가 되던 버그가 있었다 (2026-10-11).
    base_id = body.get("base") or "overcast-photoreal"
    template = read_json(os.path.join(base, safe_id(base_id, "base"), "pack.json")) or {}
    if not template:
        raise ApiError(400, f"바탕 팩을 찾을 수 없습니다: {base_id}")
    full_id = pid if pid.startswith("custom-") else f"custom-{pid}"
    if full_id == template.get("id") and not full_id.startswith("custom-"):
        raise ApiError(400, "기본 팩과 같은 이름으로는 저장할 수 없습니다")
    if os.path.exists(os.path.join(base, full_id, "pack.json")) and not body.get("overwrite"):
        raise ApiError(409, f"이미 있는 팩입니다: {full_id}", exists=True)
    def as_list(v, sep=","):
        return v if isinstance(v, list) else [x.strip() for x in str(v).split(sep) if x.strip()]

    slots = dict(template.get("slots") or {})          # template slots, overridden by UI choices
    for k, v in options.items():                      # every axis except per-shot keys lands in slots
        if k in ("mood", "keep_fixed", "aspect", "references") or v in ("", None, False):
            continue
        slots[k] = as_list(v) if k in ("materials", "entourage") else str(v)
    inherited = {k: v for k, v in template.items()
                 if k not in ("id", "version", "name", "mood", "slots", "keep_fixed", "samples", "changelog")}
    pack = {"id": full_id, "version": "1.0.0", "name": name,
            "mood": options.get("mood") or template.get("mood") or "photoreal", "slots": slots, **inherited,
            "keep_fixed": as_list(options.get("keep_fixed") or [], ";"),
            "samples": [], "source_template": template.get("source_template") or template.get("id"),
            "changelog": [{"date": date.today().isoformat(), "note": "saved from webtool"}]}
    d = os.path.join(base, full_id)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "pack.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(pack, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return {"id": full_id, "path": os.path.relpath(path, ROOT)}


ROUTES = {
    ("GET", "/api/packs"): api_packs,
    ("GET", "/api/options"): api_options,
    ("POST", "/api/upload_ref"): api_upload_ref,
    ("POST", "/api/ref/delete"): api_ref_delete,
    ("POST", "/api/upload"): api_upload,
    ("GET", "/api/options"): api_options,
    ("POST", "/api/compose"): api_compose,
    ("POST", "/api/render"): api_render,
    ("POST", "/api/fix"): api_fix,
    ("GET", "/api/revisions"): api_revisions,
    ("POST", "/api/pack/save"): api_pack_save,
}


# ---------------------------------------------------------------- HTTP layer
class Handler(BaseHTTPRequestHandler):
    server_version = "archi-render-webtool/0.1"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (time.strftime("%H:%M:%S"), fmt % args))

    def _json(self, status, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _dispatch(self, method):
        url = urlparse(self.path)
        handler = ROUTES.get((method, url.path))
        if handler is None:
            if method == "GET":
                return self._static(url.path)
            return self._json(404, {"error": "unknown endpoint"})
        try:
            body = {}
            if method == "POST":
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b"{}"
                if "multipart/form-data" in (self.headers.get("Content-Type") or ""):
                    body = self._multipart(raw)
                else:
                    body = json.loads(raw or b"{}")
                if not isinstance(body, dict):
                    raise ApiError(400, "JSON body must be an object")
            self._json(200, handler(parse_qs(url.query), body))
        except ApiError as e:
            self._json(e.status, {"error": e.message, **e.extra})
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid JSON"})
        except Exception as e:  # noqa: BLE001 — never let the server die on a request
            self._json(500, {"error": f"{type(e).__name__}: {e}"})

    def _multipart(self, raw):
        """Minimal multipart parser for /api/upload and /api/upload_ref (fields: project, shot, file)."""
        ctype = self.headers.get("Content-Type", "")
        m = re.search(r'boundary="?([^";]+)"?', ctype)
        if not m:
            raise ApiError(400, "multipart boundary missing")
        body = {}
        for part in raw.split(b"--" + m.group(1).encode()):
            if b"\r\n\r\n" not in part:
                continue
            head, _, data = part.partition(b"\r\n\r\n")
            data = data.rstrip(b"\r\n").removesuffix(b"--")
            name = re.search(rb'name="([^"]+)"', head)
            fname = re.search(rb'filename="([^"]*)"', head)
            if not name:
                continue
            if fname:
                body["data"] = base64.b64encode(data).decode()
                body["ext"] = fname.group(1).decode(errors="ignore").rsplit(".", 1)[-1].lower()
            else:
                body[name.group(1).decode()] = data.decode("utf-8", errors="ignore")
        return body

    def _static(self, path):
        if path == "/":
            path = "/index.html"
        if path.startswith("/renders/") or path.startswith("/assets/"):
            base, rel = ROOT, path.lstrip("/")
        else:
            base, rel = STATIC, path.lstrip("/")
        full = os.path.realpath(os.path.join(base, rel))
        if not full.startswith(os.path.realpath(base) + os.sep) or not os.path.isfile(full):
            return self._json(404, {"error": "not found", "path": path})
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        with open(full, "rb") as fh:
            data = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store" if base == ROOT else "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")


def main():
    global ROOT, SCRIPTS_DIR
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--root", default=ROOT, help="workspace root (default: parent of webtool/)")
    ap.add_argument("--stub", action="store_true",
                    help="use webtool/stubs/ instead of scripts/ (offline UI testing)")
    args = ap.parse_args()
    ROOT = os.path.abspath(args.root)
    SCRIPTS_DIR = os.path.join(HERE, "stubs") if args.stub else os.path.join(ROOT, "scripts")
    mimetypes.add_type("application/javascript", ".js")
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"archi-render webtool  http://127.0.0.1:{args.port}   root={ROOT}"
          f"   scripts={SCRIPTS_DIR}{'  [STUB]' if args.stub else ''}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
