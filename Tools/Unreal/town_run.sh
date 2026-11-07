#!/bin/bash
set -eu
stage="$1"
label="$2"
out="${SELENE_TOWN_OUT:-$PWD/Saved/Town/session-1}"
mkdir -p "$out"
test ! -e "$out/$stage-$label-console.log"
started=$SECONDS
while pgrep -f 'UnrealEditor.*Selene.uproject' > /dev/null; do
  if (( SECONDS - started >= 900 )); then echo 'User editor running; no launch'; exit 2; fi
  sleep 15
done
until mkdir /tmp/selene-unreal.lock 2>/dev/null; do
  if (( SECONDS - started >= 900 )); then echo 'Shared lock occupied'; exit 2; fi
  sleep 15
done
trap 'rmdir /tmp/selene-unreal.lock' EXIT
if pgrep -f 'UnrealEditor.*Selene.uproject' > /dev/null; then exit 2; fi
bin='/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac'
if [[ "$stage" == v7-game ]]; then
 export SELENE_TOWN_V2_CAPTURE="$out/$label"
 perl -e 'alarm 300; exec @ARGV' "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/TownV2 -game -RenderOffscreen -TodPause -TodHour=15 "-ExecCmds=py __import__('runpy').run_path(__import__('unreal').Paths.project_dir()+'Tools/Unreal/town_v2_session7_capture.py')" -unattended -nop4 -nosplash -ResX=1280 -ResY=720 "-abslog=$out/$stage-$label-editor.log" > "$out/$stage-$label-console.log" 2>&1
elif [[ "$stage" == v7-fronts ]]; then
 perl -e 'alarm 300; exec @ARGV' "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/TownV2 -game -RenderOffscreen -TodPause -TodHour=15 "-ExecCmds=py __import__('runpy').run_path(__import__('unreal').Paths.project_dir()+'Tools/Unreal/town_v2_session7_fronts.py')" -unattended -nop4 -nosplash -ResX=1280 -ResY=720 "-abslog=$out/$stage-$label-editor.log" > "$out/$stage-$label-console.log" 2>&1
elif [[ "$stage" == v7-walk ]]; then
 perl -e 'alarm 180; exec @ARGV' "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/TownV2 -game -RenderOffscreen -TodPause -TodHour=15 "-ExecCmds=py __import__('runpy').run_path(__import__('unreal').Paths.project_dir()+'Tools/Unreal/town_v2_session7_walk.py')" -unattended -nop4 -nosplash -ResX=1280 -ResY=720 "-abslog=$out/$stage-$label-editor.log" > "$out/$stage-$label-console.log" 2>&1
elif [[ "$stage" == v6-walk ]]; then
 perl -e 'alarm 180; exec @ARGV' "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/TownV2 -game -RenderOffscreen -TodPause -TodHour=15 "-ExecCmds=py __import__('runpy').run_path(__import__('unreal').Paths.project_dir()+'Tools/Unreal/town_v2_session6_walk.py')" -unattended -nop4 -nosplash -ResX=1280 -ResY=720 "-abslog=$out/$stage-$label-editor.log" > "$out/$stage-$label-console.log" 2>&1
elif [[ "$stage" == v5-scale ]]; then
 export SELENE_TOWN_V2_CAPTURE="$out/$label"
 perl -e 'alarm 180; exec @ARGV' "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/TownV2 -game -RenderOffscreen -TodPause -TodHour=15 "-ExecCmds=py __import__('runpy').run_path(__import__('unreal').Paths.project_dir()+'Tools/Unreal/town_v2_session5_scale.py')" -unattended -nop4 -nosplash -ResX=1280 -ResY=720 "-abslog=$out/$stage-$label-editor.log" > "$out/$stage-$label-console.log" 2>&1
elif [[ "$stage" == v5-walk ]]; then
 perl -e 'alarm 180; exec @ARGV' "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/TownV2 -game -RenderOffscreen -TodPause -TodHour=15 "-ExecCmds=py __import__('runpy').run_path(__import__('unreal').Paths.project_dir()+'Tools/Unreal/town_v2_session5_walk.py')" -unattended -nop4 -nosplash -ResX=1280 -ResY=720 "-abslog=$out/$stage-$label-editor.log" > "$out/$stage-$label-console.log" 2>&1
elif [[ "$stage" == v4-walk ]]; then
 perl -e 'alarm 180; exec @ARGV' "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/TownV2 -game -RenderOffscreen -TodPause -TodHour=15 "-ExecCmds=py __import__('runpy').run_path(__import__('unreal').Paths.project_dir()+'Tools/Unreal/town_v2_session4_walk.py')" -unattended -nop4 -nosplash -ResX=1280 -ResY=720 "-abslog=$out/$stage-$label-editor.log" > "$out/$stage-$label-console.log" 2>&1
elif [[ "$stage" == v2-walk ]]; then
 perl -e 'alarm 150; exec @ARGV' "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/TownV2 -game -RenderOffscreen -TodPause -TodHour=15 "-ExecCmds=py __import__('runpy').run_path(__import__('unreal').Paths.project_dir()+'Tools/Unreal/town_v2_walk.py')" -unattended -nop4 -nosplash -ResX=1280 -ResY=720 "-abslog=$out/$stage-$label-editor.log" > "$out/$stage-$label-console.log" 2>&1
elif [[ "$stage" == v2-game ]]; then
 export SELENE_TOWN_V2_CAPTURE="$out/$label"
 perl -e 'alarm 240; exec @ARGV' "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/TownV2 -game -RenderOffscreen -TodPause -TodHour=15 "-ExecCmds=py __import__('runpy').run_path(__import__('unreal').Paths.project_dir()+'Tools/Unreal/town_v2_capture.py')" -unattended -nop4 -nosplash -ResX=1280 -ResY=720 "-abslog=$out/$stage-$label-editor.log" > "$out/$stage-$label-console.log" 2>&1
elif [[ "$stage" == v2-editor ]]; then
 export SELENE_TOWN_V2_OUT="$out"
 perl -e 'alarm 780; exec @ARGV' "$bin/UnrealEditor.app/Contents/MacOS/UnrealEditor" "$PWD/Selene.uproject" "-ExecCmds=py __import__('runpy').run_path(__import__('unreal').Paths.project_dir()+'Tools/Unreal/town_v2_setup.py')" -unattended -nop4 -nosplash -windowed -ResX=1600 -ResY=1000 "-abslog=$out/$stage-$label-editor.log" > "$out/$stage-$label-console.log" 2>&1
elif [[ "$stage" == capture ]]; then
 export SELENE_SHOT_OUTPUT="${SELENE_TOWN_CAPTURE_DIR:-$out/$label}"
 export SELENE_STAGE_REPORT="$out/$stage-$label.json"
 perl -e 'alarm 240; exec @ARGV' "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/Town "-ExecCmds=py __import__('runpy').run_path(__import__('unreal').Paths.project_dir()+'Tools/Unreal/town_capture.py')" -unattended -nop4 -nosplash -windowed -ResX=1920 -ResY=1080 "-abslog=$out/$stage-$label-editor.log" > "$out/$stage-$label-console.log" 2>&1
elif [[ "$stage" == walk ]]; then
 mkdir -p "$out/walk-$label"
 perl -e 'alarm 180; exec @ARGV' "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/Town -game -PerfRoute=R1 -PerfDrive=1 -PerfCam=1P -PerfHour=12 -PerfWarmup=3 -PerfSpeed=150 "-PerfOut=$out/walk-$label" -ExecCmds="selene.AdvancedMovement 0,t.MaxFPS 60" -unattended -nop4 -nosplash -windowed -ResX=1280 -ResY=720 "-abslog=$out/$stage-$label-editor.log" > "$out/$stage-$label-console.log" 2>&1
elif [[ "$stage" == walk-python ]]; then
 perl -e 'alarm 180; exec @ARGV' "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/Town -game "-ExecCmds=selene.AdvancedMovement 0,tod.pause 1,tod.set 12,t.MaxFPS 60,py __import__('runpy').run_path(__import__('unreal').Paths.project_dir()+'Tools/Unreal/town_walk.py')" -unattended -nop4 -nosplash -windowed -ResX=1280 -ResY=720 "-abslog=$out/$stage-$label-editor.log" > "$out/$stage-$label-console.log" 2>&1
else
 perl -e 'alarm 240; exec @ARGV' "$bin/UnrealEditor-Cmd" "$PWD/Selene.uproject" -run=pythonscript "-script=$PWD/Tools/Unreal/$stage.py" -unattended -nop4 -nosplash -nullrhi "-abslog=$out/$stage-$label-editor.log" > "$out/$stage-$label-console.log" 2>&1
fi
