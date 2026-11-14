"""Ground height of the lanes map as one continuous field (metres, layout frame), from layout.json's terrain pieces.
Ground-shaping roles (base plateaus, ramps, hills, plinths) become heights; everything else (cover, overpasses,
landmarks, parapets) stays as separate meshes. The field is lightly blurred so every join is a slope, not a seam.
Used by Tools/Unreal/lanes_ground.py (editor) and runnable on its own to print a summary."""
import json, math, os, sys

GROUND_ROLES = ('base', 'hill', 'plinth')
# Macro elevation (Tools/Maps/lanes_elevation.py): False restores the old, mostly flat ground.
ELEVATION = True


def is_ground(piece):
    """Pieces folded into the height field (parapet walls on the plateau stay separate)."""
    if piece['role'] not in GROUND_ROLES: return False
    if piece['kind'] == 'box' and piece['role'] == 'base' and piece['size'][2] < 2.0: return False
    return True


def _box_height(p, x, y):
    c = p['c']; L, W, H = p['size']; a = math.radians(p['yaw_deg'])
    dx, dy = x - c[0], y - c[1]
    u = dx * math.cos(a) + dy * math.sin(a); v = -dx * math.sin(a) + dy * math.cos(a)
    if abs(u) <= L / 2 and abs(v) <= W / 2: return p['z'] + H
    return None


def _ramp_height(p, x, y):
    (lx, ly), (hx, hy) = p['low'], p['high']
    dx, dy = hx - lx, hy - ly; run = math.hypot(dx, dy)
    if run < 1e-6: return None
    ux, uy = dx / run, dy / run
    t = (x - lx) * ux + (y - ly) * uy
    side = -(x - lx) * uy + (y - ly) * ux
    if t < -0.01 or t > run + 0.01 or abs(side) > p['width'] / 2: return None
    return p['z_low'] + (p['z_high'] - p['z_low']) * max(0.0, min(1.0, t / run))


def build(layout, cell=1.0, margin=30.0, blur_passes=2):
    """Returns (x0, y0, nx, ny, cell, heights[row-major ny][nx]) in metres."""
    bx, by = layout['bounds']
    x0, y0 = -bx - margin, -by - margin
    nx = int(round((2 * (bx + margin)) / cell)) + 1
    ny = int(round((2 * (by + margin)) / cell)) + 1
    pieces = [p for p in layout.get('terrain', []) if is_ground(p)]
    # Coarse bucket by bounding box to keep it fast.
    def bbox(p):
        if p['kind'] == 'box':
            r = math.hypot(p['size'][0], p['size'][1]) / 2; return (p['c'][0] - r, p['c'][1] - r, p['c'][0] + r, p['c'][1] + r)
        (lx, ly), (hx, hy) = p['low'], p['high']; w = p['width'] / 2 + 0.5
        return (min(lx, hx) - w, min(ly, hy) - w, max(lx, hx) + w, max(ly, hy) + w)
    boxes = [(bbox(p), p) for p in pieces]
    H = [[0.0] * nx for _ in range(ny)]
    for j in range(ny):
        y = y0 + j * cell
        row = H[j]
        live = [(b, p) for b, p in boxes if b[1] <= y <= b[3]]
        if not live: continue
        for i in range(nx):
            x = x0 + i * cell; best = 0.0
            for b, p in live:
                if not (b[0] <= x <= b[2]): continue
                h = _box_height(p, x, y) if p['kind'] == 'box' else _ramp_height(p, x, y)
                if h is not None and h > best: best = h
            row[i] = best
    if ELEVATION:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import lanes_elevation
        E = lanes_elevation.Elevation(layout)
        for j in range(ny):
            y = y0 + j * cell; row = H[j]
            for i in range(nx):
                row[i] += E.at(x0 + i * cell, y)
    # Soften: a few 3x3 averaging passes turn every hard edge into a short slope (about 2 m wide).
    for _ in range(blur_passes):
        G = [r[:] for r in H]
        for j in range(1, ny - 1):
            for i in range(1, nx - 1):
                s = 0.0
                for dj in (-1, 0, 1):
                    rj = H[j + dj]
                    s += rj[i - 1] + rj[i] + rj[i + 1]
                G[j][i] = s / 9.0
        H = G
    return x0, y0, nx, ny, cell, H


def macro(layout):
    """Macro elevation only (m): what pieces with absolute heights (cover, walls, ramps, overpasses) are raised by."""
    if not ELEVATION: return lambda x, y: 0.0
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import lanes_elevation
    return lanes_elevation.Elevation(layout).at


def sampler(layout):
    """height_at(x, y) in metres (layout frame), bilinear over the built field."""
    x0, y0, nx, ny, cell, H = build(layout)
    def height_at(xm, ym):
        fx = min(max((xm - x0) / cell, 0.0), nx - 1.001); fy = min(max((ym - y0) / cell, 0.0), ny - 1.001)
        i, j = int(fx), int(fy); tx, ty = fx - i, fy - j
        a = H[j][i] * (1 - tx) + H[j][i + 1] * tx
        b = H[j + 1][i] * (1 - tx) + H[j + 1][i + 1] * tx
        return a * (1 - ty) + b * ty
    return height_at


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'docs/maps/lanes-test/layout.json'
    L = json.load(open(path))
    x0, y0, nx, ny, cell, H = build(L)
    flat = [h for r in H for h in r]
    print(json.dumps({'grid': [nx, ny], 'cell_m': cell, 'max_h': round(max(flat), 2), 'raised_cells': sum(1 for h in flat if h > 0.05),
                      'ground_pieces': sum(1 for p in L.get('terrain', []) if is_ground(p))}))
