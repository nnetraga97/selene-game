"""Retarget the template Manny locomotion onto a Mixamo-skeleton character (headless, -nullrhi is fine).

Environment: SELENE_CHAR (name, e.g. Champion), SELENE_CHAR_MESH (skeletal mesh asset path).
The mesh normally faces Unreal +Y like Manny. SELENE_CHAR_POSE_YAW optionally aligns a differently
oriented mesh in the target retarget pose (degrees about world Z; no mesh transform/scale edit).
For this opt-in correction, SELENE_CHAR_BIND_QUAT can supply the audited mesh reference root
quaternion as JSON [x,y,z,w], allowing regeneration without loading an existing output asset.
Otherwise an existing MM_Idle_<name> supplies it.
Creates under /Game/Selene/Characters/<name>: IK_Manny, IK_<name>, RTG_Manny_To_<name>, and Anims/ with
ABP_Unarmed's idle/walk/jog anims + blend space retargeted (suffix _<name>). Writes Saved/Characters/<name>/retarget.json.
"""
import json
import os
import math

import unreal as u

ROOT = u.Paths.convert_relative_path_to_full(u.Paths.project_dir())
NAME = os.environ["SELENE_CHAR"]
CHAMP = os.environ["SELENE_CHAR_MESH"]
if NAME != "Fox" or CHAMP != "/Game/Assets/fox-spirit-sovereign/fox-spirit-sovereign/SkeletalMeshes/fox-spirit-sovereign":
    raise RuntimeError("This script is scoped only to Fox")
CANONICAL_BASE = "/Game/Selene/Characters/" + NAME
BASE = CANONICAL_BASE
MANNY = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"
ABP = "/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed"
report = {"status": "failed"}
lib = u.EditorAssetLibrary
tools = u.AssetToolsHelpers.get_asset_tools()


def fresh(name, cls, factory):
    """Reuse an existing asset (it is reset below; referenced assets cannot be deleted) or create it."""
    path = BASE + "/" + name
    if lib.does_asset_exist(path):
        return u.load_asset(path)
    asset = tools.create_asset(name, BASE, cls, factory)
    if not asset:
        raise RuntimeError("Could not create " + path)
    return asset


MIXAMO_CHAINS = [("Spine", "Spine", "Spine2"), ("Neck", "Neck", "Neck"), ("Head", "Head", "Head")] + [
    (side + chain, side_bone + start, side_bone + end)
    for side, side_bone in (("Left", "Left"), ("Right", "Right"))
    for chain, start, end in (
        ("Leg", "UpLeg", "Foot"), ("Foot", "ToeBase", "ToeBase"), ("Clavicle", "Shoulder", "Shoulder"),
        ("Arm", "Arm", "Hand"), ("Thumb", "HandThumb1", "HandThumb3"), ("Index", "HandIndex1", "HandIndex3"),
        ("Middle", "HandMiddle1", "HandMiddle3"), ("Ring", "HandRing1", "HandRing3"), ("Pinky", "HandPinky1", "HandPinky3"))]


def mixamo_chains(c):
    root = "mixamorig_Hips"
    if str(c.get_retarget_root()) != root:
        c.set_retarget_root(root)
    if str(c.get_retarget_root()) != root:
        raise RuntimeError("Required Mixamo root is missing: " + root)
    existing = {str(chain.chain_name): chain.chain_name for chain in c.get_retarget_chains()}
    for name, start, end in MIXAMO_CHAINS:
        start, end = "mixamorig_" + start, "mixamorig_" + end
        if name in existing:
            chain = existing[name]
            if str(c.get_retarget_chain_start_bone(chain)) == start and str(c.get_retarget_chain_end_bone(chain)) == end:
                continue
            c.remove_retarget_chain(chain)
        c.add_retarget_chain(name, start, end, "")
        if str(c.get_retarget_chain_start_bone(name)) != start or str(c.get_retarget_chain_end_bone(name)) != end:
            raise RuntimeError(f"Missing Mixamo topology for {name} ({start} to {end})")


def ik_rig(name, mesh):
    rig = fresh(name, u.IKRigDefinition, u.IKRigDefinitionFactory())
    c = u.IKRigController.get_controller(rig)
    if not c.set_skeletal_mesh(mesh):
        raise RuntimeError(name + ": skeletal mesh rejected")
    while c.get_num_solvers() > 0:  # reruns: avoid stacking a second auto FBIK solver
        c.remove_solver(0)
    if name == "IK_Fox" or not c.apply_auto_generated_retarget_definition():
        # Extra secondary-physics bones (braid/skirt/hair chains) stop the template matcher recognising the
        # Mixamo skeleton, so define the body chains by bone name (same map the auto rig produced for Angel).
        mixamo_chains(c)
        report.setdefault("manual_chains", []).append(name)
    try:
        if name != "IK_Fox": c.apply_auto_fbik()
    except Exception as exc:  # FK retargeting still works without the FBIK solver
        report.setdefault("warnings", []).append("%s: auto FBIK failed: %s" % (name, exc))
    names = [ch.chain_name for ch in c.get_retarget_chains()]
    chains = [(str(n), str(c.get_retarget_chain_start_bone(n)), str(c.get_retarget_chain_end_bone(n))) for n in names]
    report[name] = {"retarget_root": str(c.get_retarget_root()), "chains": chains}
    return rig


def main():
    if lib.does_directory_exist(BASE):
        raise RuntimeError("Fox output already exists; do not replay")
    champ = u.load_asset(CHAMP)
    manny = u.load_asset(MANNY)
    if not champ or not manny:
        raise RuntimeError("Missing champion or Manny mesh")
    src = ik_rig("IK_Manny", manny)
    tgt = ik_rig("IK_" + NAME, champ)

    rtg = fresh("RTG_Manny_To_" + NAME, u.IKRetargeter, u.IKRetargetFactory())
    r = u.IKRetargeterController.get_controller(rtg)
    S, T = u.RetargetSourceOrTarget.SOURCE, u.RetargetSourceOrTarget.TARGET
    r.set_ik_rig(S, src)
    r.set_ik_rig(T, tgt)
    r.set_preview_mesh(S, manny)
    r.set_preview_mesh(T, champ)
    r.remove_all_ops()
    r.add_default_ops()
    # Her skeleton has no root bone: the auto rig makes mixamorig_Hips the root-motion bone, so the
    # Root Motion op would stack Manny's pelvis height onto the hips again (~1 m float on root-motion
    # anims). Locomotion comes from CharacterMovement, so disable it.
    rm = r.get_index_of_op_by_name("Root Motion")
    if rm >= 0:
        r.set_retarget_op_enabled(rm, False)
    report["ops"] = [(str(r.get_op_name(i)), r.get_retarget_op_enabled(i)) for i in range(r.get_num_retarget_ops())]
    r.assign_ik_rig_to_all_ops(S, src)
    r.assign_ik_rig_to_all_ops(T, tgt)
    r.auto_map_chains(u.AutoMapChainType.FUZZY, True)
    # Tripo characters bind in A/T-pose; align their chains to Manny's reference pose directions.
    pose = r.create_retarget_pose("AlignedToManny", T)
    r.set_current_retarget_pose(pose, T)
    yaw = float(os.environ.get("SELENE_CHAR_POSE_YAW", "0"))
    if yaw:
        if os.environ.get("SELENE_CHAR_BIND_QUAT"):
            values = json.loads(os.environ["SELENE_CHAR_BIND_QUAT"])
            if len(values) != 4 or not all(math.isfinite(v) for v in values) or abs(sum(v*v for v in values)-1) > .0001:
                raise RuntimeError("Invalid audited bind quaternion")
            q = u.Quat(*values)
        else:
            idle = u.load_asset(CANONICAL_BASE + "/Anims/MM_Idle_" + NAME)
            if not idle:
                raise RuntimeError("Pose-yaw alignment requires an audited bind quaternion or existing base idle")
            opts = u.AnimPoseEvaluationOptions()
            opts.set_editor_property("optional_skeletal_mesh", champ)
            p = u.AnimPoseExtensions.get_anim_pose_at_time(idle, .5, opts)
            q = u.AnimPoseExtensions.get_ref_bone_pose(p, "mixamorig_Hips", u.AnimPoseSpaces.WORLD).rotation
        def mul(a, b):
            x,y,z,w = a; X,Y,Z,W = b
            return (w*X+x*W+y*Z-z*Y, w*Y-x*Z+y*W+z*X,
                    w*Z+x*Y-y*X+z*W, w*W-x*X-y*Y-z*Z)
        # Retarget pose deltas are local. Convert the desired component-Z turn through the bind quaternion.
        bind = (q.x,q.y,q.z,q.w)
        half = math.radians(yaw)/2
        delta = mul(mul((-q.x,-q.y,-q.z,q.w), (0,0,math.sin(half),math.cos(half))), bind)
        r.set_rotation_offset_for_retarget_pose_bone("mixamorig_Hips", u.Quat(*delta), T)
        report["pose_yaw_alignment"] = {"world_yaw_degrees": yaw, "reference_root_quaternion": bind, "local_delta_quaternion": delta}
    r.auto_align_all_bones(T)
    report["mapping"] = {ch[0]: str(r.get_source_chain(ch[0])) for ch in report["IK_" + NAME]["chains"]}
    required = {"Spine", "LeftLeg", "RightLeg", "LeftArm", "RightArm"}
    if any(report["mapping"].get(chain) in {None, "", "None"} for chain in required):
        raise RuntimeError("Required locomotion chains are unmapped")
    for asset in (src, tgt, rtg):
        if not lib.save_loaded_asset(asset):
            raise RuntimeError("Could not save " + asset.get_path_name())

    inputs = u.IKRetargetBatchOperationInputs()
    inputs.set_editor_property("assets_to_retarget", [u.AssetRegistryHelpers.get_asset_registry().get_asset_by_object_path(ABP + ".ABP_Unarmed")])
    inputs.set_editor_property("source_mesh", manny)
    inputs.set_editor_property("target_mesh", champ)
    inputs.set_editor_property("ik_retarget_asset", rtg)
    inputs.set_editor_property("suffix", "_" + NAME)
    inputs.set_editor_property("target_path", BASE + "/Anims")
    inputs.set_editor_property("include_referenced_assets", True)
    inputs.set_editor_property("overwrite_existing_files", False)
    made = u.IKRetargetBatchOperation.run_batch_retarget(inputs)
    report["retargeted"] = sorted(str(a.package_name) for a in made)
    if os.environ.get("SELENE_CHAR_EXPECTED_PACKAGES"):
        expected = sorted(json.loads(os.environ["SELENE_CHAR_EXPECTED_PACKAGES"]))
        if report["retargeted"] != expected:
            raise RuntimeError("Retarget output does not match exact canonical package names")
    for a in made:
        if not lib.save_asset(str(a.package_name), only_if_is_dirty=False):
            raise RuntimeError("Could not save " + str(a.package_name))
    report["status"] = "success" if made else "failed: batch retarget produced nothing"


try:
    main()
except Exception as exc:  # report, then fail the commandlet
    import traceback
    report["error"] = str(exc)
    report["traceback"] = traceback.format_exc()
out = os.path.join(ROOT, "Saved", "Characters", NAME)
os.makedirs(out, exist_ok=True)
report["invocation"] = os.environ.get("SELENE_STAGE_ID")
with open(os.environ.get("SELENE_STAGE_REPORT") or os.path.join(out, "retarget.json"), "w") as f:
    json.dump(report, f, indent=2)
u.log("CHARACTER_RETARGET " + report["status"])
if report["status"] != "success":
    raise RuntimeError(report.get("error", report["status"]))
