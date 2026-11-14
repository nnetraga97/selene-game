"""Rebuild the runtime sample grid of every strafe blend space (Python-set samples left it empty, so they played the
T-pose) and save. Report: Saved/CombatAnims/strafe_rebuild.json."""
import json
from pathlib import Path
import unreal as u
R = {}
for h in ('Warrior', 'Warden', 'Sparrow', 'Aurora'):
    p = '/Game/Selene/Characters/%s/Anims/BS_Strafe_%s' % (h, h)
    bs = u.load_asset(p)
    if not bs: R[h] = 'missing'; continue
    grid = u.SeleneAnimTools.rebuild_blend_space(bs)
    R[h] = dict(grid=grid, saved=u.EditorAssetLibrary.save_loaded_asset(bs, only_if_is_dirty=False))
Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()), 'Saved/CombatAnims/strafe_rebuild.json').write_text(json.dumps(R, indent=1))
