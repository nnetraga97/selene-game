"""Render converted geometry beside its OSM source, with explicit adaptations."""
import json,numpy as np
from matplotlib.patches import Polygon,Rectangle
from geo import ROOT,raw_map,setup_plot,ocean_mask,load

def draw(ax,layout):
 s,d,n,w=load(layout['site']['key']);v=np.linspace(-125,125,260);X,Y=np.meshgrid(v,v)
 coast=[e['xy'] for e in w if e.get('tags',{}).get('natural')=='coastline']
 sea,_=ocean_mask(X,Y,coast)
 ax.imshow(sea,origin='lower',extent=[-125,125,-125,125],cmap=__import__('matplotlib').colors.ListedColormap(['#eeeadd','#a6ccd6']))
 for a in layout['areas']:
  ax.add_patch(Polygon(a['polygon'],facecolor='#e6c87e' if a['kind']=='plaza' else '#a9bfa2',alpha=.55,edgecolor='#977a46' if a['kind']=='plaza' else 'none'))
  if a['kind']=='plaza':
   c=np.mean(a['polygon'][:-1],axis=0);ax.text(*c,'PLAZA\n(design adaptation)',ha='center',va='center',fontsize=7,zorder=10)
 for r in layout['streets']:
  p=np.array(r['points'],dtype=float);ped=r['kind'] in ['footway','pedestrian','path','steps']
  # Map a metre width to figure points after axis layout is fixed.
  width=r['width_m']/250*ax.get_window_extent().width*72/ax.figure.dpi
  ax.plot(p[:,0],p[:,1],lw=width,color='#ac9c75' if ped else '#7b8383',zorder=3,solid_capstyle='round')
 for l in layout['lots']:
  hero=l.get('hero');ax.add_patch(Polygon(l['footprint']['outer'],facecolor='#da7964' if hero else '#e2b69a',edgecolor='#80695e',lw=.7,zorder=5))
  if hero:
   c=np.mean(l['footprint']['outer'][:-1],axis=0);ax.text(*c,hero,ha='center',va='center',fontsize=7,zorder=7)
 for t in layout['trees']:ax.scatter(*t['point'][:2],c='#477955',s=15,zorder=7)
 for c in layout['coastline']:ax.plot(*np.array(c).T,c='#386d7a',lw=1.5,zorder=6)
 ax.set(xlim=(-125,125),ylim=(-125,125),aspect='equal',xlabel='East (m)',ylabel='North (m)');ax.grid(alpha=.15)

if __name__=='__main__':
 l=json.loads((ROOT/'Design/TownV2/layout.json').read_text());plt=setup_plot();fig,axs=plt.subplots(1,2,figsize=(15,8));fig.subplots_adjust(bottom=.12,top=.85,wspace=.22)
 raw_map(axs[0],l['site']['key'],125);axs[0].set_title('OSM source geometry / 250 × 250 m')
 draw(axs[1],l);axs[1].set_title('TownV2 conversion / same origin and scale')
 fig.suptitle('Kailua-Kona — compact palace / church / waterfront core',fontsize=18)
 fig.text(.5,.045,'© OpenStreetMap contributors, ODbL • coral = hero lots • gold = adapted plaza • untagged widths are estimates',ha='center',fontsize=10)
 fig.savefig(ROOT/'Saved/TownV2/session-1/layout-preview.png',dpi=150)
