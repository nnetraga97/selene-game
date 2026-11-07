#!/bin/bash
# One diagnosed correction: quarantine exact superseded OFPA packages, then reload.
set -eu
out="$PWD/Saved/Town/session-1"
started=$SECONDS
while pgrep -f 'UnrealEditor.*Selene.uproject' > /dev/null; do
 if (( SECONDS-started>=900 )); then exit 2; fi
 sleep 15
done
until mkdir /tmp/selene-unreal.lock 2>/dev/null; do
 if (( SECONDS-started>=900 )); then exit 2; fi
 sleep 15
done
trap 'rmdir /tmp/selene-unreal.lock' EXIT
if pgrep -f 'UnrealEditor.*Selene.uproject' > /dev/null; then exit 2; fi
python3 - <<'PY'
from pathlib import Path
import json,hashlib,shutil
root=Path.cwd();out=root/'Saved/Town/session-1';paths=json.loads((out/'obsolete-first-pass-actors.json').read_text());receipt=[]
assert len(paths)==291
for name in paths:
 p=root/name;dst=out/'rejected-first-pass-actors'/name
 assert p.is_file() and not dst.exists(),name
for name in paths:
 p=root/name;dst=out/'rejected-first-pass-actors'/name;dst.parent.mkdir(parents=True,exist_ok=True)
 digest=hashlib.sha256(p.read_bytes()).hexdigest();shutil.move(p,dst)
 assert hashlib.sha256(dst.read_bytes()).hexdigest()==digest
 receipt.append({'path':name,'sha256':digest,'quarantined_to':str(dst.relative_to(root))})
(out/'reconciliation-receipt.json').write_text(json.dumps(receipt,indent=2))
print('Quarantined',len(receipt),'superseded actor packages; no original actor packages moved')
PY
perl -e 'alarm 180; exec @ARGV' '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd' "$PWD/Selene.uproject" -run=pythonscript "-script=$PWD/Tools/Unreal/town_verify.py" -unattended -nop4 -nosplash -nullrhi "-abslog=$out/reconcile-editor.log" > "$out/reconcile-console.log" 2>&1
