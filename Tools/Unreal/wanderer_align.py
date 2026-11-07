"""One diagnosed fix: align target bind directions to Manny; retain original clips for comparison."""
import json,os,traceback
from pathlib import Path
import unreal as u
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));OUT=Path(os.environ['SELENE_STAGE_REPORT']);BASE='/Game/Selene/Characters/Wanderer'
LIB=u.EditorAssetLibrary;report={'status':'running','diagnosis':'Wanderer binds arms near body and asymmetrically; Manny arms point farther outward. Default retarget pose carried that mismatch into locomotion.','facing_correction_degrees':0}
def checkpoint():OUT.write_text(json.dumps(report,indent=2)+'\n')
def main():
 assert not LIB.does_directory_exist(BASE+'/Aligned')
 src=u.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple');mesh=u.load_asset('/Game/Assets/teal-wanderer/teal-wanderer/SkeletalMeshes/teal-wanderer')
 rtg=u.load_asset(BASE+'/RTG_Manny_To_Wanderer');r=u.IKRetargeterController.get_controller(rtg);T=u.RetargetSourceOrTarget.TARGET
 pose=r.create_retarget_pose('AlignedToManny',T);r.set_current_retarget_pose(pose,T);r.auto_align_all_bones(T)
 assert LIB.save_loaded_asset(rtg,only_if_is_dirty=False)
 def batch(assets,path,refs):
  inp=u.IKRetargetBatchOperationInputs()
  for k,v in dict(assets_to_retarget=assets,source_mesh=src,target_mesh=mesh,ik_retarget_asset=rtg,target_path=path,suffix='_Wanderer',include_referenced_assets=refs,overwrite_existing_files=False,use_source_path=False).items():inp.set_editor_property(k,v)
  made=u.IKRetargetBatchOperation.run_batch_retarget(inp)
  for d in made:assert LIB.save_loaded_asset(d.get_asset(),only_if_is_dirty=False)
  return made
 made=batch([LIB.find_asset_data('/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed')],BASE+'/Aligned/Anims',True)
 report['template_assets']=[str(d.package_name) for d in made];checkpoint()
 sources=json.loads((ROOT/'Saved/Clips/session-3/reload-dependencies.json').read_text())['clips']
 made=batch([LIB.find_asset_data(c['package']) for c in sources],BASE+'/Aligned/Anims/GASP',False);assert len(made)==15
 byname={str(d.asset_name):d.get_asset() for d in made}
 report['clips']=[{'role':c['role'],'asset':byname[c['package'].rsplit('/',1)[-1]+'_Wanderer'].get_path_name()} for c in sources]
 original=json.loads((ROOT/'Saved/WandererHookup/session-1/retarget/report.json').read_text())
 for k in ['hierarchy','slots']:report[k]=original[k]
 report['status']='success'
try:main()
except Exception:report.update(status='failed',error=traceback.format_exc())
finally:checkpoint()
if report['status']!='success':raise RuntimeError(report['error'])
