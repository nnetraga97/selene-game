"""Headless only: blender -b --python THIS_FILE -- --layout PATH --out DIR."""

import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Tools/Blockout"))
from layout_core import load, height, surface_pads, terrain_digest
from validate_layout import validate


def main():
    import bpy

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--layout", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    d = load(args.layout)
    errors = validate(d)
    if errors:
        raise RuntimeError("\n".join(errors))
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    x0, y0, x1, y1 = d["terrain"]["bounds"]
    grid = d["terrain"]["grid"]
    nx = math.ceil((x1 - x0) / grid)
    ny = math.ceil((y1 - y0) / grid)
    pads = surface_pads(d)
    verts = []
    faces = []
    for j in range(ny + 1):
        y = y0 + (y1 - y0) * j / ny
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            # Bake layout to Blender: (north, -east, up), metres.
            # glTF -> (north, up, east); UE -> (north, east, up), cm.
            verts.append((y, -x, height(d, x, y, pads)))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    mesh = bpy.data.meshes.new("SeleneTerrain")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("SeleneTerrain", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    uv = mesh.uv_layers.new(name="LayoutUV")
    for face in mesh.polygons:
        face.use_smooth = True
        for index in face.loop_indices:
            vx, vy, vz = mesh.vertices[mesh.loops[index].vertex_index].co
            uv.data[index].uv = ((-vy - x0) / (x1 - x0), (vx - y0) / (y1 - y0))
    mat = bpy.data.materials.new("TerrainGraybox")
    mat.diffuse_color = (0.34, 0.39, 0.29, 1)
    obj.data.materials.append(mat)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "terrain.blend"))
    bpy.ops.export_scene.gltf(
        filepath=str(out / "terrain.glb"),
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_apply=True,
    )
    report = dict(
        terrain_contract_sha256=terrain_digest(d),
        vertices=len(verts),
        quads=len(faces),
        bounds=d["terrain"]["bounds"],
        grid=grid,
        blender_axes="north,-east,up",
        unreal_axes="north,east,up",
        height_min=min(v[2] for v in verts),
        height_max=max(v[2] for v in verts),
    )
    (out / "terrain-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
