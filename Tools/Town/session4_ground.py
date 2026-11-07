"""Headless geometry-only pavement arrangement, from immutable session-3 grade.
Constrained triangulation unites road junctions; no downloads/dependencies.
"""
import bpy,json,math
import numpy as np
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'Saved/TownV2/session-4/meshes-refined';O.mkdir(parents=True,exist_ok=True)
L=json.loads((R/'Design/TownV2/layout.json').read_text());Z=np.load(R/'Saved/TownV2/session-3/meshes/graded-elevation-metres.npy')
def raw(e,n):
 x=np.clip((e+590)/1500*1008,0,1007.999);y=np.clip((n+750)/1500*1008,0,1007.999);i=int(x);j=int(y);a=x-i;b=y-j
 return float(Z[j,i]*(1-a)*(1-b)+Z[j,i+1]*a*(1-b)+Z[j+1,i]*(1-a)*b+Z[j+1,i+1]*a*b)
def h(e,n):
 # Match the actual planar triangles of the saved 2.5 m core mesh.
 x=math.floor((e+150)/2.5)*2.5-150;y=math.floor((n+150)/2.5)*2.5-150;a=(e-x)/2.5;b=(n-y)/2.5
 z00=raw(x,y);z11=raw(x+2.5,y+2.5)
 return z00*(1-a)+raw(x+2.5,y)*(a-b)+z11*b if a>=b else z00*(1-b)+raw(x,y+2.5)*(b-a)+z11*a
verts=[];constraints=[];regions=[]
def polygon(points,kind):
 pts=[tuple(p[:2]) for p in points]
 if pts[0]==pts[-1]:pts.pop()
 if sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts)))<0:pts.reverse()
 ids=[]
 # Densify boundaries to preserve terrain curvature.
 for p,q in zip(pts,pts[1:]+pts[:1]):
  count=max(1,math.ceil(math.dist(p,q)/2))
  for j in range(count):ids.append(len(verts));verts.append(Vector((p[0]+(q[0]-p[0])*j/count,p[1]+(q[1]-p[1])*j/count)))
 constraints.append(ids);regions.append(kind)
def ribbon(points,width,kind):
 pts=[p[:2] for p in points];left=[];right=[]
 for i,p in enumerate(pts):
  a=pts[max(i-1,0)];b=pts[min(i+1,len(pts)-1)];dx=b[0]-a[0];dy=b[1]-a[1];length=max(.001,math.hypot(dx,dy));nx=-dy/length;ny=dx/length
  left.append((p[0]+nx*width/2,p[1]+ny*width/2));right.append((p[0]-nx*width/2,p[1]-ny*width/2))
 polygon(left+right[::-1],kind)
# Town boundary follows the built district; the seaward lawn is a retained park.
city=[(-125,64),(-57,27),(-39,-2),(-25,-28),(26,-67),(64,-125),(128,-125),(128,128),(-125,128)]
polygon(city,'district')
roads=[]
for road in L['streets']:
 ped=road['kind'] in ['footway','path','steps','pedestrian'];width=max(road['width_m'],2.5 if ped else 7.5 if road['kind']=='tertiary' else 5.5 if road['kind']=='unclassified' else 4.5)
 ribbon(road['points'],width if ped else width+5,'sidewalk')
 if not ped:ribbon(road['points'],width,'road')
 roads.append({'id':road['id'],'kind':road['kind'],'source_width_m':road['width_m'],'width_m':width,'sidewalk_each_m':2.5 if not ped else None})
# Plaza and adjoining courts stay connected all the way to cafe and clock.
polygon([(-38,-1),(-7,-1),(-7,21),(-38,21)],'plaza')
ribbon([[-24,18],[-24,61]],7,'sidewalk');ribbon([[-10,10],[12,11],[43,12]],6,'sidewalk')
for area in L['areas']:
 if area['kind']=='parking':polygon(area['polygon'],'parking')
 if area['kind']=='grass':polygon(area['polygon'],'park')
# Deliberate planted courtyards, retained as park islands rather than stray lawn.
for cx,cy,rx,ry in [(4,-17,9,5),(57,86,10,7),(91,107,7,5)]:
 polygon([(cx+rx*math.cos(t*math.tau/32),cy+ry*math.sin(t*math.tau/32)) for t in range(32)],'park')
for lot in L['lots']:
 if lot['area_m2']>=25:
  pts=lot['footprint']['outer'][:-1];cx=sum(p[0] for p in pts)/len(pts);cy=sum(p[1] for p in pts)/len(pts)
  # Outward apron approximately 2.5 m, explicit boundary for every occupied frontage.
  polygon([(x+(x-cx)/max(.01,math.hypot(x-cx,y-cy))*2.5,y+(y-cy)/max(.01,math.hypot(x-cx,y-cy))*2.5) for x,y in pts],'sidewalk')
grid_start=len(verts);grid_values=np.arange(-130,131,2.5);grid_width=len(grid_values);grade_edges=[]
for y in grid_values:
 for x in grid_values:verts.append(Vector((float(x),float(y))))
for j in range(grid_width-1):
 for i in range(grid_width-1):
  a=grid_start+j*grid_width+i;grade_edges.extend([(a,a+1),(a,a+grid_width),(a,a+grid_width+1)])
vv,ee,ff,ov,oe,orig=delaunay_2d_cdt(verts,grade_edges,constraints,0,.0001,True)
print('TRIANGULATED',len(vv),len(ff),flush=True)
sets={name:([],[]) for name in ['V4Roads','V4Paving','V4Parking','V4Curbs']};types=[];heights={'road':.065,'parking':.10,'paving':.19,'none':0}
for f,parents in zip(ff,orig):
 kinds={regions[i] for i in parents};e=sum(vv[i].x for i in f)/len(f);n=sum(vv[i].y for i in f)/len(f)
 typ='none'
 if kinds and h(e,n)>1.3:
  if 'road' in kinds:typ='road'
  elif 'park' not in kinds:
   if 'parking' in kinds:typ='parking'
   elif kinds.intersection({'district','plaza','sidewalk'}):typ='paving'
 types.append(typ)
 if typ=='none':continue
 name={'road':'V4Roads','parking':'V4Parking','paving':'V4Paving'}[typ];v,faces=sets[name];start=len(v)
 for i in f:e,n=vv[i];v.append((e,n,h(e,n)+heights[typ]))
 faces.append(tuple(range(start,len(v))))
# Rounded curb profile on true surface boundaries; no duplicate intersection curbs.
adj={}
for f,typ in zip(ff,types):
 for i,j in zip(f,f[1:]+f[:1]):adj.setdefault(tuple(sorted((i,j))),[]).append((typ,i,j))
for edge,sides in adj.items():
 cats={s[0] for s in sides}
 if 'paving' not in cats or cats=={'paving'}:continue
 typ,i,j=next(s for s in sides if s[0]=='paving');a=vv[i];b=vv[j];dx=b.x-a.x;dy=b.y-a.y;length=max(.001,math.hypot(dx,dy));nx=-dy/length;ny=dx/length
 # Inward bevel is inside paving, leaving the measured carriageway clear.
 v,f=sets['V4Curbs'];k=len(v)
 for p in [a,b]:
  for off,zz in [(0,.065),(.035,.19),(.10,.23),(.25,.23),(.30,.19)]:
   x=p.x+nx*off;y=p.y+ny*off;v.append((x,y,h(x,y)+zz))
 for t in range(4):f.append((k+t,k+5+t,k+6+t,k+1+t))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);report={}
for name,(v,f) in sets.items():
 bpy.ops.object.select_all(action='DESELECT');mesh=bpy.data.meshes.new(name);mesh.from_pydata([(n,-e,z) for e,n,z in v],[],f);mesh.update();a=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(a);a.select_set(True);bpy.context.view_layer.objects.active=a
 mat=bpy.data.materials.new(name+'_Placeholder');mat.diffuse_color=(.5,.45,.35,1);mesh.materials.append(mat)
 bpy.ops.export_scene.gltf(filepath=str(O/(name+'.glb')),export_format='GLB',use_selection=True,export_yup=True,export_apply=True)
 report[name]={'vertices':len(v),'faces':len(f)}
report.update(roads=roads,sidewalk_width_m=2.5,city_boundary=city,park_islands=[[4,-17,9,5],[57,86,10,7],[91,107,7,5]],method='Shared constrained planar triangulation, explicit original terrain triangle constraints to eliminate grass breakthroughs, rounded 5-point curb profile; original heightmap unchanged')
(O/'ground.json').write_text(json.dumps(report,indent=2));print('V4_GROUND_COMPLETE',flush=True)
