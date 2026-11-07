from pathlib import Path
from PIL import Image,ImageDraw
import sys,json
R=Path(__file__).resolve().parents[2];O=R/'Saved/TownV2/session-6';phase=sys.argv[1]
all_files=sorted((O/phase).glob('*.png'));files=[p for p in all_files if int(p.name[:2])<=9];eye=[p for p in files if not p.name.startswith(('06_','08_'))]
for suffix,selected in [('eye-level',eye),('all-views',files)]:
 im=Image.new('RGB',(1280,55+400*((len(selected)+1)//2)),'#18212c');draw=ImageDraw.Draw(im);draw.text((18,17),'TOWN V2 / SESSION 6 / '+phase.upper()+' / 8 fixed views + lighthouse from seafront',fill='white',font_size=20)
 for i,p in enumerate(selected):
  shot=Image.open(p).convert('RGB');shot.thumbnail((640,360));x=i%2*640;y=i//2*400+55;im.paste(shot,(x,y));draw.text((x+12,y+369),p.stem,fill='white',font_size=16)
 path=O/(phase+'-'+suffix+'-sheet.jpg');im.save(path,quality=94);print(path)
if phase!='before':
 before=json.loads((O/'before/capture.json').read_text());after=json.loads((O/phase/'capture.json').read_text());assert before['cameras']==after['cameras'][:len(before['cameras'])];assert before['resolution']==after['resolution'];assert before['fov']==after['fov'];print('Camera position, target, FOV, resolution identical')
 selected=[p for p in files if p.name in [x.name for x in (O/'before').glob('*.png')]];im=Image.new('RGB',(1280,55+390*len(selected)),'#18212c');draw=ImageDraw.Draw(im);draw.text((18,17),'SESSION 6    BEFORE                                                  AFTER',fill='white',font_size=20)
 for i,p in enumerate(selected):
  for j,q in enumerate([O/'before'/p.name,p]):
   shot=Image.open(q).convert('RGB');shot.thumbnail((640,360));im.paste(shot,(640*j,55+390*i))
  draw.text((18,55+390*i+365),p.stem,fill='white',font_size=16)
 im.save(O/'before-after-comparison.jpg',quality=94)

if len(all_files)>len(files):
 selected=[p for p in all_files if int(p.name[:2])>9];im=Image.new('RGB',(1280,55+400*((len(selected)+1)//2)),'#18212c');draw=ImageDraw.Draw(im);draw.text((18,17),'SESSION 6 / SUPPLEMENTAL EYE-LEVEL VERIFICATION',fill='white',font_size=20)
 for i,p in enumerate(selected):
  shot=Image.open(p).convert('RGB');shot.thumbnail((640,360));x=i%2*640;y=i//2*400+55;im.paste(shot,(x,y));draw.text((x+12,y+369),p.stem,fill='white',font_size=16)
 im.save(O/(phase+'-supplemental-sheet.jpg'),quality=94)
