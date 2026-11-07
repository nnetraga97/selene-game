"""Read-only retarget operator and root rotation audit; distinguish root-lock success from mapping artifacts."""
import json,os,traceback
from pathlib import Path
import unreal as u
out=Path(os.environ['SELENE_STAGE_REPORT']);report={'status':'running','ops':[]}
try:
 r=u.IKRetargeterController.get_controller(u.load_asset('/Game/Selene/Characters/Wanderer/RTG_Manny_To_Wanderer'))
 for i in range(r.get_num_retarget_ops()):
  c=r.get_op_controller(i);row={'name':str(r.get_op_name(i)),'class':str(type(c))}
  if row['name'] in ['Pelvis Motion','Root Motion']:
   row['methods']={n:str(getattr(c,n).__doc__) for n in dir(c) if any(s in n for s in ['pelvis','root','settings'])}
   for n in dir(c):
    if n.startswith('get_') and any(s in n for s in ['pelvis','root','settings']):
     try:row[n]=str(getattr(c,n)())
     except Exception as e:row[n]=str(e)
  report['ops'].append(row)
 report['rig_retarget_root']=str(u.IKRigController.get_controller(u.load_asset('/Game/Selene/Characters/Wanderer/IK_Wanderer')).get_retarget_root())
 assert report['rig_retarget_root']=='root'
 report['rotations']={}
 for name,path in [('target','/Game/Selene/Characters/Wanderer/RootSeparated/Anims/GASP/M_Neutral_Run_Loop_F_Wanderer'),('source','/Game/Selene/Animation/GASP/M_Neutral_Run_Loop_F')]:
  a=u.load_asset(path);opts=u.AnimPoseEvaluationOptions();opts.set_editor_property('incorporate_root_motion_into_pose',True)
  rows=[]
  for t in [0,.1,.2,.3,.4]:
   p=u.AnimPoseExtensions.get_anim_pose_at_time(a,t,opts);row={'time':t}
   for b in ['root','pelvis']:
    tr=u.AnimPoseExtensions.get_bone_pose(p,b,u.AnimPoseSpaces.LOCAL);q=tr.rotation;v=tr.translation
    row[b]={'rotation':[q.x,q.y,q.z,q.w],'translation':[v.x,v.y,v.z]}
   rows.append(row)
  report['rotations'][name]=rows
 mesh=u.load_asset('/Game/Selene/Characters/Wanderer/SK_Wanderer');original=u.load_asset('/Game/Assets/teal-wanderer/teal-wanderer/SkeletalMeshes/teal-wanderer')
 comp=u.SkeletalMeshComponent();comp.set_skeletal_mesh_asset(mesh)
 eye=mesh.get_editor_property('materials')[1].material_interface;parent=eye.get_editor_property('parent')
 report['fresh_eye_readback']={'skeleton_unchanged':mesh.get_editor_property('skeleton')==original.get_editor_property('skeleton'),'bones':comp.get_num_bones(),'slot':str(mesh.get_editor_property('materials')[1].material_slot_name),'material':eye.get_path_name(),'skeletal_usage':parent.get_editor_property('used_with_skeletal_mesh'),'texture':u.MaterialEditingLibrary.get_material_instance_texture_parameter_value(eye,'BaseColorTexture').get_path_name()}
 assert report['fresh_eye_readback']['skeleton_unchanged'] and report['fresh_eye_readback']['skeletal_usage']
 report['status']='success' 
except Exception:report.update(status='failed',error=traceback.format_exc())
out.write_text(json.dumps(report,indent=2)+'\n')
