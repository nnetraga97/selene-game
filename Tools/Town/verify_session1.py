"""Artifact, source geometry and heightmap readback checks for the Session 1 checkpoint."""
import hashlib,json,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from geo import ROOT,load,clip_polygon,clip_line,area
B=ROOT/'Design/TownV2';O=ROOT/'Saved/TownV2/session-1'
l=json.loads((B/'layout.json').read_text());checks={};counts={}
for key in ['kona','hilo','haleiwa','sanur','kona-core']:
 j=json.loads((B/f'osm/{key}.json').read_text());x=ET.parse(B/f'osm/{key}.osm').getroot()
 ids={(e['type'],e['id']) for e in j['elements']};xmlids={(e.tag,int(e.attrib['id'])) for e in x if e.tag in ['node','way','relation']}
 assert ids==xmlids,(key,'JSON/XML entity mismatch')
 for ext in ['json','osm']:
  receipt=json.loads((B/f'osm/{key}.{ext}.receipt.json').read_text());assert hashlib.sha256((B/f'osm/{key}.{ext}').read_bytes()).hexdigest()==receipt['sha256']
 counts[key]=len(ids)
checks['five_raw_json_xml_pairs_and_hashes']=True
site,raw,nodes,ways=load(l['site']['key']);byid={e.get('osm_id',f"way/{e['id']}"):e for e in ways}
for lot in l['lots']:
 assert np.allclose(clip_polygon(byid[lot['id']]['xy']),lot['footprint']['outer'])
 assert len(lot['footprint']['outer'])>=4 and lot['footprint']['outer'][0]==lot['footprint']['outer'][-1]
 assert lot['area_m2']>0 and lot['base_z_m'] is not None
for road in l['streets']:
 assert road['width_m']>0 and len(road['points'])>=2 and all(p[2] is not None for p in road['points'])
checks['lots_match_source_and_elevations_attached']=True
checks['multipolygon_courtyard_preserved']=any(q['footprint']['holes'] for q in l['lots'])
z=np.load(B/'terrain/elevation-metres.npy');encoded=np.array(Image.open(B/'terrain/heightmap-ue.png'))
r16=np.fromfile(B/'terrain/heightmap-ue.r16',dtype='<u2').reshape(1009,1009)
assert np.array_equal(encoded,r16)
error=float(np.max(np.abs((encoded.T.astype(float)-32768)/128-z)))
assert error<=1/256+.00001 and np.isfinite(z).all()
m=json.loads((B/'terrain/metadata.json').read_text());assert m['missing_land_pixels']==0
assert len(list((B/'terrain').glob('*.tif')))==1
assert l['player_spawn']['point'][2] is not None
checks['png_r16_match_and_orientation_roundtrip']=True;checks['one_dem_tile_no_missing_land']=True
assert all(checks.values())
out={'status':'verified_session_1_data','checks':checks,'raw_element_counts':counts,'counts':{k:len(l[k]) for k in ['lots','streets','areas','trees','seawalls']},'max_height_roundtrip_error_m':error,'estimated_width_streets':sum('estimate' in r['width_source'] for r in l['streets']),'height_range_m':m['height_range_m'],'limitations':['Road widths lack OSM tags and are class estimates','Copernicus is a 30 m DSM, not surveyed bare earth','Plaza and synthetic seabed are explicit design adaptations','Unreal visual and runtime checks belong to Session 2']}
(O/'retry/verification.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
