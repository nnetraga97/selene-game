#!/bin/bash
# Session 5 native slot probe. Never run alongside another Selene editor.
set -eu
test -f "$PWD/Selene.uproject"
out="$PWD/Saved/Clips/session-5"
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
perl -e 'alarm 900; exec @ARGV' \
    '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor' \
    "$PWD/Selene.uproject" /Game/Selene/Maps/Town \
    "-ExecCmds=py __import__('runpy').run_path(__import__('unreal').Paths.project_dir()+'Tools/Unreal/gasp_slot_probe.py')" \
    -unattended -nop4 -nosplash \
    "-abslog=$out/slot-probe-editor.log" > "$out/slot-probe-console.log" 2>&1
