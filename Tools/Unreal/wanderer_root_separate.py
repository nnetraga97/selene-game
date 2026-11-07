"""One diagnosed fix: separate UE5 pelvis motion from the real root; preserve previous clips."""
import json,os,traceback
from pathlib import Path
import unreal as u
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));OUT=Path(os.environ['SELENE_STAGE_REPORT']);BASE='/Game/Selene/Characters/Wanderer'
LIB=u.EditorAssetLibrary;report={'status':'running','diagnosis':'IK root=root implicitly assigned target pelvis=root in both motion operators; map target pelvis explicitly to pelvis.','facing_correction_degrees':0}
def checkpoint():OUT.write_text(json.dumps(report,indent=2)+'\n')
def main():
 assert not LIB.does_directory_exist(BASE+'/RootSeparated')
 src=u.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple');mesh=u.load_asset('/Game/Assets/teal-wanderer/teal-wanderer/SkeletalMeshes/teal-wanderer')
 rtg=u.load_asset(BASE+'/RTG_Manny_To_Wanderer');r=u.IKRetargeterController.get_controller(rtg);T=u.RetargetSourceOrTarget.TARGET
 pelvis=r.get_op_controller(r.get_index_of_op_by_name('Pelvis Motion'));root=r.get_op_controller(r.get_index_of_op_by_name('Root Motion'))
 pelvis.set_source_pelvis_bone('pelvis');pelvis.set_target_pelvis_bone('pelvis')
 root.set_source_root_bone('root');root.set_target_root_bone('root');root.set_target_pelvis_bone('pelvis')
 report['motion_bones']={'pelvis_source':str(pelvis.get_source_pelvis_bone()),'pelvis_target':str(pelvis.get_target_pelvis_bone()),'root_source':str(root.get_source_root_bone()),'root_target':str(root.get_target_root_bone()),'root_op_pelvis':str(root.get_target_pelvis_bone())}
 assert report['motion_bones']=={'pelvis_source':'pelvis','pelvis_target':'pelvis','root_source':'root','root_target':'root','root_op_pelvis':'pelvis'}
 assert LIB.save_loaded_asset(rtg,only_if_is_dirty=False)
 def batch(assets,path,refs):
  inp=u.IKRetargetBatchOperationInputs()
  for k,v in dict(assets_to_retarget=assets,source_mesh=src,target_mesh=mesh,ik_retarget_asset=rtg,target_path=path,suffix='_Wanderer',include_referenced_assets=refs,overwrite_existing_files=False,use_source_path=False).items():inp.set_editor_property(k,v)
  made=u.IKRetargetBatchOperation.run_batch_retarget(inp)
  for d in made:assert LIB.save_loaded_asset(d.get_asset(),only_if_is_dirty=False)
  return made
 made=batch([LIB.find_asset_data('/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed')],BASE+'/RootSeparated/Anims',True)
 report['template_assets']=[str(d.package_name) for d in made];checkpoint()
 sources=json.loads((ROOT/'Saved/Clips/session-3/reload-dependencies.json').read_text())['clips']
 made=batch([LIB.find_asset_data(c['package']) for c in sources],BASE+'/RootSeparated/Anims/GASP',False);assert len(made)==15
 byname={str(d.asset_name):d.get_asset() for d in made}
 report['clips']=[{'role':c['role'],'asset':byname[c['package'].rsplit('/',1)[-1]+'_Wanderer'].get_path_name()} for c in sources]
 original=json.loads((ROOT/'Saved/WandererHookup/session-1/retarget/report.json').read_text())
 for k in ['hierarchy','slots']:report[k]=original[k]
 report['status']='success'
try:main()
except Exception:report.update(status='failed',error=traceback.format_exc())
finally:checkpoint()
if report['status']!='success':raise RuntimeError(report['error'])
