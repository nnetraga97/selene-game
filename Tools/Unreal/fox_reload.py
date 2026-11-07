"""Read-only fresh compressed Fox audit, including imported hierarchy and colliders."""
import json, math, os, statistics, traceback
from pathlib import Path
import unreal as u
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));OUT=Path(os.environ['SELENE_STAGE_REPORT'])
source=json.loads((ROOT/'Saved/FoxHookup/session-1/clips/report.json').read_text())
report={'status':'running','clips':[],'saved_assets':[]}
def vec(v):return [v.x,v.y,v.z]
def main():
 mesh=u.load_asset(os.environ['SELENE_CHAR_MESH']);comp=u.SkeletalMeshComponent();comp.set_skeletal_mesh_asset(mesh)
 bones=[str(comp.get_bone_name(i)) for i in range(comp.get_num_bones())]
 report['hierarchy']=[{'name':n,'parent':str(comp.get_parent_bone(n))} for n in bones]
 report['chains']=[n for n in bones if n.endswith('_00')];assert len(report['chains'])==24
 opts=u.AnimPoseEvaluationOptions()
 for k,v in dict(evaluation_type=u.AnimDataEvalType.COMPRESSED,should_retarget=True,extract_root_motion=False,incorporate_root_motion_into_pose=False,optional_skeletal_mesh=mesh,evaluate_curves=False).items():opts.set_editor_property(k,v)
 targets=source['clips']+source['transitions']
 for row in targets:
  a=u.load_asset(row['asset']);length=a.get_play_length()
  # Warm up entire compressed clip before collecting evidence.
  for i in range(math.ceil(length*60)+1):u.AnimPoseExtensions.get_anim_pose_at_time(a,min(i/60,length),opts)
  samples=[]
  for i in range(math.ceil(length*60)+1):
   t=min(i/60,length);p=u.AnimPoseExtensions.get_anim_pose_at_time(a,t,opts)
   samples.append({'time':t,'bones':{b:vec(u.AnimPoseExtensions.get_bone_pose(p,b,u.AnimPoseSpaces.WORLD).translation) for b in ['mixamorig_Hips','mixamorig_LeftToeBase','mixamorig_RightToeBase','mixamorig_LeftLeg','mixamorig_RightLeg']}})
  positions=[s['bones']['mixamorig_Hips'] for s in samples];entry=dict(role=row['role'],asset=row['asset'],hips_first=positions[0],hips_last=positions[-1],hips_range=[[min(p[k] for p in positions),max(p[k] for p in positions)] for k in range(3)],samples=samples)
  if row['role'] in ('WalkLoop','RunLoop','SprintLoop'):
   candidates=[]
   for b in ('mixamorig_LeftToeBase','mixamorig_RightToeBase'):
    xyz=[s['bones'][b] for s in samples];h=sorted(p[2] for p in xyz)[int((len(xyz)-1)*.35)]
    for i in range(1,len(samples)-1):
     dt=samples[i+1]['time']-samples[i-1]['time'];v=[(xyz[i+1][k]-xyz[i-1][k])/dt for k in range(3)]
     if xyz[i][2]<=h and abs(v[2])<25 and -v[1]>30:candidates.append(-v[1])
   entry['stance_speed_cm_s']=statistics.median(candidates) if candidates else None;entry['stance_sample_count']=len(candidates)
  report['clips'].append(entry)
 # Record reference collider endpoints, no unticked socket assumptions.
 p=u.AnimPoseExtensions.get_anim_pose_at_time(u.load_asset(source['clips'][0]['asset']),0,opts)
 refnames=['mixamorig_Hips','mixamorig_LeftUpLeg','mixamorig_RightUpLeg','mixamorig_LeftLeg','mixamorig_RightLeg','mixamorig_LeftForeArm','mixamorig_RightForeArm','mixamorig_LeftHand','mixamorig_RightHand']+report['chains']
 report['reference_positions_cm']={b:vec(u.AnimPoseExtensions.get_ref_bone_pose(p,b,u.AnimPoseSpaces.WORLD).translation) for b in refnames}
 mi=u.load_asset('/Game/Selene/Materials/Character/MI_Toon_Fox');report['material']={'parent':mi.get_editor_property('parent').get_path_name(),'texture':u.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mi,'BaseColorTex').get_path_name()}
 report['status']='success'
try:main()
except Exception:report.update(status='failed',error=traceback.format_exc())
OUT.write_text(json.dumps(report,indent=2)+'\n')
if report['status']!='success':raise RuntimeError(report['error'])
