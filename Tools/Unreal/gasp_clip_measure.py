"""Read-only dense GASP root-lock/stance-foot audit. Never changes or saves assets.

AnimPose's incorporate_root_motion_into_pose maps to bIgnoreRootLock. Compare
both settings in raw and compressed evaluation at 60 Hz, using the actual mesh.
All coordinates are skeletal component space, cm; bones are not shoe soles.
"""
import hashlib
import json
import math
from pathlib import Path
import statistics
import traceback

import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
OUT = ROOT / 'Saved/Clips/session-4'
REPORT = OUT / 'measurement.json'
report = {'status': 'running', 'sample_hz': 60, 'clips': [],
          'notes': ['Bone positions are not sole clearance.',
                    'Unlocked is an in-memory evaluation option, not an asset edit.',
                    'Stance candidates: lowest 35% toe heights, abs vertical speed <25 cm/s, backward speed >30 cm/s.']}


def checkpoint():
    REPORT.write_text(json.dumps(report, indent=2) + '\n')


def vector(v):
    values = [v.x, v.y, v.z]
    if not all(math.isfinite(x) for x in values):
        raise RuntimeError('Nonfinite sampled position')
    return values


def stats(values):
    if not values:
        return {'count': 0}
    a = sorted(values)
    return {'count': len(a), 'min': a[0], 'max': a[-1], 'median': statistics.median(a),
            'mean': statistics.mean(a), 'p10': a[int((len(a)-1)*.1)], 'p90': a[int((len(a)-1)*.9)]}


def summarize(samples, bones):
    output = {}
    for bone in bones:
        xyz = [s['bones'][bone]['translation'] for s in samples]
        entry = {'xyz_range_cm': [[min(v[k] for v in xyz), max(v[k] for v in xyz)] for k in range(3)],
                 'endpoint_delta_cm': [xyz[-1][k]-xyz[0][k] for k in range(3)]}
        if 'Toe' in bone or 'ball_' in bone or 'Foot' in bone or 'foot_' in bone:
            heights = sorted(v[2] for v in xyz)
            height_limit = heights[int((len(heights)-1)*.35)]
            candidates = []
            for i in range(1, len(samples)-1):
                dt = samples[i+1]['time'] - samples[i-1]['time']
                vz = (xyz[i+1][2]-xyz[i-1][2])/dt
                backward = -(xyz[i+1][1]-xyz[i-1][1])/dt
                if xyz[i][2] <= height_limit and abs(vz) < 25 and backward > 30:
                    candidates.append({'time': samples[i]['time'], 'speed': backward, 'height': xyz[i][2]})
            entry.update(stance_speed_cm_s=stats([c['speed'] for c in candidates]), stance_candidates=candidates)
        output[bone] = entry
    return output


def main():
    if not (ROOT/'Selene.uproject').is_file() or REPORT.exists():
        raise RuntimeError('Wrong project or existing report; do not replay')
    saved = json.loads((ROOT/'Saved/Clips/session-3/retarget.json').read_text())
    manny = json.loads((ROOT/'Saved/Clips/session-3/reload-dependencies.json').read_text())
    if saved['status'] != 'success' or manny['status'] != 'success':
        raise RuntimeError('Prior retarget/reload must pass')
    groups = [('Manny', '/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple', manny['clips'])]
    groups += [(name, hero['mesh'], hero['clips']) for name, hero in saved['heroes'].items()]
    for name, mesh_path, clips in groups:
        mesh = u.load_asset(mesh_path)
        if not mesh:
            raise RuntimeError('Missing mesh: '+mesh_path)
        bones = (['root', 'pelvis', 'foot_l', 'foot_r', 'ball_l', 'ball_r'] if name == 'Manny' else
                 ['mixamorig_Hips', 'mixamorig_LeftFoot', 'mixamorig_RightFoot', 'mixamorig_LeftToeBase', 'mixamorig_RightToeBase'])
        for clip in clips:
            if clip['role'] not in ('WalkLoop', 'RunLoop', 'SprintLoop'):
                continue
            filename = ROOT/'Content'/(clip['package'][6:]+'.uasset')
            if hashlib.sha256(filename.read_bytes()).hexdigest() != clip['sha256']:
                raise RuntimeError('Previously verified clip changed: '+clip['package'])
            anim = u.load_asset(clip['package'])
            if not isinstance(anim, u.AnimSequence):
                raise RuntimeError('Missing animation: '+clip['package'])
            item = {'hero': name, 'role': clip['role'], 'package': clip['package'], 'sha256': clip['sha256'],
                    'seconds': anim.get_play_length(), 'force_root_lock': anim.get_editor_property('force_root_lock'),
                    'enable_root_motion': anim.get_editor_property('enable_root_motion'), 'modes': {}}
            report['clips'].append(item)
            checkpoint()
            for evaluation in ('RAW', 'COMPRESSED'):
                for unlocked in (False, True):
                    key = evaluation.lower() + ('_unlocked' if unlocked else '_locked')
                    opts = u.AnimPoseEvaluationOptions()
                    for prop, value in {'evaluation_type': getattr(u.AnimDataEvalType, evaluation),
                                        'should_retarget': True, 'extract_root_motion': False,
                                        'incorporate_root_motion_into_pose': unlocked,
                                        'optional_skeletal_mesh': mesh, 'evaluate_curves': False}.items():
                        opts.set_editor_property(prop, value)
                    samples = []
                    frames = round(anim.get_play_length()*60)
                    for frame in range(frames+1):
                        t = min(frame/60., anim.get_play_length())
                        pose = u.AnimPoseExtensions.get_anim_pose_at_time(anim, t, opts)
                        if not u.AnimPoseExtensions.is_valid(pose):
                            raise RuntimeError('Invalid pose: '+clip['package'])
                        if frame == 0:
                            names = [str(b) for b in u.AnimPoseExtensions.get_bone_names(pose)]
                            if not all(b in names for b in bones):
                                raise RuntimeError('Missing sampled bones: '+str(names))
                            item['bone_zero'] = names[0]
                            item['reference_positions_cm'] = {b: vector(u.AnimPoseExtensions.get_ref_bone_pose(pose,b,u.AnimPoseSpaces.WORLD).translation) for b in bones}
                        values = {}
                        for bone in bones:
                            x = u.AnimPoseExtensions.get_bone_pose(pose, bone, u.AnimPoseSpaces.WORLD)
                            q = x.rotation
                            values[bone] = {'translation': vector(x.translation), 'quaternion': [q.x,q.y,q.z,q.w]}
                        samples.append({'time': t, 'bones': values})
                    item['modes'][key] = {'samples': samples, 'summary': summarize(samples,bones)}
                    checkpoint()
            u.log('SELENE_CLIP_MEASURE '+name+' '+clip['role'])
    report['status'] = 'success'


try:
    main()
except Exception as exc:
    report.update(status='failed', error=str(exc), traceback=traceback.format_exc())
finally:
    checkpoint()
u.log('SELENE_CLIP_MEASURE '+report['status'])
if report['status'] != 'success':
    raise RuntimeError(report['error'])
