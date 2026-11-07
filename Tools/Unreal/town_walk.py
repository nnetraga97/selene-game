"""Real runtime character movement around R1, bypassing the existing startup-world PerfRoute bug.
One initial positioning; subsequent travel uses AddMovementInput and CharacterMovement collision.
No map or asset saves. Bounded stall detection. Run without -PerfRoute.
"""
import unreal as u,json,time,traceback,math
from pathlib import Path
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));OUT=ROOT/'Saved/Town/session-1/walk-python';OUT.mkdir(parents=True,exist_ok=True)
route=next(r['points'] for r in json.loads((ROOT/'Design/Blockout/layout.json').read_text())['routes'] if r['id']=='R1')
report={'status':'waiting','method':'One initial spawn positioning, then real AddMovementInput / CharacterMovement collision; no route teleportation','waypoints':route,'samples':[],'reached_waypoints':[]}
s={'start':time.monotonic(),'char':None,'target':1,'last_sample':0,'best':1e9,'progress':time.monotonic(),'walk_start':None}
def write(): (OUT/'report.json').write_text(json.dumps(report,indent=2))
def finish(status,error=None):
 report['status']=status;report['error']=error
 if s['walk_start']:report['walk_seconds']=time.monotonic()-s['walk_start']
 write();u.unregister_slate_post_tick_callback(handle)
 if s['char']:
  s['char'].get_component_by_class(u.CharacterMovementComponent).stop_movement_immediately()
  u.SystemLibrary.execute_console_command(s['char'],'quit')
def tick(dt):
 try:
  now=time.monotonic();world=u.find_object(None,'/Game/Selene/Maps/Town.Town')
  if not world or not u.GameplayStatics.get_player_character(world,0):
   if now-s['start']>45:finish('failed','Town/pawn not available within 45 seconds')
   return
  char=u.GameplayStatics.get_player_character(world,0);move=char.get_component_by_class(u.CharacterMovementComponent)
  if s['char'] is None:
   s['char']=char
   cap=char.get_component_by_class(u.CapsuleComponent)
   s['half']=cap.get_scaled_capsule_half_height()
   report['capsule_radius_cm']=cap.get_scaled_capsule_radius();report['capsule_half_height_cm']=s['half']
   char.set_actor_location(u.Vector(route[0][1]*100,route[0][0]*100,s['half']+5),False,False)
   if hasattr(char,'set_movement_pace'):char.set_movement_pace(u.SelenePace.WALK)
   move.set_editor_property('max_walk_speed',150.);move.set_movement_mode(u.MovementMode.MOVE_WALKING)
   s['walk_start']=now;s['progress']=now;report['status']='walking';report['reached_waypoints'].append(0);write();return
  loc=char.get_actor_location();target=route[s['target']];dx=target[1]*100-loc.x;dy=target[0]*100-loc.y;distance=math.hypot(dx,dy)
  if distance<35:
   report['reached_waypoints'].append(s['target']);s['target']+=1;s['best']=1e9;s['progress']=now
   if s['target']>=len(route):finish('success');return
   target=route[s['target']];dx=target[1]*100-loc.x;dy=target[0]*100-loc.y;distance=math.hypot(dx,dy)
  if distance<s['best']-25:s['best']=distance;s['progress']=now
  if now-s['progress']>10:finish('failed','No 25 cm progress for 10 seconds at waypoint '+str(s['target']));return
  char.add_movement_input(u.Vector(dx/distance,dy/distance,0),1.,True)
  if now-s['last_sample']>.1:
   vel=char.get_velocity();report['samples'].append({'seconds':now-s['walk_start'],'feet_cm':[loc.x,loc.y,loc.z-s['half']],'target':s['target'],'target_distance_cm':distance,'speed_cm_s':math.hypot(vel.x,vel.y),'falling':move.is_falling()});s['last_sample']=now
   write()
 except Exception:finish('failed',traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick);write()
