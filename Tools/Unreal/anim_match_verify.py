"""Record completed session evidence; image review is recorded separately in progress notes."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Saved/AnimMatch/session-1'
report=dict(stages={},captures={},original_assets_changed=[],errors=[])
for p in OUT.glob('*-exit.txt'):
    code=int(p.read_text());report['stages'][p.name]=code
    expected=142 if p.name.startswith('game-') else 0
    if code!=expected: report['errors'].append(p.name+' unexpected exit')
for label,heroes in [('before',['Sparrow','Champion','Angel','Fixer','Courier']),('after-facing',['Fixer','Courier'])]:
 for hero in heroes:
  files=sorted((ROOT/'Saved/AnimMatch/Captures'/label/hero).glob('*.png'))
  report['captures'][label+'/'+hero]=[str(p.relative_to(ROOT)) for p in files]
  if len(files)!=21: report['errors'].append(label+'/'+hero+' incomplete')
  log=OUT/('game-'+hero+'-'+label+'-editor.log')
  text=log.read_text(errors='replace')
  if len(re.findall(r'LogSelene: AnimMatch '+hero+' ',text))!=21: report['errors'].append('Missing runtime phase records: '+hero+'/'+label)
  if re.search(r'LogSelene: Warning:.*failed to load|Fatal error:|LogPython: Error:',text): report['errors'].append('Runtime error: '+str(log))
for p,h in json.loads((OUT/'assets-before.json').read_text()).items():
 if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h: report['original_assets_changed'].append(p)
if report['original_assets_changed']: report['errors'].append('Original assets changed')
report['new_assets']=sorted(str(p.relative_to(ROOT)) for hero in ['Fixer','Courier'] for p in (ROOT/'Content/Selene/Characters'/hero/'AnimMatchS1').rglob('*.uasset'))
report['processes']=subprocess.run(['pgrep','-fl','UnrealEditor.*Selene.uproject'],capture_output=True,text=True).stdout.strip()
report['lock_exists']=Path('/tmp/selene-unreal.lock').exists()
report['status']='passed' if not report['errors'] else 'failed'
(OUT/'verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['captures','new_assets']},indent=2))
print('captures',sum(len(x) for x in report['captures'].values()),'new assets',len(report['new_assets']))
if report['errors']: raise SystemExit(1)
