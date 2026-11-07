"""Read-only fresh root reload and bow/hand placement diagnosis after game review."""
import json
import math
from pathlib import Path
import traceback
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
OUT = ROOT / 'Saved/Sparrow/session-4'
report = dict(status='running', saved_assets=[], clips=[])


def main():
    if (OUT / 'reload-weapon-check.json').exists():
        raise RuntimeError('Existing verification evidence; do not replay')
    mesh = u.load_asset('/Game/ParagonSparrow/Characters/Heroes/Sparrow/Meshes/Sparrow')
    opts = u.AnimPoseEvaluationOptions()
    for key, value in dict(evaluation_type=u.AnimDataEvalType.COMPRESSED, should_retarget=True,
                           extract_root_motion=False, incorporate_root_motion_into_pose=False,
                           optional_skeletal_mesh=mesh, evaluate_curves=False).items():
        opts.set_editor_property(key, value)
    prior = json.loads((OUT / 'clips.json').read_text())
    paths = prior['saved'] + ['/Game/ParagonSparrow/Characters/Heroes/Sparrow/Animations/' + name
                              for name in ('Sprint_Fwd', 'Travel_mode_Idle')]
    for path in paths:
        anim = u.load_asset(path)
        if not anim:
            raise RuntimeError('Cannot load ' + path)
        samples = []
        for i in range(math.ceil(anim.get_play_length() * 60) + 1):
            t = min(i / 60., anim.get_play_length())
            pose = u.AnimPoseExtensions.get_anim_pose_at_time(anim, t, opts)
            bones = {}
            for name in ('root', 'pelvis', 'hand_l', 'bow_base', 'bow_string_mid', 'bow_string_top', 'bow_string_bott', 'hand_r', 'arrow_nock'):
                tr = u.AnimPoseExtensions.get_bone_pose(pose, name, u.AnimPoseSpaces.WORLD)
                bones[name] = [tr.translation.x, tr.translation.y, tr.translation.z]
            samples.append(dict(time=t, bones=bones,
                                bow_grip_to_left_hand_cm=math.dist(bones['bow_base'], bones['hand_l']),
                                bow_tip_span_cm=math.dist(bones['bow_string_top'], bones['bow_string_bott']),
                                arrow_to_right_hand_cm=math.dist(bones['arrow_nock'], bones['hand_r'])))
        item = dict(package=anim.get_path_name(), samples=samples,
                    flags={key: str(anim.get_editor_property(key)) for key in
                           ('enable_root_motion', 'force_root_lock', 'root_motion_root_lock')},
                    root_max_cm=max(math.dist(s['bones']['root'], [0, 0, 0]) for s in samples),
                    pelvis_y_range_cm=[min(s['bones']['pelvis'][1] for s in samples), max(s['bones']['pelvis'][1] for s in samples)])
        for metric in ('bow_grip_to_left_hand_cm', 'bow_tip_span_cm', 'arrow_to_right_hand_cm'):
            item[metric] = [min(s[metric] for s in samples), max(s[metric] for s in samples)]
        report['clips'].append(item)
        if path.startswith('/Game/Selene/') and item['root_max_cm'] > .01:
            raise RuntimeError('Fresh reload root is not zero: ' + path)
    report['status'] = 'success'


try:
    main()
except Exception:
    report.update(status='failed', error=traceback.format_exc())
finally:
    (OUT / 'reload-weapon-check.json').write_text(json.dumps(report, indent=2))
if report['status'] != 'success':
    raise RuntimeError(report['error'])
