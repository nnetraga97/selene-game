"""Ten repeatable noon views: eight eye-level, overlook and aerial.
Run via town_run.sh capture <immutable-label>. Environment SELENE_SHOT_OUTPUT
sets the evidence directory; SELENE_SHOTS filters prefixes. No map is saved.
Stat-unit API counters are unavailable on this editor; Slate intervals are not
GPU timings. See Saved/Town/session-1 for the verified session baseline.
"""
import json
import os
import time

import unreal as u

ROOT = u.Paths.convert_relative_path_to_full(u.Paths.project_dir())
OUT = os.environ.get("SELENE_SHOT_OUTPUT") or os.path.join(ROOT, "Saved", "Town", "fixed-views")
os.makedirs(OUT, exist_ok=True)
if any(name.endswith(".png") for name in os.listdir(OUT)):
    raise RuntimeError("Use a fresh capture directory; existing evidence is immutable")

# name, eye [x east, y north, z up] metres, look-at target (layout coords, see Design/Blockout/README.md)
SHOTS = [
    ("01_plaza_clock", (0,-25,1.65), (0,43,6)),
    ("02_plaza_cafe", (-20,-12,1.65), (-45,-24,2)),
    ("03_cafe_approach", (-35,-18,1.65), (-45,-24,2)),
    ("04_cafe_door", (-45,-20,1.65), (-45,-32,1.6)),
    ("05_cafe_window", (-40,-30,1.65), (0,43,6)),
    ("06_main_street", (-55.256,-49.944,1.65), (-97.556,-92.244,3)),
    ("07_main_return", (-85,-80,1.65), (-42,-32,3)),
    ("08_plaza_west_edge", (-32,15,1.65), (0,20,3)),
    ("09_overlook", (39,187,29.65), (0,0,4)),
    ("10_aerial", (-210,-250,110), (0,40,0)),
]
# Optional filter: SELENE_SHOTS="05,06,12" reshoots only names starting with those prefixes.
_only = [x for x in os.environ.get("SELENE_SHOTS", "").split(",") if x]
if _only:
    SHOTS = [shot for shot in SHOTS if any(shot[0].startswith(x) for x in _only)]
if not SHOTS:
    raise ValueError("SELENE_SHOTS did not match a capture")
INITIAL_WAIT = 25.0  # map load, shader compile, Lumen settle
SETTLE = 4.0  # per camera move
WRITE_TIMEOUT = 30.0


def ue(p):
    return u.Vector(p[1] * 100, p[0] * 100, p[2] * 100)


state = {"i": 0, "phase": "init", "t": time.time(), "file": None, "camera": None}
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_game_view(True)
log = []
world = editor.get_editor_world()
tod = next((a for a in actors.get_all_level_actors() if a.get_class().get_name() == "SeleneTimeOfDay"), None)
if tod:
    tod.set_hour(12.0)
for cmd in ["r.VSync 0", "t.MaxFPS 0", "r.MotionBlurQuality 0", "stat unit"]:
    u.SystemLibrary.execute_console_command(world, cmd)
with open(os.path.join(OUT, "cameras.json"), "w") as f:
    json.dump({"shots": SHOTS, "hour": 12, "fov": 75, "resolution": [1920,1080]}, f, indent=2)
u.AutomationLibrary.enable_stat_group(world,"Engine")
perf=[]
with open(os.path.join(OUT, "stat-api.json"), "w") as f:
    json.dump({n:getattr(u.AutomationLibrary,n).__doc__ for n in dir(u.AutomationLibrary) if "stat" in n.lower()},f,indent=2)
frame_samples=[]




def finish():
    u.unregister_slate_post_tick_callback(handle)
    with open(os.path.join(OUT, "shots.txt"), "w") as f:
        f.write("\n".join(log) + "\n")
    u.log("SIMPLE_SHOTS done: " + "; ".join(log))
    if report := os.environ.get("SELENE_STAGE_REPORT"):
        shots = [entry.removeprefix("ok ") for entry in log if entry.startswith("ok ")]
        with open(report, "w") as f:
            json.dump({"invocation": os.environ.get("SELENE_STAGE_ID"), "shots": shots,
                       "expected": len(SHOTS), "status": "success" if shots and len(shots) == len(SHOTS) else "failed"}, f)
    with open(os.path.join(OUT, "perf.json"), "w") as f:
        json.dump(perf,f,indent=2)
    u.SystemLibrary.quit_editor()


def tick(_dt):
    now = time.time()
    if state["phase"] == "settle": frame_samples.append(_dt*1000)
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
        frame_samples.clear()
        state.update(camera=cam, phase="settle", t=now, file=os.path.join(OUT, name + ".png"))
        return
    if state["phase"] == "settle":
        if now - state["t"] >= SETTLE:
            if SHOTS[state["i"]][0].startswith(("01_","03_","06_")):
                sample={"view":SHOTS[state["i"]][0],"slate_frame_ms":sum(frame_samples)/len(frame_samples) if frame_samples else None,"stat_unit":{},"stat_note":"Unit counters unavailable from editor AutomationLibrary; zero values are not timings."}
                if os.environ.get("SELENE_TOWN_QUERY_STATS") == "1" and hasattr(u.AutomationLibrary,"get_stat_inc_average"):
                    for name in ("STAT_UnitFrame","STAT_UnitGame","STAT_UnitRender","STAT_UnitGPU"):
                        sample["stat_unit"][name]=u.AutomationLibrary.get_stat_inc_average(name)
                perf.append(sample)
                with open(os.path.join(OUT,"perf.json"),"w") as f: json.dump(perf,f,indent=2)
            state.update(phase="wait", t=now)
            u.AutomationLibrary.take_high_res_screenshot(1920, 1080, state["file"], state["camera"])
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
