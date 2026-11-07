#!/usr/bin/env python3
"""Convert an Overpass extract to TownV2 polygon lots and measured/tagged road splines.
Run via Tools/Town/local_python.sh; all output confined to new TownV2 folders.
Road widths without tags are explicit estimates, never represented as measurements.
"""
import argparse,hashlib,json,math,re
from geo import ROOT,load,project,clip_polygon,clip_line,area
FALLBACK_WIDTH={'primary':8.,'secondary':7.,'tertiary':6.5,'residential':5.5,'unclassified':5.5,'service':3.5,'living_street':4.,'pedestrian':4.,'footway':1.8,'path':1.5,'steps':1.5,'cycleway':2.5,'track':3.}
def metres(value):
 if value is None:return None
 m=re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\s*(m|ft|feet|\')?\s*$',str(value))
 if not m:return None
 return float(m[1])*(.3048 if m[2] in ['ft','feet',"'"] else 1)
def convert(key):
 site,raw,nodes,ways=load(key);lots=[];streets=[];areas=[];walls=[];trees=[];amenities=[];coasts=[];warnings=[]
 bounds=(-125,-125,125,125)
 for e in ways:
  tags=e.get('tags',{});points=e['xy'];oid=e.get("osm_id",f"way/{e['id']}");label=tags.get('name',tags.get('building',oid))
  poly=clip_polygon(points,bounds) if len(points)>3 and points[0]==points[-1] else []
  if 'building' in tags and poly and area(poly)>1:
   levels=metres(tags.get('building:levels'));height=metres(tags.get('height'))
   if height is not None:source='osm:height';storeys=levels or max(1,round(height/3.3))
   elif levels is not None:height=levels*3.3;source='osm:building:levels × assumed 3.3 m';storeys=levels
   else:storeys=3 if tags['building'] in ['apartments','commercial','hotel'] else 2;height=storeys*3.3;source='design fallback: 2–3 storeys, 3.3 m per storey'
   lots.append({'id':oid,'label':label,'source':{'osm':oid,'tags':tags},'footprint':{'type':'polygon','outer':poly,'holes':[clip_polygon(h,bounds) for h in e.get('holes',[]) if clip_polygon(h,bounds)]},'full_source_footprint':points,'area_m2':area(poly),'height_m':height,'height_source':source,'storeys':storeys,'clipped_at_core_edge':abs(area(poly)-area(points))>.01,'base_z_m':None,'hero':False})
  if 'highway' in tags and tags.get('area')!='yes':
   width=metres(tags.get('width'));width_source='osm:width'
   if width is None:
    width=metres(tags.get('est_width'));width_source='osm:est_width (mapper estimate)'
   if width is None:
    width=FALLBACK_WIDTH.get(tags['highway'],4.);width_source='class estimate: field verification required'
   for i,line in enumerate(clip_line(points,bounds)):
    streets.append({'id':oid+f'/{i}','label':tags.get('name',tags['highway']),'source':{'osm':oid,'tags':tags},'kind':tags['highway'],'points':[[x,y,None] for x,y in line],'width_m':width,'width_source':width_source,'spline_interpolation':'linear','surface':tags.get('surface','unknown'),'bridge':tags.get('bridge'),'layer':tags.get('layer','0')})
  if poly and 'building' not in tags and (any(k in tags for k in ['landuse','leisure']) or tags.get('highway')=='pedestrian' or tags.get('amenity')=='parking' or tags.get('natural')=='beach'):
   kind=tags.get('leisure',tags.get('landuse',tags.get('amenity',tags.get('natural','pedestrian'))))
   areas.append({'id':oid,'label':tags.get('name',kind),'kind':kind,'source':{'osm':oid,'tags':tags},'polygon':poly,'origin':'osm'})
  if tags.get('natural')=='coastline':coasts.extend(clip_line(points,bounds))
  if tags.get('man_made')=='seawall' or tags.get('barrier')=='retaining_wall':
   for i,line in enumerate(clip_line(points,bounds)):walls.append({'id':oid+f'/{i}','kind':tags.get('man_made',tags.get('barrier')),'points':line,'source':{'osm':oid,'tags':tags}})
 for n in nodes.values():
  t=n.get('tags',{});xy=project(n['lon'],n['lat'],site)
  if abs(xy[0])>125 or abs(xy[1])>125:continue
  if t.get('natural')=='tree':trees.append({'id':f"node/{n['id']}",'point':xy+[None],'source_tags':t})
  if any(k in t for k in ['amenity','shop','historic','tourism']):amenities.append({'id':f"node/{n['id']}",'point':xy,'tags':t})
 for lot in lots:
  lot['area_m2']-=sum(area(h) for h in lot['footprint']['holes'])
 out={'schema_version':'town-v2.1','name':'Selene TownV2 — '+site['name'],'units':'metres','axes':'east,north,up','site':{'key':key,**site},'georeference':{'datum':'WGS84','projection':'local tangent approximation using WGS84 meridional and prime-vertical radii at origin','origin_lon_lat':[site['lon'],site['lat']],'vertical_datum':'EGM2008 orthometric metres from Copernicus DSM; sea level zero','unreal_mapping':'UE cm = (100*north, 100*east, 100*up)'},'core_bounds':list(bounds),'source':{'osm_file':f'osm/{key}.json','sha256':hashlib.sha256((ROOT/f'Design/TownV2/osm/{key}.json').read_bytes()).hexdigest(),'osm_timestamp':raw.get('osm3s',{}).get('timestamp_osm_base'),'attribution':'© OpenStreetMap contributors, ODbL'},'lots':lots,'streets':streets,'areas':areas,'seawalls':walls,'trees':trees,'amenities':amenities,'coastline':coasts,'design_adaptations':[],'terrain':{'bounds':[-750,-750,750,750],'sea_level_m':0},'warnings':warnings}
 if warnings: raise RuntimeError('Multipolygon relations need explicit assembly before conversion: '+str(warnings))
 dest=ROOT/'Design/TownV2/layout.json';dest.write_text(json.dumps(out,indent=2));print({k:len(out[k]) for k in ['lots','streets','areas','seawalls','trees','amenities','warnings']})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--site',default='kona-core');convert(p.parse_args().site)
