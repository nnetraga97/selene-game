"""Actual pawn walk from plaza through shop street; no teleporting or saved mutations."""
import unreal as u,time,json,pathlib,math,traceback
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));O=R/'Saved/TownV2/session-6';points=[[-30,10],[-34,19],[-38,30],[-43,39],[-48,48],[-50,60],[-56,70]];state={'start':time.monotonic(),'walking':None,'target':0,'best':1e9,'progress':time.monotonic(),'last':0,'world':None};report={'status':'waiting','route':points,'samples':[],'reached':[],'method':'Starting PlayerStart; normal AddMovementInput and CharacterMovement collision, no teleports'}
def write():(O/'plaza-shop-walk-final.json').write_text(json.dumps(report,indent=2))
def finish(status,error=None):
 report['status']=status;report['error']=error;write();u.unregister_slate_post_tick_callback(handle)
 if state['world']:u.SystemLibrary.execute_console_command(state['world'],'quit')
def tick(dt):
 try:
  now=time.monotonic();world=u.find_object(None,'/Game/Selene/Maps/TownV2.TownV2');state['world']=world
  if not world or now-state['start']<6:return
  char=u.GameplayStatics.get_player_character(world,0)
  if not char:
   if now-state['start']>40:finish('failed','No pawn')
   return
  move=char.get_component_by_class(u.CharacterMovementComponent)
  if state['walking'] is None:
   char.set_movement_pace(u.SelenePace.WALK);state['walking']=now;state['progress']=now;report['status']='walking'
  pos=char.get_actor_location();e,n=points[state['target']];dx=n*100-pos.x;dy=e*100-pos.y;dist=math.hypot(dx,dy)
  if dist<40:
   report['reached'].append(state['target']);state['target']+=1;state['best']=1e9;state['progress']=now
   if state['target']==len(points):report['seconds']=now-state['walking'];report['grounded_samples']=sum(not x['falling'] for x in report['samples']);finish('success');return
   return
  if dist<state['best']-20:state['best']=dist;state['progress']=now
  if now-state['progress']>10:finish('failed','No 20 cm progress for ten seconds');return
  char.add_movement_input(u.Vector(dx/dist,dy/dist,0),1,True)
  if now-state['last']>.2:
   report['samples'].append({'seconds':now-state['walking'],'position_cm':[pos.x,pos.y,pos.z],'falling':move.is_falling(),'target':state['target'],'distance_cm':dist});state['last']=now;write()
 except Exception:finish('failed',traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick);write()
