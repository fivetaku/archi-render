#!/usr/bin/env python3
"""Build a contact sheet: one row per shot, tiles = input capture | latest render.

CLI: python3 scripts/contact_sheet.py --project P [--shots S1 S2 ...] [--latest] [--tile 512] [--out f.jpg]
Output: 50-output/<P>/contact_sheet_<YYYYMMDD>.jpg (deliverable, git-tracked). Prints one JSON line.
--latest (default behaviour) picks the newest revision that has a render file; shots whose
revisions are dry-run only get a grey "no render" tile so the sheet still builds.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
RENDERS, CAPTURES, OUTPUT = ROOT / "renders", ROOT / "assets" / "captures", ROOT / "50-output"
IMG_EXTS = (".png", ".jpg", ".jpeg", ".webp")
LABEL_H = 22


def _find(dir_: Path, stem: str) -> Path | None:
    return next((dir_ / f"{stem}{e}" for e in IMG_EXTS if (dir_ / f"{stem}{e}").is_file()), None)


def latest_render(shot_dir: Path):
    for rev in sorted((p for p in shot_dir.glob("R*") if p.is_dir()), reverse=True):
        img = _find(rev, "render")
        if img:
            meta = json.loads((rev / "meta.json").read_text()) if (rev / "meta.json").is_file() else {}
            return rev.name, img, meta.get("stage", "")
    return None, None, ""


def tile(img: Path | None, size: int, label: str) -> Image.Image:
    canvas = Image.new("RGB", (size, size + LABEL_H), (245, 245, 245))
    if img:
        im = Image.open(img).convert("RGB")
        im.thumbnail((size, size))
        canvas.paste(im, ((size - im.width) // 2, (size - im.height) // 2))
    else:
        ImageDraw.Draw(canvas).text((size // 2 - 30, size // 2), "no render", fill=(120, 120, 120))
    d = ImageDraw.Draw(canvas)
    d.rectangle((0, size, size, size + LABEL_H), fill=(30, 30, 30))
    d.text((6, size + 5), label[:70], fill=(255, 255, 255))
    return canvas


def build(project: str, shots: list[str] | None, tile_px: int, out: Path | None) -> dict:
    shot_names = shots or sorted({p.name for base in (CAPTURES / project, RENDERS / project)
                                  if base.is_dir() for p in base.iterdir() if p.is_dir()})
    if not shot_names:
        raise SystemExit(f"no shots found for project {project!r}")
    rows = []
    for s in shot_names:
        cap = _find(CAPTURES / project / s, "capture")
        rev, render, stage = latest_render(RENDERS / project / s)
        rows.append((tile(cap, tile_px, f"{s}  input"), tile(render, tile_px, f"{s}  {rev or '-'} {stage}".strip())))
    sheet = Image.new("RGB", (2 * tile_px + 12, len(rows) * (tile_px + LABEL_H + 8) + 4), (255, 255, 255))
    for i, (a, b) in enumerate(rows):
        y = 4 + i * (tile_px + LABEL_H + 8)
        sheet.paste(a, (4, y))
        sheet.paste(b, (tile_px + 8, y))
    out = out or OUTPUT / project / f"contact_sheet_{date.today():%Y%m%d}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=88)
    return {"ok": True, "project": project, "shots": shot_names, "out": str(out), "size": list(sheet.size)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", required=True)
    ap.add_argument("--shots", nargs="*")
    ap.add_argument("--latest", action="store_true", help="use latest rendered revision (default)")
    ap.add_argument("--tile", type=int, default=512)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    print(json.dumps(build(a.project, a.shots, a.tile, Path(a.out) if a.out else None), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
