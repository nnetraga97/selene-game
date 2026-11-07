# Selene environment asset list — draft

Based on 2026-11-05 prices and the 57-lot blockout: route pass covers the plaza south-west, 14 × 12 m café, 34 × 22 m clock hall, +12 m rail and hillside loop; other areas follow at mid detail. Accepted assets are excluded, except the requested streetlamp redo. Derive each neutral-lit, single-object Tripo input from its cited approved concept; do not upload scene images directly.

Area envelopes (m): plaza 140 × 110; commercial 220 × 180; hillside 160 × 140 (0–28 rise); mid-rise 150 × 120 (+4); industrial 170 × 120. Routes: R1 café 92 m; R2 street/transit/workshop/hills 1,411 m; R3 overlook 25 m.

## Tripo assets

Studio H3.1 means Best, Ultra, PBR, Remove Lighting; set polycount to the listed cap. H3.0 uses 2K. Heights are target Unreal placement heights; correct scale and pivots locally.

| ID | Asset | Where used | Pass | Tier / pool | Model + settings | Credits | Neutral single-object reference plan | Height | Max tris | Blender additions |
|---|---|---|---|---|---|---:|---|---:|---:|---|
| A01 | Clock tower crown/upper shaft | Clock hall roof, plaza landmark | Route | Hero / Studio | H3.1 4K | 55 | `town-style-study-01/04-town-square-night.png`; isolate tower top | 10 m | 120k | Clock face/hands and emissive; simple collision proxy |
| A02 | Café sign + awning assembly | Café north storefront, 14 × 12 m shell | Route | Mid / Studio | H3.0 2K | 30 | `town-style-study-01/02-main-street.png`; single façade-mounted set | 2.4 m | 30k | Emissive lettering plane; no collision |
| A03 | Plaza kiosk | Southwest plaza quarter | Route | Mid / Studio | H3.1 2K | 45 | `town-style-study-01/04-town-square-night.png`; derive a compact kiosk | 3.2 m | 55k | Menu emissive; collision proxy |
| A04 | Monorail train car | +12 m viaduct over plaza and depot | Route | Hero / Studio | H3.1 4K | 55 | `town-style-study-01/01-town-overview.png`; isolate one car, three-quarter view | 3.6 m | 150k | Glass and emissive strips; collision proxy; omit interior |
| A05 | Streetlamp redo | Plaza south-west approach | Route | Mid / Studio | H3.1 2K | 45 | `asset-reference-study-01/03-streetlamp-v2.png`; preserve approved lantern-head silhouette | 4.5 m | 60k | Separate emissive diffuser; collision proxy |
| A06 | Hillside house variant A | Residential A, stepped terraces; distant façades | Route | Mid / Studio | H3.0 2K | 30 | `town-style-study-01/03-residential-lane.png`; one complete two-storey house | 9 m | 45k | Collision proxy only; no walkable interior |
| A07 | Hillside house variant B | Residential A; repeated at +8/+13/+18/+23/+28 m | Route | Mid / Studio | H3.0 2K | 30 | Same approved lane image; distinct roof/window silhouette, same palette | 9 m | 45k | Collision proxy only; no walkable interior |
| A08 | Wind turbine | Hillside skyline/backdrop | Route | Mid / Studio | H3.1 2K | 45 | `environment-style-B-01/01-daylight-main-street.png`; derive one small distant turbine | 18 m | 70k | Optional simple pivot/rotation; collision proxy |
| A09 | Shop-front dressing assembly | Hero commercial façades along main street | Later | Mid / Studio | H3.1 2K | 45 | `town-style-study-01/02-main-street.png`; one façade-mounted sign/canopy ensemble | 4 m | 50k | Emissive sign plane; collision proxy |
| A10 | Small commercial background building | Commercial street, distant lot variant | Later | Mid / Studio | H3.0 2K | 30 | `town-style-study-01/02-main-street.png`; simplify to a closed 2–3-storey building | 12.5 m | 40k | Collision proxy; no interior |
| A11 | Industrial power unit | Workshop/depot dressing | Later | Mid / Studio | H3.1 2K | 45 | `environment-style-B-01/01-daylight-main-street.png` as style cue; derive one neutral machine | 2.2 m | 60k | Emissive readout; collision proxy |
| A12 | Industrial workbench | Enterable 20 × 14 m workshop | Later | Mid / Studio | H3.1 2K | 45 | Same approved environment image as style cue; isolate a service bench | 1.1 m | 35k | Collision proxy |
| A13 | Residential mailbox | Hillside house fronts | Later | Small / Studio | H3.0 2K | 30 | `town-style-study-01/03-residential-lane.png`; single street mailbox | 1.4 m | 15k | Collision proxy |
| A14 | Laundry rack | Residential terraces/courtyards | Later | Small / Studio | H3.0 2K | 30 | Same approved lane image; freestanding rack with folded fabric | 1.8 m | 20k | Collision proxy |
| A15 | Industrial crate | Workshop/depot clutter | Later | Small / CLI | CLI v3.1 textured; `face_limit=15k` | 30 | `environment-style-B-01/01-daylight-main-street.png` as style cue; derive one closed crate | 0.8 m | 15k | Collision proxy |

## Keep in Blender

| Asset group | Reason |
|---|---|
| Café, clock/transit-hall and workshop shells, doors, floors, stairs, partitions | Exact 14 × 12 m café (4.2 m clear), 34 × 22 m hall (7 m clear) and 20 × 14 m workshop (6 m clear); doors/routes must line up. Use Tripo accents on shells. |
| Paving, plaza curbs, terrace steps, street ramps | Continuous walkable surfaces must match blockout routes and capsule collision. |
| Viaduct spans, piers, railings and track | Long, straight, repeatable spans need exact 7 m width, +12 m deck and controlled pier exclusions. The train car remains Tripo. |
| New foliage/leaf-card canopies | Tripo foliage is solid; use Blender cards for leafy silhouettes. |

## Credit plan and order

| Batch | Order and scope | Assets | Studio | CLI |
|---|---|---:|---:|---:|
| 1 | Route slice: clock top, café sign/awning, kiosk, train car, streetlamp | 5 | 230 | 0 |
| 2 | Route slice: two hillside house variants and wind turbine backdrop | 3 | 105 | 0 |
| 3 | Later town: shop-front set, one background building, power unit, workbench | 4 | 165 | 0 |
| 4 | Later town: mailbox, laundry rack, crate | 3 | 60 | 30 |
| **Planned total** | 15 outputs; at most five per batch | **15** | **560 / 620** | **30 / 40** |
| **Held reserve** | About 10% overall; keep for retries | — | **60** | **10** |

Batch 1–2 deliver the route slice first; only then start the later-town batches. A 55-credit Studio retry fits the Studio reserve once. Texture regeneration (20) or retopology (40) is not included; fund either by dropping or deferring a later asset. Confirm the final Studio quote before each generation.

## Tripo building risks and mitigations

- **Scale/pivots:** outputs can be wrongly scaled. Apply transforms in Blender; align the base and compare doors to the 1.515 m player eye height.
- **Interiors/collision:** Tripo buildings are visual shells. Use Blender shells for the three interiors; give closed background assets simple collision or none.
- **Texture density:** reserve 4K for landmark/train; inspect 2K at camera distance. Build glazing, signs, clock faces and lights as Blender parts.
- **Consistency/fit:** Tripo makes one-offs; edges soften and glass/emissive smears. Limit full buildings to distant variants; share palette/materials and keep hero shells/modular trim in Blender.
