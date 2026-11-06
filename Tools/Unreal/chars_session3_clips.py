"""A2.4: retarget the verified 15 Manny clips using the existing hero retargeters.

Requires the successful session-3 read-only audit. Rejects existing destinations;
never edits or saves the existing rigs, retargeters, meshes, or source sequences.
"""
import hashlib
import json
from pathlib import Path
import traceback

import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
OUT = ROOT / "Saved/Chars/session-3"
MANNY = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"
HEROES = {
    "Fixer": "/Game/Assets/night-market-fixer/night-market-fixer/SkeletalMeshes/night-market-fixer",
    "Courier": "/Game/Assets/scooter-courier/scooter-courier/SkeletalMeshes/scooter-courier",
}
report = {"status": "running", "heroes": {}, "saved_packages": []}


def checkpoint():
    (OUT / "clips.json").write_text(json.dumps(report, indent=2) + "\n")


def main():
    if (OUT / "clips.json").exists():
        raise RuntimeError("Existing report; do not replay")
    if not (ROOT / "Selene.uproject").is_file():
        raise RuntimeError("Run only in Selene")
    verified = json.loads((ROOT / "Saved/Clips/session-3/reload-dependencies.json").read_text())
    if verified["status"] != "success" or len(verified["clips"]) != 15:
        raise RuntimeError("A2.3 must pass before retargeting")
    verified["clips"] = [c for c in verified["clips"] if not c["role"].startswith("Turn")]
    if len(verified["clips"]) != 11:
        raise RuntimeError("Expected exactly eleven source clips")
    registry = u.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(True)
    source = u.load_asset(MANNY)
    if not source:
        raise RuntimeError("Missing existing Manny mesh")
    assets = []
    for clip in verified["clips"]:
        if hashlib.sha256((ROOT / clip["file"]).read_bytes()).hexdigest() != clip["sha256"]:
            raise RuntimeError("Verified source has changed: " + clip["package"])
        data = registry.get_assets_by_package_name(clip["package"], True)
        if data is None or len(data) != 1:
            raise RuntimeError("Missing source registry entry: " + clip["package"])
        assets.append(data[0])
    loaded = {}
    # Preflight both heroes before creating anything.
    for name, mesh_path in HEROES.items():
        base = "/Game/Selene/Characters/" + name
        target, rtg = u.load_asset(mesh_path), u.load_asset(base + "/RTG_Manny_To_" + name)
        if not target or not rtg:
            raise RuntimeError("Missing existing hero mesh/retargeter: " + name)
        controller = u.IKRetargeterController.get_controller(rtg)
        ops = [(str(controller.get_op_name(i)), controller.get_retarget_op_enabled(i))
               for i in range(controller.get_num_retarget_ops())]
        rm = controller.get_index_of_op_by_name("Root Motion")
        if rm >= 0 and controller.get_retarget_op_enabled(rm):
            raise RuntimeError("Existing hero retargeter unexpectedly enables Root Motion: " + name)
        for clip in verified["clips"]:
            dest = base + "/Anims/GASP/" + clip["package"].rsplit("/", 1)[-1] + "_" + name
            if u.EditorAssetLibrary.does_asset_exist(dest) or (ROOT / "Content" / (dest[6:] + ".uasset")).exists():
                raise RuntimeError("Destination already exists; do not replay: " + dest)
        report["heroes"][name] = {"mesh": mesh_path, "retargeter": rtg.get_path_name(), "ops": ops, "clips": []}
        loaded[name] = (target, rtg)
    checkpoint()
    for name, (target, rtg) in loaded.items():
        dest = "/Game/Selene/Characters/" + name + "/Anims/GASP"
        inputs = u.IKRetargetBatchOperationInputs()
        for key, value in {"assets_to_retarget": assets, "source_mesh": source,
            "target_mesh": target, "ik_retarget_asset": rtg, "target_path": dest,
            "suffix": "_" + name, "include_referenced_assets": False,
            "overwrite_existing_files": False, "use_source_path": False}.items():
            inputs.set_editor_property(key, value)
        made = u.IKRetargetBatchOperation.run_batch_retarget(inputs)
        if len(made) != 11:
            raise RuntimeError("Expected exactly 11 hero sequences: " + name)
        by_name = {str(data.asset_name): data.get_asset() for data in made}
        for clip in verified["clips"]:
            asset_name = clip["package"].rsplit("/", 1)[-1] + "_" + name
            anim = by_name[asset_name]
            package = anim.get_path_name().split(".")[0]
            if package != dest + "/" + asset_name or not isinstance(anim, u.AnimSequence):
                raise RuntimeError("Unexpected output path/class: " + package)
            if anim.get_editor_property("skeleton") != target.get_editor_property("skeleton"):
                raise RuntimeError("Wrong hero skeleton: " + package)
            model = anim.get_editor_property("data_model_interface")
            rate = model.get_frame_rate()
            if model.get_number_of_frames() != clip["frames"] or rate.numerator != 30 * rate.denominator:
                raise RuntimeError("Hero retarget changed frame count/rate: " + package)
            if abs(anim.get_play_length() - clip["seconds"]) > 0.001:
                raise RuntimeError("Hero retarget changed duration: " + package)
            if not model.is_valid_bone_track_name("mixamorig_Hips"):
                raise RuntimeError("Hero retarget lost the hips track: " + package)
            if u.AnimationLibrary.get_animation_notify_events(anim):
                raise RuntimeError("Unexpected hero notifies: " + package)
            if not u.EditorAssetLibrary.save_loaded_asset(anim, only_if_is_dirty=False):
                raise RuntimeError("Could not save hero sequence: " + package)
            report["saved_packages"].append(package)
            filename = ROOT / "Content" / (package[6:] + ".uasset")
            report["heroes"][name]["clips"].append({"role": clip["role"], "package": package,
                "seconds": anim.get_play_length(), "frames": model.get_number_of_frames(), "fps": 30,
                "bone_tracks": model.get_num_bone_tracks(), "float_curves": model.get_number_of_float_curves(),
                "skeleton": anim.get_editor_property("skeleton").get_path_name(), "notifies": 0,
                "enable_root_motion": anim.get_editor_property("enable_root_motion"),
                "force_root_lock": anim.get_editor_property("force_root_lock"),
                "bytes": filename.stat().st_size, "sha256": hashlib.sha256(filename.read_bytes()).hexdigest()})
            checkpoint()
        report["heroes"][name]["total_bytes"] = sum(c["bytes"] for c in report["heroes"][name]["clips"])
    report["status"] = "success"


try:
    main()
except Exception as exc:
    report.update(status="failed", error=str(exc), traceback=traceback.format_exc())
finally:
    checkpoint()
u.log("SELENE_CLIP_RETARGET " + report["status"])
if report["status"] != "success":
    raise RuntimeError(report["error"])
