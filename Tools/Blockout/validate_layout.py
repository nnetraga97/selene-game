#!/usr/bin/env python3
"""Validate schema v1 plus checkpoint constraints. No third party dependencies."""

import argparse
import math
import sys
from collections import Counter
from layout_core import (
    load,
    polygon,
    overlap,
    length,
    distances,
    route_points,
    local_xy,
)


def validate(d):
    errors = []

    def check(ok, text):
        if not ok:
            errors.append(text)

    def num(v):
        return (
            isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
        )

    def point(p, n):
        return isinstance(p, list) and len(p) == n and all(num(v) for v in p)

    def shape(s, name):
        # v1 deliberately uses oriented rectangles, with optional rounded-corner massing.
        check(
            isinstance(s, dict)
            and point(s.get("center"), 2)
            and point(s.get("size"), 2)
            and all(v > 0 for v in s.get("size", []))
            and num(s.get("rotation", 0)),
            name + ": invalid rect",
        )

    try:
        check(d["schema_version"] == 1, "unsupported schema_version")
        check(
            d["units"] == "metres" and d["axes"] == "east,north,up",
            "units/axes mismatch",
        )
        bounds = d["terrain"]["bounds"]
        check(
            point(bounds, 4) and bounds[0] < bounds[2] and bounds[1] < bounds[3],
            "invalid terrain bounds",
        )
        check(2 <= d["terrain"]["grid"] <= 4, "terrain grid must be 2–4 m")
        h = d["terrain"]["height_model"]
        check(
            h["type"] == "north_ramp"
            and h["start_y"] < h["end_y"]
            and 25 <= h["rise"] <= 30,
            "invalid height model",
        )
        for collection in ("areas", "lots", "slabs", "streets", "stairs", "routes"):
            check(
                isinstance(d[collection], list) and bool(d[collection]),
                collection + ": empty/not array",
            )
            ids = [v["id"] for v in d[collection]]
            check(len(set(ids)) == len(ids), collection + ": duplicate id")
        areas = {a["id"] for a in d["areas"]}
        for a in d["areas"]:
            shape(a, a["id"])
            check(
                len(a["color"]) == 7 and a["color"][0] == "#",
                a["id"] + ": color must be #RRGGBB",
            )
            int(a["color"][1:], 16)

        def within(p):
            return bounds[0] <= p[0] <= bounds[2] and bounds[1] <= p[1] <= bounds[3]

        for v in d["lots"]:
            name = v["id"]
            s = v["footprint"]
            shape(s, name)
            check(v["area"] in areas, name + ": unknown area")
            check(
                type(v["storeys"]) is int and 1 <= v["storeys"] <= 5,
                name + ": invalid storeys",
            )
            check(
                type(v["hero"]) is bool and num(v["base_z"]),
                name + ": invalid hero/base_z",
            )
            check(
                v["ground_height"] >= 4.2 and v["floor_height"] == 3.5,
                name + ": floor heights",
            )
            check(all(within(p) for p in polygon(s)), name + ": lot outside terrain")
            if "interior" in v:
                interior = v["interior"]
                clear = interior["clear_height"]
                t = interior["wall_thickness"]
                check(
                    num(clear) and clear >= 4.2 and 0 < t <= 0.5,
                    name + ": invalid shell dimensions",
                )
                check(
                    type(interior["optional"]) is bool,
                    name + ": optional must be boolean",
                )
                check(
                    clear
                    <= v["ground_height"] + (v["storeys"] - 1) * v["floor_height"],
                    name + ": shell too tall",
                )
                check(
                    any(
                        o["kind"] == "door" and o["sill"] == 0
                        for o in interior["openings"]
                    ),
                    name + ": no ground door",
                )
                for wall in ("north", "south", "east", "west"):
                    opens = [o for o in interior["openings"] if o["wall"] == wall]
                    span = s["size"][0 if wall in ("north", "south") else 1]
                    for o in opens:
                        check(
                            o["kind"] in ("door", "window")
                            and o["width"] > 0
                            and o["height"] > 0
                            and o["sill"] >= 0
                            and abs(o["offset"]) + o["width"] / 2 <= span / 2 - t
                            and o["height"] + o["sill"] <= clear,
                            name + ": invalid opening",
                        )
                    opens.sort(key=lambda o: o["offset"])
                    check(
                        all(
                            a["offset"] + a["width"] / 2 <= b["offset"] - b["width"] / 2
                            for a, b in zip(opens, opens[1:])
                        ),
                        name + ": overlapping openings",
                    )
                check(
                    all(
                        o["wall"] in ("north", "south", "east", "west")
                        for o in interior["openings"]
                    ),
                    name + ": invalid wall",
                )
        for i, a in enumerate(d["lots"]):
            for b in d["lots"][i + 1 :]:
                check(
                    not overlap(polygon(a["footprint"]), polygon(b["footprint"])),
                    f"lot overlap: {a['id']} / {b['id']}",
                )
        for s in d["slabs"]:
            shape(s, s["id"])
            check(num(s["z"]) and s["area"] in areas, s["id"] + ": invalid slab")
        for pad in d["terrain"]["pads"]:
            shape(pad, "terrain pad")
            check(num(pad["z"]) and pad["blend"] > 0, "invalid pad height/blend")
        for c in d["streets"] + d["stairs"]:
            check(
                c["area"] in areas and c["width"] > 0 and len(c["points"]) >= 2,
                c["id"] + ": invalid corridor",
            )
            check(
                all(point(p, 3) and within(p) for p in c["points"]),
                c["id"] + ": invalid corridor point",
            )
            for a, b in zip(c["points"], c["points"][1:]):
                check(math.dist(a[:2], b[:2]) > 0, c["id"] + ": zero length")
                strip = dict(
                    center=[(a[0] + b[0]) / 2, (a[1] + b[1]) / 2],
                    size=[math.dist(a[:2], b[:2]), c["width"]],
                    rotation=math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])),
                )
                for lot in d["lots"]:
                    if "interior" not in lot:
                        check(
                            not overlap(polygon(strip), polygon(lot["footprint"])),
                            c["id"] + ": corridor overlaps " + lot["id"],
                        )
            if c in d["stairs"]:
                check(0 < c["max_riser"] <= 0.18, c["id"] + ": excessive riser")
        check(50 <= len(d["lots"]) <= 60, "expected 50–60 lots")
        check(9 <= sum(v["hero"] for v in d["lots"]) <= 11, "expected ~10 heroes")
        counts = Counter(v["area"] for v in d["lots"])
        for a, lo, hi in [
            ("commercial", 14, 18),
            ("residential_a", 18, 24),
            ("residential_b", 8, 10),
            ("industrial", 6, 8),
        ]:
            check(lo <= counts[a] <= hi, a + ": lot count")
        check(
            {r["id"] for r in d["routes"]} == {"R1", "R2", "R3"},
            "missing/unknown camera routes",
        )
        for r in d["routes"]:
            check(
                len(r["points"]) >= 2
                and all(
                    (point(p, 2) or point(p, 3)) and within(p) for p in r["points"]
                ),
                r["id"] + ": invalid route points",
            )
            lo, hi = r["length_range"]
            measured = length(d, r)
            check(
                lo <= measured <= hi,
                f"{r['id']}: length {measured:.1f} outside [{lo}, {hi}]",
            )
            end = 0
            for s in r["segments"]:
                check(
                    s["tag"] in ("exterior", "doorway", "interior")
                    and s["start_index"] == end
                    and s["start_index"] < s["end_index"] < len(r["points"]),
                    r["id"] + ": invalid segment coverage",
                )
                end = s["end_index"]
            check(
                end == len(r["points"]) - 1, r["id"] + ": segments do not cover route"
            )
            # Sample at <=0.5 m. Solid lots and shell walls must not obstruct the camera.
            points = route_points(d, r)
            for a, b in zip(points, points[1:]):
                for i in range(math.ceil(math.dist(a, b) / 0.5) + 1):
                    t = i / max(1, math.ceil(math.dist(a, b) / 0.5))
                    p = [x + (y - x) * t for x, y in zip(a, b)]
                    for lot in d["lots"]:
                        x, y = local_xy(lot["footprint"], *p[:2])
                        w, h = lot["footprint"]["size"]
                        if abs(x) >= w / 2 + 0.15 or abs(y) >= h / 2 + 0.15:
                            continue
                        shell = lot.get("interior")
                        if not shell:
                            check(False, f"{r['id']}: passes through solid {lot['id']}")
                            break
                        if (
                            abs(x) < w / 2 - shell["wall_thickness"]
                            and abs(y) < h / 2 - shell["wall_thickness"]
                        ):
                            continue
                        wall = (
                            ("east" if x > 0 else "west")
                            if abs(x) / (w / 2) > abs(y) / (h / 2)
                            else ("north" if y > 0 else "south")
                        )
                        offset = y if wall in ("east", "west") else x
                        check(
                            any(
                                o["wall"] == wall
                                and o["kind"] == "door"
                                and abs(offset - o["offset"]) <= o["width"] / 2 - 0.15
                                for o in shell["openings"]
                            ),
                            f"{r['id']}: shell crossing misses {lot['id']} door",
                        )
        walk = d["east_west_walk"]
        seconds = distances(walk["points"])[-1] / walk["speed"]
        check(
            walk["speed"] == 1.5 and 300 <= seconds <= 360,
            f"E–W walk {seconds:.1f}s must be 300–360 s",
        )
        check(
            abs(walk["points"][0][0] - bounds[0]) < 1
            and abs(walk["points"][-1][0] - bounds[2]) < 1,
            "E–W walk does not span town",
        )
        check(
            point(d["player_start"]["position"], 3)
            and within(d["player_start"]["position"]),
            "invalid player start",
        )
        v = d["viaduct"]
        check(
            len(v["points"]) == 2
            and all(point(p, 3) for p in v["points"])
            and v["width"] > 0
            and v["pier_spacing"] > 0,
            "invalid viaduct",
        )
    except (KeyError, TypeError, ValueError, IndexError, ZeroDivisionError) as e:
        errors.append("Schema error: " + str(e))
    return list(dict.fromkeys(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout", nargs="?")
    args = parser.parse_args()
    try:
        d = load(args.layout)
    except (OSError, ValueError) as e:
        print(e, file=sys.stderr)
        return 1
    errors = validate(d)
    if errors:
        print("\n".join("ERROR: " + e for e in errors), file=sys.stderr)
        return 1
    print(f"VALID: {len(d['lots'])} lots, {sum(l['hero'] for l in d['lots'])} heroes")
    for r in d["routes"]:
        print(f"{r['id']}: {length(d, r):.2f} m")
    walk = d["east_west_walk"]
    meters = distances(walk["points"])[-1]
    print(
        f"E–W: {meters:.2f} m / 1.5 m/s = {meters / 1.5:.2f} s = {meters / 90:.3f} min"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
