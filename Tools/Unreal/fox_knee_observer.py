"""Actual -game observer: runtime joints and screenshots, independent of AnimMatch's early return.
No assets, actors, camera transforms, animation state, source, or gameplay are modified.
"""
import json, math, os, time, traceback
from pathlib import Path
import unreal as u
OUT=Path(os.environ['SELENE_FOX_KNEE_OUTPUT']);OUT.mkdir(parents=True,exist_ok=True)
report={'status':'waiting','captures':[],'samples':[],'method':'Runtime socket positions and game screenshots; knee flexion = 180 minus hip-knee-ankle angle.'}
state={'start':None,'last_shot':-100.,'was_falling':False,'land_time':None,'landing_shots':0,'wall_start':time.monotonic()}
def checkpoint(): (OUT/'observer.json').write_text(json.dumps(report,indent=2)+'\n')
def xyz(v):return [v.x,v.y,v.z]
def flex(h,k,a):
 v=[h[i]-k[i] for i in range(3)];w=[a[i]-k[i] for i in range(3)];den=math.sqrt(sum(x*x for x in v)*sum(x*x for x in w))
 return 180-math.degrees(math.acos(max(-1,min(1,sum(v[i]*w[i] for i in range(3))/den)))) if den else None
def finish(status):
 report['status']=status;checkpoint();u.unregister_slate_post_tick_callback(handle)
def tick(_):
 try:
  world=u.find_object(None,'/Game/Selene/Maps/Town.Town')
  if not world:
   if time.monotonic()-state['wall_start']>30:raise RuntimeError('Town game World not found')
   return
  char=u.GameplayStatics.get_player_character(world,0)
  if not char or str(char.get_active_character_name())!='Fox':return
  now=u.GameplayStatics.get_time_seconds(world)
  if state['start'] is None:state['start']=now;report['status']='recording';report['world']=world.get_path_name();checkpoint()
  elapsed=now-state['start']-5
  if elapsed<0:return
  if elapsed>=42:finish('success');return
  view=['front','side','back'][min(2,int(elapsed/14))];phase=elapsed%14
  mesh=char.get_component_by_class(u.SkeletalMeshComponent);movement=char.get_component_by_class(u.CharacterMovementComponent)
  velocity=char.get_velocity();falling=movement.is_falling();angles={};positions={}
  for side in ('Left','Right'):
   points=[xyz(mesh.get_socket_location('mixamorig_'+side+b)) for b in ('UpLeg','Leg','Foot')];angles[side]=flex(*points);positions[side]=points
  row={'time':elapsed,'phase':phase,'view':view,'velocity':xyz(velocity),'falling':falling,'knee_flexion_degrees':angles,'joint_positions_world_cm':positions}
  report['samples'].append(row)
  if state['was_falling'] and not falling and phase>12:state['land_time']=now;state['landing_shots']=0
  state['was_falling']=falling
  speed=math.hypot(velocity.x,velocity.y);label=None
  if 4.2<=phase<=5.8 and speed>300:label='run'
  elif 6.2<=phase<=7.8 and speed>500:label='sprint'
  elif 12.1<=phase<=12.8 and falling:label='jump'
  elif state['land_time'] is not None and 0<=now-state['land_time']<=.7 and state['landing_shots']<4:label='landing'
  if label and now-state['last_shot']>=.23:
   name=f'{len(report["captures"]):03d}_{view}_{label}_{phase:05.2f}.png';file=OUT/name
   u.SystemLibrary.execute_console_command(world,'HighResShot 1 filename="'+str(file)+'"')
   report['captures'].append(dict(row,file=name,action=label));state['last_shot']=now
   if label=='landing':state['landing_shots']+=1
   checkpoint()
 except Exception:
  report['error']=traceback.format_exc();finish('failed')
handle=u.register_slate_post_tick_callback(tick)
checkpoint()
