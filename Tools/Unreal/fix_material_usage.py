"""Set the material usage flags game builds need (the editor sets missing flags on the fly, cooked/-game runs don't:
"missing usage flag Nanite/SkeletalMesh! Default Material will be used in game").

For every material instance and material under /Game/Assets and /Game/Selene, resolve the base material; if it lives
under /Game, enable used_with_nanite (static props/ground/buildings are Nanite) and used_with_skeletal_mesh (characters),
recompile and save. Imported glTF materials are instances of Interchange plugin materials (/InterchangeAssets/gltf/...), which live in the
shared engine install and must not be edited: their parent chain is duplicated once into /Game/Selene/Materials/Imported
(keeping each intermediate instance's static switches and overrides), the copies get the flags, and the project instances
are re-parented to the copied chain. Writes Saved/MaterialUsage/report.json.
"""
import json
import os

import unreal as u

ROOT = u.Paths.convert_relative_path_to_full(u.Paths.project_dir())
LIB = u.EditorAssetLibrary
report = {"fixed": [], "already": [], "external_bases": {}, "errors": []}
bases = {}
for folder in ("/Game/Assets", "/Game/Selene"):
    for path in LIB.list_assets(folder, recursive=True, include_folder=False):
        data = LIB.find_asset_data(path)
        cls = str(data.asset_class_path.asset_name)
        if cls not in ("Material", "MaterialInstanceConstant"):
            continue
        asset = u.load_asset(path)
        base = asset if cls == "Material" else asset.get_base_material()
        if base:
            bases.setdefault(base.get_path_name(), base)
TOOLS = u.AssetToolsHelpers.get_asset_tools()
MEL = u.MaterialEditingLibrary
COPY_ROOT = "/Game/Selene/Materials/Imported"
copies = {}


def local_copy(obj):
    """Copy an external material/instance (and its external parents) into /Game, preserving the chain."""
    path = obj.get_path_name()
    if path in copies:
        return copies[path]
    name = obj.get_name()
    dest = COPY_ROOT + "/" + name
    copy = u.load_asset(dest) if LIB.does_asset_exist(dest) else TOOLS.duplicate_asset(name, COPY_ROOT, obj)
    if not copy:
        raise RuntimeError("Could not copy " + path)
    if isinstance(obj, u.MaterialInstanceConstant):
        parent = obj.get_editor_property("parent")
        if parent and not parent.get_path_name().startswith("/Game/"):
            MEL.set_material_instance_parent(copy, local_copy(parent))
    copies[path] = copy
    LIB.save_loaded_asset(copy, only_if_is_dirty=False)
    return copy


relinked = []
for folder in ("/Game/Assets",):
    for path in LIB.list_assets(folder, recursive=True, include_folder=False):
        data = LIB.find_asset_data(path)
        if str(data.asset_class_path.asset_name) != "MaterialInstanceConstant":
            continue
        mi = u.load_asset(path)
        parent = mi.get_editor_property("parent")
        if parent and not parent.get_path_name().startswith("/Game/"):
            try:
                mi.modify()
                MEL.set_material_instance_parent(mi, local_copy(parent))
                MEL.update_material_instance(mi)
                LIB.save_loaded_asset(mi, only_if_is_dirty=False)
                relinked.append(path)
            except Exception as exc:
                report["errors"].append({"instance": path, "error": str(exc)})
report["relinked_instances"] = relinked
report["copied"] = {k: v.get_path_name() for k, v in copies.items()}
for copy in copies.values():
    if isinstance(copy, u.Material):
        bases[copy.get_path_name()] = copy
for path, mat in sorted(bases.items()):
    if not path.startswith("/Game/"):
        report["external_bases"][path] = True
        continue
    need = [f for f in ("used_with_nanite", "used_with_skeletal_mesh") if not mat.get_editor_property(f)]
    if not need:
        report["already"].append(path)
        continue
    try:
        mat.modify()
        for flag in need:
            mat.set_editor_property(flag, True)
        u.MaterialEditingLibrary.recompile_material(mat)
        LIB.save_loaded_asset(mat, only_if_is_dirty=False)
        report["fixed"].append({"material": path, "flags": need})
    except Exception as exc:  # keep going; report
        report["errors"].append({"material": path, "error": str(exc)})
os.makedirs(os.path.join(ROOT, "Saved", "MaterialUsage"), exist_ok=True)
with open(os.path.join(ROOT, "Saved", "MaterialUsage", "report.json"), "w") as f:
    json.dump(report, f, indent=2)
