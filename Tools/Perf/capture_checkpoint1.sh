#!/bin/bash
# Run only after rebuilding Town with the EW route actor.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ENGINE="${ENGINE:-/Users/Shared/Epic Games/UE_5.8}"
PROJECT="$ROOT/Selene.uproject"
EDITOR="$ENGINE/Engine/Binaries/Mac/UnrealEditor"
OUT="$ROOT/Saved/Checkpoint1/$(date -u +%Y%m%dT%H%M%SZ)-$$"
[[ -x "$EDITOR" ]] || { echo "Editor executable missing: $EDITOR" >&2; exit 1; }
cd "$ROOT"
# Use the same terrain-aware feet geometry as the map builder for watchdogs.
JOBS="$(python3 - <<'PY'
import math
import sys
sys.path.insert(0, 'Tools/Blockout')
from layout_core import load, length
layout = load('Design/Blockout/layout.json')
for route, count in [('R1', 6), ('R2', 12), ('R3', 3)]:
    authored = next(r for r in layout['routes'] if r['id'] == route)
    seconds = length(layout, authored) * 100 / 150
    # Startup + moving warmup + worst-case settle/write at every stop + exit.
    timeout = math.ceil(60 + 1.1 * (10 + seconds + count * 21.5) + 120)
    for camera in ('3P', '1P'):
        print(route, camera, count, timeout)
seconds = length(layout, layout['east_west_walk']) * 100 / 150
print('EW', '3P', 0, math.ceil(60 + 1.5 * (10 + seconds) + 120))
PY
)"
mkdir -p "$OUT"
child=''
watchdog=''
cleanup() {
    if [[ -n "$watchdog" ]]; then kill "$watchdog" 2>/dev/null || true; fi
    if [[ -n "$child" ]]; then kill "$child" 2>/dev/null || true; fi
}
trap 'cleanup; exit 130' INT TERM
failed=0
while read -r route camera shots timeout; do
    job="${route}_${camera}"
    args=("-PerfRoute=$route" "-PerfCam=$camera" -PerfHour=12 -PerfWarmup=10 -PerfSpeed=150 "-PerfOut=$OUT")
    if [[ "$shots" -gt 0 ]]; then args+=("-PerfShots=$shots"); else args+=(-PerfDrive=1); fi
    echo "Capturing $job (watchdog ${timeout}s)"
    "$EDITOR" "$PROJECT" /Game/Selene/Maps/Town -game -windowed -ResX=1920 -ResY=1080 \
        -unattended -nosplash -nosound "-abslog=$OUT/$job.engine.log" "${args[@]}" >"$OUT/$job.process.log" 2>&1 &
    child=$!
    (
        for ((elapsed=0; elapsed<timeout; elapsed++)); do
            kill -0 "$child" 2>/dev/null || exit 0
            sleep 1
        done
        echo "Watchdog expired for $job" >"$OUT/$job.timeout"
        kill -TERM "$child" 2>/dev/null || true
        sleep 5
        kill -KILL "$child" 2>/dev/null || true
    ) &
    watchdog=$!
    rc=0
    wait "$child" || rc=$?
    child=''
    kill "$watchdog" 2>/dev/null || true
    wait "$watchdog" 2>/dev/null || true
    watchdog=''
    echo "$rc" >"$OUT/$job.exitcode"
    if [[ "$rc" -ne 0 || -f "$OUT/$job.timeout" ]]; then failed=1; fi
done <<<"$JOBS"
trap - INT TERM
# Process success alone is insufficient: fail closed on missing/incomplete artifacts.
python3 - "$OUT" <<'PY' || failed=1
import json
from pathlib import Path
import sys
root = Path(sys.argv[1])
metadata = []
failed = False
for path in root.glob('*.meta.json'):
    try:
        item = json.loads(path.read_text())
        if not isinstance(item, dict):
            raise ValueError('metadata must be an object')
        metadata.append(item)
    except (OSError, ValueError) as exc:
        print(f'Invalid metadata {path.name}: {exc}')
        failed = True
for route, count in [('R1', 6), ('R2', 12), ('R3', 3), ('EW', 0)]:
    for camera in (('3P', '1P') if count else ('3P',)):
        job = f'{route}_{camera}'
        matches = [m for m in metadata if m.get('route') == route and m.get('camera') == camera]
        ok = len(matches) == 1
        m = matches[0] if ok else {}
        ok = ok and m.get('status') == 'complete' and not m.get('error') and m.get('configuration_verified') is True
        ok = ok and (root / f'{job}.exitcode').read_text().strip() == '0' and not (root / f'{job}.timeout').exists()
        if count:
            manifest = root / 'shots' / f'{job}.manifest.json'
            try:
                entries = json.loads(manifest.read_text()).get('shots', []) if manifest.exists() else []
                if not isinstance(entries, list) or any(not isinstance(e, dict) for e in entries):
                    raise ValueError('shots must be an array of objects')
            except (OSError, ValueError, AttributeError) as exc:
                print(f'Invalid manifest {manifest.name}: {exc}')
                entries = []
            expected = [f'{job}_{i:02d}.png' for i in range(1, count + 1)]
            found = sum((root / 'shots' / name).is_file() and (root / 'shots' / name).stat().st_size > 0 for name in expected)
            ok = ok and m.get('mode') == 'shots' and m.get('shot_count') == count and len(entries) == count
            ok = ok and [e.get('filename') for e in entries] == expected and found == count
            print(f'{job}: {found}/{count} shots — {"OK" if ok else "FAILED"}')
        else:
            seconds = m.get('walk_seconds')
            ok = ok and m.get('mode') == 'drive' and isinstance(seconds, (int, float)) and seconds > 0
            duration = f'{int(seconds) // 60}:{int(seconds) % 60:02d}' if isinstance(seconds, (int, float)) else 'missing'
            expected = isinstance(seconds, (int, float)) and 300 <= seconds <= 360
            ok = ok and expected
            print(f'EW: {duration} vs expected 5–6 min ({"within range" if expected else "outside range"}) — {"OK" if ok else "FAILED"}')
        failed |= not ok
print(f'Artifacts: {root}')
sys.exit(1 if failed else 0)
PY
exit "$failed"
