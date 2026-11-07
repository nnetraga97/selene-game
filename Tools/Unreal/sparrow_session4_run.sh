#!/bin/bash
# Session 4 only: guard, lock, alarm, immutable logs, and per-launch exit evidence.
set -eu
stage="$1"
out="$PWD/Saved/Sparrow/session-4"
test -f "$PWD/Selene.uproject"
test ! -e "$out/$stage-editor.log"
started=$SECONDS
while pgrep -fl 'UnrealEditor.*Selene.uproject' >> "$out/$stage-guard.log"; do
    date -u >> "$out/$stage-guard.log"
    if (( SECONDS - started >= 900 )); then
        echo "waiting for the user's game to close"; exit 2
    fi
    sleep 30
done
until mkdir /tmp/selene-unreal.lock 2>/dev/null; do
    if (( SECONDS - started >= 900 )); then
        echo 'Unreal lock occupied; no launch'; exit 2
    fi
    sleep 15
done
trap 'rmdir /tmp/selene-unreal.lock' EXIT
if pgrep -fl 'UnrealEditor.*Selene.uproject' >> "$out/$stage-guard.log"; then exit 2; fi
date -u >> "$out/$stage-guard.log"
bin='/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac'
set +e
case "$stage" in
    clips|verify)
        script=sparrow_session4_clips.py
        if [ "$stage" = verify ]; then script=sparrow_session4_verify.py; fi
        perl -e 'alarm 900; exec @ARGV' "$bin/UnrealEditor-Cmd" "$PWD/Selene.uproject" \
            -run=pythonscript "-script=$PWD/Tools/Unreal/$script" \
            -unattended -nop4 -nosplash -nullrhi \
            "-abslog=$out/$stage-editor.log" > "$out/$stage-console.log" 2>&1 ;;
    game-Sparrow|game-Champion|game-Angel)
        character="${stage#game-}"
        duration=45
        if [ "$character" = Sparrow ]; then duration=75; fi
        perl -e "alarm $duration; exec @ARGV" "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/Town \
            -game "-ExecCmds=selene.Character $character,selene.AutoWalk 1,selene.AutoShots 1" \
            -unattended -nop4 -nosplash -windowed -ResX=1280 -ResY=900 \
            "-abslog=$out/$stage-editor.log" > "$out/$stage-console.log" 2>&1 ;;
    *) echo "Unknown stage: $stage" >&2; exit 1 ;;
esac
rc=$?
echo "$rc" > "$out/$stage-exit.txt"
date -u >> "$out/$stage-guard.log"
exit "$rc"
