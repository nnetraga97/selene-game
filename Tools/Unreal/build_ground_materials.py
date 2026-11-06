"""Import local Ground PNGs and build the world-space ground material, null-RHI safe.

Run UnrealEditor-Cmd Selene.uproject -run=pythonscript -script=<this file>
-unattended -nop4 -nosplash -nullrhi. Configuration: ground_materials.json.
No downloads; only /Game/Selene/Materials/Ground assets are saved.
"""
import json
import os
from pathlib import Path
import traceback

import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
CONFIG = ROOT / "Design/Blockout/ground_materials.json"
REPORT = {"status": "started", "textures": [], "instances": {}}
MEL = u.MaterialEditingLibrary
LIB = u.EditorAssetLibrary
TOOLS = u.AssetToolsHelpers.get_asset_tools()

# A shared absolute-world projection keeps adjacent differently scaled boxes aligned.
# Three planar samples blend by geometric normal; normals use the same projections
# and a surface-gradient perturbation, so zero strength returns the geometric normal.
SHADER = r"""
float3 n = normalize(N);
float3 w = pow(abs(n), 4.0);
w /= max(w.x + w.y + w.z, 0.0001);
float3 signs = float3(n.x < 0 ? -1 : 1, n.y < 0 ? -1 : 1, n.z < 0 ? -1 : 1);
float3 p = P / max(TileSizeMetres * 100.0, 1.0);
float2 ux = p.yz * float2(1, signs.x);
float2 uy = p.zx * float2(1, signs.y);
float2 uz = p.xy * float2(1, signs.z);
float3 color = Texture2DSample(BaseColorTex, BaseColorTexSampler, ux).rgb * w.x
             + Texture2DSample(BaseColorTex, BaseColorTexSampler, uy).rgb * w.y
             + Texture2DSample(BaseColorTex, BaseColorTexSampler, uz).rgb * w.z;
float lum = dot(color, float3(0.2126, 0.7152, 0.0722));
float3 macroP = P / max(MacroSizeMetres * 100.0, 1.0);
float variation = sin(dot(macroP, float3(1.71, 2.31, 0.83)))
                * sin(dot(macroP, float3(-2.11, 0.97, 1.37))) * 0.65
                + sin(dot(macroP, float3(4.13, -3.17, 2.19))) * 0.35;
color = lerp(lum.xxx, color, saturate(Saturation)) * Tint
      * (1.0 + variation * saturate(MacroStrength));
float3 nx = UnpackNormalMap(Texture2DSample(NormalTex, NormalTexSampler, ux)).xyz;
float3 ny = UnpackNormalMap(Texture2DSample(NormalTex, NormalTexSampler, uy)).xyz;
float3 nz = UnpackNormalMap(Texture2DSample(NormalTex, NormalTexSampler, uz)).xyz;
float3 perturb = float3(0, nx.x, nx.y * signs.x) * w.x / max(nx.z, 0.2)
               + float3(ny.y * signs.y, 0, ny.x) * w.y / max(ny.z, 0.2)
               + float3(nz.x, nz.y * signs.z, 0) * w.z / max(nz.z, 0.2);
WorldNormal = normalize(n + (perturb - n * dot(n, perturb)) * NormalStrength);
float rough = Texture2DSample(RoughnessTex, RoughnessTexSampler, ux).r * w.x
            + Texture2DSample(RoughnessTex, RoughnessTexSampler, uy).r * w.y
            + Texture2DSample(RoughnessTex, RoughnessTexSampler, uz).r * w.z;
Roughness = clamp(rough * RoughnessScale, 0.45, 1.0);
float ao = Texture2DSample(AOTex, AOTexSampler, ux).r * w.x
         + Texture2DSample(AOTex, AOTexSampler, uy).r * w.y
         + Texture2DSample(AOTex, AOTexSampler, uz).r * w.z;
Occlusion = lerp(1.0, ao, 0.45);
return saturate(color);
"""


def checked(value, message):
    if not value:
        raise RuntimeError(message)
    return value


def asset(base, name, cls, factory):
    path = base + "/" + name
    result = u.load_asset(path) if LIB.does_asset_exist(path) else TOOLS.create_asset(name, base, cls, factory)
    if not isinstance(result, cls):
        raise RuntimeError("Missing or wrong asset type: " + path)
    return result


def texture_sources(name):
    files = list((ROOT / "SourceArt/Ground" / name).glob("*.png"))
    result = {}
    for role, suffixes in {
        "BaseColorTex": ("basecolor", "color"), "NormalTex": ("normaldx",),
        "RoughnessTex": ("roughness",), "AOTex": ("ambientocclusion",),
        "HeightTex": ("height",),
    }.items():
        matches = [p for p in files if any(p.stem.lower().replace("_", "").endswith(s + "2k") for s in suffixes)]
        if len(matches) != 1:
            raise RuntimeError(f"Expected one {role} PNG for {name}: {matches}")
        result[role] = matches[0]
    return result


def import_textures(base, sources):
    result = {}
    for name, roles in sources.items():
        result[name] = {}
        for role, source in roles.items():
            task = u.AssetImportTask()
            for key, value in dict(filename=str(source), destination_path=base + "/" + name,
                                   destination_name="T_" + name + "_" + role,
                                   automated=True, replace_existing=True, save=False).items():
                task.set_editor_property(key, value)
            TOOLS.import_asset_tasks([task])
            paths = task.get_editor_property("imported_object_paths")
            if len(paths) != 1:
                raise RuntimeError("Texture import failed: " + str(source))
            tex = checked(u.load_asset(paths[0]), "Missing imported texture")
            tex.set_editor_property("srgb", role == "BaseColorTex")
            tex.set_editor_property("compression_settings", u.TextureCompressionSettings.TC_NORMALMAP if role == "NormalTex"
                                    else u.TextureCompressionSettings.TC_DEFAULT if role == "BaseColorTex"
                                    else u.TextureCompressionSettings.TC_MASKS)
            if role == "NormalTex":
                tex.set_editor_property("flip_green_channel", False)  # supplied DirectX normal
            tex.set_editor_property("virtual_texture_streaming", False)
            checked(LIB.save_loaded_asset(tex, only_if_is_dirty=False), "Texture save failed")
            result[name][role] = tex
            REPORT["textures"].append(dict(source=str(source), asset=tex.get_path_name(),
                                           srgb=bool(tex.get_editor_property("srgb")),
                                           compression=str(tex.get_editor_property("compression_settings"))))
    return result


def build_parent(base, textures):
    mat = asset(base, "M_Ground_Stylized", u.Material, u.MaterialFactoryNew())
    mat.modify()
    MEL.delete_all_material_expressions(mat)
    mat.set_editor_property("tangent_space_normal", False)
    custom = MEL.create_material_expression(mat, u.MaterialExpressionCustom, 0, 0)
    custom.set_editor_property("description", "Metre-scaled triplanar ground with world-space normals and macro variation")
    custom.set_editor_property("output_type", u.CustomMaterialOutputType.CMOT_FLOAT3)
    custom.set_editor_property("code", SHADER)
    nodes = {
        "P": MEL.create_material_expression(mat, u.MaterialExpressionWorldPosition, -600, -500),
        "N": MEL.create_material_expression(mat, u.MaterialExpressionVertexNormalWS, -600, -350),
    }
    defaults = dict(TileSizeMetres=3.0, Saturation=0.6, NormalStrength=0.3,
                    RoughnessScale=1.0, MacroStrength=0.1, MacroSizeMetres=13.0)
    for i, (name, value) in enumerate(defaults.items()):
        node = MEL.create_material_expression(mat, u.MaterialExpressionScalarParameter, -600, i * 140)
        node.set_editor_property("parameter_name", name)
        node.set_editor_property("default_value", value)
        nodes[name] = node
    tint = MEL.create_material_expression(mat, u.MaterialExpressionVectorParameter, -600, 900)
    tint.set_editor_property("parameter_name", "Tint")
    tint.set_editor_property("default_value", u.LinearColor(1, 1, 1, 1))
    nodes["Tint"] = tint
    for i, role in enumerate(("BaseColorTex", "NormalTex", "RoughnessTex", "AOTex")):
        node = MEL.create_material_expression(mat, u.MaterialExpressionTextureObjectParameter, -1000, i * 220)
        node.set_editor_property("parameter_name", role)
        node.set_editor_property("texture", textures[role])
        node.set_editor_property("sampler_type", u.MaterialSamplerType.SAMPLERTYPE_COLOR if role == "BaseColorTex"
                                 else u.MaterialSamplerType.SAMPLERTYPE_NORMAL if role == "NormalTex"
                                 else u.MaterialSamplerType.SAMPLERTYPE_MASKS)
        nodes[role] = node
    inputs = []
    for name in nodes:
        inp = u.CustomInput()
        inp.set_editor_property("input_name", name)
        inputs.append(inp)
    custom.set_editor_property("inputs", inputs)
    outputs = []
    for name, kind in (("WorldNormal", u.CustomMaterialOutputType.CMOT_FLOAT3),
                       ("Roughness", u.CustomMaterialOutputType.CMOT_FLOAT1),
                       ("Occlusion", u.CustomMaterialOutputType.CMOT_FLOAT1)):
        out = u.CustomOutput()
        out.set_editor_property("output_name", name)
        out.set_editor_property("output_type", kind)
        outputs.append(out)
    custom.set_editor_property("additional_outputs", outputs)
    for name, node in nodes.items():
        checked(MEL.connect_material_expressions(node, "", custom, name), "Cannot connect " + name)
    for output, prop in (("", u.MaterialProperty.MP_BASE_COLOR), ("WorldNormal", u.MaterialProperty.MP_NORMAL),
                         ("Roughness", u.MaterialProperty.MP_ROUGHNESS), ("Occlusion", u.MaterialProperty.MP_AMBIENT_OCCLUSION)):
        checked(MEL.connect_material_property(custom, output, prop), "Cannot connect output " + output)
    spec = MEL.create_material_expression(mat, u.MaterialExpressionConstant, 0, 700)
    spec.set_editor_property("r", 0.25)
    checked(MEL.connect_material_property(spec, "", u.MaterialProperty.MP_SPECULAR), "Cannot connect specular")
    MEL.recompile_material(mat)
    checked(LIB.save_loaded_asset(mat, only_if_is_dirty=False), "Parent material save failed")
    REPORT["parent"] = mat.get_path_name()
    return mat


def main():
    data = json.loads(CONFIG.read_text())
    base = data["asset_root"]
    # Validate all source paths before importing anything.
    sources = {name: texture_sources(name) for name in data["materials"]}
    textures = import_textures(base, sources)
    # SELENE_GROUND_SKIP_PARENT=1 reuses the saved parent: instances created in the same session as a parent
    # rebuild could not find its texture parameters yet ("Cannot set BaseColorTex").
    if os.environ.get("SELENE_GROUND_SKIP_PARENT") == "1" and LIB.does_asset_exist(base + "/M_Ground_Stylized"):
        mat = u.load_asset(base + "/M_Ground_Stylized")
        REPORT["parent"] = mat.get_path_name()
    else:
        mat = build_parent(base, textures["ground_tiles_27"])
    if os.environ.get("SELENE_GROUND_PARENT_ONLY") == "1":
        REPORT["status"] = "success"
        return
    for name, settings in data["materials"].items():
        mi = asset(base, "MI_Ground_" + name, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        mi.modify()
        MEL.set_material_instance_parent(mi, mat)
        # MaterialEditingLibrary.set_material_instance_texture_parameter_value refuses TextureObjectParameters
        # (returns False even though the parent exposes them), so write the override list directly.
        overrides = []
        for role, tex in textures[name].items():
            if role != "HeightTex":
                value = u.TextureParameterValue()
                info = u.MaterialParameterInfo()
                info.set_editor_property("name", role)
                value.set_editor_property("parameter_info", info)
                value.set_editor_property("parameter_value", tex)
                overrides.append(value)
        mi.set_editor_property("texture_parameter_values", overrides)
        got = {str(v.parameter_info.name): v.parameter_value for v in mi.get_editor_property("texture_parameter_values")}
        for role, tex in textures[name].items():
            if role != "HeightTex":
                checked(got.get(role) == tex, "Cannot set " + role)
        # UE 5.8's MaterialEditingLibrary setters return False even when the value is applied (probe: set ->
        # False, get -> new value), so verify by reading back instead of trusting the return value.
        for key, value in settings["scalars"].items():
            MEL.set_material_instance_scalar_parameter_value(mi, key, value)
            checked(abs(MEL.get_material_instance_scalar_parameter_value(mi, key) - value) < 1e-4, "Cannot set " + key)
        tint = u.LinearColor(*settings["tint_linear"], 1)
        MEL.set_material_instance_vector_parameter_value(mi, "Tint", tint)
        got = MEL.get_material_instance_vector_parameter_value(mi, "Tint")
        checked(abs(got.r - tint.r) + abs(got.g - tint.g) + abs(got.b - tint.b) < 1e-4, "Cannot set tint")
        MEL.update_material_instance(mi)
        checked(LIB.save_loaded_asset(mi, only_if_is_dirty=False), "Instance save failed")
        REPORT["instances"][name] = dict(asset=mi.get_path_name(), **settings)
    REPORT["status"] = "success"
    REPORT["shader_validation"] = "Null-RHI creates assets; final rendered shots and editor shader log must validate the GPU shader."


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        REPORT.update(status="failed", error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        path = Path(os.environ["SELENE_STAGE_REPORT"]) if os.environ.get("SELENE_STAGE_REPORT") else ROOT / "Saved/Ground/materials.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        REPORT["invocation"] = os.environ.get("SELENE_STAGE_ID")
        path.write_text(json.dumps(REPORT, indent=2) + "\n")
        u.log("Ground material report: " + str(path))
