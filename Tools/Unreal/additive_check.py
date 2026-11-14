import json
from pathlib import Path
import unreal as u
S = '/Game/ParagonSparrow/Characters/Heroes/Sparrow/Animations/'
R = {}
for n in ['idle', 'idle_relaxed', 'Travel_mode_Idle', 'Jog_Fwd', 'Jog_Bwd', 'Jog_Left', 'Jog_Right', 'Primary_Fire_Fast', 'Primary_Fire_Med', 'Q_Ability', 'RMB_Fire', 'Cast',
          'HitReact_Fwd', 'HitReact_Bwd', 'HitReact_Left', 'HitReact_Right', 'Death_Fwd', 'Turn_Left_90', 'Turn_Right_90', 'Jog_Fwd_Start', 'Jog_Fwd_Stop', 'Jog_Fwd_Pivot180']:
    a = u.load_asset(S + n)
    R[n] = str(a.get_editor_property('additive_anim_type')) if a else 'missing'
A = '/Game/Selene/Characters/Warrior/Anims/Aurora/'
for n in ['HitReact_Front_Warrior', 'Death_Warrior', 'Turn_Left_90_Warrior', 'Primary_Attack_A_InMotion_Warrior', 'Idle_Warrior', 'Jog_Bwd_Warrior']:
    a = u.load_asset(A + n); R[n] = str(a.get_editor_property('additive_anim_type')) if a else 'missing'
Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()), 'Saved/CombatAnims/additive.json').write_text(json.dumps(R, indent=1))
