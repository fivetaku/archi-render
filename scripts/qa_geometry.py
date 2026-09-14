#!/usr/bin/env python3
"""ADVISORY geometry check: edge-map agreement between a capture and its render.

This is NOT a gate (design §8 rule 2). A low score means "a human must look", nothing more:
photoreal renders legitimately add texture edges that clay captures lack.

Method (Pillow only): both images → grayscale → resized to a common width → light blur →
FIND_EDGES → threshold → binary edge sets.
  iou              : |A∩B| / |A∪B| of the raw edge sets (strict)
  structural_score : mean of (A covered by B dilated 2px, B covered by A dilated 2px) —
                     tolerant to 1-2px drift, which is what geometry fidelity cares about.

CLI: python3 scripts/qa_geometry.py --capture in.png --render out.jpg [--threshold 0.25]
     [--edge-threshold 40] [--width 512] [--json-out report.json]
Prints one JSON line; adds a "WARN ..." line on stderr if iou < threshold. Always exits 0
(advisory), except on I/O errors. Selftest: --selftest
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter


def edge_map(im: Image.Image, width: int = 512, edge_threshold: int = 40, height: int | None = None) -> Image.Image:
    """Binary (0/255) edge image at the common size."""
    g = im.convert("L")
    if height is None:
        height = max(1, round(g.height * width / g.width))
    g = g.resize((width, height), Image.BILINEAR).filter(ImageFilter.GaussianBlur(1))
    e = g.filter(ImageFilter.FIND_EDGES)
    return e.point(lambda v: 255 if v >= edge_threshold else 0)


def _count(im: Image.Image) -> int:
    return im.histogram()[255]


def compare(capture: Image.Image, render: Image.Image, width: int = 512, edge_threshold: int = 40) -> dict:
    height = max(1, round(capture.height * width / capture.width))
    a = edge_map(capture, width, edge_threshold, height)
    b = edge_map(render, width, edge_threshold, height)
    inter = _count(ImageChops.multiply(a, b))
    union = _count(ImageChops.lighter(a, b))
    iou = inter / union if union else 1.0
    a_d = a.filter(ImageFilter.MaxFilter(5))
    b_d = b.filter(ImageFilter.MaxFilter(5))
    na, nb = _count(a), _count(b)
    cov_a = _count(ImageChops.multiply(a, b_d)) / na if na else 1.0
    cov_b = _count(ImageChops.multiply(b, a_d)) / nb if nb else 1.0
    return {
        "size": [width, height],
        "edge_px_capture": na,
        "edge_px_render": nb,
        "iou": round(iou, 4),
        "structural_score": round((cov_a + cov_b) / 2, 4),
        "capture_covered_by_render": round(cov_a, 4),
        "render_covered_by_capture": round(cov_b, 4),
    }


def _synthetic(shift: int = 0, extra: bool = False) -> Image.Image:
    im = Image.new("L", (256, 192), 230)
    d = ImageDraw.Draw(im)
    d.rectangle((40 + shift, 60, 200 + shift, 170), outline=20, width=3)   # building
    d.polygon([(40 + shift, 60), (120 + shift, 20), (200 + shift, 60)], outline=20)  # roof
    for x in (60, 110, 160):
        d.rectangle((x + shift, 90, x + 25 + shift, 120), outline=20, width=2)  # windows
    if extra:
        d.ellipse((205, 100, 250, 160), outline=20, width=2)  # added tree = drift
    return im


def _selftest() -> int:
    base = _synthetic()
    same = compare(base, base)
    assert same["iou"] == 1.0 and same["structural_score"] == 1.0, same
    near = compare(base, _synthetic(shift=1))
    assert near["structural_score"] > 0.9 > near["iou"] - 0.5, near     # tolerant score forgives 1px
    far = compare(base, _synthetic(shift=40, extra=True))
    assert far["iou"] < near["iou"] and far["structural_score"] < near["structural_score"], (near, far)
    print("qa_geometry selftest OK", json.dumps({"same": same["iou"], "near": near["iou"], "far": far["iou"]}))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--capture")
    ap.add_argument("--render")
    ap.add_argument("--threshold", type=float, default=0.25, help="WARN if iou below this (advisory)")
    ap.add_argument("--edge-threshold", type=int, default=40)
    ap.add_argument("--width", type=int, default=512)
    ap.add_argument("--json-out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if not (a.capture and a.render):
        ap.error("--capture and --render required")
    rep = compare(Image.open(a.capture), Image.open(a.render), a.width, a.edge_threshold)
    rep.update({"capture": str(a.capture), "render": str(a.render), "threshold": a.threshold,
                "warn": (rep["iou"] < a.threshold and rep["structural_score"] < 0.7), "advisory": True})
    if a.json_out:
        Path(a.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json_out).write_text(json.dumps(rep, indent=2, ensure_ascii=False))
    print(json.dumps(rep, ensure_ascii=False))
    if rep["warn"]:
        print(f"WARN geometry drift suspected: iou={rep['iou']} < {a.threshold} "
              f"(structural_score={rep['structural_score']}). Advisory only — human review required.",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
