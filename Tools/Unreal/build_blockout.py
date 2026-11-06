"""Rebuild /Game/Selene/Maps/Town from the versioned layout. Headless UE Python.

Environment: SELENE_LAYOUT, SELENE_TERRAIN_GLB (both required).
Only actors tagged SeleneBlockout are removed on a rebuild. Untagged user actors
are preserved. Failure writes a report and raises to fail the commandlet.
"""

import hashlib
import json
import math
import os
from pathlib import Path
import sys
import traceback

import unreal as u

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Tools/Blockout"))
from layout_core import load, world_xy, height, route_points, distances, terrain_digest
from validate_layout import validate

MAP = "/Game/Selene/Maps/Town"
ASSETS = "/Game/Selene/Blockout"
TAG = "SeleneBlockout"
REPORT = {
    "status": "started",
    "warnings": [],
    "actors_per_area": {},
    "lots_per_area": {},
    "routes": {},
}
ACTORS = None
MATERIALS = {}
CUBE = None


def warn(text):
    REPORT["warnings"].append(text)
    u.log_warning(text)


def vec(p):
    return u.Vector(p[1] * 100, p[0] * 100, p[2] * 100)


def spawn(cls, name, p, area, rotation=None):
    actor = ACTORS.spawn_actor_from_class(cls, vec(p), rotation or u.Rotator())
    if not actor:
        raise RuntimeError("Could not spawn " + name)
    actor.set_actor_label(name)
    actor.set_folder_path("Blockout/" + area)
    actor.set_editor_property("tags", [u.Name(TAG), u.Name("Area_" + area)])
    REPORT["actors_per_area"][area] = REPORT["actors_per_area"].get(area, 0) + 1
    return actor


def box(name, p, size, area, angle=0, material=None, collision=True, pitch=0):
    actor = spawn(
        u.StaticMeshActor, name, p, area, u.Rotator(pitch=pitch, yaw=90 - angle, roll=0)
    )
    component = actor.static_mesh_component
    component.set_static_mesh(CUBE)
    component.set_material(0, material or MATERIALS.get(area, MATERIALS["neutral"]))
    component.set_collision_enabled(
        u.CollisionEnabled.QUERY_AND_PHYSICS
        if collision
        else u.CollisionEnabled.NO_COLLISION
    )
    actor.set_actor_scale3d(
        u.Vector(*size)
    )  # Engine cube is 100 cm; metre dimensions = scale.
    return actor


def make_materials(data):
    tools = u.AssetToolsHelpers.get_asset_tools()
    lib = u.MaterialEditingLibrary
    parent = u.load_asset("/Game/LevelPrototyping/Materials/M_PrototypeGrid")
    if not parent:
        warn("LevelPrototyping grid missing; generating world-space 1 m grid fallback.")
        path = ASSETS + "/Materials/M_BlockoutGrid"
        parent = u.load_asset(path)
        if not parent:
            parent = tools.create_asset(
                "M_BlockoutGrid",
                ASSETS + "/Materials",
                u.Material,
                u.MaterialFactoryNew(),
            )
            # World position -> 1 m periodic grid, independent of cube scaling.
            pos = lib.create_material_expression(
                parent, u.MaterialExpressionWorldPosition
            )
            custom = lib.create_material_expression(parent, u.MaterialExpressionCustom)
            custom.set_editor_property(
                "code",
                "float3 f=frac(P/100.0); float3 g=step(0.025,f)*step(f,0.975); float3 n=abs(N); float grid=(n.z>0.5)?min(g.x,g.y):((n.x>n.y)?min(g.y,g.z):min(g.x,g.z)); return grid*0.28+0.72;",
            )
            custom.set_editor_property(
                "output_type", u.CustomMaterialOutputType.CMOT_FLOAT1
            )
            inp = u.CustomInput()
            inp.set_editor_property("input_name", "P")
            normal_input = u.CustomInput()
            normal_input.set_editor_property("input_name", "N")
            custom.set_editor_property("inputs", [inp, normal_input])
            normal = lib.create_material_expression(
                parent, u.MaterialExpressionVertexNormalWS
            )
            lib.connect_material_expressions(pos, "", custom, "P")
            lib.connect_material_expressions(normal, "", custom, "N")
            color = lib.create_material_expression(
                parent, u.MaterialExpressionVectorParameter
            )
            color.set_editor_property("parameter_name", "BlockoutTint")
            mul = lib.create_material_expression(parent, u.MaterialExpressionMultiply)
            lib.connect_material_expressions(custom, "", mul, "A")
            lib.connect_material_expressions(color, "", mul, "B")
            lib.connect_material_property(mul, "", u.MaterialProperty.MP_BASE_COLOR)
            lib.recompile_material(parent)
    params = list(lib.get_vector_parameter_names(parent))
    REPORT["grid_parent"] = parent.get_path_name()
    REPORT["grid_vector_parameters"] = [str(p) for p in params]
    # PrototypeGrid exposes Color parameters; tint all color parameters consistently.
    tint_names = [
        p
        for p in params
        if any(s in str(p).lower() for s in ("color", "colour", "tint"))
    ]
    if not tint_names:
        warn(
            "Grid material exposes no tint parameter; inspect grid_vector_parameters in report."
        )
    palette = {a["id"]: a["color"] for a in data["areas"]}
    palette.update(
        neutral="#b5b3a7", terrain="#798568", bay="#7399ac", accent="#c78470"
    )
    for area, color in palette.items():
        name = "MI_" + area
        mi = u.load_asset(ASSETS + "/Materials/" + name)
        if not mi:
            mi = tools.create_asset(
                name,
                ASSETS + "/Materials",
                u.MaterialInstanceConstant,
                u.MaterialInstanceConstantFactoryNew(),
            )
        lib.set_material_instance_parent(mi, parent)
        rgb = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = u.LinearColor(*[v**2.2 for v in rgb], 1)
        for parameter in tint_names:
            # Dark contrasting grid lines preserve scale cues on every area tint.
            value = (
                linear
                if "surface" in str(parameter).lower()
                or "tint" in str(parameter).lower()
                else u.LinearColor(
                    *[v * 0.35 for v in [linear.r, linear.g, linear.b]], 1
                )
            )
            lib.set_material_instance_vector_parameter_value(mi, parameter, value)
        MATERIALS[area] = mi
    glass = u.load_asset(ASSETS + "/Materials/M_Glass")
    if not glass:
        glass = tools.create_asset(
            "M_Glass", ASSETS + "/Materials", u.Material, u.MaterialFactoryNew()
        )
        glass.set_editor_property("blend_mode", u.BlendMode.BLEND_TRANSLUCENT)
        c = lib.create_material_expression(glass, u.MaterialExpressionConstant3Vector)
        c.set_editor_property("constant", u.LinearColor(0.15, 0.3, 0.35, 1))
        opacity = lib.create_material_expression(glass, u.MaterialExpressionConstant)
        opacity.set_editor_property("r", 0.18)
        lib.connect_material_property(c, "", u.MaterialProperty.MP_BASE_COLOR)
        lib.connect_material_property(opacity, "", u.MaterialProperty.MP_OPACITY)
        lib.recompile_material(glass)
    MATERIALS["glass"] = glass


def lot_box(lot, suffix, local, size, material=None, collision=True):
    xy = world_xy(lot["footprint"], *local[:2])
    return box(
        lot["id"] + "_" + suffix,
        [*xy, lot["base_z"] + local[2]],
        size,
        lot["area"],
        lot["footprint"].get("rotation", 0),
        material,
        collision,
    )


def build_shell(lot):
    shell = lot["interior"]
    w, d = lot["footprint"]["size"]
    h = shell["clear_height"]
    t = shell["wall_thickness"]
    lot_box(lot, "floor", [0, 0, -0.1], [w, d, 0.2])
    lot_box(lot, "roof", [0, 0, h + 0.15], [w, d, 0.3])
    for wall in ("north", "south", "east", "west"):
        horizontal = wall in ("north", "south")
        span = w if horizontal else d
        fixed = (
            (d / 2 - t / 2) * (1 if wall == "north" else -1)
            if horizontal
            else (w / 2 - t / 2) * (1 if wall == "east" else -1)
        )
        openings = sorted(
            [o for o in shell["openings"] if o["wall"] == wall],
            key=lambda o: o["offset"],
        )

        def piece(a, b, z0, z1, suffix, material=None, collision=True):
            if b - a < 0.001 or z1 - z0 < 0.001:
                return
            local = (
                [(a + b) / 2, fixed, (z0 + z1) / 2]
                if horizontal
                else [fixed, (a + b) / 2, (z0 + z1) / 2]
            )
            size = [b - a, t, z1 - z0] if horizontal else [t, b - a, z1 - z0]
            lot_box(lot, wall + "_" + suffix, local, size, material, collision)

        cursor = -span / 2
        for i, o in enumerate(openings):
            a = o["offset"] - o["width"] / 2
            b = o["offset"] + o["width"] / 2
            piece(cursor, a, 0, h, "pier_%d" % i)
            piece(a, b, 0, o["sill"], "sill_%d" % i)
            piece(a, b, o["sill"] + o["height"], h, "lintel_%d" % i)
            if o["kind"] == "window":
                piece(
                    a,
                    b,
                    o["sill"],
                    o["sill"] + o["height"],
                    "glass_%d" % i,
                    MATERIALS["glass"],
                    False,
                )
            cursor = b
        piece(cursor, span / 2, 0, h, "end")
    full = lot["ground_height"] + (lot["storeys"] - 1) * lot["floor_height"]
    if full > h + 0.3:
        lot_box(lot, "upper_mass", [0, 0, (full + h + 0.3) / 2], [w, d, full - h - 0.3])
    for prop in shell.get("props", []):
        ph = prop["size"][2]
        lot_box(
            lot,
            prop["id"],
            [*prop["center"], ph / 2],
            prop["size"],
            MATERIALS["accent"],
        )


def buildings(data):
    for lot in data["lots"]:
        REPORT["lots_per_area"][lot["area"]] = (
            REPORT["lots_per_area"].get(lot["area"], 0) + 1
        )
        w, d = lot["footprint"]["size"]
        h = lot["ground_height"] + (lot["storeys"] - 1) * lot["floor_height"]
        if "interior" in lot:
            build_shell(lot)
        elif lot.get("corner_radius"):
            # Twelve cube strips approximate curved corners without new mesh assets.
            radius = lot["corner_radius"]
            n = 12
            for i in range(n):
                y = -d / 2 + (i + 0.5) * d / n
                dy = max(0, abs(y) - (d / 2 - radius))
                inset = radius - math.sqrt(max(0, radius * radius - dy * dy))
                lot_box(
                    lot,
                    "round_%02d" % i,
                    [0, y, h / 2],
                    [w - 2 * inset, d / n + 0.01, h],
                )
        else:
            lot_box(lot, "mass", [0, 0, h / 2], [w, d, h])
        if lot["hero"]:
            lot_box(
                lot,
                "hero_canopy",
                [0, -d / 2 - 0.8, 3.5],
                [w * 0.85, 1.6, 0.2],
                MATERIALS["accent"],
                False,
            )
        if lot.get("landmark") == "clock_tower":
            lot_box(lot, "tower", [0, 0, 16], [8, 8, 17])
            lot_box(lot, "tower_cap", [0, 0, 24.7], [11, 11, 0.6], MATERIALS["accent"])
            # Readable clock placeholder, no texture dependency.
            lot_box(
                lot,
                "clock_face",
                [0, -4.05, 20],
                [4, 0.12, 4],
                MATERIALS["neutral"],
                False,
            )
            lot_box(
                lot,
                "clock_hand_vertical",
                [0, -4.14, 20.5],
                [0.13, 0.1, 1.4],
                MATERIALS["accent"],
                False,
            )
            lot_box(
                lot,
                "clock_hand_horizontal",
                [0.5, -4.14, 20],
                [1.3, 0.1, 0.13],
                MATERIALS["accent"],
                False,
            )


def corridor(name, a, b, width, area, thickness=0.16, material=None):
    dx, dy, dz = [b[i] - a[i] for i in range(3)]
    horizontal = math.hypot(dx, dy)
    angle = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, horizontal))
    return box(
        name,
        [
            (a[0] + b[0]) / 2,
            (a[1] + b[1]) / 2,
            (a[2] + b[2]) / 2 - thickness / 2 + 0.025,
        ],
        [math.sqrt(horizontal**2 + dz**2) + 0.03, width, thickness],
        area,
        angle,
        material,
        pitch=pitch,
    )


def infrastructure(data):
    for s in data["slabs"]:
        box(s["id"], [*s["center"], s["z"] - 0.075], s["size"] + [0.2], s["area"])
    for s in data["streets"]:
        for i, (a, b) in enumerate(zip(s["points"], s["points"][1:])):
            corridor(s["id"] + "_%d" % i, a, b, s["width"], s["area"])
    for s in data["stairs"]:
        for a, b in zip(s["points"], s["points"][1:]):
            n = math.ceil(abs(b[2] - a[2]) / s["max_riser"])
            dx, dy = b[0] - a[0], b[1] - a[1]
            run = math.hypot(dx, dy)
            angle = math.degrees(math.atan2(dy, dx))
            bottom = min(a[2], b[2]) - 0.25
            for i in range(n):
                t = (i + 0.5) / n
                top = a[2] + (b[2] - a[2]) * (i + 1) / n
                box(
                    s["id"] + "_step_%03d" % i,
                    [a[0] + t * dx, a[1] + t * dy, (top + bottom) / 2],
                    [run / n + 0.015, s["width"], top - bottom],
                    s["area"],
                    angle,
                )
    v = data["viaduct"]
    a, b = v["points"]
    corridor("monorail_deck", a, b, v["width"], v["area"], v["deck_thickness"])
    run = math.dist(a[:2], b[:2])
    n = math.ceil(run / v["pier_spacing"])
    for i in range(n + 1):
        t = i / n
        x = a[0] + t * (b[0] - a[0])
        y = a[1] + t * (b[1] - a[1])
        top = a[2] + t * (b[2] - a[2]) - v["deck_thickness"]
        if any(lo <= x <= hi for lo, hi in v.get("exclude_piers", [])):
            continue
        base = height(data, x, y)
        box(
            "monorail_pier_%02d" % i,
            [x, y, (base + top) / 2],
            [v["pier_size"], v["pier_size"], top - base],
            v["area"],
        )
    for boundary in data["boundaries"]:
        a, b = boundary["points"]
        run = math.dist(a[:2], b[:2])
        n = math.ceil(run / 8)
        for i in range(n):
            p = [a[j] + (b[j] - a[j]) * i / n for j in range(3)]
            q = [a[j] + (b[j] - a[j]) * (i + 1) / n for j in range(3)]
            p[2] = height(data, *p[:2])
            q[2] = height(data, *q[:2])
            corridor(
                boundary["id"] + "_embankment_%d" % i,
                p,
                q,
                2,
                "boundary",
                boundary["embankment_depth"],
            )
            for offset in (0.6, 1.1):
                corridor(
                    boundary["id"] + "_rail_%d_%.1f" % (i, offset),
                    [p[0], p[1], p[2] + offset],
                    [q[0], q[1], q[2] + offset],
                    0.1,
                    "boundary",
                    0.1,
                )
            box(
                boundary["id"] + "_post_%d" % i,
                [p[0], p[1], p[2] + 0.55],
                [0.12, 0.12, 1.1],
                "boundary",
            )
    b = data["backdrop"]
    box(
        "distant_bay",
        b["center"],
        b["size"] + [0.2],
        "backdrop",
        material=MATERIALS["bay"],
        collision=False,
    )
    if "west_extension" in b:
        west = b["west_extension"]
        box(
            "western_bay",
            west["center"],
            west["size"] + [0.2],
            "backdrop",
            material=MATERIALS["bay"],
            collision=False,
        )


def import_terrain(glb):
    manager = u.InterchangeManager.get_interchange_manager_scripted()
    source = manager.create_source_data(str(glb))
    params = u.ImportAssetParameters()
    params.set_editor_property("is_automated", True)
    params.set_editor_property("replace_existing", True)
    params.set_editor_property("destination_name", "SeleneTerrain")
    if not manager.import_asset(ASSETS + "/Terrain", source, params):
        raise RuntimeError("Interchange terrain import failed")
    meshes = [
        u.load_asset(p)
        for p in u.EditorAssetLibrary.list_assets(ASSETS + "/Terrain", recursive=True)
        if isinstance(u.load_asset(p), u.StaticMesh)
    ]
    if len(meshes) != 1:
        raise RuntimeError(
            f"Expected exactly one terrain StaticMesh; found {len(meshes)}"
        )
    mesh = meshes[0]
    body = mesh.get_editor_property("body_setup")
    body.set_editor_property(
        "collision_trace_flag", u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
    )
    actor = spawn(u.StaticMeshActor, "SeleneTerrain", [0, 0, 0], "terrain")
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.static_mesh_component.set_material(0, MATERIALS["terrain"])
    actor.static_mesh_component.set_collision_enabled(
        u.CollisionEnabled.QUERY_AND_PHYSICS
    )
    REPORT["terrain_asset"] = mesh.get_path_name()
    origin, extent = actor.get_actor_bounds(False)
    REPORT["terrain_bounds_cm"] = {
        "origin": [origin.x, origin.y, origin.z],
        "extent": [extent.x, extent.y, extent.z],
    }
    # glTF metres must have become centimetres, with north aligned to UE X.
    if abs(extent.x - 20000) > 10 or abs(extent.y - 24000) > 10:
        raise RuntimeError(
            "Terrain axis/unit mismatch; refusing to save incorrect Town"
        )


def routes(data):
    cls = u.load_class(None, "/Script/Selene.SelenePerfRoute")
    if not cls:
        warn(
            "SelenePerfRoute class unavailable; skipped route actors (route metrics still reported)."
        )
    for route in data["routes"]:
        points = route_points(data, route)
        ds = distances(points)
        segments = [
            dict(
                tag=s["tag"],
                start_distance=ds[s["start_index"]] * 100,
                end_distance=ds[s["end_index"]] * 100,
            )
            for s in route["segments"]
        ]
        REPORT["routes"][route["id"]] = {
            "length_m": ds[-1],
            "segments_cm": segments,
            "look_at": route.get("look_at"),
        }
        if route.get("look_at"):
            for suffix, p in [("start", points[0]), ("end", points[-1])]:
                camera = spawn(
                    u.CameraActor,
                    route["id"] + "_view_" + suffix,
                    p,
                    "routes",
                    u.MathLibrary.find_look_at_rotation(vec(p), vec(route["look_at"])),
                )
                camera.camera_component.set_editor_property("field_of_view", 70.0)
        if not cls:
            continue
        actor = spawn(cls, route["id"], [0, 0, 0], "routes")
        actor.set_editor_property("route_name", u.Name(route["id"]))
        spline = next(
            (
                c
                for c in actor.get_components_by_class(u.SplineComponent)
                if c.get_name() == "Route"
            ),
            None,
        )
        if not spline:
            raise RuntimeError("SelenePerfRoute has no Route spline component")
        spline.clear_spline_points(False)
        for p in points:
            spline.add_spline_point(vec(p), u.SplineCoordinateSpace.WORLD, False)
        for i in range(len(points)):
            spline.set_spline_point_type(i, u.SplinePointType.LINEAR, False)
        spline.update_spline()
        actor.set_editor_property("segments", segments)
        if abs(spline.get_spline_length() / 100 - ds[-1]) > 0.05:
            raise RuntimeError("Route spline distance mismatch")
    p = data["player_start"]
    spawn(
        u.PlayerStart,
        "Town_PlayerStart",
        p["position"],
        "plaza",
        u.MathLibrary.find_look_at_rotation(vec(p["position"]), vec(p["look_at"])),
    )
    tod = u.load_class(None, "/Script/Selene.SeleneTimeOfDay")
    if tod:
        spawn(tod, "Town_TimeOfDay", [0, 0, 0], "lighting")
    else:
        warn(
            "SeleneTimeOfDay class unavailable; using default sun, sky light and atmosphere."
        )
        sun = spawn(
            u.DirectionalLight,
            "Blockout_Sun",
            [0, 0, 80],
            "lighting",
            u.Rotator(pitch=-40, yaw=-35, roll=0),
        )
        sun.light_component.set_editor_property("intensity", 5.0)
        spawn(u.SkyLight, "Blockout_Sky", [0, 0, 60], "lighting")
        spawn(u.SkyAtmosphere, "Blockout_Atmosphere", [0, 0, 0], "lighting")


def external_actors(level):
    # Prefer callable conversions if a future engine exposes them. UE 5.8's
    # SetUseExternalActors and ConvertAllActorsToPackaging are not UFUNCTIONs.
    if level.get_editor_property("use_external_actors"):
        external = [
            a.is_package_external()
            for a in ACTORS.get_all_level_actors()
            if a.actor_has_tag(TAG)
        ]
        REPORT["external_actors"] = (
            "enabled"
            if all(external)
            else "flag enabled, but some actors are internal; run conversion commandlet again"
        )
        REPORT["external_generated_actor_count"] = sum(external)
    elif hasattr(level, "set_use_external_actors") and hasattr(
        level, "convert_all_actors_to_packaging"
    ):
        level.set_use_external_actors(True)
        level.convert_all_actors_to_packaging(True)
        REPORT["external_actors"] = "enabled and converted through Python API"
    else:
        REPORT["external_actors"] = (
            "not enabled: UE 5.8 Level conversion methods are not reflected to Python"
        )
        warn(
            "OFPA requires the stock ConvertLevelsToExternalActors commandlet after this build; see README. The editable use_external_actors flag alone does not convert existing actor packages."
        )


def main():
    global ACTORS, CUBE
    layout = Path(os.environ["SELENE_LAYOUT"]).resolve()
    glb = Path(os.environ["SELENE_TERRAIN_GLB"]).resolve()
    if not glb.is_file():
        raise RuntimeError("Missing SELENE_TERRAIN_GLB: " + str(glb))
    data = load(layout)
    errors = validate(data)
    if errors:
        raise RuntimeError("\n".join(errors))
    terrain_report = glb.parent / "terrain-report.json"
    if terrain_report.is_file():
        exported = json.loads(terrain_report.read_text()).get("terrain_contract_sha256")
        if exported and exported != terrain_digest(data):
            raise RuntimeError(
                "Stale terrain export: regenerate Blender terrain from current layout"
            )
        REPORT["terrain_contract_sha256"] = exported
    else:
        warn("No terrain-report.json sidecar; height-input identity cannot be checked.")

    REPORT.update(
        layout=str(layout),
        layout_sha256=hashlib.sha256(layout.read_bytes()).hexdigest(),
        terrain_glb_sha256=hashlib.sha256(glb.read_bytes()).hexdigest(),
        engine=u.SystemLibrary.get_engine_version(),
    )
    ACTORS = u.get_editor_subsystem(u.EditorActorSubsystem)
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    if u.EditorAssetLibrary.does_asset_exist(MAP):
        if not levels.load_level(MAP):
            raise RuntimeError("Could not load Town")
    elif not levels.new_level(MAP, False):
        raise RuntimeError("Could not create non-partitioned Town")
    level = levels.get_current_level()
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_world_settings().get_editor_property("world_partition"):
        raise RuntimeError("Town is World Partition; refusing to overwrite")
    removed = 0
    for actor in ACTORS.get_all_level_actors():
        if actor.actor_has_tag(TAG):
            if not ACTORS.destroy_actor(actor):
                raise RuntimeError("Could not remove " + actor.get_actor_label())
            removed += 1
    REPORT["removed_previous_generated_actors"] = removed
    CUBE = u.load_asset("/Engine/BasicShapes/Cube.Cube")
    if not CUBE:
        raise RuntimeError("Engine cube missing")
    make_materials(data)
    import_terrain(glb)
    infrastructure(data)
    buildings(data)
    routes(data)
    external_actors(level)
    if not levels.save_current_level():
        raise RuntimeError("Map save failed")
    if not u.EditorAssetLibrary.save_directory(
        ASSETS, only_if_is_dirty=True, recursive=True
    ):
        raise RuntimeError("Asset save failed")
    # Includes external actor packages if this map was converted by the commandlet.
    u.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    REPORT["generated_actor_count"] = sum(REPORT["actors_per_area"].values())
    REPORT["world_partition"] = False
    REPORT["map"] = MAP
    REPORT["status"] = "success"


if __name__ == "__main__":
    report_path = Path(u.Paths.project_saved_dir()) / "Blockout/report.json"
    try:
        main()
    except Exception as error:
        REPORT["status"] = "failed"
        REPORT["error"] = str(error)
        REPORT["traceback"] = traceback.format_exc()
        raise
    finally:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(REPORT, indent=2) + "\n")
        u.log("Blockout report: " + str(report_path))
