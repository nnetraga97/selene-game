"""Create only the new MovementTest map; refuse to overwrite any existing map."""
import json
from pathlib import Path
import unreal as u

ROOT = Path(__file__).resolve().parents[2]
TARGET = "/Game/Selene/Maps/MovementTest"
if u.EditorAssetLibrary.does_asset_exist(TARGET):
    raise RuntimeError("MovementTest already exists; refusing to replace it")
levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
assert levels.new_level(TARGET, False), "Could not create MovementTest"
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
world.get_world_settings().set_editor_property("default_game_mode", u.load_class(None, "/Script/Selene.SeleneGameMode"))
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
cube = u.load_asset("/Engine/BasicShapes/Cube")
assert cube
layout = []

def box(name, center, size, pitch=0):
    actor = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(*center), u.Rotator(pitch=pitch))
    assert actor, name
    actor.set_actor_label(name)
    actor.static_mesh_component.set_static_mesh(cube)
    actor.static_mesh_component.set_collision_profile_name("BlockAll")
    actor.set_actor_scale3d(u.Vector(*(v / 100 for v in size)))
    layout.append(dict(name=name, center=center, size=size, pitch=pitch))

# Independent lanes keep a failed attempt away from other fixtures. All units cm.
box("Flat run-up", (2800, 0, -40), (7600, 1000, 80))
for x in range(0, 6500, 500):
    box(f"Lane marker {x}", (x, 460, 35), (25, 35, 70))
box("Ramp run-up", (-200, 1600, 320), (1000, 700, 80))
box("Downhill ramp", (875, 1600, 156), (1280, 700, 60), -16)
box("Ramp exit", (3000, 1600, -40), (3000, 700, 80))
box("Gap takeoff", (300, 3000, -40), (1800, 700, 80))
box("Gap landing", (2650, 3000, -40), (1500, 700, 80))  # 700 cm gap
box("Double jump approach", (0, 4400, -40), (1400, 700, 80))
box("Double jump platform", (1050, 4400, 110), (700, 700, 220))
box("Wall jump floor", (500, 5800, -40), (2400, 1100, 80))
box("Wall jump wall", (800, 5800, 230), (80, 900, 460))
for index, height in enumerate((100, 140, 180, 220)):
    y = 7300 + index * 1000
    box(f"Ledge {height} floor", (150, y, -40), (1600, 750, 80))
    box(f"Ledge {height} top", (700, y, height / 2), (600, 750, height))
actors.spawn_actor_from_class(u.PlayerStart, u.Vector(0, 0, 100))
sun = actors.spawn_actor_from_class(u.DirectionalLight, u.Vector(0, 0, 1800), u.Rotator(pitch=-55, yaw=-35))
sun.light_component.set_editor_property("intensity", 4.0)
sky = actors.spawn_actor_from_class(u.SkyLight, u.Vector(0, 0, 1600))
sky.light_component.set_editor_property("intensity", 1.0)
actors.spawn_actor_from_class(u.SkyAtmosphere, u.Vector(0, 0, 0))
assert levels.save_current_level(), "Could not save MovementTest"
out = ROOT / "Saved/MovementTest/level-layout.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(dict(map=TARGET, fixtures=layout), indent=2))
u.log("MOVEMENT_LEVEL_SAVED " + TARGET)
