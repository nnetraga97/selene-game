"""Anime look on top of the Toon BSDF prototype (requires r.Substrate=True and build_toon_materials.py run first).

From the 2026-11-06 shading research (Genshin/HSR/Guilty Gear practice), the two cheap, high-impact pieces:
  1. Two-band diffuse ramp on TP_Character (hard terminator, cool-violet shadow tint) and lower diffuse GI,
     so form reads as cel bands instead of soft PBR falloff.
  2. Inverted-hull outline: M_Character_Outline, an unlit masked two-sided material that pushes vertices
     along the normal (width grows mildly with camera distance) and keeps back faces only (TwoSidedSign).
     Applied as the skeletal meshes' Overlay Material, so no C++ is needed and it follows every switch.
Env: SELENE_OUTLINE_MESHES="/Game/path/mesh,..."  Writes Saved/Characters/toon_style.json. Headless is fine.
"""
import json
import os

import unreal as u

ROOT = u.Paths.convert_relative_path_to_full(u.Paths.project_dir())
BASE = "/Game/Selene/Materials/Character"
lib = u.EditorAssetLibrary
mel = u.MaterialEditingLibrary
tools = u.AssetToolsHelpers.get_asset_tools()
report = {"status": "failed", "steps": []}

SHADOW = (0.60, 0.55, 0.70)  # cool violet shadow multiplier
TERMINATOR = 0.48            # ramp input where the lit band starts
OUTLINE_COLOR = (0.06, 0.04, 0.05)
OUTLINE_WIDTH_CM = 0.25      # at 3 m; scaled by camera distance, clamped


def step(msg):
    report["steps"].append(msg)


def ramp_curve():
    """The ramp's inline keys are not exposed to Python, so build a CurveLinearColor asset through the CSV
    importer (linear keys; a 0.04-wide transition gives a crisp but anti-aliased terminator)."""
    csv = os.path.join(ROOT, "Saved", "Characters", "C_ToonDiffuseRamp.csv")
    edge = 0.02
    rows = [(0.0, *SHADOW, 1.0), (TERMINATOR - edge, *SHADOW, 1.0), (TERMINATOR + edge, 1.0, 1.0, 1.0, 1.0), (1.0, 1.0, 1.0, 1.0, 1.0)]
    with open(csv, "w") as f:
        f.write("\n".join(",".join("%g" % v for v in r) for r in rows) + "\n")
    factory = u.CSVImportFactory()
    settings = factory.get_editor_property("automated_import_settings")
    settings.set_editor_property("import_type", u.CSVImportType.ECSV_CURVE_LINEAR_COLOR)
    factory.set_editor_property("automated_import_settings", settings)
    task = u.AssetImportTask()
    for k, v in (("filename", csv), ("destination_path", BASE), ("destination_name", "C_ToonDiffuseRamp"),
                 ("automated", True), ("replace_existing", True), ("save", True), ("factory", factory)):
        task.set_editor_property(k, v)
    tools.import_asset_tasks([task])
    curve = u.load_asset(BASE + "/C_ToonDiffuseRamp")
    if not isinstance(curve, u.CurveLinearColor):
        raise RuntimeError("Ramp curve import failed: %r" % curve)
    report["ramp_samples"] = {t: [round(c, 3) for c in (lambda v: (v.r, v.g, v.b))(curve.get_linear_color_value(t))]
                              for t in (0.0, 0.4, 0.5, 0.8)}
    return curve


def tune_profile():
    profile = u.load_asset(BASE + "/TP_Character")
    if not profile:
        raise RuntimeError("TP_Character missing: run build_toon_materials.py first")
    s = profile.get_editor_property("settings")
    ramp = s.get_editor_property("diffuse_ramp")
    ramp.set_editor_property("external_curve", ramp_curve())
    s.set_editor_property("diffuse_ramp", ramp)
    s.set_editor_property("diffuse_indirect_scale", 0.6)
    profile.set_editor_property("settings", s)
    profile.modify()
    lib.save_loaded_asset(profile)
    back = profile.get_editor_property("settings")
    report["profile"] = {"external_curve": str(back.get_editor_property("diffuse_ramp").get_editor_property("external_curve")),
                         "diffuse_indirect_scale": back.get_editor_property("diffuse_indirect_scale")}
    step("profile tuned")


def outline_material():
    path = BASE + "/M_Character_Outline"
    mat = u.load_asset(path) if lib.does_asset_exist(path) else tools.create_asset(
        "M_Character_Outline", BASE, u.Material, u.MaterialFactoryNew())
    mel.delete_all_material_expressions(mat)
    mat.set_editor_property("shading_model", u.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", u.BlendMode.BLEND_MASKED)
    mat.set_editor_property("two_sided", True)
    mat.set_editor_property("used_with_skeletal_mesh", True)

    color = mel.create_material_expression(mat, u.MaterialExpressionVectorParameter, -600, -200)
    color.set_editor_property("parameter_name", "OutlineColor")
    color.set_editor_property("default_value", u.LinearColor(*OUTLINE_COLOR, 1.0))
    mel.connect_material_property(color, "", u.MaterialProperty.MP_EMISSIVE_COLOR)

    # Keep back faces only: TwoSidedSign is -1 on back faces.
    sign = mel.create_material_expression(mat, u.MaterialExpressionTwoSidedSign, -800, 0)
    neg = mel.create_material_expression(mat, u.MaterialExpressionMultiply, -600, 0)
    neg.set_editor_property("const_b", -1.0)
    mel.connect_material_expressions(sign, "", neg, "A")
    mel.connect_material_property(neg, "", u.MaterialProperty.MP_OPACITY_MASK)

    # WPO = VertexNormalWS * width * clamp(distance/300, 0.6, 3)
    normal = mel.create_material_expression(mat, u.MaterialExpressionVertexNormalWS, -1000, 300)
    width = mel.create_material_expression(mat, u.MaterialExpressionScalarParameter, -1000, 400)
    width.set_editor_property("parameter_name", "OutlineWidth")
    width.set_editor_property("default_value", OUTLINE_WIDTH_CM)
    cam = mel.create_material_expression(mat, u.MaterialExpressionCameraPositionWS, -1300, 500)
    wpos = mel.create_material_expression(mat, u.MaterialExpressionWorldPosition, -1300, 600)
    dist = mel.create_material_expression(mat, u.MaterialExpressionDistance, -1100, 550)
    mel.connect_material_expressions(cam, "", dist, "A")
    mel.connect_material_expressions(wpos, "", dist, "B")
    scale = mel.create_material_expression(mat, u.MaterialExpressionDivide, -950, 550)
    scale.set_editor_property("const_b", 300.0)
    mel.connect_material_expressions(dist, "", scale, "A")
    clamp = mel.create_material_expression(mat, u.MaterialExpressionClamp, -800, 550)
    clamp.set_editor_property("min_default", 0.6)
    clamp.set_editor_property("max_default", 3.0)
    mel.connect_material_expressions(scale, "", clamp, "")
    m1 = mel.create_material_expression(mat, u.MaterialExpressionMultiply, -650, 400)
    mel.connect_material_expressions(width, "", m1, "A")
    mel.connect_material_expressions(clamp, "", m1, "B")
    m2 = mel.create_material_expression(mat, u.MaterialExpressionMultiply, -500, 300)
    mel.connect_material_expressions(normal, "", m2, "A")
    mel.connect_material_expressions(m1, "", m2, "B")
    mel.connect_material_property(m2, "", u.MaterialProperty.MP_WORLD_POSITION_OFFSET)

    mel.recompile_material(mat)
    lib.save_loaded_asset(mat)
    step("outline material built")
    return mat


def apply_overlay(mat):
    report["overlay"] = {}
    for path in [p for p in os.environ.get("SELENE_OUTLINE_MESHES", "").split(",") if p]:
        mesh = u.load_asset(path)
        if not mesh:
            raise RuntimeError("Missing mesh " + path)
        mesh.set_editor_property("overlay_material", mat)
        lib.save_loaded_asset(mesh)
        report["overlay"][path] = mesh.get_editor_property("overlay_material").get_path_name()
    step("overlay applied")


try:
    if not u.SystemLibrary.get_console_variable_bool_value("r.Substrate"):
        raise RuntimeError("Substrate is off")
    tune_profile()
    apply_overlay(outline_material())
    report["status"] = "success"
except Exception as exc:
    import traceback
    report["error"] = str(exc)
    report["traceback"] = traceback.format_exc()
os.makedirs(os.path.join(ROOT, "Saved", "Characters"), exist_ok=True)
with open(os.path.join(ROOT, "Saved", "Characters", "toon_style.json"), "w") as f:
    json.dump(report, f, indent=2)
if report["status"] != "success":
    raise RuntimeError(report.get("error"))
