import json
from pathlib import Path
import unreal as u
S = '/Game/ParagonSparrow/Characters/Heroes/Sparrow/Animations/'
R = {}
for n in ['idle', 'idle_relaxed', 'Travel_mode_Idle', 'Idle_FrontEnd', 'Jog_Fwd', 'Jog_Bwd', 'Jog_Left', 'Jog_Right']:
    a = u.load_asset(S + n)
    R[n] = [a.get_play_length(), a.get_editor_property('number_of_sampled_frames') if hasattr(a, 'number_of_sampled_frames') else None] if a else 'missing'
    try: R[n].append(len(u.AnimationLibrary.get_animation_sync_markers(a)))
    except Exception as e: R[n].append(str(e)[:60])
Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()), 'Saved/CombatAnims/lengths.json').write_text(json.dumps(R, indent=1, default=str))
