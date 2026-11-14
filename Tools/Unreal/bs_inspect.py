import json
from pathlib import Path
import unreal as u
R = {}
for p in ['/Game/Selene/Characters/%s/Anims/BS_Strafe_%s' % (h, h) for h in ('Warrior', 'Warden', 'Sparrow', 'Aurora')] + ['/Game/Selene/Characters/Warden/Anims/BS_Idle_Walk_Run_Warden']:
    bs = u.load_asset(p)
    d = {'params': [[str(b.get_editor_property('display_name')), b.get_editor_property('min'), b.get_editor_property('max'), b.get_editor_property('grid_num')] for b in bs.get_editor_property('blend_parameters')]}
    d['samples'] = []
    for s in bs.get_editor_property('sample_data'):
        a = s.get_editor_property('animation'); v = s.get_editor_property('sample_value')
        d['samples'].append([a.get_name() if a else None, v.x, v.y, s.get_editor_property('rate_scale')])
    for k in ('skeleton',):
        try: d[k] = bs.get_editor_property(k).get_path_name()
        except Exception as e: d[k] = str(e)[:80]
    d['anim_skeletons'] = list({s.get_editor_property('animation').get_editor_property('skeleton').get_path_name() for s in bs.get_editor_property('sample_data')})
    for k in ('axis_to_scale_animation', 'allow_marker_based_sync'):
        try: d[k] = str(bs.get_editor_property(k))
        except Exception as e: d[k] = 'n/a'
    d['bs_skeleton'] = bs.get_editor_property('skeleton').get_path_name() if bs.get_editor_property('skeleton') else None
    d['mismatch'] = [x for x in d['anim_skeletons'] if x != d['bs_skeleton']]
    for k in ('interpolation_param', 'target_weight_interpolation_speed_per_sec', 'b_loop'):
        try: d[k] = str(bs.get_editor_property(k))
        except Exception as e: d[k] = 'n/a'
    R[p] = d
Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()), 'Saved/CombatAnims/bs.json').write_text(json.dumps(R, indent=1, default=str))
