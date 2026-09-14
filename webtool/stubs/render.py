#!/usr/bin/env python3
"""STUB for scripts/render.py — offline UI testing only (server.py --stub).

Mirrors the fixed CLI and output contract:
  render.py --input <img> --project P --shot S --pack <id> [--option k=v] [--backend gpt|grok] [--aspect W:H]
  render.py fix --project P --shot S --base Rnn --mask <png> --instruction "..." --backend grok
Prints one JSON line {revision, path, prompt, backend, elapsed_s, stub: true}.
The "render" is just the input image (or base render) copied, with a fake 1s delay.
"""
import argparse
import json
import os
import shutil
import sys
import time

fix = len(sys.argv) > 1 and sys.argv[1] == "fix"
ap = argparse.ArgumentParser()
if fix:
    ap.add_argument("fix")
    ap.add_argument("--base", required=True)
    ap.add_argument("--mask", required=True)
    ap.add_argument("--instruction", required=True)
else:
    ap.add_argument("--input", required=True)
    ap.add_argument("--pack", required=True)
    ap.add_argument("--option", action="append", default=[])
    ap.add_argument("--aspect")
ap.add_argument("--project", required=True)
ap.add_argument("--shot", required=True)
ap.add_argument("--backend", default="gpt")
a = ap.parse_args()

t0 = time.time()
shot_dir = os.path.join("renders", a.project, a.shot)
os.makedirs(shot_dir, exist_ok=True)
existing = sorted(d for d in os.listdir(shot_dir) if d.startswith("R") and d[1:].isdigit())
rev = f"R{len(existing):02d}"
rev_dir = os.path.join(shot_dir, rev)
os.makedirs(rev_dir)

if fix:
    src_dir = os.path.join(shot_dir, a.base)
    src = next((os.path.join(src_dir, n) for n in os.listdir(src_dir) if n.startswith("render.")), None)
    if not src or not os.path.exists(a.mask):
        sys.exit("stub: base render or mask missing")
    prompt = f"[STUB fix] {a.instruction}"
else:
    src = a.input
    prompt = f"[STUB prompt] pack={a.pack} " + " ".join(a.option)

ext = os.path.splitext(src)[1].lower().lstrip(".") or "png"
ext = "jpg" if ext == "jpeg" else ext
out = os.path.join(rev_dir, f"render.{ext}")
time.sleep(1)
shutil.copyfile(src, out)
meta = {"revision": rev, "path": out, "prompt": prompt, "backend": a.backend,
        "elapsed_s": round(time.time() - t0, 2), "stub": True,
        "mode": "fix" if fix else "render", "base": getattr(a, "base", None),
        "created": time.strftime("%Y-%m-%dT%H:%M:%S")}
with open(os.path.join(rev_dir, "meta.json"), "w", encoding="utf-8") as fh:
    json.dump(meta, fh, ensure_ascii=False, indent=2)
print(json.dumps(meta, ensure_ascii=False))
