"""Offscreen -game fixed cameras, real game-frame deltas and short capsule walk. Never saves."""
import unreal as u,os,time,json,traceback,statistics,array
from pathlib import Path
R=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));O=Path(os.environ['SELENE_TOWN_V2_CAPTURE']);O.mkdir(parents=True,exist_ok=True)
assert not list(O.glob('*.png')),'Fresh evidence directory required'
z=array.array('f');z.frombytes((R/'Saved/TownV2/session-3/meshes/graded-elevation-ue.f32').read_bytes())
def h(e,n):return z[round((e+590)/1500*1008)*1009+round((n+750)/1500*1008)]
SHOTS=[('01_plaza_clock',(-22,8),(50,12,10)),('02_plaza_cafe',(-26,17),(-24,50,8)),('03_shop_street',(-45,41),(-65,66,8)),('04_seafront',(-49,10),(-115,-30,0)),('05_hills',(-7,-6),(110,95,14)),('06_aerial',(-180,-190,145),(20,20,4))]
SHOTS += [('07_shop_from_plaza',(-30,20),(-52,61,7)),('08_plaza_block_aerial',(-82,-35,76),(-8,30,5)),('09_lighthouse_from_seafront',(-75,2),(-65,27,10)),('10_lighthouse_from_plaza',(-26,10),(-59.5,22,12)),('11_city_cluster_eye',(298,-55),(311,50,55)),('12_city_skyline_from_plaza',(-22,8),(319,55,44)),('13_city_cluster_aerial',(205,-55,150),(307,52,34))]
placements=json.loads((R/'Saved/TownV2/session-7/placement-final.json').read_text())['placements']
for i,p in enumerate(placements):
 e,n,base=p['center_m'];SHOTS.append((f'{14+i:02d}_front_'+p['asset'],(298,n,h(298,n)+1.83),(e,n,p['visible_floor_m']+4.5)))
if os.environ.get('SELENE_TOWN_V2_CITY_ONLY')=='1':
 SHOTS=[('11_city_cluster_eye',(298,130),(310,52,48)),('12_city_skyline_from_plaza',(-26,17),(319,55,44))]
def vec(p):return u.Vector(p[1]*100,p[0]*100,p[2]*100)
shots=[]
for name,p,t in SHOTS:shots.append((name,(*p,h(*p)+1.65+.20) if len(p)==2 else p,t))
report={'status':'waiting','shots':[],'cameras':shots,'resolution':[1280,720],'fov':70,'hour':15,'fps_note':'Indicative offscreen -game frame-delta throughput after warmup; 100 percent screen percentage; not packaged, not GPU stat-unit timing. Screenshot frames excluded.','walk_samples':[]}
state={'phase':'init','start':time.monotonic(),'t':time.monotonic(),'i':0,'world':None,'cam':None,'frames':[],'last':0}
def write(): (O/'capture.json').write_text(json.dumps(report,indent=2))
def finish(status,error=None):
 report['status']=status;report['error']=error;write();u.unregister_slate_post_tick_callback(handle)
 if state['world']:u.SystemLibrary.execute_console_command(state['world'],'quit')
def tick(dt):
 try:
  now=time.monotonic();world=u.find_object(None,'/Game/Selene/Maps/TownV2.TownV2')
  if not world:
   if now-state['start']>45:finish('failed','World not loaded')
   return
  state['world']=world;pc=u.GameplayStatics.get_player_controller(world,0)
  if not pc:return
  char=u.GameplayStatics.get_player_character(world,0)
  if state['phase']=='init':
   if now-state['start']<45:return
   for cmd in ['r.VSync 0','t.MaxFPS 0','r.ScreenPercentage 100','r.MotionBlurQuality 0','tod.pause 1','tod.set 15']:
    u.SystemLibrary.execute_console_command(world,cmd)
   if char:
    state['char']=char;state['walk_start']=char.get_actor_location();state.update(phase='walk',t=now)
    if hasattr(char,'set_movement_pace'):char.set_movement_pace(u.SelenePace.WALK)
   else:state.update(phase='move',t=now)
   return
  if state['phase']=='walk':
   char=state['char'];move=char.get_component_by_class(u.CharacterMovementComponent);char.add_movement_input(u.Vector(1,0,0),1,True)
   if now-state['last']>.2:
    p=char.get_actor_location();report['walk_samples'].append({'t':now-state['t'],'position_cm':[p.x,p.y,p.z],'falling':move.is_falling()});state['last']=now
   if now-state['t']>3:
    p=char.get_actor_location();b=state['walk_start'];report['walk_distance_cm']=((p.x-b.x)**2+(p.y-b.y)**2)**.5;report['walk_grounded']=all(not q['falling'] for q in report['walk_samples']);move.stop_movement_immediately();char.set_actor_hidden_in_game(True);state.update(phase='move',t=now);write()
   return
  if state['phase']=='move':
   name,eye,target=shots[state['i']];rot=u.MathLibrary.find_look_at_rotation(vec(eye),vec(target));transform=u.Transform(location=vec(eye),rotation=rot)
   if state['cam'] is None:
    cam=next(a for a in u.GameplayStatics.get_all_actors_of_class(world,u.CameraActor) if a.actor_has_tag('V2Capture'));state['cam']=cam
   state['cam'].set_actor_location_and_rotation(vec(eye),rot,False,False);pc.set_view_target_with_blend(state['cam'],0);state.update(phase='settle',t=now,frames=[]);return
  if state['phase']=='settle':
   if now-state['t']>2:
    frame=u.GameplayStatics.get_world_delta_seconds(world)
    if frame>0:state['frames'].append(frame)
   if now-state['t']<7:return
   name=shots[state['i']][0];frames=state['frames'];report.setdefault('performance',[]).append({'view':name,'frames':len(frames),'mean_ms':statistics.mean(frames)*1000,'median_ms':statistics.median(frames)*1000,'indicative_fps':1/statistics.mean(frames)})
   path=O/(name+'.png');state.update(phase='write',t=now,file=path);u.SystemLibrary.execute_console_command(world,'HighResShot 1280x720 filename="'+str(path)+'"');write();return
  if state['phase']=='write':
   if state['file'].exists() and state['file'].stat().st_size>0:
    report['shots'].append(str(state['file']));state['i']+=1
    if state['i']==len(shots):finish('success')
    else:state.update(phase='move',t=now)
   elif now-state['t']>25:finish('failed','Screenshot timeout '+str(state['file']))
 except Exception:finish('failed',traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick);write()
