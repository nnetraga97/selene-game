"""Make the Fixer/Courier GASP walk/run/sprint loops play in place, and measure their ground speed.

Mixamo rigs have no root bone: the retargeted hips carry the loop's forward travel. For each loop,
remove only the straight-line XY drift of mixamorig_Hips across the clip (start-to-end displacement
spread evenly over time), keeping hips Z, sway, rotation and every other track. Ground speed =
that displacement / clip length. Then turn force_root_lock off (the travel is gone from the keys).

Run headless: SELENE_LOOP_HEROES=Fixer,Courier UnrealEditor-Cmd Selene.uproject -run=pythonscript -script=<this>
Writes Saved/Chars/linear-in-place.json. Refuses to touch a clip twice (force_root_lock already off).
"""
import json
import math
import os
from pathlib import Path
import traceback

import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
OUT = ROOT / 'Saved/Chars/linear-in-place.json'
HEROES = [h for h in os.environ.get('SELENE_LOOP_HEROES', 'Fixer,Courier').split(',') if h]
ROLES = {'Walk': 'M_Neutral_Walk_Loop_F', 'Run': 'M_Neutral_Run_Loop_F', 'Sprint': 'M_Neutral_Sprint_Loop_F'}
report = {'status': 'running', 'clips': []}


def hips_xyz(anim, t, opts):
    pose = u.AnimPoseExtensions.get_anim_pose_at_time(anim, t, opts)
    x = u.AnimPoseExtensions.get_bone_pose(pose, 'mixamorig_Hips', u.AnimPoseSpaces.LOCAL)
    return x


def main():
    for hero in HEROES:
        for role, base in ROLES.items():
            path = f'/Game/Selene/Characters/{hero}/Anims/GASP/{base}_{hero}'
            anim = u.load_asset(path)
            if not isinstance(anim, u.AnimSequence):
                raise RuntimeError('Missing ' + path)
            if not anim.get_editor_property('force_root_lock'):
                raise RuntimeError('Already corrected (force_root_lock off): ' + path)
            model = anim.get_editor_property('data_model_interface')
            frames = model.get_number_of_frames()
            length = anim.get_play_length()
            opts = u.AnimPoseEvaluationOptions()
            opts.set_editor_property('evaluation_type', u.AnimDataEvalType.RAW)
            opts.set_editor_property('incorporate_root_motion_into_pose', True)
            opts.set_editor_property('evaluate_curves', False)
            poses = [hips_xyz(anim, length * f / frames, opts) for f in range(frames + 1)]
            d = [poses[-1].translation.x - poses[0].translation.x, poses[-1].translation.y - poses[0].translation.y]
            speed = math.hypot(*d) / length
            keys, rots, scales = [], [], []
            for f, x in enumerate(poses):
                k = f / frames
                keys.append(u.Vector(x.translation.x - d[0] * k, x.translation.y - d[1] * k, x.translation.z))
                rots.append(x.rotation)
                scales.append(x.scale3d)
            controller = anim.get_editor_property('controller')
            controller.open_bracket('Remove linear hips ground travel', False)
            try:
                if not controller.set_bone_track_keys('mixamorig_Hips', keys, rots, scales, False):
                    raise RuntimeError('SetBoneTrackKeys failed: ' + path)
            finally:
                controller.close_bracket(False)
            anim.set_editor_property('force_root_lock', False)
            # Check: after correction the hips end where they started (in place).
            after = [hips_xyz(anim, length * f / frames, opts) for f in (0, frames)]
            drift = math.hypot(after[1].translation.x - after[0].translation.x, after[1].translation.y - after[0].translation.y)
            if drift > 1.0 or model.get_number_of_frames() != frames:
                raise RuntimeError(f'Correction check failed for {path}: drift {drift:.3f} cm')
            if not u.EditorAssetLibrary.save_loaded_asset(anim, only_if_is_dirty=False):
                raise RuntimeError('Save failed: ' + path)
            report['clips'].append({'hero': hero, 'role': role, 'package': path, 'frames': frames,
                                    'length_s': length, 'travel_xy_cm': d, 'speed_cm_s': round(speed, 1),
                                    'end_drift_after_cm': round(drift, 4)})
            OUT.write_text(json.dumps(report, indent=2) + '\n')
    report['status'] = 'success'


try:
    main()
except Exception as exc:
    report.update(status='failed', error=str(exc), traceback=traceback.format_exc())
finally:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + '\n')
u.log('SELENE_LINEAR_IN_PLACE ' + report['status'])
