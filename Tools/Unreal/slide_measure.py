"""Fresh compressed playback measurement of new slides, no asset saves."""
import json, math, traceback, hashlib
from pathlib import Path
import unreal as u
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
OUT=ROOT/'Saved/SlidePass/session-1'
r={'status':'running','clips':[]}
def sample(anim,mesh):
 opts=u.AnimPoseEvaluationOptions()
 for k,v in dict(optional_skeletal_mesh=mesh,evaluation_type=u.AnimDataEvalType.COMPRESSED,extract_root_motion=False,incorporate_root_motion_into_pose=False,evaluate_curves=False).items():opts.set_editor_property(k,v)
 bones=u.AnimPoseExtensions.get_bone_names(u.AnimPoseExtensions.get_anim_pose_at_time(anim,0,opts))
 bones=[str(b) for b in bones]
 chosen=[b for b in ['root','pelvis','mixamorig_Hips','ball_l','ball_r','calf_l','calf_r','foot_l','foot_r','mixamorig_LeftFoot','mixamorig_RightFoot','mixamorig_LeftLeg','mixamorig_RightLeg'] if b in bones]
 rows=[]
 for i in range(math.ceil(anim.get_play_length()*10)+1):
  t=min(i*.1,anim.get_play_length())
  u.AnimPoseExtensions.get_anim_pose_at_time(anim,t,opts)
  pose=u.AnimPoseExtensions.get_anim_pose_at_time(anim,t,opts)
  poses={}
  for b in chosen:
   v=u.AnimPoseExtensions.get_bone_pose(pose,b,u.AnimPoseSpaces.WORLD).translation
   poses[b]=[v.x,v.y,v.z]
  rows.append({'time':t,'bones':poses})
 return {'bones':bones,'samples':rows}
try:
 sources=json.loads((OUT/'source-reload.json').read_text())
 heroes=json.loads((OUT/'retarget.json').read_text())
 if heroes['status']!='success':raise RuntimeError('Retarget incomplete')
 work=[('Manny','/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple',c) for c in sources['clips']]
 work += [(name,h['mesh'],c) for name,h in heroes['heroes'].items() for c in h['clips']]
 for name,meshpath,c in work:
  anim=u.load_asset(c['package']);mesh=u.load_asset(meshpath)
  assert anim.get_editor_property('skeleton')==mesh.get_editor_property('skeleton')
  assert anim.get_editor_property('force_root_lock') and not anim.get_editor_property('enable_root_motion')
  assert anim.get_editor_property('root_motion_root_lock')==u.RootMotionRootLock.REF_POSE
  r['clips'].append(dict(hero=name,role=c['role'],package=c['package'],**sample(anim,mesh)))
  (OUT/'measure.json').write_text(json.dumps(r,indent=2))
 r['status']='success'
except Exception:r.update(status='failed',error=traceback.format_exc())
finally:(OUT/'measure.json').write_text(json.dumps(r,indent=2))
if r['status']!='success':raise RuntimeError(r['error'])
