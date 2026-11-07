from pathlib import Path
import json,math
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'Saved/TownV2/session-5';B=json.loads((R/'Saved/TownV2/session-4/apply.json').read_text());L=json.loads((R/'Design/TownV2/layout.json').read_text());im=Image.new('RGB',(1400,1400),'#dedacc');d=ImageDraw.Draw(im)
def pt(e,n):return ((e+100)*7,1200-(n+40)*7)
for r in L['streets']:d.line([pt(*p[:2]) for p in r['points']],fill='#9d9d99',width=round(max(r['width_m'],4.5)*7))
for i,b in enumerate(B['placements']):
 e,n,z=b['center_m'];w,dd=b['building_dimensions_m'];a=math.radians(b['yaw']);points=[pt(e+x*math.sin(a)+y*math.cos(a),n+x*math.cos(a)-y*math.sin(a)) for x,y in [(-w/2,-dd/2),(w/2,-dd/2),(w/2,dd/2),(-w/2,dd/2)]]
 d.polygon(points,fill='#b99779',outline='black',width=2);d.text(pt(e,n),str(i)+' '+b['building'][:4],fill='black',font_size=15)
for name,p,t in [('01',(-22,8),(50,12)),('02',(-26,17),(-24,50)),('03',(-45,41),(-65,66)),('05',(-7,-6),(110,95)),('07',(-30,20),(-52,61))]:
 d.line([pt(*p),pt(*t)],fill='red',width=2);d.ellipse([pt(p[0]-.5,p[1]+.5),pt(p[0]+.5,p[1]-.5)],fill='red');d.text(pt(p[0]+1,p[1]),name,fill='red',font_size=18)
for e in range(-100,101,10):d.text(pt(e,-38),str(e),fill='black',font_size=15)
for n in range(-30,131,10):d.text(pt(-99,n),str(n),fill='black',font_size=15)
d.line([pt(*p) for p in [[-30,10],[-34,19],[-38,30],[-43,39],[-48,48],[-50,60],[-56,70]]],fill='blue',width=4)
im.save(O/'before-plan.png')
