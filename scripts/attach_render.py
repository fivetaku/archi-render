#!/usr/bin/env python3
"""Codex 내장 이미지 도구로 만든 그림을 렌더 리비전(Rnn)에 붙인다.

render.py --dry-run 이 만든 리비전 폴더(prompt.txt, meta.json)에 생성 이미지를 복사하고
meta.json을 실제 렌더 기록으로 바꾼다. 이미지는 재인코딩하지 않는다(원본 바이트 그대로 복사).

  python3 scripts/attach_render.py --dir renders/<P>/<S>/Rnn --file <생성 이미지>
  python3 scripts/attach_render.py --dir renders/<P>/<S>/Rnn --latest-codex

--latest-codex: ~/.codex/generated_images/ 아래에서 리비전 생성 시각 이후 만들어진
가장 최근 이미지를 찾는다 (Codex 앱·CLI가 생성 이미지를 저장하는 위치).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

EXTS = (".png", ".jpg", ".jpeg", ".webp")


def latest_codex_image(since: float) -> Path | None:
    root = Path.home() / ".codex" / "generated_images"
    if not root.is_dir():
        return None
    hits = [p for p in root.rglob("*") if p.suffix.lower() in EXTS and p.stat().st_mtime >= since]
    return max(hits, key=lambda p: p.stat().st_mtime) if hits else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", required=True, help="renders/<P>/<S>/Rnn (render.py --dry-run 결과)")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="생성된 이미지 파일 경로")
    src.add_argument("--latest-codex", action="store_true", help="~/.codex/generated_images 에서 최신 이미지 사용")
    ap.add_argument("--elapsed", type=float, default=None, help="생성에 걸린 초 (알면)")
    a = ap.parse_args()

    rev = Path(a.dir)
    meta_p = rev / "meta.json"
    if not meta_p.is_file():
        sys.exit(f"[중단] {meta_p} 가 없습니다. 먼저 render.py ... --dry-run 으로 리비전을 만드세요.")
    meta = json.loads(meta_p.read_text())

    if a.file:
        img = Path(a.file).expanduser()
    else:
        since = meta_p.stat().st_mtime - 5
        img = latest_codex_image(since)
        if img is None:
            sys.exit("[중단] 리비전을 만든 뒤 생성된 이미지를 ~/.codex/generated_images 에서 찾지 못했습니다. "
                     "--file 로 경로를 직접 주세요.")
    if not img.is_file() or img.suffix.lower() not in EXTS:
        sys.exit(f"[중단] 이미지 파일이 아닙니다: {img}")

    for old in rev.glob("render.*"):
        sys.exit(f"[중단] 이미 렌더가 있습니다: {old}. 새 리비전을 만드세요.")
    out = rev / f"render{img.suffix.lower()}"
    shutil.copyfile(img, out)

    size = None
    try:
        from PIL import Image
        with Image.open(out) as im:
            size = list(im.size)
    except Exception:
        pass

    meta.update({
        "backend": "codex-app",
        "model": "gpt-image (Codex 내장 이미지 도구)",
        "output_path": str(out.resolve()),
        "output_size": size,
        "output_sha1": hashlib.sha1(out.read_bytes()).hexdigest(),
        "source_file": str(img),
        "elapsed_s": a.elapsed,
        "dry_run": False,
        "attached_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    meta_p.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(json.dumps({"ok": True, "revision": meta.get("revision"), "output": str(out), "size": size}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
