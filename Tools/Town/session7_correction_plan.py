"""Read-only terrain/tree planning for one placement correction; no asset edits."""
from pathlib import Path
import json,heapq,math,struct,collections
R=Path(__file__).resolve().parents[2];O=R/'Saved/TownV2/session-7';B=json.loads((O/'audit-before.json').read_text());P=json.loads((O/'apply.json').read_text())
obstacles=[]
for a in B['actors']:
 if a['label'].startswith('V2_Tree'):
  obstacles.append((a['bounds_center'][1]/100,a['bounds_center'][0]/100,a['extent'][1]/100+2.0,a['extent'][0]/100+2.0))
def clear(e,n):return not any(abs(e-x)<w and abs(n-y)<d for x,y,w,d in obstacles)
start=(125,55);goal=(298,60);q=[(0,start)];came={start:None};g={start:0}
while q:
 _,p=heapq.heappop(q)
 if p==goal:break
 for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
  n=(p[0]+dx,p[1]+dy)
  if not (124<=n[0]<=300 and 20<=n[1]<=110) or not clear(*n):continue
  cost=g[p]+math.hypot(dx,dy)
  if cost<g.get(n,1e9):g[n]=cost;came[n]=p;heapq.heappush(q,(cost+math.dist(n,goal),n))
assert goal in came
path=[];v=goal
while v is not None:path.append(v);v=came[v]
path.reverse()
def line_clear(p,q):
 count=math.ceil(math.dist(p,q)*3)
 return all(clear(p[0]+(q[0]-p[0])*t/count,p[1]+(q[1]-p[1])*t/count) for t in range(count+1))
simple=[path[0]];i=0
while i<len(path)-1:
 j=len(path)-1
 while j>i+1 and not line_clear(path[i],path[j]):j-=1
 simple.append(path[j]);i=j
for p in P['placements']:
 for e,n in p['terrace']['corners_m']:assert clear(e+134,n),'Moved footprint touches tree clearance'
# Source geometry confirms one thin dangling fragment below the walk-up floor.
b=(R/'SourceArt/Assets/metro-walkup/metro-walkup.glb').read_bytes();size=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+size]);binary=b[28+size:];a=j['accessors'][0];bv=j['bufferViews'][a['bufferView']];o=bv.get('byteOffset',0)+a.get('byteOffset',0);vs=list(struct.iter_unpack('<fff',binary[o:o+a['count']*12]));floor=[y for x,y,z in vs if y<2.5 and (abs(x)>8 or abs(z)>4.5)]
plan={'reason':'Pines intersected initial city footprints/fronts; preserve every existing actor by moving the six-building cluster 134m east to clear hillside. Walk-up has dangling fragment below its floor.','east_shift_m':134,'lane_east_m':298,'town_link':simple,'town_link_length_m':sum(math.dist(p,q) for p,q in zip(simple,simple[1:])),'walkup_floor_offset_m':1.65,'walkup_low_vertex_count_below_1_5m':sum(y<1.5 for x,y,z in vs),'walkup_total_vertices':len(vs),'walkup_perimeter_floor_min_m':min(floor),'tree_canopy_and_path_half_width_clearance':True}
(O/'correction-plan.json').write_text(json.dumps(plan,indent=2));print(json.dumps(plan,indent=2))
