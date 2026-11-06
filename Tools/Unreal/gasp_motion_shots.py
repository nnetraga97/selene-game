"""Run character_motion_shots.py's cameras/pose driver on saved GASP hero clips.

SELENE_CHAR and SELENE_CHAR_MESH select the hero. Uses the existing script without
editing it; replaces only its shot asset paths/output directory and adds evidence.
No level or asset saves. Run separately for Champion and Angel under the Selene lock.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import time
import traceback

import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
NAME = os.environ["SELENE_CHAR"]
OUT = ROOT / "Saved/Clips/session-3" / ("motion-" + NAME + os.environ.get("SELENE_SHOTS_SUFFIX", ""))
OUT.mkdir(parents=True, exist_ok=True)
report = {"status": "running", "hero": NAME, "reloaded_clips": [], "pose_samples": [],
          "driver": "Tools/Unreal/character_motion_shots.py", "mode": "editor static pose samples; no gameplay or physics claim"}
scope = {}
in_tick = False


def checkpoint():
    (OUT / "motion.json").write_text(json.dumps(report, indent=2) + "\n")


def finish():
    log = scope["log"]
    report["shots"] = log
    if report["status"] != "failed":
        report["status"] = "success" if len(log) == 8 and all(s.startswith("ok ") for s in log) else "failed"
    checkpoint()
    original_finish()


def tick(delta):
    global in_tick
    # High-res capture synchronously finishes asset/texture loading and can pump
    # Slate callbacks before returning. Do not request the same screenshot again.
    if in_tick:
        return
    in_tick = True
    try:
        s = scope["state"]
        preparing_capture = s["phase"] == "settle" and time.time() - s["t"] >= scope["SETTLE"]
        if s["phase"] == "settle" and time.time() - s["t"] >= scope["SETTLE"]:
            sample = {"shot": scope["SHOTS"][s["i"]][0], "feet_actor_local_cm": {}}
            actor = scope["champ"]
            origin = actor.get_actor_location()
            for bone in ("mixamorig_LeftFoot", "mixamorig_RightFoot", "mixamorig_LeftToeBase", "mixamorig_RightToeBase"):
                v = actor.skeletal_mesh_component.get_socket_location(bone) - origin
                point = [v.x, v.y, v.z]
                if not all(math.isfinite(x) for x in point):
                    raise RuntimeError("Nonfinite foot pose: " + bone)
                sample["feet_actor_local_cm"][bone] = point
            report["pose_samples"].append(sample)
            checkpoint()
        original_tick(delta)
        if preparing_capture and s["phase"] == "wait":
            # The shared driver records `now` before the blocking capture call.
            # Start its async-file timeout after that preparation has returned.
            s["t"] = time.time()
        if any(s.startswith("TIMEOUT ") for s in scope["log"]):
            raise RuntimeError("Screenshot timed out; stopping without another shot run")
    except Exception as exc:
        report.update(status="failed", error=str(exc), traceback=traceback.format_exc())
        checkpoint()
        finish()
    finally:
        in_tick = False


try:
    if list(OUT.glob("*.png")) or (OUT / "motion.json").exists():
        raise RuntimeError("Motion output already exists; inspect before replay")
    saved = json.loads((ROOT / "Saved/Clips/session-3/retarget.json").read_text())
    if saved["status"] != "success":
        raise RuntimeError("Both hero retargets must complete before motion shots")
    hero = saved["heroes"][NAME]
    if os.environ["SELENE_CHAR_MESH"] != hero["mesh"]:
        raise RuntimeError("Hero mesh mismatch")
    mesh = u.load_asset(hero["mesh"])
    for clip in hero["clips"]:
        filename = ROOT / "Content" / (clip["package"][6:] + ".uasset")
        if hashlib.sha256(filename.read_bytes()).hexdigest() != clip["sha256"]:
            raise RuntimeError("Saved hero asset changed: " + clip["package"])
        anim = u.load_asset(clip["package"])
        if not isinstance(anim, u.AnimSequence) or anim.get_editor_property("skeleton") != mesh.get_editor_property("skeleton"):
            raise RuntimeError("Failed fresh hero sequence/skeleton load: " + clip["package"])
        model = anim.get_editor_property("data_model_interface")
        if model.get_number_of_frames() != clip["frames"] or abs(anim.get_play_length() - clip["seconds"]) > 0.001:
            raise RuntimeError("Hero reload duration/frame mismatch: " + clip["package"])
        report["reloaded_clips"].append(clip["package"])
    checkpoint()
    driver = ROOT / report["driver"]
    scope.update(__name__="__gasp_motion_driver__", __file__=str(driver))
    exec(compile(driver.read_text(), str(driver), "exec"), scope)
    scope["OUT"] = str(OUT)
    source = "/Game/Selene/Animation/GASP/"
    target = "/Game/Selene/Characters/" + NAME + "/Anims/GASP/"
    shots = []
    for title, _, phase, yaw, distance in scope["SHOTS"]:
        clip = "M_Neutral_Stand_Idle_Loop" if title.startswith("idle_") else "M_Neutral_Walk_Loop_F"
        shots.append((title, (target + clip + "_" + NAME, source + clip), phase, yaw, distance))
    scope["SHOTS"] = shots
    report["shot_definitions"] = shots
    original_tick, original_finish = scope["tick"], scope["finish"]
    u.unregister_slate_post_tick_callback(scope["handle"])
    scope["finish"] = finish
    scope["handle"] = u.register_slate_post_tick_callback(tick)
    checkpoint()
except Exception as exc:
    report.update(status="failed", error=str(exc), traceback=traceback.format_exc())
    checkpoint()
    u.log_error("GASP_MOTION " + str(exc))
    u.SystemLibrary.quit_editor()
