#!/bin/bash
# Guard every launch; never terminate an editor belonging to another session.
set -eu
stage="$1"
out="$PWD/Saved/Chars/session-3"
test -f "$PWD/Selene.uproject"
mkdir -p "$out"
test ! -e "$out/$stage-editor.log"
started=$SECONDS
while pgrep -fl 'UnrealEditor.*Selene.uproject' >> "$out/$stage-guard.log"; do
    if (( SECONDS - started >= 900 )); then echo 'Existing Selene editor still running; stopping'; exit 2; fi
    sleep 15
done
until mkdir /tmp/selene-unreal.lock 2>/dev/null; do
    if (( SECONDS - started >= 900 )); then echo 'Unreal lock occupied; stopping'; exit 2; fi
    sleep 15
done
trap 'rmdir /tmp/selene-unreal.lock' EXIT
if pgrep -fl 'UnrealEditor.*Selene.uproject' >> "$out/$stage-guard.log"; then exit 2; fi
date -u >> "$out/$stage-guard.log"
bin='/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac'
set +e
case "$stage" in
    cleanup|create|inventory)
        SELENE_CHARS_STAGE="$stage" perl -e 'alarm 600; exec @ARGV' "$bin/UnrealEditor-Cmd" "$PWD/Selene.uproject" \
            -run=pythonscript "-script=$PWD/Tools/Unreal/chars_session3.py" -unattended -nop4 -nosplash -nullrhi \
            "-abslog=$out/$stage-editor.log" > "$out/$stage-console.log" 2>&1 ;;
    clips|correct|measure|materials|verify)
        SELENE_CHARS_STAGE="$stage" perl -e 'alarm 600; exec @ARGV' "$bin/UnrealEditor-Cmd" "$PWD/Selene.uproject" \
            -run=pythonscript "-script=$PWD/Tools/Unreal/chars_session3_hookup.py" -unattended -nop4 -nosplash -nullrhi \
            "-abslog=$out/$stage-editor.log" > "$out/$stage-console.log" 2>&1 ;;
    build)
        perl -e 'alarm 600; exec @ARGV' '/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh' SeleneEditor Mac Development "$PWD/Selene.uproject" -waitmutex \
            > "$out/$stage-editor.log" 2>&1 ;;
    game-Fixer|game-Courier|game-Champion|game-Fixer-corrected|game-Courier-corrected)
        character="${stage#game-}"
        character="${character%-corrected}"
        duration=75
        if [ "$character" = Champion ]; then duration=40; fi
        perl -e "alarm $duration; exec @ARGV" "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/Town \
            -game "-ExecCmds=selene.Character $character,selene.AutoWalk 1,selene.AutoShots 1" \
            -windowed -ResX=1280 -ResY=900 -unattended -nop4 -nosplash \
            "-abslog=$out/$stage-editor.log" > "$out/$stage-console.log" 2>&1 ;;
    *) echo "Unknown stage: $stage" >&2; exit 1 ;;
esac
rc=$?
echo "$rc" > "$out/$stage-exit.txt"
exit "$rc"
