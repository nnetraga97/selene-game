"""Measure compressed AM1 transitions, then normalize hips XY in new immutable copies."""
import json, math, traceback
from pathlib import Path
import unreal as u
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
OUT=ROOT/'Saved/AnimMatch/session-3/normalization.json'
report=dict(status='running',heroes={})
NAMES=['M_Neutral_'+n for n in ['Walk_Start_F_Lfoot','Run_Start_F_Lfoot','Walk_Stop_F_Lfoot','Run_Stop_F_Lfoot','Sprint_Stop_F_Lfoot','Walk_Pivot_F_B_Lfoot','Run_Pivot_F_B_Lfoot']]
LIB=u.EditorAssetLibrary
BONE='mixamorig_Hips'
def checkpoint(): OUT.write_text(json.dumps(report,indent=2))
def sample(anim,mesh):
 opts=u.AnimPoseEvaluationOptions()
 for k,v in dict(evaluation_type=u.AnimDataEvalType.COMPRESSED,should_retarget=True,extract_root_motion=False,incorporate_root_motion_into_pose=False,optional_skeletal_mesh=mesh,evaluate_curves=False).items():opts.set_editor_property(k,v)
 length=anim.get_play_length();rows=[]
 for i in range(math.ceil(length*60)+1):
  t=min(i/60.,length);pose=u.AnimPoseExtensions.get_anim_pose_at_time(anim,t,opts)
  p=u.AnimPoseExtensions.get_bone_pose(pose,BONE,u.AnimPoseSpaces.WORLD).translation
  rows.append(dict(time=t,hips=[p.x,p.y,p.z]))
 return dict(seconds=length,first=rows[0]['hips'],last=rows[-1]['hips'],minimum=[min(s['hips'][a] for s in rows) for a in range(3)],maximum=[max(s['hips'][a] for s in rows) for a in range(3)],samples=rows)
def main():
 if OUT.exists():raise RuntimeError('Do not replay immutable normalization')
 for hero,slug in [('Fixer','night-market-fixer'),('Courier','scooter-courier')]:
  mesh=u.load_asset('/Game/Assets/'+slug+'/'+slug+'/SkeletalMeshes/'+slug)
  base='/Game/Selene/Characters/'+hero;dest=base+'/AnimMatchS3/Anims'
  if LIB.does_directory_exist(dest):raise RuntimeError('Outputs already exist')
  rows=[];report['heroes'][hero]=rows
  # Measure every original before creating any copies for this hero.
  for name in NAMES:
   original=u.load_asset(base+'/AnimMatchS1/Anims/'+name+'_'+hero+'_AM1')
   rows.append(dict(source=original.get_path_name(),before=sample(original,mesh)))
  checkpoint()
  for row,name in zip(rows,NAMES):
   anim=u.AssetToolsHelpers.get_asset_tools().duplicate_asset(name+'_'+hero+'_AM3',dest,u.load_asset(row['source']))
   # RAW+incorporate includes unlocked authored motion; subtract the initial XY only.
   opts=u.AnimPoseEvaluationOptions()
   for k,v in dict(evaluation_type=u.AnimDataEvalType.RAW,incorporate_root_motion_into_pose=True,evaluate_curves=False).items():opts.set_editor_property(k,v)
   frames=anim.get_editor_property('data_model_interface').get_number_of_frames();length=anim.get_play_length();keys=[]
   for f in range(frames+1):
    pose=u.AnimPoseExtensions.get_anim_pose_at_time(anim,length*f/frames,opts)
    keys.append(u.AnimPoseExtensions.get_bone_pose(pose,BONE,u.AnimPoseSpaces.LOCAL))
   x,y=keys[0].translation.x,keys[0].translation.y
   c=anim.get_editor_property('controller');c.open_bracket('Normalize transition hips origin XY',False)
   try:
    if not c.set_bone_track_keys(BONE,[u.Vector(k.translation.x-x,k.translation.y-y,k.translation.z) for k in keys],[k.rotation for k in keys],[k.scale3d for k in keys],False):raise RuntimeError('Track save failed')
   finally:c.close_bracket(False)
   anim.set_editor_property('enable_root_motion',False);anim.set_editor_property('force_root_lock',True)
   # ZERO would erase hips height and the accepted root-facing rotation.
   anim.set_editor_property('root_motion_root_lock',u.RootMotionRootLock.ANIM_FIRST_FRAME)
   if not LIB.save_loaded_asset(anim,only_if_is_dirty=False):raise RuntimeError('Asset save failed')
   row.update(asset=anim.get_path_name(),removed_xy_cm=[x,y],after=sample(anim,mesh));checkpoint()
 report['status']='success'
try:main()
except Exception:report.update(status='failed',error=traceback.format_exc())
finally:checkpoint()
if report['status']!='success':raise RuntimeError(report['error'])
