#!/usr/bin/env python3
"""Plan-only dressing checks; yaw_deg is Unreal yaw (UE X=north, Y=east).

Sizes below are imported mesh X/Y/Z, not layout E/N/Z. Pending imports use
conservative envelopes; the editor script checks actual bounds before spawning.
R1 buffer is capsule radius 0.34 m PLUS 1.0 m clear space, in plan even overhead.
"""
import argparse
import json
import math
from pathlib import Path

from layout_core import ROOT, inside, local_xy, overlap, polygon, world_xy

SIZES = {
    'plaza-bench': (1.34, .86, .90),
    'vending-machine': (1.02, .71, 1.90),
    'delivery-scooter': (.91, 1.88, 1.35),
    'espresso-machine': (.70, .70, .48),
    'bistro-chair-r2': (.50, .52, .85),
    'hydrangea-clump-r2': (.75, .91, .65),
    'potted-plant-r2': (.48, .84, 1.25),
    'trash-bin-r2': (.53, .57, .95),
    'wall-ac-unit-r2': (.62, .82, .60),
    'wall-lantern-r2': (.20, .36, .48),
    'concrete-planter': (1.2, 1.2, .6),
    'street-tree': (5., 5., 6.2),  # full assembly: trunk + leaf-card crown, 6.0 m as imported
    'bistro-table': (.75, .75, .75),
    'pendant-lamp': (.6, .6, .6),
}
BUFFER = 1.34


def asset_key(p):
    return p['asset'].split('/')[3]


def dimensions(p):
    s = p.get('scale', [1, 1, 1])
    if isinstance(s, (int, float)):
        s = [s] * 3
    return [a * b for a, b in zip(SIZES[asset_key(p)], s)]


def footprint(p):
    w, d, _ = dimensions(p)
    return polygon(dict(center=p['position'][:2], size=[w, d], rotation=90-p['yaw_deg']))


def point_segment(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    t = max(0, min(1, ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy))) if dx or dy else 0
    return math.hypot(p[0]-a[0]-t*dx, p[1]-a[1]-t*dy)


def cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def segment_distance(a, b, c, d):
    if (cross(a,b,c)*cross(a,b,d) < 0 and cross(c,d,a)*cross(c,d,b) < 0):
        return 0
    return min(point_segment(a,c,d), point_segment(b,c,d), point_segment(c,a,b), point_segment(d,a,b))


def path_distance(poly, points):
    if any(inside(poly, *p[:2]) for p in points):
        return 0
    return min(segment_distance(a,b,c,d) for a,b in zip(poly, poly[1:]+poly[:1])
               for c,d in zip(points, points[1:]))


def wall_mount(p, poly, lot):
    """Recognize wall assets by asset identity, never a user-supplied exemption."""
    key = asset_key(p)
    if key not in ('wall-ac-unit-r2', 'wall-lantern-r2') or lot['id'] != 'cafe':
        return False
    coords = [local_xy(lot['footprint'], *v) for v in poly]
    w,d = lot['footprint']['size']
    z = p['position'][2] - lot['base_z']
    top = z + dimensions(p)[2]
    full = lot['ground_height']+(lot['storeys']-1)*lot['floor_height']
    for wall, axis, edge, sign in [('east',0,w/2,1), ('west',0,-w/2,-1), ('north',1,d/2,1), ('south',1,-d/2,-1)]:
        values = [v[axis] for v in coords]
        near = min(values) if sign == 1 else max(values)
        along = [v[1-axis] for v in coords]
        span = d if axis == 0 else w
        if abs(near-edge) > .015 or max(abs(v) for v in along) > span/2 or z < 0 or top > full:
            continue
        for o in lot['interior']['openings']:
            if o['wall'] == wall and z < o['sill']+o['height'] and top > o['sill']:
                if min(along) < o['offset']+o['width']/2 and max(along) > o['offset']-o['width']/2:
                    break
        else:
            return True
    return False


def validate(data, layout):
    errors = []
    minimum = float('inf')
    lots = {l['id']:l for l in layout['lots']}
    route = next(r['points'] for r in layout['routes'] if r['id']=='R1')
    seen = set()
    def check(ok, msg):
        if not ok: errors.append(msg)
    check(data.get('schema_version') == 1, 'schema_version must be 1')
    for p in data['placements'] + data['buildings']:
        check(isinstance(p['id'], str) and p['id'] and p['id'] not in seen, f"duplicate/invalid id: {p['id']}")
        seen.add(p['id'])
        check(p['asset'].startswith('/Game/'), f"{p['id']}: invalid asset path")
        check(isinstance(p['yaw_deg'], (int,float)) and math.isfinite(p['yaw_deg']), f"{p['id']}: invalid yaw")
    for p in data['placements']:
        name = p['id']
        check(len(p['position'])==3 and all(isinstance(v,(int,float)) and math.isfinite(v) for v in p['position']), name+': invalid position')
        check(p.get('collision', 'none') in ('simple','none'), name+': invalid collision')
        check(len(dimensions(p))==3 and all(math.isfinite(v) and v>0 for v in dimensions(p)), name+': invalid scale')
        poly = footprint(p)
        distance = path_distance(poly, route)
        minimum = min(minimum, distance)
        check(distance >= BUFFER-1e-6, f'{name}: R1 footprint distance {distance:.3f} < {BUFFER}')
        check(path_distance(poly, [layout['player_start']['position'],layout['player_start']['position']]) >= BUFFER-1e-6, name+': player start clearance')
        mounted = wall_mount(p, poly, lots['cafe'])
        if asset_key(p).startswith('wall-'):
            check(mounted, name+': wall mount is not flush or covers an opening')
        for lot in layout['lots']:
            if not overlap(poly, polygon(lot['footprint'])):
                continue
            shell = lot.get('interior')
            if lot['id']=='cafe' and shell:
                w,d = lot['footprint']['size']
                t = shell['wall_thickness']
                inner = all(abs(x)<w/2-t-1e-6 and abs(y)<d/2-t-1e-6 for x,y in [local_xy(lot['footprint'],*v) for v in poly])
                z = p['position'][2]-lot['base_z']
                check(inner and z>=0 and z+dimensions(p)[2]<=shell['clear_height'], name+': intersects cafe wall/floor/ceiling')
                # Counter appliance may sit exactly on counter; all other interior
                # assets must avoid existing counter/seat volumes.
                for prop in shell.get('props',[]):
                    center = world_xy(lot['footprint'], *prop['center'])
                    shape = dict(center=center,size=prop['size'][:2],rotation=lot['footprint'].get('rotation',0))
                    if overlap(poly, polygon(shape)):
                        check(z>=prop['size'][2]-1e-6, name+': intersects cafe '+prop['id'])
            else:
                check(False, name+': overlaps '+lot['id'])
        # Keep an additional capsule + 1 m route from either doorway face.
        for o in lots['cafe']['interior']['openings']:
            if o['kind']=='door':
                w,d = lots['cafe']['footprint']['size']
                if o['wall']=='north':
                    door=[world_xy(lots['cafe']['footprint'],o['offset'],d/2+v) for v in (-1,1)]
                    check(path_distance(poly,door)>=BUFFER-1e-6,name+': doorway approach clearance')
    for b in data['buildings']:
        check(b['fit'] in ('height','footprint','native'), b['id']+': invalid fit')
        lot = lots[b['lot']]
        check(path_distance(polygon(lot['footprint']), route)>=BUFFER-1e-6,b['id']+': building lot too close to R1')
    return errors, minimum


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dressing',type=Path,default=ROOT/'Design/Blockout/dressing.json')
    ap.add_argument('--layout',type=Path,default=ROOT/'Design/Blockout/layout.json')
    args=ap.parse_args()
    try:
        data=json.loads(args.dressing.read_text()); layout=json.loads(args.layout.read_text())
        errors,minimum=validate(data,layout)
    except (KeyError,ValueError,TypeError,IndexError) as exc:
        raise SystemExit('ERROR: invalid dressing schema: '+str(exc))
    if errors: raise SystemExit('\n'.join('ERROR: '+e for e in errors))
    print(f"VALID: {len(data['placements'])} placements, {len(data['buildings'])} building replacements; all IDs unique")
    print(f'R1 minimum footprint distance: {minimum:.3f} m; capsule-edge clearance: {minimum-.34:.3f} m (required 1.000 m)')
    print('PASS: lot/wall intersections, flush wall mounts, cafe shell/props, doorway and player-start clearance')
    print('Pending-import envelopes require actual mesh bounds and orientation review in Unreal.')

if __name__=='__main__': main()
