"""Scoped Fixer/Courier integration; reports are immutable between stages."""
import json
import math
import os
from pathlib import Path
import runpy
import traceback
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
OUT = ROOT / 'Saved/Chars/session-1'
STAGE = os.environ['SELENE_CHARS_STAGE']
LIB = u.EditorAssetLibrary
HEROES = {'Fixer': ('night-market-fixer', 170.0), 'Courier': ('scooter-courier', 178.0)}
report = dict(status='running', stage=STAGE, heroes={})


def checkpoint():
    (OUT / (STAGE + '.json')).write_text(json.dumps(report, indent=2) + '\n')


def vector(v):
    return [v.x, v.y, v.z]


def mesh_path(slug):
    return '/Game/Assets/' + slug + '/' + slug + '/SkeletalMeshes/' + slug


def preflight():
    for name, (slug, height) in HEROES.items():
        mesh = u.load_asset(mesh_path(slug))
        if not mesh:
            raise RuntimeError('Missing mesh: ' + name)
        bounds = mesh.get_bounds()
        component = u.new_object(u.SkeletalMeshComponent)
        component.set_skeletal_mesh_asset(mesh)
        bones = [str(component.get_bone_name(i)) for i in range(component.get_num_bones())]
        positions = {b: vector(component.get_socket_transform(b, u.RelativeTransformSpace.RTS_COMPONENT).translation)
                     for b in bones}
        report['heroes'][name] = dict(mesh=mesh_path(slug), height_cm=2*bounds.box_extent.z,
            origin_cm=vector(bounds.origin), extent_cm=vector(bounds.box_extent), bones=bones,
            reference_positions_cm=positions, expected_height_cm=height,
            materials=[str(m.material_interface.get_path_name()) for m in mesh.get_editor_property('materials')])
        checkpoint()
        if abs(2*bounds.box_extent.z-height) > height*.05:
            raise RuntimeError('Mesh height does not match delivery; STOP without rescaling: ' + name)


def options(mesh, raw=True, unlocked=True):
    opts = u.AnimPoseEvaluationOptions()
    for k, v in dict(optional_skeletal_mesh=mesh, evaluation_type=u.AnimDataEvalType.RAW if raw else u.AnimDataEvalType.COMPRESSED,
                     should_retarget=True, extract_root_motion=False,
                     incorporate_root_motion_into_pose=unlocked, evaluate_curves=False).items():
        opts.set_editor_property(k, v)
    return opts


def pose_at(anim, time, opts):
    # First AnimPose evaluation can initialize compression and return a reference pose.
    u.AnimPoseExtensions.get_anim_pose_at_time(anim, time, opts)
    return u.AnimPoseExtensions.get_anim_pose_at_time(anim, time, opts)


def create():
    pre = json.loads((OUT / 'preflight.json').read_text())
    if pre['status'] != 'success':
        raise RuntimeError('Preflight must pass')
    for name, (slug, _) in HEROES.items():
        if STAGE == 'create' and LIB.does_directory_exist('/Game/Selene/Characters/' + name):
            raise RuntimeError('Existing hero destination; do not replay: ' + name)
    for name, (slug, _) in HEROES.items():
        os.environ.update(SELENE_CHAR=name, SELENE_CHAR_MESH=mesh_path(slug),
                          SELENE_STAGE_REPORT=str(OUT / (name + ('-aligned-base.json' if STAGE == 'align' else '-base.json'))))
        if STAGE == 'align':
            os.environ['SELENE_CHAR_POSE_YAW'] = '-90'
        runpy.run_path(str(ROOT / 'Tools/Unreal/character_retarget.py'), run_name='__main__')
        mesh = u.load_asset(mesh_path(slug))
        anim = u.load_asset('/Game/Selene/Characters/' + name + '/Anims/MM_Idle_' + name)
        opts = options(mesh)
        pose = pose_at(anim, .5, opts)
        bones = ['mixamorig_Hips', 'mixamorig_Head', 'mixamorig_HeadTop_End', 'mixamorig_LeftFoot',
                 'mixamorig_RightFoot', 'mixamorig_LeftToeBase', 'mixamorig_RightToeBase',
                 'mixamorig_LeftShoulder', 'mixamorig_RightShoulder']
        report['heroes'][name] = dict(
            reference_positions_cm={b: vector(u.AnimPoseExtensions.get_ref_bone_pose(pose, b, u.AnimPoseSpaces.WORLD).translation) for b in bones},
            idle_positions_cm={b: vector(u.AnimPoseExtensions.get_bone_pose(pose, b, u.AnimPoseSpaces.WORLD).translation) for b in bones})
        checkpoint()


def diagnose():
    report['rotation_api'] = u.IKRetargeterController.set_rotation_offset_for_retarget_pose_bone.__doc__
    for name, (slug, _) in HEROES.items():
        mesh = u.load_asset(mesh_path(slug))
        anim = u.load_asset('/Game/Selene/Characters/' + name + '/Anims/MF_Unarmed_Walk_Fwd_' + name)
        opts = options(mesh)
        samples = []
        for i in range(13):
            pose = pose_at(anim, anim.get_play_length()*i/12, opts)
            samples.append({b: vector(u.AnimPoseExtensions.get_bone_pose(pose, b, u.AnimPoseSpaces.WORLD).translation)
                            for b in ['mixamorig_Hips', 'mixamorig_LeftFoot', 'mixamorig_RightFoot',
                                      'mixamorig_LeftToeBase', 'mixamorig_RightToeBase']})
        report['heroes'][name] = dict(walk_samples=samples)


try:
    if (OUT / (STAGE + '.json')).exists():
        raise RuntimeError('Report exists; do not replay')
    if STAGE == 'preflight':
        preflight()
    elif STAGE in ('create', 'align'):
        create()
    elif STAGE == 'diagnose':
        diagnose()
    else:
        raise RuntimeError('Stage not implemented: ' + STAGE)
    report['status'] = 'success'
except Exception:
    report.update(status='failed', error=traceback.format_exc())
finally:
    checkpoint()
if report['status'] != 'success':
    raise RuntimeError(report['error'])
