"""Read-only live PIE phase probe. No map/asset saves; evidence in SlidePass only."""
import unreal as u
import time,json,traceback,gc
from pathlib import Path
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
OUT=ROOT/'Saved/SlidePass/session-2';OUT.mkdir(parents=True,exist_ok=True)
REPORT=OUT/'runtime-probe.json'
r={'status':'running','hero':'Champion','mode':'live PIE sprint -> slide -> moving exit','samples':[],'actions':[]}
state={'phase':'start','started':time.monotonic()};busy=False
level=u.get_editor_subsystem(u.LevelEditorSubsystem)
editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
def save():REPORT.write_text(json.dumps(r,indent=2)+'\n')
def finish(error=None):
 r['status']='failed' if error else 'success'
 if error:r.update(error=str(error),traceback=traceback.format_exc())
 save();level.editor_request_end_play();state['phase']='end';state['end']=time.monotonic()
def tick(delta):
 global busy,handle
 if busy:return
 busy=True
 try:
  now=time.monotonic()
  if state['phase']=='end':
   if now-state['end']>2:
    u.unregister_slate_post_tick_callback(handle);state.clear();gc.collect();u.SystemLibrary.quit_editor()
   return
  if now-state['started']>90:raise RuntimeError('PIE probe timeout')
  if state['phase']=='start':
   level.editor_request_begin_play();state['phase']='load';return
  if state['phase']=='load':
   world=editor.get_game_world()
   if not world:return
   pawn=u.GameplayStatics.get_player_character(world,0)
   if not pawn:return
   pawn.select_character('Champion');state.update(pawn=pawn,world=world,phase='hero');return
  pawn=state['pawn']
  if state['phase']=='hero':
   if str(pawn.get_active_character_name())!='Champion':return
   move=pawn.get_component_by_class(u.SeleneMovementComponent)
   pawn.set_actor_location_and_rotation(u.Vector(0,0,90),u.Rotator(),False,False)
   pawn.set_movement_pace(u.SelenePace.SPRINT)
   move.set_editor_property('velocity',u.Vector())
   state.update(move=move,phase='drive',time=now,slide=False,stop=False);return
  move=state['move'];t=now-state['time']
  pawn.add_movement_input(u.Vector(1,0,0),1.,False)
  if t>1.2 and not state['slide']:
   accepted=move.try_slide();state['slide']=True;r['actions'].append(dict(action='TrySlide',t=t,accepted=accepted))
  if t>2.3 and not state['stop']:
   move.stop_slide();state['stop']=True;r['actions'].append(dict(action='StopSlide',t=t))
  mesh=pawn.get_component_by_class(u.SkeletalMeshComponent);anim=mesh.get_anim_instance();montage=anim.get_current_active_montage() if anim else None
  sequence=None
  if montage:
   tracks=montage.get_editor_property('slot_anim_tracks')
   if tracks:
    segments=tracks[0].get_editor_property('anim_track').get_editor_property('anim_segments')
    if segments:
     asset=segments[0].get_editor_property('anim_reference');sequence=asset.get_name() if asset else None
  v=move.get_editor_property('velocity')
  r['samples'].append(dict(t=t,speed=(v.x*v.x+v.y*v.y)**.5,movement=str(move.get_editor_property('movement_mode')),custom=move.get_editor_property('custom_movement_mode'),montage=montage.get_name() if montage else None,sequence=sequence,position=anim.montage_get_position(montage) if montage else None,base=anim.get_animation_asset().get_name() if anim and anim.get_animation_asset() else None))
  if t>3.8:
   r['accepted_slide']=any(a.get('accepted') for a in r['actions'])
   r['out_survives_0_5_seconds']=any(s['t']>2.8 and s.get('sequence') and 'Slide_KneesOut_Out_Moving' in s['sequence'] for s in r['samples'])
   finish();return
  if len(r['samples'])%30==0:save()
 except Exception as exc:finish(exc)
 finally:busy=False
if REPORT.exists():raise RuntimeError('Existing runtime probe receipt; do not replay')
save();handle=u.register_slate_post_tick_callback(tick)
