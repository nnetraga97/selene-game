import bpy,json,math,array
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'Saved/TownV2/session-5/meshes';O.mkdir(parents=True,exist_ok=True);D=json.loads((R/'Design/TownV2/session-5-design.json').read_text());z=array.array('f');z.frombytes((R/'Saved/TownV2/session-3/meshes/graded-elevation-ue.f32').read_bytes())
def raw(e,n):
 x=max(0,min(1007.999,(e+590)/1500*1008));y=max(0,min(1007.999,(n+750)/1500*1008));i=int(x);j=int(y);a=x-i;b=y-j
 return z[i*1009+j]*(1-a)*(1-b)+z[(i+1)*1009+j]*a*(1-b)+z[i*1009+j+1]*(1-a)*b+z[(i+1)*1009+j+1]*a*b
def h(e,n):
 x=math.floor((e+150)/2.5)*2.5-150;y=math.floor((n+150)/2.5)*2.5-150;a=(e-x)/2.5;b=(n-y)/2.5;z00=raw(x,y);z11=raw(x+2.5,y+2.5)
 return z00*(1-a)+raw(x+2.5,y)*(a-b)+z11*b if a>=b else z00*(1-b)+raw(x,y+2.5)*(b-a)+z11*a
sets={n:([],[]) for n in ['V5Gardens','V5GardenWalls','V5GardenCaps']}
def quad(name,pts):
 v,f=sets[name];i=len(v);v.extend(pts);f.append(tuple(range(i,i+len(pts))))
def wall(p,q):
 dx=q[0]-p[0];dy=q[1]-p[1];length=math.hypot(dx,dy);nx=-dy/length;ny=dx/length
 for i in range(math.ceil(length)):
  a=[p[0]+dx*i/math.ceil(length),p[1]+dy*i/math.ceil(length)];b=[p[0]+dx*(i+1)/math.ceil(length),p[1]+dy*(i+1)/math.ceil(length)]
  for name,w,lo,hi in [('V5GardenWalls',.30,.16,.83),('V5GardenCaps',.40,.83,.91)]:
   pts=[(a[0]-nx*w/2,a[1]-ny*w/2),(b[0]-nx*w/2,b[1]-ny*w/2),(b[0]+nx*w/2,b[1]+ny*w/2),(a[0]+nx*w/2,a[1]+ny*w/2)]
   quad(name,[(x,y,h(x,y)+hi) for x,y in pts])
   for t in range(4):
    x,y=pts[t];xx,yy=pts[(t+1)%4];quad(name,[(x,y,h(x,y)+lo),(xx,yy,h(xx,yy)+lo),(xx,yy,h(xx,yy)+hi),(x,y,h(x,y)+hi)])
for g in D['gardens']:
 x0,y0,x1,y1=g['rect'];xs=sorted(set([x0,x1]+[x for x in [i*1.25 for i in range(-120,121)] if x0<x<x1]));ys=sorted(set([y0,y1]+[y for y in [i*1.25 for i in range(-120,121)] if y0<y<y1]))
 for x,xx in zip(xs,xs[1:]):
  for y,yy in zip(ys,ys[1:]):
   quad('V5Gardens',[(a,b,h(a,b)+.27) for a,b in [(x,y),(xx,y),(xx,yy)]]);quad('V5Gardens',[(a,b,h(a,b)+.27) for a,b in [(x,y),(xx,yy),(x,yy)]])
 sides=[('south',(x0,y0),(x1,y0)),('east',(x1,y0),(x1,y1)),('north',(x1,y1),(x0,y1)),('west',(x0,y1),(x0,y0))]
 for side,a,b in sides:
  if side==g['gate']:
   length=math.dist(a,b);t=.5-1.2/length;tt=.5+1.2/length;wall(a,(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t));wall((a[0]+(b[0]-a[0])*tt,a[1]+(b[1]-a[1])*tt),b)
  else:wall(a,b)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for name,(v,f) in sets.items():
 bpy.ops.object.select_all(action='DESELECT');mesh=bpy.data.meshes.new(name);mesh.from_pydata([(n,-e,z) for e,n,z in v],[],f);mesh.update();a=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(a);a.select_set(True);bpy.context.view_layer.objects.active=a;mat=bpy.data.materials.new(name+'_Placeholder');mesh.materials.append(mat);bpy.ops.export_scene.gltf(filepath=str(O/(name+'.glb')),export_format='GLB',use_selection=True,export_yup=True,export_apply=True)
(O/'gardens.json').write_text(json.dumps({'gardens':D['gardens'],'area_m2':sum((g['rect'][2]-g['rect'][0])*(g['rect'][3]-g['rect'][1]) for g in D['gardens']),'meshes':{k:{'vertices':len(v),'faces':len(f)} for k,(v,f) in sets.items()}},indent=2));print('GARDENS_COMPLETE')
