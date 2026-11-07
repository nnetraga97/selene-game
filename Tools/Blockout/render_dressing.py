#!/usr/bin/env python3
"""Dependency-free PNG review map: plaza overview, cafe detail and keyed props."""
import argparse
import json
import math
from pathlib import Path
import struct
import zlib

from layout_core import ROOT, polygon, world_xy
from validate_dressing import BUFFER, asset_key, footprint, validate

# Compact 5x7 bitmap font keeps this runnable with stock python3.
FONT = dict(zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:/()+>= ',[
'01110 10001 10001 11111 10001 10001 10001','11110 10001 10001 11110 10001 10001 11110',
'01111 10000 10000 10000 10000 10000 01111','11110 10001 10001 10001 10001 10001 11110',
'11111 10000 10000 11110 10000 10000 11111','11111 10000 10000 11110 10000 10000 10000',
'01111 10000 10000 10111 10001 10001 01111','10001 10001 10001 11111 10001 10001 10001',
'11111 00100 00100 00100 00100 00100 11111','00111 00010 00010 00010 10010 10010 01100',
'10001 10010 10100 11000 10100 10010 10001','10000 10000 10000 10000 10000 10000 11111',
'10001 11011 10101 10101 10001 10001 10001','10001 11001 10101 10011 10001 10001 10001',
'01110 10001 10001 10001 10001 10001 01110','11110 10001 10001 11110 10000 10000 10000',
'01110 10001 10001 10001 10101 10010 01101','11110 10001 10001 11110 10100 10010 10001',
'01111 10000 10000 01110 00001 00001 11110','11111 00100 00100 00100 00100 00100 00100',
'10001 10001 10001 10001 10001 10001 01110','10001 10001 10001 10001 10001 01010 00100',
'10001 10001 10001 10101 10101 10101 01010','10001 10001 01010 00100 01010 10001 10001',
'10001 10001 01010 00100 00100 00100 00100','11111 00001 00010 00100 01000 10000 11111',
'01110 10001 10011 10101 11001 10001 01110','00100 01100 00100 00100 00100 00100 01110',
'01110 10001 00001 00010 00100 01000 11111','11110 00001 00001 01110 00001 00001 11110',
'00010 00110 01010 10010 11111 00010 00010','11111 10000 10000 11110 00001 00001 11110',
'01110 10000 10000 11110 10001 10001 01110','11111 00001 00010 00100 01000 01000 01000',
'01110 10001 10001 01110 10001 10001 01110','01110 10001 10001 01111 00001 00001 01110',
'00000 00000 00000 11111 00000 00000 00000','00000 00000 00000 00000 00000 00000 11111',
'00000 00000 00000 00000 00000 01100 01100','00000 01100 01100 00000 01100 01100 00000',
'00001 00010 00010 00100 01000 01000 10000','00010 00100 01000 01000 01000 00100 00010',
'01000 00100 00010 00010 00010 00100 01000','00000 00100 00100 11111 00100 00100 00000',
'10000 01000 00100 00010 00100 01000 10000','00000 11111 00000 11111 00000 00000 00000',
'00000 00000 00000 00000 00000 00000 00000']))
W,H=2000,1580
BG=(247,244,235); INK=(47,53,53)
COLORS={'plaza_sw':(100,135,85),'cafe_terrace':(189,116,55),'cafe_wall':(130,83,130),'cafe_interior':(56,128,157),'route_r1':(164,108,64)}
PIX=bytearray(bytes(BG)*(W*H))
CLIP=(0,0,W,H)


def dot(x,y,c):
    x,y=int(x),int(y)
    if 0<=x<W and 0<=y<H:
        i=(y*W+x)*3; PIX[i:i+3]=bytes(c)


def rect(x,y,w,h,c):
    for yy in range(max(CLIP[1],int(y)),min(CLIP[3],int(y+h))):
        start=max(CLIP[0],int(x)); end=min(CLIP[2],int(x+w))
        if end>start: PIX[(yy*W+start)*3:(yy*W+end)*3]=bytes(c)*(end-start)


def text(x,y,s,c=INK,scale=2):
    for char in s.upper():
        glyph=FONT.get(char,FONT[' ']).split()
        for row,bits in enumerate(glyph):
            for col,bit in enumerate(bits):
                if bit=='1':rect(x+col*scale,y+row*scale,scale,scale,c)
        x+=6*scale


def line(a,b,c,width=1):
    n=max(1,int(math.dist(a,b)*1.5))
    r=width/2
    for i in range(n+1):
        t=i/n; x=a[0]+(b[0]-a[0])*t; y=a[1]+(b[1]-a[1])*t
        rect(x-r,y-r,max(1,width),max(1,width),c)


def poly(points,fill,edge=INK):
    for y in range(max(0,int(min(p[1] for p in points))),min(H,int(max(p[1] for p in points))+1)):
        hits=[]
        for a,b in zip(points,points[1:]+points[:1]):
            if (a[1]<=y+.5<b[1]) or (b[1]<=y+.5<a[1]):
                hits.append(a[0]+(y+.5-a[1])*(b[0]-a[0])/(b[1]-a[1]))
        hits.sort()
        for a,b in zip(hits[::2],hits[1::2]):rect(math.ceil(a),y,max(0,math.ceil(b)-math.ceil(a)),1,fill)
    for a,b in zip(points,points[1:]+points[:1]):line(a,b,edge)


def panel(layout,data,origin,bounds,scale,detail=False):
    global CLIP
    x0,y0,x1,y1=bounds
    CLIP=(origin[0],origin[1],int(origin[0]+(x1-x0)*scale),int(origin[1]+(y1-y0)*scale))
    def xy(p):return (origin[0]+(p[0]-x0)*scale,origin[1]+(y1-p[1])*scale)
    def visible(p):return x0<=p[0]<=x1 and y0<=p[1]<=y1
    rect(*origin,(x1-x0)*scale,(y1-y0)*scale,(234,231,220))
    for v in range(math.ceil(x0/5)*5,int(x1)+1,5):line(xy([v,y0]),xy([v,y1]),(220,218,206))
    for v in range(math.ceil(y0/5)*5,int(y1)+1,5):line(xy([x0,v]),xy([x1,v]),(220,218,206))
    for slab in layout['slabs']:
        if visible(slab['center']):poly([xy(p) for p in polygon(slab)],(225,215,190),(175,166,146))
    for lot in layout['lots']:
        if not visible(lot['footprint']['center']):continue
        points=[xy(p) for p in polygon(lot['footprint'])]
        poly(points,(194,200,201))
        if 'interior' in lot:
            inner=dict(lot['footprint']); inner['size']=[v-2*lot['interior']['wall_thickness'] for v in inner['size']]
            poly([xy(p) for p in polygon(inner)],(243,238,224),(100,110,110))
            for prop in lot['interior']['props']:
                shape=dict(center=world_xy(lot['footprint'],*prop['center']),size=prop['size'][:2])
                poly([xy(p) for p in polygon(shape)],(196,183,158))
            w,d=lot['footprint']['size']
            for o in lot['interior']['openings']:
                if o['kind']=='door' and o['wall']=='north':
                    ends=[world_xy(lot['footprint'],o['offset']+v*o['width']/2,d/2) for v in (-1,1)]
                    line(*[xy(p) for p in ends],(255,255,255),max(3,.35*scale))
        if not detail:
            tx,ty=xy(lot['footprint']['center']);text(tx-50,ty-8,lot['id'],scale=1)
    route=next(r['points'] for r in layout['routes'] if r['id']=='R1')
    for a,b in zip(route,route[1:]):
        line(xy(a),xy(b),(240,199,207),2*BUFFER*scale)
        line(xy(a),xy(b),(177,49,84),max(2,scale*.12))
    for i,p in enumerate(data['placements'],1):
        if not visible(p['position']):continue
        if p['id']=='cafe_vending_glass':continue  # same transform as body
        c=COLORS[p['group']]
        poly([xy(v) for v in footprint(p)],c)
        x,y=xy(p['position'])
        if asset_key(p)=='street-tree':text(x-4,y-4,'T',scale=1)
        if detail or p['group'] in ('plaza_sw','route_r1'):
            # Flowers share planter footprint: list both numbers in the key.
            if not p['id'].startswith('hydrangea_'):text(x+4,y-11,str(i),scale=1 if not detail else 2)
    x,y=xy(layout['player_start']['position']);poly([(x,y-7),(x-6,y+6),(x+6,y+6)],INK)
    x,y=xy([x0+1,y0+.3 if detail else y0+2]);line((x,y),(x+5*scale,y),INK,3);text(x,y-20,'5 M',scale=1)
    x,y=xy([x1-3,y1-5]);line((x,y),(x,y-3*scale),INK,2);text(x-4,y-3*scale-14,'N',scale=1)
    CLIP=(0,0,W,H)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,default=ROOT/'Design/Blockout/dressing_map.png')
    args=ap.parse_args()
    layout=json.loads((ROOT/'Design/Blockout/layout.json').read_text())
    data=json.loads((ROOT/'Design/Blockout/dressing.json').read_text())
    errors,minimum=validate(data,layout)
    if errors:raise SystemExit('\n'.join(errors))
    text(40,26,'SELENE / ROUTE DRESSING',scale=4)
    text(40,70,'48 PROPS + 5 OPTIONAL BUILDING REPLACEMENTS / PLAN REVIEW',scale=2)
    panel(layout,data,(40,150),(-67,-42,67,63),8)
    text(40,115,'PLAZA / EAST RIGHT / NORTH UP / 5 M GRID',scale=2)
    text(1170,115,'CAFE / TERRACE + INTERIOR',scale=2)
    panel(layout,data,(1170,150),(-54,-37,-35,-16),33,True)
    text(1170,870,'R1: PINK = CAPSULE + 1 M BUFFER',scale=2)
    text(1170,902,f'MIN CAPSULE CLEARANCE: {minimum-.34:.2f} M',scale=2)
    text(1170,934,'NUMBERS MATCH THE KEY BELOW',scale=2)
    text(40,1020,'PLACEMENT KEY / FOOTPRINTS INCLUDE ROTATION AND SCALE',scale=2)
    for index,p in enumerate(data['placements']):
        col=index//16; row=index%16
        x=40+col*650; y=1060+row*25
        rect(x,y,12,12,COLORS[p['group']]);text(x+20,y,f"{index+1:02} {p['id']}",scale=2)
    text(40,1480,'BUILDINGS: CLOCK_HALL HEIGHT FIT / PLAZA_FRONT_00..03 FOOTPRINT FIT',scale=2)
    text(40,1510,'PENDING ASSETS: ENVELOPES ONLY. VERIFY FRONTS / CORNERS / BOWLS / WALLS IN UNREAL.',scale=2)
    raw=b''.join(b'\x00'+PIX[y*W*3:(y+1)*W*3] for y in range(H))
    def chunk(kind,payload):return struct.pack('!I',len(payload))+kind+payload+struct.pack('!I',zlib.crc32(kind+payload)&0xffffffff)
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',W,H,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b'')
    args.out.write_bytes(png);print(args.out.resolve())

if __name__=='__main__':main()
