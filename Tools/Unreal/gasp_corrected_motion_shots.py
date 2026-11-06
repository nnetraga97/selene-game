"""Fresh component playback/screenshots of the six corrected hero loops.

Reuses character_motion_shots.py without changing it. Dense walk phases avoid
session 3's one-second gait aliasing. Checks actual component bone locations
against the separate compressed-pose reload report. No map or asset saves.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import time
import traceback

import unreal as u

ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
NAME=os.environ['SELENE_CHAR']
OUT=ROOT/'Saved/Clips/session-4'/('motion-'+NAME)
OUT.mkdir(parents=True,exist_ok=True)
report={'status':'running','hero':NAME,'pose_samples':[],'shots':[]}
scope={};in_tick=False;finished=False


def checkpoint():
    (OUT/'motion.json').write_text(json.dumps(report,indent=2)+'\n')


def finish():
    global finished
    if finished:return
    finished=True
    report['shots']=scope['log']
    if report['status']!='failed':
        report['status']='success' if len(scope['log'])==8 and all(s.startswith('ok ') for s in scope['log']) else 'failed'
    checkpoint();original_finish()


def tick(delta):
    global in_tick
    if in_tick or finished:return
    in_tick=True
    try:
        s=scope['state'];capturing=s['phase']=='settle' and time.time()-s['t']>=scope['SETTLE']
        if capturing:
            actor=scope['champ'];origin=actor.get_actor_location();component=actor.skeletal_mesh_component
            definition=definitions[s['i']];clip=clips[definition['role']]
            expected=clip['samples'][round(definition['seconds']*60)]['bones']
            positions={};err=0.
            for bone,b in expected.items():
                v=component.get_socket_location(bone)-origin
                positions[bone]=[v.x,v.y,v.z]
                err=max(err,math.dist(positions[bone],b['translation']))
            report['pose_samples'].append({'shot':scope['SHOTS'][s['i']][0],'seconds':definition['seconds'],
                'bones_actor_local_cm':positions,'max_compressed_reload_error_cm':err})
            checkpoint()
            if err>0.1:raise RuntimeError('Component playback differs from compressed reload: '+str(err))
        # Skip the already-destroyed camera in the shared driver's finish path.
        original_tick(delta)
        if capturing and s['phase']=='wait':s['t']=time.time()
        if any(x.startswith('TIMEOUT ') for x in scope['log']):raise RuntimeError('Screenshot timed out')
    except Exception as exc:
        report.update(status='failed',error=str(exc),traceback=traceback.format_exc());checkpoint();finish()
    finally:
        in_tick=False


try:
    if (OUT/'motion.json').exists() or list(OUT.glob('*.png')):raise RuntimeError('Existing capture; do not replay')
    reload=json.loads((ROOT/'Saved/Clips/session-4/loop-reload.json').read_text())
    if reload['status']!='success':raise RuntimeError('Fresh reload verification must pass')
    clips={c['role']:c for c in reload['clips'] if c['hero']==NAME}
    for clip in clips.values():
        path=ROOT/'Content'/(clip['package'][6:]+'.uasset')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=clip['sha256_after']:raise RuntimeError('Corrected asset changed')
        anim=u.load_asset(clip['package'])
        if not anim or anim.get_editor_property('force_root_lock'):raise RuntimeError('Corrected clip failed reload')
    driver=ROOT/'Tools/Unreal/character_motion_shots.py'
    scope.update(__name__='__gasp_corrected_motion_driver__',__file__=str(driver))
    exec(compile(driver.read_text(),str(driver),'exec'),scope)
    scope['OUT']=str(OUT)
    definitions=[{'role':'WalkLoop','seconds':t} for t in (0.,.2,.4,.6)]
    definitions += [{'role':role,'seconds':t} for role in ('RunLoop','SprintLoop') for t in (0.,.1)]
    shots=[]
    for d in definitions:
        clip=clips[d['role']];target=clip['package'];source='/Game/Selene/Animation/GASP/'+target.rsplit('/',1)[1].removesuffix('_'+NAME)
        seconds=u.load_asset(target).get_play_length()
        shots.append((d['role']+'_%03dms'%round(d['seconds']*1000),(target,source),d['seconds']/seconds,0,360))
    scope['SHOTS']=shots;report['shot_definitions']=definitions
    original_tick,original_finish=scope['tick'],scope['finish']
    u.unregister_slate_post_tick_callback(scope['handle'])
    scope['finish']=finish;scope['handle']=u.register_slate_post_tick_callback(tick)
    checkpoint()
except Exception as exc:
    report.update(status='failed',error=str(exc),traceback=traceback.format_exc());checkpoint()
    u.log_error('GASP_CORRECTED_MOTION '+str(exc));u.SystemLibrary.quit_editor()
