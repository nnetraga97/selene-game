"""Rebuild the shared character materials on a Substrate Slab (standard lit) instead of the Toon BSDF.

Why: the Toon BSDF's hard default ramp turns the fine normal detail of dense Tripo faces into
blotchy light/dark patches that read as a ghosted second face (Saved/FaceCheck*). Under ordinary
lighting the same geometry shades cleanly. Parameter names are kept (BaseColorTex, Roughness,
Specular, RimColor, RimStrength) so every MI_Toon_* instance keeps its texture.

Backs up the previous materials to /Game/Selene/Materials/Character/Backup_ToonBSDF/ first.
M_Character_Toon becomes one-sided; M_Character_Toon_TwoSided stays two-sided (Ysolde's cloth).
Writes Saved/Characters/character_lit.json.
"""
import json
import unreal as u

lib = u.EditorAssetLibrary
mel = u.MaterialEditingLibrary
BASE = "/Game/Selene/Materials/Character"
BACKUP = BASE + "/Backup_ToonBSDF"
report = {"status": "failed", "materials": {}}


def pin(src, dst, names):
    for n in names:
        if mel.connect_material_expressions(src, "", dst, n):
            return n
    raise RuntimeError("could not connect to %s (tried %s)" % (dst.get_name(), names))


def rebuild(name, two_sided):
    path = BASE + "/" + name
    backup = BACKUP + "/" + name
    if not lib.does_asset_exist(backup):
        if not lib.duplicate_asset(path, backup):
            raise RuntimeError("backup failed for " + path)
    mat = u.load_asset(path)
    mel.delete_all_material_expressions(mat)
    mat.set_editor_property("two_sided", two_sided)
    mat.set_editor_property("used_with_skeletal_mesh", True)

    tex = mel.create_material_expression(mat, u.MaterialExpressionTextureSampleParameter2D, -900, -200)
    tex.set_editor_property("parameter_name", "BaseColorTex")
    rough = mel.create_material_expression(mat, u.MaterialExpressionScalarParameter, -900, 50)
    rough.set_editor_property("parameter_name", "Roughness")
    rough.set_editor_property("default_value", 0.75)
    spec = mel.create_material_expression(mat, u.MaterialExpressionScalarParameter, -900, 150)
    spec.set_editor_property("parameter_name", "Specular")
    spec.set_editor_property("default_value", 0.2)
    f0 = mel.create_material_expression(mat, u.MaterialExpressionMultiply, -650, 150)
    mel.connect_material_expressions(spec, "", f0, "A")
    f0.set_editor_property("const_b", 0.08)

    fres = mel.create_material_expression(mat, u.MaterialExpressionFresnel, -1100, 300)
    rim_c = mel.create_material_expression(mat, u.MaterialExpressionVectorParameter, -1100, 450)
    rim_c.set_editor_property("parameter_name", "RimColor")
    rim_c.set_editor_property("default_value", u.LinearColor(1.0, 0.86, 0.72, 1.0))
    rim_s = mel.create_material_expression(mat, u.MaterialExpressionScalarParameter, -1100, 600)
    rim_s.set_editor_property("parameter_name", "RimStrength")
    rim_s.set_editor_property("default_value", 0.12)
    m1 = mel.create_material_expression(mat, u.MaterialExpressionMultiply, -800, 400)
    mel.connect_material_expressions(fres, "", m1, "A")
    mel.connect_material_expressions(rim_c, "", m1, "B")
    m2 = mel.create_material_expression(mat, u.MaterialExpressionMultiply, -600, 400)
    mel.connect_material_expressions(m1, "", m2, "A")
    mel.connect_material_expressions(rim_s, "", m2, "B")

    slab = mel.create_material_expression(mat, u.MaterialExpressionSubstrateSlabBSDF, -300, 0)
    got = {
        "albedo": pin(tex, slab, ["Diffuse Albedo", "DiffuseAlbedo"]),
        "roughness": pin(rough, slab, ["Roughness"]),
        "f0": pin(f0, slab, ["F0"]),
        "emissive": pin(m2, slab, ["Emissive Color", "EmissiveColor"]),
    }
    if not mel.connect_material_property(slab, "", u.MaterialProperty.MP_FRONT_MATERIAL):
        raise RuntimeError("could not connect Slab to Front Material on " + name)
    mel.recompile_material(mat)
    lib.save_loaded_asset(mat)
    report["materials"][name] = {"two_sided": two_sided, "pins": got, "backup": backup}


def main():
    if not u.SystemLibrary.get_console_variable_bool_value("r.Substrate"):
        raise RuntimeError("Substrate is off")
    rebuild("M_Character_Toon", False)
    rebuild("M_Character_Toon_TwoSided", True)
    report["status"] = "ok"


try:
    main()
finally:
    out = u.Paths.project_saved_dir() + "Characters/character_lit.json"
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
