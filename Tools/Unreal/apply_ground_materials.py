"""Assign Ground instances to exact layout ground actors; save and reload to verify.

Only tagged ground/slab/street/terrain actors with the expected folder and area
are eligible. Building lots, stairs, walls, rails and dressing are excluded.
Run headless after build_ground_materials.py. Writes Saved/Ground/report.json.
"""
import json
import os
from pathlib import Path
import traceback

import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
REPORT = {"status": "started", "assignments": [], "counts": {}, "warnings": []}


def snapshot(actor):
    return [[comp.get_material(i).get_path_name() if comp.get_material(i) else None
             for i in range(comp.get_num_materials())]
            for comp in actor.get_components_by_class(u.StaticMeshComponent)]


def main():
    data = json.loads((ROOT / "Design/Blockout/ground_materials.json").read_text())
    layout = json.loads((ROOT / "Design/Blockout/layout.json").read_text())
    rules = data["assignment"]
    expected = {}
    for slab in layout["slabs"]:
        expected[slab["id"]] = (slab["area"], rules["slab_kinds"][slab["kind"]], "slab:" + slab["kind"])
    for street in layout["streets"]:
        for i in range(len(street["points"]) - 1):
            expected[f"{street['id']}_{i}"] = (street["area"], rules["streets"], "street:" + street["kind"])
    terrain = rules["terrain"]
    expected[terrain["label"]] = (terrain["area"], terrain["material"], "terrain")
    materials = {}
    for name in data["materials"]:
        materials[name] = u.load_asset(data["asset_root"] + "/MI_Ground_" + name)
        if not isinstance(materials[name], u.MaterialInstanceConstant):
            raise RuntimeError("Missing material instance: " + name)
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    if not levels.load_level(data["map"]):
        raise RuntimeError("Cannot load Town")
    all_actors = list(actors.get_all_level_actors())
    by_label = {}
    for actor in all_actors:
        by_label.setdefault(actor.get_actor_label(), []).append(actor)
    plan = []
    for label, (area, name, kind) in expected.items():
        candidates = by_label.get(label, [])
        if len(candidates) != 1:
            raise RuntimeError(f"Expected exactly one ground actor {label}, found {len(candidates)}")
        actor = candidates[0]
        if not (actor.actor_has_tag(rules["required_tag"]) and actor.actor_has_tag("Area_" + area)
                and str(actor.get_folder_path()) == "Blockout/" + area
                and isinstance(actor, u.StaticMeshActor)):
            raise RuntimeError("Ground actor identity check failed: " + label)
        comp = actor.static_mesh_component
        if comp.get_num_materials() < 1:
            raise RuntimeError("No material slots: " + label)
        plan.append((actor, comp, name, kind))
    # Check the entire plan before changing any actor.
    untouched = {a.get_path_name(): snapshot(a) for a in all_actors if a.get_actor_label() not in expected}
    for actor, comp, name, kind in plan:
        before = snapshot(actor)
        actor.modify()
        comp.modify()
        for slot in range(comp.get_num_materials()):
            comp.set_material(slot, materials[name])
        REPORT["assignments"].append(dict(label=actor.get_actor_label(), actor=actor.get_path_name(),
                                           area=str(actor.get_folder_path()), kind=kind,
                                           instance=materials[name].get_path_name(), slots=comp.get_num_materials(), before=before))
        REPORT["counts"][name] = REPORT["counts"].get(name, 0) + 1
    REPORT["warnings"].append("Terrain kept grass across its existing slots; no height, slope or layout mask added.")
    REPORT["warnings"].append("Optional ground_tiles_13 border instance created but not assigned: no dedicated border ground in layout.")
    if not levels.save_current_level():
        raise RuntimeError("Town save failed")
    if not u.EditorLoadingAndSavingUtils.save_dirty_packages(True, True):
        raise RuntimeError("Dirty package save failed")
    # Reload the actual saved map, including external actors, before claiming persistence.
    if not levels.load_level(data["map"]):
        raise RuntimeError("Town verification reload failed")
    reloaded = list(actors.get_all_level_actors())
    by_path = {a.get_path_name(): a for a in reloaded}
    for entry in REPORT["assignments"]:
        actor = by_path.get(entry["actor"])
        if not actor or snapshot(actor) != [[entry["instance"]] * entry["slots"]]:
            raise RuntimeError("Saved assignment mismatch: " + entry["label"])
    for path, before in untouched.items():
        if path not in by_path or snapshot(by_path[path]) != before:
            raise RuntimeError("Unrelated actor material changed: " + path)
    REPORT.update(status="success", map=data["map"], verified_after_reload=len(plan),
                  untouched_actors_verified=len(untouched))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        REPORT.update(status="failed", error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        path = Path(os.environ["SELENE_STAGE_REPORT"]) if os.environ.get("SELENE_STAGE_REPORT") else ROOT / "Saved/Ground/report.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        REPORT["invocation"] = os.environ.get("SELENE_STAGE_ID")
        path.write_text(json.dumps(REPORT, indent=2) + "\n")
        u.log("Ground assignment report: " + str(path))
