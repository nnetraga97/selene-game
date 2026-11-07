from pathlib import Path
import json,math
R=Path(__file__).resolve().parents[2];O=R/'Saved/TownV2/session-5';old=json.loads((R/'Saved/TownV2/session-4/apply.json').read_text())['placements']
assert not (R/'Design/TownV2/session-5-design.json').exists(), 'Design already recorded; do not replay'
# Existing actors are transformed in place. All building scale is uniform.
changes=[(0,-18,-17,270),(4,28,3,180),(9,-72,72,315),(20,18,50,90),(23,-24.34,50,90),(24,-10,50,90)]
move=[]
for idx,e,n,yaw in changes:
 x=old[idx].copy();x.update(index=idx,new_center_m=[e,n],new_yaw=yaw,new_scale=x['scale']);move.append(x)
new=[{'label':'SouthCorner','building':'shop-bakery-corner','center_m':[2,-17],'scale':1.05,'yaw':270,'palette':'cream'}, {'label':'CafeNeighbour','building':'shop-bakery-corner','center_m':[4,50],'scale':1.05,'yaw':90,'palette':'sand'}, {'label':'ShopCorner','building':'shop-tool-repair','center_m':[-33,63],'scale':1.12,'yaw':135,'palette':'ivory'}, {'label':'ShopRow','building':'townhouse-terrace','center_m':[-46,76],'scale':1.128,'yaw':135,'palette':'coral'}, {'label':'LowerShop','building':'shop-tool-repair','center_m':[-58,39],'scale':1.12,'yaw':315,'palette':'cream'}]
gardens=[{'name':'CafeRear','rect':[-22,61,1,79],'gate':'south'}, {'name':'UpperCourt','rect':[5,63,28,82],'gate':'south'}, {'name':'ClockRear','rect':[40,-3,66,20],'gate':'west'}, {'name':'EastCourt','rect':[32,34,65,50],'gate':'west'}]
d={'source':'saved Session 4, targeted in-place Session 5','moves':move,'additions':new,'gardens':gardens,'scale_policy':'No whole-district enlargement. Existing central assets retain uniform scales; new bakery copies 1.05. Central doors and floors already substantial against 1.8 m pawn.','walk_route_unchanged':True}
(R/'Design/TownV2/session-5-design.json').write_text(json.dumps(d,indent=2));print('Design saved')
