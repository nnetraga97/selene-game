"""Audit scoped preservation and collect proof without changing assets."""
import ast,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Saved/YsoldeHookup/session-1';before=json.loads((OUT/'entry.json').read_text())
changed=[n for n,h in before['files'].items() if hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=h]
assert sorted(changed)==sorted(['Config/DefaultGame.ini','Source/Selene/SeleneCharacter.cpp','Source/Selene/SeleneCharacterSettings.h']),changed
changed_content=[n for n,m in before['content'].items() if [(ROOT/n).stat().st_size,(ROOT/n).stat().st_mtime_ns]!=m]
assert not changed_content,changed_content
for name in ['SeleneCharacter.cpp','SeleneCharacterSettings.h']:
 new=(ROOT/'Source/Selene'/name).read_text();old=(OUT/name).read_text()
 clean=re.sub(r'\t// YSOLDE MATERIAL SLOTS:.*?\t// END YSOLDE MATERIAL SLOTS\n','',new,flags=re.S)
 if name.endswith('.h'):clean=clean.replace('\t// END WANDERER MATERIAL SLOTS\n\n\n','\t// END WANDERER MATERIAL SLOTS\n\n')
 assert clean==old,name
line=(OUT/'Ysolde-roster-line.txt').read_text().strip();cook=['+DirectoriesToAlwaysCook=(Path="/Game/Assets/council-envoy/council-envoy/SkeletalMeshes")','+DirectoriesToAlwaysCook=(Path="/Game/Selene/Characters/Ysolde")']
text=(ROOT/'Config/DefaultGame.ini').read_text()
assert ''.join(l for l in text.splitlines(keepends=True) if l.strip()!=line and l.strip() not in cook)==(OUT/'DefaultGame.ini').read_text()
assets=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'Content').rglob('*') if p.is_file() and str(p.relative_to(ROOT)) not in before['content'])
assert all(p.startswith('Content/Selene/Characters/Ysolde/') or p.startswith('Content/Selene/Materials/Character/MI_Toon_Ysolde_') or p=='Content/Selene/Materials/Character/M_Character_Toon_TwoSided.uasset' for p in assets),assets
assert int((OUT/'build/exit.txt').read_text())==0 and 'libUnrealEditor-Selene.dylib' in (OUT/'build/console.log').read_text()
stages={}
for label in ['retarget','measure','readback']:
 report=json.loads((OUT/label/'report.json').read_text());code=int((OUT/label/'exit.txt').read_text());assert code==0 and report['status']=='success',(label,report)
 stages[label]={'exit':code,'status':report['status']}
errors={}
for label,hero in [('baseline','Ysolde'),('sparrow-regression','Sparrow'),('wanderer-regression','Wanderer'),('fox-regression','Fox'),('advanced-on','Ysolde')]:
 logs=(OUT/label/'editor.log').read_text();files=list((OUT/label/'standard'/hero).glob('*.png'));code=int((OUT/label/'exit.txt').read_text())
 stages[label]={'exit':code,'captures':len(files),'advanced_mode':re.findall(r'selene.AdvancedMovement = "(\d)"',logs),'active_hero':('Active playable character: '+hero) in logs,'transitions_requested':sorted(set(re.findall(r'AnimMatch transition hero=\w+ clip=(\S+)',logs)))}
 assert code==0 and len(files)==21 and stages[label]['active_hero'],stages[label]
 errors[label]=[l for l in logs.splitlines() if any(x in l for x in ['Error:','Warning:','Fatal','Assertion failed'])]
for label in ['details-close','details-gameplay']:
 report=json.loads((OUT/label/'captures/observer.json').read_text());assert report['status']=='success',report.get('error')
 assert all((OUT/label/'captures'/r['file']).is_file() for r in report['captures'])
 stages[label]={'status':report['status'],'captures':len(report['captures']),'runtime_materials':report['runtime_materials'],'runtime_mesh':report['runtime_mesh'],'distance':report['distance'],'joint_samples':len(report['samples']),'max_knee_flexion':max(max(s['knee_flexion_degrees'].values()) for s in report['samples'])}
for log in OUT.glob('*/editor.log'):
 errors[log.parent.name]=[l for l in log.read_text().splitlines() if any(x in l for x in ['Error:','Warning:','Fatal','Assertion failed'])]
for p in (ROOT/'Tools/Unreal').glob('ysolde_*.py'):ast.parse(p.read_text())
for p in (ROOT/'Tools/Unreal').glob('ysolde_*.sh'):subprocess.run(['bash','-n',str(p)],check=True)
proc=subprocess.run(['pgrep','-fl','UnrealEditor.*Selene.uproject'],capture_output=True,text=True)
assert not proc.stdout and not Path('/tmp/selene-unreal.lock').exists()
report={'status':'technical_checks_passed_visual_limits_documented','changed_existing_files':changed,'preserved_existing_content_files':len(before['content']),'new_content':assets,'stages':stages,'config_only_ysolde_and_two_cook_lines':True,'source_only_marked_material_blocks':True,'remaining_selene_processes':proc.stdout,'lock_exists':False}
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'log-errors-and-warnings.json').write_text(json.dumps(errors,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='new_content'},indent=2));print('new assets:',len(assets))
