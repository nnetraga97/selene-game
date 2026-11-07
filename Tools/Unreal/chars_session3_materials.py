"""Create two toon instances and relink only the new heroes' imported materials."""
import json
from pathlib import Path
import traceback
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
OUT = ROOT/'Saved/Chars/session-3'
LIB, MEL = u.EditorAssetLibrary, u.MaterialEditingLibrary
TOOLS = u.AssetToolsHelpers.get_asset_tools()
HEROES = {'Fixer': ('night-market-fixer', 'female_action_figure_3d_model_basecolor'),
          'Courier': ('scooter-courier', 'stylized_character_3d_model_basecolor')}
COPY_ROOT = '/Game/Selene/Materials/Imported/CharsSession3'
report = dict(status='running', heroes={}, copied={}, saved=[], usage=[])
copies = {}
def checkpoint():
    (OUT/'materials.json').write_text(json.dumps(report,indent=2)+'\n')
def save(a):
    p=a.get_path_name()
    if not any(p.startswith(x) for x in ['/Game/Selene/Materials/', '/Game/Assets/night-market-fixer/', '/Game/Assets/scooter-courier/']):
        raise RuntimeError('Out-of-scope save: '+p)
    if not LIB.save_loaded_asset(a,only_if_is_dirty=False): raise RuntimeError('Save failed: '+p)
    report['saved'].append(p)
def usage(mat):
    flags=['used_with_skeletal_mesh','used_with_nanite']
    changed=[f for f in flags if not mat.get_editor_property(f)]
    if changed:
        if not mat.get_path_name().startswith('/Game/Selene/'): raise RuntimeError('External base cannot be edited')
        for f in changed: mat.set_editor_property(f,True)
        MEL.recompile_material(mat)
        save(mat)
    report['usage'].append(dict(material=mat.get_path_name(), changed=changed,
                               flags={f:mat.get_editor_property(f) for f in flags}))
def local_copy(obj):
    path=obj.get_path_name()
    if path in copies: return copies[path]
    name=obj.get_name(); dest=COPY_ROOT+'/'+name
    if LIB.does_asset_exist(dest): raise RuntimeError('Existing copy; do not replay: '+dest)
    copy=TOOLS.duplicate_asset(name,COPY_ROOT,obj)
    if not copy: raise RuntimeError('Duplicate failed: '+path)
    copies[path]=copy
    if isinstance(copy,u.MaterialInstanceConstant):
        parent=obj.get_editor_property('parent')
        if parent: MEL.set_material_instance_parent(copy,local_copy(parent))
        MEL.update_material_instance(copy)
    else: usage(copy)
    save(copy)
    report['copied'][path]=copy.get_path_name()
    return copy
try:
    if (OUT/'materials.json').exists(): raise RuntimeError('Existing report; do not replay')
    parent=u.load_asset('/Game/Selene/Materials/Character/M_Character_Toon')
    if not parent or not u.SystemLibrary.get_console_variable_bool_value('r.Substrate'):
        raise RuntimeError('Existing toon parent/Substrate unavailable')
    usage(parent)
    for name,(slug,texture_name) in HEROES.items():
        folder='/Game/Assets/'+slug+'/'+slug
        tex=u.load_asset(folder+'/Textures/'+texture_name)
        mesh=u.load_asset(folder+'/SkeletalMeshes/'+slug)
        if not tex or not mesh: raise RuntimeError('Missing imported mesh/texture: '+name)
        dest='/Game/Selene/Materials/Character/MI_Toon_'+name
        if LIB.does_asset_exist(dest): raise RuntimeError('Existing toon instance; do not replay')
        mi=TOOLS.create_asset('MI_Toon_'+name,'/Game/Selene/Materials/Character',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
        if not mi: raise RuntimeError('Failed to create toon instance')
        MEL.set_material_instance_parent(mi,parent)
        if not MEL.set_material_instance_texture_parameter_value(mi,'BaseColorTex',tex):
            raise RuntimeError('BaseColorTex parameter rejected')
        MEL.update_material_instance(mi); save(mi)
        relinks=[]
        for slot in mesh.get_editor_property('materials'):
            imported=slot.material_interface
            if not isinstance(imported,u.MaterialInstanceConstant) or not imported.get_path_name().startswith(folder+'/Materials/'):
                raise RuntimeError('Unexpected imported material slot')
            old_parent=imported.get_editor_property('parent')
            copied=local_copy(old_parent)
            MEL.set_material_instance_parent(imported,copied)
            MEL.update_material_instance(imported); save(imported)
            usage(imported.get_base_material())
            relinks.append(dict(material=imported.get_path_name(),old_parent=old_parent.get_path_name(),new_parent=copied.get_path_name()))
        report['heroes'][name]=dict(toon=mi.get_path_name(),texture=tex.get_path_name(),relinks=relinks,
            height_cm=mesh.get_bounds().box_extent.z*2)
        checkpoint()
    report['status']='success'
except Exception:
    report.update(status='failed',error=traceback.format_exc())
finally:
    checkpoint()
if report['status']!='success': raise RuntimeError(report['error'])
