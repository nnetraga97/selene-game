"""Fox-only GASP batch, centered transition copies, in-place loops, and toon MI."""
import hashlib, json, math, os, traceback
from pathlib import Path
import unreal as u
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
OUT=Path(os.environ['SELENE_STAGE_REPORT']); BASE='/Game/Selene/Characters/Fox'
LIB=u.EditorAssetLibrary; TOOLS=u.AssetToolsHelpers.get_asset_tools(); BONE='mixamorig_Hips'
report={'status':'running','clips':[],'transitions':[]}
def checkpoint(): OUT.write_text(json.dumps(report,indent=2)+'\n')
def keys(anim):
 opts=u.AnimPoseEvaluationOptions()
 for k,v in dict(evaluation_type=u.AnimDataEvalType.RAW,incorporate_root_motion_into_pose=True,evaluate_curves=False).items():opts.set_editor_property(k,v)
 frames=anim.get_editor_property('data_model_interface').get_number_of_frames();length=anim.get_play_length()
 u.AnimPoseExtensions.get_anim_pose_at_time(anim,0,opts)
 return [u.AnimPoseExtensions.get_bone_pose(u.AnimPoseExtensions.get_anim_pose_at_time(anim,length*f/frames,opts),BONE,u.AnimPoseSpaces.LOCAL) for f in range(frames+1)]
def setkeys(anim,ks,positions):
 c=anim.get_editor_property('controller');c.open_bracket('Fox hips normalization',False)
 try:
  if not c.set_bone_track_keys(BONE,positions,[k.rotation for k in ks],[k.scale3d for k in ks],False):raise RuntimeError('Set keys failed')
 finally:c.close_bracket(False)
def save(a):
 if not LIB.save_loaded_asset(a,only_if_is_dirty=False):raise RuntimeError('Save failed '+a.get_path_name())
def main():
 if LIB.does_directory_exist(BASE+'/Anims/GASP'):raise RuntimeError('Existing outputs; no replay')
 verified=json.loads((ROOT/'Saved/Clips/session-3/reload-dependencies.json').read_text())
 assert verified['status']=='success' and len(verified['clips'])==15
 src=u.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple');mesh=u.load_asset(os.environ['SELENE_CHAR_MESH']);rtg=u.load_asset(BASE+'/RTG_Manny_To_Fox')
 assets=[]
 for clip in verified['clips']:
  if hashlib.sha256((ROOT/clip['file']).read_bytes()).hexdigest()!=clip['sha256']:raise RuntimeError('Source changed')
  assets.append(LIB.find_asset_data(clip['package']))
 inputs=u.IKRetargetBatchOperationInputs()
 for k,v in dict(assets_to_retarget=assets,source_mesh=src,target_mesh=mesh,ik_retarget_asset=rtg,target_path=BASE+'/Anims/GASP',suffix='_Fox',include_referenced_assets=False,overwrite_existing_files=False,use_source_path=False).items():inputs.set_editor_property(k,v)
 made=u.IKRetargetBatchOperation.run_batch_retarget(inputs)
 if len(made)!=15:raise RuntimeError('Expected 15 clips')
 byname={str(d.asset_name):d.get_asset() for d in made}
 for clip in verified['clips']:
  a=byname[clip['package'].rsplit('/',1)[-1]+'_Fox'];role=clip['role']
  if a.get_editor_property('skeleton')!=mesh.get_editor_property('skeleton'):raise RuntimeError('Wrong skeleton')
  a.set_editor_property('enable_root_motion',False);a.set_editor_property('force_root_lock',True);a.set_editor_property('root_motion_root_lock',u.RootMotionRootLock.ANIM_FIRST_FRAME)
  row={'role':role,'asset':a.get_path_name(),'seconds':a.get_play_length()}
  if role in ('WalkLoop','RunLoop','SprintLoop'):
   ks=keys(a);dx=ks[-1].translation.x-ks[0].translation.x;dy=ks[-1].translation.y-ks[0].translation.y;n=len(ks)-1
   setkeys(a,ks,[u.Vector(k.translation.x-dx*i/n,k.translation.y-dy*i/n,k.translation.z) for i,k in enumerate(ks)])
   a.set_editor_property('force_root_lock',False);row.update(speed_cm_s=math.hypot(dx,dy)/a.get_play_length(),removed_travel_xy_cm=[dx,dy])
  save(a);report['clips'].append(row);checkpoint()
  if role not in ('Idle','WalkLoop','RunLoop','SprintLoop'):
   c=TOOLS.duplicate_asset(a.get_name()+'_Centred',BASE+'/Anims/Centred',a);ks=keys(c);x,y=ks[0].translation.x,ks[0].translation.y
   setkeys(c,ks,[u.Vector(k.translation.x-x,k.translation.y-y,k.translation.z) for k in ks]);save(c)
   report['transitions'].append({'role':role,'source':a.get_path_name(),'asset':c.get_path_name(),'removed_xy_cm':[x,y]});checkpoint()
 parent=u.load_asset('/Game/Selene/Materials/Character/M_Character_Toon');tex=u.load_asset('/Game/Assets/fox-spirit-sovereign/fox-spirit-sovereign/Textures/kitsune_fantasy_character_3d_model_basecolor')
 dest='/Game/Selene/Materials/Character/MI_Toon_Fox'
 if LIB.does_asset_exist(dest):raise RuntimeError('Material exists; no replay')
 mi=TOOLS.create_asset('MI_Toon_Fox','/Game/Selene/Materials/Character',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew());mel=u.MaterialEditingLibrary
 mel.set_material_instance_parent(mi,parent);mel.set_material_instance_texture_parameter_value(mi,'BaseColorTex',tex);mel.update_material_instance(mi)
 got=mel.get_material_instance_texture_parameter_value(mi,'BaseColorTex')
 if got!=tex or mi.get_editor_property('parent')!=parent:raise RuntimeError('Material readback mismatch')
 save(mi);report['material']={'asset':mi.get_path_name(),'parent':parent.get_path_name(),'texture_readback':got.get_path_name()}
 report['status']='success'
try:main()
except Exception:report.update(status='failed',error=traceback.format_exc())
finally:checkpoint()
if report['status']!='success':raise RuntimeError(report['error'])
