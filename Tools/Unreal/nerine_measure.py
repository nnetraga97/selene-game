"""Read-only 60 Hz raw/unlocked and compressed/runtime audit before choosing corrections."""
import json,math,os,statistics,traceback
from pathlib import Path
import unreal as u
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));OUT=Path(os.environ['SELENE_STAGE_REPORT'])
source=json.loads((ROOT/os.environ.get('SELENE_NERINE_SOURCE_REPORT','Saved/NerineHookup/session-1/Nerine/retarget/report.json')).read_text())
ANIM_BASE=os.environ.get('SELENE_NERINE_ANIM_BASE','/Game/Selene/Characters/Nerine/Anims')
report={'status':'running','clips':[],'saved_assets':[]}
def vec(v):return [v.x,v.y,v.z]
def sample(a,mesh,raw):
 opts=u.AnimPoseEvaluationOptions()
 for k,v in dict(evaluation_type=u.AnimDataEvalType.RAW if raw else u.AnimDataEvalType.COMPRESSED,should_retarget=True,extract_root_motion=False,incorporate_root_motion_into_pose=raw,optional_skeletal_mesh=mesh,evaluate_curves=False).items():opts.set_editor_property(k,v)
 length=a.get_play_length();times=[min(i/60,length) for i in range(math.ceil(length*60)+1)]
 for t in times:u.AnimPoseExtensions.get_anim_pose_at_time(a,t,opts)
 rows=[]
 for t in times:
  p=u.AnimPoseExtensions.get_anim_pose_at_time(a,t,opts)
  rows.append({'time':t,'bones':{b:vec(u.AnimPoseExtensions.get_bone_pose(p,b,u.AnimPoseSpaces.WORLD).translation) for b in ['root','pelvis','ball_l','ball_r','calf_l','calf_r','head','hand_l','hand_r']}})
 summary={b:{'first':rows[0]['bones'][b],'last':rows[-1]['bones'][b],'range':[[min(s['bones'][b][k] for s in rows),max(s['bones'][b][k] for s in rows)] for k in range(3)]} for b in ['root','pelvis']}
 candidates=[]
 for b in ['ball_l','ball_r']:
  xyz=[s['bones'][b] for s in rows];h=sorted(p[2] for p in xyz)[int((len(xyz)-1)*.35)]
  for i in range(1,len(rows)-1):
   dt=rows[i+1]['time']-rows[i-1]['time'];v=[(xyz[i+1][k]-xyz[i-1][k])/dt for k in range(3)]
   if xyz[i][2]<=h and abs(v[2])<25 and -v[1]>30:candidates.append(-v[1])
 return {'seconds':length,'summary':summary,'stance_speed_cm_s':statistics.median(candidates) if candidates else None,'stance_sample_count':len(candidates),'samples':rows}
def main():
 mesh=u.load_asset('/Game/Assets/nerine/nerine/SkeletalMeshes/nerine')
 report['chains']=[b['name'] for b in source['hierarchy'] if b['name'].endswith('_00')];assert len(report['chains'])==10
 report['slots']=source['slots']
 targets=source['clips']+[{'role':n,'asset':ANIM_BASE+'/MM_'+n+'_Nerine'} for n in ['Jump','Fall_Loop','Land']]
 for row in targets:
  a=u.load_asset(row['asset']);entry=dict(row)
  entry['flags']={k:str(a.get_editor_property(k)) for k in ['enable_root_motion','force_root_lock','root_motion_root_lock']}
  entry['raw']=sample(a,mesh,True);entry['runtime']=sample(a,mesh,False);report['clips'].append(entry)
  OUT.write_text(json.dumps(report,indent=2)+'\n')
 mi=u.load_asset('/Game/Selene/Materials/Character/MI_Toon_Nerine_Body');report['material']={'parent':mi.get_editor_property('parent').get_path_name(),'texture':u.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mi,'BaseColorTex').get_path_name()}
 report['status']='success'
try:main()
except Exception:report.update(status='failed',error=traceback.format_exc())
OUT.write_text(json.dumps(report,indent=2)+'\n')
if report['status']!='success':raise RuntimeError(report['error'])
