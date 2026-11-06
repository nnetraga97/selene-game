"""Character motion check: retargeted walk/idle poses next to Manny, one editor launch, no map edits.

Env: SELENE_CHAR (name), SELENE_CHAR_MESH (skeletal mesh path); run character_retarget.py first.
Run: UnrealEditor Selene.uproject /Game/Selene/Maps/Town -ExecCmds="py <abs path without spaces>/character_motion_shots.py"
Writes Saved/Characters/<name>/motion/*.png and quits.
"""
import math
import os
import time

import unreal as u

ROOT = u.Paths.convert_relative_path_to_full(u.Paths.project_dir())
NAME = os.environ["SELENE_CHAR"]
OUT = os.path.join(ROOT, "Saved", "Characters", NAME, "motion")
os.makedirs(OUT, exist_ok=True)
CHAMP = os.environ["SELENE_CHAR_MESH"]
MANNY = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"
A = "/Game/Selene/Characters/%s/Anims/" % NAME
M = "/Game/Characters/Mannequins/Anims/Unarmed/"
WALK_C, WALK_M = A + "MF_Unarmed_Walk_Fwd_" + NAME, M + "Walk/MF_Unarmed_Walk_Fwd"
IDLE_C, IDLE_M = A + "MM_Idle_" + NAME, M + "MM_Idle"
ORIGIN = u.Vector(-1000, 0, 0)  # plaza, layout (0,-10), ground z=0
GAP = 160.0  # wide enough for winged characters  # cm between champion and Manny

# name, (anim champion, anim manny), normalized time, camera yaw around subject (deg), distance cm
# Both subjects face +Y (Manny's mesh forward; characters normalized to match).
SHOTS = [("idle_front", (IDLE_C, IDLE_M), 0.0, 90, 420), ("idle_back", (IDLE_C, IDLE_M), 0.0, 270, 420)]
for phase in (0.0, 0.25, 0.5, 0.75):
    SHOTS.append(("walk_side_%02d" % int(phase * 100), (WALK_C, WALK_M), phase, 0, 360))
for phase in (0.0, 0.5):
    SHOTS.append(("walk_front34_%02d" % int(phase * 100), (WALK_C, WALK_M), phase, 60, 420))
INITIAL_WAIT, SETTLE, TIMEOUT = 40.0, 3.0, 30.0

actors = u.get_editor_subsystem(u.EditorActorSubsystem)
u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_game_view(True)


def spawn(mesh_path, offset, yaw):
    a = actors.spawn_actor_from_class(u.SkeletalMeshActor, ORIGIN + offset, u.Rotator(0, 0, yaw), transient=True)
    c = a.skeletal_mesh_component
    c.set_skeletal_mesh_asset(u.load_asset(mesh_path))
    c.set_update_animation_in_editor(True)
    return a


champ = spawn(CHAMP, u.Vector(-GAP / 2, 0, 0), 0)  # normalized meshes face +Y like Manny
manny = spawn(MANNY, u.Vector(GAP / 2, 0, 0), 0)
state = {"i": 0, "phase": "init", "t": time.time(), "file": None, "cam": None}
log = []


def pose(actor, anim_path, t):
    anim = u.load_asset(anim_path)
    c = actor.skeletal_mesh_component
    # OverrideAnimationData only re-initialises the single-node instance when the mode changes,
    # so switch away first; it then ticks and refreshes bones at the requested position.
    c.set_animation_mode(u.AnimationMode.ANIMATION_BLUEPRINT)
    c.override_animation_data(anim, False, False, t * anim.get_play_length(), 0.0)


def finish():
    u.unregister_slate_post_tick_callback(handle)
    for a in (champ, manny):
        actors.destroy_actor(a)
    with open(os.path.join(OUT, "shots.txt"), "w") as f:
        f.write("\n".join(log) + "\n")
    u.log("CHARACTER_MOTION done: " + "; ".join(log))
    u.SystemLibrary.quit_editor()


def tick(_):
    now = time.time()
    s = state
    if s["phase"] == "init":
        if now - s["t"] >= INITIAL_WAIT:
            s["phase"] = "move"
        return
    if s["phase"] == "move":
        name, (ac, am), t, yaw, dist = SHOTS[s["i"]]
        pose(champ, ac, t)
        pose(manny, am, t)
        side = yaw in (0, 180)
        manny.set_is_temporarily_hidden_in_editor(side)  # side views: champion alone
        target = (champ.get_actor_location() if side else ORIGIN) + u.Vector(0, 0, 95)
        rad = math.radians(yaw)
        loc = target + u.Vector(math.cos(rad) * dist, math.sin(rad) * dist, 10)
        rot = u.MathLibrary.find_look_at_rotation(loc, target)
        cam = actors.spawn_actor_from_class(u.CameraActor, loc, rot, transient=True)
        cam.camera_component.set_editor_property("field_of_view", 50.0)
        cam.camera_component.set_editor_property("constrain_aspect_ratio", False)
        s.update(cam=cam, phase="settle", t=now, file=os.path.join(OUT, "%02d_%s.png" % (s["i"] + 1, name)))
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
