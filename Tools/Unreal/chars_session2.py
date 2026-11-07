"""Session 2 scoped gates, each in a fresh guarded Unreal process."""
import hashlib
import json
import math
import os
from pathlib import Path
import runpy
import statistics
import traceback
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
OUT = ROOT / 'Saved/Chars/session-2'
STAGE = os.environ['SELENE_CHARS_STAGE']
ACTION = STAGE.removesuffix('-retry')
LIB = u.EditorAssetLibrary
HEROES = {'Fixer': 'night-market-fixer', 'Courier': 'scooter-courier'}
BASES = ['/Game/Selene/Characters/' + n for n in HEROES]
report = dict(status='running', stage=STAGE, heroes={})

def checkpoint():
    (OUT / (STAGE + '.json')).write_text(json.dumps(report, indent=2) + '\n')

def mesh_path(slug):
    return '/Game/Assets/' + slug + '/' + slug + '/SkeletalMeshes/' + slug

def vec(v):
    return [v.x, v.y, v.z]

def options(mesh, raw=False, unlocked=True):
    opts = u.AnimPoseEvaluationOptions()
    for k, v in dict(optional_skeletal_mesh=mesh, evaluation_type=u.AnimDataEvalType.RAW if raw else u.AnimDataEvalType.COMPRESSED,
                     should_retarget=True, extract_root_motion=False,
                     incorporate_root_motion_into_pose=unlocked, evaluate_curves=False).items():
        opts.set_editor_property(k, v)
    return opts

def pose_at(anim, time, opts):
    u.AnimPoseExtensions.get_anim_pose_at_time(anim, time, opts)
    pose = u.AnimPoseExtensions.get_anim_pose_at_time(anim, time, opts)
    if not u.AnimPoseExtensions.is_valid(pose):
        raise RuntimeError('Invalid pose: ' + anim.get_path_name())
    return pose

def position(pose, bone):
    return vec(u.AnimPoseExtensions.get_bone_pose(pose, bone, u.AnimPoseSpaces.WORLD).translation)

def approved(stage):
    data = json.loads((OUT / (stage + '.json')).read_text())
    if data['status'] != 'success' or (OUT / (stage + '-exit.txt')).read_text().strip() != '0':
        raise RuntimeError('Prior gate failed: ' + stage)
    return data

def cleanup():
    registry = u.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(True)
    report['references'] = {}
    report['external_references'] = {}
    paths = [p for base in BASES for p in LIB.list_assets(base, recursive=True, include_folder=False)]
    if not paths:
        raise RuntimeError('No generated assets to audit; do not replay')
    for path in paths:
        refs = [str(x) for x in LIB.find_package_referencers_for_asset(path, load_assets_to_confirm=True)]
        report['references'][path] = refs
        outside = [p for p in refs if not any(p.split('.')[0].startswith(b + '/') for b in BASES)]
        if outside:
            report['external_references'][path] = outside
    checkpoint()
    if report['external_references']:
        raise RuntimeError('External references found; no deletion authorized')
    for name, slug in HEROES.items():
        mesh = u.load_asset(mesh_path(slug))
        anim = u.load_asset('/Game/Selene/Characters/' + name + '/Anims/MM_Idle_' + name)
        if not anim and ACTION == 'cleanup':
            report['heroes'][name] = json.loads((OUT/'cleanup.json').read_text())['heroes'][name]
            continue
        pose = pose_at(anim, .5, options(mesh, raw=True))
        q = u.AnimPoseExtensions.get_ref_bone_pose(pose, 'mixamorig_Hips', u.AnimPoseSpaces.WORLD).rotation
        bounds = mesh.get_bounds()
        height = 2*bounds.box_extent.z
        expected = {'Fixer':170., 'Courier':178.}[name]
        if abs(height-expected) > .01:
            raise RuntimeError('Unexpected mesh height: ' + name)
        report['heroes'][name] = dict(mesh=mesh_path(slug), height_cm=height,
            bounds_min_z_cm=bounds.origin.z-bounds.box_extent.z, reference_root_quaternion=[q.x,q.y,q.z,q.w])
    checkpoint()
    report['deleted_directories'] = []
    for base in BASES:
        if not LIB.delete_directory(base):
            raise RuntimeError('Directory deletion failed: ' + base)
        report['deleted_directories'].append(base)
        checkpoint()
        if LIB.list_assets(base, recursive=True, include_folder=False):
            raise RuntimeError('Generated assets remain: ' + base)

def create():
    audited = approved('cleanup-retry' if STAGE.endswith('-retry') else 'cleanup')
    for base in BASES:
        if LIB.list_assets(base, recursive=True, include_folder=False):
            raise RuntimeError('Destination is not empty: ' + base)
    for name, slug in HEROES.items():
        previous = json.loads((ROOT / 'Saved/Chars/session-1' / (name + '-base.json')).read_text())
        expected = previous['retargeted']
        if len(expected) != 21 or any(not p.endswith('_' + name) for p in expected):
            raise RuntimeError('Invalid canonical manifest')
        os.environ.update(SELENE_CHAR=name, SELENE_CHAR_MESH=mesh_path(slug), SELENE_CHAR_POSE_YAW='-90',
            SELENE_CHAR_BIND_QUAT=json.dumps(audited['heroes'][name]['reference_root_quaternion']),
            SELENE_CHAR_EXPECTED_PACKAGES=json.dumps(expected), SELENE_STAGE_REPORT=str(OUT / (name + ('-base-retry.json' if STAGE.endswith('-retry') else '-base.json'))))
        runpy.run_path(str(ROOT / 'Tools/Unreal/character_retarget.py'), run_name='__main__')
        base = '/Game/Selene/Characters/' + name
        # Batch retarget returns exact names before the registry has necessarily indexed every new save.
        actual = sorted('/Game/' + str(p.relative_to(ROOT/'Content').with_suffix(''))
                        for p in (ROOT/'Content'/base[6:]).rglob('*.uasset'))
        expected_all = sorted(expected + [base+'/IK_Manny', base+'/IK_'+name, base+'/RTG_Manny_To_'+name])
        report['heroes'][name] = dict(packages=actual, expected_packages=expected_all)
        checkpoint()
        if actual != expected_all:
            raise RuntimeError('Unexpected generated package inventory: ' + name)
        report['heroes'][name] = dict(packages=actual, canonical=True)
        checkpoint()

def inventory():
    for name in HEROES:
        base = '/Game/Selene/Characters/' + name
        report['heroes'][name] = dict(library_paths=list(LIB.list_assets(base, recursive=True, include_folder=False)),
            disk_packages=sorted('/Game/' + str(p.relative_to(ROOT/'Content').with_suffix(''))
                for p in (ROOT/'Content'/base[6:]).rglob('*.uasset')))

def facing():
    approved('create-retry')
    for name, slug in HEROES.items():
        mesh = u.load_asset(mesh_path(slug))
        item = dict(clips={})
        report['heroes'][name] = item
        for role, asset in [('idle', 'MM_Idle_'), ('walk', 'MF_Unarmed_Walk_Fwd_')]:
            anim = u.load_asset('/Game/Selene/Characters/' + name + '/Anims/' + asset + name)
            opts = options(mesh, raw=False, unlocked=False)
            samples = []
            count = math.ceil(anim.get_play_length()*60)
            for i in range(count+1):
                t = anim.get_play_length()*i/count
                pose = pose_at(anim, t, opts)
                bones = {b: position(pose, b) for b in ['mixamorig_Hips','mixamorig_Head','mixamorig_HeadTop_End',
                    'mixamorig_LeftFoot','mixamorig_RightFoot','mixamorig_LeftToeBase','mixamorig_RightToeBase',
                    'mixamorig_LeftShoulder','mixamorig_RightShoulder']}
                samples.append(dict(time=t,bones=bones))
            facings = [[s['bones']['mixamorig_'+side+'ToeBase'][k]-s['bones']['mixamorig_'+side+'Foot'][k]
                        for k in range(2)] for s in samples for side in ['Left','Right']]
            f = [statistics.mean(v[k] for v in facings) for k in range(2)]
            norm = math.hypot(*f)
            f = [v/norm for v in f]
            entry = dict(package=anim.get_path_name(), samples=samples, mean_toe_facing_xy=f)
            item['clips'][role] = entry
            checkpoint()
            if f[1] < .9:
                raise RuntimeError(name + ' ' + role + ' does not face +Y after yaw fix')
            if role == 'walk':
                velocities = []
                for side in ['Left','Right']:
                    xyz = [s['bones']['mixamorig_'+side+'ToeBase'] for s in samples]
                    low = sorted(v[2] for v in xyz)[int((len(xyz)-1)*.35)]
                    for i in range(1,len(samples)-1):
                        dt = samples[i+1]['time']-samples[i-1]['time']
                        v = [(xyz[i+1][k]-xyz[i-1][k])/dt for k in range(3)]
                        if xyz[i][2] <= low and abs(v[2]) < 25 and math.hypot(v[0],v[1]) > 30:
                            velocities.append([-v[0],-v[1]])
                if len(velocities) < 6:
                    raise RuntimeError('Insufficient base walk stance samples: ' + name)
                travel = [statistics.median(v[k] for v in velocities) for k in range(2)]
                norm = math.hypot(*travel)
                direction = [v/norm for v in travel]
                cosine = sum(a*b for a,b in zip(direction,f))
                entry.update(inferred_travel_xy=direction, facing_travel_cosine=cosine, stance_samples=len(velocities))
                checkpoint()
                if cosine < .9 or direction[1] < .9:
                    raise RuntimeError('Facing/travel mismatch persists: ' + name)

try:
    if (OUT / (STAGE + '.json')).exists():
        raise RuntimeError('Report exists; do not replay')
    if ACTION not in ('cleanup','create','facing','inventory'):
        raise RuntimeError('Stage not yet implemented: ' + STAGE)
    globals()[ACTION]()
    report['status'] = 'success'
except Exception:
    report.update(status='failed', error=traceback.format_exc())
finally:
    checkpoint()
if report['status'] != 'success':
    raise RuntimeError(report['error'])
