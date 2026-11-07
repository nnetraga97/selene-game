"""Audit scoped preservation and collect proof without changing assets."""
import ast,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Saved/NerineHookup/session-1';before=json.loads((OUT/'entry.json').read_text())
changed=[n for n,h in before['files'].items() if hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=h]
assert 'Config/DefaultEngine.ini' not in changed
concurrent_source=[n for n in changed if n.startswith('Source/')]
assert not [n for n in changed if n!='Config/DefaultGame.ini' and not n.startswith('Source/')],changed
changed_content=[n for n,m in before['content'].items() if [(ROOT/n).stat().st_size,(ROOT/n).stat().st_mtime_ns]!=m]
assert not changed_content,changed_content
lines=[(OUT/h/(h+'-roster-line.txt')).read_text().strip() for h in ['Nerine','Base']]
cook=['+DirectoriesToAlwaysCook=(Path="'+p+'")' for p in ['/Game/Assets/nerine/nerine/SkeletalMeshes','/Game/Selene/Characters/Nerine','/Game/Assets/base-female-v2/base-female-v2/SkeletalMeshes','/Game/Selene/Characters/Base']]
text=(ROOT/'Config/DefaultGame.ini').read_text()
assert ''.join(l for l in text.splitlines(keepends=True) if l.strip() not in lines+cook)==(OUT/'DefaultGame.ini').read_text()
roster=[l.split('Name="')[1].split('"')[0] for l in text.splitlines() if l.startswith('+Roster=')]
assert roster[roster.index('Ysolde')+1:roster.index('Ysolde')+3]==['Nerine','Base']
assets=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'Content').rglob('*') if p.is_file() and str(p.relative_to(ROOT)) not in before['content'])
assert all(p.startswith(('Content/Selene/Characters/Nerine/','Content/Selene/Characters/Base/','Content/Selene/Materials/Character/MI_Toon_Nerine_','Content/Selene/Materials/Character/MI_Toon_Base')) for p in assets),assets
stages={}
for hero in ['Nerine','Base']:
 for label in ['retarget','measure','readback']:
  report=json.loads((OUT/hero/label/'report.json').read_text());code=int((OUT/hero/label/'exit.txt').read_text());assert code==0 and report['status']=='success',(hero,label,report.get('error'))
  stages[hero+'/'+label]={'exit':code,'status':report['status']}
for hero in ['Nerine','Base']:
 measurement=json.loads((OUT/hero/'measure/report.json').read_text())
 for clip in measurement['clips']:
  assert clip['flags']['force_root_lock']=='True' and 'REF_POSE' in clip['flags']['root_motion_root_lock']
  assert all(abs(x)<1e-4 for pair in clip['runtime']['summary']['root']['range'] for x in pair)
 ret=json.loads((OUT/hero/'retarget/report.json').read_text())
 bones={b['name'] for b in ret['hierarchy']}
 kawaii=json.loads((OUT/hero/'kawaii-values.json').read_text())
 assert all(n in bones for n in kawaii['chains'])
 assert all(b in bones and (not c or c in bones) for b,c,r in kawaii['colliders'])
errors={}
for label,hero in [('Nerine/baseline','Nerine'),('Base/baseline','Base'),('Nerine/ysolde-regression','Ysolde'),('Nerine/sparrow-regression','Sparrow')]:
 logs=(OUT/label/'editor.log').read_text();files=list((OUT/label/'standard'/hero).glob('*.png'));code=int((OUT/label/'exit.txt').read_text())
 stages[label]={'exit':code,'captures':len(files),'advanced_mode':re.findall(r'selene.AdvancedMovement = "(\d)"',logs),'active_hero':('Active playable character: '+hero) in logs,'transitions_requested':sorted(set(re.findall(r'AnimMatch transition hero=\w+ clip=(\S+)',logs)))}
 assert code==0 and len(files)==21 and stages[label]['active_hero'],stages[label]
 errors[label]=[l for l in logs.splitlines() if any(x in l for x in ['Error:','Warning:','Fatal','Assertion failed'])]
for label in ['Nerine/details-gameplay','Nerine/ysolde-details-gameplay','Base/details-gameplay','Nerine/details-close','Nerine/ysolde-details-close']:
 report=json.loads((OUT/label/'captures/observer.json').read_text());assert report['status']=='success',report.get('error')
 code=int((OUT/label/'exit.txt').read_text());assert code==0,(label,code)
 assert all((OUT/label/'captures'/r['file']).is_file() for r in report['captures'])
 stages[label]={'exit':code,'status':report['status'],'captures':len(report['captures']),'runtime_materials':report['runtime_materials'],'runtime_mesh':report['runtime_mesh'],'distance':report['distance'],'joint_samples':len(report['samples']),'max_knee_flexion':max(max(s['knee_flexion_degrees'].values()) for s in report['samples'])}
for log in OUT.glob('*/*/editor.log'):
 errors[str(log.parent.relative_to(OUT))]=[l for l in log.read_text().splitlines() if any(x in l for x in ['Error:','Warning:','Fatal','Assertion failed'])]
for p in [*(ROOT/'Tools/Unreal').glob('nerine_*.py'),*(ROOT/'Tools/Unreal').glob('basebody_*.py')]:ast.parse(p.read_text())
for p in [*(ROOT/'Tools/Unreal').glob('nerine_*.sh'),*(ROOT/'Tools/Unreal').glob('basebody_*.sh')]:subprocess.run(['bash','-n',str(p)],check=True)
proc=subprocess.run(['pgrep','-fl','UnrealEditor.*Selene.uproject'],capture_output=True,text=True)
assert not proc.stdout and not Path('/tmp/selene-unreal.lock').exists()
report={'status':'technical_checks_passed_visual_limits_documented','changed_existing_files':changed,'preserved_existing_content_files':len(before['content']),'new_content':assets,'stages':stages,'config_only_two_roster_and_four_cook_lines':True,'concurrent_source_changes_not_authored_here':concurrent_source,'remaining_selene_processes':proc.stdout,'lock_exists':False}
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'log-errors-and-warnings.json').write_text(json.dumps(errors,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='new_content'},indent=2));print('new assets:',len(assets))
