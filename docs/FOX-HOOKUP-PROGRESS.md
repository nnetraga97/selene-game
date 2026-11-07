# Fox (Lysara Vey) hookup progress

## Session 1 — 2026-11-06, started 22:23 UTC

Scope: Fox-only generated assets, one Fox roster line and two cook directories, new `fox_*` tools, this document, and ignored capture/evidence files. Existing advanced-movement source/config edits are preserved. No Source edits, Blender, browser, downloads, paid services, or commits. Comparison launches explicitly set `selene.AdvancedMovement 0`. Every Unreal launch checks/waits for existing Selene, takes `/tmp/selene-unreal.lock`, rechecks, and uses a Perl alarm with EXIT lock cleanup.

### First verified checkpoint — 22:29 UTC

- `Saved/FoxHookup/session-1/entry.json` records entry source/config SHA-256 and Content/Tools metadata; the original DefaultGame.ini is preserved alongside it.
- The brief's external `rig-v10/report.json` exists but is a repair delta, not the promised hierarchy/roster snippet; adjacent `REPORT.md` is absent. The local delivered GLB and fresh Unreal component hierarchy agree on 160 bones and the 24 secondary roots. No imported asset was changed.
- Created `IK_Manny`, `IK_Fox`, `RTG_Manny_To_Fox` and 21 template animation/blend-space assets under `/Game/Selene/Characters/Fox`. Fox target chains are named explicitly, without target template matching. Default target pose retained; no hips yaw correction. Root Motion op disabled.
- Retargeted all 15 GASP source clips, including four turns. Preserved originals and created 11 centred transition/turn copies. Original stop/pivot origins ranged approximately -278 to -570 cm Y. Fresh compressed readback confirms centred roots; walk/run/sprint hips XY loop seams are approximately 0.0008/0.0015/0.0021 cm. These are measurements, not visual acceptance gates.
- Loops remove linear hips XY travel while retaining Z/sway/rotation/scale and other tracks. Raw travel speeds: 207.908 / 519.774 / 727.686 cm/s. Fresh 60 Hz compressed low-toe stance medians used in the roster: **201.365 / 504.542 / 704.951 cm/s**. Sampling uses the existing lowest-35%-height, abs vertical speed <25, backwards speed >30 method; it does not establish zero sliding.
- Created and freshly read back `MI_Toon_Fox`: parent `M_Character_Toon`, `BaseColorTex` is the delivered kitsune base-colour texture.
- Added one Fox roster line, mesh offset (0,0,-87.5), rotation (0,-90,0), eye height 163, boom 350; two cook roots are Fox and the imported Fox SkeletalMeshes directory. Exact line: `Saved/FoxHookup/session-1/Fox-roster-line.txt`.
- First gameplay capture completed all 21 AnimMatch frames, normal exit 0. Front walk and side run were inspected at full size: correct facing versus travel arrow, normal toon texture, animated/grounded body. Runtime logs confirm 24 chains, 1 sphere + 10 capsules and expected 150/350/600 cm/s paces. Full sheet review, comparisons, knees and advanced-on check remain next.

Evidence: `Saved/FoxHookup/session-1/{retarget,clips,reload,fox-baseline}/`, raw images `Saved/AnimMatch/Captures/fox-fox-baseline/Fox/`. Original raw transition clips are retained; accepted roster references select centred copies. Existing runtime stop cancellation/pivot-request limitations from AnimMatch are not repaired here.

Exact next step: finish Sparrow and Champion disabled-mode regression captures, inspect all three views, run the dedicated Fox close-up series through running and landing with Kawaii, then one advanced-on Fox capture. Append final scope verification and visual verdict.

### Final verified checkpoint — 22:39 UTC (about 16 minutes)

**Playable Fox hookup and the requested capture/visibility investigation are delivered. Visual polish is not equivalent to Sparrow, and the known knee area is not reliably hidden.** No additional asset repair is attempted outside this brief.

#### What works

- **51 new assets total:** 50 under `Content/Selene/Characters/Fox/` plus `MI_Toon_Fox.uasset`. The Fox assets comprise three rigs/retargeter assets, 21 template animation/blend-space assets (including jump/fall/land), 15 GASP sequences, and 11 centred copies. All three commandlets returned 0 with successful reports. Fresh compressed readback, not same-process output alone, verifies the loop and transition results.
- Fox loads through the native `SeleneSecondaryAnimInstance`, renders her toon texture, remains facing travel in front/side views, moves at 150/350/600 cm/s, stays centred in stop/reversal samples, and jumps/lands with secondary motion.
- **24 chains / 95 real secondary bones**, plus configured dummy tips. All 24 chains log nonzero simulation displacement. Nine tails fan out at rest and trail/settle in motion; sleeve/tabard/hair/tassel motion is visible. Tail-to-tail overlap remains accepted as specified.
- **Four complete 21-image captures:** Fox/Sparrow/Champion with advanced movement disabled, and Fox with it enabled. All four runs exit normally after the existing harness writes the images. All contact sheets were visually inspected. Sparrow and Champion match the prior baseline framing, scale, material and locomotion behavior; stop/reversal timing varies with screenshot hitches, so no pixel-identical claim.
- Advanced-on run explicitly uses `selene.Character Sparrow` followed by `selene.Character next`, exercising the same `CycleCharacter()` function bound to C, and logs Fox as active. The roster list contains Fox after Sparrow. Physical keyboard C dispatch was not separately pressed. The enabled-mode run verifies locomotion/jump compatibility on the flat AnimMatch fixture; it does **not** test Fox-specific mantle/dash/slide polish or ledge auto-mantle.
- Config changes are exactly the Fox roster line and two cook-directory lines. Full exact roster line is `Saved/FoxHookup/session-1/Fox-roster-line.txt`; it is identical to the installed line in `Config/DefaultGame.ini`. No other roster line, default character, or config setting was changed.

#### Kawaii values and collision coverage

All units follow the existing native fields: radius in cm, angle in degrees, gravity in cm/s². Values below are the installed and captured configuration, not placeholders.

| Group | Chains | Damping | Stiffness | World location damping | World rotation damping | Radius | Limit angle | Gravity Z |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Tails | 9 | 0.16 | 0.06 | 0.55 | 0.65 | 3.0 | 55 | -650 |
| Sleeves | 4 | 0.22 | 0.09 | 0.62 | 0.70 | 0.7 | 50 | -490 |
| Tabards | 4 | 0.22 | 0.09 | 0.62 | 0.70 | 0.8 | 45 | -490 |
| Hair | 4 | 0.24 | 0.12 | 0.65 | 0.70 | 0.6 | 30 | -245 |
| Tassels | 2 | 0.14 | 0.05 | 0.55 | 0.60 | 0.4 | 65 | -490 |
| Sash | 1 | 0.20 | 0.10 | 0.60 | 0.68 | 0.5 | 35 | -490 |

Colliders: hips sphere radius 11; Spine→Spine2 radius 8.5; Spine2→Neck radius 9; each UpLeg→Leg radius 6.5; Leg→Foot radius 4.5; Arm→ForeArm radius 4; **ForeArm→Hand radius 3.5**. One sphere and ten capsules are confirmed by the native runtime log. The hips-to-thigh-root distances are 9.487 cm, so the hips sphere overlaps both thigh capsule starts; thigh capsules extend 43.347 cm to the knees, overlapping the lower-leg capsules. Forearm capsules extend 23.154 cm to the hands. This confirms continuous bone-centred coverage, not a mesh-surface collision guarantee. Evidence: `collider-coverage.json`, `kawaii-values.json`, `reload/report.json`.

Performance note: this is 24 sequential Kawaii nodes, 95 real secondary bones plus dummy tips, with the body limits shared across the nodes. No isolated CPU timing claim is made from screenshot-heavy runs. **Proposal only:** keep all groups near the camera; gate cloth groups (sleeves/tabards/tassels/sash) by visibility, distance and skeletal LOD before reducing the silhouette-defining tails; reset/warm-start simulation on reactivation. Profile representative crowds before choosing distances or update rates. No gating implementation was added.

#### Dedicated knee/tabard result

**The pointed knee silhouette is visible in real play; tabards do not reliably conceal it.** In side running/sprinting and the tucked jump, the cloth lifts away and the angular knee/armour region is exposed below/beside its hem. Front running shows less of the protrusion; front and side landing recovery regain substantial coverage. The captures do **not** establish a literal through-fabric puncture at landing, nor do they isolate the contribution of authored armour shape versus skin-weight distortion. Treat this as a visible rig/mesh review item, not evidence that the tabards solve it.

- Full-size witnesses: `knees-observer/captures/013_side_run_04.23.png`, `017_side_sprint_06.20.png`, `022_side_jump_12.55.png`.
- Landing/recovery: `011_front_landing_13.04.png`, `012_front_landing_13.36.png`, `023_side_landing_13.16.png`, `024_side_landing_13.54.png` in that same directory. The last side frame shows feet recovered to the ground; the earlier landing frame retains an airborne-looking mesh pose during the animation transition.
- **37 close-ups**, including front and side running/sprinting and landing, plus back views. Kawaii remained on throughout. `observer.json` contains **706 actual runtime joint samples**, with maximum measured knee flexion **145.503°**. The run therefore exercises deep bends beyond 130°, rather than merely assuming the gameplay clips do so. Joint values are recorded at screenshot request time; asynchronous screenshots can render a subsequent frame. They are not exact per-image deformation measurements.
- The first close-up attempt generated ordinary zoomed AnimMatch shots but **zero extra AutoShots**: `TickDebugDrivers` returns immediately after AnimMatch. One diagnosed capture-only correction added `fox_knee_observer.py`, which observes the live game World, records knee sockets/falling state, and requests high-resolution screenshots independently. The corrected observer succeeded; no C++/asset/physics correction was made. Both close-up launches ended with the prescribed 90-second alarm (142). The unsuccessful AutoShots attempt is preserved under `knees/`; do not replay it.

#### Contact sheets

Paths below are relative to the project root. All are present and visually reviewed.

| Check | Contact sheet |
|---|---|
| Fox versus Sparrow — front | `Saved/FoxHookup/session-1/Fox-vs-Sparrow-front.jpg` |
| Fox versus Sparrow — side | `Saved/FoxHookup/session-1/Fox-vs-Sparrow-side.jpg` |
| Fox versus Sparrow — back | `Saved/FoxHookup/session-1/Fox-vs-Sparrow-back.jpg` |
| Knee/tabard close-ups — front | `Saved/FoxHookup/session-1/Fox-knees-front.jpg` |
| Knee/tabard close-ups — side | `Saved/FoxHookup/session-1/Fox-knees-side.jpg` |
| Knee/tabard close-ups — back | `Saved/FoxHookup/session-1/Fox-knees-back.jpg` |
| Sparrow regression versus earlier baseline | `Saved/FoxHookup/session-1/Sparrow-regression-side.jpg` |
| Champion regression versus disabled baseline | `Saved/FoxHookup/session-1/Champion-regression-side.jpg` |
| Fox advanced off/on | `Saved/FoxHookup/session-1/Fox-advanced-off-vs-on-side.jpg` |

Full front/side/back seven-phase sheets also exist in `Saved/AnimMatch/fox-session-1/`: `Fox-fox-fox-baseline-contact.jpg`, `Sparrow-fox-sparrow-regression-contact.jpg`, `Champion-fox-champion-regression-contact.jpg`, `Fox-fox-advanced-on-contact.jpg`. Raw images are under `Saved/AnimMatch/Captures/fox-{fox-baseline,sparrow-regression,champion-regression,advanced-on}/<Hero>/`. Comparisons are phase samples, not synchronized gait cycles.

#### Remaining differences from Sparrow and exact next step

- Fox retains GASP idle/sprint and template jump/fall/land, whereas Sparrow uses some Paragon-authored clips; their arm pose, stride, jump silhouette and proportions differ. Angular thigh/knee deformation and hand/wrist quality remain delivered-mesh limitations.
- Existing shared transition routing is unchanged. Disabled-mode logs request walk/run starts and stops but **no pivot montage** despite reversal-phase captures. Advanced mode requests the walk pivot under its different deceleration. Centred pivot/stop assets exist and are configured; this does not claim every montage is played fully or that transition continuity is fixed. Four turn clips and their centred copies are generated, but the current native roster has no turn fields to drive them.
- No continuous foot-sliding acceptance, all-ability animation acceptance, Shipping cook, or isolated performance benchmark is claimed. Speeds are measured estimates and live playback rates match them; screenshot hitches limit temporal assessment.
- **Exact next step:** review the three full-size knee witnesses above with the rig owner and decide whether the exposed pointed knee shape is acceptable at the standard 450 cm gameplay framing. If it needs repair, authorize a separate delivered-mesh/weight revision (outside this task's allowlist), then repeat this same Fox-only observer capture with a fresh immutable label. Keep the current clips/material/roster checkpoint. Separately, resume the existing AnimMatch transition work only under a task that permits shared Source changes; do not reapply its archived patch here.

#### Final verification / cleanup

`Saved/FoxHookup/session-1/verification.json`: all **3,319 pre-existing Content files** retain size/mtime; all entry Source files and `DefaultEngine.ini` retain SHA-256. Only pre-existing `DefaultGame.ini` changed, with exact subtraction of the three added lines reproducing entry bytes. Exactly 51 new Content assets are confined to the permitted Fox paths. Python AST parsing, Bash syntax, and scoped Git whitespace checks pass. No Selene process remains and `/tmp/selene-unreal.lock` is released.

`log-errors-and-warnings.json` preserves all error/warning evidence. Game logs contain only the brief-cleared AgentSkill/PythonTestRunner startup exceptions among errors; no new runtime/script/fatal/assert failure was found. The imported original Fox material emits its missing SkeletalMesh usage warning while `ApplyCharacter` installs the mesh, before applying `MI_Toon_Fox`; the final override is rendered in captures and its parent/texture are freshly read back. The original material remains untouched as required.

No source edits, other-hero asset edits, imported-asset edits, DefaultEngine edits, commits, browser use, downloads, or paid operations. The only diagnosed correction was to the capture observer. Stopped at this verified checkpoint within the session bound.
