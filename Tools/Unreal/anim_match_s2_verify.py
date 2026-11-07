"""Session-2 evidence audit: classified known startup noise never masks visual rejection."""
import hashlib,json,re,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Saved/AnimMatch/session-2'
report=dict(status='failed_visual_acceptance',technical_errors=[],stages={},captures={},known_startup_errors=[],unclassified_python_errors=[],original_assets_changed=[],visual_failures=['Rejected transition correction: Fixer and Courier stop/pivot visibly separate from the capsule and leave the frame.','Rejected hold-base correction delays run pace: walk base remains selected at 350 cm/s.'],retained_state='Routing and diagnostic logging only; additional transition correction rolled back. Final routing captured for Fixer, not re-captured for Courier. Champion regression, Sparrow candidates and speed tuning not reached.')
for p in sorted(OUT.glob('*-exit.txt')):
 code=int(p.read_text());report['stages'][p.name]=code
 if code!=(142 if p.name.startswith('game-') else 0):report['technical_errors'].append(p.name+' unexpected exit')
if report['stages'].get('build-rollback-uht-recovery-exit.txt')==0:
 report['recovered_build_failures']=[json.loads((OUT/'rollback-build-recovery.json').read_text())]
 report['technical_errors']=[e for e in report['technical_errors'] if e!='build-rollback-routing-exit.txt unexpected exit']
 report['final_build']='passed: rollback-uht-recovery restores routing-only source'
for p in sorted(OUT.glob('*-editor.log')):
 text=p.read_text(errors='replace');lines=text.splitlines();blocks=[];block=[]
 for i,line in enumerate(lines,1):
  if 'LogPython: Error:' not in line:continue
  if 'Traceback (most recent call last):' in line and block:blocks.append(block);block=[]
  block.append(dict(line=i,text=line))
 if block:blocks.append(block)
 for block in blocks:
  content='\n'.join(x['text'] for x in block)
  known=None
  for plugin,attr in [('EditorToolset','AgentSkill'),('ToolsetRegistry','PythonTestRunner')]:
   if plugin+'/Content/Python/' in content and content.endswith("AttributeError: module 'unreal' has no attribute '"+attr+"'"):known=plugin+'/'+attr
  if known:report['known_startup_errors'].append(dict(log=p.name,classification=known,controller_cleared=True,lines=block))
  else:report['unclassified_python_errors'].append(dict(log=p.name,lines=block))
 for line in lines:
  if re.search(r'Fatal error:|Assertion failed:|Ensure condition failed:|LogSelene: Warning:.*failed to load',line):report['technical_errors'].append(dict(log=p.name,line=line))
for label,hero in [('s2-routing','Fixer'),('s2-transitions','Fixer'),('s2-transitions','Courier')]:
 folder=ROOT/'Saved/AnimMatch/Captures'/label/hero;files=sorted(folder.glob('*.png'))
 report['captures'][label+'/'+hero]=len(files)
 if len(files)!=21:report['technical_errors'].append(label+'/'+hero+' incomplete images')
 log=(OUT/('game-'+hero+'-'+label+'-editor.log')).read_text()
 count=len(re.findall('LogSelene: AnimMatch '+hero+' ',log))
 if count!=21:report['technical_errors'].append(label+'/'+hero+' incomplete phase records')
 report.setdefault('runtime',{})[label+'/'+hero]=dict(phase_records=count,zero_chain_custom_player='anim=SeleneSecondaryAnimInstance_0 secondaryChains=0' in log,transition_requests=re.findall(r'AnimMatch transition hero=\w+ clip=(\S+) slot=DefaultSlot montage=\S+ playing=1',log),advancing_slot_records=len(re.findall(r'AnimMatch slot .*position=0\.[1-9]\d* playing=1',log)))
 dest=OUT/'captures'/label/hero
 if not dest.exists():shutil.copytree(folder,dest)
for name,sha in json.loads((OUT/'assets-before.json').read_text()).items():
 if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:report['original_assets_changed'].append(name)
report['original_hash_count']=len(json.loads((OUT/'assets-before.json').read_text()))
report['new_assets']=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'Content/Selene').rglob('*.uasset') if str(p.relative_to(ROOT)) not in json.loads((OUT/'assets-before.json').read_text()))
report['roster_unchanged']=(ROOT/'Config/DefaultGame.ini').read_bytes()==(OUT/'before/Config/DefaultGame.ini').read_bytes()
report['header_unchanged']=(ROOT/'Source/Selene/SeleneCharacter.h').read_bytes()==(OUT/'before/Source/Selene/SeleneCharacter.h').read_bytes()
report['processes']=subprocess.run(['pgrep','-fl','UnrealEditor.*Selene.uproject'],capture_output=True,text=True).stdout.strip()
report['lock_exists']=Path('/tmp/selene-unreal.lock').exists()
(OUT/'verification.json').write_text(json.dumps(report,indent=2))
(OUT/'startup-error-classification.json').write_text(json.dumps(dict(known=report['known_startup_errors'],unclassified=report['unclassified_python_errors']),indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['known_startup_errors','runtime']},indent=2))
print('Known cleared startup exceptions:',len(report['known_startup_errors']))
