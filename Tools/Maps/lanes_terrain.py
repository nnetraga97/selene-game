#!/usr/bin/env python3
"""Terrain pass for the 3-lane test map: base plateaus, side-lane hills, overpasses, a centre landmark,
lane cover and structure plinths. Reads docs/maps/lanes-test/layout.json, writes its "terrain" key and
terrain.svg. Units: metres, layout frame (X base to base, Y across). Pieces are designed on the Dawn half
(x <= 0) and mirrored by a 180-degree rotation, like lanes_layout.py.

Piece formats:
  box : {"kind":"box","role","c":[x,y],"size":[len,width,height],"z":bottom,"yaw_deg","mat"}
  ramp: {"kind":"ramp","role","low":[x,y],"high":[x,y],"width","z_low","z_high","thick","mat"}
"""
import json, math, random, shutil, subprocess, sys

DIR = sys.argv[1] if len(sys.argv) > 1 else "docs/maps/lanes-test"
L = json.load(open(f"{DIR}/layout.json"))
LANES = {k: [tuple(p) for p in v] for k, v in L["lanes"].items()}
ALLEYS = [[tuple(p) for p in a] for a in L["alleys"]]
BASES = {k: tuple(v) for k, v in L["bases"].items()}
LANE_HALF = L["lane_half_width"]
rnd = random.Random(11)

# ---------- geometry
def corners(c, w, d, yaw):
    cs, sn = math.cos(yaw), math.sin(yaw)
    return [(c[0] + x * cs - y * sn, c[1] + x * sn + y * cs) for x, y in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2))]

def sat(A, B):
    for P in (A, B):
        for a, b in zip(P, P[1:] + P[:1]):
            nx, ny = b[1] - a[1], a[0] - b[0]
            pa = [x * nx + y * ny for x, y in A]; pb = [x * nx + y * ny for x, y in B]
            if max(pa) < min(pb) or max(pb) < min(pa): return False
    return True

def seg_d(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)

def poly_d(p, poly): return min(seg_d(p, a, b) for a, b in zip(poly, poly[1:]))

def segs(poly): return [(a, b, math.hypot(b[0] - a[0], b[1] - a[1])) for a, b in zip(poly, poly[1:])]

def at(poly, s):
    for a, b, l in segs(poly):
        if s <= l:
            t = s / l; return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), math.atan2(b[1] - a[1], b[0] - a[0])
        s -= l
    a, b, l = segs(poly)[-1]; return b, math.atan2(b[1] - a[1], b[0] - a[0])

def length(poly): return sum(l for *_, l in segs(poly))

BUILDINGS = [corners((b["x"], b["y"]), L["sizes"][b["asset"]][0] + 0.4, L["sizes"][b["asset"]][1] + 0.4, math.radians(b["yaw_deg"]))
             for b in L["buildings"]]   # 0.2 m clearance each side

def footprint(p):
    if p["kind"] == "box":
        return corners(p["c"], p["size"][0], p["size"][1], math.radians(p["yaw_deg"]))
    (lx, ly), (hx, hy) = p["low"], p["high"]
    return corners(((lx + hx) / 2, (ly + hy) / 2), math.hypot(hx - lx, hy - ly), p["width"], math.atan2(hy - ly, hx - lx))

def mirror(p):
    q = dict(p)
    if p["kind"] == "box":
        q["c"] = [-p["c"][0], -p["c"][1]]; q["yaw_deg"] = (p["yaw_deg"] + 180.0) % 360.0
    else:
        q["low"] = [-p["low"][0], -p["low"][1]]; q["high"] = [-p["high"][0], -p["high"][1]]
    return q

# ---------- piece makers
def box(role, c, size, z, yaw_deg, mat="plaza"):
    return {"kind": "box", "role": role, "c": [round(c[0], 3), round(c[1], 3)], "size": [round(s, 3) for s in size],
            "z": round(z, 3), "yaw_deg": round(yaw_deg % 360.0, 2), "mat": mat}

def ramp(role, low, high, width, z_low, z_high, mat="road", thick=0.4):
    return {"kind": "ramp", "role": role, "low": [round(low[0], 3), round(low[1], 3)], "high": [round(high[0], 3), round(high[1], 3)],
            "width": width, "z_low": z_low, "z_high": z_high, "thick": thick, "mat": mat}

pieces, dropped = [], []
def keep(p, check_buildings=True, mirror_it=True):
    fp = footprint(p)
    if check_buildings and any(sat(fp, b) for b in BUILDINGS):
        dropped.append({"role": p["role"], "kind": p["kind"], "at": p.get("c") or p.get("low")}); return False
    pieces.append(p)
    if mirror_it: pieces.append(mirror(p))
    return True

def group(ps, mirror_it=True):
    """All-or-nothing: keep a set of pieces only if none hits a building."""
    if any(any(sat(footprint(p), b) for b in BUILDINGS) for p in ps):
        dropped.append({"role": ps[0]["role"], "kind": "group", "at": ps[0].get("c") or ps[0].get("low")}); return False
    for p in ps: keep(p, False, mirror_it)
    return True

blocked = []    # (footprint, why): areas lane cover must avoid
def block(p, grow=1.0):
    fp = footprint(p); cx = sum(x for x, _ in fp) / 4; cy = sum(y for _, y in fp) / 4
    blocked.append([(cx + (x - cx) * grow, cy + (y - cy) * grow) for x, y in fp])

# ---------- a. base plateaus with lane ramps and parapets
PLAT, PLAT_H, RAMP_LEN = 38.0, 2.5, 15.0
base = BASES["dawn"]; half = PLAT / 2
plat = box("base", base, (PLAT, PLAT, PLAT_H), 0.0, 0.0, "plaza")
keep(plat, check_buildings=False); block(plat, 1.05)
exits = []   # angle of each lane leaving the platform
for name, poly in LANES.items():
    s = 0.0
    while s < length(poly):       # first point of the lane outside the platform square
        p, ang = at(poly, s)
        if abs(p[0] - base[0]) > half or abs(p[1] - base[1]) > half: break
        s += 0.05
    edge, ang = at(poly, s)
    low = (edge[0] + math.cos(ang) * RAMP_LEN, edge[1] + math.sin(ang) * RAMP_LEN)
    r = ramp("base", edge, low, 2 * LANE_HALF - 0.4, 0.0, PLAT_H)
    r["low"], r["high"] = [round(low[0], 3), round(low[1], 3)], [round(edge[0] - math.cos(ang) * 0.6, 3), round(edge[1] - math.sin(ang) * 0.6, 3)]
    r["z_high"] = PLAT_H
    keep(r); block(r, 1.15)
    exits.append((edge, ang))
# parapets: walk the platform edge and leave gaps where ramps leave
step = 0.5; runs = []
for side in range(4):
    run_pts = []
    for i in range(int(PLAT / step) + 1):
        t = -half + i * step
        q = [(base[0] + t, base[1] - half), (base[0] + half, base[1] + t), (base[0] - t, base[1] + half), (base[0] - half, base[1] - t)][side]
        gap = any(math.hypot(q[0] - e[0], q[1] - e[1]) < LANE_HALF + 1.5 for e, _ in exits)
        if not gap: run_pts.append(q)
        elif run_pts: runs.append(run_pts); run_pts = []
    if run_pts: runs.append(run_pts)
for run in runs:
    if len(run) < 3: continue
    a, b = run[0], run[-1]; c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    keep(box("cover", c, (math.hypot(b[0] - a[0], b[1] - a[1]) + 0.5, 0.5, 1.0), PLAT_H, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])), "curb"), False)

# ---------- b. side-lane hill on the north lane's longest Dawn-half straight
HILL_H, HILL_RAMP, HILL_TOP = 1.5, 10.0, 10.0
north = LANES["north"]
STRUCTS = [tuple(st["pos"]) for st in L["structures"] if st["type"] in ("guardian", "walker")]
SPAN = HILL_TOP + 2 * HILL_RAMP
def hill_at(m, ang):
    u = (math.cos(ang), math.sin(ang)); pt = lambda d: (m[0] + u[0] * d, m[1] + u[1] * d); w = 2 * LANE_HALF - 0.4
    return [ramp("hill", pt(-HILL_TOP / 2 - HILL_RAMP), pt(-HILL_TOP / 2 + 0.3), w, 0.0, HILL_H),
            box("hill", m, (HILL_TOP, w, HILL_H), 0.0, math.degrees(ang), "road"),
            ramp("hill", pt(HILL_TOP / 2 + HILL_RAMP), pt(HILL_TOP / 2 - 0.3), w, 0.0, HILL_H)]
options = []
for a, b, l in segs(north):
    ang = math.atan2(b[1] - a[1], b[0] - a[0]); u = (math.cos(ang), math.sin(ang))
    d = SPAN / 2 + 2
    while d <= l - SPAN / 2 - 2:
        m = (a[0] + u[0] * d, a[1] + u[1] * d); d += 1.0
        if m[0] > -SPAN / 2: continue
        if min(math.hypot(m[0] - q[0], m[1] - q[1]) for q in STRUCTS) < SPAN / 2 + 8: continue
        hill = hill_at(m, ang)
        if any(sat(footprint(p), x) for p in hill for x in blocked + BUILDINGS): continue
        options.append((abs(m[0] + 60), m, ang))   # prefer the middle of the Dawn half
if options:
    _, m, ang = min(options)
    hill = hill_at(m, ang); group(hill)
    for p in hill: block(p, 1.1)
else:
    dropped.append({"role": "hill", "kind": "group", "at": None})

# ---------- c. overpasses over the mid lane on the x = -40 alley
DECK_Z, DECK_T, DECK_W, STAIR_LEN, STAIR_W = 4.5, 0.5, 5.4, 16.0, 5.0
mid = LANES["mid"]
for al in ALLEYS:
    x = al[0][0]
    if abs(x + 40) > 0.1: continue
    # mid lane y at this x
    yc = next(a[1] + (x - a[0]) / (b[0] - a[0]) * (b[1] - a[1]) for a, b, _ in segs(mid) if min(a[0], b[0]) <= x <= max(a[0], b[0]) and a[0] != b[0])
    dl = 2 * LANE_HALF + 2.0 + 4.0            # deck spans lane + pillar room
    deck = box("overpass", (x, yc), (DECK_W, dl, DECK_T), DECK_Z - DECK_T, 0.0, "plaza")
    parts = [deck]
    for s in (1, -1):
        top = (x, yc + s * dl / 2)
        bottom = (x, yc + s * (dl / 2 + STAIR_LEN))
        parts.append(ramp("overpass", bottom, (top[0], top[1] - s * 0.3), STAIR_W, 0.0, DECK_Z, "plaza"))
        for px in (-1, 1):
            parts.append(box("overpass", (x + px * (DECK_W / 2 - 0.5), yc + s * (LANE_HALF + 1.2)), (1.0, 1.0, DECK_Z - DECK_T), 0.0, 0.0, "curb"))
    for px in (-1, 1):
        parts.append(box("overpass", (x + px * (DECK_W / 2 - 0.15), yc), (0.3, dl, 0.9), DECK_Z, 0.0, "curb"))
    if group(parts):
        for p in parts: block(p, 1.2)

# ---------- d. centre landmark beside the mid lane (single, not mirrored)
cp = min(((at(mid, s / 10.0)) for s in range(int(length(mid) * 10))), key=lambda pa: math.hypot(*pa[0]))
(c0, ang0) = cp
off = 8.5
lm = (c0[0] - math.sin(ang0) * off, c0[1] + math.cos(ang0) * off)
mono = [box("landmark", lm, (4.0, 4.0, 1.0), 0.0, math.degrees(ang0), "curb"),
        box("landmark", lm, (1.6, 1.6, 10.0), 1.0, math.degrees(ang0), "plaza")]
lm2 = (-lm[0], -lm[1])
if math.hypot(lm[0] - lm2[0], lm[1] - lm2[1]) > 6.0:
    group(mono)                               # mirrored pair, one each side of the lane
else:
    group(mono, mirror_it=False)
for p in mono: block(p, 1.6)

# ---------- f. plinths under guardians and walkers (before cover, so cover avoids them)
PL, PL_H, PL_RAMP = 9.0, 0.6, 3.0
for s in L["structures"]:
    if s["team"] != "dawn" or s["type"] not in ("guardian", "walker"): continue
    poly = LANES[s["lane"]]; sp = s["pos"]
    best = min((abs(math.hypot(at(poly, d / 4)[0][0] - sp[0], at(poly, d / 4)[0][1] - sp[1])), d / 4) for d in range(int(length(poly) * 4)))
    _, ang = at(poly, best[1]); u = (math.cos(ang), math.sin(ang))
    parts = [box("plinth", sp, (PL, PL, PL_H), 0.0, math.degrees(ang), "curb")]
    for sgn in (1, -1):
        edge = (sp[0] + u[0] * sgn * PL / 2, sp[1] + u[1] * sgn * PL / 2)
        parts.append(ramp("plinth", (edge[0] + u[0] * sgn * PL_RAMP, edge[1] + u[1] * sgn * PL_RAMP),
                          (edge[0] - u[0] * sgn * 0.2, edge[1] - u[1] * sgn * 0.2), PL, 0.0, PL_H, "curb", 0.3))
    if not group(parts):
        dropped.pop(); keep(parts[0], check_buildings=False)   # structures stand in the lane: the plinth itself always fits
    for p in parts: block(p, 1.0)
    blocked.append(corners(sp, 14.0, 14.0, ang))     # 7 m clear round the structure

# ---------- e. lane cover
def cover_piece(c, ang):
    kind = rnd.choice(("wall", "crates", "pillar"))
    if kind == "wall": return [box("cover", c, (3.0, 0.8, 1.2), 0.0, math.degrees(ang), "curb")]
    if kind == "pillar": return [box("cover", c, (1.0, 1.0, 3.0), 0.0, math.degrees(ang), "curb")]
    out = [box("cover", c, (1.6, 1.6, 1.6), 0.0, math.degrees(ang), "road")]
    if rnd.random() < 0.5: out.append(box("cover", c, (1.6, 1.6, 1.6), 1.6, math.degrees(ang) + 20, "road"))
    return out

spawns = [tuple(s["pos"]) for s in L["structures"] if s["type"] in ("minion_spawn", "hero_spawn")]
for name, poly in LANES.items():
    total = length(poly); s = 30.0; side = 1 if name != "south" else -1
    while s < total:
        p, ang = at(poly, s)
        if p[0] > -2.0: break
        lat = rnd.uniform(4.2, 5.2) * side
        c = (p[0] - math.sin(ang) * lat, p[1] + math.cos(ang) * lat)
        ps = cover_piece(c, ang)
        fp = footprint(ps[0])
        ok = (not any(sat(fp, b) for b in blocked) and all(math.hypot(c[0] - q[0], c[1] - q[1]) > 7 for q in spawns)
              and all(math.hypot(c[0] - b[0], c[1] - b[1]) > 27 for b in BASES.values()))
        if ok and group(ps):
            side = -side; s += rnd.uniform(22.0, 28.0)
        else:
            s += 3.0
# alley mouths: two to three pieces where each Dawn-half alley meets a lane
for al in ALLEYS:
    x = al[0][0]
    if x > 0.1: continue
    for end in (al[0], al[1]):
        inward = 1 if end[1] < 0 else -1
        for k in range(rnd.choice((1, 2))):
            c = (x + rnd.choice((-1, 1)) * rnd.uniform(1.0, 2.0), end[1] + inward * (LANE_HALF + 3.0 + k * 4.0))
            ps = [box("cover", c, (1.6, 1.6, 1.6), 0.0, rnd.uniform(0, 90), "road")] if k else [box("cover", c, (2.4, 0.8, 1.2), 0.0, 0.0, "curb")]
            if not any(sat(footprint(ps[0]), b) for b in blocked): group(ps)

# ---------- write
L["terrain"] = pieces
json.dump(L, open(f"{DIR}/layout.json", "w"), indent=1)

def slope(p):
    if p["kind"] != "ramp": return 0.0
    run = math.hypot(p["high"][0] - p["low"][0], p["high"][1] - p["low"][1])
    return math.degrees(math.atan2(p["z_high"] - p["z_low"], run))

roles = {}
for p in pieces: roles[p["role"]] = roles.get(p["role"], 0) + 1
summary = {"pieces": len(pieces), "per_role": roles, "max_slope_deg": round(max(map(slope, pieces)), 1), "dropped": dropped}

# ---------- svg
BX, BY = L["bounds"]; S = 5.0; W = (BX * 2 + 10) * S; H = (BY * 2 + 10) * S; LEG = 260
X = lambda x: (x + BX + 5) * S; Y = lambda y: (BY + 5 - y) * S
def pts(cs): return " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in cs)
def hcol(h):
    t = max(0.0, min(1.0, h / 4.5)); return f"rgb({int(70 + 160 * t)},{int(120 + 60 * t)},{int(200 - 120 * t)})"
o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W + LEG:.0f} {H + 60:.0f}" font-family="Helvetica,Arial,sans-serif">',
     f'<rect width="{W + LEG:.0f}" height="{H + 60:.0f}" fill="#14161b"/><rect width="{W:.0f}" height="{H:.0f}" fill="#1d2027"/>']
for al in ALLEYS: o.append(f'<line x1="{X(al[0][0]):.0f}" y1="{Y(al[0][1]):.0f}" x2="{X(al[1][0]):.0f}" y2="{Y(al[1][1]):.0f}" stroke="#34373f" stroke-width="{6 * S:.0f}"/>')
for poly in LANES.values():
    o.append(f'<polyline points="{pts(poly)}" fill="none" stroke="#3a3d46" stroke-width="{LANE_HALF * 2 * S:.0f}" stroke-linejoin="round" stroke-linecap="round"/>')
for b in L["buildings"]:
    o.append(f'<polygon points="{pts(corners((b["x"], b["y"]), L["sizes"][b["asset"]][0], L["sizes"][b["asset"]][1], math.radians(b["yaw_deg"])))}" fill="#555a66" fill-opacity="0.35"/>')
order = {"base": 0, "hill": 1, "plinth": 2, "overpass": 3, "landmark": 4, "cover": 5}
for p in sorted(pieces, key=lambda p: (order.get(p["role"], 9), p.get("z", 0))):
    fp = footprint(p)
    if p["role"] == "cover":
        o.append(f'<polygon points="{pts(fp)}" fill="#ff7a3c" stroke="#000" stroke-width="1"/>'); continue
    top = p["z"] + p["size"][2] if p["kind"] == "box" else p["z_high"]
    o.append(f'<polygon points="{pts(fp)}" fill="{hcol(top)}" fill-opacity="0.9" stroke="#0c0d10" stroke-width="1.2"/>')
    if p["kind"] == "ramp":
        (lx, ly), (hx, hy) = p["low"], p["high"]
        o.append(f'<line x1="{X(lx):.0f}" y1="{Y(ly):.0f}" x2="{X(hx):.0f}" y2="{Y(hy):.0f}" stroke="#fff" stroke-width="2" marker-end="url(#a)"/>')
o.insert(1, '<defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#fff"/></marker></defs>')
for s in L["structures"]:
    if s["type"] in ("guardian", "walker", "patron"):
        o.append(f'<circle cx="{X(s["pos"][0]):.0f}" cy="{Y(s["pos"][1]):.0f}" r="9" fill="{"#ffd23f" if s["team"] == "dawn" else "#b56bff"}" stroke="#000" stroke-width="2"/>')
lx = W + 16; y = 34
o.append(f'<text x="{lx}" y="{y}" fill="#fff" font-size="20" font-weight="700">Terrain</text>'); y += 30
for h in (0.6, 1.5, 2.5, 4.5):
    o.append(f'<rect x="{lx}" y="{y - 13}" width="18" height="16" fill="{hcol(h)}"/><text x="{lx + 26}" y="{y}" fill="#dde" font-size="15">top {h} m</text>'); y += 24
o.append(f'<rect x="{lx}" y="{y - 13}" width="18" height="16" fill="#ff7a3c"/><text x="{lx + 26}" y="{y}" fill="#dde" font-size="15">cover (1.2-3 m)</text>'); y += 24
o.append(f'<text x="{lx}" y="{y}" fill="#dde" font-size="15">arrow = uphill</text>'); y += 34
for k, v in roles.items(): o.append(f'<text x="{lx}" y="{y}" fill="#aab" font-size="15">{k}: {v}</text>'); y += 22
o.append(f'<text x="{lx}" y="{y + 10}" fill="#aab" font-size="15">max slope {summary["max_slope_deg"]}°</text>')
o.append(f'<text x="24" y="{H + 40:.0f}" fill="#fff" font-size="22" font-weight="700">Selene lanes map — terrain pass (plateaus, hills, overpasses, cover)</text></svg>')
open(f"{DIR}/terrain.svg", "w").write("\n".join(o))
if shutil.which("rsvg-convert"):
    subprocess.run(["rsvg-convert", "-o", f"{DIR}/terrain.svg.png", f"{DIR}/terrain.svg"], check=False)
else:
    try:
        import cairosvg; cairosvg.svg2png(url=f"{DIR}/terrain.svg", write_to=f"{DIR}/terrain.svg.png")
    except Exception:
        pass
print(json.dumps(summary, indent=1))
