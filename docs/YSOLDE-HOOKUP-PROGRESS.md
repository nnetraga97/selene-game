# Ysolde hookup progress

## Session 1 — 2026-11-07 06:08 UTC (2026-11-06 local)

### Playable checkpoint — 06:13 UTC

- Read the full brief, Wanderer final recipe/scripts, Fox values, import report and the rig-owner progress/review. No Blender, browser, download, paid service or commit used.
- Entry snapshot: `Saved/YsoldeHookup/session-1/entry.json`, including pre-existing source/config/tool hashes and content size/mtime. Original editable files are alongside it. All Selene launches use the process guard, 15-minute maximum wait, shared `/tmp/selene-unreal.lock`, post-lock guard, Perl alarm and EXIT `rmdir`. Game runs use `-RenderOffscreen`.
- Added the marked `SlotMaterials` field and marked async-load, validation, and post-global-override application lines. Empty maps preserve existing behavior. Canonical `SeleneEditor` build succeeded in 14.46 s with `-NoHotReloadFromIDE -NoHotReload`.
- Created Ysolde-only IK rigs and retargeter using the Wanderer recipe: mannequin auto-template succeeds, target retarget root `root`, `AlignedToManny` target pose, Pelvis Motion uses `pelvis`, Root Motion uses `root` and anatomical `pelvis`. Both operators are enabled. Generated 21 template assets and 15 GASP sequences in `Ysolde/Anims`; reference-pose root locking is enabled without animation-key rewrites.
- Fresh 60 Hz raw/compressed readback measures walk/run/sprint at **203.865 / 510.961 / 714.471 cm/s** (113/16/11 stance samples). Runtime root XYZ stays zero; loop pelvis XY seams are **0.01617 / 0.00258 / 0.00118 cm**. Measurements are estimates, not proof of zero sliding.
- Roster `Ysolde` points directly at `/Game/Assets/council-envoy/council-envoy/SkeletalMeshes/council-envoy`. Fresh registry readback confirms exactly one imported SkeletalMesh, 111 bones, original skeleton, and no Ysolde-owned mesh duplicate.
- Created `MI_Toon_Ysolde_Body` and `MI_Toon_Ysolde_Cloth`, plus the copied `M_Character_Toon_TwoSided` parent. Fresh readback verifies atlas/atlas1 respectively, skeletal usage and two-sided cloth. Runtime observer verifies both named overrides on the original mesh. The existing body toon parent also already has Two Sided enabled; it was not changed.
- Added only the Ysolde roster line and two cook roots. Exact line: `Saved/YsoldeHookup/session-1/Ysolde-roster-line.txt`. Kawaii values: `kawaii-values.json`. Nine chains, pelvis sphere and thirteen capsules; thigh/calf radii start at **8 / 6.5 cm**.
- Complete 21-frame offscreen baseline captured at `Saved/YsoldeHookup/session-1/baseline/standard/Ysolde/`. Front/side captures confirm default yaw **-90**, offset **(0,0,-87.5)**. All requested phases exist. A back-run frame suggests boot/coat intersection; detailed rating is pending actual close-up and gameplay-distance review.
- Interim preservation check finds no pre-existing Content changes. Removing only the marked new source blocks exactly reproduces the entry source files, including unrelated user work.

**Exact next step:** finish the already-running serial close-up/gameplay observers, Sparrow/Wanderer/Fox regressions and Ysolde advanced-on cycle check. Generate and inspect front/side/back comparison sheets, rate every rig-review item, then run `python3 Tools/Unreal/ysolde_verify.py` and append final evidence/limitations. Do not rerun retarget or rebuild the existing assets.

### Final verified checkpoint — 2026-11-07 06:20 UTC, about 12 minutes

**Playable Ysolde and the capture review are installed. Overall status is partial because the coat does not clear the boots reliably and the trouser/crotch deformation needs repair. Do not interpret the successful engine hookup as clean rig acceptance.** No mesh repair or speculative collider sweep was attempted.

#### Installed result and verification

- **42 new content assets:** 3 IK/retarget assets, 21 template assets, 15 GASP clips, and 3 materials. All are confined to the allowed Ysolde/character-material paths. There is **no mesh duplicate**. Accepted animation path is `/Game/Selene/Characters/Ysolde/Anims`; no diagnostic retarget variants were needed.
- Fresh `readback/report.json` verifies `IK_Ysolde` retarget root `root`, Pelvis Motion source/target `pelvis`, Root Motion source/target `root` and target pelvis `pelvis`. Source GASP checksums matched the existing 15-clip manifest. Reference-pose root locking, rather than pelvis-key editing, produces zero runtime root translation.
- Exact installed roster line is [Ysolde-roster-line.txt](../Saved/YsoldeHookup/session-1/Ysolde-roster-line.txt), identical to the single `+Roster=(Name="Ysolde",...)` line in `Config/DefaultGame.ini`. It selects the imported mesh, the generated template jump/fall/land and GASP loops/transitions, the measured speeds above, the two named `SlotMaterials`, EyeHeight **156**, BoomLength **350**, offset **(0,0,-87.5)** and yaw **-90**. Two new cook roots cover the original mesh folder and Ysolde content; the existing character-material cook directory already covers the new materials.
- Native runtime reports **9 chains, 31 real secondary bones, 1 sphere + 13 capsules**. `secondary-hierarchy.json` records all children: cape chains 4 each, coat chains 4 each, sash 3, tassels 2 each. Debug logs show nonzero secondary displacement on all nine chains.
- The `SlotMaterials` implementation participates in existing async loading and validation, then applies named overrides after the global override. `EmptyOverrideMaterials` still resets slots on character changes. Fresh runtime observers verify `Ysolde_Body_Opaque → MI_Toon_Ysolde_Body` and `Ysolde_Cloth_TwoSided → MI_Toon_Ysolde_Cloth` on the original mesh. The cloth parent is the saved, skeletal-compatible, two-sided `M_Character_Toon_TwoSided` copy. Base-colour textures read back as the imported `ysolde-atlas` and `ysolde-atlas1` respectively.
- **Five complete 21-frame standard sets:** Ysolde advanced off, Sparrow/Wanderer/Fox regressions off, Ysolde advanced on. **Two 51-frame detail sets:** close and gameplay distance. All **seven game runs exit 0**; build and all three commandlets also exit 0. The observers contain **1,011 / 1,022 runtime samples**, with maximum measured knee flexion **139.507° / 140.875°**. Front sprint screenshot requests reach approximately **130°** flexion; jump-tuck requests approximately **138°**. These are actual deep-stride/jump samples, not relabelled idle poses. Screenshot rendering is asynchronous, so joint samples are not exact per-image vertex measurements.
- Advanced-on invokes `selene.Character Wanderer` then `selene.Character next` and confirms Ysolde active, exercising `CycleCharacter()`, the existing C-bound function. Physical C key dispatch was not synthesized. This proves flat-fixture locomotion/jump compatibility, not every advanced ability.
- Sparrow, Wanderer and Fox side regression sheets were inspected against their prior accepted captures: materials, silhouettes, scale and behavior remain consistent. Phase timing differs, especially stops; these are not pixel-equality or gait-synchronized comparisons.

#### Installed Kawaii values and colliders

Values are in native units: radius cm, angle degrees, gravity cm/s². Exact machine-readable settings: `Saved/YsoldeHookup/session-1/kawaii-values.json`.

| Group | Chains | Damping | Stiffness | World location damping | World rotation damping | Radius | Limit angle | Gravity Z |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Cape | 3 | 0.28 | 0.07 | 0.70 | 0.75 | 1.0 | 40 | -650 |
| Coat tails (`skirt`) | 3 | 0.22 | 0.09 | 0.62 | 0.70 | 0.8 | 45 | -490 |
| Sash | 1 | 0.18 | 0.07 | 0.58 | 0.65 | 0.5 | 50 | -490 |
| Tassels | 2 | 0.14 | 0.05 | 0.55 | 0.60 | 0.4 | 65 | -490 |

Colliders: pelvis sphere **11 cm**; spine_01→02 **8**, spine_02→03 **8**, spine_03→04 **8.5**, spine_04→05 **8.5**, spine_05→neck_01 **9**; each thigh→calf **8**, calf→foot **6.5**, upperarm→lowerarm **4**, lowerarm→hand **3.5 cm**. All bone names exist. Thigh/calf radii are deliberately larger than Wanderer's 6.5/4.5 cm, but bone-centred capsules do not guarantee clearance of all skinned garment vertices. The captured boot/coat failures remain despite these settings. Cape lifts substantially in motion; this is an initial cloth setup, not performance or physical-weight acceptance.

#### Rig-review verdicts

Gameplay-distance judgments use the standard 450 cm AnimMatch camera and a dedicated 450 cm / 90° observer pass. Close views use 310 cm / 40°, with 240 cm idle detail. Inspect original PNGs for detail; contact sheets reduce their resolution.

| Watch item | Gameplay distance | Close up | Evidence / interpretation |
|---|---|---|---|
| Cape clearance, run and sprint | **fine** in sampled views | **visible-but-minor** | Side/back cape stays above the lifted legs. Angular folds and large lift remain; no cape puncture isolated in this set. This does not certify every pose. |
| Coat clearance, run and sprint | **needs a Blender fix** | **needs a Blender fix** | Rear boot crosses the ivory/dark coat tail. Clear side witness: `details-close/captures/025_side_run_stride_05.56.png`; sprint: `027_side_sprint_06.65.png`; back: `042_back_run_stride_05.55.png`, `044_back_sprint_06.63.png`. Standard `baseline/standard/Ysolde/02_run_back.png` shows it at play distance. |
| Dark coat interior | **fine** | **fine** | Ivory inner hem and blue lining remain rendered and shaded on exposed backfaces. Dark navy shadow regions retain folds rather than disappearing into missing backfaces. The crotch opening below is a separate deformation issue. Front idle, jump and the front detail sheets are the witnesses. |
| Crotch/trousers, stride extreme and jump tuck | **needs a Blender fix** | **needs a Blender fix** | Pinching/dark seams during stride; conspicuous opening below the belt at the jump tuck. `details-close/captures/007_front_run_stride_05.14.png`, `011_front_sprint_07.12.png`, `014_front_jump_shoulders_12.53.png`; gameplay counterpart `details-gameplay/captures/014_front_jump_shoulders_12.53.png`. Small detached-looking fragments also appear during sprint. |
| Shoulders during arm swing | **visible-but-minor** | **visible-but-minor** | Flared/angular sleeve edges are visible, especially in sprint. No major run shoulder cavity was isolated at this framing. `007_front_run_stride_05.14.png`, `025_side_run_stride_05.56.png`, `027_side_sprint_06.65.png` in close captures. This does not overturn the rig review's raised-arm limitation. |
| Idle hand | **visible-but-minor** | **needs a Blender fix** | Small angular/hooked silhouette at play distance; flattened/separated-looking finger sections become obvious close up. `details-close/captures/001_front_idle_hand_interior_01.16.png`, gameplay counterpart `001_front_idle_hand_interior_01.17.png`. No clean closed-fist claim. |

Ratings and selected request-time joint measurements are also recorded in `rig-review-ratings.json` and `watch-item-witnesses.json`. These are visual findings; they do not establish the precise weight/topology cause of every defect. No source mesh, skeleton, imported material or texture was changed.

#### Contact sheets

All paths below are relative to `Saved/YsoldeHookup/session-1/`; all exist and were visually inspected.

| Check | Sheets |
|---|---|
| Ysolde beside Sparrow, all seven phases | `Ysolde-vs-Sparrow-front.jpg`, `Ysolde-vs-Sparrow-side.jpg`, `Ysolde-vs-Sparrow-back.jpg` |
| Rig watch items, close | `Ysolde-details-close-front.jpg`, `Ysolde-details-close-side.jpg`, `Ysolde-details-close-back.jpg` |
| Rig watch items, gameplay distance | `Ysolde-details-gameplay-front.jpg`, `Ysolde-details-gameplay-side.jpg`, `Ysolde-details-gameplay-back.jpg` |
| Existing-hero regressions | `Sparrow-regression-side.jpg`, `Wanderer-regression-side.jpg`, `Fox-regression-side.jpg` |
| Advanced movement off/on | `Ysolde-advanced-off-vs-on-side.jpg` |

Standard raw PNGs are under `<stage>/standard/<Hero>/`, detail PNGs under `details-{close,gameplay}/captures/`. The detail launches also retained their ordinary harness frames inside their own stage directories. No screenshots were written into other heroes' earlier evidence directories.

#### Remaining differences and exact next step

Ysolde has shorter measured strides than Sparrow (**203.865/510.961/714.471** versus **221.822/555.061/833.369 cm/s**), different proportions, stronger forward lean, and a different idle/sprint/jump silhouette. Sparrow uses a mixture of GASP and Paragon-authored clips; Ysolde uses GASP and template jump/fall/land. The screenshots do not certify continuous foot contact, temporal smoothness or equivalent polish.

The inherited transition limitation remains: advanced-off logs play walk/run starts and stops but do **not** play a pivot montage despite the reversal-phase screenshots. Advanced-on does play `M_Neutral_Walk_Pivot_F_B_Lfoot_Ysolde`. RunPivot and SprintStop assets are generated/configured but not demonstrated playing here; four turn clips have no roster turn fields. Shared transition routing is outside the marked material changes and was left untouched. No Shipping cook, full advanced-ability test or isolated physics performance benchmark is claimed.

**Exact next step:** keep this playable checkpoint. Review the coat-penetration, jump-crotch and idle-hand PNGs above for a separately authorized rig/weight/geometry repair. Prioritize the coat tail's relation to the bent boot and the trouser-to-pelvis attachment; do not rerun retargeting or guess new collider radii as a substitute for diagnosing those surfaces. After an approved repaired import, repeat `ysolde_details_run.sh` with fresh immutable labels at both distances, then the standard comparisons and preservation audit. The shared disabled-mode pivot limitation requires a separately scoped source task.

#### Preservation and stopped state

`Saved/YsoldeHookup/session-1/verification.json` passes. **5,010 pre-existing Content files** preserve size/mtime. Existing Source/Config/Tools hashes are unchanged except the two explicitly permitted source files and DefaultGame.ini. Removing just the marked Ysolde source additions reproduces entry bytes exactly, preserving the user's uncommitted work. Removing just the Ysolde roster and two cook lines reproduces entry DefaultGame.ini exactly. DefaultEngine.ini, imported `/Game/Assets/*`, other hero content and town maps are unchanged.

Canonical build, Python AST parsing, Bash syntax and scoped Git whitespace checks pass. Runtime logs retain the pre-existing AgentSkill/PythonTestRunner startup exceptions and transient source-material skeletal-usage warnings when installing the original mesh; the named final toon overrides are independently verified in the runtime observers. No new script/fatal/assert failure was found. Full warning/error evidence is in `log-errors-and-warnings.json`.

No Selene process remains and `/tmp/selene-unreal.lock` is released. No editor UI/computer use, Blender edits, commits, browser, downloads, paid or externally visible operations occurred. Stopped well before the 25-minute checkpoint bound.

ORCH_OUTCOME {"version":1,"state":"partial","reason":"Playable Ysolde and full capture review installed; coat clearance and trouser deformation remain unacceptable","unmet_checks":["Coat/boot clearance in run and sprint","Clean crotch/trouser deformation at jump tuck","Clean close-up idle fingers","Disabled-mode pivot montage coverage"]}
