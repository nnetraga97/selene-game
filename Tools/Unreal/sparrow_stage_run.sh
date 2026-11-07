#!/bin/bash
# Guard each Sparrow stage; preserve its first log and release only our lock.
set -eu
stage="$1"
out="$PWD/Saved/Sparrow/session-3"
test -f "$PWD/Selene.uproject"
test ! -e "$out/$stage-editor.log"
started=$SECONDS
while pgrep -fl 'UnrealEditor.*Selene.uproject' >> "$out/$stage-guard.log"; do
    if (( SECONDS - started >= 900 )); then
        echo "waiting for the user's game to close"; exit 2
    fi
    sleep 30
done
until mkdir /tmp/selene-unreal.lock 2>/dev/null; do sleep 15; done
trap 'rmdir /tmp/selene-unreal.lock' EXIT
if pgrep -fl 'UnrealEditor.*Selene.uproject' >> "$out/$stage-guard.log"; then exit 2; fi
date -u >> "$out/$stage-guard.log"
bin='/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac'
case "$stage" in
    inspection)
        perl -e 'alarm 900; exec @ARGV' "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/Town \
            "-ExecCmds=py __import__('runpy').run_path(__import__('unreal').Paths.project_dir()+'Tools/Unreal/sparrow_inspect.py')" \
            -unattended -nop4 -nosplash -windowed -ResX=1200 -ResY=1200 \
            "-abslog=$out/$stage-editor.log" > "$out/$stage-console.log" 2>&1 ;;
    retarget|cook_label)
        perl -e 'alarm 900; exec @ARGV' "$bin/UnrealEditor-Cmd" "$PWD/Selene.uproject" \
            -run=pythonscript "-script=$PWD/Tools/Unreal/sparrow_$stage.py" \
            -unattended -nop4 -nosplash -nullrhi \
            "-abslog=$out/$stage-editor.log" > "$out/$stage-console.log" 2>&1 ;;
    game-*)
        character="${stage#game-}"
        shots=0
        duration=4
        camera=""
        if [ "$character" = Sparrow-camera ]; then
            character=Sparrow
            camera=',getall SelenePlayerController ControlRotation,set SelenePlayerController ControlRotation (Pitch=-15),getall SelenePlayerController ControlRotation'
        fi
        if [ "$character" = Sparrow ]; then shots=1; duration=24; fi
        perl -e 'alarm 900; exec @ARGV' "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/Town \
            -game "-ExecCmds=selene.Character $character,selene.AutoWalk 1,selene.AutoShots $shots,selene.SecondaryDebug 1$camera" \
            -benchmark "-seconds=$duration" -fps=30 -unattended -nop4 -nosplash -windowed -ResX=1280 -ResY=900 \
            "-abslog=$out/$stage-editor.log" > "$out/$stage-console.log" 2>&1 ;;
    *) echo "Unknown stage: $stage" >&2; exit 1 ;;
esac
