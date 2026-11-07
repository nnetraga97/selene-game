"""Immutable-session audit; recovered reference error remains visible."""
import hashlib,json,re,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Saved/AnimMatch/session-3'
r=dict(status='failed_visual_regression',technical_errors=[],stages={},captures={},known_startup_errors=[],unclassified_python_errors=[],original_assets_changed=[],recovered_failures=['game-Fixer-s3-normalized: old AM1 object suffix inside new AM3 package path; full reference corrected once; rerun uses s3-fixedrefs.'])
for p in sorted(OUT.glob('*-exit.txt')):
 code=int(p.read_text());r['stages'][p.name]=code
 if code!=(142 if p.name.startswith('game-') else 0):r['technical_errors'].append(p.name+' unexpected exit')
for p in sorted(OUT.glob('*-editor.log')):
 lines=p.read_text(errors='replace').splitlines();blocks=[];block=[]
 for i,line in enumerate(lines,1):
  if 'LogPython: Error:' not in line:continue
  if 'Traceback (most recent call last):' in line and block:blocks.append(block);block=[]
  block.append(dict(line=i,text=line))
 if block:blocks.append(block)
 for block in blocks:
  content='\n'.join(x['text'] for x in block);known=None
  for plugin,attr in [('EditorToolset','AgentSkill'),('ToolsetRegistry','PythonTestRunner')]:
   if plugin+'/Content/Python/' in content and content.endswith("AttributeError: module 'unreal' has no attribute '"+attr+"'"):known=plugin+'/'+attr
  r['known_startup_errors' if known else 'unclassified_python_errors'].append(dict(log=p.name,classification=known,lines=block))
 for line in lines:
  if re.search(r'Fatal error:|Assertion failed:|Ensure condition failed:|LogSelene: Warning:.*failed to load',line):
   if p.name!='game-Fixer-s3-normalized-editor.log':r['technical_errors'].append(dict(log=p.name,line=line))
for hero in ['Fixer','Courier','Champion']:
 label='s3-fixedrefs' if hero!='Champion' else 's3-regression'
 folder=ROOT/'Saved/AnimMatch/Captures'/label/hero;files=sorted(folder.glob('*.png'))
 r['captures'][label+'/'+hero]=len(files)
 if len(files)!=39:r['technical_errors'].append(label+'/'+hero+' incomplete images')
 logfile=OUT/('game-'+hero+'-'+label+'-editor.log')
 if not logfile.exists():continue
 log=logfile.read_text();r.setdefault('runtime',{})[hero]=dict(phase_records=len(re.findall('LogSelene: AnimMatch '+hero+' ',log)),base_switches_under_transition=re.findall(r'Base changed under transition hero='+hero+r' .*',log),transitions=re.findall(r'AnimMatch transition hero='+hero+r' .*',log),kawaii_13_chains='Kawaii secondary motion on 13 chains' in log,advancing_slots=len(re.findall(r'AnimMatch slot .*position=0\.[1-9]\d* playing=1',log)))
 dest=OUT/'captures'/label/hero
 if files and not dest.exists():shutil.copytree(folder,dest)
originals=json.loads((OUT/'assets-before.json').read_text())
for name,sha in originals.items():
 if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:r['original_assets_changed'].append(name)
r['visual_review']={'Fixer':'Centered AM3 start/stop/pivot in all three views with experimental playback patch.','Courier':'Centered AM3 start/stop/pivot in all three views with experimental playback patch.','Champion':'FAILED: stop/pivot leave arrow/capsule; side/back bodies leave frame. 13 Kawaii chains still active.','timing_gap':'Long walk-start overlay still influences run sample after base has switched.'}
r['final_source']='Session-entry routing-only source restored byte-for-byte; rebuilt successfully. Experimental implementation archived in unaccepted-playback.patch. Final restored runtime plus normalized assets was not recaptured after stopping.'
r['original_hash_count']=len(originals)
r['new_assets']=sorted(str(p.relative_to(ROOT)) for p in (ROOT/'Content/Selene').rglob('*.uasset') if str(p.relative_to(ROOT)) not in originals)
r['default_engine_unchanged']=hashlib.sha256((ROOT/'Config/DefaultEngine.ini').read_bytes()).hexdigest()==(OUT/'default-engine-before.sha256').read_text()
r['processes']=subprocess.run(['pgrep','-fl','[U]nrealEditor.*Selene.uproject'],capture_output=True,text=True).stdout.strip();r['lock_exists']=Path('/tmp/selene-unreal.lock').exists()
(OUT/'verification.json').write_text(json.dumps(r,indent=2))
print(json.dumps({k:v for k,v in r.items() if k not in ['runtime','known_startup_errors','new_assets']},indent=2))
