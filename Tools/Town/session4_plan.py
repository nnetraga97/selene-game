import json,math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
R=Path(__file__).resolve().parents[2];O=R/'Saved/TownV2/session-4';B=json.loads((R/'Design/TownV2/session-4-build.json').read_text());L=json.loads((R/'Design/TownV2/layout.json').read_text());fig,ax=plt.subplots(figsize=(12,12));colors={'townhouse-terrace':'#d9c7a0','apartment-curved':'#82a6ac','shop-bakery-corner':'#d69079','shop-tool-repair':'#c57963','workshop-garage':'#8d929a','clock-hall':'#efbc54'};codes={'townhouse-terrace':'T','apartment-curved':'A','shop-bakery-corner':'B','shop-tool-repair':'S','workshop-garage':'W','clock-hall':'C'}
ax.add_patch(Polygon(B['ground']['city_boundary'],facecolor='#e7e3d8',edgecolor='#c6c0ae',lw=1))
for road in L['streets']:
 points=road['points'];ax.plot([p[0] for p in points],[p[1] for p in points],color='#848989',lw=3 if road['kind'] not in ['footway','path'] else 1)
for area in L['areas']:
 if area['kind']=='plaza':ax.add_patch(Polygon(area['polygon'],facecolor='#f1dca8',edgecolor='#aa9c74'))
for i,b in enumerate(B['placements']):
 e,n,z=b['center_m'];w,d=b['building_dimensions_m'];a=math.radians(b['yaw']);points=[]
 for x,y in [(-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2)]:points.append((e+x*math.sin(a)+y*math.cos(a),n+x*math.cos(a)-y*math.sin(a)))
 ax.add_patch(Polygon(points,facecolor=colors[b['building']],edgecolor='#364144',lw=.9));ax.text(e,n,'CAFÉ' if b['hero']=='cafe' else codes[b['building']]+str(i+1),fontsize=8,ha='center',va='center')
for k,c in colors.items():ax.plot([],[],lw=8,color=c,label=k+' ('+str(B['counts'][k])+')')
ax.legend(loc='lower left',fontsize=9);ax.set(xlim=(-145,145),ylim=(-145,145),aspect='equal',xlabel='East (m)',ylabel='North (m)',title='TownV2 / Session 4 saved placement plan\nTripo buildings, paved district and source street alignment');ax.grid(alpha=.16);fig.tight_layout();fig.savefig(O/'building-placement-plan.png',dpi=150)
