#!/usr/bin/env python3
import contextlib
import io
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import summarize


class SummaryTests(unittest.TestCase):
    def setUp(self):
        # Keep test artifacts inside the permitted workspace.
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.root = Path(self.temp.name)
        self.path = self.root / 'synthetic.frames.csv'

    def tearDown(self):
        self.temp.cleanup()

    def summarize_cli(self, args):
        with contextlib.redirect_stdout(io.StringIO()):
            return summarize.main(args)

    def fixture(self, warm=None, cold=None, declared=('exterior',), tags=None):
        warm = warm or [10] * 100
        cold = cold or [12] * 100
        rows = []
        for lap, values in ((-1, [100]), (0, cold), (1, warm)):
            for index, delta in enumerate(values):
                rows.append(dict(frame_index=len(rows), lap=lap, segment_tag=(tags[index] if tags and lap == 1 else 'exterior'),
                                 delta_ms=delta, game_thread_ms=4, render_thread_ms=5, gpu_ms='', is_discarded=int(lap == -1)))
        with self.path.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        summarize.meta_path(self.path).write_text(json.dumps(dict(status='complete', build_config='Shipping', warm_laps=1,
            segments=[dict(tag=tag, category=tag.split("_")[0]) for tag in declared], measured_frames=len(warm) + len(cold), total_frames=len(rows))))
        return summarize.analyze(self.path)

    def test_categories_and_unique_tags(self):
        self.fixture()
        with self.path.open() as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            row['segment_tag'] = 'exterior_street' if int(row['frame_index']) % 2 else 'exterior_hill'
            row['delta_ms'] = 5 if row['segment_tag'] == 'exterior_street' else 15
        with self.path.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        meta = json.loads(summarize.meta_path(self.path).read_text())
        meta['segments'] = [dict(tag=t, category='exterior') for t in ('exterior_street', 'exterior_hill')]
        summarize.meta_path(self.path).write_text(json.dumps(meta))
        run = summarize.analyze(self.path)
        self.assertTrue(run['pass'])
        self.assertEqual(run['warm']['categories']['exterior']['frames'], 100)
        self.assertEqual(run['warm']['categories']['exterior']['avg_fps'], 100)
        self.assertEqual(run['warm']['segments']['exterior_street']['avg_fps'], 200)
        self.assertEqual(run['laps']['0']['categories']['exterior']['frames'], 100)
        meta['segments'][1]['tag'] = 'EXTERIOR_STREET'
        summarize.meta_path(self.path).write_text(json.dumps(meta))
        self.assertEqual(summarize.analyze(self.path)['result'], 'INVALID')
        meta['segments'] = [dict(tag='exterior_street', category='unknown')]
        summarize.meta_path(self.path).write_text(json.dumps(meta))
        self.assertEqual(summarize.analyze(self.path)['result'], 'INVALID')

    def test_configuration_flags_invalidate_complete_fast_capture(self):
        for flag, value in [('warnings', ['unhandled tod.set']),
                            ('configuration_error', 'wrong pawn'),
                            ('configuration_warning', True), ('warnings', True),
                            ('configuration_errors', ['wrong camera']),
                            ('configuration_warnings', ['wrong hour']),
                            ('configuration_verified', False)]:
            with self.subTest(flag=flag):
                self.fixture()
                meta = json.loads(summarize.meta_path(self.path).read_text())
                meta[flag] = value
                summarize.meta_path(self.path).write_text(json.dumps(meta))
                run = summarize.analyze(self.path)
                self.assertEqual(run['result'], 'INVALID')
                self.assertFalse(run['pass'])
                self.assertFalse(run['shipping_pass'])
        self.assertEqual(self.summarize_cli([str(self.path), '--reports', str(self.root / 'reports'),
                                           '--archive', str(self.root / 'archive')]), 1)
        report = json.loads(next((self.root / 'reports').glob('*.json')).read_text())
        self.assertEqual(report['result'], 'INVALID')
        self.assertNotIn('| PASS |', summarize.markdown(report))

    def test_pass_and_unavailable_timers(self):
        run = self.fixture()
        self.assertTrue(run['shipping_pass'])
        self.assertEqual(run['warm']['overall']['avg_fps'], 100)
        self.assertIsNone(run['warm']['overall']['gpu_ms']['median'])
        self.assertEqual(run['warm']['overall']['frames'], 100)

    def test_fail_p99(self):
        self.assertFalse(self.fixture([20] * 100)['pass'])

    def test_hitch_even_if_p99_passes(self):
        result = self.fixture([10] * 999 + [40])
        self.assertEqual(result['warm']['overall']['p99_frame_ms'], 10)
        self.assertEqual(result['warm']['overall']['hitches_over_33_3'], 1)
        self.assertFalse(result['pass'])

    def test_empty_segment(self):
        result = self.fixture(declared=('exterior', 'interior'))
        self.assertFalse(result['pass'])
        self.assertTrue(any('interior has zero frames' in e for e in result['errors']))

    def test_cold_separate(self):
        result = self.fixture(cold=[50] * 100)
        self.assertTrue(result['pass'])
        self.assertFalse(result['cold']['overall']['pass'])

    def test_segment_cannot_hide_behind_whole_run(self):
        result = self.fixture([10] * 999 + [25], declared=('exterior', 'doorway'),
                              tags=['exterior'] * 999 + ['doorway'])
        self.assertTrue(result['warm']['overall']['pass'])
        self.assertFalse(result['warm']['segments']['doorway']['pass'])
        self.assertFalse(result['pass'])

    def test_truncation_and_missing_metadata(self):
        self.fixture()
        self.path.write_text(self.path.read_text().rsplit('\n', 2)[0] + '\n')
        self.assertFalse(summarize.analyze(self.path)['pass'])
        summarize.meta_path(self.path).unlink()
        self.assertFalse(summarize.analyze(self.path)['pass'])

    def test_empty_log(self):
        self.fixture()
        self.path.write_text('')
        self.assertFalse(summarize.analyze(self.path)['pass'])

    def test_nan_rejected(self):
        self.assertFalse(self.fixture([float('nan')])['pass'])

    def test_reports_preserve_runs_and_archive_hashes(self):
        self.fixture()
        other = self.root / 'failed.frames.csv'
        other.write_bytes(self.path.read_bytes().replace(b',10,', b',20,'))
        summarize.meta_path(other).write_bytes(summarize.meta_path(self.path).read_bytes())
        code = self.summarize_cli([str(self.path), str(other), '--reports', str(self.root / 'reports'),
                               '--archive', str(self.root / 'archive')])
        self.assertEqual(code, 1)
        report = json.loads(next((self.root / 'reports').glob('*.json')).read_text())
        self.assertEqual([r['pass'] for r in report['runs']], [True, False])
        for raw in report['raw_inputs']:
            self.assertEqual(raw['sha256'], hashlib.sha256(Path(raw['archived_path']).read_bytes()).hexdigest())

    def test_missing_launch_is_failure(self):
        self.fixture()
        manifest = self.root / 'launches.json'
        manifest.write_text(json.dumps([dict(returncode=0, frame_logs=[])]))
        self.assertEqual(self.summarize_cli([str(self.path), '--manifest', str(manifest),
            '--reports', str(self.root / 'reports'), '--archive', str(self.root / 'archive')]), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
