#!/bin/bash
# lanes_run.sh python <label> <script>   |   lanes_run.sh game <label> <seconds> <execcmds> [extra args]
# Never signals an existing game: waits for it, then takes the shared lock.
set -eu
stage="${1:?stage}"; label="${2:?label}"
out="$PWD/Saved/LanesMap/$label"; test -f "$PWD/Selene.uproject"; mkdir -p "$out"
started=$SECONDS
while pgrep -f 'UnrealEditor.*Selene.uproject' > /dev/null; do
 if (( SECONDS - started >= 600 )); then echo 'Selene still running; no launch'; exit 2; fi; sleep 10
done
until mkdir /tmp/selene-unreal.lock 2>/dev/null; do
 if (( SECONDS - started >= 600 )); then echo 'Lock occupied; no launch'; exit 2; fi; sleep 10
done
trap 'rmdir /tmp/selene-unreal.lock' EXIT
bin='/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac'
set +e
case "$stage" in
python) perl -e 'alarm 900; exec @ARGV' "$bin/UnrealEditor-Cmd" "$PWD/Selene.uproject" -run=pythonscript "-script=$PWD/Tools/Unreal/${3:?script}.py" -unattended -nop4 -nosplash -nullrhi "-abslog=$out/editor.log" > "$out/console.log" 2>&1 ;;
game) secs="${3:?seconds}"; cmds="${4:?execcmds}"; shift 4
 perl -e 'alarm shift; exec @ARGV' "$secs" "$bin/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/Lanes -game "-ExecCmds=$cmds" -unattended -nop4 -nosplash -windowed -ResX=1600 -ResY=900 "$@" "-abslog=$out/editor.log" > "$out/console.log" 2>&1 ;;
*) exit 2;;
esac
rc=$?; echo "$rc" > "$out/exit.txt"; exit 0
