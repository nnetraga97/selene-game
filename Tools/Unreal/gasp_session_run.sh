#!/bin/bash
# Guarded session-3 launches. Call from the Selene root; logs stay in Saved/Clips.
set -eu
test -f "$PWD/Selene.uproject"
mode="$1"
run_name="$mode${2:+-$2}"
export SELENE_SHOTS_SUFFIX="${2:+-$2}"
out="$PWD/Saved/Clips/session-3"
mkdir -p "$out"
if pgrep -fl 'UnrealEditor.*Selene.uproject'; then
    echo 'Selene is already running; stopping.' >&2
    exit 2
fi
until mkdir /tmp/selene-unreal.lock 2>/dev/null; do sleep 15; done
trap 'rmdir /tmp/selene-unreal.lock' EXIT
if pgrep -fl 'UnrealEditor.*Selene.uproject'; then
    echo 'Selene started before lock acquisition; stopping.' >&2
    exit 2
fi
case "$mode" in
    verify|retarget)
        perl -e 'alarm 900; exec @ARGV' \
            '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd' \
            "$PWD/Selene.uproject" -run=pythonscript \
            "-script=$PWD/Tools/Unreal/gasp_clip_${mode}.py" \
            -ForceDependsGathering -unattended -nop4 -nosplash -nullrhi \
            "-abslog=$out/$run_name-editor.log" > "$out/$run_name-console.log" 2>&1
        ;;
    motion-Champion|motion-Angel)
        export SELENE_CHAR="${mode#motion-}"
        if [ "$SELENE_CHAR" = Champion ]; then
            export SELENE_CHAR_MESH='/Game/Assets/festival-champion-p2/festival-champion-p2/SkeletalMeshes/festival-champion-p2'
        else
            export SELENE_CHAR_MESH='/Game/Assets/angel-warrior/angel-warrior/SkeletalMeshes/angel-warrior'
        fi
        perl -e 'alarm 900; exec @ARGV' \
            '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor' \
            "$PWD/Selene.uproject" /Game/Selene/Maps/Town \
            "-ExecCmds=py __import__('runpy').run_path(__import__('unreal').Paths.project_dir()+'Tools/Unreal/gasp_motion_shots.py')" \
            -unattended -nop4 -nosplash \
            "-abslog=$out/$run_name-editor.log" > "$out/$run_name-console.log" 2>&1
        ;;
    *) echo "Unknown mode: $mode" >&2; exit 2 ;;
esac
