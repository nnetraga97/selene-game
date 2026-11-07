"""One diagnosed fix for grey eye-card fallback: Wanderer-owned mesh and skeletal-compatible eye material copies.
Imported mesh/materials are read only. Animation skeleton and eye slot name stay unchanged.
"""
import json,os,traceback
from pathlib import Path
import unreal as u
OUT=Path(os.environ['SELENE_STAGE_REPORT']);LIB=u.EditorAssetLibrary;TOOLS=u.AssetToolsHelpers.get_asset_tools();MEL=u.MaterialEditingLibrary
BASE='/Game/Selene/Characters/Wanderer';report={'status':'running','diagnosis':'Runtime keeps FoxEye_amber but cards render grey; engine logs missing SkeletalMesh usage on imported eye material.','copies':[]}
def checkpoint():OUT.write_text(json.dumps(report,indent=2)+'\n')
def save(a):
 assert a.get_path_name().startswith(BASE+'/')
 assert LIB.save_loaded_asset(a,only_if_is_dirty=False)
def copy_parent(a,depth=0):
 name='M_Wanderer_Eyes' if isinstance(a,u.Material) else 'MI_Wanderer_Eyes_Parent'+str(depth)
 assert not LIB.does_asset_exist(BASE+'/Materials/'+name)
 copied=TOOLS.duplicate_asset(name,BASE+'/Materials',a)
 report['copies'].append({'source':a.get_path_name(),'copy':copied.get_path_name()})
 if isinstance(a,u.Material):
  report['source_used_with_skeletal_mesh']=a.get_editor_property('used_with_skeletal_mesh')
  copied.set_editor_property('used_with_skeletal_mesh',True);MEL.recompile_material(copied)
  assert copied.get_editor_property('used_with_skeletal_mesh')
 else:
  MEL.set_material_instance_parent(copied,copy_parent(a.get_editor_property('parent'),depth+1));MEL.update_material_instance(copied)
 save(copied);return copied
try:
 mesh=u.load_asset('/Game/Assets/teal-wanderer/teal-wanderer/SkeletalMeshes/teal-wanderer');slots=mesh.get_editor_property('materials');eye=slots[1].material_interface
 report['source_slot']=str(slots[1].material_slot_name);assert report['source_slot']=='FoxEye_amber'
 assert not LIB.does_asset_exist(BASE+'/Materials/FoxEye_amber') and not LIB.does_asset_exist(BASE+'/SK_Wanderer')
 parent=copy_parent(eye.get_editor_property('parent'))
 copied=TOOLS.duplicate_asset('FoxEye_amber',BASE+'/Materials',eye);MEL.set_material_instance_parent(copied,parent);MEL.update_material_instance(copied);save(copied)
 report['eye_material']=copied.get_path_name();report['texture_parameters']={str(n):str(MEL.get_material_instance_texture_parameter_value(copied,n).get_path_name()) for n in MEL.get_texture_parameter_names(parent) if MEL.get_material_instance_texture_parameter_value(copied,n)}
 dup=TOOLS.duplicate_asset('SK_Wanderer',BASE,mesh)
 newslots=dup.get_editor_property('materials');slot=newslots[1];slot.material_interface=copied;newslots[1]=slot;dup.set_editor_property('materials',newslots)
 assert dup.get_editor_property('skeleton')==mesh.get_editor_property('skeleton');save(dup)
 report['mesh']=dup.get_path_name();report['skeleton']=dup.get_editor_property('skeleton').get_path_name();report['status']='success'
except Exception:report.update(status='failed',error=traceback.format_exc())
finally:checkpoint()
if report['status']!='success':raise RuntimeError(report['error'])
