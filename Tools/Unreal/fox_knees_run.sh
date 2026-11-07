#!/bin/bash
# Dedicated actual-game close-up capture. Never alter the launch script while active.
set -eu
out="$PWD/Saved/FoxHookup/session-1/knees"
test -f "$PWD/Selene.uproject"
mkdir -p "$out"
test ! -e "$out/console.log"
# AutoShots has no label: refuse to overwrite any prior Fox frames.
if find "$PWD/Saved/AutoShots" -name 'Fox_*.png' -print -quit | grep -q .; then echo 'Existing Fox autos, no launch'; exit 2; fi
started=$SECONDS
while pgrep -fl 'UnrealEditor.*Selene.uproject' >> "$out/guard.log"; do
 if (( SECONDS-started >= 900 )); then exit 2; fi
 sleep 15
done
until mkdir /tmp/selene-unreal.lock 2>/dev/null; do
 if (( SECONDS-started >= 900 )); then exit 2; fi
 sleep 15
done
trap 'rmdir /tmp/selene-unreal.lock' EXIT
if pgrep -fl 'UnrealEditor.*Selene.uproject' >> "$out/guard.log"; then exit 2; fi
set +e
perl -e 'alarm 90; exec @ARGV' '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor' "$PWD/Selene.uproject" /Game/Selene/Maps/Town -game '-ExecCmds=selene.Character Fox,selene.AdvancedMovement 0,selene.AnimMatchLabel fox-knees,selene.AnimMatch 1,selene.AutoShots 0.25,selene.SecondaryDebug 1,t.MaxFPS 30,r.MotionBlurQuality 0,fov 40' -unattended -nop4 -nosplash -windowed -ResX=1200 -ResY=1100 "-abslog=$out/editor.log" > "$out/console.log" 2>&1
rc=$?
echo "$rc" > "$out/exit.txt"
if [[ "$rc" != 142 && "$rc" != 0 ]]; then exit "$rc"; fi
python3 - <<'PY'
import hashlib,json
from pathlib import Path
root=Path.cwd();out=root/'Saved/FoxHookup/session-1/knees';dest=out/'captures';dest.mkdir()
rows=[]
for p in sorted((root/'Saved/AutoShots').glob('Fox_*.png')):
 h=hashlib.sha256(p.read_bytes()).hexdigest();q=dest/p.name;p.rename(q);assert hashlib.sha256(q.read_bytes()).hexdigest()==h;rows.append({'file':q.name,'sha256':h})
(out/'manifest.json').write_text(json.dumps(rows,indent=2)+'\n');print('Moved',len(rows),'new Fox close-ups')
PY
