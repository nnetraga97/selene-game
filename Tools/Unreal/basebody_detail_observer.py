"""Runtime eye/material and skirt/shoulder capture using AnimMatch; no asset or level saves."""
import json,math,os,time,traceback
from pathlib import Path
import unreal as u
OUT=Path(os.environ['SELENE_BASEBODY_DETAIL_OUTPUT']);OUT.mkdir(parents=True,exist_ok=True)
HERO=os.environ.get('SELENE_DETAIL_HERO','Base')
report={'status':'waiting','captures':[],'samples':[]};state={'start':None,'last_shot':-100.,'wall_start':time.monotonic()}
def checkpoint():(OUT/'observer.json').write_text(json.dumps(report,indent=2)+'\n')
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
   if time.monotonic()-state['wall_start']>30:raise RuntimeError('Game World not found')
   return
  char=u.GameplayStatics.get_player_character(world,0)
  if not char or str(char.get_active_character_name())!=HERO:return
  now=u.GameplayStatics.get_time_seconds(world)
  mesh=char.get_component_by_class(u.SkeletalMeshComponent)
  if state['start'] is None:
   state['start']=now;report['status']='recording';report['world']=world.get_path_name()
   report['runtime_materials']=[{'index':i,'slot':str(n),'material':mesh.get_material(i).get_path_name()} for i,n in enumerate(mesh.get_material_slot_names())]
   report['runtime_mesh']=mesh.get_skinned_asset().get_path_name()
   if HERO=='Ysolde':
    expected={'Ysolde_Body_Opaque':'MI_Toon_Ysolde_Body','Ysolde_Cloth_TwoSided':'MI_Toon_Ysolde_Cloth'}
    expected_mesh='/Game/Assets/council-envoy/council-envoy/SkeletalMeshes/council-envoy.council-envoy'
   else:
    project=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
    ret=json.loads((project/'Saved/NerineHookup/session-1'/HERO/'retarget/report.json').read_text())
    expected={slot['slot']:mat['asset'].split('.')[-1] for slot,mat in zip(ret['slots'],ret['materials'])}
    slug='nerine' if HERO=='Nerine' else 'base-female-v2'
    expected_mesh=f'/Game/Assets/{slug}/{slug}/SkeletalMeshes/{slug}.{slug}'
   assert {m['slot']:m['material'].split('.')[-1] for m in report['runtime_materials']}==expected
   assert report['runtime_mesh']==expected_mesh
   report['hero']=HERO
   checkpoint()
  elapsed=now-state['start']-5
  if elapsed<0:return
  if elapsed>=42:finish('success');u.SystemLibrary.execute_console_command(world,'quit');return
  view=['front','side','back'][min(2,int(elapsed/14))];phase=elapsed%14
  boom=char.get_component_by_class(u.SpringArmComponent)
  # Isolate eyes during settled idle; all motion phases show body/skirt at close range.
  eyes=phase<1.8 and view=='front'
  gameplay=os.environ.get('SELENE_BASEBODY_DETAIL_DISTANCE')=='gameplay'
  report['distance']='gameplay' if gameplay else 'close'
  boom.set_editor_property('target_arm_length',450. if gameplay else (240. if eyes else 310.))
  boom.set_editor_property('target_offset',u.Vector(0,0,0 if gameplay else -5))
  u.SystemLibrary.execute_console_command(world,'fov '+('90' if gameplay else '40'))
  velocity=char.get_velocity();angles={};positions={}
  for side in ('l','r'):
   points=[xyz(mesh.get_socket_location(b+'_'+side)) for b in ('thigh','calf','foot')];angles[side]=flex(*points);positions[side]=points
  row={'time':elapsed,'phase':phase,'view':view,'velocity':xyz(velocity),'knee_flexion_degrees':angles,'joints':positions}
  report['samples'].append(row)
  speed=math.hypot(velocity.x,velocity.y);label=None
  if .7<phase<1.6:label='idle_hand_interior'
  elif 3.0<phase<3.8:label='walk_stride'
  elif 4.2<phase<5.8 and speed>300:label='run_stride'
  elif 6.2<phase<7.7 and speed>500:label='sprint'
  elif 12.1<phase<12.8:label='jump_shoulders'
  elif 13<phase<13.8:label='landing_bend'
  if label and now-state['last_shot']>.4:
   name=f'{len(report["captures"]):03d}_{view}_{label}_{phase:05.2f}.png'
   u.SystemLibrary.execute_console_command(world,'HighResShot 1 filename="'+str(OUT/name)+'"')
   report['captures'].append(dict(row,file=name,action=label));state['last_shot']=now;checkpoint()
 except Exception:
  report['error']=traceback.format_exc();finish('failed');u.SystemLibrary.execute_console_command(world,'quit')
handle=u.register_slate_post_tick_callback(tick);checkpoint()
