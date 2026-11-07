"""Explicit game-design choices layered on top of unchanged OSM geometry."""
import json
from geo import ROOT,area
p=ROOT/'Design/TownV2/layout.json';l=json.loads(p.read_text())
assert l['site']['key']=='kona-core'
heroes={'way/455896316':'clock-hall','way/1296717081':'cafe','way/663900821':'bakery','way/1296717082':'tool-shop'}
for q in l['lots']:
 q['hero']=heroes.get(q['id'],False)
 q['placement_policy']='backdrop_partial_lot' if q['clipped_at_core_edge'] else 'fit_owned_building_to_footprint'
poly=[[-37,0],[-8,0],[-8,20],[-37,20],[-37,0]]
l['areas']=[q for q in l['areas'] if q['id']!='design/plaza']
l['areas'].append({'id':'design/plaza','label':'Palace forecourt plaza — game adaptation','kind':'plaza','polygon':poly,'area_m2':area(poly),'origin':'design adaptation','base_z_m':None,'source':{'osm_context':['way/198653703','way/455896316'],'note':'Unmapped open ground north of palace; not represented as a real OSM public square'}})
l['design_adaptations']=[{'id':'plaza','description':'29 × 20 m pedestrian plaza on open ground north of palace, preserving road and building geometry. No real-world plaza claim.','polygon':poly},{'id':'hero-replacements','description':'Replace selected footprint occupants with Selene fictional buildings; retain source IDs and full footprints.','lots':heroes}]
l['player_spawn']={'point':[-20,10,None],'eye_height_m':1.65,'note':'Inside adapted plaza; ground elevation attached by terrain tool.'}
p.write_text(json.dumps(l,indent=2));print('Plaza and four hero plots assigned')
