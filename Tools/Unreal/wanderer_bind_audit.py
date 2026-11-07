"""Read-only bind direction diagnosis before any pose correction."""
import json,math,os
from pathlib import Path
import unreal as u
out=Path(os.environ['SELENE_STAGE_REPORT']);report={'status':'success','rigs':{}}
for name,meshpath,animpath in [('Wanderer','/Game/Assets/teal-wanderer/teal-wanderer/SkeletalMeshes/teal-wanderer','/Game/Selene/Characters/Wanderer/Anims/MM_Idle_Wanderer'),('Manny','/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple','/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle')]:
 mesh=u.load_asset(meshpath);anim=u.load_asset(animpath)
 opts=u.AnimPoseEvaluationOptions();opts.set_editor_property('optional_skeletal_mesh',mesh)
 p=u.AnimPoseExtensions.get_anim_pose_at_time(anim,0,opts)
 bones=['root','pelvis','spine_01','spine_05','head']+[b+'_'+s for s in ['l','r'] for b in ['clavicle','upperarm','lowerarm','hand','thigh','calf','foot','ball']]
 positions={}
 for b in bones:
  tr=u.AnimPoseExtensions.get_ref_bone_pose(p,b,u.AnimPoseSpaces.WORLD);v=tr.translation;q=tr.rotation
  positions[b]={'position':[v.x,v.y,v.z],'rotation':[q.x,q.y,q.z,q.w]}
 report['rigs'][name]=positions
out.write_text(json.dumps(report,indent=2)+'\n')
