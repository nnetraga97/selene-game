"""Combat animation pass for the finished heroes (Sparrow, Warrior, Warden).
1. Warrior: retarget the extra Aurora clips it needs (hit reacts, death, turns, moving attacks, directional jogs).
2. Warden: build RTG_Aurora_To_Warden from the Warrior's Aurora retargeter and give Warden the whole Aurora sword set.
3. Measure each hero's forward jog ground speed from foot contacts.
4. Build directional strafe blend spaces (Direction -180..180, Speed 0..jog) for Sparrow, Warrior and Warden.
Re-runnable: existing clips are kept; blend spaces are rebuilt. Report: Saved/CombatAnims/report.json."""
import json, math, statistics, traceback
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
OUT = ROOT / 'Saved/CombatAnims'; OUT.mkdir(parents=True, exist_ok=True)
LIB = u.EditorAssetLibrary; TOOLS = u.AssetToolsHelpers.get_asset_tools()
AURORA = '/Game/ParagonAurora/Characters/Heroes/Aurora/'
SPARROW = '/Game/ParagonSparrow/Characters/Heroes/Sparrow/'
R = {'status': 'running'}

BASE_SET = ['Idle', 'Jog_Fwd', 'Jog_Fwd_Start', 'Jog_Fwd_Stop', 'Jog_Fwd_Pivot180', 'Jump_Start', 'Jump_Apex', 'Jump_Land', 'Jump_Recovery',
            'Primary_Attack_A', 'Primary_Attack_B', 'Primary_Attack_C', 'Primary_Attack_Fast_A', 'Primary_Attack_Fast_B', 'Primary_Attack_Fast_C',
            'Primary_Attack_Fast_D', 'Ability_Q', 'Ability_E', 'Ability_R', 'Level_Start', 'Melee_Attack_Air']
EXTRA = ['HitReact_Front', 'HitReact_Back', 'HitReact_Left', 'HitReact_Right', 'Death', 'Turn_Left_90', 'Turn_Right_90',
         'Primary_Attack_A_InMotion', 'Primary_Attack_B_InMotion', 'Primary_Attack_C_InMotion', 'Ability_Q_InMotion', 'Ability_E_InMotion',
         'Jog_Bwd', 'Jog_Left', 'Jog_Right', 'Stun_Loop', 'Knockback_Fwd',
         'Ability_RMB_Fwd', 'Ability_RMB_Bwd', 'Ability_RMB_Left', 'Ability_RMB_Right']
HEROES = {
    'Warrior': {'mesh': '/Game/Assets/eclipse-warrior/eclipse-warrior/SkeletalMeshes/eclipse-warrior', 'base': '/Game/Selene/Characters/Warrior'},
    'Warden': {'mesh': '/Game/Assets/eclipse-warden/eclipse-warden/SkeletalMeshes/eclipse-warden', 'base': '/Game/Selene/Characters/Warden'},
}


def save(a):
    if not LIB.save_loaded_asset(a, only_if_is_dirty=False): raise RuntimeError('save failed ' + a.get_path_name())


def checkpoint(): (OUT / 'report.json').write_text(json.dumps(R, indent=1, default=str))


def warden_retargeter():
    base = HEROES['Warden']['base']; path = base + '/RTG_Aurora_To_Warden'
    if LIB.does_asset_exist(path): return u.load_asset(path)
    src_rtg = HEROES['Warrior']['base'] + '/RTG_Aurora_To_Warrior'
    rtg = LIB.duplicate_asset(src_rtg, path)
    if not rtg: raise RuntimeError('duplicate failed')
    r = u.IKRetargeterController.get_controller(rtg)
    T = u.RetargetSourceOrTarget.TARGET
    tgt = u.load_asset(base + '/IK_Warden'); mesh = u.load_asset(HEROES['Warden']['mesh'])
    r.set_ik_rig(T, tgt); r.set_preview_mesh(T, mesh)
    r.assign_ik_rig_to_all_ops(T, tgt)
    r.auto_map_chains(u.AutoMapChainType.EXACT, True)
    pose = r.create_retarget_pose('AlignedToAurora', T); r.set_current_retarget_pose(pose, T); r.auto_align_all_bones(T)
    pelvis = r.get_op_controller(r.get_index_of_op_by_name('Pelvis Motion')); root = r.get_op_controller(r.get_index_of_op_by_name('Root Motion'))
    pelvis.set_target_pelvis_bone('pelvis'); root.set_target_root_bone('root'); root.set_target_pelvis_bone('pelvis')
    save(rtg)
    R['warden_rtg_chains'] = {n: str(r.get_source_chain(n)) for n in ['Spine', 'LeftLeg', 'RightLeg', 'LeftArm', 'RightArm', 'Head']}
    return rtg


def retarget(hero, rtg, clips):
    h = HEROES[hero]; dest = h['base'] + '/Anims/Aurora'; suffix = '_' + hero
    src = u.load_asset(AURORA + 'Meshes/Aurora'); mesh = u.load_asset(h['mesh'])
    todo, missing = [], []
    for n in clips:
        if LIB.does_asset_exist(f'{dest}/{n}{suffix}'): continue
        d = LIB.find_asset_data(AURORA + 'Animations/' + n)
        if d.is_valid() and isinstance(d.get_asset(), u.AnimSequence): todo.append(d)
        else: missing.append(n)
    R.setdefault('missing', {})[hero] = missing
    made = []
    if todo:
        inp = u.IKRetargetBatchOperationInputs()
        for k, v in dict(assets_to_retarget=todo, source_mesh=src, target_mesh=mesh, ik_retarget_asset=rtg, target_path=dest, suffix=suffix,
                         include_referenced_assets=False, overwrite_existing_files=False, use_source_path=False).items():
            inp.set_editor_property(k, v)
        made = u.IKRetargetBatchOperation.run_batch_retarget(inp)
    for d in made:
        a = d.get_asset()
        if isinstance(a, u.AnimSequence):
            a.set_editor_property('enable_root_motion', False); a.set_editor_property('force_root_lock', True)
            a.set_editor_property('root_motion_root_lock', u.RootMotionRootLock.REF_POSE)
            save(a)
    R.setdefault('made', {})[hero] = [str(d.asset_name) for d in made]
    # Load + save every clip so curve names land on the skeleton (avoids a -game PostLoad crash), then the skeleton.
    for p in LIB.list_assets(dest, recursive=True):
        a = u.load_asset(p)
        if isinstance(a, u.AnimSequence): save(a)
    skel = mesh.get_editor_property('skeleton'); save(skel)
    checkpoint()


def jog_speed(clip_path, mesh):
    a = u.load_asset(clip_path); opts = u.AnimPoseEvaluationOptions()
    for k, v in dict(evaluation_type=u.AnimDataEvalType.RAW, should_retarget=True, extract_root_motion=False,
                     incorporate_root_motion_into_pose=True, optional_skeletal_mesh=mesh, evaluate_curves=False).items():
        opts.set_editor_property(k, v)
    L = a.get_play_length(); times = [min(i / 60, L) for i in range(math.ceil(L * 60) + 1)]
    rows = [{b: u.AnimPoseExtensions.get_bone_pose(u.AnimPoseExtensions.get_anim_pose_at_time(a, t, opts), b, u.AnimPoseSpaces.WORLD).translation
             for b in ['ball_l', 'ball_r']} for t in times]
    cand = []
    for b in ['ball_l', 'ball_r']:
        xyz = [[r[b].x, r[b].y, r[b].z] for r in rows]; h = sorted(p[2] for p in xyz)[int((len(xyz) - 1) * .35)]
        for i in range(1, len(rows) - 1):
            dt = times[i + 1] - times[i - 1]; v = [(xyz[i + 1][k] - xyz[i - 1][k]) / dt for k in range(3)]
            if xyz[i][2] <= h and abs(v[2]) < 25: cand.append(math.hypot(v[0], v[1]))
    return statistics.median(cand) if cand else None


def strafe_space(name, folder, skeleton, idle, fwd, bwd, left, right, speed):
    path = f'{folder}/{name}'
    if LIB.does_asset_exist(path):
        bs = u.load_asset(path)   # update in place (delete + recreate fails while the asset is loaded)
    else:
        f = u.BlendSpaceFactoryNew(); f.set_editor_property('target_skeleton', skeleton)
        bs = TOOLS.create_asset(name, folder, u.BlendSpace, f)
    p0 = u.BlendParameter(); p0.set_editor_property('display_name', 'Direction'); p0.set_editor_property('min', -180.0); p0.set_editor_property('max', 180.0); p0.set_editor_property('grid_num', 4)
    p1 = u.BlendParameter(); p1.set_editor_property('display_name', 'Speed'); p1.set_editor_property('min', 0.0); p1.set_editor_property('max', float(speed)); p1.set_editor_property('grid_num', 2)
    p2 = u.BlendParameter()
    bs.set_editor_property('blend_parameters', [p0, p1, p2])
    clips = {k: u.load_asset(v) for k, v in dict(idle=idle, fwd=fwd, bwd=bwd, left=left, right=right).items()}
    missing = [k for k, v in clips.items() if not v]
    if missing: raise RuntimeError(f'{name}: missing {missing}')
    samples = []
    def add(anim, x, y):
        s = u.BlendSample(); s.set_editor_property('animation', anim); s.set_editor_property('sample_value', u.Vector(x, y, 0)); s.set_editor_property('rate_scale', 1.0)
        samples.append(s)
    for x in (-180.0, -90.0, 0.0, 90.0, 180.0): add(clips['idle'], x, 0.0)
    add(clips['fwd'], 0.0, speed); add(clips['left'], -90.0, speed); add(clips['right'], 90.0, speed)
    add(clips['bwd'], -180.0, speed); add(clips['bwd'], 180.0, speed)
    bs.set_editor_property('sample_data', samples)
    # No speed-axis scaling (idle samples sit at speed 0) and no marker sync (mismatched jog markers): both gave NaN poses.
    bs.set_editor_property('allow_marker_based_sync', False)
    # Script-set samples leave the runtime grid empty (the blend space then plays the T-pose): rebuild it.
    u.SeleneAnimTools.rebuild_blend_space(bs)
    save(bs)
    return {'path': bs.get_path_name(), 'samples': len(bs.get_editor_property('sample_data')), 'speed': speed}


def main():
    warrior_rtg = u.load_asset(HEROES['Warrior']['base'] + '/RTG_Aurora_To_Warrior')
    retarget('Warrior', warrior_rtg, EXTRA)
    retarget('Warden', warden_retargeter(), BASE_SET + EXTRA)
    R['jog'] = {}
    for hero in ('Warrior', 'Warden'):
        a = HEROES[hero]['base'] + f'/Anims/Aurora/Jog_Fwd_{hero}'
        R['jog'][hero] = jog_speed(a, u.load_asset(HEROES[hero]['mesh']))
    sparrow_mesh = u.load_asset(SPARROW + 'Meshes/Sparrow')
    R['jog']['Sparrow'] = jog_speed(SPARROW + 'Animations/Jog_Fwd', sparrow_mesh)
    aurora_mesh = u.load_asset(AURORA + 'Meshes/Aurora')
    R['jog']['Aurora'] = jog_speed(AURORA + 'Animations/Jog_Fwd', aurora_mesh)
    checkpoint()
    R['blendspaces'] = {}
    for hero in ('Warrior', 'Warden'):
        A = HEROES[hero]['base'] + '/Anims/Aurora/'; s = '_' + hero
        skel = u.load_asset(HEROES[hero]['mesh']).get_editor_property('skeleton')
        R['blendspaces'][hero] = strafe_space(f'BS_Strafe_{hero}', HEROES[hero]['base'] + '/Anims', skel,
                                              A + 'Idle' + s, A + 'Jog_Fwd' + s, A + 'Jog_Bwd' + s, A + 'Jog_Left' + s, A + 'Jog_Right' + s,
                                              round(R['jog'][hero] or 440.0))
    R['blendspaces']['Sparrow'] = strafe_space('BS_Strafe_Sparrow', '/Game/Selene/Characters/Sparrow/Anims', sparrow_mesh.get_editor_property('skeleton'),
                                               SPARROW + 'Animations/idle', SPARROW + 'Animations/Jog_Fwd', SPARROW + 'Animations/Jog_Bwd',
                                               SPARROW + 'Animations/Jog_Left', SPARROW + 'Animations/Jog_Right', round(R['jog']['Sparrow'] or 500.0))
    A = AURORA + 'Animations/'
    R['blendspaces']['Aurora'] = strafe_space('BS_Strafe_Aurora', '/Game/Selene/Characters/Aurora/Anims', aurora_mesh.get_editor_property('skeleton'),
                                              A + 'Idle', A + 'Jog_Fwd', A + 'Jog_Bwd', A + 'Jog_Left', A + 'Jog_Right', round(R['jog']['Aurora'] or 440.0))
    R['status'] = 'success'


try: main()
except Exception: R.update(status='failed', error=traceback.format_exc())
checkpoint()
if R['status'] != 'success': raise RuntimeError(R['error'])
