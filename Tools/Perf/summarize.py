#!/usr/bin/env python3
"""Summarize Selene frame logs; UE profiler CSVs are archived diagnostics only."""
import argparse
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import shutil
import statistics
import sys
import uuid

ARCHIVE_ROOT = Path('/Users/nicknetraganti/Desktop/Developer Stuff/game-asset-workflow/evidence/selene-perf')
TIMERS = ('game_thread_ms', 'render_thread_ms', 'gpu_ms')
COLUMNS = {'frame_index', 'lap', 'segment_tag', 'delta_ms', 'is_discarded', *TIMERS}


def percentile(values, fraction):
    """Nearest rank; small samples never interpolate away a hitch."""
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)] if values else None


def metrics(rows):
    times = [r['delta_ms'] for r in rows]
    if not times:
        return {'frames': 0, 'pass': False}
    slow = sorted(times, reverse=True)[:max(1, math.ceil(len(times) * .01))]
    p99 = percentile(times, .99)
    hitches = sum(t > 33.3 for t in times)
    result = {
        'frames': len(times), 'avg_fps': 1000 / statistics.mean(times),
        'one_percent_low_fps': 1000 / statistics.mean(slow),
        'p99_frame_ms': p99, 'over_16_7_percent': 100 * sum(t > 16.7 for t in times) / len(times),
        'hitches_over_33_3': hitches, 'gap_to_120_ms': max(0, p99 - 8.33),
        'pass': p99 <= 16.7 and hitches == 0,
    }
    for timer in TIMERS:
        values = [r[timer] for r in rows if r[timer] is not None]
        result[timer] = {'samples': len(values), 'median': statistics.median(values) if values else None,
                         'p99': percentile(values, .99)}
    return result


def meta_path(path):
    return path.with_name(path.name.removesuffix('.frames.csv') + '.meta.json')


def analyze(path):
    path = Path(path)
    errors, rows, metadata = [], [], {}
    try:
        metadata = json.loads(meta_path(path).read_text())
        if not isinstance(metadata, dict):
            raise ValueError('metadata must be an object')
        if metadata.get('mode') == 'shots':
            return None
        if metadata.get('status') != 'complete':
            errors.append('capture did not complete')
        if metadata.get('error'):
            errors.append(str(metadata['error']))
        for flag in ('warnings', 'configuration_error', 'configuration_errors',
                     'configuration_warning', 'configuration_warnings'):
            if metadata.get(flag):
                errors.append(f"configuration {flag}: {metadata[flag]}")
        if metadata.get('configuration_verified') is not True:
            errors.append('configuration was not verified')
    except (OSError, ValueError) as exc:
        errors.append(f'metadata: {exc}')
        metadata = {}
    declared, categories = [], {}
    try:
        declared = [s['tag'] for s in metadata['segments']]
        if not declared or any(not isinstance(s, str) or not s for s in declared) or len({s.casefold() for s in declared}) != len(declared):
            raise ValueError('segments must have unique nonempty tags')
        categories = {s['tag']: s['category'] for s in metadata['segments']}
        if any(c not in ('exterior', 'doorway', 'interior') for c in categories.values()):
            raise ValueError('invalid segment category')
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f'segment declarations: {exc}')
        declared, categories = [], {}
    try:
        with path.open(newline='') as stream:
            reader = csv.DictReader(stream)
            if not COLUMNS.issubset(reader.fieldnames or []):
                raise ValueError('missing required frame columns')
            previous = -1
            for line, raw in enumerate(reader, 2):
                try:
                    row = dict(raw)
                    row['frame_index'] = int(raw['frame_index'])
                    row['lap'] = int(raw['lap'])
                    row['delta_ms'] = float(raw['delta_ms'])
                    if raw['is_discarded'] not in ('0', '1'):
                        raise ValueError('invalid is_discarded')
                    row['is_discarded'] = raw['is_discarded'] == '1'
                    if row['frame_index'] <= previous:
                        raise ValueError('frame indices not strictly increasing')
                    previous = row['frame_index']
                    if not math.isfinite(row['delta_ms']) or row['delta_ms'] <= 0:
                        raise ValueError('invalid delta_ms')
                    if not row['is_discarded'] and (row['lap'] < 0 or not row['segment_tag']):
                        raise ValueError('invalid measured lap or tag')
                    for timer in TIMERS:
                        row[timer] = float(raw[timer]) if raw[timer] else None
                        if row[timer] is not None and (not math.isfinite(row[timer]) or row[timer] <= 0):
                            raise ValueError(f'invalid {timer}; unavailable values must be empty')
                    rows.append(row)
                except (ValueError, TypeError) as exc:
                    errors.append(f'line {line}: {exc}')
    except (OSError, ValueError, csv.Error) as exc:
        errors.append(f'frame log: {exc}')
    measured = [r for r in rows if not r['is_discarded']]
    warm = [r for r in measured if r['lap'] > 0]
    cold = [r for r in measured if r['lap'] == 0]
    if not measured:
        errors.append('empty measured frame log')
    if metadata.get('measured_frames') != len(measured) or metadata.get('total_frames') != len(rows):
        errors.append('frame counts do not match metadata (truncated or malformed log)')
    laps = metadata.get('warm_laps', 0)
    if not isinstance(laps, int) or isinstance(laps, bool) or not 1 <= laps <= 1000:
        errors.append('missing/invalid warm_laps')
        laps = 0
    if any(r['lap'] > laps for r in measured):
        errors.append('unexpected measured lap')
    if any(r['segment_tag'] not in declared + ['unsegmented'] for r in measured):
        errors.append('undeclared segment tag')

    def group(items):
        tags = sorted(set(declared) | {r['segment_tag'] for r in items})
        return {'overall': metrics(items), 'segments': {
            tag: metrics([r for r in items if r['segment_tag'] == tag]) for tag in tags},
            'categories': {category: metrics([r for r in items if categories.get(r['segment_tag']) == category])
                           for category in sorted(set(categories.values()))}}

    by_lap = {}
    for lap in range(laps + 1):
        subset = [r for r in measured if r['lap'] == lap]
        by_lap[str(lap)] = group(subset)
        if not subset:
            errors.append(f'lap {lap} has no frames')
        for tag in declared:
            if not any(r['segment_tag'] == tag for r in subset):
                errors.append(f'lap {lap}: segment {tag} has zero frames')
    warm_metrics, cold_metrics = group(warm), group(cold)
    performance_pass = warm_metrics['overall']['pass'] and all(
        m['pass'] for m in warm_metrics['segments'].values()) and all(
        g['overall']['pass'] and all(m['pass'] for m in g['segments'].values())
        for lap, g in by_lap.items() if int(lap) > 0)
    passed = not errors and performance_pass
    build = metadata.get('build_config', 'Unknown')
    return {'input': str(path.resolve()), 'build': build, 'metadata': metadata, 'errors': errors,
            'warnings': (metadata.get('warnings', []) if isinstance(metadata.get('warnings', []), list)
                         else [str(metadata['warnings'])]), 'pass': passed,
            'result': 'INVALID' if errors else ('PASS' if passed else 'FAIL'),
            'shipping_pass': passed and build == 'Shipping',
            'warm': warm_metrics, 'cold': cold_metrics, 'laps': by_lap}


def archive_inputs(paths, destination):
    destination.mkdir(parents=True, exist_ok=False)
    entries = []
    for index, path in enumerate(dict.fromkeys(Path(p).resolve() for p in paths)):
        entry = {'path': str(path)}
        if not path.is_file():
            entry['error'] = 'missing input'
        else:
            target = destination / f'{index:04d}_{path.name}'
            shutil.copy2(path, target)
            entry.update(sha256=hashlib.sha256(target.read_bytes()).hexdigest(), archived_path=str(target))
        entries.append(entry)
    return entries


def markdown(report):
    lines = [f"# Selene performance — {report['build']}", '',
             f"Result: **{report['result']}**. Every run is retained below.", '',
             'Shipping frame logs are the performance authority. Development CSV profiles are diagnostic attachments.',
             'COLD = first recorded lap after warm-up; it is not an OS/shader cache reset. Cold timing does not gate warm performance.',
             'Percentiles use nearest rank. 1% low = 1000 / mean of the slowest ceil(1% × frames) intervals.',
             'PASS requires every warm run, lap and declared segment to have p99 ≤16.7 ms and zero frames >33.3 ms, with complete coverage.',
             'Diagnostic timers are latest available samples, potentially delayed; empty timers stay unavailable.', '']
    for run in report['runs']:
        lines += [f"## {Path(run['input']).name}", '',
                  f"**{run['result']}** ({run['build']}); Shipping evidence: {run['shipping_pass']}.", '']
        for error in run['errors']:
            lines.append(f'- ERROR: {error}')
        for warning in run['warnings']:
            lines.append(f'- WARNING: {warning}; requested camera/time behavior needs runtime confirmation.')
        lines += ['', '| Scope | Frames | Avg FPS | 1% low | p99 ms | >16.7 ms % | >33.3 ms | Gap to 120 ms | GT med/p99 | RT med/p99 | GPU med/p99 | Result |',
                  '|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|']
        groups = [('WARM all', run['warm']), ('COLD', run['cold'])]
        groups += [(f"lap {lap}", group) for lap, group in run['laps'].items() if lap != '0']
        for label, group in groups:
            for tag, metric in [('overall', group['overall']), *group['segments'].items(),
                                *((f'category:{k}', v) for k, v in group['categories'].items())]:
                def fmt(value):
                    return '—' if value is None else f'{value:.2f}'
                values = [f'{label}/{tag}'.replace('|', '\\|'), str(metric['frames'])]
                values += [fmt(metric.get(key)) for key in ('avg_fps', 'one_percent_low_fps', 'p99_frame_ms',
                           'over_16_7_percent', 'hitches_over_33_3', 'gap_to_120_ms')]
                for timer in TIMERS:
                    value = metric.get(timer, {})
                    values.append(f"{fmt(value.get('median'))}/{fmt(value.get('p99'))}")
                values.append('INVALID' if run['errors'] else ('PASS' if metric['pass'] else 'FAIL'))
                lines.append('| ' + ' | '.join(values) + ' |')
        lines += ['', '<details><summary>Run metadata</summary>', '', '```json',
                  json.dumps(run['metadata'], indent=2), '```', '</details>', '']
    if report['launch_failures']:
        lines += ['## Launch failures', '', '```json', json.dumps(report['launch_failures'], indent=2), '```', '']
    lines += ['## Raw input archive', '', '| Input | SHA256 | Archived copy |', '|---|---|---|']
    for item in report['raw_inputs']:
        lines.append(f"| {item['path']} | {item.get('sha256', 'MISSING')} | {item.get('archived_path', '')} |")
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('logs', nargs='*', type=Path)
    parser.add_argument('--profiler', nargs='*', default=[], type=Path)
    parser.add_argument('--manifest', type=Path, help='run_matrix launch manifest; missing logs fail the report')
    parser.add_argument('--reports', type=Path, default=Path('Tools/Perf/reports'))
    parser.add_argument('--archive', type=Path, help='new archive directory (must not exist)')
    parser.add_argument('--build', choices=('Shipping', 'Development'), default='Shipping')
    parser.add_argument('--run-id', default=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8])
    args = parser.parse_args(argv)
    logs = list(dict.fromkeys(p.resolve() for p in args.logs))
    analyzed = [(p, analyze(p)) for p in logs]
    logs = [p for p, run in analyzed if run is not None]
    runs = [run for _, run in analyzed if run is not None]
    raw = logs + [meta_path(p) for p in logs] + args.profiler
    failures = []
    if args.manifest:
        raw.append(args.manifest)
        launches = json.loads(args.manifest.read_text())
        for launch in launches:
            raw.extend(Path(p) for p in launch.get('artifacts', []))
            expected = [Path(p).resolve() for p in launch.get('frame_logs', [])]
            if launch.get('returncode') != 0 or len(expected) != 1 or any(p not in logs for p in expected):
                failures.append(launch)
    for run in runs:
        if run['build'] != args.build:
            run['errors'].append(f"expected {args.build}, found {run['build']}")
            run['pass'] = run['shipping_pass'] = False
            run['result'] = 'INVALID'
    inputs = archive_inputs(raw, args.archive or ARCHIVE_ROOT / args.run_id)
    passed = bool(runs) and all(r['pass'] for r in runs) and not failures and all('error' not in p for p in inputs)
    result = ('PASS' if passed else 'FAIL') if args.build == 'Shipping' else ('DIAGNOSTIC_PASS' if passed else 'DIAGNOSTIC_FAIL')
    if any(r['errors'] for r in runs) or failures or not runs or any('error' in p for p in inputs):
        result = 'INVALID'
    report = {'run_id': args.run_id, 'build': args.build, 'result': result, 'runs': runs,
              'launch_failures': failures, 'raw_inputs': inputs}
    args.reports.mkdir(parents=True, exist_ok=True)
    stem = args.reports / f"{dt.datetime.now(dt.timezone.utc).date()}-{args.build}"
    # Preserve earlier reports instead of overwriting evidence on the same date.
    if stem.with_suffix('.json').exists() or stem.with_suffix('.md').exists():
        stem = stem.with_name(stem.name + '-' + args.run_id)
    stem.with_suffix('.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    stem.with_suffix('.md').write_text(markdown(report))
    print(f"{result}: {stem}.md\nJSON: {stem}.json\nArchive: {args.archive or ARCHIVE_ROOT / args.run_id}")
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
