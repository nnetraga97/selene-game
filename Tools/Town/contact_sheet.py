"""Compose existing capture evidence, preserving full-resolution originals."""
from pathlib import Path
from PIL import Image,ImageDraw
import sys
root=Path(__file__).resolve().parents[2];phase=sys.argv[1];out=root/'Saved/TownV2/session-3'
if phase=='before':
 files=sorted((root/'Saved/Town/session-1/after-verified').glob('*.png'))[:8];title='BEFORE - prior Town fallback (different map/cameras; TownV2 was empty)'
else:
 files=[p for p in sorted((out/phase).glob('*.png')) if not p.name.startswith('06_')];title=phase.upper()+' - Kona TownV2 - scripted offscreen game captures'
w=1280;cellw=640;cellh=400;rows=(len(files)+1)//2
sheet=Image.new('RGB',(w,rows*cellh+55),'#18212c');d=ImageDraw.Draw(sheet);d.text((18,16),title,fill='white',font_size=19)
for i,f in enumerate(files):
 im=Image.open(f).convert('RGB');im.thumbnail((640,360));x=(i%2)*640;y=(i//2)*400+55;sheet.paste(im,(x,y));d.text((x+12,y+369),f.stem,fill='white',font_size=16)
path=out/(phase+'-eye-level-sheet.jpg');sheet.save(path,quality=94);print(path)
