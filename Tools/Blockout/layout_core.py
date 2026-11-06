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


def route_geometry(data, route):
    """Sample an upright capsule's feet path; retain authored segment boundaries.

    Two-dimensional anchors follow terrain, explicit Z denotes floor height.
    Samples follow terrain between anchors and the tops of constructed paving
    and stairs. Near a riser the lower hemisphere contacts its edge before the
    capsule centre crosses it, so the feet path rises continuously at that edge.
    """
    radius = 0.34  # Native SeleneCharacter radius; verified against the CDO.
    pads = surface_pads(data)
    steps = []
    for stair in data["stairs"]:
        for a, b in zip(stair["points"], stair["points"][1:]):
            n = math.ceil(abs(b[2] - a[2]) / stair["max_riser"])
            run = math.dist(a[:2], b[:2])
            for i in range(n):
                t = (i + 0.5) / n
                steps.append(dict(center=[a[j] + (b[j] - a[j]) * t for j in range(2)],
                    size=[run / n + 0.015, stair["width"]],
                    rotation=math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])),
                    z=a[2] + (b[2] - a[2]) * (i + 1) / n))

    def ground(x, y, authored):
        z = max(height(data, x, y, pads), authored if authored is not None else -math.inf)
        for slab in data["slabs"]:
            lx, ly = local_xy(slab, x, y)
            distance = math.hypot(max(abs(lx) - slab["size"][0] / 2, 0),
                                  max(abs(ly) - slab["size"][1] / 2, 0))
            if distance < radius:
                z = max(z, slab["z"] + 0.025 - radius + math.sqrt(radius**2 - distance**2))
        for street in data["streets"]:
            for a, b in zip(street["points"], street["points"][1:]):
                dx, dy = b[0] - a[0], b[1] - a[1]
                run = math.hypot(dx, dy)
                t = ((x - a[0]) * dx + (y - a[1]) * dy) / run**2
                side = abs((x - a[0]) * dy - (y - a[1]) * dx) / run
                distance = math.hypot(max(max(-t, t - 1) * run - 0.015, 0),
                                      max(side - street["width"] / 2, 0))
                if distance < radius:
                    slope = (b[2] - a[2]) / run
                    # Builder's pitched 16 cm paving cube, including edge contact.
                    z = max(z, a[2] + max(0, min(1, t)) * (b[2] - a[2]) + 0.025
                            + (radius + 0.08) * (math.sqrt(1 + slope**2) - 1)
                            - radius + math.sqrt(radius**2 - distance**2))
        for step in steps:
            lx, ly = local_xy(step, x, y)
            distance = math.hypot(max(abs(lx) - step["size"][0] / 2, 0),
                                  max(abs(ly) - step["size"][1] / 2, 0))
            if distance < radius:
                z = max(z, step["z"] - radius + math.sqrt(radius**2 - distance**2))
        return z

    points, anchors = [], []
    for index, a in enumerate(route["points"]):
        if index:
            b = a
            a = route["points"][index - 1]
            # Resolve the curved capsule contact at stair edges more finely.
            near_stairs = any(all(
                max(a[j], b[j]) >= min(p[j] for p in stair["points"]) - stair["width"] / 2 - radius
                and min(a[j], b[j]) <= max(p[j] for p in stair["points"]) + stair["width"] / 2 + radius
                for j in range(2)) for stair in data["stairs"])
            count = max(1, math.ceil(math.dist(a[:2], b[:2]) / (0.05 if near_stairs else 0.25)))
            for i in range(1, count):
                t = i / count
                x, y = [a[j] + (b[j] - a[j]) * t for j in range(2)]
                authored = a[2] + (b[2] - a[2]) * t if len(a) == len(b) == 3 else None
                points.append([x, y, ground(x, y, authored)])
            a = b
        anchors.append(len(points))
        points.append([a[0], a[1], ground(a[0], a[1], a[2] if len(a) == 3 else None)])
    return points, anchors


def route_points(data, route):
    return route_geometry(data, route)[0]


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
