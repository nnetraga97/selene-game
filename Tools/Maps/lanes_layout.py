#!/usr/bin/env python3
"""Generate the 3-lane test map layout (JSON + top-down SVG). Units: metres.
X runs base to base, Y across. The map is 180-degree rotationally symmetric."""
import json, math, random, sys, os
OUT = sys.argv[1] if len(sys.argv) > 1 else "docs/maps/lanes-test"
SEED = 7
LANE_HALF, ALLEY_HALF, GAP = 6.0, 3.0, 0.6
BOUND_X, BOUND_Y, FILL_REACH = 165.0, 118.0, 34.0
JOG, SPRINT = 4.43, 7.47
# asset: (frontage m, depth m, height m, triangles, colour)
B = {
 "apartment-curved": (12.3,12.5,18,17332,"#e07b6e"), "clock-hall": (25.5,20.7,22,10382,"#c9a24a"),
 "harbour-boathouse": (11.1,9.7,9,12392,"#5aa9c9"), "metro-brownstones": (16.6,10.2,13,8292,"#9e5b3c"),
 "metro-diner": (11.1,14.4,6.5,4618,"#d94f6a"), "metro-lane-houses": (14.0,9.2,9,10446,"#b98ad6"),
 "metro-walkup": (20.8,11.0,18,12391,"#7d6bd0"), "seaside-guesthouse": (12.9,12.5,15,18970,"#4fc1a6"),
 "seaside-lighthouse-house": (14.5,12.7,14,11664,"#3f8fd9"), "shop-bakery-corner": (10.5,8.2,13,19602,"#f0a646"),
 "shop-tool-repair": (9.2,9.8,9.5,11446,"#8aa34a"), "townhouse-terrace": (17.1,6.8,10,17500,"#d98f5a"),
 "workshop-garage": (16.5,15.1,10,13352,"#6f7f8f"), "metro-glass-office": (31.5,30.4,38,4202,"#6fb7c9"),
 "artdeco-tower": (55.9,32.2,80,14702,"#b9a37a"),
}
FRONT = [k for k in B if k not in ("metro-glass-office","artdeco-tower","clock-hall")]
FILL = ["metro-glass-office","clock-hall","metro-walkup","workshop-garage","metro-brownstones","seaside-lighthouse-house","metro-lane-houses","metro-diner","shop-tool-repair"]
rot = lambda p: (-p[0], -p[1])
MID = [(-104,0),(-62,0),(-24,13),(24,-13),(62,0),(104,0)]
NORTH = [(-112,28),(-100,68),(-56,86),(-10,70),(36,86),(86,76),(112,28)]
SOUTH = [rot(p) for p in reversed(NORTH)]          # runs Dawn (-x) to Dusk (+x)
LANES = {"north": NORTH, "mid": MID, "south": SOUTH}
BASES = {"dawn": (-128,0), "dusk": (128,0)}; BASE_R = 27.0
def lane_y(poly, x):
    for a,b in zip(poly, poly[1:]):
        if min(a[0],b[0]) <= x <= max(a[0],b[0]) and a[0]!=b[0]:
            t=(x-a[0])/(b[0]-a[0]); return a[1]+t*(b[1]-a[1])
ALLEYS = [[(x, lane_y(SOUTH,x)), (x, lane_y(NORTH,x))] for x in (-78,-40,0,40,78)]
def seg_d(p,a,b):
    ax,ay=a; bx,by=b; dx,dy=bx-ax,by-ay; L=dx*dx+dy*dy
    t=0 if L==0 else max(0,min(1,((p[0]-ax)*dx+(p[1]-ay)*dy)/L))
    return math.hypot(p[0]-ax-t*dx, p[1]-ay-t*dy)
def poly_d(p,poly): return min(seg_d(p,a,b) for a,b in zip(poly,poly[1:]))
def corners(c,w,d,yaw):
    cs,sn=math.cos(yaw),math.sin(yaw)
    return [(c[0]+x*cs-y*sn, c[1]+x*sn+y*cs) for x,y in ((-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2))]
def samples(cs, step=1.5):
    pts=[]
    for a,b in zip(cs, cs[1:]+cs[:1]):
        n=max(1,int(math.hypot(b[0]-a[0],b[1]-a[1])/step))
        pts += [(a[0]+(b[0]-a[0])*i/n, a[1]+(b[1]-a[1])*i/n) for i in range(n)]
    return pts
def sat(A,Bc):
    for P in (A,Bc):
        for a,b in zip(P,P[1:]+P[:1]):
            nx,ny=b[1]-a[1],a[0]-b[0]
            pa=[x*nx+y*ny for x,y in A]; pb=[x*nx+y*ny for x,y in Bc]
            if max(pa) < min(pb) or max(pb) < min(pa): return False
    return True
def grow(c,w,d,yaw,g): return corners(c,w+2*g,d+2*g,yaw)
placed=[]
fronts=[]   # (lane, side, s_start, s_end) of every lane-front building on the Dawn half
def free(c,w,d,yaw, lane_clear=LANE_HALF):
    cs=corners(c,w,d,yaw); pts=samples(cs)+[c]
    for p in pts:
        if abs(p[0])>BOUND_X or abs(p[1])>BOUND_Y: return False
        for poly in LANES.values():
            if poly_d(p,poly) < lane_clear: return False
        for al in ALLEYS:
            if poly_d(p,al) < ALLEY_HALF: return False
        for bc in BASES.values():
            if math.hypot(p[0]-bc[0],p[1]-bc[1]) < BASE_R: return False
    g=grow(c,w,d,yaw,GAP/2)
    return not any(sat(g,q["grown"]) for q in placed)
def put(name,c,yaw,role):
    w,d=B[name][0],B[name][1]
    for cc,yy in ((c,yaw),(rot(c),yaw+math.pi)):
        placed.append({"asset":name,"x":round(cc[0],2),"y":round(cc[1],2),"yaw_deg":round(math.degrees(yy)%360,1),
                       "role":role,"corners":corners(cc,w,d,yy),"grown":grow(cc,w,d,yy,GAP/2)})
def try_put(name,c,yaw,role):
    w,d=B[name][0],B[name][1]
    if c[0] > 0.01: return False                      # design the Dawn half, mirror the rest
    if not free(c,w,d,yaw): return False
    if sat(grow(c,w,d,yaw,GAP/2), grow(rot(c),w,d,yaw+math.pi,GAP/2)): return False
    put(name,c,yaw,role); return True
rnd=random.Random(SEED)
# backdrops behind the Dawn base (mirrored for Dusk)
try_put("artdeco-tower",(-146,-34),math.pi/2,"backdrop"); try_put("artdeco-tower",(-146,34),math.pi/2,"backdrop")
# rows fronting each lane, both sides
def along(poly):
    out=[]; 
    for a,b in zip(poly,poly[1:]):
        L=math.hypot(b[0]-a[0],b[1]-a[1]); out.append((a,b,L))
    return out
def at(poly,s):
    for a,b,L in along(poly):
        if s<=L: t=s/L; return (a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t), math.atan2(b[1]-a[1],b[0]-a[0])
        s-=L
    a,b,L=along(poly)[-1]; return b, math.atan2(b[1]-a[1],b[0]-a[0])
def length(poly): return sum(L for _,_,L in along(poly))
for lname,poly in LANES.items():
    for side in (1,-1):
        s=0.0; total=length(poly); last=None
        while s < total:
            opts=[n for n in FRONT if n!=last]; rnd.shuffle(opts); ok=False
            for name in opts[:5]:
                w,d=B[name][0],B[name][1]
                p,ang=at(poly,s+w/2)
                off=LANE_HALF+0.4+d/2
                c=(p[0]-math.sin(ang)*off*side, p[1]+math.cos(ang)*off*side)
                yaw=ang+(math.pi if side==1 else 0)      # front faces the lane
                if try_put(name,c,yaw,"lane-front"):
                    fronts.append((lname,side,s,s+w)); s+=w+GAP; last=name; ok=True; break
            if not ok: s+=1.5
# fill what is left near the lanes so there is no open ground
def near(c):
    return min(min(poly_d(c,p) for p in LANES.values()), min(math.hypot(c[0]-b[0],c[1]-b[1]) for b in BASES.values())-BASE_R+LANE_HALF) < FILL_REACH
for name in FILL:
    w,d=B[name][0],B[name][1]
    y=-BOUND_Y
    while y<=BOUND_Y:
        x=-BOUND_X
        while x<=0:
            for yaw in (0,math.pi/2):
                if near((x,y)) and try_put(name,(x,y),yaw,"fill"): break
            x+=2.0
        y+=2.0
# low walls that close the gaps left in the lane-front rows (never across a lane, alley or base)
walls=[]
def wall_ok(p):
    if any(poly_d(p,poly) < LANE_HALF-0.1 for poly in LANES.values()): return False
    if any(poly_d(p,al) < ALLEY_HALF for al in ALLEYS): return False
    return all(math.hypot(p[0]-b[0],p[1]-b[1]) >= BASE_R for b in BASES.values())
def inside(p):
    for q in placed:
        cs=q["corners"]; ok=True
        for a,b in zip(cs,cs[1:]+cs[:1]):
            if (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]) < 0: ok=False; break
        if ok: return True
    return False
for lname,poly in LANES.items():
    for side in (1,-1):
        total=length(poly); s=0.0; run=[]
        def flush():
            if len(run)>=2:
                a,b=run[0],run[-1]
                for A2,B2 in ((a,b),(rot(a),rot(b))): walls.append([[round(A2[0],2),round(A2[1],2)],[round(B2[0],2),round(B2[1],2)]])
            run.clear()
        while s<=total:
            p,ang=at(poly,s); off=LANE_HALF+0.6
            q=(p[0]-math.sin(ang)*off*side, p[1]+math.cos(ang)*off*side)
            if q[0]<=0.5 and wall_ok(q) and not inside(q): run.append(q)
            else: flush()
            if len(run)>=2 and abs(math.atan2(run[-1][1]-run[0][1],run[-1][0]-run[0][0])-ang)>0.05: 
                last_pt=run.pop(); flush(); run.append(last_pt)
            s+=0.75
        flush()
# structures and spawns
def frac(poly,f): return at(poly,length(poly)*f)[0]
structs=[]
for lname,poly in LANES.items():
    for team,fw,fg,fs in (("dawn",0.15,0.36,0.03),("dusk",0.85,0.64,0.97)):
        structs += [{"type":"walker","team":team,"lane":lname,"pos":frac(poly,fw)},
                    {"type":"guardian","team":team,"lane":lname,"pos":frac(poly,fg)},
                    {"type":"minion_spawn","team":team,"lane":lname,"pos":frac(poly,fs)}]
for team,c in BASES.items():
    structs.append({"type":"patron","team":team,"lane":None,"pos":c})
    structs.append({"type":"hero_spawn","team":team,"lane":None,"pos":(c[0]+(-12 if c[0]<0 else 12),c[1])})
counts={}; tris=0
for q in placed: counts[q["asset"]]=counts.get(q["asset"],0)+1; tris+=B[q["asset"]][3]
stats={"buildings":len(placed),"triangles":tris,"per_asset":counts,
       "lane_length_m":{k:round(length(v),1) for k,v in LANES.items()},
       "base_to_centre_jog_s":{k:round(length(v)/2/JOG,1) for k,v in LANES.items()},
       "base_to_centre_sprint_s":{k:round(length(v)/2/SPRINT,1) for k,v in LANES.items()}}
os.makedirs(OUT,exist_ok=True)
json.dump({"units":"m","seed":SEED,"lane_half_width":LANE_HALF,"alley_half_width":ALLEY_HALF,"base_radius":BASE_R,
           "lanes":LANES,"alleys":ALLEYS,"bases":BASES,"structures":structs,"walls":walls,"bounds":[BOUND_X,BOUND_Y],"sizes":{k:[v[0],v[1],v[2]] for k,v in B.items()},
           "buildings":[{k:q[k] for k in ("asset","x","y","yaw_deg","role")} for q in placed],"stats":stats},
          open(f"{OUT}/layout.json","w"),indent=1)
# ---- SVG
S=5.0; W=(BOUND_X*2+10)*S; LEG=330; H=(BOUND_Y*2+10)*S
X=lambda x:(x+BOUND_X+5)*S; Y=lambda y:(BOUND_Y+5-y)*S
o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W+LEG:.0f} {H+70:.0f}" font-family="Helvetica,Arial,sans-serif">',
   f'<rect width="{W+LEG:.0f}" height="{H+70:.0f}" fill="#14161b"/>',f'<rect x="0" y="0" width="{W:.0f}" height="{H:.0f}" fill="#1d2027"/>']
for c in BASES.values(): o.append(f'<circle cx="{X(c[0]):.0f}" cy="{Y(c[1]):.0f}" r="{BASE_R*S:.0f}" fill="#3a3d46"/>')
for al in ALLEYS: o.append(f'<line x1="{X(al[0][0]):.0f}" y1="{Y(al[0][1]):.0f}" x2="{X(al[1][0]):.0f}" y2="{Y(al[1][1]):.0f}" stroke="#34373f" stroke-width="{ALLEY_HALF*2*S:.0f}"/>')
LC={"north":"#e8c15a","mid":"#5ab0e8","south":"#7bd88f"}
for n,poly in LANES.items():
    pts=" ".join(f"{X(x):.0f},{Y(y):.0f}" for x,y in poly)
    o.append(f'<polyline points="{pts}" fill="none" stroke="#3a3d46" stroke-width="{LANE_HALF*2*S:.0f}" stroke-linejoin="round" stroke-linecap="round"/>')
    o.append(f'<polyline points="{pts}" fill="none" stroke="{LC[n]}" stroke-width="3" stroke-dasharray="10 8" stroke-linejoin="round"/>')
for q in placed:
    pts=" ".join(f"{X(x):.1f},{Y(y):.1f}" for x,y in q["corners"])
    o.append(f'<polygon points="{pts}" fill="{B[q["asset"]][4]}" fill-opacity="{0.55 if q["role"]!="lane-front" else 0.95}" stroke="#0c0d10" stroke-width="1.5"/>')
for a,b in walls: o.append(f'<line x1="{X(a[0]):.1f}" y1="{Y(a[1]):.1f}" x2="{X(b[0]):.1f}" y2="{Y(b[1]):.1f}" stroke="#ff5a2a" stroke-width="3"/>')
TC={"dawn":"#ffd23f","dusk":"#b56bff"}
for s in structs:
    x,y=X(s["pos"][0]),Y(s["pos"][1]); c=TC[s["team"]]
    if s["type"]=="guardian": o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="13" fill="{c}" stroke="#000" stroke-width="2"/><text x="{x:.0f}" y="{y+5:.0f}" font-size="15" font-weight="700" text-anchor="middle">G</text>')
    elif s["type"]=="walker": o.append(f'<rect x="{x-14:.0f}" y="{y-14:.0f}" width="28" height="28" fill="{c}" stroke="#000" stroke-width="2"/><text x="{x:.0f}" y="{y+5:.0f}" font-size="15" font-weight="700" text-anchor="middle">W</text>')
    elif s["type"]=="patron": o.append(f'<polygon points="{x:.0f},{y-24:.0f} {x+22:.0f},{y:.0f} {x:.0f},{y+24:.0f} {x-22:.0f},{y:.0f}" fill="{c}" stroke="#000" stroke-width="2"/><text x="{x:.0f}" y="{y+5:.0f}" font-size="15" font-weight="700" text-anchor="middle">P</text>')
    elif s["type"]=="minion_spawn": o.append(f'<polygon points="{x-9:.0f},{y-9:.0f} {x+9:.0f},{y:.0f} {x-9:.0f},{y+9:.0f}" fill="#fff" stroke="{c}" stroke-width="3" transform="rotate({0 if s["team"]=="dawn" else 180} {x:.0f} {y:.0f})"/>')
    else: o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="8" fill="none" stroke="#fff" stroke-width="3"/>')
o.append(f'<text x="{X(-128):.0f}" y="{Y(-32):.0f}" fill="{TC["dawn"]}" font-size="22" font-weight="700" text-anchor="middle">DAWN BASE</text>')
o.append(f'<text x="{X(128):.0f}" y="{Y(-32):.0f}" fill="{TC["dusk"]}" font-size="22" font-weight="700" text-anchor="middle">DUSK BASE</text>')
for n,(lx,ly) in {"north":(-10,84),"mid":(0,12),"south":(10,-84)}.items():
    o.append(f'<text x="{X(lx):.0f}" y="{Y(ly):.0f}" fill="{LC[n]}" font-size="20" font-weight="700" text-anchor="middle" stroke="#14161b" stroke-width="5" paint-order="stroke">{n.upper()} LANE  {stats["lane_length_m"][n]:.0f} m</text>')
o.append(f'<line x1="30" y1="{H-25:.0f}" x2="{30+50*S:.0f}" y2="{H-25:.0f}" stroke="#fff" stroke-width="4"/><text x="30" y="{H-35:.0f}" fill="#fff" font-size="18">50 m  (jog {50/JOG:.0f} s, sprint {50/SPRINT:.0f} s)</text>')
lx=W+18; y=34
o.append(f'<text x="{lx}" y="{y}" fill="#fff" font-size="21" font-weight="700">Buildings: {len(placed)}</text>'); y+=26
o.append(f'<text x="{lx}" y="{y}" fill="#aab" font-size="15">{tris/1e6:.2f} M triangles, {len(counts)} unique meshes</text>'); y+=30
for k,v in sorted(counts.items(), key=lambda kv:-kv[1]):
    o.append(f'<rect x="{lx}" y="{y-13}" width="18" height="16" fill="{B[k][4]}"/><text x="{lx+26}" y="{y}" fill="#dde" font-size="15">{k}  ×{v}</text>'); y+=23
y+=14
for lab,sh in (("G  Guardian (outer)","c"),("W  Walker (inner)","r"),("P  Patron (base)","d"),("▶  Minion spawn","t"),("○  Hero spawn","h")):
    o.append(f'<text x="{lx}" y="{y}" fill="#dde" font-size="15">{lab}</text>'); y+=23
y+=14
o.append(f'<text x="{lx}" y="{y}" fill="#fff" font-size="16" font-weight="700">Base to map centre</text>'); y+=23
for n in LANES:
    o.append(f'<text x="{lx}" y="{y}" fill="{LC[n]}" font-size="15">{n}: jog {stats["base_to_centre_jog_s"][n]:.0f} s, sprint {stats["base_to_centre_sprint_s"][n]:.0f} s</text>'); y+=23
y+=14
for t in ("Lanes 12 m wide, alleys 6 m","Solid colour = faces a lane","Faded = block filler","Orange = gap-closing wall","Flat ground, no terrain"):
    o.append(f'<text x="{lx}" y="{y}" fill="#aab" font-size="15">{t}</text>'); y+=22
o.append(f'<text x="30" y="{H+42:.0f}" fill="#fff" font-size="24" font-weight="700">Selene 3-lane test map — top-down layout, to scale ({BOUND_X*2:.0f} × {BOUND_Y*2:.0f} m)</text>')
o.append('</svg>'); open(f"{OUT}/layout.svg","w").write("\n".join(o))
print(json.dumps(stats,indent=1))
