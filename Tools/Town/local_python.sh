#!/bin/sh
# Reuse installed wheels read-only. No dependency installation or network access.
set -eu
cd "$(dirname "$0")/../.."
export PYTHONDONTWRITEBYTECODE=1
export MPLCONFIGDIR="$PWD/Saved/TownV2/matplotlib-cache"
export XDG_CACHE_HOME="$PWD/Saved/TownV2/cache"
exec /opt/homebrew/bin/python3.14 - "$@" <<'PY'
import pathlib,sys,runpy,os
cache=pathlib.Path.home()/'.cache/uv/archive-v0'
wanted=['numpy','PIL','matplotlib','contourpy','cycler','dateutil','kiwisolver','packaging','pyparsing','six','fontTools']
for name in wanted:
 for p in sorted(cache.glob('*')):
  if (p/name).exists() or (p/(name+'.py')).exists():
   wheels=list(p.glob('*.dist-info/WHEEL'))
   if wheels:
    text=wheels[0].read_text()
    if any(t in text for t in ['cp312-cp312','cp313-cp313','cp315-cp315']): continue
   sys.path.append(str(p)); break
script=sys.argv[1];sys.argv=sys.argv[1:]
sys.path.insert(0,str(pathlib.Path(script).resolve().parent))
runpy.run_path(script,run_name='__main__')
PY
