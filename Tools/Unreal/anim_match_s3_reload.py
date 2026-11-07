"""Measure compressed AM1 transitions, then normalize hips XY in new immutable copies."""
import json, math, traceback
from pathlib import Path
import unreal as u
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
OUT=ROOT/'Saved/AnimMatch/session-3/compressed-reload.json'
report=dict(status='running',heroes={})
NAMES=['M_Neutral_'+n for n in ['Walk_Start_F_Lfoot','Run_Start_F_Lfoot','Walk_Stop_F_Lfoot','Run_Stop_F_Lfoot','Sprint_Stop_F_Lfoot','Walk_Pivot_F_B_Lfoot','Run_Pivot_F_B_Lfoot']]
LIB=u.EditorAssetLibrary
BONE='mixamorig_Hips'
def checkpoint(): OUT.write_text(json.dumps(report,indent=2))
def sample(anim,mesh,incorporate=False):
 opts=u.AnimPoseEvaluationOptions()
 for k,v in dict(evaluation_type=u.AnimDataEvalType.COMPRESSED,should_retarget=True,extract_root_motion=False,incorporate_root_motion_into_pose=incorporate,optional_skeletal_mesh=mesh,evaluate_curves=False).items():opts.set_editor_property(k,v)
 length=anim.get_play_length();rows=[]
 for i in range(math.ceil(length*60)+1):
  t=min(i/60.,length);pose=u.AnimPoseExtensions.get_anim_pose_at_time(anim,t,opts)
  p=u.AnimPoseExtensions.get_bone_pose(pose,BONE,u.AnimPoseSpaces.WORLD).translation
  rows.append(dict(time=t,hips=[p.x,p.y,p.z]))
 return dict(seconds=length,first=rows[0]['hips'],last=rows[-1]['hips'],minimum=[min(s['hips'][a] for s in rows) for a in range(3)],maximum=[max(s['hips'][a] for s in rows) for a in range(3)],samples=rows)
original=json.loads((OUT.parent/'normalization.json').read_text())
# Preload assets and evaluate a complete warm-up pass before reporting frame zero.
for hero,rows in original['heroes'].items():
 slug={'Fixer':'night-market-fixer','Courier':'scooter-courier'}[hero]
 mesh=u.load_asset('/Game/Assets/'+slug+'/'+slug+'/SkeletalMeshes/'+slug)
 assets=[(row,kind,u.load_asset(row[key])) for row in rows for kind,key in [('before','source'),('after','asset')]]
 for row,kind,anim in assets: sample(anim,mesh)
 report['heroes'][hero]=[]
 for row in rows:
  item=dict(source=row['source'],asset=row['asset'])
  for kind,key in [('before','source'),('after','asset')]: item[kind]=sample(u.load_asset(row[key]),mesh)
  item['before_unlocked_compressed']=sample(u.load_asset(row['source']),mesh,True)
  report['heroes'][hero].append(item)
report['status']='success'
checkpoint()
