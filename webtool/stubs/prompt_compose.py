#!/usr/bin/env python3
"""STUB for scripts/prompt_compose.py — offline UI testing only (server.py --stub).

Mirrors the fixed CLI: --pack <id> [--option k=v ...] --print   |   --list-options
"""
import argparse
import json

ap = argparse.ArgumentParser()
ap.add_argument("--pack")
ap.add_argument("--option", action="append", default=[])
ap.add_argument("--print", action="store_true")
ap.add_argument("--list-options", action="store_true")
a = ap.parse_args()

if a.list_options:   # minimal subset of the real schema (values / options / free / slots_order)
    print(json.dumps({
        "source": "STUB", "slots_order": ["shot", "materials", "lighting", "season", "entourage", "context", "grading"],
        "values": {"mood": ["photoreal", "cinematic", "clay"], "lighting": ["overcast", "midday", "dusk"],
                   "camera": ["eye_level", "drone"], "materials": ["white_stucco_oak", "timber_glass"],
                   "entourage": ["people", "cars", "vegetation", "furniture"], "people_density": ["sparse", "busy"],
                   "post": ["neutral", "bw"], "aspect": ["4:3", "16:9", "auto"]},
        "options": {"lighting": {"merged_into": "lighting"}, "camera": {"merged_into": "shot"},
                    "people_density": {"merged_into": "entourage", "requires": "entourage.people=on"},
                    "post": {"merged_into": "grading"},
                    "entourage": {"type": "toggles", "values": ["people", "cars", "vegetation", "furniture"], "format": "people:on,cars:off,..."}},
        "free": {"lens_mm": "int", "keep_fixed": "text_list"}}))
    raise SystemExit(0)
if not a.pack:
    ap.error("--pack is required")

opts = dict(o.split("=", 1) for o in a.option if "=" in o)
lines = [f"[STUB prompt] architectural visualization, style pack '{a.pack}'"]
for k, v in opts.items():
    lines.append(f"- {k}: {v}")
print("\n".join(lines))
