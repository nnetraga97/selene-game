"""Create Sparrow's FK body rig/retargeter and exactly four GASP walks; measure playback."""
import json
import math
from pathlib import Path
import statistics
import traceback
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
OUT = ROOT / 'Saved/Sparrow/session-3'
BASE = '/Game/Selene/Characters/Sparrow'
SOURCE = '/Game/Selene/Animation/GASP/'
NAMES = ('M_Neutral_Walk_Loop_F', 'M_Neutral_Walk_Start_F_Lfoot',
         'M_Neutral_Walk_Stop_F_Lfoot', 'M_Neutral_Walk_Pivot_F_B_Lfoot')
report = dict(status='running', saved=[], clips=[])
lib = u.EditorAssetLibrary
tools = u.AssetToolsHelpers.get_asset_tools()

def checkpoint():
    (OUT / 'retarget.json').write_text(json.dumps(report, indent=2))

def save(asset):
    if not lib.save_loaded_asset(asset, only_if_is_dirty=False):
        raise RuntimeError('Save failed: ' + asset.get_path_name())
    report['saved'].append(asset.get_path_name())
    checkpoint()

def main():
    if (OUT / 'retarget.json').exists() or lib.does_asset_exist(BASE + '/IK_Sparrow'):
        raise RuntimeError('Existing retarget evidence/assets; do not replay')
    source = u.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple')
    target = u.load_asset('/Game/ParagonSparrow/Characters/Heroes/Sparrow/Meshes/Sparrow')
    src = tools.duplicate_asset('IK_Manny', BASE, u.load_asset('/Game/Selene/Characters/Champion/IK_Manny'))
    tgt = tools.create_asset('IK_Sparrow', BASE, u.IKRigDefinition, u.IKRigDefinitionFactory())
    if not source or not target or not src or not tgt:
        raise RuntimeError('Missing mesh or failed rig creation')
    c = u.IKRigController.get_controller(tgt)
    if not c.set_skeletal_mesh(target) or not c.set_retarget_root('pelvis'):
        raise RuntimeError('Could not set target mesh/pelvis')
    chains = [('Spine', 'spine_01', 'spine_03'), ('Neck', 'neck_01', 'neck_02'), ('Head', 'head', 'head')]
    for side, suffix in (('Left', 'l'), ('Right', 'r')):
        for name, start, end in [('Leg', 'thigh', 'foot'), ('Foot', 'ball', 'ball'),
                                 ('Clavicle', 'clavicle', 'clavicle'), ('Arm', 'upperarm', 'hand')]:
            chains.append((side + name, start + '_' + suffix, end + '_' + suffix))
        for finger in ('thumb', 'index', 'middle', 'ring', 'pinky'):
            chains.append((side + finger.title(), finger + '_01_' + suffix, finger + '_03_' + suffix))
    for name, start, end in chains:
        c.add_retarget_chain(name, start, end, '')
    if len(c.get_retarget_chains()) != len(chains):
        raise RuntimeError('Incomplete Sparrow chains')
    report['chains'] = chains
    rtg = tools.create_asset('RTG_Manny_To_Sparrow', BASE, u.IKRetargeter, u.IKRetargetFactory())
    r = u.IKRetargeterController.get_controller(rtg)
    S, T = u.RetargetSourceOrTarget.SOURCE, u.RetargetSourceOrTarget.TARGET
    r.set_ik_rig(S, src)
    r.set_ik_rig(T, tgt)
    r.set_preview_mesh(S, source)
    r.set_preview_mesh(T, target)
    r.add_default_ops()
    r.assign_ik_rig_to_all_ops(S, src)
    r.assign_ik_rig_to_all_ops(T, tgt)
    # This explicit body-chain rig uses FK; no solver or unverified weapon goals.
    r.set_retarget_op_enabled(r.get_index_of_op_by_name('Run IK Rig'), False)
    r.auto_map_chains(u.AutoMapChainType.EXACT, True)
    pose = r.create_retarget_pose('AlignedToManny', T)
    r.set_current_retarget_pose(pose, T)
    r.auto_align_all_bones(T)
    root = r.get_op_controller(r.get_index_of_op_by_name('Root Motion'))
    root.set_source_root_bone('root')
    root.set_target_root_bone('root')
    report['mapping'] = {name: str(r.get_source_chain(name)) for name, _, _ in chains}
    if any(name != mapped for name, mapped in report['mapping'].items()):
        raise RuntimeError('Incomplete source chain mapping')
    report['ops'] = [(str(r.get_op_name(i)), r.get_retarget_op_enabled(i)) for i in range(r.get_num_retarget_ops())]
    for asset in (src, tgt, rtg):
        save(asset)
    inputs = u.IKRetargetBatchOperationInputs()
    assets = [lib.find_asset_data(SOURCE + name) for name in NAMES]
    for key, value in dict(assets_to_retarget=assets, source_mesh=source, target_mesh=target,
                           ik_retarget_asset=rtg, suffix='_Sparrow', target_path=BASE + '/Anims/GASP',
                           include_referenced_assets=False, overwrite_existing_files=False, use_source_path=False).items():
        inputs.set_editor_property(key, value)
    made = u.IKRetargetBatchOperation.run_batch_retarget(inputs)
    if len(made) != 4:
        raise RuntimeError('Expected four walks, got ' + str(len(made)))
    for data in made:
        anim = data.get_asset()
        if anim.get_name() not in [n + '_Sparrow' for n in NAMES] or anim.get_editor_property('skeleton') != target.get_editor_property('skeleton'):
            raise RuntimeError('Unexpected retarget output')
        anim.set_editor_property('enable_root_motion', False)
        anim.set_editor_property('force_root_lock', True)
        anim.set_editor_property('root_motion_root_lock', u.RootMotionRootLock.ANIM_FIRST_FRAME)
        save(anim)
        opts = u.AnimPoseEvaluationOptions()
        for key, value in dict(evaluation_type=u.AnimDataEvalType.COMPRESSED, should_retarget=True,
                               extract_root_motion=False, incorporate_root_motion_into_pose=False,
                               optional_skeletal_mesh=target, evaluate_curves=False).items():
            opts.set_editor_property(key, value)
        samples = []
        seconds = anim.get_play_length()
        for i in range(math.ceil(seconds * 60) + 1):
            t = min(i / 60., seconds)
            pose = u.AnimPoseExtensions.get_anim_pose_at_time(anim, t, opts)
            bones = {}
            for bone in ('root', 'pelvis', 'ball_l', 'ball_r'):
                v = u.AnimPoseExtensions.get_bone_pose(pose, bone, u.AnimPoseSpaces.WORLD).translation
                bones[bone] = [v.x, v.y, v.z]
            samples.append(dict(time=t, bones=bones))
        item = dict(package=anim.get_path_name(), seconds=seconds, samples=samples,
                    enable_root_motion=False, force_root_lock=True)
        report['clips'].append(item)
        if anim.get_name() == NAMES[0] + '_Sparrow':
            speeds = []
            for bone in ('ball_l', 'ball_r'):
                xyz = [s['bones'][bone] for s in samples]
                h = sorted(p[2] for p in xyz)[int((len(xyz)-1)*.35)]
                for i in range(1, len(samples)-1):
                    dt = samples[i+1]['time'] - samples[i-1]['time']
                    backward = -(xyz[i+1][1]-xyz[i-1][1])/dt
                    vz = (xyz[i+1][2]-xyz[i-1][2])/dt
                    if xyz[i][2] <= h and abs(vz) < 25 and backward > 30:
                        speeds.append(backward)
            if len(speeds) < 6:
                raise RuntimeError('Insufficient walk stance samples')
            ordered = sorted(speeds)
            report['walk_speed_cm_s'] = statistics.median(speeds)
            report['stance_samples'] = len(speeds)
            report['stance_p10_p90_cm_s'] = [ordered[int((len(ordered)-1)*q)] for q in (.1, .9)]
            drift = math.dist(samples[0]['bones']['pelvis'][:2], samples[-1]['bones']['pelvis'][:2])
            report['walk_pelvis_horizontal_seam_cm'] = drift
            if drift > 10:
                raise RuntimeError('Walk pelvis drifts despite locked root')
        checkpoint()
    report['status'] = 'success'

try:
    main()
except Exception:
    report.update(status='failed', error=traceback.format_exc())
finally:
    checkpoint()
if report['status'] != 'success':
    raise RuntimeError(report['error'])
