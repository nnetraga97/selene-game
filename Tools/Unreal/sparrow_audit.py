"""Read-only Sparrow audit; run through sparrow_session_run.sh after the game closes.

Never changes/saves an asset. NullRHI cannot establish Metal/Substrate rendering
correctness. Reports raw package hints separately from evaluated mesh/clip data.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import traceback

import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
OUT = ROOT / "Saved/Sparrow" / os.environ.get("SELENE_SPARROW_SESSION", "session-1")
REPORT = OUT / "audit.json"
BASE = "/Game/ParagonSparrow/Characters/Heroes/Sparrow"
CLIPS = (
    "idle", "idle_relaxed", "Travel_mode_Idle", "Jog_Fwd", "Jog_Fwd_Start",
    "Jog_Fwd_Stop", "Jog_Fwd_Pivot180", "Sprint_Fwd", "Sprint_Fwd_Start",
    "Sprint_Fwd_Stop", "Sprint_Fwd_Pivot180", "Jump_Start", "Jump_Apex",
    "Jump_Land", "Jump_Recovery", "Turn_Left_90", "Turn_Right_90",
    "Turn_Left_180", "Turn_Right_180",
)
report = {"status": "running", "saved_assets": [], "clips": [], "materials": [],
          "sample_hz": 60, "limitations": [
              "NullRHI does not compile or validate Metal/Substrate appearance.",
              "Bone heights are not skin/sole clearance measurements.",
              "Stance-foot estimates do not prove runtime absence of sliding.",
              "Forward axis must be visually confirmed before choosing roster speeds.",
          ]}


def checkpoint():
    REPORT.write_text(json.dumps(report, indent=2) + "\n")


def vector(v):
    values = [float(v.x), float(v.y), float(v.z)]
    if not all(math.isfinite(x) for x in values):
        raise RuntimeError("Nonfinite pose coordinate")
    return values


def asset_path(obj):
    return obj.get_path_name() if obj else None


def stats(values):
    values = sorted(values)
    if not values:
        return {"count": 0, "median_cm_s": None}
    return {"count": len(values), "median_cm_s": statistics.median(values),
            "min_cm_s": values[0], "max_cm_s": values[-1],
            "p10_cm_s": values[int((len(values) - 1) * .1)],
            "p90_cm_s": values[int((len(values) - 1) * .9)]}


def summarize(samples, feet):
    result = {}
    for bone in samples[0]["bones"]:
        points = [s["bones"][bone] for s in samples]
        delta = [points[-1][k] - points[0][k] for k in range(3)]
        result[bone] = {
            "xyz_range_cm": [[min(p[k] for p in points), max(p[k] for p in points)] for k in range(3)],
            "endpoint_delta_cm": delta,
            "net_horizontal_speed_cm_s": math.hypot(*delta[:2]) / samples[-1]["time"],
        }
    # Same stance filters as gasp_ground_speeds.py, reported for each possible
    # horizontal facing axis instead of assuming Sparrow has Manny's orientation.
    stance = {}
    for axis_name, axis, sign in (("+X", 0, 1), ("-X", 0, -1), ("+Y", 1, 1), ("-Y", 1, -1)):
        per_foot = {}
        bilateral = []
        for foot in feet:
            xyz = [s["bones"][foot] for s in samples]
            height = sorted(p[2] for p in xyz)[int((len(xyz) - 1) * .35)]
            candidates = []
            for i in range(1, len(samples) - 1):
                dt = samples[i + 1]["time"] - samples[i - 1]["time"]
                vz = (xyz[i + 1][2] - xyz[i - 1][2]) / dt
                backward = -sign * (xyz[i + 1][axis] - xyz[i - 1][axis]) / dt
                if xyz[i][2] <= height and abs(vz) < 25 and backward > 30:
                    candidates.append({"time": samples[i]["time"], "speed_cm_s": backward})
            speeds = [c["speed_cm_s"] for c in candidates]
            per_foot[foot] = {"stats": stats(speeds), "candidates": candidates}
            bilateral.extend(speeds)
        stance[axis_name] = {"bilateral": stats(bilateral), "feet": per_foot}
    return {"bones": result, "stance_by_forward_axis": stance}


def options(mesh, unlocked):
    opts = u.AnimPoseEvaluationOptions()
    for key, value in {"evaluation_type": u.AnimDataEvalType.COMPRESSED,
                       "should_retarget": True, "extract_root_motion": False,
                       "incorporate_root_motion_into_pose": unlocked,
                       "optional_skeletal_mesh": mesh, "evaluate_curves": False}.items():
        opts.set_editor_property(key, value)
    return opts


def main():
    if not (ROOT / "Selene.uproject").is_file() or REPORT.exists():
        raise RuntimeError("Wrong project or existing report; use a fresh session directory")
    OUT.mkdir(parents=True, exist_ok=True)
    mesh = u.load_asset(BASE + "/Meshes/Sparrow")
    if not isinstance(mesh, u.SkeletalMesh):
        raise RuntimeError("Default Sparrow mesh missing")
    skeleton = mesh.get_editor_property("skeleton")
    report.update(mesh=asset_path(mesh), skeleton=asset_path(skeleton),
                  physics_asset=asset_path(mesh.get_editor_property("physics_asset")))
    # A transient, unticked component gives the mesh's actual reference hierarchy,
    # excluding unused skin-only bones that exist on the shared Skeleton asset.
    component = u.SkeletalMeshComponent()
    component.set_skeletal_mesh_asset(mesh)
    mesh_bones = [str(component.get_bone_name(i)) for i in range(component.get_num_bones())]
    report["mesh_bone_hierarchy"] = [
        {"name": name, "parent": str(component.get_parent_bone(name))} for name in mesh_bones]
    report["mesh_bone_count"] = len(mesh_bones)
    report["mesh_secondary_name_candidates"] = [name for name in mesh_bones if any(
        tag in name.lower() for tag in ("hair", "ponytail", "cloth", "quiver", "strap"))]
    if hasattr(mesh, "get_bounds"):
        bounds = mesh.get_bounds()
        report["mesh_bounds_cm"] = {"origin": vector(bounds.origin), "box_extent": vector(bounds.box_extent),
                                    "height": float(bounds.box_extent.z * 2)}
    else:
        report["mesh_bounds_cm"] = None
        report["limitations"].append("Mesh.get_bounds not exposed; measure actual mesh bounds in the visual inspection.")
    for index, slot in enumerate(mesh.get_editor_property("materials")):
        material = slot.get_editor_property("material_interface")
        base = material.get_base_material() if material else None
        report["materials"].append({"slot": index, "slot_name": str(slot.get_editor_property("material_slot_name")),
                                    "material": asset_path(material), "base": asset_path(base),
                                    "used_with_skeletal_mesh": base.get_editor_property("used_with_skeletal_mesh") if base else None})
    report["material_slot_count"] = len(report["materials"])
    checkpoint()
    for name in CLIPS:
        path = BASE + "/Animations/" + name
        anim = u.load_asset(path)
        if not isinstance(anim, u.AnimSequence) or anim.get_editor_property("skeleton") != skeleton:
            raise RuntimeError("Missing animation or wrong skeleton: " + path)
        seconds = anim.get_play_length()
        if seconds <= 0:
            raise RuntimeError("Empty animation: " + path)
        file = ROOT / "Content" / (path[6:] + ".uasset")
        item = {"name": name, "package": path, "seconds": seconds,
                "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
                "enable_root_motion": anim.get_editor_property("enable_root_motion"),
                "force_root_lock": anim.get_editor_property("force_root_lock"),
                "root_motion_root_lock": str(anim.get_editor_property("root_motion_root_lock")),
                "rate_scale": anim.get_editor_property("rate_scale"),
                "additive_anim_type": str(anim.get_editor_property("additive_anim_type")),
                "notify_count": len(u.AnimationLibrary.get_animation_notify_events(anim)), "modes": {}}
        report["clips"].append(item)
        checkpoint()
        for unlocked in (False, True):
            opts = options(mesh, unlocked)
            # Record the first evaluation separately: earlier project probes saw a
            # first-sample inconsistency. Do not mistake normal pelvis motion for drift.
            first = u.AnimPoseExtensions.get_anim_pose_at_time(anim, 0., opts)
            if not u.AnimPoseExtensions.is_valid(first):
                raise RuntimeError("Invalid first pose: " + path)
            names = [str(b) for b in u.AnimPoseExtensions.get_bone_names(first)]
            selected = [b for b in ("root", "pelvis", "head", "foot_l", "foot_r", "ball_l", "ball_r", "bow_base") if b in names]
            if not all(b in selected for b in ("root", "pelvis", "ball_l", "ball_r")):
                raise RuntimeError("Required measurement bones absent: " + path)
            if "bones" not in report:
                report["bones"] = [{"name": b, "reference_component_cm": vector(
                    u.AnimPoseExtensions.get_ref_bone_pose(first, b, u.AnimPoseSpaces.WORLD).translation)} for b in names]
                report["secondary_name_candidates"] = [b for b in names if any(
                    tag in b.lower() for tag in ("hair", "ponytail", "cloth", "quiver", "strap"))]
                report["bow_bones"] = [b for b in names if "bow" in b.lower()]
            initial = {b: vector(u.AnimPoseExtensions.get_bone_pose(first, b, u.AnimPoseSpaces.WORLD).translation) for b in selected}
            samples = []
            frames = math.ceil(seconds * 60)
            for frame in range(frames + 1):
                time = min(frame / 60., seconds)
                pose = u.AnimPoseExtensions.get_anim_pose_at_time(anim, time, opts)
                if not u.AnimPoseExtensions.is_valid(pose):
                    raise RuntimeError("Invalid evaluated pose: " + path)
                samples.append({"time": time, "bones": {b: vector(u.AnimPoseExtensions.get_bone_pose(
                    pose, b, u.AnimPoseSpaces.WORLD).translation) for b in selected}})
            item["modes"]["unlocked" if unlocked else "playback"] = {
                "first_evaluation": initial, "samples": samples,
                "summary": summarize(samples, ["ball_l", "ball_r"])}
            checkpoint()
    report["status"] = "success"


try:
    main()
except Exception as exc:
    report.update(status="failed", error=str(exc), traceback=traceback.format_exc())
finally:
    # Refuse to overwrite old evidence even on a preflight failure.
    if not REPORT.exists() or report.get("mesh"):
        OUT.mkdir(parents=True, exist_ok=True)
        checkpoint()
u.log("SELENE_SPARROW_AUDIT " + report["status"])
if report["status"] != "success":
    raise RuntimeError(report["error"])
