"""Offscreen candidate pose sheets via native DefaultSlot. No level/asset saves.
These are deterministic animation diagnostics, not live CMC/transition acceptance.
"""
import json, math, time, traceback, gc, re, os
from pathlib import Path
import unreal as u
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
INPUT=ROOT/'Saved/SlidePass/session-1'
OUT=ROOT/'Saved/SlidePass'/os.environ.get('SELENE_SLIDE_SESSION','session-1'); IMAGES=OUT/'captures';IMAGES.mkdir(parents=True,exist_ok=True)
COMPENSATE=os.environ.get('SELENE_SLIDE_COMPENSATE','0')=='1'
report={'status':'running','mode':'native DefaultSlot sampled poses; not live movement or continuity proof','shots':[]}
manifest=json.loads((INPUT/'retarget.json').read_text())
report['root_compensation']=COMPENSATE
roster={}
for line in (ROOT/'Config/DefaultGame.ini').read_text().splitlines():
 if line.startswith('+Roster='):
  fields=dict(re.findall(r'(\w+)="([^"]*)"',line));roster[fields['Name']]=fields
names=['Champion','Angel','Sparrow','Fixer','Courier','Fox','Wanderer','Ysolde','Nerine','Base']
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_game_view(True)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
u.SystemLibrary.execute_console_command(world,'r.ScreenPercentage 100')
u.SystemLibrary.execute_console_command(world,'r.MotionBlurQuality 0')
origin=u.Vector(-1000,0,0)
shots=[]
for hero in names:
 for view in ['side','front']:
  for phase,field,seconds,slot in [('run','RunLoop',.2,False),('into','SlideInto',.85,True),('loop','SlideLoop',.3,True),('out_run','SlideOutMoving',.45,True),('resume_run','RunLoop',.6,False),('out_stand','SlideOutStand',.5,True),('stand','SlideOutStand',1.25,True)]:
   shots.append(dict(hero=hero,view=view,phase=phase,field=field,seconds=seconds,slot=slot))
for hero in ['Ysolde','Sparrow']:
 for view in ['side','front']:
  for phase,field in [('walk','WalkLoop'),('run','RunLoop'),('sprint','SprintLoop'),('jump','Jump')]:
   shots.append(dict(hero=hero,view=view,phase='regression_'+phase,field=field,seconds=.25,slot=False))
state={'phase':'init','time':time.monotonic(),'index':0,'hero':None};busy=False;spawned=[]
def checkpoint(): (OUT/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
def finish(error=None):
 report['status']='failed' if error else 'success'
 if error:report.update(error=str(error),traceback=traceback.format_exc())
 checkpoint();state['phase']='cleanup'
def tick(delta):
 global busy,handle
 if busy:return
 busy=True
 try:
  now=time.monotonic();phase=state['phase']
  if phase=='cleanup':
   for a in spawned:actors.destroy_actor(a)
   spawned.clear();state.clear();state['phase']='quit';gc.collect();return
  if phase=='quit':
   u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor();return
  if phase=='init':
   if now-state['time']<12:return
   state['phase']='prepare';return
  if phase=='prepare':
   shot=shots[state['index']]
   if state['hero']!=shot['hero']:
    if state.get('actor'):actors.destroy_actor(state['actor']);spawned.remove(state['actor'])
    actor=actors.spawn_actor_from_class(u.load_class(None,'/Script/Selene.SeleneCharacter'),origin,transient=True);spawned.append(actor)
    actor.select_character(shot['hero']);state.update(actor=actor,hero=shot['hero'],phase='load',time=now);return
   state['phase']='pose';return
  if phase=='load':
   actor=state['actor']
   if str(actor.get_active_character_name())!=state['hero']:
    if now-state['time']>45:raise RuntimeError('Hero load timeout '+state['hero'])
    return
   component=actor.get_component_by_class(u.SkeletalMeshComponent)
   actor.set_actor_tick_enabled(False)
   component.set_component_tick_enabled(False)
   component.set_relative_location(u.Vector(),False,False)
   component.set_relative_rotation(u.Rotator(),False,False)
   component.set_update_animation_in_editor(True)
   component.set_editor_property('visibility_based_anim_tick_option',u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
   state.update(component=component,instance=component.get_anim_instance(),phase='pose');return
  if phase=='pose':
   shot=shots[state['index']];entry=roster[shot['hero']];component=state['component'];instance=state['instance']
   clip=u.load_asset(entry[shot['field']]);base=u.load_asset(entry['RunLoop'])
   component.set_relative_location(u.Vector(),False,False)
   component.set_relative_rotation(u.Rotator(),False,False)
   instance.set_animation_asset(base if shot['slot'] else clip,True,1.)
   instance.set_position(shot['seconds'] if not shot['slot'] else 0.,False)
   instance.set_playing(False)
   if shot['slot']:
    montage=instance.play_slot_animation_as_dynamic_montage(clip,'DefaultSlot',.08,.12,1.,1,-1.,shot['seconds'])
    if not montage:raise RuntimeError('DefaultSlot montage failed')
   for i in range(8):u.SeleneSecondaryAnimInstance.probe_single_node_component(component,1./60.)
   if COMPENSATE and shot['slot']:
    correction=u.SeleneMovementComponent.get_slide_mesh_compensation(component,clip,shot['seconds']+8./60.)
    component.set_relative_transform(u.MathLibrary.compose_transforms(correction,component.get_relative_transform()),False,False)
   # Hold the evaluated bones while the offscreen renderer settles.
   target=origin+u.Vector(0,0,90);offset=u.Vector(360,0,8) if shot['view']=='side' else u.Vector(0,360,8)
   cam=actors.spawn_actor_from_class(u.CameraActor,target+offset,u.MathLibrary.find_look_at_rotation(target+offset,target),transient=True);spawned.append(cam)
   cam.camera_component.set_editor_property('field_of_view',45.)
   cam.camera_component.set_editor_property('constrain_aspect_ratio',False)
   filename=IMAGES/(shot['hero']+'_'+shot['view']+'_'+shot['phase']+'.png')
   if filename.exists():raise RuntimeError('Existing shot: do not replay '+str(filename))
   bones={}
   for bone in ['pelvis','mixamorig_Hips','calf_l','calf_r','mixamorig_LeftLeg','mixamorig_RightLeg']:
    if component.get_bone_index(bone)>=0:
     v=component.get_socket_location(bone)-origin;bones[bone]=[v.x,v.y,v.z]
   state.update(phase='settle',time=now,cam=cam,file=filename,bones=bones);return
  if phase=='settle':
   if now-state['time']<.2:return
   u.AutomationLibrary.take_high_res_screenshot(640,640,str(state['file']),state['cam'])
   state.update(phase='wait',time=time.monotonic());return
  if phase=='wait':
   if not state['file'].exists():
    if now-state['time']>30:raise RuntimeError('Screenshot timeout '+str(state['file']))
    return
   report['shots'].append(dict(**shots[state['index']],file=str(state['file'].relative_to(ROOT)),bones=state['bones']))
   checkpoint();actors.destroy_actor(state['cam']);spawned.remove(state['cam'])
   state['index']+=1
   if state['index']==len(shots):finish();return
   state['phase']='prepare'
 except Exception as exc:finish(exc)
 finally:busy=False
checkpoint();handle=u.register_slate_post_tick_callback(tick)
