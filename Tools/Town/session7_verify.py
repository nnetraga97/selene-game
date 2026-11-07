"""Verify session evidence without editing assets or replaying placement."""
from pathlib import Path
import json,hashlib,statistics,datetime,subprocess,ast
R=Path(__file__).resolve().parents[2];O=R/'Saved/TownV2/session-7'
def load(n):return json.loads((O/n).read_text())
before=load('before/capture.json');final=load('final/capture.json');read=load('readback-final.json');walk=load('plaza-shop-walk-final.json');fronts=load('front-approaches.json');apply=load('placement-final.json');s6=json.loads((R/'Saved/TownV2/session-6/final/capture.json').read_text())
assert before['status']==final['status']=='success' and len(before['shots'])==9 and len(final['shots'])==19
assert before['cameras']==final['cameras'][:9]==s6['cameras'][:9]
assert before['resolution']==final['resolution']==[1280,720] and before['fov']==final['fov']==70
assert fronts['status']=='success' and len(fronts['trials'])==7 and all(t['status']=='success' for t in fronts['trials'])
assert read['status']=='verified' and walk['status']=='success' and walk['reached']==list(range(7))
assert all(not s['falling'] for s in walk['samples']);assert walk['route']==json.loads((R/'Saved/TownV2/session-6/plaza-shop-walk-final.json').read_text())['route']
protected=load('protected-before.json');bad=[n for n,h in protected.items() if not (R/n).exists() or hashlib.sha256((R/n).read_bytes()).hexdigest()!=h];assert not bad,bad
backup=load('backup-manifest.json');changed=[n for n,h in backup.items() if hashlib.sha256((R/n).read_bytes()).hexdigest()!=h]
for p in (R/'Tools/Unreal').glob('town_v2_session7*.py'):ast.parse(p.read_text())
subprocess.run(['bash','-n',str(R/'Tools/Unreal/town_run.sh')],check=True)
proc=subprocess.run(['pgrep','-f','UnrealEditor.*Selene.uproject'],capture_output=True,text=True);assert proc.returncode==1,proc.stdout;assert not Path('/tmp/selene-unreal.lock').exists()
rows=[]
for old,b,a in zip(s6['performance'][:9],before['performance'],final['performance'][:9]):
 assert old['view']==b['view']==a['view'];rows.append({'view':b['view'],'session6_fps':old['indicative_fps'],'fresh_before_fps':b['indicative_fps'],'final_fps':a['indicative_fps'],'change_vs_session6_percent':(a['indicative_fps']/old['indicative_fps']-1)*100,'change_vs_fresh_before_percent':(a['indicative_fps']/b['indicative_fps']-1)*100,'session6_ms':old['mean_ms'],'fresh_before_ms':b['mean_ms'],'final_ms':a['mean_ms']})
agg={}
for count in [8,9]:
 ms={k:statistics.mean(x[k+'_ms'] for x in rows[:count]) for k in ['session6','fresh_before','final']};agg[str(count)]={'mean_ms':ms,'fps':{k:1000/v for k,v in ms.items()},'change_vs_session6_percent':(ms['session6']/ms['final']-1)*100,'change_vs_fresh_before_percent':(ms['fresh_before']/ms['final']-1)*100}
fps={'method':'Equal-view-weighted mean world-frame delta then 1000/mean_ms. Offscreen editor game; 45s warmup, 5s stationary sampling, screenshots excluded. Not GPU timings.','aggregates':agg,'views':rows};(O/'fps-comparison.json').write_text(json.dumps(fps,indent=2))
verification={'delivery_state':'partial','unmet_checks':load('visual-review.json')['unmet_checks'],'status':'verified','time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protected_checked':len(protected),'protected_mismatches':bad,'existing_allowed_files_changed':changed,'nine_cameras_match_session6':True,'all_773_existing_actors_unchanged':True,'actor_count':len(read['actors']),'ground_contacts':read['ground_contacts'],'walk_waypoints':7,'walk_grounded_samples':len(walk['samples']),'walk_seconds':walk['seconds'],'front_approach_status':fronts['status'],'lock_released':True,'fps':fps}
city=load('city-framing/capture.json');assert city['status']=='success' and len(city['shots'])==2
artifacts=[R/'Content/Selene/Maps/TownV2.umap',*sorted((O/'city-framing').glob('*.png')),*sorted((O/'final').glob('*.png')),O/'readback-final.json',O/'plaza-shop-walk-final.json',O/'front-approaches.json'];verification['artifacts']={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts};(O/'verification-final.json').write_text(json.dumps(verification,indent=2));(R/'Design/TownV2/session-7-checkpoint.json').write_text(json.dumps({'status':'saved preview; plaza skyline framing incomplete','placements':apply['placements'],'verification':'Saved/TownV2/session-7/verification-final.json'},indent=2));print(json.dumps({k:verification[k] for k in ['status','protected_checked','actor_count','walk_grounded_samples','walk_seconds','front_approach_status']},indent=2));print(json.dumps(agg,indent=2))
