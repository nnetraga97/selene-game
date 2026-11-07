"""Summarize evidence without substituting numeric gates for visual acceptance."""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
directory = root / "Saved/MovementTest" / sys.argv[1]
report = {"label": directory.name, "visual_acceptance": "requires review", "captures": sorted(p.name for p in directory.glob("*.png"))}
trace = directory / "trace.csv"
if trace.exists():
    rows = list(csv.DictReader(trace.open(encoding="utf-8-sig")))
    report["frames"] = len(rows)
    report["views"] = {}
    for view in sorted({r["view"] for r in rows}):
        selected = [r for r in rows if r["view"] == view]
        report["views"][view] = {
            field: [min(float(r[field]) for r in selected), max(float(r[field]) for r in selected)]
            for field in ("speed", "x", "y", "z", "stamina")
        }
        report["views"][view]["state_changes"] = [
            {k: r[k] for k in ("time", "state", "speed", "z", "stamina")}
            for i, r in enumerate(selected) if i == 0 or r["state"] != selected[i - 1]["state"]
        ]
log = directory / "editor.log"
if log.exists():
    text = log.read_text(errors="replace")
    report["cleared_startup_exceptions"] = [line for line in text.splitlines()
        if "AttributeError:" in line and ("AgentSkill" in line or "PythonTestRunner" in line)]
    # Keep every error line for review, including the full cleared startup traceback.
    report["all_errors"] = [line for line in text.splitlines()
        if any(key in line for key in ("Error:", "Fatal error:", "Assertion failed", "Ensure condition failed"))]
    report["captures_in_log"] = [line for line in text.splitlines() if "MoveTest capture=" in line]
before = root / "Saved/MovementTest/session-1/source-before.json"
if before.exists():
    hashes = json.loads(before.read_text())
    report["protected_sources_unchanged"] = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
        for name, digest in hashes.items() if name.startswith("Config/") or "/Animation/" in name}
target = directory / "report.json"
if target.exists():
    raise SystemExit("Refusing to overwrite evidence: " + str(target))
target.write_text(json.dumps(report, indent=2))
print(json.dumps({k: v for k, v in report.items() if k not in ("all_errors", "captures_in_log")}, indent=2))
