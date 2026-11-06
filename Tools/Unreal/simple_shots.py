"""Checkpoint 1 review shots: fixed cameras from layout coordinates, one editor launch, no map edits.

Run (editor with rendering, Town map):
  UnrealEditor Selene.uproject /Game/Selene/Maps/Town -ExecCmds="py <abs path without spaces>/simple_shots.py"  (ExecutePythonScript quits the editor after running)
Writes PNGs to Saved/Checkpoint1/simple/ and quits the editor when done.
"""
import os
import time

import unreal as u

ROOT = u.Paths.convert_relative_path_to_full(u.Paths.project_dir())
OUT = os.path.join(ROOT, "Saved", "Checkpoint1", "simple")
os.makedirs(OUT, exist_ok=True)

# name, eye [x east, y north, z up] metres, look-at target (layout coords, see Design/Blockout/README.md)
SHOTS = [
    ("01_plaza_to_clock_tower", (0, -25, 1.65), (0, 43, 10)),
    ("02_cafe_terrace", (-30, -12, 1.65), (-45, -24, 2)),
    ("03_cafe_interior_counter", (-40, -30, 1.65), (-50, -33, 1.2)),
    ("04_cafe_window_seat_to_tower", (-40, -30, 1.25), (0, 43, 10)),
    ("05_main_street", (-55, -58, 1.65), (-178, -181, 3)),
    ("06_side_square", (-125, -92, 1.65), (-142, -79, 2)),
    ("07_concourse_interior", (-10, 48, 1.65), (10, 38, 4)),
    ("08_workshop_entrance", (105, -55, 1.65), (105, -36, 3)),
    ("09_industrial_yard_viaduct", (135, -5, 1.65), (156, 22, 6)),
    ("10_hillside_stairs", (38, 24, 1.65), (38, 115, 18)),
    ("11_overlook_to_town", (39, 187, 29.65), (0, 0, 4)),
    ("12_aerial_overview", (-210, -250, 110), (0, 40, 0)),
]
INITIAL_WAIT = 45.0  # map load, shader compile, Lumen settle
SETTLE = 4.0  # per camera move
WRITE_TIMEOUT = 30.0


def ue(p):
    return u.Vector(p[1] * 100, p[0] * 100, p[2] * 100)


state = {"i": 0, "phase": "init", "t": time.time(), "file": None, "camera": None}
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_game_view(True)
log = []


def finish():
    u.unregister_slate_post_tick_callback(handle)
    with open(os.path.join(OUT, "shots.txt"), "w") as f:
        f.write("\n".join(log) + "\n")
    u.log("SIMPLE_SHOTS done: " + "; ".join(log))
    u.SystemLibrary.quit_editor()


def tick(_dt):
    now = time.time()
    if state["phase"] == "init":
        if now - state["t"] >= INITIAL_WAIT:
            state["phase"] = "move"
        return
    if state["phase"] == "move":
        name, eye, target = SHOTS[state["i"]]
        loc = ue(eye)
        rot = u.MathLibrary.find_look_at_rotation(loc, ue(target))
        editor.set_level_viewport_camera_info(loc, rot)
        cam = actors.spawn_actor_from_class(u.CameraActor, loc, rot, transient=True)
        cam.camera_component.set_editor_property("field_of_view", 75.0)
        cam.camera_component.set_editor_property("constrain_aspect_ratio", False)
        state.update(camera=cam, phase="settle", t=now, file=os.path.join(OUT, name + ".png"))
        return
    if state["phase"] == "settle":
        if now - state["t"] >= SETTLE:
            u.AutomationLibrary.take_high_res_screenshot(1920, 1080, state["file"], state["camera"])
            state.update(phase="wait", t=now)
        return
    if state["phase"] == "wait":
        done = os.path.exists(state["file"]) and os.path.getsize(state["file"]) > 0
        if done or now - state["t"] >= WRITE_TIMEOUT:
            log.append(("ok " if done else "TIMEOUT ") + os.path.basename(state["file"]))
            actors.destroy_actor(state["camera"])
            state["i"] += 1
            if state["i"] >= len(SHOTS):
                finish()
            else:
                state.update(phase="move", t=now)


handle = u.register_slate_post_tick_callback(tick)
