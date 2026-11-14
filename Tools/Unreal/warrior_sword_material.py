"""Warrior sword slot: toon instance for the new Warrior_Sword slot and a skeleton/anim readback after the re-import."""
import json,os,traceback
from pathlib import Path
import unreal as u
OUT=Path(os.environ['SELENE_STAGE_REPORT']);report={'status':'running'}
LIB=u.EditorAssetLibrary;TOOLS=u.AssetToolsHelpers.get_asset_tools();mel=u.MaterialEditingLibrary
def main():
 mesh=u.load_asset('/Game/Assets/eclipse-warrior/eclipse-warrior/SkeletalMeshes/eclipse-warrior')
 comp=u.SkeletalMeshComponent();comp.set_skeletal_mesh_asset(mesh)
 bones=[str(comp.get_bone_name(i)) for i in range(comp.get_num_bones())];report['bones']=len(bones);assert 'weapon_r' in bones
 report['slots']=[{'slot':str(m.material_slot_name),'material':m.material_interface.get_path_name()} for m in mesh.get_editor_property('materials')]
 original=next(m.material_interface for m in mesh.get_editor_property('materials') if str(m.material_slot_name)=='Warrior_Sword')
 tex=mel.get_material_instance_texture_parameter_value(original,'BaseColorTexture');assert tex
 path='/Game/Selene/Materials/Character/MI_Toon_Warrior_Sword'
 if not LIB.does_asset_exist(path):
  mi=TOOLS.create_asset('MI_Toon_Warrior_Sword','/Game/Selene/Materials/Character',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
  mel.set_material_instance_parent(mi,u.load_asset('/Game/Selene/Materials/Character/M_Character_Toon'));mel.set_material_instance_texture_parameter_value(mi,'BaseColorTex',tex);mel.update_material_instance(mi)
  assert LIB.save_loaded_asset(mi,only_if_is_dirty=False)
 report['sword_material']=path
 a=u.load_asset('/Game/Selene/Characters/Warrior/Anims/GASP/M_Neutral_Run_Loop_F_Warrior');report['anim_skeleton']=a.get_skeleton().get_path_name();report['mesh_skeleton']=mesh.skeleton.get_path_name()
 assert report['anim_skeleton']==report['mesh_skeleton']
 report['status']='success'
try:main()
except Exception:report.update(status='failed',error=traceback.format_exc())
OUT.write_text(json.dumps(report,indent=2)+'\n')
if report['status']!='success':raise RuntimeError(report['error'])
