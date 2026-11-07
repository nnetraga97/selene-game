"""Scoped candidate: preserve root-facing pose while aligning child chains. Originals retained."""
import json, math, traceback
from pathlib import Path
import unreal as u
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
OUT=ROOT/'Saved/AnimMatch/session-1/fix.json'
AUDIT=json.loads((OUT.parent/'audit.json').read_text())
report=dict(status='running',heroes={})
LIB=u.EditorAssetLibrary
NAMES=['M_Neutral_Stand_Idle_Loop','M_Neutral_Walk_Loop_F','M_Neutral_Run_Loop_F','M_Neutral_Sprint_Loop_F','M_Neutral_Walk_Start_F_Lfoot','M_Neutral_Run_Start_F_Lfoot','M_Neutral_Walk_Stop_F_Lfoot','M_Neutral_Run_Stop_F_Lfoot','M_Neutral_Sprint_Stop_F_Lfoot','M_Neutral_Walk_Pivot_F_B_Lfoot','M_Neutral_Run_Pivot_F_B_Lfoot']
SOURCES=['/Game/Selene/Animation/GASP/'+n for n in NAMES]+['/Game/Characters/Mannequins/Anims/Unarmed/Jump/'+n for n in ['MM_Jump','MM_Fall_Loop','MM_Land']]
def checkpoint(): OUT.write_text(json.dumps(report,indent=2))
def mul(a,b):
 x,y,z,w=a;X,Y,Z,W=b
 return (w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z)
def main():
 for hero in ['Fixer','Courier']:
  old='/Game/Selene/Characters/'+hero
  base=old+'/AnimMatchS1'
  if LIB.does_directory_exist(base): raise RuntimeError('Candidate exists; no replay: '+base)
  mesh=u.load_asset(AUDIT['heroes'][hero]['mesh'])
  rtg=u.AssetToolsHelpers.get_asset_tools().duplicate_asset('RTG_Manny_To_'+hero+'_Facing',base,u.load_asset(old+'/RTG_Manny_To_'+hero))
  r=u.IKRetargeterController.get_controller(rtg);T=u.RetargetSourceOrTarget.TARGET
  pose=r.create_retarget_pose('FacingManny',T);r.set_current_retarget_pose(pose,T);r.reset_retarget_pose(pose,[],T)
  x,y,z,w=AUDIT['heroes'][hero]['reference_hips_quaternion'];bind=(x,y,z,w)
  half=math.radians(-90)/2
  delta=mul(mul((-x,-y,-z,w),(0,0,math.sin(half),math.cos(half))),bind)
  r.set_rotation_offset_for_retarget_pose_bone('mixamorig_Hips',u.Quat(*delta),T)
  idle=u.load_asset(old+'/Anims/GASP/M_Neutral_Stand_Idle_Loop_'+hero)
  opts=u.AnimPoseEvaluationOptions();opts.set_editor_property('optional_skeletal_mesh',mesh)
  p=u.AnimPoseExtensions.get_anim_pose_at_time(idle,0,opts)
  bones=[b for b in u.AnimPoseExtensions.get_bone_names(p) if str(b)!='mixamorig_Hips']
  r.auto_align_bones(bones,u.RetargetAutoAlignMethod.CHAIN_TO_CHAIN,T)
  h=dict(retargeter=rtg.get_path_name(),local_root_delta=delta,pose=r.get_current_retarget_pose(T).export_text(),clips=[])
  report['heroes'][hero]=h;checkpoint()
  if not LIB.save_loaded_asset(rtg,only_if_is_dirty=False): raise RuntimeError('Retargeter save failed')
  inputs=u.IKRetargetBatchOperationInputs()
  for k,v in dict(assets_to_retarget=[LIB.find_asset_data(p) for p in SOURCES],source_mesh=u.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple'),target_mesh=mesh,ik_retarget_asset=rtg,target_path=base+'/Anims',suffix='_'+hero+'_AM1',include_referenced_assets=False,overwrite_existing_files=False,use_source_path=False).items(): inputs.set_editor_property(k,v)
  made=u.IKRetargetBatchOperation.run_batch_retarget(inputs)
  if len(made)!=14: raise RuntimeError('Expected 14 clips: '+hero)
  for data in made:
   anim=data.get_asset();name=anim.get_name();entry=dict(asset=anim.get_path_name())
   anim.set_editor_property('enable_root_motion',False)
   anim.set_editor_property('force_root_lock',True)
   anim.set_editor_property('root_motion_root_lock',u.RootMotionRootLock.ANIM_FIRST_FRAME)
   if any(name.startswith('M_Neutral_'+pace+'_Loop_F_') for pace in ['Walk','Run','Sprint']):
    model=anim.get_editor_property('data_model_interface');frames=model.get_number_of_frames();length=anim.get_play_length()
    opts=u.AnimPoseEvaluationOptions()
    opts.set_editor_property('evaluation_type',u.AnimDataEvalType.RAW);opts.set_editor_property('incorporate_root_motion_into_pose',True);opts.set_editor_property('evaluate_curves',False)
    keys=[]
    for f in range(frames+1):
     p=u.AnimPoseExtensions.get_anim_pose_at_time(anim,length*f/frames,opts)
     keys.append(u.AnimPoseExtensions.get_bone_pose(p,'mixamorig_Hips',u.AnimPoseSpaces.LOCAL))
    dx=keys[-1].translation.x-keys[0].translation.x;dy=keys[-1].translation.y-keys[0].translation.y
    positions=[u.Vector(k.translation.x-dx*f/frames,k.translation.y-dy*f/frames,k.translation.z) for f,k in enumerate(keys)]
    c=anim.get_editor_property('controller');c.open_bracket('AnimMatch in-place loop',False)
    try:
     if not c.set_bone_track_keys('mixamorig_Hips',positions,[k.rotation for k in keys],[k.scale3d for k in keys],False): raise RuntimeError('Keys failed')
    finally: c.close_bracket(False)
    anim.set_editor_property('force_root_lock',False)
    entry['speed_cm_s']=math.hypot(dx,dy)/length
   if not LIB.save_loaded_asset(anim,only_if_is_dirty=False): raise RuntimeError('Clip save failed: '+name)
   h['clips'].append(entry);checkpoint()
 report['status']='success'
try: main()
except Exception: report.update(status='failed',error=traceback.format_exc())
finally: checkpoint()
if report['status']!='success': raise RuntimeError(report['error'])
