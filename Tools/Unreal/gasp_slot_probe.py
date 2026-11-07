"""Read-only native slot/clock probe; body bones exclude roster secondary subtrees.

Writes diagnostic poses and state before assertions. References deliberately switch
animation mode before OverrideAnimationData. UObject wrappers are released on a
separate callback before requesting editor shutdown.
"""
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
import traceback

import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
OUT = ROOT / 'Saved/Clips' / os.environ.get('SELENE_CLIPS_SESSION', 'session-6')
REPORT = OUT / 'slot-probe.json'
report = {'status': 'running', 'cases': [], 'saved_packages': []}
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
spawned = []
cases = []
state = {'phase': 'load', 'started': time.monotonic(), 'frames': 0}
busy = False
handle = None


def checkpoint():
    REPORT.write_text(json.dumps(report, indent=2) + '\n')


def xyz(v):
    values = [v.x, v.y, v.z]
    if not all(math.isfinite(x) for x in values):
        raise RuntimeError('Nonfinite bone position')
    return values


def transform(t):
    q = t.rotation
    return {'translation': xyz(t.translation), 'rotation': [q.x, q.y, q.z, q.w], 'scale': xyz(t.scale3d)}


def component_pose(component, bones):
    return {b: transform(component.get_socket_transform(b, u.RelativeTransformSpace.RTS_COMPONENT)) for b in bones}


def errors(a, b):
    per_bone = {bone: math.dist(a[bone]['translation'], b[bone]['translation']) for bone in a}
    return {'max_cm': max(per_bone.values()), 'worst_bone': max(per_bone, key=per_bone.get), 'per_bone_cm': per_bone}


def expected_pose(case, anim, seconds, bones):
    options = u.AnimPoseEvaluationOptions()
    for key, value in {'optional_skeletal_mesh': case['mesh'],
                       'evaluation_type': u.AnimDataEvalType.COMPRESSED,
                       'evaluate_curves': False}.items():
        options.set_editor_property(key, value)
    pose = u.AnimPoseExtensions.get_anim_pose_at_time(anim, seconds, options)
    if not u.AnimPoseExtensions.is_valid(pose):
        raise RuntimeError('Invalid independent pose')
    return {b: transform(u.AnimPoseExtensions.get_bone_pose(pose, b, u.AnimPoseSpaces.WORLD)) for b in bones}


def component_state(component):
    instance = component.get_anim_instance()
    playback = u.SeleneSecondaryAnimInstance.probe_single_node_component(component, -1.0)
    data = {'time': playback.x, 'rate': playback.y, 'playing': bool(playback.z), 'mode': str(component.get_animation_mode()), 'instance_class': instance.get_class().get_name() if instance else None}
    if instance:
        for name in ('get_current_time', 'get_animation_asset', 'is_playing', 'get_play_rate'):
            method = getattr(instance, name, None)
            if method:
                value = method()
                data[name] = value.get_path_name() if isinstance(value, u.Object) else value
    return data


def snapshot(c, name, animation=None, seconds=None):
    actual = component_pose(c['component'], c['all_bones'])
    reference = component_pose(c['reference'].skeletal_mesh_component, c['all_bones'])
    result = {'actual_state': component_state(c['component']),
              'reference_state': component_state(c['reference'].skeletal_mesh_component),
              'actual': actual, 'reference': reference,
              'compared_error': errors({b: actual[b] for b in c['bones']}, reference)}
    if c['secondary']:
        result['secondary_displacement'] = errors({b: actual[b] for b in c['secondary']}, reference)
    if animation:
        expected = expected_pose(c, animation, seconds, c['all_bones'])
        result.update(expected=expected, expected_seconds=seconds,
                      actual_expected_error=errors({b: actual[b] for b in c['bones']}, expected),
                      reference_expected_error=errors({b: reference[b] for b in c['bones']}, expected))
    c['result'][name] = result
    checkpoint()
    return result


def finish(error=None):
    report['status'] = 'failed' if error else 'success'
    if error:
        report.update(error=str(error), traceback=traceback.format_exc())
    checkpoint()
    state['phase'] = 'cleanup'


def cleanup():
    global actors, handle
    # Previous tick frame has unwound; remove all UObject/bound-method references.
    cases.clear()
    for actor in spawned:
        actors.destroy_actor(actor)
    actor = None
    spawned.clear()
    actors = None
    gc.collect()
    report['cleanup'] = 'actors destroyed; Python UObject references released before quit'
    checkpoint()
    state['phase'] = 'quit'


def slot_weight(c):
    return getattr(c['instance'], c['weight_method'])('DefaultSlot')


def tick(delta):
    global busy, handle
    if busy:
        return
    busy = True
    try:
        now = time.monotonic()
        phase = state['phase']
        if phase == 'cleanup':
            cleanup()
            return
        if phase == 'quit':
            u.unregister_slate_post_tick_callback(handle)
            handle = None
            gc.collect()
            u.log('SELENE_SLOT_PROBE ' + report['status'])
            u.SystemLibrary.quit_editor()
            return
        if now - state['started'] > 120:
            raise RuntimeError('Probe timed out')
        if phase not in ('load', 'cleanup', 'quit'):
            for c in cases:
                for component in (c['component'], c['reference'].skeletal_mesh_component):
                    u.SeleneSecondaryAnimInstance.probe_single_node_component(component, 1.0 / 60.0)
            state['elapsed'] += 1.0 / 60.0
        if phase == 'load':
            if any(c['chains'] and str(c['actor'].get_active_character_name()) != c['hero'] for c in cases):
                return
            for c in cases:
                component = c['actor'].get_component_by_class(u.SkeletalMeshComponent)
                c['component'] = component
                component.set_component_tick_enabled(False)
                c['actor'].set_actor_tick_enabled(False)
                component.set_relative_location(u.Vector(), False, False)
                component.set_relative_rotation(u.Rotator(), False, False)
                component.set_update_animation_in_editor(True)
                component.set_editor_property('visibility_based_anim_tick_option', u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
                instance = component.get_anim_instance()
                if not instance or instance.get_class().get_name() != 'SeleneSecondaryAnimInstance':
                    raise RuntimeError('Wrong native anim instance')
                c['instance'] = instance
                c['weight_method'] = next((n for n in ('blueprint_get_slot_montage_local_weight', 'get_slot_local_weight') if hasattr(instance, n)), None)
                if not c['weight_method']:
                    raise RuntimeError('Slot weight query unavailable')
                bones = [str(b) for b in component.get_all_socket_names() if component.get_bone_index(b) >= 0]
                roots = set(c['roots'])
                if not roots.issubset(bones):
                    raise RuntimeError('Roster roots absent from skeleton')
                def secondary(b):
                    while b and b != 'None':
                        if b in roots:
                            return True
                        b = str(component.get_parent_bone(b))
                    return False
                c['all_bones'] = bones
                c['secondary'] = [b for b in bones if secondary(b)]
                c['bones'] = [b for b in bones if b.startswith('mixamorig_') and b not in c['secondary']] if c['chains'] else bones
                c['result'].update(compared_bones=c['bones'], excluded_secondary_bones=c['secondary'] if c['chains'] else [], roots=c['roots'])
                instance.set_animation_asset(c['walk'], True, 0.83)
                instance.set_position(0.6, False)
                instance.set_playing(False)
                ref = c['reference'].skeletal_mesh_component
                ref.set_component_tick_enabled(False)
                ref.set_update_animation_in_editor(True)
                ref.set_editor_property('visibility_based_anim_tick_option', u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
                c['result']['reference_before_override'] = component_state(ref)
                # Record the old API path without using it as a valid reference.
                ref.override_animation_data(c['walk'], True, False, 0.6, 0.83)
                c['result']['reference_after_same_mode_override'] = component_state(ref)
                ref.set_animation_mode(u.AnimationMode.ANIMATION_BLUEPRINT)
                ref.override_animation_data(c['walk'], True, False, 0.6, 0.83)
                c['result']['reference_after_mode_switch_override'] = component_state(ref)
            checkpoint()
            state.update(phase='frozen', changed=now, elapsed=0.0)
        elif phase == 'frozen' and state['elapsed'] > 1:
            for c in cases:
                r = snapshot(c, 'frozen', c['walk'], 0.6)
                if max(r[k]['max_cm'] for k in ('compared_error', 'actual_expected_error', 'reference_expected_error')) > 0.1:
                    raise RuntimeError('Frozen body/all-bone mismatch: ' + c['name'])
            for c in cases:
                c['instance'].set_playing(True)
                c['reference'].skeletal_mesh_component.get_anim_instance().set_playing(True)
            state.update(phase='base', changed=now, elapsed=0.0)
        elif phase == 'base' and state['elapsed'] > 1:
            for c in cases:
                r = snapshot(c, 'advancing_base')
                if r['compared_error']['max_cm'] > 0.1:
                    raise RuntimeError('Base passthrough mismatch: ' + c['name'])
                if errors(r['actual'], c['result']['frozen']['actual'])['max_cm'] < 1:
                    raise RuntimeError('Base failed to advance')
            for c in cases:
                c['montage'] = c['instance'].play_slot_animation_as_dynamic_montage(c['run'], 'DefaultSlot', 0.15, 0.15, 1.0, 1)
                if not c['montage']:
                    raise RuntimeError('Dynamic montage rejected')
            state.update(phase='overlay', changed=now, elapsed=0.0)
        elif phase == 'overlay' and state['elapsed'] > 0.5:
            for c in cases:
                c['instance'].montage_pause(c['montage'])
            state.update(phase='paused', frames=0)
        elif phase == 'paused':
            state['frames'] += 1
            if state['frames'] < 3:
                return
            for c in cases:
                instance = c['instance']
                weight = slot_weight(c)
                seconds = instance.montage_get_position(c['montage'])
                r = snapshot(c, 'overlay', c['run'], seconds)
                c['result'].update(slot_weight=weight, montage_seconds=seconds)
                error = r['actual_expected_error']['max_cm']
                separation = r['compared_error']['max_cm']
                if weight < 0.99 or error > 0.1 or separation < 1:
                    raise RuntimeError('Slot did not override the base: ' + c['name'])
                if c['chains']:
                    swing = errors({b: r['actual'][b] for b in c['secondary']}, r['expected'])['max_cm']
                    c['result']['secondary_after_slot_cm'] = swing
                    if swing < 0.01:
                        raise RuntimeError('No secondary simulation after slot: ' + c['name'])
            for c in cases:
                c['instance'].montage_stop(0.15, c['montage'])
            checkpoint()
            state.update(phase='return', changed=now, elapsed=0.0)
        elif phase == 'return' and state['elapsed'] > 0.6:
            for c in cases:
                r = snapshot(c, 'returned_base')
                weight = slot_weight(c)
                c['result']['return_slot_weight'] = weight
                if weight > 0.001 or r['compared_error']['max_cm'] > 0.1:
                    raise RuntimeError('Base clock/return mismatch: ' + c['name'])
                c['result']['status'] = 'success'
            finish()
    except Exception as exc:
        finish(exc)
    finally:
        busy = False


def initialize():
    if REPORT.exists():
        raise RuntimeError('Existing report; do not replay')
    manifest = json.loads((ROOT / 'Saved/Clips/session-4/loop-reload.json').read_text())
    heroes = json.loads((ROOT / 'Saved/Clips/session-3/retarget.json').read_text())['heroes']
    config = (ROOT / 'Config/DefaultGame.ini').read_text().splitlines()
    if manifest['status'] != 'success':
        raise RuntimeError('Loop reload must pass')
    for hero in ('Champion', 'Angel'):
        roster = next(line for line in config if line.startswith('+Roster=(Name="' + hero + '"'))
        roots = re.findall(r'RootBone="([^"]+)"', roster)
        clips = {c['role']: c for c in manifest['clips'] if c['hero'] == hero}
        for clip in clips.values():
            path = ROOT / 'Content' / (clip['package'][6:] + '.uasset')
            if hashlib.sha256(path.read_bytes()).hexdigest() != clip['sha256_after']:
                raise RuntimeError('Corrected clip hash changed')
        mesh = u.load_asset(heroes[hero]['mesh'])
        for chains in (True, False):
            name = hero + ('-chains' if chains else '-no-chains')
            cls = u.load_class(None, '/Script/Selene.SeleneCharacter') if chains else u.SkeletalMeshActor
            actor = actors.spawn_actor_from_class(cls, u.Vector(-1000, len(cases)*300, 300), transient=True)
            spawned.append(actor)
            if chains:
                actor.select_character(hero)
            else:
                component = actor.skeletal_mesh_component
                component.set_skeletal_mesh_asset(mesh)
                component.set_anim_instance_class(u.load_class(None, '/Script/Selene.SeleneSecondaryAnimInstance'))
            reference = actors.spawn_actor_from_class(u.SkeletalMeshActor, u.Vector(-1300, len(cases)*300, 300), transient=True)
            spawned.append(reference)
            reference.skeletal_mesh_component.set_skeletal_mesh_asset(mesh)
            result = {'name': name, 'has_chains': chains, 'status': 'running'}
            report['cases'].append(result)
            cases.append({'name': name, 'hero': hero, 'chains': chains, 'actor': actor, 'reference': reference,
                          'roots': roots, 'mesh': mesh, 'walk': u.load_asset(clips['WalkLoop']['package']),
                          'run': u.load_asset(clips['RunLoop']['package']), 'result': result})
    checkpoint()


try:
    initialize()
except Exception as exc:
    finish(exc)
handle = u.register_slate_post_tick_callback(tick)
