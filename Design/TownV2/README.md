# TownV2 — verified Session 1 data checkpoint

Chosen site: **Kailua-Kona**, refined origin **19.63950, -155.99420**.
See [site decision](site-selection.md), [layout](layout.json),
[terrain encoding](terrain/metadata.json), and [source attribution](ATTRIBUTION.md).

`osm/` retains five raw JSON/XML pairs (four comparison windows plus the refined
Kona core), exact Overpass queries and SHA256 retrieval receipts. The new layout
has 31 polygon lots, 26 road/path spline records, eight areas including an explicit
29 × 20 m plaza adaptation, one mapped tree, and no mapped seawall. Courtyard
multipolygons are assembled with holes. Source tags and full footprints remain.

All 26 road widths are class estimates because the extracts contain no width tags.
These are not surveyed widths. The church, café, bakery and tool-shop lots carry
fictional hero replacement assignments; all other source geometry stays traceable.
No dedicated Tripo café mesh is installed; use a pack building for that role.

Terrain uses exactly one Copernicus GLO-30 tile, N19/W156, from the public AWS bucket.
The 1.5 km crop is shifted 160 m east to remain inside that tile. It uses a 9 m
Gaussian smoothing kernel, 7 m pad blends and a 12 m shore blend. Sea surface is
zero. Negative seabed depth is synthetic, not bathymetry. This is a 30 m surface
model including vegetation/buildings, not a surveyed bare-earth terrain.

1009 × 1009 heightmap: `heightmap-ue.png` or little-endian `heightmap-ue.r16`.
UE X=north, Y=east; landscape location=(-75000,-59000,0) cm,
scale=(148.80952381,148.80952381,100), 16 × 16 components, 63 quads each.
The PNG columns advance north and rows advance east. `heightmap-north-up.png` is
for GIS viewing, **not** the UE import orientation. UInt16 32768 means sea level;
one unit is 1/128 m. No vertical exaggeration.

Reproduce locally (no dependency downloads):

```sh
Tools/Town/local_python.sh Tools/Town/geo.py
Tools/Town/local_python.sh Tools/Town/osm_to_layout.py --site kona-core
Tools/Town/local_python.sh Tools/Town/adapt_kona.py
Tools/Town/local_python.sh Tools/Town/terrain.py
Tools/Town/local_python.sh Tools/Town/preview_layout.py
Tools/Town/local_python.sh Tools/Town/verify_session1.py
```

The terrain helper reuses the downloaded tile. The fetcher uses only
`overpass-api.de`, the exact required User-Agent/Accept headers, 10-second spacing,
and no automatic retry loop. Preview/verification evidence is in
`Saved/TownV2/session-1/`. Session 2 and its remaining checks are recorded in
[the progress log](../../docs/TOWN-V2-PROGRESS.md).
