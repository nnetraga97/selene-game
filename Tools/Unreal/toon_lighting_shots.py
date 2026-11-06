"""Toon shading acceptance shots: characters in the plan's four lighting states, toon vs imported material.

States (plan, section 3): noon sun on the plaza, café shade (north of the café wall at noon),
café interior under a warm practical light, night under a streetlamp-style light.
Env: SELENE_TOON_SUBJECTS="Name=/Game/mesh/path=/Game/Selene/Materials/Character/MI_Toon_Name,..."
     SELENE_TOON_ANIM_<NAME>="/Game/.../MM_Idle_<Name>" (optional idle pose per character)
Run: UnrealEditor Selene.uproject /Game/Selene/Maps/Town -ExecCmds="py <abs path without spaces>/toon_lighting_shots.py"
Writes Saved/Characters/toon/*.png and quits. Transient actors only; the map is not modified.
"""
import os
import time

import unreal as u

ROOT = u.Paths.convert_relative_path_to_full(u.Paths.project_dir())
OUT = os.path.join(ROOT, "Saved", "Characters", "toon")
os.makedirs(OUT, exist_ok=True)
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_game_view(True)


def ue(x, y, z):  # layout metres (east, north, up) -> Unreal cm (X north, Y east)
    return u.Vector(y * 100, x * 100, z * 100)


SUBJECTS = []
for item in [x for x in os.environ.get("SELENE_TOON_SUBJECTS", "").split(",") if x]:
    name, mesh, mi = item.split("=")
    SUBJECTS.append((name, mesh, mi, os.environ.get("SELENE_TOON_ANIM_" + name.upper())))

# name, subject layout position, hour, extra light (layout pos, colour, intensity cd, radius cm) or None
STATES = [
    ("noon_plaza", (0, -8, 0), 12.0, None),
    ("cafe_shade", (-45, -22.6, 0), 12.0, None),
    ("cafe_interior", (-46, -31, 0), 12.0, ((-46, -29.5, 3.6), (1.0, 0.78, 0.55), 900.0, 700.0)),
    ("night_streetlamp", (0, -8, 0), 22.0, ((1.8, -6.5, 4.2), (1.0, 0.82, 0.6), 2500.0, 1500.0)),
]
SHOTS = [(s, look) for s in STATES for look in ("toon", "imported")]
GAP = 1.0  # m between subjects (north-south); they face +Y Unreal = east, cameras look west
INITIAL_WAIT = float(os.environ.get("SELENE_INITIAL_WAIT", "45"))  # first Substrate launch compiles shaders
SETTLE, TIMEOUT = 4.0, 30.0

tod = next((a for a in actors.get_all_level_actors() if a.get_class().get_name() == "SeleneTimeOfDay"), None)
spawned = []
for i, (name, mesh, mi, anim) in enumerate(SUBJECTS):
    a = actors.spawn_actor_from_class(u.SkeletalMeshActor, u.Vector(0, 0, 0), u.Rotator(0, 0, 0), transient=True)
    c = a.skeletal_mesh_component
    c.set_skeletal_mesh_asset(u.load_asset(mesh))
    c.set_update_animation_in_editor(True)
    if anim:
        c.set_animation_mode(u.AnimationMode.ANIMATION_BLUEPRINT)
        c.override_animation_data(u.load_asset(anim), False, False, 0.0, 0.0)
    imported = [c.get_material(k) for k in range(c.get_num_materials())]
    spawned.append((a, u.load_asset(mi), imported, i))
state = {"i": 0, "phase": "init", "t": time.time()}
extras = []
log = []


def set_hour(h):
    if tod:
        tod.set_editor_property("hour", h)
        tod.rerun_construction_scripts()


def stage(shot):
    (name, pos, hour, light), look = shot
    for a, mi, imported, i in spawned:
        off = (i - (len(spawned) - 1) / 2.0) * GAP
        a.set_actor_location(ue(pos[0], pos[1] + off, pos[2]), False, False)
        c = a.skeletal_mesh_component
        for k in range(c.get_num_materials()):
            c.set_material(k, mi if look == "toon" else imported[k])
    set_hour(hour)
    for e in extras:
        actors.destroy_actor(e)
    extras.clear()
    if light:
        lp, col, cd, radius = light
        l = actors.spawn_actor_from_class(u.PointLight, ue(*lp), u.Rotator(0, 0, 0), transient=True)
        pl = l.point_light_component
        pl.set_editor_property("intensity_units", u.LightUnits.CANDELAS)
        pl.set_intensity(cd)
        pl.set_light_color(u.LinearColor(*col, 1.0))
        pl.set_attenuation_radius(radius)
        extras.append(l)
    target = ue(pos[0], pos[1], 1.05)
    cam_loc = target + u.Vector(0, 330, 25)  # 3.3 m east of the subjects
    rot = u.MathLibrary.find_look_at_rotation(cam_loc, target)
    cam = actors.spawn_actor_from_class(u.CameraActor, cam_loc, rot, transient=True)
    cam.camera_component.set_editor_property("field_of_view", 55.0)
    cam.camera_component.set_editor_property("constrain_aspect_ratio", False)
    return cam


def finish():
    u.unregister_slate_post_tick_callback(handle)
    for e in extras:
        actors.destroy_actor(e)
    for a, *_ in spawned:
        actors.destroy_actor(a)
    set_hour(12.0)
    with open(os.path.join(OUT, "shots.txt"), "w") as f:
        f.write("\n".join(log) + "\n")
    u.SystemLibrary.quit_editor()


def tick(_):
    now = time.time()
    s = state
    if s["phase"] == "init":
        if now - s["t"] >= INITIAL_WAIT:
            s["phase"] = "move"
        return
    if s["phase"] == "move":
        shot = SHOTS[s["i"]]
        s["cam"] = stage(shot)
        s["file"] = os.path.join(OUT, "%02d_%s_%s.png" % (s["i"] + 1, shot[0][0], shot[1]))
        s.update(phase="settle", t=now)
        return
    if s["phase"] == "settle":
        if now - s["t"] >= SETTLE:
            u.AutomationLibrary.take_high_res_screenshot(1600, 1200, s["file"], s["cam"])
            s.update(phase="wait", t=now)
        return
    done = os.path.exists(s["file"]) and os.path.getsize(s["file"]) > 0
    if done or now - s["t"] >= TIMEOUT:
        log.append(("ok " if done else "TIMEOUT ") + os.path.basename(s["file"]))
        actors.destroy_actor(s["cam"])
        s["i"] += 1
        if s["i"] >= len(SHOTS):
            finish()
        else:
            s.update(phase="move", t=now)


handle = u.register_slate_post_tick_callback(tick)
