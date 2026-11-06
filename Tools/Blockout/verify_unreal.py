"""Read-only saved-map audit via Unreal's headless pythonscript commandlet.

Checks serialized actors, materials, collision configuration and actual cube
transforms around doors/floors. Capsule-volume and eye checks are analytic: a commandlet world
is not a gameplay physics scene. This does not claim a runtime physics sweep.
"""

import json
import math
import sys
from pathlib import Path
import unreal as u


def main():
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    assert levels.load_level("/Game/Selene/Maps/Town"), "Map reload failed"
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    assert world.get_world_settings().get_editor_property("world_partition") is None
    assert world.get_world_settings().get_editor_property("default_game_mode") == u.load_class(None, "/Script/Selene.SeleneGameMode")
    actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    generated = [a for a in actors if a.actor_has_tag("SeleneBlockout")]
    labels = [a.get_actor_label() for a in generated]
    assert len(labels) == len(set(labels)), "Duplicate generated labels after rebuild"
    report_dir = Path(u.Paths.project_saved_dir()) / "Blockout"
    build = json.loads((report_dir / "report.json").read_text())
    assert len(generated) == build["generated_actor_count"], (
        "Saved actor count differs from build report"
    )
    result = {
        "status": "success",
        "generated_actors": len(generated),
        "world_partition": False,
        "external_generated_actors": sum(a.is_package_external() for a in generated),
        "floor_geometry": {},
        "door_geometry": {},
        "physics_sweep": "not run: headless construction audit",
    }
    cubes = []
    for actor in generated:
        if not isinstance(actor, u.StaticMeshActor):
            continue
        component = actor.static_mesh_component
        mesh = component.get_editor_property("static_mesh")
        assert mesh and component.get_material(0), (
            actor.get_actor_label() + ": missing mesh/material"
        )
        if component.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION:
            continue
        if mesh.get_path_name() == "/Engine/BasicShapes/Cube.Cube":
            cubes.append(actor)
        elif actor.get_actor_label() == "SeleneTerrain":
            assert (
                mesh.get_editor_property("body_setup").get_editor_property(
                    "collision_trace_flag"
                )
                == u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
            )
            result["terrain_collision_configuration"] = "complex as simple"
            origin, extent = actor.get_actor_bounds(False)
            assert abs(extent.x - 20000) < 10 and abs(extent.y - 24000) < 10

    boxes = []
    for actor in cubes:
        transform = actor.get_actor_transform()
        origin = actor.get_actor_location()
        scale = actor.get_actor_scale3d()
        axes = []
        for direction in (u.Vector(1, 0, 0), u.Vector(0, 1, 0), u.Vector(0, 0, 1)):
            axis = u.MathLibrary.transform_direction(transform, direction)
            axes.append((axis.x, axis.y, axis.z))
        boxes.append((actor.get_actor_label(), (origin.x / 100, origin.y / 100, origin.z / 100),
                      axes, (abs(scale.x) / 2, abs(scale.y) / 2, abs(scale.z) / 2)))


    # Spatial bins keep dense feet/eye audits independent of Unreal API call cost.
    cells = {}
    for index, (_, origin, axes, extents) in enumerate(boxes):
        bounds = [sum(abs(axes[j][i]) * extents[j] for j in range(3)) + 0.5 for i in range(2)]
        for x in range(math.floor((origin[0] - bounds[0]) / 10), math.floor((origin[0] + bounds[0]) / 10) + 1):
            for y in range(math.floor((origin[1] - bounds[1]) / 10), math.floor((origin[1] + bounds[1]) / 10) + 1):
                cells.setdefault((x, y), []).append(index)

    def nearby(a, b):
        indices = set()
        for x in range(math.floor(min(a[0], b[0]) / 10), math.floor(max(a[0], b[0]) / 10) + 1):
            for y in range(math.floor(min(a[1], b[1]) / 10), math.floor(max(a[1], b[1]) / 10) + 1):
                indices.update(cells.get((x, y), []))
        return (boxes[i] for i in sorted(indices))

    def vec(p):
        return u.Vector(p[1] * 100, p[0] * 100, p[2] * 100)

    def hits(a, b):
        found = []
        for label, origin, axes, extents in nearby((a[1], a[0]), (b[1], b[0])):
            coords = [(p[1], p[0], p[2]) for p in (a, b)]
            p, q = [[sum((v[j] - origin[j]) * axis[j] for j in range(3))
                     for axis in axes] for v in coords]
            lo, hi = 0.0, 1.0
            for start, end, extent in zip(p, q, extents):
                delta = end - start
                if abs(delta) < 1e-8:
                    if not -extent < start < extent:
                        lo, hi = 1, 0
                        break
                else:
                    t0, t1 = sorted(((-extent - start) / delta, (extent - start) / delta))
                    lo, hi = max(lo, t0), min(hi, t1)
                    if lo >= hi:
                        break
            if lo < hi:
                found.append(label)
        return found

    for name, x, y, z in [
        ("plaza", 0, 0, 0),
        ("cafe_floor", -45, -30, 0),
        ("hall_floor", 0, 43, 0),
        ("workshop_floor", 105, -36, 0),
        ("overlook", 38, 187, 28),
    ]:
        found = hits([x, y, z + 1], [x, y, z - 2])
        assert found, name + ": no floor geometry"
        result["floor_geometry"][name] = found
    for name, a, b in [
        ("cafe_door", [-45, -22, 1.65], [-45, -26, 1.65]),
        ("hall_door", [0, 30, 1.65], [0, 34, 1.65]),
        ("hall_exit", [15, 43, 1.65], [19, 43, 1.65]),
        ("workshop_door", [105, -45, 1.65], [105, -41, 1.65]),
        ("workshop_exit", [96, -36, 1.65], [93, -36, 1.65]),
    ]:
        found = hits(a, b)
        assert not found, name + ": blocked by " + str(found)
        result["door_geometry"][name] = "clear"
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from layout_core import load, route_points

    layout = load(build["layout"])
    character = u.get_default_object(u.load_class(None, "/Script/Selene.SeleneCharacter"))
    capsule = character.get_component_by_class(u.CapsuleComponent)
    radius = capsule.get_scaled_capsule_radius() / 100
    assert abs(radius - 0.34) < 1e-6, "Update layout capsule support radius to match character"
    half_height = capsule.get_scaled_capsule_half_height() / 100
    eye_height = half_height + character.get_editor_property("base_eye_height") / 100
    result["capsule_metres"] = dict(radius=radius, half_height=half_height, eye_height=eye_height)
    # Exact distance between a capsule axis segment and each oriented cube. This
    # is a saved-geometry audit, not a gameplay physics sweep or spring-arm test.

    def capsule_hits(feet):
        # Swap layout east/north to UE; capsule axis excludes the hemisphere radii.
        a = (feet[1], feet[0], feet[2] + radius)
        b = (feet[1], feet[0], feet[2] + 2 * half_height - radius)
        found = []
        for label, origin, axes, extents in nearby(a, b):
            local = [[sum((p[j] - origin[j]) * axis[j] for j in range(3))
                      for axis in axes] for p in (a, b)]
            start, end = local
            if any(min(start[i], end[i]) > extents[i] + radius or
                   max(start[i], end[i]) < -extents[i] - radius for i in range(3)):
                continue
            delta = [end[i] - start[i] for i in range(3)]
            cuts = [0., 1.]
            for i in range(3):
                if abs(delta[i]) > 1e-10:
                    cuts += [t for edge in (-extents[i], extents[i])
                             if 0 < (t := (edge - start[i]) / delta[i]) < 1]
            cuts.sort()
            def distance2(t):
                return sum(max(abs(start[i] + t * delta[i]) - extents[i], 0)**2 for i in range(3))
            candidates = cuts[:]
            for lo, hi in zip(cuts, cuts[1:]):
                mid = (lo + hi) / 2
                active = [(i, math.copysign(extents[i], start[i] + mid * delta[i]))
                          for i in range(3) if abs(start[i] + mid * delta[i]) > extents[i]]
                denom = sum(delta[i]**2 for i, _ in active)
                if denom:
                    t = -sum(delta[i] * (start[i] - edge) for i, edge in active) / denom
                    candidates.append(max(lo, min(hi, t)))
            if min(distance2(t) for t in candidates) < (radius - 0.03)**2:
                found.append(label)
        return found

    result["route_geometry"] = {}
    for route in layout["routes"]:
        actor = next(a for a in generated if a.get_actor_label() == route["id"])
        spline = actor.get_component_by_class(u.SplineComponent)
        segments = actor.get_editor_property("segments")
        assert [str(s.get_editor_property("tag")) for s in segments] == [s["tag"] for s in route["segments"]]
        assert [str(s.get_editor_property("category")) for s in segments] == [s["category"] for s in route["segments"]]
        previous = 0.0
        for segment in segments:
            assert abs(segment.get_editor_property("start_distance") - previous) < 0.01
            previous = segment.get_editor_property("end_distance")
        assert abs(previous - spline.get_spline_length()) < 0.01, "Segment coverage differs from spline length"
        keys = actor.get_editor_property("view_keys")
        assert len(keys) == (2 if "look_at" in route else 0)
        if keys:
            assert keys[0].get_editor_property("distance") == 0
            assert abs(keys[-1].get_editor_property("distance") - spline.get_spline_length()) < 0.01
        for key in keys:
            assert key.get_editor_property("use_look_at")
            assert (key.get_editor_property("look_at_target") - vec(route["look_at"])).length() < 0.01
        points = route_points(layout, route)
        assert spline.get_number_of_spline_points() == len(points)
        for index, point in enumerate(points):
            assert (spline.get_location_at_spline_point(index, u.SplineCoordinateSpace.WORLD) - vec(point)).length() < 0.1
        samples = 0
        for a, b in zip(points, points[1:]):
            eye_a, eye_b = [*a[:2], a[2] + eye_height], [*b[:2], b[2] + eye_height]
            found = hits(eye_a, eye_b)
            assert not found, route["id"] + ": eye blocked by " + str(found)
            count = max(1, math.ceil(math.dist(a, b) / 0.25))
            for i in range(count + 1):
                feet = [a[j] + (b[j] - a[j]) * i / count for j in range(3)]
                found = capsule_hits(feet)
                assert not found, f"{route['id']}: capsule at {feet} blocked by {found}"
                samples += 1
        result["route_geometry"][route["id"]] = dict(capsule_samples=samples, eye_segments_clear=True,
            tolerance_cm=3, view_keys=len(keys), serialized_feet_points=True)
    # The intended seat-to-tower sightline must leave the cafe through a window gap.
    found = hits([-40, -30, 1.65], [-37, -24.525, 2.277])
    assert not found, "Cafe view blocked by " + str(found)
    result["cafe_window_sightline"] = "clear through the east storefront"
    (report_dir / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    u.log(str(result))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        path = Path(u.Paths.project_saved_dir()) / "Blockout/verification.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"status": "failed", "error": str(error)}, indent=2) + "\n"
        )
        raise
