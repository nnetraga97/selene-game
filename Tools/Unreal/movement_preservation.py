"""Report protected-file parity against session entry; asset metadata is not a content hash."""
import hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
session=root/'Saved/MovementTest'/sys.argv[1]
out=session/sys.argv[2]
assert not out.exists(),out
before=json.loads((session/'content-entry.json').read_text())
current={str(p.relative_to(root)):[p.stat().st_size,p.stat().st_mtime_ns] for p in (root/'Content').rglob('*') if p.is_file()}
hashes=json.loads((session/'entry-sha256.json').read_text())
report={'source_sha256_matches_entry':{f:hashlib.sha256((root/f).read_bytes()).hexdigest()==sha for f,sha in hashes.items()},'preexisting_asset_count':len(before),'preexisting_assets_changed_or_missing':[p for p,meta in before.items() if current.get(p)!=meta],'new_assets':sorted(set(current)-set(before)),'selene_processes':subprocess.run(['pgrep','-fl','UnrealEditor.*Selene.uproject'],text=True,capture_output=True).stdout.strip(),'lock_exists':Path('/tmp/selene-unreal.lock').exists()}
out.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
