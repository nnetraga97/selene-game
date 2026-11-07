"""Wanderer only: UE5-named rig and template/GASP retarget with a real root; no Mixamo corrections."""
import hashlib,json,os,traceback
from pathlib import Path
import unreal as u
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));OUT=Path(os.environ['SELENE_STAGE_REPORT'])
BASE='/Game/Selene/Characters/Wanderer';MESH='/Game/Assets/teal-wanderer/teal-wanderer/SkeletalMeshes/teal-wanderer'
LIB=u.EditorAssetLibrary;TOOLS=u.AssetToolsHelpers.get_asset_tools();report={'status':'running'}
def checkpoint():OUT.write_text(json.dumps(report,indent=2)+'\n')
def save(a):
 if not LIB.save_loaded_asset(a,only_if_is_dirty=False):raise RuntimeError('Save failed '+a.get_path_name())
def create(n,cls,factory):
 if LIB.does_asset_exist(BASE+'/'+n):raise RuntimeError('No replay '+n)
 return TOOLS.create_asset(n,BASE,cls,factory)
def main():
 if LIB.does_directory_exist(BASE):raise RuntimeError('Output exists; reconcile before replay')
 src=u.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple');mesh=u.load_asset(MESH)
 comp=u.SkeletalMeshComponent();comp.set_skeletal_mesh_asset(mesh)
 bones=[str(comp.get_bone_name(i)) for i in range(comp.get_num_bones())]
 report['hierarchy']=[{'name':n,'parent':str(comp.get_parent_bone(n))} for n in bones]
 report['slots']=[{'slot':str(m.material_slot_name),'material':m.material_interface.get_path_name()} for m in mesh.get_editor_property('materials')]
 source=create('IK_Manny',u.IKRigDefinition,u.IKRigDefinitionFactory());sc=u.IKRigController.get_controller(source);sc.set_skeletal_mesh(src)
 assert sc.apply_auto_generated_retarget_definition();sc.apply_auto_fbik()
 target=create('IK_Wanderer',u.IKRigDefinition,u.IKRigDefinitionFactory());tc=u.IKRigController.get_controller(target);tc.set_skeletal_mesh(mesh)
 auto=tc.apply_auto_generated_retarget_definition();report['target_auto_template']=auto
 if not auto:
  for chain in sc.get_retarget_chains():
   n=chain.chain_name;start=str(sc.get_retarget_chain_start_bone(n));end=str(sc.get_retarget_chain_end_bone(n))
   if start in bones and end in bones:tc.add_retarget_chain(n,start,end,'')
 tc.set_retarget_root('root');assert str(tc.get_retarget_root())=='root'
 report['chains']=[(str(c.chain_name),str(tc.get_retarget_chain_start_bone(c.chain_name)),str(tc.get_retarget_chain_end_bone(c.chain_name))) for c in tc.get_retarget_chains()]
 rtg=create('RTG_Manny_To_Wanderer',u.IKRetargeter,u.IKRetargetFactory());r=u.IKRetargeterController.get_controller(rtg)
 S,T=u.RetargetSourceOrTarget.SOURCE,u.RetargetSourceOrTarget.TARGET
 for side,rig,m in [(S,source,src),(T,target,mesh)]:r.set_ik_rig(side,rig);r.set_preview_mesh(side,m)
 r.remove_all_ops();r.add_default_ops()
 for side,rig in [(S,source),(T,target)]:r.assign_ik_rig_to_all_ops(side,rig)
 r.auto_map_chains(u.AutoMapChainType.FUZZY,True)
 report['mapping']={ch[0]:str(r.get_source_chain(ch[0])) for ch in report['chains']}
 for n in ['Spine','LeftLeg','RightLeg','LeftArm','RightArm']:assert report['mapping'].get(n) not in [None,'','None']
 report['ops']=[(str(r.get_op_name(i)),r.get_retarget_op_enabled(i)) for i in range(r.get_num_retarget_ops())]
 report['target_retarget_root']=str(tc.get_retarget_root());report['facing_correction_degrees']=0
 for a in [source,target,rtg]:save(a)
 def batch(assets,path):
  inp=u.IKRetargetBatchOperationInputs()
  for k,v in dict(assets_to_retarget=assets,source_mesh=src,target_mesh=mesh,ik_retarget_asset=rtg,target_path=path,suffix='_Wanderer',include_referenced_assets=path.endswith('/Anims'),overwrite_existing_files=False,use_source_path=False).items():inp.set_editor_property(k,v)
  made=u.IKRetargetBatchOperation.run_batch_retarget(inp)
  for d in made:save(d.get_asset())
  return made
 made=batch([LIB.find_asset_data('/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed')],BASE+'/Anims')
 report['template_assets']=[str(d.package_name) for d in made];checkpoint()
 verified=json.loads((ROOT/'Saved/Clips/session-3/reload-dependencies.json').read_text());assert verified['status']=='success' and len(verified['clips'])==15
 for c in verified['clips']:assert hashlib.sha256((ROOT/c['file']).read_bytes()).hexdigest()==c['sha256']
 made=batch([LIB.find_asset_data(c['package']) for c in verified['clips']],BASE+'/Anims/GASP');assert len(made)==15
 byname={str(d.asset_name):d.get_asset() for d in made}
 report['clips']=[{'role':c['role'],'asset':byname[c['package'].rsplit('/',1)[-1]+'_Wanderer'].get_path_name()} for c in verified['clips']]
 parent=u.load_asset('/Game/Selene/Materials/Character/M_Character_Toon');tex=u.load_asset('/Game/Assets/teal-wanderer/teal-wanderer/Textures/fantasy_female_character_3d_model_Clone1_basecolor')
 assert not LIB.does_asset_exist('/Game/Selene/Materials/Character/MI_Toon_Wanderer')
 mi=TOOLS.create_asset('MI_Toon_Wanderer','/Game/Selene/Materials/Character',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew());mel=u.MaterialEditingLibrary
 mel.set_material_instance_parent(mi,parent);mel.set_material_instance_texture_parameter_value(mi,'BaseColorTex',tex);mel.update_material_instance(mi)
 got=mel.get_material_instance_texture_parameter_value(mi,'BaseColorTex');assert got==tex and mi.get_editor_property('parent')==parent
 save(mi);report['material']={'asset':mi.get_path_name(),'parent':parent.get_path_name(),'texture_readback':got.get_path_name()}
 report['status']='success'
try:main()
except Exception:report.update(status='failed',error=traceback.format_exc())
finally:checkpoint()
if report['status']!='success':raise RuntimeError(report['error'])
