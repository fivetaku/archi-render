#!/usr/bin/env python3
"""Render a shot (full) or fix a region (mask) and record a revision.

Full shot:
  python3 scripts/render.py --input <img> --project P --shot S --pack <id>
      [--option k=v ...] [--backend gpt|grok] [--aspect 16:9] [--prompt-file f.txt] [--dry-run]
  backend gpt  (default) = pumasi imagen.sh with --ref <input>  (Codex image_gen, subscription, no mask)
  backend grok           = insane-router POST {URL}/images/edits, model x-ai/grok-imagine-image-2.0, no mask

Fix (masked region edit — grok only, gpt has no mask input):
  python3 scripts/render.py fix --project P --shot S [--base R02] --mask m.png --instruction "..."
      [--backend grok] [--dilate 12 --feather 6] [--dry-run]

Output: renders/<P>/<S>/Rnn/{render.png|jpg, prompt.txt, meta.json[, mask_internal.png, mask_grok.png]}
The input is copied once to assets/captures/<P>/<S>/capture.<ext>. Last stdout line is one JSON result.
Secrets: router URL/key are read at runtime through the tikeytaka CLI and never printed or stored.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mask_convert  # noqa: E402
import prompt_compose  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RENDERS = ROOT / "renders"
CAPTURES = ROOT / "assets" / "captures"
IMAGEN_GLOB = os.path.expanduser("~/.claude/plugins/cache/gptaku-plugins/pumasi/*/skills/image/scripts/imagen.sh")
TKT_GLOB = os.path.expanduser("~/.claude/plugins/cache/gptaku-plugins/tikeytaka/*/bin/tkt")
GROK_MODEL = "x-ai/grok-imagine-image-2.0"
ROUTER_KEY_SERVICE = os.environ.get("ARCHI_RENDER_ROUTER_KEY_SERVICE", "insane-router-key-aside")
ASPECTS = {"16:9": 16 / 9, "4:3": 4 / 3, "3:2": 3 / 2, "1:1": 1.0, "9:16": 9 / 16, "3:4": 3 / 4, "2:3": 2 / 3}
IMG_EXTS = (".png", ".jpg", ".jpeg", ".webp")


# ---------------------------------------------------------------- helpers
def _latest(pattern: str) -> str | None:
    hits = sorted(glob.glob(pattern))
    return hits[-1] if hits else None


def tkt_get(service: str) -> str:
    """Fetch a vault value via the tikeytaka CLI (value never logged)."""
    tkt = _latest(TKT_GLOB)
    if not tkt:
        raise RuntimeError("tikeytaka CLI not found; cannot read router credentials")
    r = subprocess.run(["bash", tkt, "get", service], capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(f"tikeytaka: cannot read '{service}' (rc={r.returncode})")
    return r.stdout.strip().splitlines()[-1].strip()


def sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def next_revision(shot_dir: Path) -> str:
    shot_dir.mkdir(parents=True, exist_ok=True)
    nums = [int(m.group(1)) for p in shot_dir.iterdir() if (m := re.fullmatch(r"R(\d{2,})", p.name))]
    return f"R{(max(nums) + 1) if nums else 0:02d}"


def find_render(rev_dir: Path) -> Path | None:
    for ext in IMG_EXTS:
        p = rev_dir / f"render{ext}"
        if p.is_file():
            return p
    return None


def latest_revision_with_render(shot_dir: Path) -> Path | None:
    revs = sorted((p for p in shot_dir.glob("R*") if p.is_dir()), reverse=True)
    return next((r for r in revs if find_render(r)), None)


def guess_aspect(img_path: Path) -> str:
    from PIL import Image

    with Image.open(img_path) as im:
        r = im.width / im.height
    return min(ASPECTS, key=lambda k: abs(ASPECTS[k] - r))


def ensure_capture(input_path: Path, project: str, shot: str) -> Path:
    dst_dir = CAPTURES / project / shot
    dst_dir.mkdir(parents=True, exist_ok=True)
    existing = next((p for p in dst_dir.glob("capture.*")), None)
    if existing:
        return existing
    dst = dst_dir / f"capture{input_path.suffix.lower() or '.png'}"
    shutil.copy2(input_path, dst)
    return dst


def image_size(path: Path):
    from PIL import Image

    with Image.open(path) as im:
        return list(im.size)


# ---------------------------------------------------------------- backends
def call_imagen(prompt_file: Path, target: Path, aspect: str | None, ref: Path) -> Path:
    """gpt-image via pumasi imagen.sh (only allowed gpt path). Returns the produced file."""
    imagen = _latest(IMAGEN_GLOB)
    if not imagen:
        raise RuntimeError("pumasi imagen.sh not found (gptaku-plugins/pumasi)")
    cmd = ["bash", imagen, str(prompt_file), str(target), aspect or "", "--ref", str(ref)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    sys.stderr.write(r.stdout[-2000:] + r.stderr[-2000:])
    if r.returncode != 0:
        raise RuntimeError(f"imagen.sh failed rc={r.returncode}")
    produced = find_render(target.parent)
    if not produced:
        raise RuntimeError("imagen.sh reported success but no render.* file found")
    return produced


def _multipart(fields: dict, files: dict) -> tuple[bytes, str]:
    boundary = "----archi" + uuid.uuid4().hex
    body = bytearray()
    for k, v in fields.items():
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    for k, path in files.items():
        ctype = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"; "
                 f"filename=\"{Path(path).name}\"\r\nContent-Type: {ctype}\r\n\r\n").encode()
        body += Path(path).read_bytes() + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def call_router_edit(prompt: str, image: Path, mask: Path | None, out_dir: Path) -> tuple[Path, dict]:
    """POST {URL}/images/edits (grok). Downloads data[0].url immediately (temporary URL)."""
    url = tkt_get("insane-router-url").rstrip("/")
    key = tkt_get(ROUTER_KEY_SERVICE)
    files = {"image": image}
    if mask:
        files["mask"] = mask
    body, ctype = _multipart({"model": GROK_MODEL, "prompt": prompt}, files)
    req = urllib.request.Request(f"{url}/images/edits", data=body, method="POST",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": ctype,
                                          # Cloudflare 앞단이 기본 Python-urllib UA를 1010으로 차단함 (2026-09-14 실측)
                                          "User-Agent": "archi-render/1.0 (+curl-compatible)"})
    try:
        with urllib.request.urlopen(req, timeout=240) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"router HTTP {e.code}: {e.read()[:300].decode(errors='replace')}") from None
    item = (payload.get("data") or [{}])[0]
    img_url = item.get("url")
    if not img_url:
        raise RuntimeError(f"router response has no data[0].url: {json.dumps(payload)[:300]}")
    dl_req = urllib.request.Request(img_url, headers={"User-Agent": "archi-render/1.0 (+curl-compatible)"})
    with urllib.request.urlopen(dl_req, timeout=120) as r:
        data = r.read()
        ctype_resp = r.headers.get("Content-Type", item.get("mime_type", ""))
    ext = ".png" if "png" in (item.get("mime_type") or ctype_resp or "") else ".jpg"
    out = out_dir / f"render{ext}"
    out.write_bytes(data)
    payload["data"][0]["url"] = "<downloaded>"  # temporary URL — not worth keeping
    return out, payload


# ---------------------------------------------------------------- pipeline
def run_full(a) -> dict:
    inp = Path(a.input).expanduser().resolve()
    if not inp.is_file():
        raise SystemExit(f"input not found: {inp}")
    capture = ensure_capture(inp, a.project, a.shot)
    pack = prompt_compose.load_pack(a.pack)
    options = prompt_compose.parse_options(a.option)
    # precedence: --aspect > --option aspect > pack aspect_hint > nearest ratio of the input ("auto")
    aspect = a.aspect or options.get("aspect") or prompt_compose.pack_aspect(pack)
    if not aspect or str(aspect).lower() == "auto":
        aspect = guess_aspect(inp)
    options["aspect"] = aspect
    if a.prompt_file:
        prompt = Path(a.prompt_file).read_text(encoding="utf-8").strip()
    else:
        prompt = prompt_compose.compose(pack, options, a.source_note)

    shot_dir = RENDERS / a.project / a.shot
    rev = next_revision(shot_dir)
    rev_dir = shot_dir / rev
    rev_dir.mkdir(parents=True)
    (rev_dir / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")

    meta = {
        "revision": rev, "project": a.project, "shot": a.shot, "mode": "full",
        "backend": a.backend, "model": GROK_MODEL if a.backend == "grok" else "gpt-image (Codex image_gen via pumasi imagen.sh)",
        "pack_id": pack.get("id"), "pack_version": str(pack.get("version", "")), "options": options,
        "prompt": prompt, "input_path": str(inp), "capture_path": str(capture), "input_sha1": sha1(inp),
        "mask_path": None, "aspect": aspect, "elapsed_s": None, "usage": None, "output_path": None,
        "output_size": None, "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stage": "clay", "dry_run": bool(a.dry_run),
    }
    if not a.dry_run:
        t0 = time.time()
        try:
            if a.backend == "gpt":
                out = call_imagen(rev_dir / "prompt.txt", rev_dir / "render.png", aspect, inp)
            else:
                out, meta["usage"] = call_router_edit(prompt, inp, None, rev_dir)
        except Exception:
            # 실패한 시도는 빈 리비전 폴더를 남기지 않는다 (2026-09-14 실측: 403 시 R00 잔재)
            shutil.rmtree(rev_dir, ignore_errors=True)
            raise
        meta["elapsed_s"] = round(time.time() - t0, 1)
        meta["output_path"] = str(out)
        meta["output_size"] = image_size(out)
    (rev_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "revision": rev, "dir": str(rev_dir), "output": meta["output_path"],
            "backend": a.backend, "elapsed_s": meta["elapsed_s"], "dry_run": meta["dry_run"]}


def run_fix(a) -> dict:
    if a.backend != "grok":
        raise SystemExit("fix: backend 'gpt' has no mask input (pumasi imagen.sh accepts --ref only). "
                         "Use --backend grok, or do a full re-render with --option keep_fixed='...' "
                         "describing what must stay unchanged.")
    shot_dir = RENDERS / a.project / a.shot
    base_dir = shot_dir / a.base if a.base else latest_revision_with_render(shot_dir)
    if not base_dir or not base_dir.is_dir():
        raise SystemExit(f"fix: no base revision with a render under {shot_dir}")
    base_img = find_render(base_dir)
    if not base_img:
        raise SystemExit(f"fix: no render.* in {base_dir}")
    mask_in = Path(a.mask).expanduser()
    if not mask_in.is_file():
        raise SystemExit(f"fix: mask not found: {mask_in}")

    rev = next_revision(shot_dir)
    rev_dir = shot_dir / rev
    rev_dir.mkdir(parents=True)
    size = tuple(image_size(base_img))
    internal = mask_convert.dilate_feather(mask_convert.to_internal(mask_in), a.dilate, a.feather)
    if internal.size != size:
        from PIL import Image

        internal = internal.resize(size, Image.NEAREST)
    internal.save(rev_dir / "mask_internal.png")
    vendor_mask = rev_dir / "mask_grok.png"
    mask_convert.to_vendor(internal, "grok", size).save(vendor_mask)

    prompt = (f"{a.instruction.strip().rstrip('.')}. Change only the masked region; keep everything "
              f"outside the mask exactly as in the source image, including geometry, materials and lighting.")
    (rev_dir / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")
    base_meta = json.loads((base_dir / "meta.json").read_text()) if (base_dir / "meta.json").is_file() else {}
    meta = {
        "revision": rev, "project": a.project, "shot": a.shot, "mode": "fix", "base_revision": base_dir.name,
        "backend": "grok", "model": GROK_MODEL, "pack_id": base_meta.get("pack_id"),
        "pack_version": base_meta.get("pack_version"), "options": {"dilate": a.dilate, "feather": a.feather},
        "prompt": prompt, "input_path": str(base_img), "input_sha1": sha1(base_img),
        "mask_path": str(vendor_mask), "mask_source": str(mask_in), "elapsed_s": None, "usage": None,
        "output_path": None, "output_size": None,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "stage": "clay",
        "dry_run": bool(a.dry_run),
    }
    if not a.dry_run:
        t0 = time.time()
        try:
            out, meta["usage"] = call_router_edit(prompt, base_img, vendor_mask, rev_dir)
        except Exception:
            shutil.rmtree(rev_dir, ignore_errors=True)
            raise
        meta["elapsed_s"] = round(time.time() - t0, 1)
        meta["output_path"] = str(out)
        meta["output_size"] = image_size(out)
    (rev_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "revision": rev, "dir": str(rev_dir), "output": meta["output_path"],
            "base": base_dir.name, "backend": "grok", "elapsed_s": meta["elapsed_s"], "dry_run": meta["dry_run"]}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "fix":
        ap = argparse.ArgumentParser(prog="render.py fix", description="masked region edit (grok)")
        ap.add_argument("--project", required=True)
        ap.add_argument("--shot", required=True)
        ap.add_argument("--base", help="base revision, e.g. R02 (default: latest with a render)")
        ap.add_argument("--mask", required=True, help="mask png (internal L 255=edit, or RGBA alpha0=edit)")
        ap.add_argument("--instruction", required=True)
        ap.add_argument("--backend", default="grok", choices=["grok", "gpt"])
        ap.add_argument("--dilate", type=int, default=12)
        ap.add_argument("--feather", type=int, default=6)
        ap.add_argument("--dry-run", action="store_true")
        res = run_fix(ap.parse_args(argv[1:]))
    else:
        ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
        ap.add_argument("--input", required=True)
        ap.add_argument("--project", required=True)
        ap.add_argument("--shot", required=True)
        ap.add_argument("--pack", required=True)
        ap.add_argument("--option", action="append", default=[])
        ap.add_argument("--backend", default="gpt", choices=["gpt", "grok"])
        ap.add_argument("--aspect", help="e.g. 16:9 (default: nearest to input ratio)")
        ap.add_argument("--prompt-file", help="use this prompt verbatim instead of composing")
        ap.add_argument("--source-note", default="SketchUp")
        ap.add_argument("--dry-run", action="store_true", help="compose + write prompt/meta, no API call")
        res = run_full(ap.parse_args(argv))
    print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
