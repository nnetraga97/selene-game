"""Isolated approach checks. Teleport only between trials; normal collision walking within each."""
import unreal as u,time,json,pathlib,math,traceback,array
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));O=R/'Saved/TownV2/session-7'
z=array.array('f');z.frombytes((R/'Saved/TownV2/session-3/meshes/graded-elevation-ue.f32').read_bytes())
def h(e,n):return z[round((e+590)/1500*1008)*1009+round((n+750)/1500*1008)]
plan=json.loads((O/'correction-plan.json').read_text());trials=[{'name':'TownLink','start':[125,55,h(125,55)+.18],'targets':plan['town_link'][1:]}]
for p in json.loads((O/'placement-final.json').read_text())['placements']:
 e,n,base=p['center_m'];f=p['front_apron_m'];sign=1 if e<298 else -1
 trials.append({'name':p['actor'],'start':[298,n,h(298,n)+.18],'targets':[[f[0]-sign*.5,n],[f[0]-sign*.9,n]]})
state={'start':time.monotonic(),'world':None,'phase':'init','trial':0,'target':0,'last':0,'best':1e9,'progress':0};report={'status':'waiting','method':'Independent normal CharacterMovement approach walks. Pawn positioned at start of each trial only; separate seven-point original walk has no teleports. Targets reach the exterior apron, not interior doors.','trials':[]}
def write():(O/'front-approaches.json').write_text(json.dumps(report,indent=2))
def finish(status,error=None):
 report['status']=status;report['error']=error;write();u.unregister_slate_post_tick_callback(handle)
 if state['world']:u.SystemLibrary.execute_console_command(state['world'],'quit')
def tick(dt):
 try:
  now=time.monotonic();world=u.find_object(None,'/Game/Selene/Maps/TownV2.TownV2');state['world']=world
  if not world or now-state['start']<6:return
  char=u.GameplayStatics.get_player_character(world,0)
  if not char:return
  move=char.get_component_by_class(u.CharacterMovementComponent)
  if state['phase']=='init':
   char.set_movement_pace(u.SelenePace.WALK);move.stop_movement_immediately();p=trials[state['trial']]['start'];cap=char.get_component_by_class(u.CapsuleComponent);char.set_actor_location(u.Vector(p[1]*100,p[0]*100,p[2]*100+cap.get_scaled_capsule_half_height()+5),False,True)
   report['trials'].append({'name':trials[state['trial']]['name'],'samples':[],'reached':[]});state.update(phase='settle',t=now,target=0,best=1e9,progress=now);return
  if state['phase']=='settle':
   if now-state['t']<1:return
   state.update(phase='walk',t=now,progress=now)
  tr=report['trials'][-1];pos=char.get_actor_location();e,n=trials[state['trial']]['targets'][state['target']];dx=n*100-pos.x;dy=e*100-pos.y;dist=math.hypot(dx,dy)
  if dist<25:
   tr['reached'].append(state['target']);state['target']+=1;state['best']=1e9;state['progress']=now
   if state['target']==len(trials[state['trial']]['targets']):
    tr['status']='success';tr['seconds']=now-state['t'];move.stop_movement_immediately();state['trial']+=1;write()
    if state['trial']==len(trials):finish('success');return
    state['phase']='init'
   return
  if dist<state['best']-10:state['best']=dist;state['progress']=now
  if now-state['progress']>8:tr['status']='failed';finish('failed','No approach progress: '+tr['name']);return
  char.add_movement_input(u.Vector(dx/dist,dy/dist,0),1,True)
  if now-state['last']>.2:
   tr['samples'].append({'seconds':now-state['t'],'position_cm':[pos.x,pos.y,pos.z],'falling':move.is_falling(),'target':state['target'],'distance_cm':dist});state['last']=now;write()
 except Exception:finish('failed',traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick);write()
