"""Offline preservation and evidence inventory; visual verdict is separately recorded."""
import ast, hashlib, json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Saved/FoxHookup/session-1'
before=json.loads((OUT/'entry.json').read_text());changed=[];missing=[]
for name,meta in before.items():
 p=ROOT/name
 if not p.exists():missing.append(name);continue
 if 'sha256' in meta:
  if hashlib.sha256(p.read_bytes()).hexdigest()!=meta['sha256']:changed.append(name)
 elif p.stat().st_size!=meta['size'] or p.stat().st_mtime_ns!=meta['mtime_ns']:changed.append(name)
old=(OUT/'DefaultGame.ini.before').read_text();new=(ROOT/'Config/DefaultGame.ini').read_text()
added=[l for l in new.splitlines(keepends=True) if l not in old.splitlines(keepends=True)]
config_preserved=len(added)==3 and ''.join(l for l in new.splitlines(keepends=True) if l not in added)==old
assert config_preserved and any('Name="Fox"' in l for l in added)
assert changed==['Config/DefaultGame.ini'] and not missing
assets=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'Content').rglob('*') if p.is_file() and str(p.relative_to(ROOT)) not in before)
assert all(p.startswith('Content/Selene/Characters/Fox/') or p=='Content/Selene/Materials/Character/MI_Toon_Fox.uasset' for p in assets)
checks={}
for label in ['retarget','clips','reload']:
 checks[label]={'exit':int((OUT/label/'exit.txt').read_text()),'status':json.loads((OUT/label/'report.json').read_text())['status']}
 assert checks[label]=={'exit':0,'status':'success'}
for label,hero in [('fox-baseline','Fox'),('sparrow-regression','Sparrow'),('champion-regression','Champion'),('advanced-on','Fox')]:
 logs=(OUT/label/'editor.log').read_text();files=sorted((ROOT/'Saved/AnimMatch/Captures'/('fox-'+label)/hero).glob('*.png'))
 checks[label]={'exit':int((OUT/label/'exit.txt').read_text()),'captures':len(files),'advanced_mode':re.findall(r'selene.AdvancedMovement = "(\d)"',logs),'active_hero':('Active playable character: '+hero) in logs,'transitions_requested':sorted(set(re.findall(r'AnimMatch transition hero=\w+ clip=(\S+)',logs)))}
 assert len(files)==21 and checks[label]['active_hero'] and checks[label]['exit'] in [0,142]
knee=json.loads((OUT/'knees-observer/captures/observer.json').read_text())
assert knee['status']=='success' and all((OUT/'knees-observer/captures'/r['file']).is_file() for r in knee['captures'])
checks['knees']={'status':knee['status'],'captures':len(knee['captures']),'runtime_joint_samples':len(knee['samples']),'max_sampled_knee_flexion':max(max(s['knee_flexion_degrees'].values()) for s in knee['samples']),'landings':sorted(set(s['view'] for s in knee['captures'] if s['action']=='landing')),'limitation':'Joint values are sampled at request time; asynchronous screenshot rendering can show a subsequent animation frame.'}
for p in (ROOT/'Tools/Unreal').glob('fox_*.py'):ast.parse(p.read_text())
for p in (ROOT/'Tools/Unreal').glob('fox_*.sh'):subprocess.run(['bash','-n',str(p)],check=True)
proc=subprocess.run(['pgrep','-fl','UnrealEditor.*Selene.uproject'],capture_output=True,text=True)
report={'status':'technical_checks_passed_visual_limits_documented','changed_existing_files':changed,'missing_existing_files':missing,'existing_content_files_preserved_by_metadata':sum(k.startswith('Content/') for k in before),'source_and_DefaultEngine_hashes_preserved':True,'config_only_fox_and_two_cook_lines':config_preserved,'new_content':assets,'stages':checks,'remaining_selene_processes':proc.stdout,'lock_exists':Path('/tmp/selene-unreal.lock').exists()}
assert not proc.stdout and not report['lock_exists']
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='new_content'},indent=2));print('New assets',len(assets))
