#!/bin/bash
# Session 4: guarded launches; no export/import/batch-retarget replay.
set -eu
test -f "$PWD/Selene.uproject"
mode="$1"
out="$PWD/Saved/Clips/session-4"
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
    measure)
        perl -e 'alarm 900; exec @ARGV' \
            '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd' \
            "$PWD/Selene.uproject" -run=pythonscript \
            "-script=$PWD/Tools/Unreal/gasp_clip_measure.py" \
            -unattended -nop4 -nosplash -nullrhi \
            "-abslog=$out/$mode-editor.log" > "$out/$mode-console.log" 2>&1
        ;;
    correct-loops|verify-loops)
        export SELENE_LOOP_MODE="${mode%-loops}"
        perl -e 'alarm 900; exec @ARGV' \
            '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd' \
            "$PWD/Selene.uproject" -run=pythonscript \
            "-script=$PWD/Tools/Unreal/gasp_loop_in_place.py" \
            -unattended -nop4 -nosplash -nullrhi \
            "-abslog=$out/$mode-editor.log" > "$out/$mode-console.log" 2>&1
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
            "-ExecCmds=py __import__('runpy').run_path(__import__('unreal').Paths.project_dir()+'Tools/Unreal/gasp_corrected_motion_shots.py')" \
            -unattended -nop4 -nosplash \
            "-abslog=$out/$mode-editor.log" > "$out/$mode-console.log" 2>&1
        ;;
    *) echo "Unknown mode: $mode" >&2; exit 2 ;;
esac
