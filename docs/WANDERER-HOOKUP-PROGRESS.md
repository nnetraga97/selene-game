# Wanderer hookup progress

## Session 1 — 2026-11-07 00:15 UTC (2026-11-06 local)

Scope: Wanderer content/material, her roster/cook lines, the marked material-slot change, new Wanderer tools and this document. Existing source/config edits are preserved in the entry snapshot. All launches use the Selene process guard, shared `/tmp/selene-unreal.lock`, a post-lock guard, Perl alarm and EXIT cleanup. No running Selene was killed. No browser, downloads, paid actions, commits, Blender edits or source-asset saves.

### First checkpoint — 00:20 UTC

- `SeleneEditor` build succeeded (13.09 seconds). Added optional `KeepMaterialSlots` and the marked `ApplyCharacter` skip for named slots. Existing heroes retain an empty keep list and all-slot overrides. `EmptyOverrideMaterials` already resets materials on cycling.
- Mannequin template auto-detection succeeds with all seven secondary chains present. `IK_Wanderer` uses `root` as requested; `RTG_Manny_To_Wanderer` keeps Root Motion enabled. Generated 21 template assets and all 15 GASP clips. No hips normalization or loop key editing.
- `MI_Toon_Wanderer` parent and texture readback match `M_Character_Toon` and imported `fantasy_female_character_3d_model_Clone1_basecolor`. Mesh slot 1 is exactly `FoxEye_amber`.
- Original fresh compressed audit: root translation is zero throughout all clips; walk/run/sprint pelvis XY seams <0.01 cm. Stops/pivots carry small local movement rather than the hundreds-of-centimeters Mixamo offsets. Raw and compressed samples are in `Saved/WandererHookup/session-1/measure/report.json`.
- First complete 21-frame AnimMatch capture, advanced off, exists at `Saved/AnimMatch/Captures/wanderer-baseline/Wanderer/`. Front and side show correct facing with default mesh yaw -90 and mesh Z -87.5; no facing-yaw fix is indicated.
- One diagnosed failure: default retarget pose preserves Wanderer's near-body/asymmetric arm bind directions, unlike Manny's wider arms. Fresh bind audit records the actual world-space joint positions. One targeted fix is in progress: target `AlignedToManny` pose using auto alignment, with output in `Wanderer/Aligned/Anims`; original clips/captures retained. No mesh edits or guessed yaw adjustments.

Evidence: `Saved/WandererHookup/session-1/{entry.json,build,retarget,measure,baseline,bind-audit,aligned}`. Exact current roster line is saved separately as `Wanderer-roster-line.txt`; final values await the aligned readback and captures.

Exact next step: freshly measure aligned clips, update only Wanderer's roster references/speeds, capture front/side/back against Sparrow, inspect eyes/skirt close-ups, run Champion/Fox regressions and advanced-on capture, then append final verification.

### Material and alignment checkpoint — 00:26 UTC

- The one bind-alignment correction succeeds visually: arms now sit beside the body in idle and swing normally in front/side locomotion. Accepted references are `Wanderer/Aligned/Anims`. Aligned raw/compressed audit still shows root XYZ zero; pelvis loop XY seams are walk **0.01107**, run **0.00174**, sprint **0.00483 cm**. Measured 60 Hz stance-speed medians: **168.362 / 433.102 / 640.261 cm/s**, from 25/19/6 samples. No normalization copies or edited animation tracks; no facing-yaw correction.
- One build/deployment failure was diagnosed: the initial successful build linked `libUnrealEditor-Selene-0001.dylib`, but game launches loaded the old canonical library. Runtime material readback exposed both slots still overridden. Rebuilding with `-NoHotReloadFromIDE -NoHotReload` linked the canonical library successfully (2.92 seconds); the next runtime readback verified the keep-slot behavior. No extra C++ edits were needed.
- One separate eye-rendering failure was diagnosed: imported `FoxEye_amber` uses `/InterchangeAssets/gltf/Substrate/M_GLTF`, whose `used_with_skeletal_mesh` flag is false. Even after the slot was preserved, eye cards rendered grey. One fix duplicates that parent into `Wanderer/Materials/M_Wanderer_Eyes`, enables skeletal usage on the copy, duplicates the eye MI as `Wanderer/Materials/FoxEye_amber`, and duplicates the unchanged mesh as `Wanderer/SK_Wanderer` with only eye material assignment changed. Skeleton/geometry/source assets are untouched. Roster uses this local mesh copy. The original amber texture is read back from the copied MI.
- The corrected eye close-up `details-eyes/captures/001_front_eyes_01.16.png` visibly shows amber irises. Runtime slot 0 is `MI_Toon_Wanderer`; slot 1 remains named `FoxEye_amber` and uses the Wanderer-owned compatible MI. The failed grey-eye witness is retained at `details-canonical/captures/001_front_eyes_01.13.png`.
- No crouch clip exists in the installed clip set, and shared movement source explicitly lacks slow crouch pending a proper clip. Landing/deep-bend captures are being recorded, but are not a claimed crouch test. This check remains unmet within the current allowed scope.

Exact next step: finish final game-distance captures/regressions and contact sheets, inspect skirt/shoulder motion, and verify source/config/content preservation before stopping.

### Root/pelvis audit checkpoint — 00:32 UTC

**The earlier zero-root conclusion is superseded, not accepted as proof that all workarounds disappeared.** A final operator audit found the IK root choice also set the target pelvis to `root` in both `Pelvis Motion` and `Root Motion`. This maps anatomical motion incorrectly and explains the suspiciously zero authored root travel. `ops-audit/report.json` records the settings and source/target local transforms.

One targeted operator fix now explicitly sets `Pelvis Motion` source/target to `pelvis`, and `Root Motion` source/target root to `root` with target pelvis `pelvis`. The IK rig retarget root remains `root`. New outputs are isolated at `Wanderer/RootSeparated/Anims`; prior variants are retained. Fresh before/after measurements and captures are required before these become the accepted roster references. If true-root first-frame offsets remain, standard `REF_POSE` root locking can preserve the imported root's nonidentity bind rotation; this is distinct from editing Mixamo hips keys.

Sparrow, Champion and Fox regression captures have completed, 21 each, all normal exits. Their side contact sheets visually preserve the previous baseline behavior/materials; phase timing is not synchronized. Fresh eye asset readback verifies 108 bones, the original shared skeleton, the original amber texture, and skeletal usage enabled on the Wanderer-owned parent. Imported assets remain untouched.

### Final verified checkpoint — 00:38 UTC, about 23 minutes

**Playable hookup is installed and captured. Overall brief status is partial: a true crouch close-up remains unavailable because there is no crouch animation in the installed set. Skirt coverage and knee deformation also remain visual limitations, not a claim of clipping-free polish.** This section supersedes the preliminary retarget measurements above.

#### Accepted assets and behavior

- Roster **Wanderer** uses `/Game/Selene/Characters/Wanderer/SK_Wanderer`, the local material-compatible copy on the unchanged imported 108-bone skeleton. Geometry was duplicated, not edited. `IK_Wanderer` retains retarget root **root**. Fresh `final-readback/report.json` confirms both motion operators use **pelvis** for anatomical motion and **root** for root motion.
- Accepted clips are the 21 template assets plus all **15 GASP sequences** under `/Game/Selene/Characters/Wanderer/RootSeparated/Anims`. Template jump/fall/land are included. Four turn clips exist; the current roster has no turn fields. Earlier unaligned/aligned variants remain as diagnostic evidence and are not selected by the roster.
- `MI_Toon_Wanderer` is freshly read back with parent `M_Character_Toon` and the delivered body base-colour texture. Slot 0 uses it. `KeepMaterialSlots=("FoxEye_amber")` preserves slot 1; the selected compatible eye MI is `/Game/Selene/Characters/Wanderer/Materials/FoxEye_amber`, using the original amber texture. No imported source material or mesh was saved.
- Native `SeleneSecondaryAnimInstance` runs all **7 chains / 28 real secondary bones**. Logs confirm **1 sphere + 13 capsule colliders** and nonzero secondary displacement. Hair trails and settles; skirt panels move and lift.
- Five complete **21-frame** standard captures: Wanderer advanced off, Sparrow/Champion/Fox regressions off, and Wanderer advanced on. All five exited **0**. Front/side/back comparison sheets and the advanced off/on side sheet were visually reviewed. Regression side sheets match prior behavior/materials; these are phase samples, not synchronized gait or pixel-equality comparisons.
- Advanced-on explicitly executes `selene.Character Fox` then `selene.Character next`, exercising `CycleCharacter()` (the existing C-bound function) and confirms Wanderer active. Physical keyboard C dispatch was not separately synthesized. This flat-fixture run verifies locomotion/jump compatibility, not every advanced ability.
- Default mesh offset **(0,0,-87.5)** and rotation **(0,-90,0)** are retained because front/side captures match travel direction and ground placement. EyeHeight **156**, BoomLength **350**; AnimMatch itself uses its standard 450 cm framing.

#### UE5 versus Mixamo: measured answer

The UE5 names make automatic mannequin chain recognition work despite secondary bones. **Manual Mixamo chain mapping, hips-key centering, linear hips loop correction, and a corrective hips-yaw turn were not needed.** Ordinary target bind-pose alignment was needed because her arm rest pose differs from Manny's.

**Large authored transition origins still exist.** With the anatomical mapping corrected, first-frame locked-root Y before the output-setting fix was:

| Clip | Before root Y, cm | After root XYZ throughout runtime playback |
|---|---:|---|
| Walk stop | -271.914 | (0,0,0) |
| Run stop | -425.853 | (0,0,0) |
| Sprint stop | -482.636 | (0,0,0) |
| Walk pivot | -555.918 | (0,0,0) |
| Run pivot | -415.994 | (0,0,0) |

The accepted GASP outputs use **enable_root_motion=False, force_root_lock=True, root_motion_root_lock=REF_POSE**. This ordinary real-root lock preserves the imported root's nonidentity bind rotation and removes the large origin offsets without touching pelvis keys or creating session-3 normalized copies. Root Motion remains enabled in the retargeter. Source/root travel remains in the authored tracks: walk/run/sprint cover **810.734 / 1266.761 / 1418.772 cm** over their full source-length clips. Runtime root locking handles it; no linear in-place key rewrite is used.

| Loop | Installed measured speed, cm/s | 60 Hz stance samples | Runtime pelvis XY loop seam, cm |
|---|---:|---:|---:|
| Walk | 193.444 | 124 | 0.016874 |
| Run | 487.574 | 17 | 0.000081 |
| Sprint | 683.326 | 12 | 0.001516 |

Method is the existing low-toe stance estimator (lowest 35% of toe heights, vertical speed below 25 cm/s, backward speed above 30 cm/s). These measurements select playback rates; they do not establish zero sliding. Raw and fresh compressed samples are in `root-separated-measure/report.json` (before root lock), `accepted-measure/report.json` (after), and `measurements-summary.json` under the session evidence directory.

#### Exact roster and Kawaii configuration

The complete, installed, single-line roster entry is **`Saved/WandererHookup/session-1/Wanderer-roster-line.txt`**, identical to **Config/DefaultGame.ini line 43**. The only additional config changes are the Wanderer and imported Wanderer SkeletalMeshes cook directories. Other hero entries and default character remain byte-identical to entry.

| Group | Roots | Damping | Stiffness | World location damping | World rotation damping | Radius, cm | Limit, degrees | Gravity Z |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Skirt | skirt_front_c_00, skirt_side_l_00, skirt_side_r_00, skirt_back_c_00 | 0.22 | 0.09 | 0.62 | 0.70 | 0.8 | 45 | -490 |
| Hair | hair_back_c_00, hair_side_l_00, hair_side_r_00 | 0.24 | 0.12 | 0.65 | 0.70 | 0.6 | 30 | -245 |

Colliders: pelvis sphere **10.5 cm**; spine_01→02 and spine_02→03 capsules **8 cm**, spine_03→04 and spine_04→05 **8.5 cm**, spine_05→neck_01 **9 cm**; each thigh→calf **6.5 cm**, calf→foot **4.5 cm**, upperarm→lowerarm **4 cm**, lowerarm→hand **3.5 cm**. Every name exists in the delivered hierarchy; no removed ruffle chains are referenced. Reference pelvis-to-thigh distances **8.853/9.304 cm** lie within the pelvis sphere. Thigh and calf capsules meet at the knees; lower-arm capsules extend to the hands. This establishes bone-centred coverage, not a mesh-surface collision guarantee. Values and distances are in `kawaii-values.json` and `collider-reference-distances.json`.

#### Eyes, shoulder trim, skirt, and crouch

- **Eyes pass the captured check:** amber irises are visible in `details-accepted/captures/001_front_eyes_01.16.png`, and eye cards remain normal at gameplay distance in `Saved/AnimMatch/Captures/wanderer-accepted-baseline/Wanderer/00_idle_front.png`. Runtime readback and fresh asset readback confirm the kept slot, original eye texture, and skeletal-compatible parent. Final game logs have **no FoxEye_amber skeletal-usage warning**. The diagnostic grey-eye before/after sheet remains available.
- **Shoulder check:** the template jump provides forward/raised arms; inspected front/side frames at about **12.52/12.55 s** show trim staying attached around the upper arms. No dedicated overhead-arms clip exists in the 15 GASP clips. The test does not certify every shoulder pose.
- **Skirt result:** panels trail, lift, and lose thigh coverage in run/sprint and deep bends. The front panel can fold back against the shorts/waist; lateral panels overlap the lifted leg in some views. Angular knee/thigh silhouettes are visible. The captures do not cleanly distinguish every shadow from literal mesh penetration, so **clipping-free behavior is not established**. No guessed collider/weight changes or Blender edits were made to hide the result.
- **39 final close-ups**, **1,032 runtime joint samples**, maximum knee flexion **142.812°**. Final witnesses include `details-accepted/captures/020_side_sprint_06.52.png`, `024_side_jump_shoulders_12.55.png`, `025_side_landing_bend_13.03.png`, and `013_front_landing_bend_13.02.png`. Joint samples occur at screenshot request time; asynchronous rendering may show a subsequent pose.
- **True crouch check remains unmet.** There is no authored crouch clip in the installed set, and `SeleneMovementComponent.cpp` explicitly says slow crouch is disabled until a proper clip exists. Landing and jump deep bends were captured as such; they are not substituted or relabeled as crouch.

#### Final contact sheets

All paths below are relative to the project root; the listed sheets exist and were visually reviewed.

| Check | Path |
|---|---|
| Wanderer versus Sparrow, front | `Saved/WandererHookup/session-1/Wanderer-vs-Sparrow-front.jpg` |
| Wanderer versus Sparrow, side | `Saved/WandererHookup/session-1/Wanderer-vs-Sparrow-side.jpg` |
| Wanderer versus Sparrow, back | `Saved/WandererHookup/session-1/Wanderer-vs-Sparrow-back.jpg` |
| Final eyes / front stride / shoulder / bend details | `Saved/WandererHookup/session-1/Wanderer-details-accepted-front.jpg` |
| Final side skirt / shoulder / bend details | `Saved/WandererHookup/session-1/Wanderer-details-accepted-side.jpg` |
| Final back skirt / hair details | `Saved/WandererHookup/session-1/Wanderer-details-accepted-back.jpg` |
| Eye material failure and fix (earlier retarget variant) | `Saved/WandererHookup/session-1/Wanderer-eyes-before-after.jpg` |
| Sparrow regression | `Saved/WandererHookup/session-1/Sparrow-regression-side.jpg` |
| Champion regression | `Saved/WandererHookup/session-1/Champion-regression-side.jpg` |
| Fox regression | `Saved/WandererHookup/session-1/Fox-regression-side.jpg` |
| Wanderer advanced off/on | `Saved/WandererHookup/session-1/Wanderer-advanced-off-vs-on-side.jpg` |

Full 21-frame Wanderer sheets: `Saved/AnimMatch/wanderer-session-1/Wanderer-wanderer-accepted-baseline-contact.jpg` and `Wanderer-wanderer-advanced-on-contact.jpg`. Raw standard frames are under `Saved/AnimMatch/Captures/wanderer-{accepted-baseline,sparrow-regression,champion-regression,fox-regression,advanced-on}/<Hero>/`.

#### Remaining differences and exact next step

Wanderer has different proportions, shorter measured strides, stronger body lean, and different idle/sprint/jump silhouettes from Sparrow's mix of GASP and Paragon-authored clips. Her angular knee deformation, cloth coverage, and hair/trim surface intersections remain less polished. Screenshot comparisons do not certify continuous foot contact or temporal smoothness.

The existing shared transition router is unchanged: disabled-mode logs request walk/run starts and stops but no pivot montage despite reversal-phase captures. Advanced-on logs do play WalkPivot. RunPivot and SprintStop are generated/configured but not shown playing by these harness logs. This is a shared runtime limitation, outside the marked material-slot source allowance. No Shipping cook, ability-complete test, or isolated physics performance benchmark is claimed.

**Exact next step:** supply/select an authorized local crouch animation, retarget it with the now-verified pelvis/root operators and the same root-lock settings into Wanderer-only content, and run front/side crouch close-ups with Kawaii on. Use the final stride/deep-bend witnesses above for a separate rig/weight and skirt-coverage review before authorizing mesh repair. Preserve this playable checkpoint; do not reapply the earlier Aligned variants or their speed values. Shared transition routing requires a separate task that permits changes beyond the marked material-slot block.

#### Verification and stopped state

`Saved/WandererHookup/session-1/verification.json` passes: **3,666 pre-existing Content files** retain size/mtime; all existing Source/Config hashes are preserved except the two permitted source files and DefaultGame.ini. Reversing only the marked source blocks reproduces entry bytes exactly, including the user's existing movement/AnimMatch work. Removing only the Wanderer roster line and two cook lines reproduces entry DefaultGame.ini exactly. DefaultEngine.ini and Town content are unchanged.

There are **115 new content assets**, all within Wanderer content or MI_Toon_Wanderer. This includes retained diagnostic animation variants; only RootSeparated clips are selected in the roster. Python syntax, Bash syntax, and scoped Git whitespace checks pass. Canonical SeleneEditor build and all final commandlets/game runs succeed. Final runtime logs contain no fatal/assert failure; nonfatal plugin startup exceptions and imported body-material initialization warnings are retained in `log-errors-and-warnings.json`. No source asset saves, other-hero edits, commits, browser use, downloads or paid actions occurred.

No Selene process remains. `/tmp/selene-unreal.lock` is released. Stopped at this verified checkpoint within the 30-minute bound.
