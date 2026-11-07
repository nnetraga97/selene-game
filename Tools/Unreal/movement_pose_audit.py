"""Read only compressed Champion pose geometry; never saves assets."""
import json
from pathlib import Path
import unreal as u
out=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))/'Saved/MovementTest/session-2/slide-pose-audit.json'
assert not out.exists()
mesh=u.load_asset('/Game/Assets/festival-champion-p2/festival-champion-p2/SkeletalMeshes/festival-champion-p2')
paths={'jump':'/Game/Selene/Characters/Champion/Anims/MM_Jump_Champion','land':'/Game/Selene/Characters/Champion/Anims/MM_Land_Champion','sprint_stop':'/Game/Selene/Characters/Champion/Anims/GASP/M_Neutral_Sprint_Stop_F_Lfoot_Champion','run_start':'/Game/Selene/Characters/Champion/Anims/GASP/M_Neutral_Run_Start_F_Lfoot_Champion'}
opts=u.AnimPoseEvaluationOptions()
for k,v in dict(evaluation_type=u.AnimDataEvalType.COMPRESSED,should_retarget=True,extract_root_motion=False,incorporate_root_motion_into_pose=False,optional_skeletal_mesh=mesh,evaluate_curves=False).items():opts.set_editor_property(k,v)
report={}
for name,path in paths.items():
 a=u.load_asset(path);length=a.get_play_length(); rows=[]
 for warmup in range(2):
  rows=[]
  for fraction in [0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1]:
   t=length*fraction;pose=u.AnimPoseExtensions.get_anim_pose_at_time(a,t,opts);r={'time':t}
   for bone in ['mixamorig_Hips','mixamorig_LeftFoot','mixamorig_RightFoot','mixamorig_Head']:
    v=u.AnimPoseExtensions.get_bone_pose(pose,bone,u.AnimPoseSpaces.WORLD).translation;r[bone]=[v.x,v.y,v.z]
   rows.append(r)
 report[name]={'asset':path,'samples':rows}
out.write_text(json.dumps(report,indent=2))
u.log('MOVEMENT_POSE_AUDIT_SAVED '+str(out))
