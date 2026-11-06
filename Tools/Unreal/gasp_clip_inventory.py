"""Read-only GASP step-A selection and migration preflight.

Run with GASP's Python commandlet. SELENE_CLIPS_ROOT must point to Selene.
Writes Saved/Clips/session-1/inventory.json in Selene; never saves GASP assets.
"""
import json
import os
from pathlib import Path
import traceback

import unreal as u

SELENE = Path(os.environ["SELENE_CLIPS_ROOT"]).resolve()
OUT = SELENE / "Saved/Clips/session-1"
BASE = "/Game/Characters/UEFN_Mannequin/"
SELECTION = {
    "Idle": "Idle/M_Neutral_Stand_Idle_Loop",
    "WalkLoop": "Walk/M_Neutral_Walk_Loop_F",
    "RunLoop": "Run/M_Neutral_Run_Loop_F",
    "SprintLoop": "Sprint/M_Neutral_Sprint_Loop_F",
    "WalkStart": "Walk/M_Neutral_Walk_Start_F_Lfoot",
    "RunStart": "Run/M_Neutral_Run_Start_F_Lfoot",
    "WalkStop": "Walk/M_Neutral_Walk_Stop_F_Lfoot",
    "RunStop": "Run/M_Neutral_Run_Stop_F_Lfoot",
    "SprintStop": "Sprint/M_Neutral_Sprint_Stop_F_Lfoot",
    "PivotWalk": "Walk/M_Neutral_Walk_Pivot_F_B_Lfoot",
    "PivotRun": "Run/M_Neutral_Run_Pivot_F_B_Lfoot",
    "Turn90L": "Idle/M_Neutral_Stand_Turn_090_L",
    "Turn90R": "Idle/M_Neutral_Stand_Turn_090_R",
    "Turn180L": "Idle/M_Neutral_Stand_Turn_180_L",
    "Turn180R": "Idle/M_Neutral_Stand_Turn_180_R",
}
report = {"status": "failed", "selection_basis": "Neutral, forward loops/starts/stops; F_B pivots; explicit standing turn angles. Left-foot variants keep the initial set small. Existing jump/fall/land retained pending a visual comparison."}


def main():
    project = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    if project.name != "GameAnimationSample" or project == SELENE:
        raise RuntimeError("Run this inventory in the read-only GameAnimationSample project")
    registry = u.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(True)
    options = u.AssetRegistryDependencyOptions(
        include_soft_package_references=True, include_hard_package_references=True,
        include_searchable_names=False, include_soft_management_references=False,
        include_hard_management_references=False)
    clips = []
    for role, relative in SELECTION.items():
        package = BASE + "Animations/" + relative
        asset = u.load_asset(package)
        if not isinstance(asset, u.AnimSequence):
            raise RuntimeError("Missing AnimSequence: " + package)
        clips.append({"role": role, "package": package,
                      "seconds": asset.get_play_length(),
                      "skeleton": asset.get_editor_property("skeleton").get_path_name(),
                      "enable_root_motion": asset.get_editor_property("enable_root_motion"),
                      "force_root_lock": asset.get_editor_property("force_root_lock")})
    report["clips"] = clips
    roots = [clip["package"] for clip in clips]
    report["roots"] = roots
    report["source_project"] = str(project)
    report["destination_content"] = str(SELENE / "Content")
    dependencies, pending, external = {}, list(roots), set()
    while pending:
        package = pending.pop()
        if package in dependencies:
            continue
        deps = sorted(str(d) for d in registry.get_dependencies(package, options))
        dependencies[package] = deps
        for dep in deps:
            if dep.startswith("/Game/"):
                if dep not in dependencies:
                    pending.append(dep)
            else:
                external.add(dep)
    report["dependencies"] = dependencies
    report["external_dependencies"] = sorted(external)
    manifest, conflicts, forbidden = [], [], []
    for package in sorted(dependencies):
        assets = registry.get_assets_by_package_name(package)
        classes = sorted({str(a.asset_class_path.asset_name) for a in assets})
        relative = package[len("/Game/"):]
        files = []
        for suffix in (".uasset", ".umap", ".uexp", ".ubulk", ".uptnl"):
            source = project / "Content" / (relative + suffix)
            if source.is_file():
                files.append({"relative": relative + suffix, "bytes": source.stat().st_size})
                if (SELENE / "Content" / (relative + suffix)).exists():
                    conflicts.append(relative + suffix)
        if not files:
            raise RuntimeError("Missing package file: " + package)
        manifest.append({"package": package, "classes": classes, "files": files,
                         "bytes": sum(f["bytes"] for f in files)})
        if any(c in ("AnimBlueprint", "Blueprint", "ChooserTable", "PoseSearchDatabase") for c in classes) or any(
                part.lower() in package.lower() for part in ("MetaHuman", "Traversal", "/Choosers/", "/Databases/")):
            forbidden.append(package)
    report["manifest"] = manifest
    report["package_count"] = len(manifest)
    report["total_bytes"] = sum(p["bytes"] for p in manifest)
    report["conflicts"] = conflicts
    report["forbidden_dependencies"] = forbidden
    report["source_rig_in_closure"] = BASE + "Rigs/IK_UEFN_Mannequin" in dependencies
    report["migration_permitted"] = not forbidden and not conflicts and report["total_bytes"] < 100_000_000
    report["status"] = "inventoried"


try:
    main()
except Exception as exc:
    report["error"] = str(exc)
    report["traceback"] = traceback.format_exc()
finally:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "inventory.json").write_text(json.dumps(report, indent=2) + "\n")
u.log("SELENE_CLIP_INVENTORY " + report["status"])
if report["status"] == "failed":
    raise RuntimeError(report["error"])
