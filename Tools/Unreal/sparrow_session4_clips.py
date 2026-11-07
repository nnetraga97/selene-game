"""Repair existing Sparrow walk roots, then retarget exactly four GASP runs."""
import json
import math
from pathlib import Path
import shutil
import statistics
import traceback
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
OUT = ROOT / 'Saved/Sparrow/session-4'
BASE = '/Game/Selene/Characters/Sparrow'
DEST = BASE + '/Anims/GASP/'
SUFFIXES = ('Loop_F', 'Start_F_Lfoot', 'Stop_F_Lfoot', 'Pivot_F_B_Lfoot')
WALKS = ['M_Neutral_Walk_' + s for s in SUFFIXES]
RUNS = ['M_Neutral_Run_' + s for s in SUFFIXES]
LIB = u.EditorAssetLibrary
report = dict(status='running', stage='preflight', saved=[], walks=[], runs=[])


def checkpoint():
    (OUT / 'clips.json').write_text(json.dumps(report, indent=2))


def save(asset):
    if not asset.get_path_name().startswith(BASE + '/'):
        raise RuntimeError('Save outside Sparrow scope')
    if not LIB.save_loaded_asset(asset, only_if_is_dirty=False):
        raise RuntimeError('Save failed: ' + asset.get_path_name())
    report['saved'].append(asset.get_path_name())
    checkpoint()


def flags(anim):
    return {k: str(anim.get_editor_property(k)) for k in
            ('enable_root_motion', 'force_root_lock', 'root_motion_root_lock')}


def sample(anim, mesh):
    opts = u.AnimPoseEvaluationOptions()
    for key, value in dict(evaluation_type=u.AnimDataEvalType.COMPRESSED, should_retarget=True,
                           extract_root_motion=False, incorporate_root_motion_into_pose=False,
                           optional_skeletal_mesh=mesh, evaluate_curves=False).items():
        opts.set_editor_property(key, value)
    seconds = anim.get_play_length()
    samples = []
    for i in range(math.ceil(seconds * 60) + 1):
        t = min(i / 60., seconds)
        pose = u.AnimPoseExtensions.get_anim_pose_at_time(anim, t, opts)
        bones = {}
        for bone in ('root', 'pelvis', 'ball_l', 'ball_r'):
            v = u.AnimPoseExtensions.get_bone_pose(pose, bone, u.AnimPoseSpaces.WORLD).translation
            bones[bone] = [v.x, v.y, v.z]
        samples.append(dict(time=t, bones=bones))
    summary = {}
    for bone in ('root', 'pelvis'):
        xyz = [s['bones'][bone] for s in samples]
        summary[bone] = dict(first=xyz[0], last=xyz[-1],
                             minimum=[min(p[a] for p in xyz) for a in range(3)],
                             maximum=[max(p[a] for p in xyz) for a in range(3)])
    return dict(seconds=seconds, flags=flags(anim), summary=summary, samples=samples)


def normalize(anim, mesh):
    anim.set_editor_property('enable_root_motion', False)
    anim.set_editor_property('force_root_lock', True)
    anim.set_editor_property('root_motion_root_lock', u.RootMotionRootLock.ZERO)
    after = sample(anim, mesh)
    after['max_root_distance_cm'] = max(math.dist(s['bones']['root'], [0, 0, 0]) for s in after['samples'])
    after['max_pelvis_horizontal_distance_cm'] = max(math.hypot(*s['bones']['pelvis'][:2]) for s in after['samples'])
    if after['max_root_distance_cm'] > .01 or after['max_pelvis_horizontal_distance_cm'] > 100:
        raise RuntimeError('Root/pelvis origin verification failed: ' + anim.get_path_name())
    save(anim)
    return after


def ground_speed(samples):
    speeds = []
    for bone in ('ball_l', 'ball_r'):
        xyz = [s['bones'][bone] for s in samples]
        h = sorted(p[2] for p in xyz)[int((len(xyz) - 1) * .35)]
        for i in range(1, len(samples) - 1):
            dt = samples[i + 1]['time'] - samples[i - 1]['time']
            backward = -(xyz[i + 1][1] - xyz[i - 1][1]) / dt
            vz = (xyz[i + 1][2] - xyz[i - 1][2]) / dt
            if xyz[i][2] <= h and abs(vz) < 25 and backward > 30:
                speeds.append(backward)
    if len(speeds) < 6:
        raise RuntimeError('Insufficient run stance samples')
    ordered = sorted(speeds)
    return dict(cm_s=statistics.median(speeds), samples=len(speeds),
                p10_p90_cm_s=[ordered[int((len(ordered) - 1) * q)] for q in (.1, .9)],
                candidates_cm_s=speeds,
                method='60 Hz compressed +Y bilateral toes; lowest 35% heights; abs(vz)<25; backward>30')


def main():
    if (OUT / 'clips.json').exists():
        raise RuntimeError('Existing report; do not replay')
    for name in WALKS:
        if not LIB.does_asset_exist(DEST + name + '_Sparrow'):
            raise RuntimeError('Missing existing walk: ' + name)
    for name in RUNS:
        if LIB.does_asset_exist(DEST + name + '_Sparrow'):
            raise RuntimeError('Run output already exists: ' + name)
    mesh = u.load_asset('/Game/ParagonSparrow/Characters/Heroes/Sparrow/Meshes/Sparrow')
    source = u.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple')
    rtg = u.load_asset(BASE + '/RTG_Manny_To_Sparrow')
    if not mesh or not source or not rtg:
        raise RuntimeError('Missing existing mesh or retargeter')
    report['stage'] = 'repair-walks'
    backup = OUT / 'original-walks'
    backup.mkdir(exist_ok=False)
    for name in WALKS:
        filename = name + '_Sparrow.uasset'
        shutil.copy2(ROOT / 'Content/Selene/Characters/Sparrow/Anims/GASP' / filename, backup / filename)
        anim = u.load_asset(DEST + name + '_Sparrow')
        item = dict(package=anim.get_path_name(), before=sample(anim, mesh))
        report['walks'].append(item)
        checkpoint()
        item['after'] = normalize(anim, mesh)
        checkpoint()
    report['walk_root_repair'] = 'passed'
    report['stage'] = 'retarget-runs'
    checkpoint()
    inputs = u.IKRetargetBatchOperationInputs()
    for key, value in dict(assets_to_retarget=[LIB.find_asset_data('/Game/Selene/Animation/GASP/' + n) for n in RUNS],
                           source_mesh=source, target_mesh=mesh, ik_retarget_asset=rtg,
                           suffix='_Sparrow', target_path=DEST.rstrip('/'), include_referenced_assets=False,
                           overwrite_existing_files=False, use_source_path=False).items():
        inputs.set_editor_property(key, value)
    made = u.IKRetargetBatchOperation.run_batch_retarget(inputs)
    if len(made) != 4:
        raise RuntimeError('Expected exactly four run outputs, got ' + str(len(made)))
    for data in made:
        anim = data.get_asset()
        if anim.get_name() not in [n + '_Sparrow' for n in RUNS] or anim.get_editor_property('skeleton') != mesh.get_editor_property('skeleton'):
            raise RuntimeError('Unexpected run output')
        item = dict(package=anim.get_path_name(), before=sample(anim, mesh))
        report['runs'].append(item)
        item['after'] = normalize(anim, mesh)
        if anim.get_name() == RUNS[0] + '_Sparrow':
            report['run_ground_speed'] = ground_speed(item['after']['samples'])
        checkpoint()
    report.update(status='success', stage='complete')


try:
    main()
except Exception:
    report.update(status='failed', error=traceback.format_exc())
finally:
    checkpoint()
if report['status'] != 'success':
    raise RuntimeError(report['error'])
