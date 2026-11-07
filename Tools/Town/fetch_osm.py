#!/usr/bin/env python3
"""Fetch approved Overpass extracts with explicit headers and polite pacing.
Fetch only approved Overpass data; preserve raw JSON/XML, queries and receipts.
No automatic retries. Inspect failure evidence before a new session.
"""
import argparse, datetime, hashlib, json, math, pathlib, urllib.parse, urllib.request, time
ROOT = pathlib.Path(__file__).resolve().parents[2]
SITES = {
 'kona': {'name':'Kailua-Kona | palace / church seafront','lat':19.63965,'lon':-155.99555},
 'kona-core': {'name':'Kailua-Kona | refined palace / church core','lat':19.6395,'lon':-155.9942},
 'hilo': {'name':'Hilo | bayfront / Kalakaua Park','lat':19.72525,'lon':-155.0860},
 'haleiwa': {'name':'Haleiwa | bridge / harbour edge','lat':21.59295,'lon':-158.1035},
 'sanur': {'name':'Sanur | Sindhu beach centre','lat':-8.68385,'lon':115.2652},
}
def fetch(key, site, half, endpoint, coast_only=False):
 dlat=half/110700; dlon=half/(111320*math.cos(math.radians(site['lat'])))
 bounds=[site['lat']-dlat,site['lon']-dlon,site['lat']+dlat,site['lon']+dlon]
 bbox=','.join(f'{v:.8f}' for v in bounds)
 if coast_only: selectors=f'way["natural"="coastline"]({bbox});'
 else:
  selectors=''.join(f'nwr["{k}"]({bbox});' for k in ['building','highway','landuse','leisure','amenity','shop','historic'])
  selectors += f'way["natural"="coastline"]({bbox});way["natural"="beach"]({bbox});node["natural"="tree"]({bbox});way["man_made"="seawall"]({bbox});way["barrier"="retaining_wall"]({bbox});'
 base=ROOT/'Design/TownV2/osm'; base.mkdir(parents=True,exist_ok=True)
 for fmt,ext in [('json','json'),('xml','osm')]:
  dest=base/f'{key}.{ext}'
  if dest.exists():
   print('EXISTS',dest,flush=True); continue
  query=f'[out:{fmt}][timeout:45];({selectors});(._;>;);out body;'
  (base/f'{key}.{fmt}.overpassql').write_text(query+'\n')
  req=urllib.request.Request(endpoint,data=urllib.parse.urlencode({'data':query}).encode(),headers={'User-Agent':'SeleneTownLayout/1.0 (game prototype)', 'Accept':'application/json'})
  time.sleep(10)
  with urllib.request.urlopen(req,timeout=70) as resp:
   data=resp.read(); headers=dict(resp.headers)
  if fmt=='json':
   parsed=json.loads(data)
   if 'remark' in parsed: raise RuntimeError(parsed['remark'])
  else:
   import xml.etree.ElementTree as ET
   parsed=ET.fromstring(data)
   if parsed.find('remark') is not None: raise RuntimeError(parsed.findtext('remark'))
  dest.write_bytes(data)
  receipt={'url':endpoint,'request_method':'POST','query_file':f'{key}.{fmt}.overpassql','retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bbox_s_w_n_e':bounds,'display_size_m':2*half,'centre':site,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'response_headers':headers}
  (base/f'{key}.{ext}.receipt.json').write_text(json.dumps(receipt,indent=2))
  print(key,ext,len(data),'bytes',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--site',choices=list(SITES)+['all'],default='all');p.add_argument('--endpoint',choices=['https://overpass-api.de/api/interpreter'],default='https://overpass-api.de/api/interpreter');p.add_argument('--coast-context',action='store_true');a=p.parse_args()
 (ROOT/'Design/TownV2/sites.json').write_text(json.dumps(SITES,indent=2))
 for key,s in SITES.items():
  if a.site==key or (a.site=='all' and key!='kona-core'):fetch(key+('-coast-context' if a.coast_context else ''),s,900 if a.coast_context else 150,a.endpoint,a.coast_context)
