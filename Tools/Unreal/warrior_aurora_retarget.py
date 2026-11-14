"""Warrior: retarget Paragon Aurora's sword set (idle, jog, jump, primary attacks, abilities) onto the Warrior; FK chains, root locked."""
import json,math,os,statistics,traceback
from pathlib import Path
import unreal as u
OUT=Path(os.environ['SELENE_STAGE_REPORT']);report={'status':'running'}
BASE='/Game/Selene/Characters/Warrior';SRC='/Game/ParagonAurora/Characters/Heroes/Aurora/'
LIB=u.EditorAssetLibrary;TOOLS=u.AssetToolsHelpers.get_asset_tools()
CLIPS=['Idle','Jog_Fwd','Jog_Fwd_Start','Jog_Fwd_Stop','Jog_Fwd_Pivot180','Jump_Start','Jump_Apex','Jump_Land','Jump_Recovery',
 'Primary_Attack_A','Primary_Attack_B','Primary_Attack_C','Primary_Attack_Fast_A','Primary_Attack_Fast_B','Primary_Attack_Fast_C','Primary_Attack_Fast_D',
 'Ability_Q','Ability_E','Ability_R','Level_Start','Melee_Attack_Air']
def checkpoint():OUT.write_text(json.dumps(report,indent=2)+'\n')
def save(a):
 if not LIB.save_loaded_asset(a,only_if_is_dirty=False):raise RuntimeError('Save failed '+a.get_path_name())
def bones_of(mesh):
 c=u.SkeletalMeshComponent();c.set_skeletal_mesh_asset(mesh)
 return [(str(c.get_bone_name(i)),str(c.get_parent_bone(c.get_bone_name(i)))) for i in range(c.get_num_bones())]
def main():
 src=u.load_asset(SRC+'Meshes/Aurora');mesh=u.load_asset('/Game/Assets/eclipse-warrior/eclipse-warrior/SkeletalMeshes/eclipse-warrior')
 assert src and mesh
 sb=bones_of(src);names=[b[0] for b in sb];report['aurora_bones']=sb;checkpoint()
 if LIB.does_asset_exist(BASE+'/IK_Aurora'):raise RuntimeError('No replay: IK_Aurora exists')
 ik=TOOLS.create_asset('IK_Aurora',BASE,u.IKRigDefinition,u.IKRigDefinitionFactory());c=u.IKRigController.get_controller(ik)
 assert c.set_skeletal_mesh(src) and c.set_retarget_root('pelvis')
 def last(prefix,cands):
  got=[n for n in cands if n in names];assert got,prefix;return got
 sp=last('spine',['spine_01','spine_02','spine_03','spine_04','spine_05']);nk=last('neck',['neck_01','neck_02'])
 chains=[('Spine',sp[0],sp[-1]),('Neck',nk[0],nk[-1]),('Head','head','head')]
 for side,s in (('Left','l'),('Right','r')):
  chains+=[(side+'Leg','thigh_'+s,'foot_'+s),(side+'Foot','ball_'+s,'ball_'+s),(side+'Clavicle','clavicle_'+s,'clavicle_'+s),(side+'Arm','upperarm_'+s,'hand_'+s)]
  for f in ('thumb','index','middle','ring','pinky'):chains.append((side+f.title(),f+'_01_'+s,f+'_03_'+s))
 for n,a,b in chains:
  assert a in names and b in names,(n,a,b);c.add_retarget_chain(n,a,b,'')
 report['chains']=chains
 tgt=u.load_asset(BASE+'/IK_Warrior');assert tgt
 rtg=TOOLS.create_asset('RTG_Aurora_To_Warrior',BASE,u.IKRetargeter,u.IKRetargetFactory());r=u.IKRetargeterController.get_controller(rtg)
 S,T=u.RetargetSourceOrTarget.SOURCE,u.RetargetSourceOrTarget.TARGET
 for side,rig,m in [(S,ik,src),(T,tgt,mesh)]:r.set_ik_rig(side,rig);r.set_preview_mesh(side,m)
 r.remove_all_ops();r.add_default_ops()
 for side,rig in [(S,ik),(T,tgt)]:r.assign_ik_rig_to_all_ops(side,rig)
 i=r.get_index_of_op_by_name('Run IK Rig')
 if i>=0:r.set_retarget_op_enabled(i,False)
 r.auto_map_chains(u.AutoMapChainType.EXACT,True)
 report['mapping']={n:str(r.get_source_chain(n)) for n,_,_ in chains}
 for n in ['Spine','LeftLeg','RightLeg','LeftArm','RightArm','RightIndex']:assert report['mapping'].get(n) not in [None,'','None'],n
 pose=r.create_retarget_pose('AlignedToAurora',T);r.set_current_retarget_pose(pose,T);r.auto_align_all_bones(T)
 pelvis=r.get_op_controller(r.get_index_of_op_by_name('Pelvis Motion'));root=r.get_op_controller(r.get_index_of_op_by_name('Root Motion'))
 pelvis.set_source_pelvis_bone('pelvis');pelvis.set_target_pelvis_bone('pelvis')
 root.set_source_root_bone('root');root.set_target_root_bone('root');root.set_target_pelvis_bone('pelvis')
 report['ops']=[(str(r.get_op_name(i)),r.get_retarget_op_enabled(i)) for i in range(r.get_num_retarget_ops())]
 for a in (ik,rtg):save(a)
 assets=[];report['missing']=[]
 for n in CLIPS:
  d=LIB.find_asset_data(SRC+'Animations/'+n)
  if d.is_valid() and isinstance(d.get_asset(),u.AnimSequence):assets.append(d)
  else:report['missing'].append(n)
 inp=u.IKRetargetBatchOperationInputs()
 for k,v in dict(assets_to_retarget=assets,source_mesh=src,target_mesh=mesh,ik_retarget_asset=rtg,target_path=BASE+'/Anims/Aurora',suffix='_Warrior',include_referenced_assets=False,overwrite_existing_files=False,use_source_path=False).items():inp.set_editor_property(k,v)
 made=u.IKRetargetBatchOperation.run_batch_retarget(inp);report['clips']={}
 for d in made:
  a=d.get_asset()
  if isinstance(a,u.AnimSequence):
   a.set_editor_property('enable_root_motion',False);a.set_editor_property('force_root_lock',True);a.set_editor_property('root_motion_root_lock',u.RootMotionRootLock.REF_POSE)
   save(a);report['clips'][str(d.asset_name)]={'path':a.get_path_name(),'seconds':a.get_play_length()}
 checkpoint()
 # jog stance speed, same method as warrior_measure
 a=u.load_asset(BASE+'/Anims/Aurora/Jog_Fwd_Warrior');opts=u.AnimPoseEvaluationOptions()
 for k,v in dict(evaluation_type=u.AnimDataEvalType.RAW,should_retarget=True,extract_root_motion=False,incorporate_root_motion_into_pose=True,optional_skeletal_mesh=mesh,evaluate_curves=False).items():opts.set_editor_property(k,v)
 L=a.get_play_length();times=[min(i/60,L) for i in range(math.ceil(L*60)+1)];cand=[];rows=[]
 for t in times:
  p=u.AnimPoseExtensions.get_anim_pose_at_time(a,t,opts)
  rows.append({b:u.AnimPoseExtensions.get_bone_pose(p,b,u.AnimPoseSpaces.WORLD).translation for b in ['ball_l','ball_r','root','pelvis','hand_r','hand_l']})
 for b in ['ball_l','ball_r']:
  xyz=[[r_[b].x,r_[b].y,r_[b].z] for r_ in rows];h=sorted(p[2] for p in xyz)[int((len(xyz)-1)*.35)]
  for i in range(1,len(rows)-1):
   dt=times[i+1]-times[i-1];v=[(xyz[i+1][k]-xyz[i-1][k])/dt for k in range(3)]
   if xyz[i][2]<=h and abs(v[2])<25:cand.append(v)
 report['jog']={'seconds':L,'stance_velocity_median':[statistics.median(c[k] for c in cand) for k in range(3)] if cand else None,'n':len(cand),
  'pelvis_range':[[min(getattr(r_['pelvis'],k) for r_ in rows),max(getattr(r_['pelvis'],k) for r_ in rows)] for k in 'xyz']}
 report['status']='success'
try:main()
except Exception:report.update(status='failed',error=traceback.format_exc())
checkpoint()
if report['status']!='success':raise RuntimeError(report['error'])
