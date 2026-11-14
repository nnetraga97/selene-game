"""Macro elevation for the lanes map (proposal): lanes and alleys stay low corridors, the blocks between them rise into
high ground, the land outside the side lanes rises into an outer terrace, and the mid plaza dips into a shallow bowl.
Every rise blends over about 8 m, so slopes stay under about 20 degrees and any edge is walkable.
lanes_heightfield.py adds this on top of the base/plinth/hill pieces when layout.json has "elevation": true.
Run on its own to write docs/maps/lanes-test/elevation.svg (preview)."""
import json, math, sys

LANE_HALF, ALLEY_HALF, BLEND = 6.0, 3.0, 8.0
JUNGLE_H, OUTER_H, MID_BOWL = 2.2, 3.5, -1.2


def _seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def _poly_dist(px, py, pts):
    return min(_seg_dist(px, py, *pts[i], *pts[i + 1]) for i in range(len(pts) - 1))


def _poly_y_at(x, pts):
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        if min(ax, bx) <= x <= max(ax, bx) and ax != bx:
            return ay + (by - ay) * (x - ax) / (bx - ax)
    return None


def smooth(e0, e1, v):
    t = max(0.0, min(1.0, (v - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


class Elevation:
    def __init__(self, layout):
        self.lanes = layout['lanes']
        self.alleys = layout['alleys']
        self.bases = list(layout['bases'].values())
        self.base_r = layout['base_radius']

    def at(self, x, y):
        d_lane = min(_poly_dist(x, y, p) for p in self.lanes.values())
        d_alley = min((_poly_dist(x, y, p) for p in self.alleys), default=1e9)
        # Region height away from any path: outer terrace beyond the side lanes, high ground between lanes.
        region = JUNGLE_H
        for name, sign in (('north', 1), ('south', -1)):
            ly = _poly_y_at(x, self.lanes[name])
            if ly is not None and sign * (y - ly) > 0:
                region = JUNGLE_H + (OUTER_H - JUNGLE_H) * smooth(0, 20, sign * (y - ly))
        # Path floors: lanes at 0, the mid plaza a shallow bowl.
        floor = MID_BOWL * (1 - smooth(10, 32, math.hypot(x, y)))
        # Corridor mask: 0 on a lane or alley, 1 in the open blocks.
        m = smooth(LANE_HALF, LANE_HALF + BLEND, d_lane) * smooth(ALLEY_HALF, ALLEY_HALF + BLEND, d_alley)
        h = floor + (region - floor) * m
        # Bases stay at their plateau height (pieces add it): fade the macro out around them.
        d_base = min(math.hypot(x - bx, y - by) for bx, by in self.bases)
        return h * smooth(self.base_r, self.base_r + 14, d_base)


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'docs/maps/lanes-test/layout.json'
    L = json.load(open(path)); E = Elevation(L)
    bx, by = L['bounds']; cell = 2.0; S = 5.0   # px per metre
    W, H = int(2 * bx * S), int(2 * by * S)
    X = lambda x: (x + bx) * S
    Y = lambda y: (by - y) * S
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W + 260} {H}" font-family="Helvetica,Arial,sans-serif">',
           f'<rect width="{W + 260}" height="{H}" fill="#14161b"/>']

    def col(h):
        t = max(0.0, min(1.0, (h - MID_BOWL) / (OUTER_H - MID_BOWL)))
        stops = [(0, (40, 70, 120)), (0.25, (70, 110, 90)), (0.6, (150, 150, 90)), (1, (200, 120, 70))]
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t <= t1:
                k = (t - t0) / (t1 - t0)
                return '#%02x%02x%02x' % tuple(int(a + (b - a) * k) for a, b in zip(c0, c1))
        return '#c87846'

    hs = []
    y = -by
    while y < by:
        x = -bx
        while x < bx:
            h = E.at(x + cell / 2, y + cell / 2); hs.append(h)
            out.append(f'<rect x="{X(x):.0f}" y="{Y(y + cell):.0f}" width="{cell * S + 1:.0f}" height="{cell * S + 1:.0f}" fill="{col(h)}"/>')
            x += cell
        y += cell
    for b in L['buildings']:
        sx, sy = L['sizes'].get(b['asset'], [10, 10, 0])[:2]
        out.append(f'<rect x="{X(b["x"]) - sx * S / 2:.0f}" y="{Y(b["y"]) - sy * S / 2:.0f}" width="{sx * S:.0f}" height="{sy * S:.0f}" '
                   f'fill="none" stroke="#000" stroke-opacity="0.35" transform="rotate({-b["yaw_deg"]:.0f} {X(b["x"]):.0f} {Y(b["y"]):.0f})"/>')
    for pts in L['lanes'].values():
        out.append('<polyline fill="none" stroke="#fff" stroke-opacity="0.8" stroke-width="3" points="' + ' '.join(f'{X(a):.0f},{Y(c):.0f}' for a, c in pts) + '"/>')
    for pts in L['alleys']:
        out.append('<polyline fill="none" stroke="#fff" stroke-opacity="0.4" stroke-width="2" stroke-dasharray="6 5" points="' + ' '.join(f'{X(a):.0f},{Y(c):.0f}' for a, c in pts) + '"/>')
    for s in L['structures']:
        c = '#7fb3ff' if s['team'] == 'dawn' else '#ff8a7a'
        out.append(f'<circle cx="{X(s["pos"][0]):.0f}" cy="{Y(s["pos"][1]):.0f}" r="7" fill="{c}" stroke="#000"/>')
    lx = W + 30
    out.append(f'<text x="{lx}" y="40" fill="#fff" font-size="22">Elevation (m)</text>')
    for i, h in enumerate([OUTER_H, 3.0, JUNGLE_H, 1.0, 0.0, MID_BOWL]):
        out.append(f'<rect x="{lx}" y="{60 + i * 40}" width="30" height="30" fill="{col(h)}"/><text x="{lx + 42}" y="{82 + i * 40}" fill="#ddd" font-size="18">{h:+.1f}</text>')
    out.append(f'<text x="{lx}" y="{340}" fill="#ddd" font-size="16">white: lanes</text><text x="{lx}" y="{364}" fill="#ddd" font-size="16">dashed: alleys</text>'
               f'<text x="{lx}" y="{388}" fill="#ddd" font-size="16">dots: structures</text><text x="{lx}" y="{412}" fill="#ddd" font-size="16">outlines: buildings</text>')
    out.append('</svg>')
    open('docs/maps/lanes-test/elevation.svg', 'w').write('\n'.join(out))
    print(json.dumps({'min': round(min(hs), 2), 'max': round(max(hs), 2), 'raised_share': round(sum(1 for h in hs if h > 1.0) / len(hs), 2)}))
