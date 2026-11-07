"""A2.3: fresh-process, read-only reload and hard/soft dependency audit.

Run in a locked Selene commandlet. Never imports, retargets, modifies or saves assets.
Every lookup is checkpointed; None means an unavailable dependency node, not a leaf.
"""
import hashlib
import json
import math
from pathlib import Path
import traceback

import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
OUT = ROOT / "Saved/Clips/session-3"
report = {"status": "running", "clips": [], "dependency_graph": {}, "packages": {},
          "current_package": None, "unavailable_dependency_records": []}


def checkpoint():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "reload-dependencies.json").write_text(json.dumps(report, indent=2) + "\n")


def main():
    if not (ROOT / "Selene.uproject").is_file():
        raise RuntimeError("Run only in Selene")
    prior = json.loads((ROOT / "Saved/Clips/session-2/verification.json").read_text())
    exported = json.loads((ROOT / "Saved/Clips/session-2/export.json").read_text())
    expected = {Path(c["fbx"]).stem: c for c in exported["clips"]}
    if len(prior["asset_manifest"]) != 15 or len(expected) != 15:
        raise RuntimeError("Expected exactly 15 saved/exported sequences")
    registry = u.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(True)
    files = [str(ROOT / c["file"]) for c in prior["asset_manifest"]]
    registry.scan_files_synchronous(files, True)
    skeleton = u.load_asset("/Game/Characters/Mannequins/Meshes/SK_Mannequin")
    mesh = u.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple")
    if not skeleton or not mesh:
        raise RuntimeError("Missing Selene Manny support assets")
    for entry in prior["asset_manifest"]:
        path = entry["package"]
        report["current_package"] = path
        checkpoint()
        filename = ROOT / entry["file"]
        digest = hashlib.sha256(filename.read_bytes()).hexdigest()
        if digest != entry["sha256"] or filename.stat().st_size != entry["bytes"]:
            raise RuntimeError("Saved sequence changed since session 2: " + path)
        assets = registry.get_assets_by_package_name(path, True)
        if assets is None or len(assets) != 1:
            raise RuntimeError("Missing/ambiguous on-disk registry entry: " + path)
        anim = u.load_asset(path)
        clip = expected[filename.stem]
        if not isinstance(anim, u.AnimSequence) or anim.get_editor_property("skeleton") != skeleton:
            raise RuntimeError("Unexpected class or skeleton: " + path)
        model = anim.get_editor_property("data_model_interface")
        rate = model.get_frame_rate()
        if rate.numerator != 30 * rate.denominator or model.get_number_of_frames() != clip["frames"]:
            raise RuntimeError("Unexpected frame count/rate: " + path)
        if abs(anim.get_play_length() - clip["seconds"]) > 0.001:
            raise RuntimeError("Unexpected duration: " + path)
        if model.get_num_bone_tracks() != 89 or not model.is_valid_bone_track_name("root"):
            raise RuntimeError("Unexpected bone/root tracks: " + path)
        if u.AnimationLibrary.get_animation_notify_events(anim):
            raise RuntimeError("Unexpected notify: " + path)
        flags = {key: anim.get_editor_property(key) for key in ("enable_root_motion", "force_root_lock")}
        if flags != {"enable_root_motion": False, "force_root_lock": True}:
            raise RuntimeError("Unexpected playback flags: " + path)
        options = u.AnimPoseEvaluationOptions()
        options.set_editor_property("optional_skeletal_mesh", mesh)
        points = []
        for seconds in (0.0, anim.get_play_length()):
            pose = u.AnimPoseExtensions.get_anim_pose_at_time(anim, seconds, options)
            v = u.AnimPoseExtensions.get_bone_pose(pose, "root", u.AnimPoseSpaces.LOCAL).translation
            points.append([v.x, v.y, v.z])
        error = max(math.dist(a, b) for a, b in zip(points, (clip["root_first_cm"], clip["root_last_cm"])))
        if error > 0.1:
            raise RuntimeError("Reload changed root endpoints: " + path)
        report["clips"].append({**entry, "role": clip["role"], "fps": 30,
            "frames": model.get_number_of_frames(), "seconds": anim.get_play_length(),
            "bone_tracks": model.get_num_bone_tracks(), "float_curves": model.get_number_of_float_curves(),
            "notifies": 0, "flags": flags, "root_endpoint_max_error_cm": error,
            "sha256_matches_session_2": True})
        checkpoint()

    mounts = {"Game": ROOT / "Content", "Engine": Path(u.Paths.convert_relative_path_to_full(u.Paths.engine_content_dir()))}
    for base in (Path(u.Paths.convert_relative_path_to_full(u.Paths.engine_plugins_dir())), ROOT / "Plugins"):
        for plugin in base.rglob("*.uplugin"):
            content = plugin.parent / "Content"
            if content.is_dir():
                mounts[plugin.stem] = content
    options = u.AssetRegistryDependencyOptions(include_soft_package_references=True,
        include_hard_package_references=True, include_searchable_names=False,
        include_soft_management_references=False, include_hard_management_references=False)
    pending = [c["package"] for c in report["clips"]]
    graph = report["dependency_graph"]
    scripts = set()
    while pending:
        path = pending.pop()
        if path in graph:
            continue
        report["current_package"] = path
        checkpoint()
        if any(s in path for s in ("UEFN_Mannequin", "UE5_Mannequins", "__SeleneClips", "PoseSearch", "PSD_", "CHT_")):
            raise RuntimeError("Forbidden GASP dependency: " + path)
        parts = path.strip("/").split("/", 1)
        if len(parts) != 2 or parts[0] not in mounts:
            raise RuntimeError("Unresolved package mount: " + path)
        filename = mounts[parts[0]] / (parts[1] + ".uasset")
        if not filename.is_file():
            raise RuntimeError("Package is not present on disk: " + str(filename))
        registry.scan_files_synchronous([str(filename)], True)
        assets = registry.get_assets_by_package_name(path, True)
        if assets is None or not assets:
            raise RuntimeError("No on-disk asset record: " + path)
        classes = sorted(set(str(a.asset_class_path.asset_name) for a in assets))
        if any(c in ("PoseSearchDatabase", "ChooserTable") for c in classes):
            raise RuntimeError("Forbidden asset class: " + path)
        report["packages"][path] = {"file": str(filename), "bytes": filename.stat().st_size, "classes": classes}
        checkpoint()
        result = registry.get_dependencies(path, options)
        if result is None:
            report["unavailable_dependency_records"].append(path)
            checkpoint()
            raise RuntimeError("Dependency node unavailable after explicit disk scan: " + path)
        deps = sorted(str(p) for p in result)
        graph[path] = deps
        checkpoint()
        for dep in deps:
            if dep.startswith("/Script/"):
                scripts.add(dep)
            else:
                pending.append(dep)
    report["script_module_terminals"] = sorted(scripts)
    report["total_imported_asset_bytes"] = sum(c["bytes"] for c in report["clips"])
    if report["total_imported_asset_bytes"] >= 100_000_000:
        raise RuntimeError("Imported set exceeds expected tens of MB")
    report["current_package"] = None
    report["dependency_packages"] = len(graph)
    report["status"] = "success"


try:
    main()
except Exception as exc:
    report.update(status="failed", error=str(exc), traceback=traceback.format_exc())
finally:
    checkpoint()
u.log("SELENE_CLIP_VERIFY " + report["status"])
if report["status"] != "success":
    raise RuntimeError(report["error"])
