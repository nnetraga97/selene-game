"""Fresh-process pass after combat_anims.py: load every Warrior/Warden Aurora clip so its curve names land on the
skeleton (UAnimSequenceBase::PostLoad), then save clips and skeletons. Without this -game crashes when a hero loads."""
import json
from pathlib import Path
import unreal as u
LIB = u.EditorAssetLibrary
R = {}
for hero, mesh in (('Warrior', '/Game/Assets/eclipse-warrior/eclipse-warrior/SkeletalMeshes/eclipse-warrior'),
                   ('Warden', '/Game/Assets/eclipse-warden/eclipse-warden/SkeletalMeshes/eclipse-warden')):
    skel = u.load_asset(mesh).get_editor_property('skeleton')
    n = 0
    for p in LIB.list_assets(f'/Game/Selene/Characters/{hero}/Anims', recursive=True):
        a = u.load_asset(p)
        if isinstance(a, (u.AnimSequence, u.BlendSpace)):
            LIB.save_loaded_asset(a, only_if_is_dirty=False); n += 1
    R[hero] = {'saved': n, 'skeleton_saved': LIB.save_loaded_asset(skel, only_if_is_dirty=False)}
Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()), 'Saved/CombatAnims/curves.json').write_text(json.dumps(R, indent=1))
