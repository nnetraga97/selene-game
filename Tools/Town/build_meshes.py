"""Headless Blender: TownV2 heightmap terrain and continuous road ribbons. No downloads."""
import bpy, json, math
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'Saved/TownV2/session-3/meshes';O.mkdir(parents=True,exist_ok=True)
L=json.loads((R/'Design/TownV2/layout.json').read_text());Z=np.load(R/'Design/TownV2/terrain/elevation-metres.npy')
def height(e,n):
 x=np.clip((e+590)/1500*1008,0,1007.999);y=np.clip((n+750)/1500*1008,0,1007.999);i=int(x);j=int(y);a=x-i;b=y-j
 return float(Z[j,i]*(1-a)*(1-b)+Z[j,i+1]*a*(1-b)+Z[j+1,i]*(1-a)*b+Z[j+1,i+1]*a*b)
# Two explicit game paths connect the adapted plaza to its hero destinations.
L['streets'] += [
 {'id':'design/plaza-clock-link','points':[[-8,10,0],[12,11,0],[39,12,0]],'width_m':3.,'kind':'pedestrian'},
 {'id':'design/plaza-cafe-link','points':[[-24,20,0],[-24,39,0],[-24,52,0]],'width_m':2.6,'kind':'pedestrian'}]
# Road grading: smooth longitudinal height over 12 m and blend a level cross-section
# into the prepared DSM. The source heightmap stays immutable; this is a mesh derivative.
base=Z.copy();total=np.zeros_like(Z);weight=np.zeros_like(Z);influence=np.zeros_like(Z)
for road in L['streets']:
 pp=[]
 for a,b in zip(road['points'],road['points'][1:]):
  count=max(1,math.ceil(math.dist(a[:2],b[:2])/2))
  pp.extend([(a[0]+(b[0]-a[0])*t/count,a[1]+(b[1]-a[1])*t/count) for t in range(count)])
 pp.append(tuple(road['points'][-1][:2]));zz=np.array([height(x,y) for x,y in pp]);kernel=np.exp(-.5*(np.arange(-9,10)/3.)**2);kernel/=kernel.sum();zz=np.convolve(np.pad(zz,(9,9),mode='edge'),kernel,mode='valid')
 half=road['width_m']/2+(0 if road['kind'] in ['footway','path','steps','pedestrian'] else 1.5);reach=half+5
 for k,(a,b) in enumerate(zip(pp,pp[1:])):
  ix0=max(0,int((min(a[0],b[0])-reach+590)/1500*1008));ix1=min(1009,int((max(a[0],b[0])+reach+590)/1500*1008)+2);iy0=max(0,int((min(a[1],b[1])-reach+750)/1500*1008));iy1=min(1009,int((max(a[1],b[1])+reach+750)/1500*1008)+2)
  xx,yy=np.meshgrid(np.arange(ix0,ix1)/1008*1500-590,np.arange(iy0,iy1)/1008*1500-750);dx=b[0]-a[0];dy=b[1]-a[1];t=np.clip(((xx-a[0])*dx+(yy-a[1])*dy)/max(.001,dx*dx+dy*dy),0,1);distance=np.hypot(xx-a[0]-t*dx,yy-a[1]-t*dy);alpha=np.clip((reach-distance)/5,0,1);ww=alpha**3;grade=zz[k]*(1-t)+zz[k+1]*t
  view=np.s_[iy0:iy1,ix0:ix1];total[view]+=ww*grade;weight[view]+=ww;influence[view]=np.maximum(influence[view],alpha)
Z=base*(1-influence)+np.divide(total,weight,out=base.copy(),where=weight>0)*influence
# Preserve the exact adapted plaza surface and feather the join around its boundary.
xx,yy=np.meshgrid(np.arange(1009)/1008*1500-590,np.arange(1009)/1008*1500-750);distance=np.hypot(np.maximum(np.maximum(-37-xx,xx+8),0),np.maximum(np.maximum(-yy,yy-20),0));alpha=np.clip(1-distance/3,0,1);Z=Z*(1-alpha)+6.259*alpha
np.save(O/'graded-elevation-metres.npy',Z)
Z.astype('<f4').T.tofile(O/'graded-elevation-ue.f32')
(O/'grading.json').write_text(json.dumps({'method':'12 m longitudinal smoothing and 5 m blended road shoulders; source data unchanged','max_delta_m':float(np.max(abs(Z-base))),'design_links':['plaza-clock-link','plaza-cafe-link']},indent=2))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
report={}
def export(name,verts,faces):
 bpy.ops.object.select_all(action='DESELECT');m=bpy.data.meshes.new(name);m.from_pydata([(n,-e,z) for e,n,z in verts],[],faces);m.update();a=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(a);a.select_set(True);bpy.context.view_layer.objects.active=a
 for p in m.polygons:p.use_smooth='Terrain' in name
 mat=bpy.data.materials.new(name+'_Surface');mat.diffuse_color=(.25,.35,.18,1);m.materials.append(mat)
 bpy.ops.export_scene.gltf(filepath=str(O/(name+'.glb')),export_format='GLB',use_selection=True,export_yup=True,export_apply=True)
 report[name]={'vertices':len(verts),'faces':len(faces),'bounds_m':[[min(v[k] for v in verts),max(v[k] for v in verts)] for k in range(3)]}
for name,xs,ys,hole in [('V2TerrainCore',np.linspace(-150,150,121),np.linspace(-150,150,121),False),('V2TerrainRing',np.arange(-590,911,10),np.arange(-750,751,10),True)]:
 v=[(float(x),float(y),height(x,y)) for y in ys for x in xs];f=[];w=len(xs)
 for j in range(len(ys)-1):
  for i in range(w-1):
   if hole and -150<=xs[i] and xs[i+1]<=150 and -150<=ys[j] and ys[j+1]<=150:continue
   a=j*w+i;f.extend([(a,a+1,a+w+1),(a,a+w+1,a+w)])
 export(name,v,f)
sets={k:([],[]) for k in ['V2Roads','V2Sidewalks','V2Curbs']}
def ribbon(name,points,lo,hi,raise_z,depth):
 v,f=sets[name];start=len(v)
 for i,(e,n) in enumerate(points):
  p=points[max(0,i-1)];q=points[min(len(points)-1,i+1)];dx=q[0]-p[0];dy=q[1]-p[1];d=max(.001,math.hypot(dx,dy));nx=-dy/d;ny=dx/d
  for off in [lo,hi]:
   x=e+nx*off;y=n+ny*off;v.append((x,y,height(x,y)+raise_z))
 for i in range(len(points)-1):
  a=start+i*2;f.extend([(a,a+3,a+1),(a,a+2,a+3)])
 # solid vertical skirts along both sides
 for side in [0,1]:
  for i in range(len(points)-1):
   a=start+2*i+side;b=a+2;k=len(v);v.extend([(v[a][0],v[a][1],v[a][2]-depth),(v[b][0],v[b][1],v[b][2]-depth)]);f.append((a,b,k+1,k))
for r in L['streets']:
 pts=[]
 for a,b in zip(r['points'],r['points'][1:]):
  count=max(1,math.ceil(math.dist(a[:2],b[:2])/2))
  pts.extend([(a[0]+(b[0]-a[0])*t/count,a[1]+(b[1]-a[1])*t/count) for t in range(count)])
 pts.append(tuple(r['points'][-1][:2]));w=r['width_m']/2;ped=r['kind'] in ['footway','path','steps','pedestrian']
 ribbon('V2Sidewalks' if ped else 'V2Roads',pts,-w,w,.06,.12)
 if not ped:
  for side in [-1,1]:
   lo,hi=sorted([side*w,side*(w+1.5)]);ribbon('V2Sidewalks',pts,lo,hi,.20,.25)
   lo,hi=sorted([side*w,side*(w+.24)]);ribbon('V2Curbs',pts,lo,hi,.23,.30)
for name,(v,f) in sets.items():export(name,v,f)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'town-v2-terrain.blend'))
(O/'report.json').write_text(json.dumps(report,indent=2));print('V2_MESH_COMPLETE',json.dumps(report))
