"""Root the selected Paragon assets for cooking without cooking the whole animation pack."""
import json
from pathlib import Path
import unreal as u

root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
out = root / 'Saved/Sparrow/session-3'
base = '/Game/Selene/Characters/Sparrow'
name = 'PAL_Sparrow'
if u.EditorAssetLibrary.does_asset_exist(base + '/' + name):
    raise RuntimeError('Cook label already exists; do not replay')
paths = [v for k, v in json.loads((out / 'roster-assets.json').read_text()).items() if k != 'Name']
assets = [u.load_asset(path) for path in paths]
if not all(assets):
    raise RuntimeError('Missing roster asset')
factory = u.DataAssetFactory()
factory.set_editor_property('data_asset_class', u.PrimaryAssetLabel)
label = u.AssetToolsHelpers.get_asset_tools().create_asset(name, base, u.PrimaryAssetLabel, factory)
label.set_editor_property('explicit_assets', assets)
label.set_editor_property('is_runtime_label', True)
label.set_editor_property('label_assets_in_my_directory', False)
rules = label.get_editor_property('rules')
rules.set_editor_property('cook_rule', u.PrimaryAssetCookRule.ALWAYS_COOK)
label.set_editor_property('rules', rules)
if not u.EditorAssetLibrary.save_loaded_asset(label, only_if_is_dirty=False):
    raise RuntimeError('Could not save Sparrow cook label')
(out / 'cook-label.json').write_text(json.dumps(dict(status='success', label=label.get_path_name(), explicit_assets=paths), indent=2))
