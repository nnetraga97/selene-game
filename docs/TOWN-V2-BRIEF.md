# Town v2: a tight seaside plaza core built from real map data (Astra, xhigh, bounded sessions)

## User decisions (2026-11-06)

- **"Tighten the core."** Replace the 480 × 400 m invented layout with a dense core of about **250 × 250 m** around one plaza. Everything outside it becomes backdrop.
- **"Our design layout is not working."** Base the layout on a **real seaside place known for its view, like Bali or Hawaii**, using **OpenStreetMap** data (approved). Not Google Maps: its terms forbid deriving data from its imagery.
- **"Skip the Blender step."** Use placeholder assets the user owns on Fab: **FANTASTIC Village Pack** and **Stylized Medieval City** (approved), plus our existing Tripo buildings and props.
- **No spending:** no purchases and no paid generation.
- **Focus on the plaza district.** Make one district excellent before anything else.

Read `docs/research/town-quality.md`, `docs/TOWN-PROGRESS.md` (session 1) and the style concepts in `concepts/` first.

Each session is killed at **30 minutes**. Stop at a verified checkpoint and append to `docs/TOWN-V2-PROGRESS.md` (create it):
- what is done;
- before and after sheets;
- the exact next step.

## Session 1: site, layout, terrain

Do this part first. Most of it doesn't need Unreal, so it can run while the user plays.

1. **Pick the site.**
   - The default candidate is **Kailua-Kona, Hawaiʻi**:
     - the Aliʻi Drive seafront;
     - a church steeple (a natural clock-tower landmark) and a historic palace on the water;
     - a dense shopfront strip;
     - green volcanic slopes rising behind the town, which give the view.
   - Compare it quickly with 2–3 alternatives: **Hilo bayfront**, **Haleʻiwa** (North Shore), and a Bali seaside centre such as **Sanur**.
   - For each, fetch a ~300 × 300 m OpenStreetMap extract with the Overpass API: buildings, highways and footways, landuse and leisure areas, coastline, amenities, trees.
   - Render a quick top-down map of each, and pick the one with the best plaza, streets and sea view at our scale.
   - Record why. Prefer Kona unless another is clearly better.
   - Keep the raw `.osm` and JSON in `Design/TownV2/osm/`, and keep the OSM attribution text ("© OpenStreetMap contributors, ODbL") in `Design/TownV2/ATTRIBUTION.md`.
2. **Terrain.**
   - Fetch real elevation for the chosen site from a free public source. The Copernicus GLO-30 DEM is on the public AWS open-data bucket (`s3://copernicus-dem-30m`, anonymous); one 1° tile is enough.
   - Crop it to about 1.5 × 1.5 km around the core, so the ring outside the core forms the backdrop slope.
   - Make a 16-bit heightmap. Smooth it lightly, because 30 m data is coarse. Flatten building pads and the plaza in a way that blends into the slope; no hard engineered pads.
   - Keep the shoreline and sea level real: sea at Z=0, using the existing ocean or water if there is one, otherwise a simple water plane.
   - Note the vertical scale you used and why.
3. **Layout conversion.**
   - Write `Tools/Town/osm_to_layout.py` to convert the chosen extract into a new `Design/TownV2/layout.json`:
     - building footprints become lots, with height from OSM tags if present, otherwise 2–3 storeys;
     - streets become road splines with real widths;
     - plazas, parks and seawalls become slabs or areas;
     - street trees become points.
   - Validate it, rendering a top-down map, and compare it visually with an OSM render.
   - Keep `Design/Blockout/` (the old layout) untouched.
4. **Checkpoint.** Put the top-down site comparison, the chosen layout map and a heightmap preview in `Saved/TownV2/session-1/`, then propose session 2.

## Session 2 onward: build it in Unreal, plaza district first

- **Fab packs.** Check whether the user has added the packs to the project; they appear under `Content/`. FANTASTIC Village supports UE 5.8. Stylized Medieval City lists only up to 5.4, so it may need migrating, which is the user's step.
  - If a pack is missing, report it and continue with what's there.
  - **Never** download or buy anything from Fab yourself.
- **New map:** `/Game/Selene/Maps/TownV2`, a new map, with `Town` kept as a fallback.
  - A Landscape from the heightmap, with an auto material: grass on flats, rock or soil on slopes, sand at the shore.
  - Landscape or road splines for the streets with real widths, plus curbs and sidewalks.
  - The sea, and a backdrop of distant hills.
- **Placement:**
  - Each building footprint gets the best-fitting building from FANTASTIC Village or Stylized Medieval City, chosen by footprint size and use (shop, house, civic).
  - Our Tripo buildings go on the hero plots: `clock-hall` on the landmark, the café on the plaza corner, the bakery and tool shop on the shop strip.
  - Use **PCG** for street furniture along road splines (lamps, benches, bins and planters at a set spacing), trees and grass in green areas, and clutter at storefronts.
  - Hand-place only the hero spots.
  - **Tropical feel:** palms and lush planting where possible. If the packs have no palms, note it as a gap; don't download anything.
- **Recolour toward our palette** (cream and ivory walls, petrol trim, coral accents) with material instances, where the packs allow it.
- **The player spawn and the camera routes** go in the new plaza. Advanced movement must still work (MovementTest is separate).
- **Captures:** reuse session 1's fixed eye-level capture tool, with new viewpoints for the new map: plaza, shop street, seafront, a view toward the hills and an aerial. Do a style-B light pass, and record indicative fps.

## Rules

- **Unreal launches.** Guard every Selene launch:
  1. Run `pgrep -f "UnrealEditor.*Selene.uproject"`. If an instance is running, **the user may be playing: never kill it.** Wait up to 15 minutes, then stop and report.
  2. Take the lock with `until mkdir /tmp/selene-unreal.lock 2>/dev/null; do sleep 15; done`, and `rmdir` it afterwards, including on failure.
  3. Wrap the run in `perl -e 'alarm N; exec @ARGV'`.
- **Downloads allowed this task:** OpenStreetMap through the Overpass API, and the one Copernicus DEM tile. Nothing else: no Fab, no other assets, no Google data.
- **Files you may touch:**
  - `Design/TownV2/**`
  - `Tools/Town/**`
  - `Tools/Unreal/town_v2_*.py` and the existing `town_run.sh` capture helper (extend it carefully)
  - `Content/Selene/Maps/TownV2*` and its external actors
  - `Content/Selene/Environment/**`
  - `Content/Selene/Materials/Ground/**`
  - instances or children of Fab pack materials, under `Content/Selene/Environment/FabTints/`
  - `docs/TOWN-V2-PROGRESS.md`
  - `Saved/TownV2/**`
- **Never:**
  - edit `Config/DefaultEngine.ini` or `Source/**`;
  - edit `Config/DefaultGame.ini`, except to switch the default or startup map to TownV2 **at the end of a verified session**, keeping the old value in the progress doc;
  - modify Fab pack assets in place, our `/Game/Assets/*` assets, or characters;
  - commit, use paid services, or buy anything.
- **Failure rule:** one fix per distinct, diagnosed failure. Clear script errors are normal work. Stop and report when a failure repeats or can't be diagnosed.
- **Judge by eye-level captures,** not invented numeric gates.
- **Final reply:** the site chosen and why (with the comparison image); the layout and heightmap previews; and, once Unreal work starts, before and after sheets, what was placed from which pack, the gaps (palms, missing packs), the fps note and the next session.

---

## Session 1 retry: diagnosis from Claude (2026-11-06)

The first attempt was blocked because Overpass "timed out".

**Cause:** `overpass-api.de` returns **HTTP 406 to requests without a User-Agent header**. The Python default and plain curl were refused; the other two public mirrors are slow or down.

**Verified fix:** Claude ran this and got HTTP 200 with 145 elements for the Kona core, 44 of them buildings:
```
curl -A "SeleneTownLayout/1.0 (game prototype)" -H "Accept: application/json" --data-urlencode 'data=[out:json][timeout:50];(way["building"](19.6370,-155.9990,19.6420,-155.9945);way["highway"](19.6370,-155.9990,19.6420,-155.9945););out geom;' https://overpass-api.de/api/interpreter
```

**How to query:**
- Always send that User-Agent (no personal data in it) and `Accept: application/json`.
- Use only `overpass-api.de`.
- Keep the queries small: one bbox per site, and space the requests at least 10 seconds apart.
- A saved copy is in Claude's scratchpad, but fetch your own to keep provenance.

**Scope:** this retry may also run Session 2, now that the user has closed Unreal.
- The FANTASTIC Village Pack is in `Content/Fantastic_Village_Pack` (642 assets, no palms).
- Stylized Medieval City is **not** available: it isn't compatible with 5.8.

Finish Session 1 first, and verify it, before starting Unreal work.

---

## Session 3: approach change from Claude (2026-11-06)

Session 2 stopped because it drove the Unreal editor UI with computer use (Landscape mode, clicks and keys), and those controls didn't respond.

**Don't drive the editor UI at all.** No computer use, no clicking. Everything runs headless (`UnrealEditor-Cmd -run=pythonscript`) or as scripted `-game` captures.

**Terrain:** build it as **meshes, not a Landscape actor**. This is the same proven route the original blockout used (`Tools/Blender/terrain_from_layout.py`, headless Blender, then glTF import with unit scale).
- Generate the terrain from `Design/TownV2` heightmap data in headless Blender:
  - a ~1.5 km ring at coarse resolution (backdrop slopes);
  - a ~300 m core at fine resolution (2–3 m grid), with the building pads and plaza flattened and blended.
- Give it a **world-aligned slope material**: grass on flats, rock or soil on slopes, sand near sea level. Build it in `Content/Selene/Materials/Ground/` from textures we already have, or ones in `Fantastic_Village_Pack`.
- Nanite on the terrain meshes is fine.

**Other pieces:**
- **Roads:** spline meshes or simple extruded road strips from `layout.json`, with curbs.
- **Sea:** a water plane at Z=0 with a simple stylized water material. The Village Pack has water materials; reuse them through a material instance.

**The order stays the same:** terrain, then roads, the sea and the backdrop, then the **plaza district** buildings (Village Pack buildings plus our Tripo hero buildings on the hero lots from `layout.json`). Then PCG or scripted scatter, a palette tint, a style-B light pass, a player start in the plaza, and eye-level captures with indicative fps.

Load the existing empty `TownV2` map; don't recreate it. Stop at a verified checkpoint by about 30 minutes.

---

## Session 4: buildings and ground only (user decision, 2026-11-06)

Session 3 built `TownV2` headless. Captures: `Saved/TownV2/session-3/after-graded-eye-level-sheet.jpg`. The review found two problems for this session:
1. **Style clash.** The FANTASTIC Village storybook-medieval cottages (steep green shingle roofs, chimneys, pines) clash with our cream/petrol/coral Tripo buildings and with a seaside town.
2. **Too much open grass.** Buildings sit on lawn, and the roads read as thin paths.

**Scope of this session: only buildings and ground.** No seafront, palms or backdrop work yet.

### Buildings
- Put **our own Tripo buildings on most lots**: every building asset under `/Game/Assets/*`, including:
  - `shop-bakery-corner`, `shop-tool-repair`;
  - `townhouse-terrace`, `apartment-curved`;
  - `workshop-garage`, `clock-hall`;
  - any others present.
- Match each by footprint size, rotation and use: shops on the main strip, townhouses and apartments behind, the workshop at the edge.
- Repetition is acceptable. **Vary it** with rotation, mirroring where it looks fine, and per-instance palette tints (material instances) across cream, ivory, sand, petrol and coral.
- **Put a building on the café hero lot.** Our café was built as blockout architecture in the old Town. Reuse it, or a Tripo shop dressed as a café with an awning, seating and a sign; don't use a Village cottage.
- **Village Pack:** props and small filler only (crates, barrels, flower boxes, lamps, fences, market stalls). Remove the Village cottage buildings from the lots, or keep at most one or two small ones far from the plaza if a lot has no fitting Tripo building. Note any such lot.

### Ground
**Pave the town; grass only where it belongs.**
- **Roads:** real-width carriageways for the main seafront road and the side streets, with curbs.
- **Sidewalks:** 2–3 m sidewalks along every built frontage.
- **Courtyards and in-between areas:** lots and the gaps between buildings get paving, small parking areas or courtyards, and low walls or planters at their edges.
- **The plaza:** fully paved, with planters, benches and trees in groups.
- **Grass and planting:** only in parks and the hillside above the town, plus planting beds.
- Use the existing ground and paving materials, and one consistent family.
- Blend the edges with curbs, low walls or planting strips, so there are no hard grass-to-paving seams.

### Captures
- Before and after, from the same eye-level views as session 3: plaza, café, shop street, a hills view, plus one aerial.
- A grounded walk through the plaza and shop street, re-checked.
- Indicative fps.

All other rules from this brief apply: headless only, no computer use, launch guard and lock, no downloads, purchases or commits, and one fix per distinct, diagnosed failure. Stop at a verified checkpoint by about 30 minutes.

---

## Session 5: tighten the plaza block (user decision, 2026-11-06)

Session 4 put Tripo buildings on all 29 lots and paved the town. Final captures: `Saved/TownV2/session-4/final-all-views-sheet.jpg`. Claude's review:
1. **Over-paved.** The aerial reads as one pale slab with small buildings dotted on it. The lawn between buildings became pavement, not town.
2. **Buildings too small and too far apart for their plots.** The plaza, café and shop-street views show wide empty paving between frontages.
3. **Bases don't meet the ground.** Plain plinths, no steps or doorstep detail.

The user chose: **tighten the plaza, café and shop-street block first.** Seafront, palms, backdrop and lighting stay out of scope.

**Continue from the saved session-4 map.** Don't replay the session-4 one-time apply, refine or sightline scripts; make targeted in-place changes, and back up first (`Saved/TownV2/session-5/backup/`).

### Scope: the plaza–café–shop-street block only
Roughly the area seen by views 01 plaza_clock, 02 plaza_cafe and 03 shop_street, plus whatever the aerial shows within about 80 m of the plaza.

- **Frontages to the sidewalk.** Move buildings forward so their fronts sit on the sidewalk line, with doors aligned to it. Rotate them so the main façade faces the street or plaza.
- **Close the gaps.** Along a street frontage, gaps between buildings should be small (about 0–4 m), like a real town street. Fill wider gaps with:
  - another building, preferably a narrower or different type to break the repeated townhouse end walls;
  - garden walls with a gate, or a low annex or shed;
  - a narrow alley, at most one in each block face.
- **Scale check.** If the Tripo buildings are clearly too small for their lots or the street widths (compare doors and windows to the 1.8 m character), scale them up uniformly to a believable storey height (about 3–3.5 m per floor). Record the factor per asset. Don't stretch them non-uniformly.
- **Shrink the leftover paving.**
  - Courts behind the frontages become smaller courtyards, enclosed by walls, buildings or planting.
  - Large paved leftovers get planting beds, small gardens, trees, a few parked scooters or cars, market stalls, or low walls. **Planting and gardens are welcome here, not just more paving.**
  - The plaza itself stays a plaza, but its edges should be enclosed by frontages, not open paving.
- **Ground meeting.** Give building bases steps at the doors, a plinth or skirting in a darker tone, planters or flower boxes beside doors, and a threshold or doormat. Do this on the frontages visible from views 01–03 first.
- **Variety.** Vary the frontage rhythm: mix building types and widths along each block face, and vary the tints and awnings so neighbours aren't identical.

### Captures and checks
- Before and after, from the same 6 fixed views as session 4, plus **one new eye-level view looking down the shop street from the plaza**, and **a close aerial of the plaza block**.
- Re-run the grounded plaza–shop walk (same waypoints, adjusted only if a building now blocks a waypoint; note it).
- Indicative fps on the same views. **Judge the result by the eye-level captures.** If a change makes a view worse, revert it.

All other rules from this brief apply: headless only, no computer use, launch guard and lock, no downloads, purchases or commits, and one fix per distinct, diagnosed failure. Stop at a verified checkpoint by about 30 minutes. Append to `docs/TOWN-V2-PROGRESS.md`.

---

## Session 6: place the new seaside buildings (user request, 2026-11-07)

The user generated new buildings in our style from Claude's reference sheets (`concepts/building-reference-study-02/seaside-building-sheet.png`, `concepts/building-reference-study-03/metropolis-building-sheet.png`). Claude processed, delivered and imported them as static meshes at real scale, base at Z=0, origin at the base centre:

| Asset | Path | Size (m) | Use |
|---|---|---|---|
| Guesthouse | `/Game/Assets/seaside-guesthouse/seaside-guesthouse/StaticMeshes/seaside-guesthouse` | 12.9 × 12.5 × 15 | 4-storey guesthouse with wraparound balconies and a side stair |
| Lighthouse house | `/Game/Assets/seaside-lighthouse-house/seaside-lighthouse-house/StaticMeshes/seaside-lighthouse-house` | 14.5 × 12.7 × 14 | Lighthouse tower joined to a house, with a terrace and a hanging sign |
| Boathouse | `/Game/Assets/harbour-boathouse/harbour-boathouse/StaticMeshes/harbour-boathouse` | 11.1 × 9.7 × 9 | Harbour master's boathouse with clock and weather vane |
| Art-deco tower | `/Game/Assets/artdeco-tower/artdeco-tower/StaticMeshes/artdeco-tower` | 55.9 × 32.2 × 80 | **Don't place.** It's for a possible metropolis district later |

They're about 250k–280k triangles each. Each import report (`Saved/AssetImport/<id>.json`) shows **no simple collision**.

### Scope
1. **Engine setup** (in place on these four assets; this is the one allowed exception to the `/Game/Assets/*` rule): turn on **Nanite**, set **collision to complex-as-simple** (or add simple box collision if complex can't be used), and save. Check that the materials render with correct textures in the town light.
2. **Placement in `TownV2`**, continuing from the saved session-5 map with a backup first:
   - The **guesthouse** replaces one repeated townhouse on a visible plaza or shop-street frontage, with its front on the sidewalk line, and its door and stair reachable.
   - The **lighthouse house** goes on the seafront at a point or corner where it reads from the plaza, the shop street and the seafront views. The lighthouse should be a landmark you can see from the plaza.
   - The **boathouse** goes on the waterfront edge, with its big door facing the water or the seafront road.
   - Ground them properly: bases flush with the ground, no floating plinths or buried doors. Add a short sidewalk, steps or a low wall where needed, using existing kit pieces.
   - Don't move other buildings except the one the guesthouse replaces.
3. **Captures:** the same 8 fixed views as session 5, plus **one new eye-level view framing the lighthouse from the seafront**, before and after. Re-run the grounded plaza–shop walk (7 waypoints). Record indicative fps on the same views. **Report the fps change** (these meshes are heavier than the old buildings).

All other rules in this brief apply: headless only, no computer use, launch guard and lock, no downloads, purchases or commits, and one fix per distinct, diagnosed failure. Stop at a verified checkpoint by about 25 minutes and append to `docs/TOWN-V2-PROGRESS.md`.

---

## Session 7: preview the city buildings in the town (user request, 2026-11-07)

The user wants to **see the six city buildings in the game now**. There's no city district yet: place them **wherever they fit** in `TownV2`, so they can be walked up to and viewed. This is a preview placement, not final town design.

| Asset | Path | Size (m) |
|---|---|---|
| Walk-up | `/Game/Assets/metro-walkup/metro-walkup/StaticMeshes/metro-walkup` | 20.8 × 11.0 × 18 |
| Brownstones | `/Game/Assets/metro-brownstones/metro-brownstones/StaticMeshes/metro-brownstones` | 16.6 × 10.2 × 13 |
| Glass office | `/Game/Assets/metro-glass-office/metro-glass-office/StaticMeshes/metro-glass-office` | 31.5 × 30.4 × 38 |
| Lane houses | `/Game/Assets/metro-lane-houses/metro-lane-houses/StaticMeshes/metro-lane-houses` | 14.0 × 9.2 × 9 |
| Diner | `/Game/Assets/metro-diner/metro-diner/StaticMeshes/metro-diner` | 11.1 × 14.4 × 6.5 |
| Art-deco tower | `/Game/Assets/artdeco-tower/artdeco-tower/StaticMeshes/artdeco-tower` | 55.9 × 32.2 × 80 |

### Scope
1. **Engine setup** on these six assets, in place: Nanite on, and complex-as-simple collision (or simple box collision), the same as session 6 did for the seaside buildings.
2. **Continue from the saved session-6 map** (back up first). Don't move or remove anything session 6 placed.
3. **Placement:**
   - Put them on **empty or low-value ground at the edge of the built town**, for example the inland or hillside side, or an open paved area away from the plaza and seafront views.
   - Keep them out of the plaza, café and shop-street frontages that sessions 4–6 tightened.
   - Group them as a small **"city block" cluster**, with fronts facing a road or path so the player can walk up to each door.
   - Put the art-deco tower and the glass office at the back of the cluster, so they read as a skyline behind the town without hiding the lighthouse from the plaza.
   - Ground each building: base flush with the terrain, no floating or buried doors. Add short paving or steps only where needed.
   - Don't block the existing walk route.
4. **Captures:** one eye-level view of the cluster, one view from the plaza showing how the towers read on the skyline, and one aerial. Re-run the grounded walk, and record indicative fps on the session's standard views, as a change from session 6.

All other rules in this brief apply: headless only, no computer use, launch guard and lock, no downloads, purchases or commits, and one fix per distinct, diagnosed failure. Stop at a verified checkpoint by about 25 minutes and append to `docs/TOWN-V2-PROGRESS.md`.
