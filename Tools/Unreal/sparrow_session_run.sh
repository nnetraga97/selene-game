#!/bin/bash
# Read-only Sparrow audit with the brief's user-game and concurrency guards.
set -eu
test -f "$PWD/Selene.uproject"
session="${SELENE_SPARROW_SESSION:-session-1}"
case "$session" in *[!a-zA-Z0-9_-]*|'') echo 'Invalid session name' >&2; exit 1;; esac
out="$PWD/Saved/Sparrow/$session"
mkdir -p "$out"
test ! -e "$out/audit.json"
test ! -e "$out/wait.log"
started=$SECONDS
while true; do
    date -u '+%Y-%m-%d %H:%M:%S UTC' >> "$out/wait.log"
    if ! pgrep -fl 'UnrealEditor.*Selene.uproject' >> "$out/wait.log"; then
        echo 'No Selene Unreal process remains.' >> "$out/wait.log"
        break
    fi
    if (( SECONDS - started >= 900 )); then
        echo "waiting for the user's game to close" | tee -a "$out/wait.log"
        exit 2
    fi
    sleep 30
done
# Do not start work too near the caller's bounded session deadline.
if [ -n "${SELENE_SPARROW_DEADLINE:-}" ] && (( $(date +%s) + 180 >= SELENE_SPARROW_DEADLINE )); then
    echo 'Insufficient session time to launch and inspect the audit.' | tee -a "$out/wait.log"
    exit 3
fi
until mkdir /tmp/selene-unreal.lock 2>/dev/null; do
    if (( SECONDS - started >= 900 )); then
        echo 'Unreal lock is still occupied; no launch.' | tee -a "$out/wait.log"
        exit 2
    fi
    sleep 15
done
trap 'rmdir /tmp/selene-unreal.lock' EXIT
if pgrep -fl 'UnrealEditor.*Selene.uproject' >> "$out/wait.log"; then
    echo 'Selene started before lock acquisition; no launch.' | tee -a "$out/wait.log"
    exit 2
fi
export SELENE_SPARROW_SESSION="$session"
perl -e 'alarm 900; exec @ARGV' \
    '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd' \
    "$PWD/Selene.uproject" -run=pythonscript "-script=$PWD/Tools/Unreal/sparrow_audit.py" \
    -unattended -nop4 -nosplash -nullrhi \
    "-abslog=$out/audit-editor.log" > "$out/audit-console.log" 2>&1
