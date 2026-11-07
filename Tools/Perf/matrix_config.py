"""Read-only matrix preflight: signature inspection and duration calculation."""
import math
from pathlib import Path
import plistlib
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Blockout'))
from layout_core import load, length


def require_unsandboxed(app):
    result = subprocess.run(['codesign', '-d', '--entitlements', ':-', str(app)],
                            capture_output=True)
    if result.returncode:
        raise ValueError('Cannot inspect app signature: ' + result.stderr.decode(errors='replace'))
    # codesign diagnostics go to stderr; entitlement XML goes to stdout.
    raw = result.stdout
    start = raw.find(b'<?xml')
    if start < 0:
        start = raw.find(b'<plist')
    if start >= 0:
        entitlements = plistlib.loads(raw[start:])
    elif not raw.strip():
        entitlements = {}
    else:
        raise ValueError('Unrecognized codesign entitlement output; refusing to launch')
    if entitlements.get('com.apple.security.app-sandbox'):
        raise ValueError('Sandboxed app cannot write matrix outputs. Rebuild/repackage with '
                         '-ubtargs="-noEntitlements" and verify the resulting signature.')


def timeout_seconds(route, layout, speed, laps, warmup, override='', route_length=''):
    if route_length:
        cm = float(route_length)
    else:
        data = load(layout)
        matches = [r for r in data['routes'] if r['id'] == route]
        if len(matches) != 1:
            raise ValueError(f'Unknown/duplicate route {route}; supply --layout or --route-length-cm')
        cm = length(data, matches[0]) * 100
    if not math.isfinite(cm) or cm <= 0:
        raise ValueError('Route length must be positive and finite')
    # 60 s startup, moving warmup, cold + warm laps with 2 s settle each,
    # then 120 s completion/I/O plus 10% traversal slack.
    duration = warmup + (laps + 1) * (cm / speed + 2)
    minimum = math.ceil(60 + duration * 1.10 + 120)
    if override:
        value = float(override)
        if not math.isfinite(value) or value < minimum:
            raise ValueError(f'--timeout must be at least {minimum}s for {route}')
        return math.ceil(value)
    return minimum


if __name__ == '__main__':
    route, layout, speed, laps, warmup, override, route_length = sys.argv[1:]
    print(timeout_seconds(route, layout, float(speed), int(laps), float(warmup), override, route_length))
