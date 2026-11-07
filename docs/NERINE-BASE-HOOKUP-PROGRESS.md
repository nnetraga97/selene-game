# Nerine and Base hookup progress

## Session 1 — 2026-11-07 09:59 UTC

Read the complete hookup brief and Ysolde recipe/scripts. Read the explicitly referenced Nerine chain list and rig review; all new work is confined to the current project. Entry snapshot is `Saved/NerineHookup/session-1/entry.json`; original DefaultGame.ini is beside it. DefaultEngine.ini and imported Content were already uncommitted at entry and will be preserved.

Copied Ysolde scripts to `nerine_*` and `basebody_*`. Both use the existing two-sided parent and SlotMaterials; no C++ build/edit or mesh duplicate is planned. Nerine uses the ten supplied chain roots (26 secondary joints), Ysolde cloth values, lighter hair values, generous 8/6.5 cm thigh/calf capsules and an additional 8 cm head sphere. Base has no chains/colliders.

All launches use the process guard, bounded 15-minute wait, shared lock, post-lock guard, Perl alarm, EXIT rmdir, and offscreen/null-RHI execution. Existing process/lock are absent at entry. No paid/external actions are planned.

**Checkpoint:** scripts prepared; retarget/runtime verification pending. Do not infer playable acceptance from this initial note.

## Playable asset checkpoint — 2026-11-07 10:04 UTC

Both retarget, measurement and fresh readback commandlets exited 0, all reports success.
- **Nerine:** 3 IK/retarget assets, 21 template assets, 15 GASP clips, 4 toon instances. 106 bones; imported mesh retained and no duplicate. Loop speeds cm/s: {'WalkLoop': 208.358, 'RunLoop': 525.372, 'SprintLoop': 719.665}.
- **Base:** 3 IK/retarget assets, 21 template assets, 15 GASP clips, 1 toon instances. 80 bones; imported mesh retained and no duplicate. Loop speeds cm/s: {'WalkLoop': 206.148, 'RunLoop': 521.726, 'SprintLoop': 731.43}.

Both use root retarget root, AlignedToManny bind alignment, Pelvis Motion pelvis→pelvis, Root Motion root→root with anatomical pelvis, and REF_POSE force root lock. All measured runtime root XYZ ranges are zero. No animation-key edits.

The roster order is Ysolde, Nerine, Base. Exact full lines are saved in Saved/NerineHookup/session-1/Nerine/Nerine-roster-line.txt and Base/Base-roster-line.txt. Four cook roots were added. Nerine has ten chains, 2 spheres (pelvis/head) and 13 capsules; Base has no chains/colliders. Nerine Body/Hair use the current standard-lit M_Character_Toon (one-sided), Jacket/Skirt use the existing two-sided parent; each reads back its own imported texture. Base uses its own imported texture. Existing parents were not changed.

**Next:** guarded offscreen AnimMatch cycles for both entries, fresh Ysolde/Sparrow regression sets, gameplay watch-item observers for Nerine/Ysolde, and Base runtime-material observation. No visual acceptance yet.


## Final verified checkpoint — 2026-11-07 10:18 UTC (under 20 minutes)

**Hookup and the requested capture review are delivered. Visual rig acceptance remains needs-work.** The known mesh defects were observed and rated; no mesh/weight repair or speculative collider sweep was attempted.

### Installed and verified

- **83 new Content assets:** Nerine 43 (3 rigs/retargeter + 21 template assets + 15 GASP clips + 4 material instances), Base 40 (same animation/rig set + 1 material). All are inside the permitted hero/material paths. Each imported mesh remains the only mesh for its hero; neither hero folder contains a duplicate SkeletalMesh.
- Fresh readback verifies both retarget roots are root. Pelvis Motion maps pelvis→pelvis; Root Motion maps root→root and uses pelvis anatomically. The copied recipe creates the AlignedToManny pose and uses the same checksum-verified 15-clip GASP manifest. All 18 measured sequences per hero use force_root_lock and REF_POSE, with runtime root XYZ fixed at zero.
- Loop speeds (walk/run/sprint, cm/s): **Nerine 208.358 / 525.372 / 719.665**, **Base 206.148 / 521.726 / 731.430**. Stance sample counts are 67/7/5 and 106/13/7 respectively; these are gait-speed estimates, not proof of zero foot sliding. Pelvis XY loop seams are 0.01630/0.00189/0.00548 cm and 0.01697/0.00290/0.00344 cm.
- Front and side runtime images confirm **yaw -90**, with offset **(0,0,-87.5)**. Both use EyeHeight 156 and BoomLength 350. AnimMatch temporarily uses its standard 450 cm camera.
- Exact installed roster lines: [Nerine](../Saved/NerineHookup/session-1/Nerine/Nerine-roster-line.txt), [Base](../Saved/NerineHookup/session-1/Base/Base-roster-line.txt). Order is **Ysolde → Nerine → Base**. The launch commands exercise the existing cycle function with Ysolde→next and Nerine→next; physical C input and the concurrently developed picker UI were not synthesized.
- Only these two roster lines and their four cook roots were added to DefaultGame.ini. Removing those six lines reproduces the entry snapshot byte for byte.
- Runtime observers verify all named SlotMaterials on the original imported meshes: Nerine_Body→MI_Toon_Nerine_Body, Nerine_Hair→MI_Toon_Nerine_Hair, Nerine_Jacket→MI_Toon_Nerine_Jacket, Nerine_Skirt→MI_Toon_Nerine_Skirt; Base's original tripo slot→MI_Toon_Base_Body. Each instance reads back its own imported texture. Jacket and skirt use the existing skeletal-compatible M_Character_Toon_TwoSided; Body/Hair/Base use the current one-sided M_Character_Toon. Existing parents were not saved or changed.

### Kawaii and colliders

Values are native units: radius cm, angle degrees, gravity cm/s². Exact settings and ordered chain names are in [Nerine/kawaii-values.json](../Saved/NerineHookup/session-1/Nerine/kawaii-values.json); descendants are in [secondary-hierarchy.json](../Saved/NerineHookup/session-1/Nerine/secondary-hierarchy.json).

| Group | Chains | Damping | Stiffness | World location damping | World rotation damping | Radius | Limit angle | Gravity Z |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Cape | 1 | 0.28 | 0.07 | 0.70 | 0.75 | 1.0 | 40 | -650 |
| Skirt | 4 | 0.22 | 0.09 | 0.62 | 0.70 | 0.8 | 45 | -490 |
| Sash | 1 | 0.18 | 0.07 | 0.58 | 0.65 | 0.5 | 50 | -490 |
| Tassel | 1 | 0.14 | 0.05 | 0.55 | 0.60 | 0.4 | 65 | -490 |
| Hair (ponytail + curls) | 3 | 0.24 | 0.12 | 0.65 | 0.70 | 0.6 | 30 | -245 |

Nerine uses all ten supplied chain roots and 26 real secondary bones. Native logs confirm nonzero displacement on all ten chains, **2 spheres + 13 capsules**. Spheres: pelvis 11 cm, head 8 cm. Spine_01→02 / 02→03 / 03→04 / 04→05 / 05→neck_01 radii: 8 / 8 / 8.5 / 8.5 / 9 cm. Both thighs→calves **8 cm**, calves→feet **6.5 cm**, upper→lower arms 4 cm, lower arms→hands 3.5 cm. All referenced bones exist. Bone-centred capsules do not guarantee clearance of every skinned garment vertex. Base has **no chains and no colliders**.

### Captures and gameplay-distance ratings

Four complete standard sets (Nerine, Base, Ysolde, Sparrow) have **21 frames each**: front/side/back × idle/walk/run/sprint/stop/pivot/jump. Five detail sets have **51 frames each**: Nerine/Ysolde at gameplay and close distance, plus Base at gameplay distance. All **six commandlets and nine game runs exit 0**. Gameplay observers contain 1,024 Nerine, 968 Ysolde and 1,028 Base runtime joint samples; maximum knee flexion is approximately 139.96°, 140.72° and 138.26°. Request-time joint samples do not provide exact per-image vertex measurements because screenshots render asynchronously.

Ratings below are for gameplay distance (450 cm; dedicated observer FOV 90°), with close views (310 cm/FOV 40°, 240 cm idle) used to corroborate defects. Phase samples are not gait-synchronized. “Fine” applies only to inspected poses and is not full rig acceptance.

| Watch item | Nerine | Ysolde | Evidence / interpretation |
|---|---|---|---|
| Cape clearance in run/sprint | **fine** | **fine** | Nerine short shoulder cape stays clear; Ysolde cape clears lifted legs in sampled views. The lower skirt/coat is a separate failure. |
| Skirt or coat through legs in run/sprint | **needs a Blender fix** | **needs a Blender fix** | Nerine calf and bare foot penetrate orange rear skirt with strong flaring; Ysolde boot crosses ivory coat tails. |
| Crotch coverage at stride and jump tuck | **fine** | **needs a Blender fix** | Nerine layered skirt/leggings retain covered pelvis in the inspected front frames, despite severe cloth folding. Ysolde has a visible dark opening/seam beneath the belt at deep tuck. |
| Shoulders during arm swing | **needs a Blender fix** | **visible-but-minor** | Nerine has torn/jagged shoulder/sleeve edges and narrow hanging underarm strips, strongest in sprint and jump. Ysolde sleeve edges are angular but no comparable long strip was isolated in these locomotion samples. |
| Idle hand shape | **visible-but-minor** | **visible-but-minor** | Small angular/hooked hand silhouettes at gameplay distance. Nerine fingers are more rounded/curled but do not establish a usable fist or grip. Close-up acceptance remains needs-work for both. |
| Two-sided garment interior | **fine** | **fine** | Exposed orange skirt folds and jacket cuffs render with shading; ivory lining/navy coat backfaces remain visible. Dark cloth shadows do not prove missing faces. |
| Jacket/waist fit | **needs a Blender fix** | **visible-but-minor** | Nerine rear waist has irregular blue/skin-coloured fragments and overlap; Ysolde belt/coat junction is more cohesive, with the separate crotch defect noted above. |

Close corroboration: Nerine has long narrow underarm strips during sprint/jump and rough shoulder surfaces; both heroes have angular/flattened idle fingers. Nerine's hands curl more convincingly in motion than Ysolde's, but neither is accepted for a closed fist/grip. Nerine skirt coverage avoids the conspicuous exposed gap under Ysolde's belt at jump tuck; it does not cure the skirt's intersections or ballooning. The exact named PNGs and request-time joint values are saved in [watch-item-witnesses.json](../Saved/NerineHookup/session-1/watch-item-witnesses.json), and ratings in [rig-review-ratings.json](../Saved/NerineHookup/session-1/rig-review-ratings.json).

**Base in motion:** the bald 1.74 m body with blue swimwear stays upright, proportionate and correctly facing in the sampled front/side walk, run and jump. The pose progression is coherent without gross body collapse in those samples. There is no cloth or hair simulation. These stills do not certify continuous foot contact or close-up hand/shoulder quality.

**Regressions:** Sparrow's material, silhouette and locomotion remain visually consistent with the prior Ysolde-session captures. Ysolde preserves scale, movement and known coat/crotch defects. Her current skin/body shading is darker than in the older set; the session-entry parent differs from the old documented material state, and no pre-existing material was changed here. Do not read the comparison as pixel equality or proof that all pre-session shading changes were intended.

**Inherited transition limitation:** advanced movement is 0 throughout these comparison runs. Walk/run starts and stops are logged playing. Pivot-phase screenshots show the harness's reversal, but a pivot montage is not logged playing; configured RunPivot and SprintStop are not demonstrated by this fixture. Four retargeted turn clips have no roster turn fields. Shared transition routing was not edited. No Shipping cook, picker UI, full advanced-ability or physics-performance acceptance is claimed.

### Contact sheets

All paths below exist. Standard comparison, Base motion and regression sheets were inspected; gameplay-detail sheets and selected original close PNGs were inspected. Close sheets preserve the full captured sets for review.
- [Base-walk-run-jump.jpg](../Saved/NerineHookup/session-1/Base-walk-run-jump.jpg)
- [Nerine/Nerine-details-close-back.jpg](../Saved/NerineHookup/session-1/Nerine/Nerine-details-close-back.jpg)
- [Nerine/Nerine-details-close-front.jpg](../Saved/NerineHookup/session-1/Nerine/Nerine-details-close-front.jpg)
- [Nerine/Nerine-details-close-side.jpg](../Saved/NerineHookup/session-1/Nerine/Nerine-details-close-side.jpg)
- [Nerine/Nerine-details-gameplay-back.jpg](../Saved/NerineHookup/session-1/Nerine/Nerine-details-gameplay-back.jpg)
- [Nerine/Nerine-details-gameplay-front.jpg](../Saved/NerineHookup/session-1/Nerine/Nerine-details-gameplay-front.jpg)
- [Nerine/Nerine-details-gameplay-side.jpg](../Saved/NerineHookup/session-1/Nerine/Nerine-details-gameplay-side.jpg)
- [Nerine/Nerine-ysolde-details-close-back.jpg](../Saved/NerineHookup/session-1/Nerine/Nerine-ysolde-details-close-back.jpg)
- [Nerine/Nerine-ysolde-details-close-front.jpg](../Saved/NerineHookup/session-1/Nerine/Nerine-ysolde-details-close-front.jpg)
- [Nerine/Nerine-ysolde-details-close-side.jpg](../Saved/NerineHookup/session-1/Nerine/Nerine-ysolde-details-close-side.jpg)
- [Nerine/Nerine-ysolde-details-gameplay-back.jpg](../Saved/NerineHookup/session-1/Nerine/Nerine-ysolde-details-gameplay-back.jpg)
- [Nerine/Nerine-ysolde-details-gameplay-front.jpg](../Saved/NerineHookup/session-1/Nerine/Nerine-ysolde-details-gameplay-front.jpg)
- [Nerine/Nerine-ysolde-details-gameplay-side.jpg](../Saved/NerineHookup/session-1/Nerine/Nerine-ysolde-details-gameplay-side.jpg)
- [Nerine-vs-Ysolde-back.jpg](../Saved/NerineHookup/session-1/Nerine-vs-Ysolde-back.jpg)
- [Nerine-vs-Ysolde-front.jpg](../Saved/NerineHookup/session-1/Nerine-vs-Ysolde-front.jpg)
- [Nerine-vs-Ysolde-side.jpg](../Saved/NerineHookup/session-1/Nerine-vs-Ysolde-side.jpg)
- [Sparrow-regression-side.jpg](../Saved/NerineHookup/session-1/Sparrow-regression-side.jpg)
- [Ysolde-regression-side.jpg](../Saved/NerineHookup/session-1/Ysolde-regression-side.jpg)

The Base short sheet contains walk/run/jump, front and side. Standard originals are under each stage's standard/Hero folder; close/gameplay originals and observer.json are under each detail stage's captures folder. The initial Base sheet had overlong captions; one diagnosed presentation fix shortened the captions, preserving Base-walk-run-jump-initial.jpg and every original PNG. No capture or retarget rerun was needed for that correction.

### Preservation and exact next step

[verification.json](../Saved/NerineHookup/session-1/verification.json) passes. **All 4,609 pre-existing Content files preserve size/mtime**, including source assets, materials, maps and other heroes. DefaultEngine.ini preserves its entry hash. The concurrent changes in SelenePlayerController.h/.cpp, SSelenePauseMenu.cpp and UI/SSeleneHeroPicker.cpp were not authored or reverted here. This session did not edit any Source file or run a C++ build. The 83 new assets and final sheets have hashes in [artifact-manifest.json](../Saved/NerineHookup/session-1/artifact-manifest.json).

Copied Python AST checks, Bash syntax checks and scoped Git whitespace checks pass. Logs retain the existing AgentSkill/PythonTestRunner startup exceptions, material warnings from briefly installing the unmodified imported materials before SlotMaterials, and engine compression dependency warnings. Runtime material readback verifies the final toon overrides; no warning names a new toon instance as missing skeletal usage. No fatal/assert failure occurred. Full logs are preserved in [log-errors-and-warnings.json](../Saved/NerineHookup/session-1/log-errors-and-warnings.json).

All launches used the required pgrep guard, bounded wait, shared lock, post-lock check, Perl alarm and EXIT rmdir. The close sequence waited for the active Base capture rather than interrupting it. No alarm fired, no existing process was killed, and no Selene process or lock remained after verification. No editor UI/computer use, Blender, browser, download, paid service, commit or externally visible submission occurred.

**Exact next step:** keep this playable checkpoint and review the Nerine-versus-Ysolde sheets. A separately authorized mesh/weight repair should prioritize Nerine's underarm strips, skirt-to-bent-calf clearance and rear waist fit, then hand shape. Preserve this imported version and evidence. After a repaired import is authorized, repeat the copied detail launchers with fresh labels, then the standard comparison/regression and preservation audit. Do not rerun the completed retarget scripts against these existing outputs. No further engine hookup is required for Base's requested motion preview.

ORCH_OUTCOME {"version":1,"state":"delivered","reason":"Both playable roster entries, retargets, materials, Nerine physics, requested captures and rated comparison are installed; known rig defects are documented"}

## User play test — 2026-11-07

Nerine is not finished: bald on one side (hair cap does not cover the head), skirt clips through the legs, hands do not come out through the sleeves. Parked; committed as a playable draft to fix later in Blender. Base accepted as the reusable body.

## Nerine v2 on the base body — 2026-11-07 (Claude, not delegated)

Same hair/jacket/skirt (v1 session-2 fit) moved onto `base-female-v2` by a v1→base bone map, re-weighted from the base body, 0 credits.
Pipeline `nerine-v2` run `20261107T104227-1a93f5` (draft), 121k tris, 5 materials (body, hair-coloured scalp, hair, jacket, skirt).
Scripts: `<WF>/work/repairs/nerine-v2/{fit_v2,build_v2,pose_v2,sheet_v2}.py`; hookup `Tools/Unreal/nerinev2_{retarget,roster}.py`; roster entry `NerineV2` after Nerine (no slide fields yet).
Evidence: `Saved/NerineV2Hookup/v1-v2-ysolde-{front,side,back}.jpg`, `<WF>/work/repairs/nerine-v2/compare-{front,side}.png`, `details-v2.png`.

Verdict (Claude + Sonnet second opinion): Ysolde > v1 ≈ v2 in game. v2 fixes the sleeves (forearm now bends inside them) and the head is covered, but the skirt still opens around the legs at run/sprint, and the bikini base shows much more skin than v1's bodysuit. The base body is not a better foundation for this outfit; the skirt weighting is the weak link in both modular builds.

**Outcome (user, 2026-11-07):** v1 is better; v2 deleted (roster line, content, scripts and pipeline record moved to the Trash).

## Nerine v1 hair fix and NPC — 2026-11-07 (Claude)

Session 3 (`<WF>/work/repairs/nerine/session3/build_hairfix.py`): cap centred +13 mm X (no clearance push: it crumples the cap over the body's baked hair volume); 13,674 scalp and dark baked-stubble body faces moved to the Hair material with UVs pinned to a flat cap-coloured patch. Still 4 materials, same skeleton and weights. Candidate run `20261107T111329-cbeedd` (parent `20261107T095808-f8653b`), re-delivered draft and re-imported in place. Evidence: `session3/head-before.png`, `head-after.png`; in game `Saved/NerineHookup/session-1/Nerine/hairfix-before-after.jpg`.
Nerine is now an NPC: roster `bPlayable=False` (hidden from the C picker and C-cycling), and `+Npcs=(Character="Nerine",Offset=(X=500,Y=150,Z=0),Yaw=180)` spawns her idle 5 m ahead of the PlayerStart, facing the player (`ASeleneGameMode::SpawnNpcs`). Verified by log: spawned on the ground at the plaza start.
