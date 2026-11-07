"""A2.3: import the exported FBX clips onto Selene's existing Manny skeleton.

Run once in a locked Selene commandlet, with Interchange.FeatureFlags.Import.FBX=0
to use the explicit FbxFactory/animation-only options. Reject existing outputs.
"""
import hashlib
import json
import math
from pathlib import Path
import traceback

import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
OUT = ROOT / "Saved/Clips/session-2"
DEST = "/Game/Selene/Animation/GASP"
SKELETON = "/Game/Characters/Mannequins/Meshes/SK_Mannequin"
MESH = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"
report = {"status": "failed", "clips": []}


def main():
    if not (ROOT / "Selene.uproject").is_file():
        raise RuntimeError("Run only in Selene")
    exported = json.loads((OUT / "export.json").read_text())
    if exported["status"] != "success" or len(exported["clips"]) != 15:
        raise RuntimeError("Missing complete, successful export")
    registry = u.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(True)
    skeleton, mesh = u.load_asset(SKELETON), u.load_asset(MESH)
    if not skeleton or not mesh:
        raise RuntimeError("Missing Selene Manny skeleton or mesh")
    tasks = []
    for clip in exported["clips"]:
        filename = ROOT / clip["fbx"]
        name = filename.stem
        if u.EditorAssetLibrary.does_asset_exist(DEST + "/" + name):
            raise RuntimeError("Destination exists; inspect before replay: " + name)
        if hashlib.sha256(filename.read_bytes()).hexdigest() != clip["sha256"]:
            raise RuntimeError("FBX hash changed: " + name)
        options = u.FbxImportUI()
        for key, value in {
            "automated_import_should_detect_type": False,
            "mesh_type_to_import": u.FBXImportType.FBXIT_ANIMATION,
            "original_import_type": u.FBXImportType.FBXIT_ANIMATION,
            "import_mesh": False, "import_animations": True,
            "import_materials": False, "import_textures": False,
            "create_physics_asset": False, "skeleton": skeleton,
        }.items():
            options.set_editor_property(key, value)
        data = options.get_editor_property("anim_sequence_import_data")
        for key, value in {
            "use_default_sample_rate": True, "custom_sample_rate": 30,
            "animation_length": u.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME,
            "import_bone_tracks": True, "import_custom_attribute": True,
            "remove_redundant_keys": False, "do_not_import_curve_with_zero": False,
            "add_curve_metadata_to_skeleton": False,
            "convert_scene": True, "force_front_x_axis": False,
        }.items():
            data.set_editor_property(key, value)
        task = u.AssetImportTask()
        for key, value in {
            "filename": str(filename), "destination_path": DEST,
            "destination_name": name, "automated": True, "replace_existing": False,
            "save": False, "factory": u.FbxFactory(), "options": options,
        }.items():
            task.set_editor_property(key, value)
        tasks.append(task)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    for clip, task in zip(exported["clips"], tasks):
        name = Path(clip["fbx"]).stem
        path = DEST + "/" + name
        objects = task.get_objects()
        if len(objects) != 1 or not isinstance(objects[0], u.AnimSequence):
            raise RuntimeError("Expected one animation only: " + name)
        anim = objects[0]
        if anim.get_path_name().split(".")[0] != path or anim.get_editor_property("skeleton") != skeleton:
            raise RuntimeError("Unexpected animation destination/skeleton: " + name)
        model = anim.get_editor_property("data_model_interface")
        rate = model.get_frame_rate()
        if rate.numerator != 30 * rate.denominator or model.get_number_of_frames() != clip["frames"]:
            raise RuntimeError("Frame count/rate changed: " + name)
        if abs(anim.get_play_length() - clip["seconds"]) > 0.001 or not model.is_valid_bone_track_name("root"):
            raise RuntimeError("Duration/root track changed: " + name)
        if u.AnimationLibrary.get_animation_notify_events(anim):
            raise RuntimeError("Unexpected imported notifies: " + name)
        options = u.AnimPoseEvaluationOptions()
        options.set_editor_property("optional_skeletal_mesh", mesh)
        points = []
        for seconds in (0.0, anim.get_play_length()):
            pose = u.AnimPoseExtensions.get_anim_pose_at_time(anim, seconds, options)
            v = u.AnimPoseExtensions.get_bone_pose(pose, "root", u.AnimPoseSpaces.LOCAL).translation
            points.append([v.x, v.y, v.z])
        root_error = max(math.dist(a, b) for a, b in zip(points, (clip["root_first_cm"], clip["root_last_cm"])))
        if root_error > 0.1:
            raise RuntimeError("FBX round trip changed root translation: %s, %.3f cm" % (name, root_error))
        # CharacterMovement drives translation. Preserve the track for measurements/retargeting,
        # but evaluate in place (the source GASP clips also have force_root_lock enabled).
        anim.set_editor_property("enable_root_motion", False)
        anim.set_editor_property("force_root_lock", True)
        anim.set_editor_property("root_motion_root_lock", u.RootMotionRootLock.ANIM_FIRST_FRAME)
        if not u.EditorAssetLibrary.save_loaded_asset(anim, only_if_is_dirty=False):
            raise RuntimeError("Save failed: " + path)
        report["clips"].append({"role": clip["role"], "package": path,
            "seconds": anim.get_play_length(), "fps": rate.numerator / rate.denominator,
            "frames": model.get_number_of_frames(), "bone_tracks": model.get_num_bone_tracks(),
            "float_curves": model.get_number_of_float_curves(), "notifies": 0,
            "root_roundtrip_max_error_cm": root_error,
            "root_net_speed_xy_cm_s": clip["root_net_speed_xy_cm_s"]})
    dependencies = u.AssetRegistryDependencyOptions(include_soft_package_references=True,
        include_hard_package_references=True, include_searchable_names=False,
        include_soft_management_references=False, include_hard_management_references=False)
    pending = [c["package"] for c in report["clips"]]
    graph = {}
    while pending:
        path = pending.pop()
        if path in graph:
            continue
        deps = sorted(str(p) for p in registry.get_dependencies(path, dependencies))
        graph[path] = deps
        for dep in deps:
            if "UEFN_Mannequin" in dep or "UE5_Mannequins" in dep or "__SeleneClips" in dep:
                raise RuntimeError("GASP dependency survived: " + dep)
            if dep.startswith("/Game/"):
                if not (ROOT / "Content" / (dep[6:] + ".uasset")).is_file():
                    raise RuntimeError("Missing Selene-local dependency: " + dep)
                pending.append(dep)
            elif not dep.startswith(("/Engine/", "/Script/")):
                raise RuntimeError("Unexpected external dependency: " + dep)
    report["dependency_graph"] = graph
    report["total_asset_bytes"] = sum((ROOT / "Content" / (c["package"][6:] + ".uasset")).stat().st_size for c in report["clips"])
    if report["total_asset_bytes"] >= 100_000_000:
        raise RuntimeError("Unexpectedly large imported animation set")
    report["status"] = "success"


try:
    main()
except Exception as exc:
    report["error"] = str(exc)
    report["traceback"] = traceback.format_exc()
finally:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "import.json").write_text(json.dumps(report, indent=2) + "\n")
u.log("SELENE_CLIP_IMPORT " + report["status"])
if report["status"] != "success":
    raise RuntimeError(report["error"])
