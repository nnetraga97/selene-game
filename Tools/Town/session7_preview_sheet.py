from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'Saved/TownV2/session-7';im=Image.new('RGB',(1600,990),'#18212c');d=ImageDraw.Draw(im)
d.text((20,16),'TOWN V2 / SESSION 7 / INLAND CITY PREVIEW',fill='white',font_size=26)
items=[('11_city_cluster_eye','City block from eye level'),('12_city_skyline_from_plaza','City skyline from the plaza'),('13_city_cluster_aerial','Six-building cluster and approach'),('10_lighthouse_from_plaza','Preserved lighthouse sightline')]
for i,(stem,title) in enumerate(items):
 shot=Image.open(O/('city-framing' if stem.startswith('11_') else 'final')/(stem+'.png')).convert('RGB');shot.thumbnail((800,450));x=i%2*800;y=55+i//2*465;im.paste(shot,(x,y));d.rectangle((x,y+420,x+800,y+450),fill='#18212c');d.text((x+12,y+425),title,fill='white',font_size=18)
im.save(O/'city-preview-sheet.jpg',quality=94)
fronts=sorted((O/'final').glob('1[4-9]_front_*.png'));im=Image.new('RGB',(1600,1515),'#18212c');d=ImageDraw.Draw(im);d.text((20,16),'TOWN V2 / SIX CITY FRONTS / EYE LEVEL',fill='white',font_size=26)
for i,p in enumerate(fronts):
 shot=Image.open(p).convert('RGB');shot.thumbnail((800,450));x=i%2*800;y=55+i//2*485;im.paste(shot,(x,y));d.text((x+12,y+457),p.stem[9:].replace('-',' '),fill='white',font_size=21)
im.save(O/'final-fronts-sheet.jpg',quality=94)
