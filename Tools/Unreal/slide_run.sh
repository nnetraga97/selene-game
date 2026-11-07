#!/bin/bash
set -eu
cd "$(dirname "$0")/../.."
root="$PWD"
out="$root/Saved/SlidePass/${SELENE_SLIDE_SESSION:-session-1}"
mkdir -p "$out"
stage="${1:?export|import|verify|capture|build}"
engine='/Users/Shared/Epic Games/UE_5.8/Engine'
project="$root/Selene.uproject"
pattern='UnrealEditor.*Selene.uproject'
if [ "$stage" = export ]; then
 project='/Users/nicknetraganti/Documents/Unreal Projects/GameAnimationSample/GameAnimationSample.uproject'
 pattern='UnrealEditor.*GameAnimationSample'
fi
if pgrep -fl "$pattern"; then echo 'Project already open; do non-Unreal work and wait as brief requires.'; exit 2; fi
until mkdir /tmp/selene-unreal.lock 2>/dev/null; do sleep 15; done
trap 'rmdir /tmp/selene-unreal.lock' EXIT
if pgrep -fl "$pattern"; then exit 2; fi
export SELENE_CLIPS_ROOT="$root"
if [ "$stage" = build ]; then
 perl -e 'alarm 600; exec @ARGV' "$engine/Build/BatchFiles/Mac/Build.sh" SeleneEditor Mac Development "$project" -WaitMutex > "$out/build.log" 2>&1
elif [ "$stage" = capture ] || [ "$stage" = runtime_probe ]; then
 map=/Game/Selene/Maps/Town
 if [ "$stage" = runtime_probe ]; then map=/Game/Selene/Maps/MovementTest; fi
 perl -e 'alarm 600; exec @ARGV' "$engine/Binaries/Mac/UnrealEditor" "$project" "$map" -RenderOffscreen -unattended -nop4 -nosplash "-ExecCmds=py __import__('runpy').run_path(__import__('unreal').Paths.project_dir()+'Tools/Unreal/slide_$stage.py')" "-abslog=$out/$stage-editor.log" > "$out/$stage-console.log" 2>&1
else
 perl -e 'alarm 600; exec @ARGV' "$engine/Binaries/Mac/UnrealEditor-Cmd" "$project" -run=pythonscript "-script=$root/Tools/Unreal/slide_$stage.py" -unattended -nop4 -nosplash -nullrhi '-ExecCmds=Interchange.FeatureFlags.Import.FBX 0' "-abslog=$out/$stage-editor.log" > "$out/$stage-console.log" 2>&1
fi
