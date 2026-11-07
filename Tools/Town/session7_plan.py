from pathlib import Path
from PIL import Image,ImageDraw
import json
R=Path(__file__).resolve().parents[2];O=R/'Saved/TownV2/session-7';B=json.loads((O/'audit-before.json').read_text());L=json.loads((R/'Design/TownV2/layout.json').read_text());P=json.loads((O/'placement-final.json').read_text());im=Image.new('RGB',(1400,1000),'#e2decd');d=ImageDraw.Draw(im)
def pt(e,n):return ((e+100)*3,800-(n+45)*3)
for c in L['coastline']:d.line([pt(*p[:2]) for p in c],fill='#218b9a',width=4)
for r in L['streets']:d.line([pt(*p[:2]) for p in r['points']],fill='#aaa9a1',width=round(max(r['width_m'],2)*3))
for a in B['actors']:
 if a['mesh'] and a['mesh'].startswith('/Game/Assets/') and any(s in a['mesh'] for s in ['townhouse-terrace','shop-bakery','shop-tool','apartment-curved','clock-hall','workshop-garage','seaside-','harbour-']):
  e,n=a['bounds_center'][1]/100,a['bounds_center'][0]/100;ew,nw=a['extent'][1]/100,a['extent'][0]/100;d.rectangle([pt(e-ew,n+nw),pt(e+ew,n-nw)],fill='#bdab91',outline='#81715e')
for c in P['connections']:d.line([pt(*c['start_m'][:2]),pt(*c['end_m'][:2])],fill='#b49b6c',width=8)
for b in P['placements']:
 pts=[pt(*p) for p in b['terrace']['corners_m']];d.polygon(pts,fill='#d97d57',outline='#492a29',width=2);e,n,z=b['center_m'];d.text(pt(e-5,n+2),b['actor'].replace('V7_',''),fill='#18212c',font_size=13)
route=[[-30,10],[-34,19],[-38,30],[-43,39],[-48,48],[-50,60],[-56,70]];d.line([pt(*p) for p in route],fill='#315fb0',width=4)
d.line([pt(-26,10),pt(-59.5,22)],fill='#c13751',width=3);d.text(pt(-65,30),'Lighthouse',fill='#a71d40',font_size=14)
d.rectangle((0,0,1400,55),fill='#18212c');d.text((16,15),'SESSION 7 | Inland city preview; six buildings, connected fronts, protected town core',fill='white',font_size=23)
d.text((20,935),'East right  |  North up  |  Blue: unchanged walk  |  Pink: plaza-to-lighthouse sightline',fill='#18212c',font_size=18);im.save(O/'placement-plan.png')
