#!/usr/bin/env python3
"""One approved Copernicus tile, local resampling, coastal treatment and blended pads.
No dependencies downloaded. Run with local_python.sh after choosing a site.
"""
import argparse,datetime,hashlib,json,math,pathlib,urllib.request
import numpy as np
from PIL import Image
from matplotlib.path import Path
from geo import ROOT,load,scales,ocean_mask,distance_poly,setup_plot
BASE=ROOT/'Design/TownV2'

def fetch_tile(site):
 lat=math.floor(site['lat']);lon=math.floor(site['lon'])
 name=f"Copernicus_DSM_COG_10_{'N' if lat>=0 else 'S'}{abs(lat):02d}_00_{'E' if lon>=0 else 'W'}{abs(lon):03d}_00_DEM"
 dest=BASE/'terrain'/f'{name}.tif';dest.parent.mkdir(exist_ok=True)
 url=f'https://copernicus-dem-30m.s3.amazonaws.com/{name}/{name}.tif'
 if not dest.exists():
  req=urllib.request.Request(url,headers={'User-Agent':'SeleneTownLayout/1.0 (game prototype)'})
  with urllib.request.urlopen(req,timeout=90) as r:
   data=r.read();headers=dict(r.headers)
  dest.write_bytes(data)
  dest.with_suffix('.receipt.json').write_text(json.dumps({'url':url,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'response_headers':headers},indent=2))
 return dest

def bilinear(a,col,row):
 x=np.clip(col,0,a.shape[1]-1.000001);y=np.clip(row,0,a.shape[0]-1.000001)
 xi=x.astype(int);yi=y.astype(int);u=x-xi;v=y-yi
 return (a[yi,xi]*(1-u)+a[yi,xi+1]*u)*(1-v)+(a[yi+1,xi]*(1-u)+a[yi+1,xi+1]*u)*v

def main():
 layout=json.loads((BASE/'layout.json').read_text());site=layout['site'];tile=fetch_tile(site)
 im=Image.open(tile);tags=dict(im.tag_v2);a=np.array(im,dtype=np.float32)
 pixel=tags[33550];tie=tags[33922];print('DEM',a.shape,pixel,tie,flush=True)
 # Sample on a 1009-point grid (16 x 63 quads), retaining geographic metres.
 N=1009;east=np.linspace(-590,910,N);north=np.linspace(-750,750,N);X,Y=np.meshgrid(east,north);sx,sy=scales(site['lat'])
 lon=site['lon']+X/sx;lat=site['lat']+Y/sy
 # Respect GTRasterTypeGeoKey: this Copernicus tile is PixelIsPoint.
 keys=tags[34735];raster_type=next((keys[i+3] for i in range(4,len(keys),4) if keys[i]==1025),1)
 offset=0 if raster_type==2 else .5
 col=(lon-tie[3])/pixel[0]-offset;row=(tie[4]-lat)/pixel[1]-offset
 missing=(col<0)|(col>a.shape[1]-1)|(row<0)|(row>a.shape[0]-1)
 source=bilinear(a,col,row)
 s,d,n,w=load(site['key']);coasts=[e['xy'] for e in w if e.get('tags',{}).get('natural')=='coastline']
 if not coasts:raise RuntimeError('No coastline: sea classification cannot be verified')
 sea,distance=ocean_mask(X,Y,coasts)
 if np.any(missing&~sea):raise RuntimeError('One tile does not cover all land in the crop')
 source[missing]=0
 # Gaussian sigma=9 m; mild compared with source 30 m spacing.
 z=source.copy();sigma=9/(1500/(N-1));radius=math.ceil(3*sigma);k=np.exp(-np.arange(-radius,radius+1)**2/(2*sigma*sigma));k/=k.sum()
 for axis in [0,1]:z=np.apply_along_axis(lambda t:np.convolve(np.pad(t,radius,mode='edge'),k,mode='valid'),axis,z)
 z[sea]=-np.minimum(8,distance[sea]*.20) # synthetic seabed, not measured bathymetry
 # Coastline is fixed at zero; smoothly restore the DSM over 12 m inland.
 f=np.clip(distance/12,0,1);f=f*f*(3-2*f)
 z[~sea]=np.maximum(.05,z[~sea])*f[~sea]
 before=z.copy();pad_records=[];interiors=[]
 def sample(x,y,grid=z):return float(bilinear(grid,np.array((x+590)/1500*(N-1)),np.array((y+750)/1500*(N-1))))
 targets=[(lot,lot['footprint']['outer'],'building') for lot in layout['lots']]
 targets += [(q,q['polygon'],'plaza') for q in layout['areas'] if q.get('kind')=='plaza']
 for obj,poly,kind in targets:
  inside=Path(poly).contains_points(np.column_stack([X.ravel(),Y.ravel()])).reshape(X.shape)&~sea
  if not np.any(inside):continue
  target=float(np.median(before[inside]));dist=distance_poly(X,Y,poly);t=np.clip(1-dist/7,0,1);blend=t*t*(3-2*t);blend[inside]=1;blend[sea]=0
  z[:]=z*(1-blend)+target*blend
  interiors.append((inside,target))
  obj['base_z_m']=round(target,3);pad_records.append({'id':obj['id'],'kind':kind,'target_z_m':target,'blend_m':7})
 # Restore each pad interior after overlapping blend skirts.
 for inside,target in interiors:z[inside]=target
 for road in layout['streets']:
  for p in road['points']:p[2]=round(sample(p[0],p[1]),3)
 for t in layout['trees']:t['point'][2]=round(sample(*t['point'][:2]),3)
 if 'player_spawn' in layout:layout['player_spawn']['point'][2]=round(sample(*layout['player_spawn']['point'][:2]),3)
 for q in layout['areas']:
  q['vertex_z_m']=[round(sample(x,y),3) for x,y in q['polygon']]
 if z.min()<-256 or z.max()>=256:raise RuntimeError('Terrain exceeds fixed encoding range')
 encoded=np.rint(32768+z*128).astype('<u2')
 out=BASE/'terrain';np.save(out/'elevation-metres.npy',z.astype(np.float32));np.save(out/'source-crop-metres.npy',source.astype(np.float32))
 Image.fromarray(np.flipud(encoded)).save(out/'heightmap-north-up.png')
 # UE mapping is X=north,Y=east. Rows advance UE Y, columns advance UE X.
 ue=encoded.T.copy();Image.fromarray(ue).save(out/'heightmap-ue.png');(out/'heightmap-ue.r16').write_bytes(ue.tobytes())
 meta={'source_tile':tile.name,'source_sha256':hashlib.sha256(tile.read_bytes()).hexdigest(),'source_geotiff_tags':{str(k):v for k,v in tags.items() if k in [33550,33922,34735,34737]},'bounds_m':[-590,-750,910,750],'crop_centre_offset_east_m':160,'crop_reason':'Shift 160 m east to retain 1.5 km coverage inside the single authorized tile; core remains surrounded by 590 m west and 910 m east backdrop','size':[N,N],'spacing_m':1500/(N-1),'vertical_datum':'EGM2008 orthometric metres','sea_level_m':0,'source_type':'Copernicus GLO-30 digital surface model including vegetation and structures; not surveyed bare earth','source_resolution_approx_m':30,'smoothing_sigma_m':9,'pad_blend_m':7,'shore_blend_m':12,'seabed':'synthetic depth min(8 m, distance to coast * 0.20), no bathymetric claim','missing_tile_pixels':int(missing.sum()),'missing_land_pixels':int((missing&~sea).sum()),'height_range_m':[float(z.min()),float(z.max())],'encoding':'uint16 = round(32768 + elevation_m * 128); little-endian r16','quantization_m':1/128,'ue_landscape':{'section_size_quads':63,'sections_per_component':1,'components':[16,16],'scale_xyz_cm':[150000/(N-1),150000/(N-1),100],'actor_location_cm':[-75000,-59000,0],'height_file':'heightmap-ue.png','orientation':'columns north increasing; rows east increasing; X=north,Y=east'},'pads':pad_records}
 (out/'metadata.json').write_text(json.dumps(meta,indent=2));layout['terrain'].update(meta);layout['terrain']['bounds']=meta['bounds_m'];(BASE/'layout.json').write_text(json.dumps(layout,indent=2))
 plt=setup_plot();fig,axs=plt.subplots(1,3,figsize=(17,6))
 for ax,data,title in [(axs[0],source,'Real Copernicus DSM / 30 m source'),(axs[1],z,'Prepared terrain / sea level 0 m'),(axs[2],z-before,'Blended building + plaza pads')]:
  art=ax.imshow(data,origin='lower',extent=[-590,910,-750,750],cmap='RdBu_r' if ax==axs[2] else 'terrain');fig.colorbar(art,ax=ax,shrink=.75,label='metres');ax.set_title(title);ax.set_xlabel('East (m)');ax.set_ylabel('North (m)');ax.add_patch(__import__('matplotlib').patches.Rectangle((-125,-125),250,250,fill=False,edgecolor='#d54d4c'))
 fig.suptitle('TownV2 — 1.5 km coastal backdrop / no vertical exaggeration',fontsize=17)
 fig.text(.5,.025,'Copernicus DEM © DLR e.V. 2010–2014 / Airbus Defence and Space GmbH 2014–2018 • coast: © OpenStreetMap contributors, ODbL',ha='center',fontsize=9)
 fig.tight_layout(rect=[0,.06,1,.95]);fig.savefig(ROOT/'Saved/TownV2/session-1/heightmap-preview.png',dpi=140);print(json.dumps({'range':meta['height_range_m'],'pads':len(pad_records),'missing_land':meta['missing_land_pixels']}),flush=True)
if __name__=='__main__':main()
