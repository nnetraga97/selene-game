#!/bin/bash
# Sequential packaged-game runs; does not build, package, or talk to an editor.
set -euo pipefail
usage() {
  cat <<'USAGE'
Usage: run_matrix.sh APP.app MAP ROUTE [ROUTE ...] [options]
  --res-x N --res-y N       Output pixels (default 1920 1080)
  --out DIR                 Fresh matrix directory (default Tools/Perf/runs/<UTC-id>)
  --reports DIR             Report destination (default <out>/reports)
  --archive DIR             Fresh raw archive (default evidence/selene-perf/<UTC-id>)
  --build Shipping|Development  Expected metadata build (default Shipping)
  --laps N --warmup S --speed CM_S  Defaults: 3, 15, 150
  --time-flow SPEED          Additional 3P/noon run per route (default 60)
  --timeout S               Override computed watchdog (must meet calculated minimum)
  --layout FILE             Route lengths source (default Design/Blockout/layout.json)
  --route-length-cm CM       Explicit length for custom routes (applies to all routes)
  --nosound                 Disable audio for every run (off by default)
USAGE
}
if [[ ${1:-} == --help ]]; then usage; exit 0; fi
[[ $# -ge 3 ]] || { usage; exit 2; }
app=$1; map=$2; shift 2
routes=()
while [[ $# -gt 0 && $1 != --* ]]; do routes+=("$1"); shift; done
[[ ${#routes[@]} -gt 0 ]] || { usage; exit 2; }
script_dir=$(cd "$(dirname "$0")" && pwd)
run_id=$(python3 -c 'import datetime,uuid; print(datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S")+"-"+uuid.uuid4().hex[:8])')
out="$script_dir/runs/$run_id"; reports=''; archive=''; build=Shipping
res_x=1920; res_y=1080; laps=3; warmup=15; speed=150; flow=60; timeout_s=''
layout="$script_dir/../../Design/Blockout/layout.json"; route_length=''
extra=()
while [[ $# -gt 0 ]]; do
  case $1 in
    --nosound) extra+=(-nosound); shift ;;
    --res-x|--res-y|--out|--reports|--archive|--build|--laps|--warmup|--speed|--time-flow|--timeout|--layout|--route-length-cm)
      [[ $# -ge 2 ]] || { echo "Missing value: $1" >&2; exit 2; }
      case $1 in
        --res-x) res_x=$2 ;; --res-y) res_y=$2 ;; --out) out=$2 ;;
        --reports) reports=$2 ;; --archive) archive=$2 ;; --build) build=$2 ;;
        --laps) laps=$2 ;; --warmup) warmup=$2 ;; --speed) speed=$2 ;;
        --time-flow) flow=$2 ;; --timeout) timeout_s=$2 ;;
        --layout) layout=$2 ;; --route-length-cm) route_length=$2 ;;
      esac
      shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done
[[ $build == Shipping || $build == Development ]] || { echo 'Invalid build' >&2; exit 2; }
# Read the bundle executable instead of assuming its Shipping filename.
exe=$(python3 - "$app" "$res_x" "$res_y" "$laps" "$warmup" "$speed" "$flow" "$script_dir" <<'PY'
from pathlib import Path
import math, plistlib, sys
app = Path(sys.argv[1]).resolve()
assert app.suffix == '.app', 'expected a packaged .app'
with (app / 'Contents/Info.plist').open('rb') as f:
    name = plistlib.load(f)['CFBundleExecutable']
exe = app / 'Contents/MacOS' / name
assert exe.is_file(), f'missing executable: {exe}'
sys.path.insert(0, sys.argv[-1])
from matrix_config import require_unsandboxed
require_unsandboxed(app)
for i, text in enumerate(sys.argv[2:-1]):
    value = float(text)
    assert math.isfinite(value) and (value >= 0 if i in (3, 5) else value > 0), 'invalid numeric option'
    if i in (0, 1, 2):
        assert value.is_integer(), 'resolution and laps must be integers'
print(exe)
PY
)
[[ -x $exe ]] || { echo "Not executable: $exe" >&2; exit 2; }
timeouts=()
for route in "${routes[@]}"; do
  timeouts+=("$(python3 "$script_dir/matrix_config.py" "$route" "$layout" "$speed" "$laps" "$warmup" "$timeout_s" "$route_length")")
done
# A new directory prevents stale successful logs from being attributed to a failed launch.
[[ ! -e $out ]] || { echo "Output directory already exists: $out" >&2; exit 2; }
mkdir -p "$out"
out=$(cd "$out" && pwd)
reports=${reports:-"$out/reports"}
printf '%s\n' 'PERFORMANCE RUN: Blender, builds, and other GPU work must be idle.'
printf '%s\n' "Outputs: $out"
index=0
run_one() {
  local route=$1 cam=$2 hour=$3 flow_value=${4:-}
  index=$((index + 1))
  local run_dir="$out/run-$(printf '%04d' "$index")"
  mkdir "$run_dir"
  local args=("$exe" "$map" -fullscreen "-ResX=$res_x" "-ResY=$res_y" -unattended
    "-PerfRoute=$route" "-PerfCam=$cam" "-PerfHour=$hour" "-PerfLaps=$laps"
    "-PerfWarmup=$warmup" "-PerfSpeed=$speed" "-PerfOut=$run_dir")
  [[ -z $flow_value ]] || args+=("-PerfTimeFlow=$flow_value")
  # Bash 3.2 with nounset requires guarded expansion of empty arrays.
  [[ ${#extra[@]} -eq 0 ]] || args+=("${extra[@]}")
  printf 'Run %s: route=%s cam=%s hour=%s flow=%s\n' "$index" "$route" "$cam" "$hour" "${flow_value:-paused}"
  python3 - "$run_dir" "$timeout_s" "${args[@]}" <<'PY'
import json, os, signal, subprocess, sys, time
from pathlib import Path
folder, timeout = Path(sys.argv[1]), float(sys.argv[2])
args = sys.argv[3:]
entry = dict(command=args, timeout_seconds=timeout, started_unix=time.time(), returncode=None, frame_logs=[])
record = folder / 'launch.json'
record.write_text(json.dumps(entry, indent=2))
with (folder / 'process.log').open('wb') as stream:
    try:
        process = subprocess.Popen(args, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            entry['returncode'] = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            entry['error'] = 'watchdog timeout'
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            entry['returncode'] = 124
    except OSError as exc:
        entry.update(returncode=127, error=str(exc))
entry['elapsed_seconds'] = time.time() - entry['started_unix']
entry['frame_logs'] = [str(p) for p in sorted(folder.glob('*.frames.csv'))]
entry['artifacts'] = [str(p) for p in sorted(folder.iterdir()) if p.is_file()]
record.write_text(json.dumps(entry, indent=2) + '\n')
print('Process exit:', entry['returncode'])
PY
}
route_index=0
for route in "${routes[@]}"; do
  timeout_s=${timeouts[$route_index]}
  route_index=$((route_index + 1))
  printf 'Watchdog for %s: %s seconds\n' "$route" "$timeout_s"
  for cam in 3P 1P; do
    for hour in 12 17.5 19 22; do run_one "$route" "$cam" "$hour"; done
  done
  run_one "$route" 3P 12 "$flow"
done
python3 - "$out" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
(root / 'matrix.json').write_text(json.dumps([json.loads(p.read_text()) for p in sorted(root.glob('run-*/launch.json'))], indent=2) + '\n')
PY
shopt -s nullglob
logs=("$out"/run-*/*.frames.csv)
profiles=("$out"/run-*/*.profile.csv)
summary=(python3 "$script_dir/summarize.py")
[[ ${#logs[@]} -eq 0 ]] || summary+=("${logs[@]}")
summary+=(--manifest "$out/matrix.json" --reports "$reports" --build "$build" --run-id "$run_id")
[[ -z $archive ]] || summary+=(--archive "$archive")
[[ ${#profiles[@]} -eq 0 ]] || summary+=(--profiler "${profiles[@]}")
"${summary[@]}"
