#!/bin/bash
# Immutable evidence labels; guard all launches and never signal an existing game.
set -eu
stage="${1:?stage}"; label="${2:?fresh-label}"; hero="${3:-Nerine}"; advanced="${4:-0}"
case "$label" in *[!a-zA-Z0-9_-]*|'') exit 2;; esac
out="$PWD/Saved/NerineHookup/session-1/Nerine/$label"
test -f "$PWD/Selene.uproject"
mkdir -p "$out"
test ! -e "$out/console.log"
started=$SECONDS
while pgrep -fl 'UnrealEditor.*Selene.uproject' >> "$out/guard.log"; do
 if (( SECONDS - started >= 900 )); then echo 'User game still running; no launch'; exit 2; fi
 sleep 15
done
until mkdir /tmp/selene-unreal.lock 2>/dev/null; do
 if (( SECONDS - started >= 900 )); then echo 'Lock occupied; no launch'; exit 2; fi
 sleep 15
done
trap 'rmdir /tmp/selene-unreal.lock' EXIT
if pgrep -fl 'UnrealEditor.*Selene.uproject' >> "$out/guard.log"; then exit 2; fi
bin='/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac'
export SELENE_CHAR=Nerine SELENE_CHAR_MESH='/Game/Assets/nerine/nerine/SkeletalMeshes/nerine'
export SELENE_STAGE_REPORT="$out/report.json" SELENE_NERINE_LABEL="$label"
unset SELENE_CHAR_POSE_YAW SELENE_CHAR_BIND_QUAT SELENE_CHAR_OUTPUT_ROOT SELENE_CHAR_EXPECTED_PACKAGES
set +e
case "$stage" in
python)
 script="${5:?script}"
 perl -e 'alarm 240; exec @ARGV' "$bin/UnrealEditor-Cmd" "$PWD/Selene.uproject" -run=pythonscript "-script=$PWD/Tools/Unreal/$script.py" -unattended -nop4 -nosplash -nullrhi "-abslog=$out/editor.log" > "$out/console.log" 2>&1 ;;
game)
 perl -e 'alarm 120; exec @ARGV' "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/Town -game "-ExecCmds=selene.Character $hero,selene.AdvancedMovement $advanced,selene.AnimMatchLabel ../../NerineHookup/session-1/Nerine/$label/standard,selene.AnimMatch 1,selene.MoveTestExitAfterAnimMatch 1,selene.SecondaryDebug 1,t.MaxFPS 30,r.MotionBlurQuality 0" -unattended -nop4 -nosplash -RenderOffscreen -windowed -ResX=960 -ResY=900 "-abslog=$out/editor.log" > "$out/console.log" 2>&1 ;;
*) exit 2;;
esac
rc=$?
echo "$rc" > "$out/exit.txt"
if [[ "$stage" == game && ( "$rc" == 142 || "$rc" == 0 ) ]]; then
 count=$(find "$out/standard/$hero" -name '*.png' | wc -l | tr -d ' ')
 test "$count" = 21
 exit $?
fi
exit "$rc"
