#!/usr/bin/env python3
"""Run Selene's dependent Unreal stages with invocation-scoped reports and captures."""
import argparse
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
TOWN = '/Game/Selene/Maps/Town'
LOCK = Path('/tmp/selene-unreal.lock')


@dataclass(frozen=True)
class Stage:
    name: str
    argv: list[str]
    report: Path
    validate: object
    inputs: tuple[Path, ...] = ()
    env: dict | None = None
    timeout: float = 900


def digest(path):
    if not path.is_file() or not path.stat().st_size:
        raise ValueError(f'Missing or empty artifact {path}')
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, value):
    temporary = path.with_name(f'.{path.name}.{uuid.uuid4().hex}')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def execute(argv, root, env, log, timeout):
    with log.open('wb') as stream:
        child = subprocess.Popen(argv, cwd=root, env=env, stdout=stream,
                                 stderr=subprocess.STDOUT, start_new_session=True)
        try:
            return child.wait(timeout=timeout)
        except BaseException:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()
            raise


def run(stages, root, output):
    invocation = uuid.uuid4().hex
    folder = output / invocation
    folder.mkdir(parents=True)
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, check=True,
                              capture_output=True, text=True).stdout.strip()
    journal = {'invocation': invocation, 'input_revision': revision, 'stages': [], 'status': 'running'}
    write_json(folder / 'manifest.json', journal)
    for stage in stages:
        stage_dir = folder / stage.name
        stage_dir.mkdir()
        report = stage_dir / stage.report
        entry = {'name': stage.name, 'command': stage.argv, 'report': str(report),
                 'log': str(stage_dir / 'console.log'), 'exit_code': None, 'status': 'running'}
        journal['stages'].append(entry)
        write_json(folder / 'manifest.json', journal)
        started = time.monotonic()
        try:
            entry['inputs'] = {str(path): digest(path) for path in stage.inputs}
            env = {**os.environ, **(stage.env or {}), 'SELENE_STAGE_ID': invocation,
                   'SELENE_STAGE_REPORT': str(report), 'SELENE_SHOT_OUTPUT': str(stage_dir / 'shots')}
            entry['exit_code'] = execute(stage.argv, root, env, stage_dir / 'console.log', stage.timeout)
            if entry['exit_code']:
                raise ValueError(f'Command exited {entry["exit_code"]}')
            entry['report_sha256'] = digest(report)
            value = json.loads(report.read_text())
            if value.get('invocation') != invocation or value.get('status') != 'success':
                raise ValueError('Missing current success report or invalid invocation ID')
            files = stage.validate(value, stage_dir)
            if not files:
                raise ValueError('Stage did not produce verifiable artifacts')
            entry['artifacts'] = {str(path): digest(path) for path in files}
            entry['status'] = 'passed'
        except BaseException as exc:
            entry.update(status='failed', error=str(exc) or type(exc).__name__)
            journal['status'] = 'failed'
            if not isinstance(exc, Exception):
                raise
        finally:
            entry['seconds'] = round(time.monotonic() - started, 3)
            write_json(folder / 'manifest.json', journal)
        if entry['status'] == 'failed':
            return folder, False
    journal['status'] = 'passed'
    write_json(folder / 'manifest.json', journal)
    write_json(output / 'latest-passed.json', {'invocation': invocation, 'manifest': str(folder / 'manifest.json')})
    return folder, True


def check_shots(value, folder):
    shots = value.get('shots', [])
    if not shots or len(shots) != value.get('expected') or any(Path(shot).name != shot for shot in shots):
        raise ValueError('Capture did not produce every requested shot')
    paths = [folder / 'shots' / shot for shot in shots]
    for path in paths:
        with path.open('rb') as stream:
            if stream.read(8) != b'\x89PNG\r\n\x1a\n':
                raise ValueError(f'Invalid screenshot {path}')
    return paths


def package(path):
    if not path.startswith('/Game/') or '..' in path:
        raise ValueError(f'Unexpected asset package {path}')
    return ROOT / 'Content' / (path.removeprefix('/Game/').split('.', 1)[0] + '.uasset')


def workflow(args):
    tools = ROOT / 'Tools/Unreal'
    project = ROOT / 'Selene.uproject'
    map_file = ROOT / 'Content/Selene/Maps/Town.umap'
    layout = ROOT / 'Design/Blockout/layout.json'
    ground = ROOT / 'Design/Blockout/ground_materials.json'
    binaries = args.engine / 'Engine/Binaries/Mac'
    flags = ['-unattended', '-nop4', '-nosplash']

    def commandlet(name):
        return [str(binaries / 'UnrealEditor-Cmd'), str(project), '-run=pythonscript',
                f'-script={tools / name}', '-nullrhi', *flags]

    def capture(name):
        call = f"py __import__('runpy').run_path(__import__('unreal').Paths.project_dir()+'Tools/Unreal/{name}')"
        return [str(binaries / 'UnrealEditor'), str(project), TOWN, f'-ExecCmds={call}', *flags]

    def town_saved(report, _):
        if report.get('map') != TOWN or report.get('generated_actor_count', 0) < 1:
            raise ValueError('Town build did not report a populated map')
        return [map_file, package(report['terrain_asset'])]

    def materials_saved(report, _):
        expected = json.loads(ground.read_text())['materials']
        if set(report.get('instances', {})) != set(expected) or not report.get('textures'):
            raise ValueError('Ground build did not produce every required material instance and texture')
        return [package(report['parent']), *(package(data['asset']) for data in report['instances'].values()),
                *(package(data['asset']) for data in report['textures'])]

    def ground_saved(report, _):
        if report.get('map') != TOWN or report.get('verified_after_reload', 0) < 1:
            raise ValueError('Ground application has no saved/reopened placement evidence')
        return [map_file]

    def retarget_saved(report, _):
        outputs = report.get('retargeted', [])
        if (not report.get('mapping') or
                any(not any(path.endswith('/' + name + '_' + args.character) for path in outputs)
                    for name in ('MF_Unarmed_Walk_Fwd', 'MM_Idle'))):
            raise ValueError('Retarget report is missing the chain map or required idle and walk')
        return [package(path) for path in outputs]

    if args.workflow == 'town':
        terrain = args.terrain.resolve(strict=True)
        script = 'build_blockout.py'
        return [
            Stage('town-build', commandlet(script), Path('town.json'), town_saved,
                  (layout, terrain, terrain.parent / 'terrain-report.json', tools / script),
                  {'SELENE_LAYOUT': str(layout), 'SELENE_TERRAIN_GLB': str(terrain)}),
            Stage('town-capture', capture('simple_shots.py'), Path('capture.json'), check_shots, (map_file,)),
        ]
    if args.workflow == 'ground':
        script = 'build_ground_materials.py'

        def parent_saved(report, _):
            return [package(report['parent'])]

        return [
            Stage('ground-parent', commandlet(script), Path('parent.json'), parent_saved, (ground, tools / script),
                  {'SELENE_GROUND_PARENT_ONLY': '1', 'SELENE_GROUND_SKIP_PARENT': '0'}),
            Stage('ground-instances', commandlet(script), Path('materials.json'), materials_saved,
                  (ground, tools / script), {'SELENE_GROUND_PARENT_ONLY': '0', 'SELENE_GROUND_SKIP_PARENT': '1'}),
            Stage('ground-apply', commandlet('apply_ground_materials.py'), Path('ground.json'), ground_saved,
                  (ground, layout, map_file)),
        ]
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,39}', args.character):
        raise ValueError('Invalid character name')
    env = {'SELENE_CHAR': args.character, 'SELENE_CHAR_MESH': args.mesh}
    return [
        Stage('retarget', commandlet('character_retarget.py'), Path('retarget.json'), retarget_saved,
              (package(args.mesh), tools / 'character_retarget.py'), env),
        Stage('motion', capture('character_motion_shots.py'), Path('motion.json'), check_shots,
              (map_file, tools / 'character_motion_shots.py'), env),
    ]


@contextmanager
def editor_lease():
    try:
        LOCK.mkdir()
    except FileExistsError as exc:
        raise ValueError(f'An Unreal workflow holds {LOCK}; reconcile editor ownership first') from exc
    try:
        probe = subprocess.run(['pgrep', '-fl', 'UnrealEditor.*Selene.uproject'], capture_output=True, text=True)
        if probe.returncode != 1:
            raise ValueError('Cannot establish exclusive Selene editor access: ' + probe.stdout.strip())
        yield
    finally:
        LOCK.rmdir()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, default=Path('/Users/Shared/Epic Games/UE_5.8'))
    sub = parser.add_subparsers(dest='workflow', required=True)
    sub.add_parser('town').add_argument('--terrain', type=Path, required=True)
    sub.add_parser('ground')
    rig = sub.add_parser('character')
    rig.add_argument('--character', required=True)
    rig.add_argument('--mesh', required=True)
    args = parser.parse_args()
    try:
        with editor_lease():
            folder, ok = run(workflow(args), ROOT, ROOT / 'Saved/CheckedStages' / args.workflow)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(1, f'{exc}\n')
    print(folder / 'manifest.json')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
