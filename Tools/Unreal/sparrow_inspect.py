"""One brief transient preview; no map or asset saves. Three idles and placement views."""
import json
import math
from pathlib import Path
import time
import traceback
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
OUT = ROOT / 'Saved/Sparrow/session-3/inspection'
OUT.mkdir(parents=True, exist_ok=True)
BASE = '/Game/ParagonSparrow/Characters/Heroes/Sparrow'
ORIGIN = u.Vector(-1000, 0, 0)
SHOTS = [(n, n, 90, 310, 90) for n in ('idle', 'idle_relaxed', 'Travel_mode_Idle')] + [
    ('relaxed_back', 'idle_relaxed', 270, 310, 90),
    ('relaxed_side', 'idle_relaxed', 0, 310, 90),
    ('relaxed_feet', 'idle_relaxed', 70, 95, 15)]
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
u.get_editor_subsystem(u.LevelEditorSubsystem).editor_set_game_view(True)
actor = actors.spawn_actor_from_class(u.SkeletalMeshActor, ORIGIN, u.Rotator(), transient=True)
comp = actor.skeletal_mesh_component
comp.set_skeletal_mesh_asset(u.load_asset(BASE + '/Meshes/Sparrow'))
comp.set_update_animation_in_editor(True)
state = dict(i=0, phase='init', t=time.time(), cam=None)
report = dict(status='running', component_origin_cm=[-1000, 0, 0], component_yaw=0, shots=[])

def finish(error=None):
    u.unregister_slate_post_tick_callback(handle)
    report['status'] = 'failed' if error else 'success'
    if error:
        report['error'] = error
    (OUT / 'inspection.json').write_text(json.dumps(report, indent=2))
    if state['cam']:
        actors.destroy_actor(state['cam'])
    actors.destroy_actor(actor)
    u.SystemLibrary.quit_editor()

def tick(_):
    try:
        now = time.time()
        if state['phase'] == 'init':
            if now - state['t'] >= 35:
                state['phase'] = 'move'
            return
        if state['phase'] == 'move':
            name, clip, yaw, distance, height = SHOTS[state['i']]
            anim = u.load_asset(BASE + '/Animations/' + clip)
            comp.set_animation_mode(u.AnimationMode.ANIMATION_BLUEPRINT)
            comp.override_animation_data(anim, False, False, 1.0, 0.0)
            target = ORIGIN + u.Vector(0, 0, height)
            rad = math.radians(yaw)
            loc = target + u.Vector(math.cos(rad)*distance, math.sin(rad)*distance, 8)
            cam = actors.spawn_actor_from_class(u.CameraActor, loc, u.MathLibrary.find_look_at_rotation(loc, target), transient=True)
            cam.camera_component.set_editor_property('field_of_view', 50.0)
            cam.camera_component.set_editor_property('constrain_aspect_ratio', False)
            state.update(cam=cam, phase='settle', t=now, file=OUT / (name + '.png'))
            return
        if state['phase'] == 'settle':
            if now - state['t'] >= 3:
                u.AutomationLibrary.take_high_res_screenshot(1200, 1200, str(state['file']), state['cam'])
                landmarks = {}
                for bone in ('head', 'L_eye', 'R_eye', 'ball_l', 'ball_r', 'foot_l', 'foot_r'):
                    if comp.get_bone_index(bone) >= 0:
                        v = comp.get_socket_location(bone) - ORIGIN
                        landmarks[bone] = [v.x, v.y, v.z]
                state.update(phase='wait', t=now, landmarks=landmarks)
            return
        if state['file'].exists() and state['file'].stat().st_size:
            report['shots'].append(dict(file=str(state['file']), clip=SHOTS[state['i']][1], landmarks_cm=state['landmarks']))
            actors.destroy_actor(state['cam'])
            state.update(cam=None, i=state['i']+1, phase='move')
            if state['i'] == len(SHOTS):
                finish()
        elif now - state['t'] > 30:
            finish('Screenshot timed out: ' + str(state['file']))
    except Exception:
        finish(traceback.format_exc())

handle = u.register_slate_post_tick_callback(tick)
