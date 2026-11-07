#!/bin/bash
# One guarded stage per invocation. Never terminate an already-running Selene.
set -eu
stage="${1:?stage}"; label="${2:?fresh evidence label}"; hero="${3:-Champion}"; advanced="${4:-1}"
case "$label" in *[!a-zA-Z0-9_-]*|'') echo 'Invalid label'; exit 2;; esac
test -f "$PWD/Selene.uproject"
out="$PWD/Saved/MovementTest/$label"
mkdir -p "$out"
test ! -e "$out/console.log"
started=$SECONDS
while pgrep -fl 'UnrealEditor.*Selene.uproject' >> "$out/guard.log"; do
    if (( SECONDS - started >= 900 )); then echo 'User game still running; no launch'; exit 2; fi
    sleep 15
done
until mkdir /tmp/selene-unreal.lock 2>/dev/null; do
    if (( SECONDS - started >= 900 )); then echo 'Unreal lock occupied; no launch'; exit 2; fi
    sleep 15
done
trap 'rmdir /tmp/selene-unreal.lock' EXIT
if pgrep -fl 'UnrealEditor.*Selene.uproject' >> "$out/guard.log"; then exit 2; fi
bin='/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac'
date -u >> "$out/guard.log"
set +e
case "$stage" in
build)
    perl -e 'alarm 600; exec @ARGV' '/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh' SeleneEditor Mac Development "$PWD/Selene.uproject" -waitmutex > "$out/console.log" 2>&1 ;;
poses)
    perl -e 'alarm 180; exec @ARGV' "$bin/UnrealEditor-Cmd" "$PWD/Selene.uproject" -run=pythonscript "-script=$PWD/Tools/Unreal/movement_pose_audit.py" -unattended -nop4 -nosplash -nullrhi "-abslog=$out/editor.log" > "$out/console.log" 2>&1 ;;
map)
    perl -e 'alarm 180; exec @ARGV' "$bin/UnrealEditor-Cmd" "$PWD/Selene.uproject" -run=pythonscript "-script=$PWD/Tools/Unreal/movement_test_level.py" -unattended -nop4 -nosplash -nullrhi "-abslog=$out/editor.log" > "$out/console.log" 2>&1 ;;
baseline|regression)
    perl -e 'alarm 120; exec @ARGV' "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/Town -game "-ExecCmds=selene.Character $hero,selene.AdvancedMovement 0,selene.AnimMatchLabel movement-$label,selene.AnimMatch 1,selene.MoveTestExitAfterAnimMatch 1,selene.SecondaryDebug 1,t.MaxFPS 30,r.MotionBlurQuality 0" -unattended -nop4 -nosplash -windowed -ResX=960 -ResY=900 "-abslog=$out/editor.log" > "$out/console.log" 2>&1 ;;
momentum|dash|slide|extra|wall|mantle|sequence|roster)
    perl -e 'alarm 90; exec @ARGV' "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/MovementTest -game "-ExecCmds=selene.Character $hero,selene.AdvancedMovement $advanced,selene.MoveTestLabel $label,selene.MoveTestStage $stage,selene.MoveTest 1,selene.SecondaryDebug 1,t.MaxFPS 30,r.MotionBlurQuality 0" -unattended -nop4 -nosplash -windowed -ResX=960 -ResY=900 "-abslog=$out/editor.log" > "$out/console.log" 2>&1 ;;
*) echo 'Unknown stage'; exit 2 ;;
esac
rc=$?
echo "$rc" > "$out/exit.txt"
date -u >> "$out/guard.log"
if [[ "$stage" == baseline || "$stage" == regression ]]; then
    if [[ "$rc" != 142 && "$rc" != 0 ]]; then exit "$rc"; fi
    count=$(find "$PWD/Saved/AnimMatch/Captures/movement-$label/$hero" -name '*.png' | wc -l | tr -d ' ')
    test "$count" = 21
    exit $?
fi
if [[ "$rc" == 142 && -f "$out/complete.txt" ]]; then exit 0; fi
exit "$rc"
