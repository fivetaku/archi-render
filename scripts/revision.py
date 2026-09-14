#!/usr/bin/env python3
"""Revision stage management for renders/<P>/<S>/Rnn/meta.json.

  python3 scripts/revision.py approve --project P --shot S --revision R01 --stage clay|internal|client|approval [--note "..."]
  python3 scripts/revision.py list --project P [--shot S]

approve: sets meta.json "stage" (+ stage_history) and appends a row to 40-reports/approvals.md.
list:    prints a table of revisions (revision, mode, backend, stage, created_at, output).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENDERS = ROOT / "renders"
APPROVALS = ROOT / "40-reports" / "approvals.md"
STAGES = ["clay", "internal", "client", "approval"]
HEADER = "# Approvals\n\n| date (UTC) | project | shot | revision | from | to | note |\n|---|---|---|---|---|---|---|\n"


def approve(project: str, shot: str, revision: str, stage: str, note: str = "") -> dict:
    meta_path = RENDERS / project / shot / revision / "meta.json"
    if not meta_path.is_file():
        raise SystemExit(f"no meta.json at {meta_path}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    prev = meta.get("stage", "clay")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    meta["stage"] = stage
    meta.setdefault("stage_history", []).append({"from": prev, "to": stage, "at": now, "note": note})
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    APPROVALS.parent.mkdir(parents=True, exist_ok=True)
    if not APPROVALS.is_file():
        APPROVALS.write_text(HEADER, encoding="utf-8")
    with APPROVALS.open("a", encoding="utf-8") as f:
        f.write(f"| {now} | {project} | {shot} | {revision} | {prev} | {stage} | {note.replace('|', '/')} |\n")
    return {"ok": True, "project": project, "shot": shot, "revision": revision, "from": prev, "to": stage}


def list_revisions(project: str, shot: str | None = None) -> list[dict]:
    rows = []
    proj = RENDERS / project
    for shot_dir in sorted(p for p in proj.glob(shot or "*") if p.is_dir()):
        for rev in sorted(p for p in shot_dir.glob("R*") if p.is_dir()):
            mp = rev / "meta.json"
            m = json.loads(mp.read_text(encoding="utf-8")) if mp.is_file() else {}
            rows.append({"shot": shot_dir.name, "revision": rev.name, "mode": m.get("mode", "?"),
                         "backend": m.get("backend", "?"), "stage": m.get("stage", "?"),
                         "created_at": m.get("created_at", ""), "output": Path(m["output_path"]).name if m.get("output_path") else "-"})
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("approve")
    a1.add_argument("--project", required=True)
    a1.add_argument("--shot", required=True)
    a1.add_argument("--revision", required=True)
    a1.add_argument("--stage", required=True, choices=STAGES)
    a1.add_argument("--note", default="")
    a2 = sub.add_parser("list")
    a2.add_argument("--project", required=True)
    a2.add_argument("--shot")
    a = ap.parse_args(argv)
    if a.cmd == "approve":
        print(json.dumps(approve(a.project, a.shot, a.revision, a.stage, a.note), ensure_ascii=False))
    else:
        rows = list_revisions(a.project, a.shot)
        print(f"{'shot':<12} {'rev':<5} {'mode':<5} {'backend':<8} {'stage':<9} {'created_at':<26} output")
        for r in rows:
            print(f"{r['shot']:<12} {r['revision']:<5} {r['mode']:<5} {r['backend']:<8} {r['stage']:<9} {r['created_at']:<26} {r['output']}")
        if not rows:
            print("(no revisions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
