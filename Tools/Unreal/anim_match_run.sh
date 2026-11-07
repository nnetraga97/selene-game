#!/bin/bash
# Guard every build/editor/game invocation; immutable per-stage evidence.
set -eu
stage="$1"
label="${2:-before}"
out="$PWD/Saved/AnimMatch/session-1"
test -f "$PWD/Selene.uproject"
mkdir -p "$out"
test ! -e "$out/$stage-$label-console.log"
started=$SECONDS
while pgrep -fl 'UnrealEditor.*Selene.uproject' >> "$out/$stage-$label-guard.log"; do
    if (( SECONDS - started >= 900 )); then echo "waiting for the user's game to close"; exit 2; fi
    sleep 15
done
until mkdir /tmp/selene-unreal.lock 2>/dev/null; do
    if (( SECONDS - started >= 900 )); then echo 'Unreal lock occupied; no launch'; exit 2; fi
    sleep 15
done
trap 'rmdir /tmp/selene-unreal.lock' EXIT
if pgrep -fl 'UnrealEditor.*Selene.uproject' >> "$out/$stage-$label-guard.log"; then exit 2; fi
bin='/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac'
date -u >> "$out/$stage-$label-guard.log"
set +e
case "$stage" in
build)
    perl -e 'alarm 600; exec @ARGV' '/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh' SeleneEditor Mac Development "$PWD/Selene.uproject" -waitmutex > "$out/$stage-$label-console.log" 2>&1 ;;
audit|settings|pose-api|fix)
    script=anim_match_audit.py
    if [ "$stage" = settings ]; then script=anim_match_settings.py; fi
    if [ "$stage" = pose-api ]; then script=anim_match_pose_api.py; fi
    if [ "$stage" = fix ]; then script=anim_match_fix.py; fi
    perl -e 'alarm 180; exec @ARGV' "$bin/UnrealEditor-Cmd" "$PWD/Selene.uproject" -run=pythonscript "-script=$PWD/Tools/Unreal/$script" -unattended -nop4 -nosplash -nullrhi "-abslog=$out/$stage-$label-editor.log" > "$out/$stage-$label-console.log" 2>&1 ;;
game-*)
    hero="${stage#game-}"
    perl -e 'alarm 90; exec @ARGV' "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/Town -game "-ExecCmds=selene.Character $hero,selene.AnimMatchLabel $label,selene.AnimMatch 1,t.MaxFPS 30,r.MotionBlurQuality 0" -unattended -nop4 -nosplash -windowed -ResX=960 -ResY=900 "-abslog=$out/$stage-$label-editor.log" > "$out/$stage-$label-console.log" 2>&1 ;;
*) echo "Unknown stage $stage"; exit 1 ;;
esac
rc=$?
echo "$rc" > "$out/$stage-$label-exit.txt"
date -u >> "$out/$stage-$label-guard.log"
if [[ "$stage" == game-* && "$rc" == 142 ]]; then
    count=$(find "$PWD/Saved/AnimMatch/Captures/$label/${stage#game-}" -name '*.png' | wc -l | tr -d ' ')
    if [ "$count" = 21 ]; then exit 0; fi
    echo "Incomplete comparison: $count / 21 captures"; exit 3
fi
exit "$rc"
