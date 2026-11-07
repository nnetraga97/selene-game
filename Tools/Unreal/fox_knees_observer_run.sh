#!/bin/bash
# Dedicated actual-game close-up capture. Never alter the launch script while active.
set -eu
out="$PWD/Saved/FoxHookup/session-1/knees-observer"
test -f "$PWD/Selene.uproject"
mkdir -p "$out"
test ! -e "$out/console.log"
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
export SELENE_FOX_KNEE_OUTPUT="$out/captures"
set +e
perl -e 'alarm 90; exec @ARGV' '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor' "$PWD/Selene.uproject" /Game/Selene/Maps/Town -game "-ExecCmds=selene.Character Fox,selene.AdvancedMovement 0,selene.AnimMatchLabel fox-knees-observer,selene.AnimMatch 1,selene.SecondaryDebug 1,t.MaxFPS 30,r.MotionBlurQuality 0,fov 40,py __import__('runpy').run_path(__import__('unreal').Paths.project_dir()+'Tools/Unreal/fox_knee_observer.py')" -unattended -nop4 -nosplash -windowed -ResX=1200 -ResY=1100 "-abslog=$out/editor.log" > "$out/console.log" 2>&1
rc=$?
echo "$rc" > "$out/exit.txt"
if [[ "$rc" != 142 && "$rc" != 0 ]]; then exit "$rc"; fi
exit 0
