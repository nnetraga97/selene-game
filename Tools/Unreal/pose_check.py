"""For each finished hero: does each locomotion clip actually move the mesh away from its reference (T) pose, and is it
free of NaN? Report: Saved/CombatAnims/pose_check.json."""
import json, math, re
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
R = {}
ini = (ROOT / 'Config/DefaultGame.ini').read_text()
FIELDS = ('IdleLoop', 'WalkLoop', 'RunLoop', 'SprintLoop', 'RunStart', 'RunStop', 'Jump', 'Land')
for hero in ('Warrior', 'Warden', 'Sparrow', 'Aurora'):
    line = next(l for l in ini.splitlines() if l.startswith('+Roster=(Name="%s"' % hero))
    mesh = u.load_asset(re.search(r'\bMesh="([^"]+)"', line).group(1))
    out = {'mesh_skeleton': mesh.get_editor_property('skeleton').get_path_name()}
    ref = u.AnimPoseExtensions.get_reference_pose(mesh.get_editor_property('skeleton'))
    names = [str(n) for n in u.AnimPoseExtensions.get_bone_names(ref)]
    probe = [b for b in ('upperarm_l', 'upperarm_r', 'thigh_l', 'spine_02', 'UpperArm_L', 'LeftArm', 'mixamorig:LeftArm') if b in names]
    out['probe_bones'] = probe
    clips = {f: re.search(r'\b%s="([^"]+)"' % f, line) for f in FIELDS}
    bs = re.search(r'\bStrafeLocomotion="([^"]+)"', line)
    for f, m in clips.items():
        if not m: continue
        anim = u.load_asset(m.group(1))
        if not anim: out[f] = 'missing'; continue
        opts = u.AnimPoseEvaluationOptions()
        opts.set_editor_property('optional_skeletal_mesh', mesh)
        opts.set_editor_property('evaluation_type', u.AnimDataEvalType.COMPRESSED)
        t = anim.get_play_length() * 0.3
        pose = u.AnimPoseExtensions.get_anim_pose_at_time(anim, t, opts)
        diffs, nan = [], False
        for b in probe:
            a = u.AnimPoseExtensions.get_bone_pose(pose, b, u.AnimPoseSpaces.LOCAL).rotation
            r = u.AnimPoseExtensions.get_bone_pose(ref, b, u.AnimPoseSpaces.LOCAL).rotation
            vals = [a.x, a.y, a.z, a.w]
            if any(v != v for v in vals): nan = True; continue
            dot = abs(a.x * r.x + a.y * r.y + a.z * r.z + a.w * r.w)
            diffs.append(round(math.degrees(2 * math.acos(min(1.0, dot))), 1))
        out[f] = dict(clip=anim.get_name(), skeleton_ok=anim.get_editor_property('skeleton') == mesh.get_editor_property('skeleton'),
                      deg_from_ref=diffs, nan=nan)
    R[hero] = out
(ROOT / 'Saved/CombatAnims').mkdir(parents=True, exist_ok=True)
(ROOT / 'Saved/CombatAnims/pose_check.json').write_text(json.dumps(R, indent=1))
