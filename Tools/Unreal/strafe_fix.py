"""Strafe blend spaces: no speed-axis animation scaling (idle samples sit at speed 0, which gives NaN play rates)
and no marker-based sync (Sparrow's jogs carry mismatched marker sets and the idle none, which gave NaN poses)."""
import json
from pathlib import Path
import unreal as u
R = {}
for p in ('/Game/Selene/Characters/Warrior/Anims/BS_Strafe_Warrior', '/Game/Selene/Characters/Warden/Anims/BS_Strafe_Warden', '/Game/Selene/Characters/Sparrow/Anims/BS_Strafe_Sparrow'):
    bs = u.load_asset(p)
    bs.set_editor_property('axis_to_scale_animation', u.BlendSpaceAxis.BSA_NONE)
    bs.set_editor_property('allow_marker_based_sync', False)
    R[p] = [str(bs.get_editor_property('allow_marker_based_sync')), u.EditorAssetLibrary.save_loaded_asset(bs, only_if_is_dirty=False)]
Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()), 'Saved/CombatAnims/strafe_fix.json').write_text(json.dumps(R, indent=1))
