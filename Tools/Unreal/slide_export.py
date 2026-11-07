"""A2.1-2: in-memory UEFN -> Manny retarget, then animation-only FBX export.

Run in GASP's commandlet with SELENE_CLIPS_ROOT pointing to Selene. Never saves
packages or changes GASP files. The selected inputs come from session 1's inventory.
Existing output files are rejected so a failed run cannot silently be replayed.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import traceback

import unreal as u

ROOT = Path(os.environ["SELENE_CLIPS_ROOT"]).resolve()
OUT = ROOT / "Saved/SlidePass/session-1"
FBX = ROOT / "Saved/SlidePass/session-1/fbx"
MEMORY_PATH = "/Game/__SeleneSlide_Memory"
SOURCE_MESH = "/Game/Characters/UEFN_Mannequin/Meshes/SKM_UEFN_Mannequin"
TARGET_MESH = "/Game/Characters/UE5_Mannequins/Meshes/SKM_Manny_Simple"
RETARGETER = "/Game/Characters/UE5_Mannequins/Rigs/RTG_UEFN_to_UE5_Mannequin"
report = {"status": "failed", "clips": [], "saved_gasp_packages": [],
          "retargeter": RETARGETER, "source_mesh": SOURCE_MESH, "target_mesh": TARGET_MESH}


def root_sample(anim, mesh, seconds):
    options = u.AnimPoseEvaluationOptions()
    options.set_editor_property("optional_skeletal_mesh", mesh)
    options.set_editor_property("extract_root_motion", False)
    options.set_editor_property("incorporate_root_motion_into_pose", True)
    pose = u.AnimPoseExtensions.get_anim_pose_at_time(anim, seconds, options)
    transform = u.AnimPoseExtensions.get_bone_pose(pose, "root", u.AnimPoseSpaces.LOCAL)
    v = transform.translation
    return [v.x, v.y, v.z]


def main():
    project = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    if project.name != "GameAnimationSample" or project == ROOT:
        raise RuntimeError("Run this export in GameAnimationSample")
    scratch = project / "Content/__SeleneSlide_Memory"
    if scratch.exists() or list(FBX.glob("*.fbx")):
        raise RuntimeError("Output already exists; inspect the previous run before any replay")
    names = {
        "SlideInto": "M_Neutral_Slide_KneesOut_Into_Lfoot",
        "SlideLoop": "M_Neutral_Slide_KneesOut_Loop",
        "SlideOutMoving": "M_Neutral_Slide_KneesOut_Out_Moving_Run",
        "SlideOutStand": "M_Neutral_Slide_KneesOut_Out_Idle_Stand",
    }
    registry = u.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(True)
    found = {str(a.asset_name): a for a in registry.get_assets_by_path("/Game/Characters/UEFN_Mannequin/Animations/Slide", recursive=True)}
    clips = []
    for role, name in names.items():
        data = found[name]
        anim = data.get_asset()
        clips.append({"role": role, "package": str(data.package_name), "seconds": anim.get_play_length()})
    if len(clips) != 4:
        raise RuntimeError("Expected exactly the 4 approved sequences")
    registry = u.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(True)
    source, target, rtg = (u.load_asset(p) for p in (SOURCE_MESH, TARGET_MESH, RETARGETER))
    if not source or not target or not rtg:
        raise RuntimeError("Missing source mesh, Manny mesh, or existing GASP retargeter")
    assets = []
    for clip in clips:
        anim = u.load_asset(clip["package"])
        if not isinstance(anim, u.AnimSequence):
            raise RuntimeError("Missing sequence: " + clip["package"])
        model = anim.get_editor_property("data_model_interface")
        rate = model.get_frame_rate()
        if rate.numerator != 30 * rate.denominator:
            raise RuntimeError("Selected source is not 30 fps: " + clip["package"])
        assets.append(registry.get_asset_by_object_path(anim.get_path_name()))
    inputs = u.IKRetargetBatchOperationInputs()
    for key, value in {
        "assets_to_retarget": assets, "source_mesh": source, "target_mesh": target,
        "ik_retarget_asset": rtg, "target_path": MEMORY_PATH,
        "include_referenced_assets": False, "overwrite_existing_files": False,
        "use_source_path": False,
    }.items():
        inputs.set_editor_property(key, value)
    made = u.IKRetargetBatchOperation.run_batch_retarget(inputs)
    if len(made) != len(clips):
        raise RuntimeError("Expected 4 retargeted sequences; got %d" % len(made))
    by_name = {str(data.asset_name): data.get_asset() for data in made}
    FBX.mkdir(parents=True, exist_ok=True)
    for clip in clips:
        name = clip["package"].rsplit("/", 1)[-1]
        anim = by_name[name]
        if anim.get_editor_property("skeleton") != target.get_editor_property("skeleton"):
            raise RuntimeError("Wrong skeleton after retarget: " + name)
        model = anim.get_editor_property("data_model_interface")
        rate = model.get_frame_rate()
        if rate.numerator != 30 * rate.denominator or not model.is_valid_bone_track_name("root"):
            raise RuntimeError("Retarget lost the 30 fps root track: " + name)
        duration = anim.get_play_length()
        if abs(duration - clip["seconds"]) > 0.001:
            raise RuntimeError("Retarget changed duration: " + name)
        first, last = root_sample(anim, target, 0), root_sample(anim, target, duration)
        filename = FBX / (name + ".fbx")
        options = u.FbxExportOption()
        options.set_editor_property("export_preview_mesh", False)
        options.set_editor_property("export_morph_targets", False)
        options.set_editor_property("ascii", False)
        options.set_editor_property("force_front_x_axis", False)
        task = u.AssetExportTask()
        for key, value in {
            "object": anim, "filename": str(filename), "automated": True,
            "prompt": False, "replace_identical": False, "selected": False,
            "exporter": u.AnimSequenceExporterFBX(), "options": options,
        }.items():
            task.set_editor_property(key, value)
        if not u.Exporter.run_asset_export_task(task) or not filename.is_file():
            raise RuntimeError("FBX export failed: " + name)
        if list(task.get_editor_property("errors")):
            raise RuntimeError("FBX exporter errors: " + str(task.get_editor_property("errors")))
        report["clips"].append({**clip, "fbx": str(filename.relative_to(ROOT)),
            "bytes": filename.stat().st_size, "sha256": hashlib.sha256(filename.read_bytes()).hexdigest(),
            "manny_skeleton": anim.get_editor_property("skeleton").get_path_name(),
            "frames": model.get_number_of_frames(), "fps": rate.numerator / rate.denominator,
            "bone_tracks": model.get_num_bone_tracks(), "float_curves": model.get_number_of_float_curves(),
            "root_first_cm": first, "root_last_cm": last,
            "root_net_speed_xy_cm_s": math.hypot(last[0] - first[0], last[1] - first[1]) / duration})
        (OUT / "export.json").write_text(json.dumps(report, indent=2) + "\n")
    if scratch.exists():
        raise RuntimeError("Unexpected disk scratch folder; batch was expected to remain in memory")
    report["memory_package_count"] = len(made)
    report["gasp_scratch_exists"] = False
    report["total_fbx_bytes"] = sum(c["bytes"] for c in report["clips"])
    report["status"] = "success"
    lines = ["# GASP Manny animation sources", "",
             "Source: Epic Game Animation Sample, installed UE 5.8 project (2026-11-06).",
             "Retargeted in memory using `" + RETARGETER + "` onto `" + TARGET_MESH + "`.",
             "Export: AnimSequenceExporterFBX, 30 fps, bone/root tracks and custom curves, no preview mesh.",
             "No GASP packages saved or migrated. FBX files are local ignored source art.",
             "Evidence and SHA-256 hashes: `Saved/SlidePass/session-1/export.json`.", "",
             "| Role | GASP sequence | FBX |", "| --- | --- | --- |"]
    lines += ["| %s | `%s` | `%s` |" % (c["role"], c["package"], Path(c["fbx"]).name) for c in report["clips"]]
    (FBX / "SOURCES.md").write_text("\n".join(lines) + "\n")


OUT.mkdir(parents=True, exist_ok=True)
try:
    main()
except Exception as exc:
    report["error"] = str(exc)
    report["traceback"] = traceback.format_exc()
finally:
    (OUT / "export.json").write_text(json.dumps(report, indent=2) + "\n")
u.log("SELENE_CLIP_EXPORT " + report["status"])
if report["status"] != "success":
    raise RuntimeError(report["error"])
