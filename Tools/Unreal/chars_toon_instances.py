"""Create MI_Toon_<Hero> for Fixer and Courier from M_Character_Toon (same as Champion's), and verify the
BaseColorTex override by reading it back (UE 5.8 MaterialEditingLibrary setters can return False on success).
Writes Saved/Chars/toon-instances.json.
"""
import json
from pathlib import Path
import traceback

import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
OUT = ROOT / 'Saved/Chars/toon-instances.json'
LIB, MEL = u.EditorAssetLibrary, u.MaterialEditingLibrary
TOOLS = u.AssetToolsHelpers.get_asset_tools()
HEROES = {
    'Fixer': '/Game/Assets/night-market-fixer/night-market-fixer/Textures/female_action_figure_3d_model_basecolor',
    'Courier': '/Game/Assets/scooter-courier/scooter-courier/Textures/stylized_character_3d_model_basecolor',
}
report = {'status': 'running', 'instances': {}}
try:
    parent = u.load_asset('/Game/Selene/Materials/Character/M_Character_Toon')
    if not parent:
        raise RuntimeError('Missing M_Character_Toon')
    for name, tex_path in HEROES.items():
        dest = '/Game/Selene/Materials/Character/MI_Toon_' + name
        mi = u.load_asset(dest) if LIB.does_asset_exist(dest) else TOOLS.create_asset(
            'MI_Toon_' + name, '/Game/Selene/Materials/Character', u.MaterialInstanceConstant,
            u.MaterialInstanceConstantFactoryNew())
        tex = u.load_asset(tex_path)
        if not mi or not tex:
            raise RuntimeError('Missing instance or texture for ' + name)
        MEL.set_material_instance_parent(mi, parent)
        MEL.set_material_instance_texture_parameter_value(mi, 'BaseColorTex', tex)
        MEL.update_material_instance(mi)
        got = MEL.get_material_instance_texture_parameter_value(mi, 'BaseColorTex')
        if not got or got.get_path_name() != tex.get_path_name():
            raise RuntimeError(f'BaseColorTex readback mismatch for {name}: {got}')
        if not LIB.save_loaded_asset(mi, only_if_is_dirty=False):
            raise RuntimeError('Save failed ' + dest)
        report['instances'][name] = {'instance': mi.get_path_name(), 'texture': got.get_path_name()}
    report['status'] = 'success'
except Exception as exc:
    report.update(status='failed', error=str(exc), traceback=traceback.format_exc())
OUT.write_text(json.dumps(report, indent=2) + '\n')
u.log('SELENE_TOON_INSTANCES ' + report['status'])
