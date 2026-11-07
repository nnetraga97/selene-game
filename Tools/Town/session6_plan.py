from pathlib import Path
from PIL import Image,ImageDraw
import json,math
R=Path(__file__).resolve().parents[2];O=R/'Saved/TownV2/session-6';B=json.loads((O/'audit-before.json').read_text());L=json.loads((R/'Design/TownV2/layout.json').read_text());P=json.loads((O/'apply.json').read_text());im=Image.new('RGB',(1300,1250),'#e2decd');d=ImageDraw.Draw(im)
def pt(e,n):return ((e+110)*8,1100-(n+30)*8)
for c in L['coastline']:d.line([pt(*p[:2]) for p in c],fill='#218b9a',width=5)
for r in L['streets']:d.line([pt(*p[:2]) for p in r['points']],fill='#a4a39e',width=round(max(r['width_m'],4.5)*8))
for b in B['actors']:
 if b['mesh'] and '/Game/Assets/' in b['mesh'] and any(s in b['mesh'] for s in ['townhouse-terrace','shop-bakery','shop-tool','apartment-curved','clock-hall','workshop-garage']) and b['label'] not in P['removed']:
  e,n=b['bounds_center'][1]/100,b['bounds_center'][0]/100;ew,nw=b['extent'][1]/100,b['extent'][0]/100;d.rectangle([pt(e-ew,n+nw),pt(e+ew,n-nw)],fill='#bdab91',outline='#81715e')
for b in P['placements']:
 if b['actor']=='V6_Lighthouse' and (O/'sightline-correction.json').exists():
  e,n,_=b['center_m'];b['terrace']['corners_m']=[[e-(pn-n),n+(pe-e)] for pe,pn in b['terrace']['corners_m']]
 pts=[pt(*p) for p in b['terrace']['corners_m']];d.polygon(pts,fill='#d97d57',outline='#492a29',width=3);e,n,z=b['center_m'];d.text(pt(e-5,n+1),b['actor'].replace('V6_',''),fill='#18212c',font_size=20)
route=[[-30,10],[-34,19],[-38,30],[-43,39],[-48,48],[-50,60],[-56,70]];d.line([pt(*p) for p in route],fill='#315fb0',width=4)
for label,p,t in [('09',(-75,2),(-65,27)),('Plaza lighthouse',(-26,10),(-59.5,22)),('Shop lighthouse',(-43,39),(-59.5,22))]:
 d.line([pt(*p),pt(*t)],fill='#c13751',width=2);d.text(pt(p[0],p[1]),label,fill='#a71d40',font_size=15)
d.rectangle((0,0,1300,50),fill='#18212c');d.text((16,13),'SESSION 6 | New seaside buildings, real shoreline and unchanged grounded route',fill='white',font_size=21)
im.save(O/'placement-plan.png')
