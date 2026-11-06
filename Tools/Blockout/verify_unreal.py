"""Read-only saved-map audit via Unreal's headless pythonscript commandlet.

Checks serialized actors, materials, collision configuration and actual cube
transforms around doors/floors. Geometric rays are analytic: a commandlet world
is not a gameplay physics scene. This does not claim a player capsule sweep.
"""

import json
import sys
from pathlib import Path
import unreal as u


def main():
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    assert levels.load_level("/Game/Selene/Maps/Town"), "Map reload failed"
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    assert world.get_world_settings().get_editor_property("world_partition") is None
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

    def vec(p):
        return u.Vector(p[1] * 100, p[0] * 100, p[2] * 100)

    def hits(a, b):
        found = []
        for actor in cubes:
            transform = actor.get_actor_transform()
            p = u.MathLibrary.inverse_transform_location(transform, vec(a))
            q = u.MathLibrary.inverse_transform_location(transform, vec(b))
            lo, hi = 0.0, 1.0
            for start, end in zip((p.x, p.y, p.z), (q.x, q.y, q.z)):
                delta = end - start
                if abs(delta) < 1e-8:
                    if not -50 < start < 50:
                        lo, hi = 1, 0
                        break
                else:
                    t0, t1 = sorted(((-50 - start) / delta, (50 - start) / delta))
                    lo, hi = max(lo, t0), min(hi, t1)
                    if lo >= hi:
                        break
            if lo < hi:
                found.append(actor.get_actor_label())
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
    result["route_geometry"] = {}
    for route in layout["routes"]:
        points = route_points(layout, route)
        for a, b in zip(points, points[1:]):
            found = hits(a, b)
            assert not found, route["id"] + ": camera centre blocked by " + str(found)
        result["route_geometry"][route["id"]] = (
            "all camera-centre segments clear of colliding cubes"
        )
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
