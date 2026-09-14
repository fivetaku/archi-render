#!/usr/bin/env python3
"""STUB for scripts/prompt_compose.py — offline UI testing only (server.py --stub).

Mirrors the fixed CLI: --pack <id> [--option k=v ...] --print
"""
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("--pack", required=True)
ap.add_argument("--option", action="append", default=[])
ap.add_argument("--print", action="store_true")
a = ap.parse_args()

opts = dict(o.split("=", 1) for o in a.option if "=" in o)
lines = [f"[STUB prompt] architectural visualization, style pack '{a.pack}'"]
for k, v in opts.items():
    lines.append(f"- {k}: {v}")
print("\n".join(lines))
