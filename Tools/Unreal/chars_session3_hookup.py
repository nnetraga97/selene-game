"""Immutable session-3 entry point for independent guarded processes."""
import os
from pathlib import Path
import runpy
ROOT = Path(__file__).resolve().parents[2]
STAGE = os.environ['SELENE_CHARS_STAGE']
def run(name):
    runpy.run_path(str(ROOT/'Tools/Unreal'/name), run_name='__main__')
if STAGE == 'clips':
    run('chars_session3_clips.py')
elif STAGE == 'correct':
    run('chars_session3_audit_loops.py')
    os.environ['SELENE_LOOP_MODE'] = 'correct'
    run('chars_session3_in_place.py')
elif STAGE == 'measure':
    os.environ['SELENE_LOOP_MODE'] = 'verify'
    run('chars_session3_in_place.py')
    run('chars_session3_speeds.py')
elif STAGE == 'materials':
    run('chars_session3_materials.py')
elif STAGE == 'verify':
    run('chars_session3_verify.py')
else:
    raise RuntimeError('Unknown stage: '+STAGE)
