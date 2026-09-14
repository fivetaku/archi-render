#!/usr/bin/env python3
"""Internal-standard mask <-> vendor mask conversion (Pillow only).

Internal standard: 8-bit grayscale ("L"), 255 = editable region, 0 = keep.

Vendor polarity table (design doc P7 / §6, exec_tests E3):
  grok       alpha0_edit   RGBA, alpha 0 = editable (measured on router grok-imagine-image-2.0)
  openai     alpha0_edit   RGBA, alpha 0 = editable (gpt-image edits; not reachable via router)
  flux       white_regen   L, white = regenerate
  stability  white_regen   L, white = inpaint (mode=mask)

API:  to_internal(path) -> PIL "L"          to_vendor(mask_L, vendor, size) -> PIL image
      dilate_feather(mask_L, dilate_px, feather_px) -> PIL "L"
CLI:  python3 scripts/mask_convert.py --in m.png --out m_grok.png --vendor grok
        [--size WxH | --match base.png] [--dilate 12] [--feather 6]
Selftest: --selftest
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageOps

POLARITY = {
    "grok": "alpha0_edit",
    "openai": "alpha0_edit",
    "flux": "white_regen",
    "stability": "white_regen",
}


def to_internal(path) -> Image.Image:
    """Load any mask file and normalise to L (255=edit).

    RGBA with a non-opaque alpha channel → transparent pixels are the edit region
    (vendor alpha0 convention). Anything else → luminance, white (>=128) = edit.
    """
    return to_internal_image(Image.open(path))


def dilate_feather(mask: Image.Image, dilate_px: int = 0, feather_px: int = 0) -> Image.Image:
    """Grow the edit region by dilate_px then soften edges with a Gaussian of feather_px."""
    out = mask.convert("L")
    if dilate_px > 0:
        out = out.filter(ImageFilter.MaxFilter(2 * int(dilate_px) + 1))
    if feather_px > 0:
        out = out.filter(ImageFilter.GaussianBlur(float(feather_px)))
    return out


def to_vendor(mask_L: Image.Image, vendor: str, size=None) -> Image.Image:
    """Convert internal mask to a vendor image; size=(w,h) resizes (NEAREST) to the base image."""
    pol = POLARITY.get(vendor)
    if pol is None:
        raise ValueError(f"unknown vendor {vendor!r}; choose {sorted(POLARITY)}")
    m = mask_L.convert("L")
    if size and tuple(size) != m.size:
        m = m.resize(tuple(size), Image.NEAREST)
    if pol == "alpha0_edit":
        rgba = Image.new("RGBA", m.size, (0, 0, 0, 255))
        rgba.putalpha(ImageOps.invert(m))  # edit(255) → alpha 0
        return rgba
    return m  # white_regen


def _parse_size(s: str):
    w, h = s.lower().split("x")
    return int(w), int(h)


def _selftest() -> int:
    # 64x64 internal mask: right half editable.
    m = Image.new("L", (64, 64), 0)
    m.paste(255, (32, 0, 64, 64))
    g = to_vendor(m, "grok", (128, 128))
    assert g.mode == "RGBA" and g.size == (128, 128)
    assert g.getpixel((100, 10))[3] == 0 and g.getpixel((10, 10))[3] == 255, "alpha polarity"
    back = to_vendor(to_internal_image(g), "flux", (64, 64))
    assert ImageChops.difference(back, m).getbbox() is None, "round trip grok→internal→flux"
    d = dilate_feather(m, 4, 0)
    assert d.getpixel((29, 10)) == 255 and d.getpixel((26, 10)) == 0, "dilate 4px"
    f = dilate_feather(m, 0, 3)
    assert 0 < f.getpixel((32, 10)) < 255, "feather makes soft edge"
    print("mask_convert selftest OK")
    return 0


def to_internal_image(im: Image.Image) -> Image.Image:
    """to_internal() for an already-open PIL image (used by selftest and render.py)."""
    if im.mode in ("RGBA", "LA") and im.getchannel("A").getextrema()[0] < 255:
        return ImageOps.invert(im.getchannel("A")).point(lambda v: 255 if v >= 128 else 0)
    return im.convert("L").point(lambda v: 255 if v >= 128 else 0)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--in", dest="inp")
    ap.add_argument("--out")
    ap.add_argument("--vendor", default="grok", choices=sorted(POLARITY))
    ap.add_argument("--size", help="WxH")
    ap.add_argument("--match", help="image whose size the mask must match")
    ap.add_argument("--dilate", type=int, default=0)
    ap.add_argument("--feather", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if not (a.inp and a.out):
        ap.error("--in and --out required")
    size = _parse_size(a.size) if a.size else (Image.open(a.match).size if a.match else None)
    m = dilate_feather(to_internal(a.inp), a.dilate, a.feather)
    out = to_vendor(m, a.vendor, size)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    out.save(a.out)
    print(f"{a.out} {out.mode} {out.size[0]}x{out.size[1]} polarity={POLARITY[a.vendor]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
