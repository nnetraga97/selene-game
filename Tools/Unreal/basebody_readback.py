"""Read-only retarget operator and root rotation audit; distinguish root-lock success from mapping artifacts."""
import json,os,traceback
from pathlib import Path
import unreal as u
out=Path(os.environ['SELENE_STAGE_REPORT']);report={'status':'running','ops':[]}
try:
 r=u.IKRetargeterController.get_controller(u.load_asset('/Game/Selene/Characters/Base/RTG_Manny_To_Base'))
 for i in range(r.get_num_retarget_ops()):
  c=r.get_op_controller(i);row={'name':str(r.get_op_name(i)),'class':str(type(c))}
  if row['name'] in ['Pelvis Motion','Root Motion']:
   row['methods']={n:str(getattr(c,n).__doc__) for n in dir(c) if any(s in n for s in ['pelvis','root','settings'])}
   for n in dir(c):
    if n.startswith('get_') and any(s in n for s in ['pelvis','root','settings']):
     try:row[n]=str(getattr(c,n)())
     except Exception as e:row[n]=str(e)
  report['ops'].append(row)
 report['rig_retarget_root']=str(u.IKRigController.get_controller(u.load_asset('/Game/Selene/Characters/Base/IK_Base')).get_retarget_root())
 assert report['rig_retarget_root']=='root'
 report['rotations']={}
 for name,path in [('target','/Game/Selene/Characters/Base/Anims/GASP/M_Neutral_Run_Loop_F_Base'),('source','/Game/Selene/Animation/GASP/M_Neutral_Run_Loop_F')]:
  a=u.load_asset(path);opts=u.AnimPoseEvaluationOptions();opts.set_editor_property('incorporate_root_motion_into_pose',True)
  rows=[]
  for t in [0,.1,.2,.3,.4]:
   p=u.AnimPoseExtensions.get_anim_pose_at_time(a,t,opts);row={'time':t}
   for b in ['root','pelvis']:
    tr=u.AnimPoseExtensions.get_bone_pose(p,b,u.AnimPoseSpaces.LOCAL);q=tr.rotation;v=tr.translation
    row[b]={'rotation':[q.x,q.y,q.z,q.w],'translation':[v.x,v.y,v.z]}
   rows.append(row)
  report['rotations'][name]=rows
 mesh=u.load_asset('/Game/Assets/base-female-v2/base-female-v2/SkeletalMeshes/base-female-v2')
 comp=u.SkeletalMeshComponent();comp.set_skeletal_mesh_asset(mesh)
 report['mesh']={'asset':mesh.get_path_name(),'skeleton':mesh.get_editor_property('skeleton').get_path_name(),'bones':comp.get_num_bones()}
 registry=u.AssetRegistryHelpers.get_asset_registry()
 imported=registry.get_assets_by_path('/Game/Assets/base-female-v2',recursive=True)
 report['imported_skeletal_meshes']=[str(d.object_path) if hasattr(d,'object_path') else str(d.package_name) for d in imported if str(d.asset_class_path.asset_name)=='SkeletalMesh']
 assert len(report['imported_skeletal_meshes'])==1
 owned=registry.get_assets_by_path('/Game/Selene/Characters/Base',recursive=True)
 assert not any(str(d.asset_class_path.asset_name)=='SkeletalMesh' for d in owned)
 report['duplicate_mesh']=False;report['materials']=[]
 for suffix in ['Body']:
  mi=u.load_asset('/Game/Selene/Materials/Character/MI_Toon_Base_'+suffix);parent=mi.get_editor_property('parent')
  row={'instance':mi.get_path_name(),'parent':parent.get_path_name(),'two_sided':parent.get_editor_property('two_sided'),'skeletal_usage':parent.get_editor_property('used_with_skeletal_mesh'),'texture':u.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mi,'BaseColorTex').get_path_name()}
  assert row['skeletal_usage']
  if suffix in ('Jacket','Skirt'):assert row['two_sided'] and parent.get_name()=='M_Character_Toon_TwoSided'
  report['materials'].append(row)
 report['status']='success' 
except Exception:report.update(status='failed',error=traceback.format_exc())
out.write_text(json.dumps(report,indent=2)+'\n')

if report['status']!='success':raise RuntimeError(report['error'])
