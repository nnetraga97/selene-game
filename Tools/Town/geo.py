"""Small, dependency-light local ENU geometry helpers (metres, WGS84)."""
import json,math,pathlib
import numpy as np
from matplotlib.path import Path
ROOT=pathlib.Path(__file__).resolve().parents[2]
def scales(lat):
 p=math.radians(lat);a=6378137.;e2=6.69437999014e-3;d=math.sqrt(1-e2*math.sin(p)**2)
 return math.pi/180*a*math.cos(p)/d, math.pi/180*a*(1-e2)/d**3

def project(lon,lat,site):
 sx,sy=scales(site['lat']);return [(lon-site['lon'])*sx,(lat-site['lat'])*sy]

def load(key):
 site=json.loads((ROOT/'Design/TownV2/sites.json').read_text())[key]
 data=json.loads((ROOT/f'Design/TownV2/osm/{key}.json').read_text())
 nodes={e['id']:e for e in data['elements'] if e['type']=='node'}
 ways=[]
 for e in data['elements']:
  if e['type']=='way':
   e=dict(e);e['xy']=[project(nodes[i]['lon'],nodes[i]['lat'],site) for i in e['nodes'] if i in nodes];ways.append(e)
 # Assemble OSM multipolygons, preserving inner rings rather than filling courtyards.
 byid={w['id']:w for w in ways};assembled=[];used=set()
 for rel in data['elements']:
  if rel['type']!='relation' or rel.get('tags',{}).get('type')!='multipolygon':continue
  rings={}
  for role in ['outer','inner']:
   chains=[list(byid[m['ref']]['nodes']) for m in rel['members'] if m['type']=='way' and m.get('role','outer')==role]
   complete=[]
   while chains:
    chain=chains.pop(0)
    while chain[0]!=chain[-1]:
     match=next(((i,c) for i,c in enumerate(chains) if chain[-1] in [c[0],c[-1]]),None)
     if match is None:raise ValueError('Open multipolygon ring '+str(rel['id']))
     i,c=match;chains.pop(i)
     if c[-1]==chain[-1]:c=c[::-1]
     chain.extend(c[1:])
    complete.append([project(nodes[i]['lon'],nodes[i]['lat'],site) for i in chain])
   rings[role]=complete
  if not rings['outer']:raise ValueError('Missing multipolygon outer '+str(rel['id']))
  for i,poly in enumerate(rings['outer']):
   holes=[h for h in rings['inner'] if Path(poly).contains_point(h[0])]
   assembled.append({'id':rel['id'],'osm_id':f"relation/{rel['id']}"+(f'/{i}' if len(rings['outer'])>1 else ''),'tags':rel['tags'],'xy':poly,'holes':holes})
  used.update(m['ref'] for m in rel['members'] if m['type']=='way')
 ways=[w for w in ways if w['id'] not in used]+assembled
 return site,data,nodes,ways

def clip_polygon(poly,b=(-125,-125,125,125)):
 out=[list(p) for p in poly]
 if len(out)>1 and out[0]==out[-1]:out.pop()
 for axis,edge,sign in [(0,b[0],1),(0,b[2],-1),(1,b[1],1),(1,b[3],-1)]:
  inp=out;out=[]
  if not inp:break
  prev=inp[-1];inside0=sign*(prev[axis]-edge)>=0
  for cur in inp:
   inside1=sign*(cur[axis]-edge)>=0
   if inside0!=inside1:
    t=(edge-prev[axis])/(cur[axis]-prev[axis]);out.append([prev[i]+t*(cur[i]-prev[i]) for i in range(2)])
   if inside1:out.append(cur)
   prev=cur;inside0=inside1
 if len(out)>=3:out.append(out[0]);return out
 return []

def clip_line(points,b=(-125,-125,125,125)):
 parts=[];current=[]
 for a,z in zip(points,points[1:]):
  dx=z[0]-a[0];dy=z[1]-a[1];t0=0.;t1=1.;ok=True
  for p,q in [(-dx,a[0]-b[0]),(dx,b[2]-a[0]),(-dy,a[1]-b[1]),(dy,b[3]-a[1])]:
   if abs(p)<1e-12:
    if q<0:ok=False;break
   elif p<0:t0=max(t0,q/p)
   else:t1=min(t1,q/p)
  if t0>t1:ok=False
  if ok:
   u=[a[0]+t0*dx,a[1]+t0*dy];v=[a[0]+t1*dx,a[1]+t1*dy]
   if np.linalg.norm(np.array(u)-v)<1e-8:continue
   if current and np.linalg.norm(np.array(current[-1])-u)<1e-6:current.append(v)
   else:
    if current:parts.append(current)
    current=[u,v]
  elif current:parts.append(current);current=[]
 if current:parts.append(current)
 return parts

def area(poly):
 return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:])))/2

def distance_poly(X,Y,poly):
 best=np.full(X.shape,np.inf)
 for a,b in zip(poly,poly[1:]):
  dx=b[0]-a[0];dy=b[1]-a[1];dd=dx*dx+dy*dy
  if dd==0:continue
  t=np.clip(((X-a[0])*dx+(Y-a[1])*dy)/dd,0,1)
  best=np.minimum(best,np.hypot(X-a[0]-t*dx,Y-a[1]-t*dy))
 return best

def ocean_mask(X,Y,coasts):
 # OSM coastline direction has land on its left; classify by closest segment.
 best=np.full(X.shape,np.inf);sea=np.zeros(X.shape,dtype=bool)
 for poly in coasts:
  for a,b in zip(poly,poly[1:]):
   dx=b[0]-a[0];dy=b[1]-a[1];dd=dx*dx+dy*dy
   if dd==0:continue
   if max(a[0],b[0])<X.min()-2000 or min(a[0],b[0])>X.max()+2000 or max(a[1],b[1])<Y.min()-2000 or min(a[1],b[1])>Y.max()+2000:continue
   t=np.clip(((X-a[0])*dx+(Y-a[1])*dy)/dd,0,1)
   dist=(X-a[0]-t*dx)**2+(Y-a[1]-t*dy)**2
   closer=dist<best
   sea[closer]=(dx*(Y-a[1])-dy*(X-a[0])<0)[closer];best=np.minimum(best,dist)
 # A nearest-segment half-plane misclassifies concave bays at vertices.
 # Use the nearest horizontal ray crossing; direction keeps land on the left.
 ray_best=np.full(X.shape,np.inf);ray_sea=sea.copy()
 for poly in coasts:
  for a,b in zip(poly,poly[1:]):
   dy=b[1]-a[1]
   if abs(dy)<1e-12:continue
   cross=(Y>=min(a[1],b[1]))&(Y<max(a[1],b[1]))
   ix=a[0]+(Y-a[1])*(b[0]-a[0])/dy
   distance=np.abs(ix-X)
   use=cross&(distance<ray_best)
   ray_sea[use]=(((X>ix)&(dy>0))|((X<ix)&(dy<0)))[use]
   ray_best[use]=distance[use]
 return ray_sea,np.sqrt(best)

def setup_plot():
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'figure.facecolor':'#f7f5ef','axes.facecolor':'#f0eddf','axes.titleweight':'bold'})
 return plt

def raw_map(ax,key,half=150):
 from matplotlib.patches import Rectangle
 s,d,ns,ws=load(key);coasts=[e['xy'] for e in ws if e.get('tags',{}).get('natural')=='coastline']
 v=np.linspace(-half,half,240);X,Y=np.meshgrid(v,v)
 if coasts:
  sea,_=ocean_mask(X,Y,coasts);ax.imshow(sea,origin='lower',extent=[-half,half,-half,half],cmap=__import__('matplotlib').colors.ListedColormap(['#eeeadd','#a6ccd6']),vmin=0,vmax=1)
 counts={'buildings':0,'streets':0,'trees':0,'areas':0,'width_tagged':0}
 for e in ws:
  t=e.get('tags',{});p=e['xy'];cl=clip_polygon(p,(-half,-half,half,half)) if p and p[0]==p[-1] else []
  if cl and ('landuse' in t or 'leisure' in t):
   ax.fill(*np.array(cl).T,color='#aec5a4',alpha=.6,zorder=2);counts['areas']+=1
  if cl and 'building' in t:
   ax.fill(*np.array(cl).T,color='#e0b69d',edgecolor='#816b61',linewidth=.5,zorder=4);counts['buildings']+=1
   for h in e.get('holes',[]):ax.fill(*np.array(h).T,color='#eeeadd',edgecolor='#816b61',linewidth=.5,zorder=5)
  if 'highway' in t:
   parts=clip_line(p,(-half,-half,half,half))
   if parts:counts['streets']+=1
   if 'width' in t:counts['width_tagged']+=1
   for line in parts:
    path=t['highway'] in ['footway','path','steps','pedestrian'];ax.plot(*np.array(line).T,color='#b39e6a' if path else '#707676',linewidth=1.2 if path else 3,zorder=3)
  if t.get('natural')=='coastline':ax.plot(*np.array(p).T,color='#386d7a',lw=1.6,zorder=5)
 for n in ns.values():
  if n.get('tags',{}).get('natural')=='tree':
   x,y=project(n['lon'],n['lat'],s)
   if abs(x)<=half and abs(y)<=half:ax.scatter(x,y,s=10,color='#477a58',zorder=6);counts['trees']+=1
 ax.set(xlim=(-half,half),ylim=(-half,half),aspect='equal');ax.grid(alpha=.12);ax.set_xlabel('East (m)');ax.set_ylabel('North (m)')
 ax.add_patch(Rectangle((-125,-125),250,250,fill=False,ec='#bd5a48',lw=1.3,ls='--',zorder=10))
 ax.plot([-130,-80],[-138,-138],color='#173e49',lw=3);ax.text(-105,-133,'50 m',ha='center',fontsize=8)
 return counts
if __name__=='__main__':
 plt=setup_plot();fig,axs=plt.subplots(2,2,figsize=(13,13))
 stats={}
 for ax,key in zip(axs.flat,['kona','hilo','haleiwa','sanur']):
  stats[key]=raw_map(ax,key);s=json.loads((ROOT/'Design/TownV2/sites.json').read_text())[key]
  ax.set_title(s['name']+'\n'+str(stats[key]['buildings'])+' mapped footprints',fontsize=12)
 fig.suptitle('Town v2 — four real waterfront cores at the same scale',fontsize=18)
 fig.text(.5,.02,'300 × 300 m windows • dashed coral = 250 m design core • © OpenStreetMap contributors, ODbL',ha='center')
 fig.tight_layout(rect=[0,.04,1,.95]);fig.savefig(ROOT/'Saved/TownV2/session-1/site-comparison.png',dpi=150)
 (ROOT/'Design/TownV2/site-statistics.json').write_text(json.dumps(stats,indent=2));print(stats)
