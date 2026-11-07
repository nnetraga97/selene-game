"""Fixture replays for the Selene editor dependency gates."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from run_checked_stages import Stage, run


REPORTER = '''
import json, os, pathlib, sys
report = pathlib.Path(os.environ['SELENE_STAGE_REPORT'])
mode = sys.argv[1]
if mode != 'missing':
    report.write_text(json.dumps({
        'invocation': 'stale' if mode == 'stale' else os.environ['SELENE_STAGE_ID'],
        'status': 'failed' if mode == 'reported-failure' else 'success',
    }))
if mode == 'good':
    (report.parent / 'artifact.bin').write_bytes(b'accepted evidence')
if mode == 'nonzero':
    raise SystemExit(7)
'''


class CheckedStagesTests(unittest.TestCase):
    def test_build_retarget_and_ground_fail_before_dependent_stage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
            subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=a@b.test', 'commit',
                            '--allow-empty', '-qm', 'fixture'], cwd=root, check=True)
            output = root / 'invocations'

            def stage(name, mode):
                return Stage(name, [sys.executable, '-c', REPORTER, mode], Path('report.json'),
                             lambda value, folder: [folder / 'artifact.bin'])

            good, passed = run([stage('motion', 'good')], root, output)
            self.assertTrue(passed)
            latest = (output / 'latest-passed.json').read_bytes()
            for name, mode in (('town-build', 'nonzero'), ('retarget', 'reported-failure'),
                               ('ground-instances', 'missing'), ('town-build', 'stale'),
                               ('ground-instances', 'missing-artifact')):
                folder, passed = run([stage(name, mode), stage('dependent', 'good')], root, output)
                self.assertFalse(passed)
                self.assertFalse((folder / 'dependent').exists())
                data = json.loads((folder / 'manifest.json').read_text())
                self.assertEqual(data['status'], 'failed')
                self.assertEqual(len(data['stages']), 1)
                self.assertEqual((output / 'latest-passed.json').read_bytes(), latest)
                self.assertTrue((folder / name / 'console.log').is_file())
            self.assertEqual((good / 'motion' / 'artifact.bin').read_bytes(), b'accepted evidence')


if __name__ == '__main__':
    unittest.main()
