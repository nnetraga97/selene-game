"""Shared, stdlib-only geometry and terrain contract (metres, east/north/up)."""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(path=None):
    return json.loads(Path(path or ROOT / "Design/Blockout/layout.json").read_text())


def local_xy(shape, x, y):
    a = math.radians(shape.get("rotation", 0))
    dx, dy = x - shape["center"][0], y - shape["center"][1]
    return dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a)


def world_xy(shape, x, y):
    a = math.radians(shape.get("rotation", 0))
    return [
        shape["center"][0] + x * math.cos(a) - y * math.sin(a),
        shape["center"][1] + x * math.sin(a) + y * math.cos(a),
    ]


def polygon(shape):
    if "polygon" in shape:
        return shape["polygon"]
    w, d = shape["size"]
    return [
        world_xy(shape, x, y)
        for x, y in [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]
    ]


def inside(poly, x, y):
    hit = False
    for a, b in zip(poly, poly[1:] + poly[:1]):
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (
            b[1] - a[1]
        ) + a[0]:
            hit = not hit
    return hit


def overlap(a, b):
    """SAT for convex footprint polygons; touching boundaries are permitted."""
    for poly in (a, b):
        for p, q in zip(poly, poly[1:] + poly[:1]):
            axis = (p[1] - q[1], q[0] - p[0])
            pa = [x * axis[0] + y * axis[1] for x, y in a]
            pb = [x * axis[0] + y * axis[1] for x, y in b]
            if min(max(pa), max(pb)) - max(min(pa), min(pb)) <= 1e-6:
                return False
    return True


def raw_height(data, x, y):
    h = data["terrain"]["height_model"]
    return h["rise"] * max(0, min(1, (y - h["start_y"]) / (h["end_y"] - h["start_y"])))


def surface_pads(data):
    # Increasing priority: streets/slabs, lots, then stair corridors.
    pads = list(data["terrain"]["pads"])
    for lot in data["lots"]:
        pads.append(dict(lot["footprint"], z=lot["base_z"], blend=2, margin=0.8))
    return pads


def height(data, x, y, pads=None):
    z = raw_height(data, x, y)
    for pad in pads if pads is not None else surface_pads(data):
        lx, ly = local_xy(pad, x, y)
        w, d = pad["size"]
        dist = math.hypot(
            max(abs(lx) - w / 2 - pad.get("margin", 0), 0),
            max(abs(ly) - d / 2 - pad.get("margin", 0), 0),
        )
        blend = pad.get("blend", 2)
        if dist <= blend:
            t = 1 if dist == 0 else 1 - dist / blend
            t = t * t * (3 - 2 * t)
            z = z * (1 - t) + pad["z"] * t
    for corridor in data["streets"] + data["stairs"]:
        pts = corridor["points"]
        width = corridor["width"] / 2
        for a, b in zip(pts, pts[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            t = max(
                0, min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / (dx * dx + dy * dy))
            )
            dist = math.hypot(x - a[0] - t * dx, y - a[1] - t * dy)
            if dist <= width + 2:
                weight = max(0, min(1, (width + 2 - dist) / 2))
                target = a[2] + (b[2] - a[2]) * t
                z = z * (1 - weight) + target * weight
    return z


def route_points(data, route):
    return [
        [
            p[0],
            p[1],
            p[2] if len(p) == 3 else height(data, *p) + route.get("eye_height", 1.65),
        ]
        for p in route["points"]
    ]


def distances(points):
    result = [0.0]
    for a, b in zip(points, points[1:]):
        result.append(result[-1] + math.dist(a, b))
    return result


def length(data, route):
    return distances(route_points(data, route))[-1]


def terrain_digest(data):
    """Identity of inputs that affect terrain geometry (routes/materials excluded)."""
    import hashlib

    inputs = {
        "terrain": data["terrain"],
        "lots": [
            {"footprint": l["footprint"], "base_z": l["base_z"]} for l in data["lots"]
        ],
        "corridors": [
            {"points": c["points"], "width": c["width"]}
            for c in data["streets"] + data["stairs"]
        ],
    }
    return hashlib.sha256(
        json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
