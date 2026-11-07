"""Preservation, build, runtime and capture inventory. Visual verdict remains in the progress document."""
import ast,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Saved/WandererHookup/session-1';before=json.loads((OUT/'entry.json').read_text())
changed=[];missing=[]
for name,meta in before.items():
 p=ROOT/name
 if not p.exists():missing.append(name);continue
 if 'sha256' in meta:
  if hashlib.sha256(p.read_bytes()).hexdigest()!=meta['sha256']:changed.append(name)
 elif p.stat().st_size!=meta['size'] or p.stat().st_mtime_ns!=meta['mtime_ns']:changed.append(name)
allowed=['Config/DefaultGame.ini','Source/Selene/SeleneCharacter.cpp','Source/Selene/SeleneCharacterSettings.h']
assert sorted(changed)==sorted(allowed),(changed,missing)
assert not missing
old=(OUT/'DefaultGame.ini.before').read_text();new=(ROOT/'Config/DefaultGame.ini').read_text();line=(OUT/'Wanderer-roster-line.txt').read_text().strip()
cook=['+DirectoriesToAlwaysCook=(Path="/Game/Assets/teal-wanderer/teal-wanderer/SkeletalMeshes")','+DirectoriesToAlwaysCook=(Path="/Game/Selene/Characters/Wanderer")']
assert ''.join(l for l in new.splitlines(keepends=True) if l.strip()!=line and l.strip() not in cook)==old
cpp=(ROOT/'Source/Selene/SeleneCharacter.cpp').read_text();cppold=(OUT/'SeleneCharacter.cpp.before').read_text()
cppclean=re.sub(r'\t\t// WANDERER MATERIAL SLOTS:.*?\t\t// END WANDERER MATERIAL SLOTS', '\t\tfor (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot) Mesh->SetMaterial(Slot, Material);',cpp,flags=re.S)
assert cppclean==cppold
header=(ROOT/'Source/Selene/SeleneCharacterSettings.h').read_text();headerold=(OUT/'SeleneCharacterSettings.h.before').read_text()
assert re.sub(r'\n\n\t// WANDERER MATERIAL SLOTS:.*?\t// END WANDERER MATERIAL SLOTS','',header,flags=re.S)==headerold
assets=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'Content').rglob('*') if p.is_file() and str(p.relative_to(ROOT)) not in before)
assert all(p.startswith('Content/Selene/Characters/Wanderer/') or p=='Content/Selene/Materials/Character/MI_Toon_Wanderer.uasset' for p in assets)
checks={}
for label in ['retarget','measure','bind-audit','aligned','aligned-measure','eye-usage','ops-audit','root-separated','root-separated-measure','root-lock','accepted-measure','final-readback']:
 report=json.loads((OUT/label/'report.json').read_text());code=int((OUT/label/'exit.txt').read_text());assert code==0 and report['status']=='success'
 checks[label]={'exit':code,'status':report['status']}
assert 'Result: Succeeded' in (OUT/'build-canonical/console.log').read_text()
assert 'Link [Apple] libUnrealEditor-Selene.dylib' in (OUT/'build-canonical/console.log').read_text()
for label,hero in [('accepted-baseline','Wanderer'),('sparrow-regression','Sparrow'),('champion-regression','Champion'),('fox-regression','Fox'),('advanced-on','Wanderer')]:
 logs=(OUT/label/'editor.log').read_text();files=sorted((ROOT/'Saved/AnimMatch/Captures'/('wanderer-'+label)/hero).glob('*.png'));code=int((OUT/label/'exit.txt').read_text())
 checks[label]={'exit':code,'captures':len(files),'advanced_mode':re.findall(r'selene.AdvancedMovement = "(\d)"',logs),'active_hero':('Active playable character: '+hero) in logs,'transitions_requested':sorted(set(re.findall(r'AnimMatch transition hero=\w+ clip=(\S+)',logs)))}
 assert len(files)==21 and checks[label]['active_hero'] and code in [0,142]
details=json.loads((OUT/'details-accepted/captures/observer.json').read_text());assert details['status']=='success'
assert all((OUT/'details-accepted/captures'/r['file']).is_file() for r in details['captures'])
assert details['runtime_materials'][1]['material']=='/Game/Selene/Characters/Wanderer/Materials/FoxEye_amber.FoxEye_amber'
checks['details']={'status':details['status'],'captures':len(details['captures']),'runtime_materials':details['runtime_materials'],'joint_samples':len(details['samples']),'max_knee_flexion':max(max(s['knee_flexion_degrees'].values()) for s in details['samples'])}
for p in (ROOT/'Tools/Unreal').glob('wanderer_*.py'):ast.parse(p.read_text())
for p in (ROOT/'Tools/Unreal').glob('wanderer_*.sh'):subprocess.run(['bash','-n',str(p)],check=True)
proc=subprocess.run(['pgrep','-fl','UnrealEditor.*Selene.uproject'],capture_output=True,text=True)
report={'status':'technical_checks_passed_visual_limits_documented','changed_existing_files':changed,'preserved_existing_content_files':sum(k.startswith('Content/') for k in before),'config_only_wanderer_and_two_cook_lines':True,'source_only_marked_material_blocks':True,'new_content':assets,'stages':checks,'remaining_selene_processes':proc.stdout,'lock_exists':Path('/tmp/selene-unreal.lock').exists()}
assert not proc.stdout and not report['lock_exists']
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='new_content'},indent=2));print('New content assets',len(assets))
