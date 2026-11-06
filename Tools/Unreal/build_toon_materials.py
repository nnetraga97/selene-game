"""Character toon shading prototype on Substrate's Toon BSDF (requires r.Substrate=True). Headless is fine.

Creates under /Game/Selene/Materials/Character:
  TP_Character      Toon Profile (engine default ramp for the first look; tuned after review)
  M_Character_Toon  Substrate Toon BSDF: BaseColorTex -> base colour, flat roughness/specular,
                    fresnel rim (RimColor * RimStrength) into the BSDF emissive
  MI_Toon_<Name>    one instance per character with its base-colour texture
Writes Saved/Characters/toon_materials.json. Characters are given as SELENE_TOON_CHARS="Name=/Game/path/to/basecolor,...".
"""
import json
import os

import unreal as u

ROOT = u.Paths.convert_relative_path_to_full(u.Paths.project_dir())
BASE = "/Game/Selene/Materials/Character"
lib = u.EditorAssetLibrary
mel = u.MaterialEditingLibrary
tools = u.AssetToolsHelpers.get_asset_tools()
report = {"status": "failed", "connections": {}}


def asset(name, cls, factory):
    path = BASE + "/" + name
    if lib.does_asset_exist(path):
        return u.load_asset(path)
    made = tools.create_asset(name, BASE, cls, factory)
    if not made:
        raise RuntimeError("Could not create " + path)
    return made


def connect(src, dst, names, key):
    """Substrate pins are matched by display name; try the likely spellings and record which one took."""
    for n in names:
        if mel.connect_material_expressions(src, "", dst, n):
            report["connections"][key] = n
            return
    raise RuntimeError("Could not connect %s (tried %s)" % (key, names))


def main():
    if not u.SystemLibrary.get_console_variable_bool_value("r.Substrate"):
        raise RuntimeError("Substrate is off: set r.Substrate=True in DefaultEngine.ini [/Script/Engine.RendererSettings]")
    profile = asset("TP_Character", u.ToonProfile, u.ToonProfileFactory())
    lib.save_loaded_asset(profile)

    mat = asset("M_Character_Toon", u.Material, u.MaterialFactoryNew())
    mel.delete_all_material_expressions(mat)
    mat.set_editor_property("two_sided", True)  # Tripo cloth/ribbons are single sheets (glTF doubleSided)
    toon = mel.create_material_expression(mat, u.MaterialExpressionSubstrateToonBSDF, -300, 0)
    toon.set_editor_property("toon_profile", profile)

    tex = mel.create_material_expression(mat, u.MaterialExpressionTextureSampleParameter2D, -900, -200)
    tex.set_editor_property("parameter_name", "BaseColorTex")
    connect(tex, toon, ["Base Color", "BaseColor"], "base_color")

    rough = mel.create_material_expression(mat, u.MaterialExpressionScalarParameter, -900, 50)
    rough.set_editor_property("parameter_name", "Roughness")
    rough.set_editor_property("default_value", 0.6)
    connect(rough, toon, ["Roughness"], "roughness")
    spec = mel.create_material_expression(mat, u.MaterialExpressionScalarParameter, -900, 150)
    spec.set_editor_property("parameter_name", "Specular")
    spec.set_editor_property("default_value", 0.35)
    connect(spec, toon, ["Specular"], "specular")

    fres = mel.create_material_expression(mat, u.MaterialExpressionFresnel, -1100, 300)
    fres.set_editor_property("exponent", 4.0)
    rim_c = mel.create_material_expression(mat, u.MaterialExpressionVectorParameter, -1100, 450)
    rim_c.set_editor_property("parameter_name", "RimColor")
    rim_c.set_editor_property("default_value", u.LinearColor(1.0, 0.92, 0.85, 1.0))
    rim_s = mel.create_material_expression(mat, u.MaterialExpressionScalarParameter, -1100, 600)
    rim_s.set_editor_property("parameter_name", "RimStrength")
    rim_s.set_editor_property("default_value", 0.12)
    m1 = mel.create_material_expression(mat, u.MaterialExpressionMultiply, -800, 400)
    mel.connect_material_expressions(fres, "", m1, "A")
    mel.connect_material_expressions(rim_c, "", m1, "B")
    m2 = mel.create_material_expression(mat, u.MaterialExpressionMultiply, -600, 400)
    mel.connect_material_expressions(m1, "", m2, "A")
    mel.connect_material_expressions(rim_s, "", m2, "B")
    connect(m2, toon, ["Emissive Color", "EmissiveColor"], "emissive")

    if not mel.connect_material_property(toon, "", u.MaterialProperty.MP_FRONT_MATERIAL):
        raise RuntimeError("Could not connect Toon BSDF to Front Material")
    mel.recompile_material(mat)
    lib.save_loaded_asset(mat)

    report["instances"] = {}
    for item in [x for x in os.environ.get("SELENE_TOON_CHARS", "").split(",") if x]:
        name, tex_path = item.split("=", 1)
        mi = asset("MI_Toon_" + name, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, mat)
        texture = u.load_asset(tex_path)
        if not texture:
            raise RuntimeError("Missing texture " + tex_path)
        mel.set_material_instance_texture_parameter_value(mi, "BaseColorTex", texture)
        lib.save_loaded_asset(mi)
        report["instances"][name] = mi.get_path_name()
    report["status"] = "success"


try:
    main()
except Exception as exc:
    import traceback
    report["error"] = str(exc)
    report["traceback"] = traceback.format_exc()
os.makedirs(os.path.join(ROOT, "Saved", "Characters"), exist_ok=True)
with open(os.path.join(ROOT, "Saved", "Characters", "toon_materials.json"), "w") as f:
    json.dump(report, f, indent=2)
if report["status"] != "success":
    raise RuntimeError(report.get("error"))
