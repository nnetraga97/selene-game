# Animation match progress

## Session 1 — 2026-11-06, started 19:24 UTC

Checkpoint deadline: before approximately 19:49 UTC. No commits, downloads, paid services, mesh edits or browser. Entry: no Selene process observed. Existing `Config/DefaultEngine.ini` modification and untracked Content preserved.

- Implementing opt-in `selene.AnimMatch` comparison driver: runtime-only platform, common 450 cm camera, front/side/back, idle/walk/run/sprint/stop/pivot/jump, cyan travel arrow and runtime logs. Sparrow must be captured first.
- Evidence: `Saved/AnimMatch/session-1/`; original Source/config snapshots under `before/`. Capture inputs go to `Saved/AnimMatch/Captures/before/<Hero>/`.
- Exact next step: build, capture Sparrow and all four heroes, review contact sheets, then diagnose the Fixer/Courier facing defect before any hero fix.

### 19:42 UTC — baseline and diagnosis complete; candidate awaiting visual acceptance

- Built `SeleneEditor` successfully (exit 0, 14.99 s). Captured Sparrow first, then Champion, Angel, Fixer, Courier. All 5 game runs produced 21 PNGs and expected alarm exit 142. Contact sheets: `Saved/AnimMatch/session-1/<Hero>-before-contact.jpg`.
- Common harness: 450 cm boom, -10 degree pitch; camera yaw relative to pawn front/side/back = 180/90/0; runtime-only platform above town; movement phases at 0/150/350/600 cm/s, stop, reversal, jump. Cyan arrow shows actual velocity, or pawn forward when stationary. Captures are phase samples, not frame-synchronized animation cycles or continuous foot-sliding proof.
- **Priority 1 — Fixer/Courier facing and retarget pose:** front idle/walk/run images show profiles; side images show bodies facing across their stride. Compressed pose samples in `audit.json` show stance travel predominantly -Y while toe directions average roughly -164/-165 degrees for walking. A mesh-yaw change alone would rotate the stride away from travel. Both target poses have only a small hips delta despite the -X bind facing; their target rigs also have one FBIK solver and four goals, unlike Sparrow's explicit FK-only target rig.
- **Priority 2 — animation player discrepancy:** runtime logs show Fixer/Courier use `AnimSingleNodeInstance`, while Sparrow/Champion/Angel use `SeleneSecondaryAnimInstance`. Source routes only heroes with SecondaryChains through the custom DefaultSlot graph. Stop/pivot overlays and loop crossfades for zero-chain heroes require a separate fix/verification; no such fix yet.
- **Champion:** faces forward, readable walk/run; 13 Kawaii chains active. More exposed hips/shoulders and cloth deformation than Sparrow. Static images cannot establish skin-weight cause or exact sliding. No hero changes yet.
- **Angel:** faces forward; 12 Kawaii chains active. Large wings/cloth conceal leg motion and make the silhouette substantially different. No hero changes yet.
- **Sparrow:** unchanged reference. Uses Paragon idle/sprint/stop/jump and GASP walk/run. No Paragon clip transfer attempted; first resolve the rigs.
- Retarget settings exported to `settings.json`; all use matching named FK chains and default chain settings. Sparrow has enabled root motion op targeting a separate root, disabled Run IK Rig and no target solver. Other heroes disable Root Motion because hips are the skeleton root. Champion/Angel have no solvers; Fixer/Courier each have one. No new runtime foot IK/planting has been added. Mesh bounds include accessories (Sparrow's 255.88 cm bound is not body height); do not rescale using that number.
- Candidate implementation: duplicate each original retargeter into `/Game/Selene/Characters/<Hero>/AnimMatchS1/`; create a fresh `FacingManny` target pose; set the component-space -90 degree hips turn via bind-local quaternion; auto-align the child bones **excluding hips** so auto-alignment cannot replace the facing offset. Exported pose retains Z=-0.707107/W=0.707107. Retarget 11 GASP clips and 3 Manny jump/fall/land clips to new names; preserve root orientation with ANIM_FIRST_FRAME locking, remove only linear hips XY drift from the three loops and disable their root lock. New speed fields come from removed loop travel / duration (not a no-slip acceptance gate).
- `fix-candidate-exit.txt` = 0; `fix.json` success with 14 clips per hero. Only Fixer/Courier roster animation references and loop speeds changed. MeshRotation remains -90. Original retargeters/clips remain intact; runtime after captures are the acceptance test.

### Visual review of the corrected facing — 19:45 UTC

- **Fixer accepted for facing:** front idle/walk/run now show her front, side views show a forward stride instead of a body facing across it, and back/pivot/jump are oriented consistently. Evidence: `Fixer-after-facing-contact.jpg`, `Fixer-before-after-front.jpg`, `Fixer-before-after-side.jpg`. The comparison sheets put Sparrow / old Fixer / corrected Fixer in columns.
- **Courier:** corrected front walk and side run likewise align torso, boots and stride with the cyan travel arrow. Final full-set review follows below. Same root-pose correction, no mesh rotation change.
- **Champion, Angel, Sparrow:** no roster, clip, retargeter or Kawaii changes. Baseline front/side/back sheets reviewed, including jump and pivot. Champion's 13 and Angel's 12 chains are active in runtime logs.
- Loop reference speeds (walk/run/sprint cm/s): Fixer **219.483 / 548.746 / 768.252**; Courier **216.374 / 540.949 / 757.342**. Still provisional for foot sliding: removed source travel and captured movement speed are evidence, not a continuous planted-foot test.
- Reference leg lengths, thigh/shin cm (`proportions.json`): Sparrow 46.73/46.14; Champion 40.42/43.99; Angel 39.72/45.49; Fixer 41.97/43.34; Courier 43.31/42.65. Proportion differences remain; no mesh scaling or Blender changes.
- Skin weights were not audited directly or edited. Shoulder/hip/knee shape, rigid jacket regions and cloth silhouettes remain visibly different; do not attribute all of these to weights from a still frame. Sparrow's bow/arm pose, longer legs, Paragon idle/sprint/jumps and transitions remain distinct.
- Verification housekeeping: the first unscoped `git diff --check` reported the **pre-existing** blank line at EOF in `Config/DefaultEngine.ini`; this file matches its session-entry SHA-256 and was not changed. Recorded one correction to check only the authorized changed paths; that scoped check passes. No engine/build/retarget/capture failure or repair retry occurred.

### Exact next step for session 2

1. Keep the accepted `AnimMatchS1` assets and current Fixer/Courier roster references. Read this checkpoint and use a new evidence directory/labels; do not re-run the immutable session-1 generation.
2. Fix the zero-chain animation-player path in `ASeleneCharacter::ApplyCharacter`: route clip-based heroes through `USeleneSecondaryAnimInstance` even when `SecondaryChains` is empty, retaining the explicit `AnimClass` branch. Its existing graph already supports `SingleNode -> DefaultSlot` with zero Kawaii nodes. Do not add decorative physics chains to Fixer/Courier just to select that player.
3. Build `SeleneEditor`, re-capture Fixer/Courier with the same front/side/back phases and inspect stop/pivot and pace changes against these accepted sheets. Record active montage/slot playback alongside images, then briefly regression-check Champion/Angel Kawaii. Keep the facing fix independent of this change.
4. Only after transitions work, evaluate Sparrow-to-hero idle/sprint/stop/jump candidates against the current GASP/Manny choices, and tune stance speed using fresh compressed measurements plus continuous side-view footage. No paid steps, mesh edits, downloads, or original-asset deletion.

### Final checkpoint — 19:47 UTC (approximately 23 minutes)

**Stopped after the final strict log audit failed. No retry, further launch, or plugin repair was attempted. Facing is visually verified; the overall validation result is not clean.**

- Courier's complete front/side/back contact sheet is reviewed: the corrected body/feet face the travel direction through idle, walk, run, sprint, stop, pivot and jump. Retain both heroes' new roster clips as the accepted facing checkpoint; original assets remain available.
- **147 PNGs** total: 105 baseline + 42 corrected. Seven complete game runs, each 21 phase records/images and expected alarm exit **142**. Build, audit, settings, API inspection and candidate retarget commandlets exited **0**. No Selene process remains and the lock is released.
- `verification.json` deliberately remains **failed**: it detected Python startup errors in all seven `-game` logs. Exact terminal exceptions: `AttributeError: module 'unreal' has no attribute 'AgentSkill'` from the installed EditorToolset startup script, and `AttributeError: module 'unreal' has no attribute 'PythonTestRunner'` from ToolsetRegistry. These occur before gameplay in both baseline and corrected runs. They did not prevent the 147 captures or hero loading. `startup-error-classification.json` records them separately; there are no fatal-error entries or Selene asset-load failures. This supersedes the earlier interim statement about no engine failures. No changes outside the project or to plugin configuration were made.
- All **160 pre-existing generated character assets** match their entry hashes. Exactly **30 new assets** (two retargeters and 28 sequences) are confined to the two `AnimMatchS1` folders. `Config/DefaultEngine.ini` matches entry hash. No commits.
- Source changes are the opt-in comparison harness only. Config changes are the two heroes' animation references and measured loop reference speeds. New tools provide guarded launches, audit/pose inspection, candidate generation, contact sheets and evidence verification. Champion/Angel/Sparrow remain unchanged.

Contact sheets, all relative to project root:

| Hero | Before | After / comparison |
|---|---|---|
| Sparrow | `Saved/AnimMatch/session-1/Sparrow-before-contact.jpg` | Unchanged reference |
| Champion | `Saved/AnimMatch/session-1/Champion-before-contact.jpg` | Unchanged; 13 Kawaii chains |
| Angel | `Saved/AnimMatch/session-1/Angel-before-contact.jpg` | Unchanged; 12 Kawaii chains |
| Fixer | `Saved/AnimMatch/session-1/Fixer-before-contact.jpg` | `Fixer-after-facing-contact.jpg`, `Fixer-before-after-front.jpg`, `Fixer-before-after-side.jpg` in the same folder |
| Courier | `Saved/AnimMatch/session-1/Courier-before-contact.jpg` | `Courier-after-facing-contact.jpg`, `Courier-before-after-front.jpg`, `Courier-before-after-side.jpg` in the same folder |

**Next-session entry action:** first report/resolve the startup-error classification with the controller before further launches under the stop-on-failure rule; the installed plugin scripts are outside this task's edit scope. Do not silently filter those errors or re-run the failed verification as a pass. Once that is cleared, the exact next animation change is the zero-chain DefaultSlot player routing described above, followed by build and front/side/back stop/pivot recaptures. Remaining Sparrow gaps: transition playback, idle/sprint/jump clip choice, proportions, skin/cloth deformation and continuous foot-sliding validation.

## Session 2 — 2026-11-06, started 19:48 UTC

Controller accepted session-1 facing assets and cleared the two pre-existing plugin startup exceptions (AgentSkill / PythonTestRunner). They remain classified evidence, not failures; plugins untouched. Evidence: `Saved/AnimMatch/session-2/`. Entry snapshots and hashes saved. Routing all native clip players through the zero-chain-capable DefaultSlot graph while preserving explicit AnimClass. Checkpoint due before 20:13 UTC.

### Routing probe and one diagnosed transition correction

Build passed (12.17 s); Fixer routing probe produced all 21 images, exit 142. It uses SeleneSecondaryAnimInstance with zero chains, but stop montages only log position 0 before a pace switch cancels them; no pivot request appears. Evidence: `game-Fixer-s2-routing-editor.log` and `Fixer-s2-routing-contact.jpg`. Source explains both: SetAnimationAsset stops montages during deceleration, and reversal tests post-movement velocity after it has already changed direction. One focused correction holds the base player while a transition montage plays, and uses previous velocity/speed for stop/pivot detection and clip selection. Rebuild and new-label captures required; original routing probe retained.

### Final checkpoint — 19:58 UTC, stopped on visual failure

**Partial only. Step 1 is not accepted as complete. No Sparrow candidates were generated/adopted and no speed tuning was attempted.**

Retained source change: `ApplyCharacter` keeps the explicit `AnimClass` branch and routes every other native clip player through `USeleneSecondaryAnimInstance`, regardless of SecondaryChains count. Existing zero-chain graph supplies DefaultSlot. Added opt-in transition request/advancing montage-position logs, capture base-clip/play-rate records, and a verbose loop-crossfade log. No changes to the secondary graph, Kawaii configuration, roster or animation assets. `final-source.patch` is the exact delta from session-2 entry. Header is byte-identical to entry.

Evidence/acceptance:

- **Fixer routing-only:** built successfully; all 21 front/side/back captures reviewed. Facing remains correct and ordinary pace poses remain centered. Runtime proves `SeleneSecondaryAnimInstance_0 secondaryChains=0`, and start montage positions advance. However, stop gets canceled by subsequent base-clip switches, and reversal does not request a pivot. This is a partial routing checkpoint, not successful stop/pivot verification.
- **One attempted transition correction (REJECTED and rolled back):** keep the old base while a transition plays; use previous speed/direction to detect and select stop/pivot. Build passed. Both Fixer and Courier then logged sprint-stop and run-pivot montages advancing through approximately 0.9 seconds. Captures reveal bodies displaced far from the stationary capsule/travel arrow, including outside the side-view frame. The strategy also delays pace selection: the walk base remains selected at 350 cm/s in the run shot. Therefore the correction is not retained. The displacement suggests nonloop/root-offset incompatibility, but compressed transition-root transforms were **not** measured; do not claim that diagnosis proven.
- **Courier:** 21 rejected-correction captures reviewed; same stop/pivot displacement. The final routing-only state was not separately captured for Courier after rollback. Accepted `AnimMatchS1` facing assets and references remain byte-identical.
- **Champion / Angel:** no per-hero changes; Kawaii setup untouched. The requested fresh Champion regression was not reached because the preceding visual gate failed. No current-session runtime Kawaii claim.
- **Sparrow:** unchanged. Session-1 images reused only as labeled comparison references.

Build/cleanup details:

- Initial routing build exit 0 (12.17 s); attempted correction build exit 0 (15.12 s). Three game runs each exited expected alarm code 142, each with 21 phase records and 21 PNGs: **63 images** total.
- A restoration build exited 6 because `shutil.copy2` preserved the old header timestamp, causing UHT to reuse generated macros for lines 29/32 while restored source used 28/31. This was directly diagnosed from the compiler output and generated header. One recorded cleanup correction touched the restored header without changing its contents; recovery build `build-rollback-uht-recovery` exited **0** (19.66 s), regenerated UHT output and linked the retained routing-only source. No gameplay retry followed. Failed-build evidence is retained in `rollback-build-recovery.json` and its log.
- `verification.json` remains **failed_visual_acceptance**, with no unresolved technical errors, no unclassified Python errors, and the recovered build failure listed explicitly. Six known startup exceptions (AgentSkill and PythonTestRunner in each of three game logs) are classified with complete traceback lines in `startup-error-classification.json`; controller clearance applied, plugins untouched.
- All **256 existing Content/Selene assets**, including accepted AnimMatchS1 assets, plus `Config/DefaultEngine.ini` match entry hashes. No new assets. `Config/DefaultGame.ini` and the header match entry snapshots. Scoped `git diff --check` passes. No Selene process remains; `/tmp/selene-unreal.lock` released. No commits.
- Draft Sparrow candidate generation and an unbuilt pose-audition harness were prepared while waiting, then archived under `unexecuted-drafts/` and `rejected-transition-and-unbuilt-audition/`. They are **not executed, built, verified or ready-to-run approvals**. The candidate launcher draft depends on the removed audition harness. Do not mistake these drafts for completed retargeting.

All following paths are beneath `Saved/AnimMatch/session-2/`:

| Hero/state | Full contact sheet | Sparrow / current / compared-state sheets |
|---|---|---|
| Fixer retained routing | `Fixer-s2-routing-contact.jpg` | `Fixer-after-facing-vs-s2-routing-front.jpg`, `Fixer-after-facing-vs-s2-routing-side.jpg` |
| Fixer rejected correction | `Fixer-s2-transitions-contact.jpg` | `Fixer-s2-routing-vs-s2-transitions-front.jpg`, `Fixer-s2-routing-vs-s2-transitions-side.jpg` |
| Courier rejected correction | `Courier-s2-transitions-contact.jpg` | `Courier-after-facing-vs-s2-transitions-front.jpg`, `Courier-after-facing-vs-s2-transitions-side.jpg` |

Raw images are also copied into `captures/s2-routing/Fixer/` and `captures/s2-transitions/{Fixer,Courier}/`; original harness outputs remain under `Saved/AnimMatch/Captures/`. Full contact sheets show front/side/back; comparison sheets crop the same fixed rectangle from each source and label the rejected column explicitly. They compare phase samples, not synchronized gait cycles.

**Exact next step:** keep the retained routing, accepted facing assets and roster unchanged. First inspect compressed root/hips transforms at the beginning and through `AnimMatchS1` start/stop/pivot clips, especially `M_Neutral_Sprint_Stop_F_Lfoot_*_AM1` and `M_Neutral_Run_Pivot_F_B_Lfoot_*_AM1`, against the centered loops. Determine why an advancing overlay separates the mesh from its capsule; `ANIM_FIRST_FRAME` preserves a nonzero first-frame root offset if one exists. Prepare normalized copies only if measurements establish that cause. Independently implement base-clip changes that preserve a live transition montage without holding the previous pace for its whole duration; the rejected hold-base strategy must not be restored unchanged. Rebuild and capture Fixer/Courier stop/pivot/start plus Champion Kawaii before declaring step 1 complete. Then evaluate Sparrow-to-hero clips in isolated assets, with Sparrow/current/candidate sheets, and finally measure sliding.

Remaining gaps versus Sparrow: stop/pivot continuity and centered transition poses; untested Paragon idle/sprint/jump/turn choices and bow-less arm suitability; proportions/deformation differences; unmeasured continuous foot sliding. No speed changes are justified by this session's static samples.

Workspace note: final Git status also showed changes in `character_motion_shots.py`, `character_retarget.py`, `run_checked_stages.py`, `test_checked_stages.py` and `docs/research/` that were not made in this session. They were left untouched.

## Session 3 — 2026-11-06, started 19:59 UTC

Evidence: `Saved/AnimMatch/session-3/`. Retaining routing-only source and accepted AM1 facing assets. Measuring compressed transition roots before making normalized copies; then switching base clips without cancelling slot montages. Known plugin startup exceptions remain controller-cleared. Checkpoint due before 20:24 UTC. No commits or edits outside the authorized project scope.

### Normalization and playback implementation — 20:04 UTC

- Created fourteen new transition sequences (seven each for Fixer/Courier) in `AnimMatchS3/Anims`. Subtracted the initial RAW hips XY from the entire root track, preserving height, rotations, scale and motion deltas. Kept `ANIM_FIRST_FRAME` lock: the Mixamo hips are the root, so ZERO would erase height/facing. Original AM1 clips and loop speeds are unchanged.
- Confirmed large origins in RAW and later compressed samples: Fixer walk/run/sprint stop Y -293.784/-476.943/-539.033 cm; walk/run pivot -601.830/-464.532 cm. Courier -289.689/-470.669/-532.402 cm and -593.308/-458.010 cm. Initial compressed evaluation sometimes returns reference pose until data is ready; `normalization.json` preserves those original observations. A fresh-process warm-up then resample is prepared to verify frame zero accurately.
- Added a base-proxy-only setter, preserving the live transition montage's time and blend while switching ground pace immediately. Ground loop crossfades no longer replace live transitions. Stop/pivot detection uses previous-frame speed/direction, and character switches reset transition tracking. Existing routing and Kawaii graph preserved. Added 18 extra early/mid/late transition screenshots per hero (39 total).
- Build passed, 14.07 s. First Fixer launch is invalid: a roster substitution changed the package but retained the AM1 object suffix, causing asset-load failure. One diagnosed correction replaces all fourteen full object paths; evidence in `roster-reference-correction.json`. No asset regeneration or source variation. The initial launcher was also edited while its process guard was waiting (capture-count update); this breached the launcher immutability rule, although no Unreal launch had started then. It is now left unchanged during runs. No other process was interrupted.

### Fixer/Courier centered transitions verified — 20:09 UTC

Fresh-process `compressed-reload.json` confirms the actual first-frame and whole-clip locked hips positions after a warm-up evaluation. All fourteen normalized clips have horizontal residual below 0.006 cm. Originals retain the large offsets; authored/unlocked compressed samples are included as well.

Both corrected captures (`s3-fixedrefs`) produced 39 images, expected alarm exit 142. Visually reviewed full transition sheets (start/start-mid, stop/stop-mid/stop-late, pivot/pivot-mid/pivot-late; front/side/back). Bodies stay at the arrow/capsule origin, remain in frame and preserve AM1 facing. Side comparison sheets against Sparrow and rejected session-2 capture show the previously empty stop/pivot panels now contain centered bodies. Runtime records show stop/pivot montage positions advancing through base changes and correct run base at 350 cm/s. No old-base hold is used.

Visible remaining timing issue: the 3.467-second GASP walk-start overlay still affects the run phase image even after the base changes to the run loop; the base now changes correctly but the long full-body overlay is not yet artistically tuned. Do not describe the run sample as an isolated run-loop comparison or the entire gait as Sparrow-matched.

Sheets: `Fixer-s3-fixedrefs-contact.jpg`, `Fixer-s3-fixedrefs-transitions.jpg`, `Courier-s3-fixedrefs-contact.jpg`, `Courier-s3-fixedrefs-transitions.jpg`; Sparrow / rejected S2 / normalized comparison sheets are `<Hero>-s2-transitions-vs-s3-fixedrefs-{front,side}.jpg`. Champion regression is running next. No Sparrow candidate assets or foot-speed changes yet.

### Final checkpoint — 20:12 UTC (approximately 13 minutes)

**Partial completion; stopped on Champion visual regression. No Sparrow-clip candidates or foot-sliding measurements were attempted.**

- **Retained Fixer/Courier changes:** fourteen normalized transition copies and the fourteen full roster references (two roster lines). AM1 idle/walk/run/sprint/jump/fall/land, facing retargeters, mesh rotations, loop speeds and all originals remain unchanged. The new copies were accepted for centering using the experimental playback implementation: start/stop/pivot remain at the arrow across front/side/back.
- **Champion regression failed:** 39 images captured and full transition sheet reviewed. Stop/pivot bodies are far from the capsule/arrow; side/back images leave the body outside the frame. All 13 Kawaii chains remain active, with nonzero braid, skirt, hair and ribbon motion. Champion's older GASP transition hips origins are the leading hypothesis, **not measured in this session**. Champion assets, roster and Kawaii setup were never modified.
- **Angel/Sparrow:** unchanged. Angel was not recaptured; Sparrow's session-1 reference was used in comparison sheets. Their behavior with the new playback implementation remains unverified.
- **Shared playback implementation not retained live:** archived the exact source and unified patch under `unaccepted-playback/` and `unaccepted-playback.patch`. It changes the base proxy without cancelling/rewinding the live montage, suppresses competing loop fades, detects stop/pivot using previous velocity, and adds the 39-shot harness. Fixer/Courier logs prove immediate run-base selection and continued slot playback; however Champion regression and long full-body start-overlay timing prevent acceptance.
- Restored all four changed C++ source/header files **byte-for-byte to session entry**, preserving session-2 routing-only behavior and the existing 21-shot harness. Rebuilt successfully (exit 0, 21.24 s). This is a rollback to the accepted runtime, not another experimental correction. The restored runtime with the retained AM3 roster was **not recaptured** after the stop. Existing stop cancellation / missing pivot behavior therefore remains in the live source; do not claim the new switching implementation is active.
- Both builds and both commandlets passed. Three target game runs produced 117 PNGs (39 each) and expected alarm exit 142. The earlier bad-reference Fixer launch is separately recorded as invalid; it produced no Fixer captures. Known AgentSkill/PythonTestRunner startup errors remain controller-cleared and separately classified; there are no unclassified Python exceptions, fatal/assert/ensure failures, or remaining target asset-load failures after the one reference correction.
- `verification.json` intentionally says `failed_visual_regression`, not pass. All **256 pre-existing** `Content/Selene` assets retain their entry SHA-256; exactly **14 new assets** are in the two `AnimMatchS3/Anims` folders. `Config/DefaultEngine.ini` matches its entry hash. Scoped `git diff --check` passes. No Selene process or lock remains at final verification. No commits, browser, downloads, paid work, mesh edits or plugin edits.
- Bookkeeping errors remain recorded: initial attempt to read normalization evidence occurred while the guard was waiting; a final roster audit expected unquoted names although the INI uses quoted names (corrected parser, no config mutation). These were not animation retries. The launcher-edit-while-waiting deviation is recorded above.

All paths below are relative to `Saved/AnimMatch/session-3/`:

| Hero | Before/after comparison | Detailed transition sheet |
| --- | --- | --- |
| Fixer | `Fixer-s2-transitions-vs-s3-fixedrefs-front.jpg`, `Fixer-s2-transitions-vs-s3-fixedrefs-side.jpg` | `Fixer-s3-fixedrefs-transitions.jpg` |
| Courier | `Courier-s2-transitions-vs-s3-fixedrefs-front.jpg`, `Courier-s2-transitions-vs-s3-fixedrefs-side.jpg` | `Courier-s3-fixedrefs-transitions.jpg` |
| Champion | `Champion-before-vs-s3-regression-front.jpg`, `Champion-before-vs-s3-regression-side.jpg` | `Champion-s3-regression-transitions.jpg` |

The `<Hero>-<label>-contact.jpg` sheets contain the seven standard phases; raw images are copied into `captures/<label>/<Hero>/`. Comparison columns are Sparrow / prior hero / session-3 hero. Phase samples are not synchronized gait cycles. `compressed-reload.json` is the authoritative warm-up/reloaded compressed-origin evidence; `normalization.json` preserves original generation measurements, including the initial reference-pose warm-up artifact. `source-restoration.json`, `retained-roster.patch`, `checkpoint.json` and `unaccepted-playback.patch` document the exact retained/pending state.

**Exact next step:** under the launch guard, measure Champion's current seven GASP transition clips with a warm-up compressed evaluation at frame 0 and through each clip; audit Angel's equivalent clips in the same read-only pass. If their hips origins confirm the same defect, normalize XY into new isolated copies and repoint only those transition references. Keep the accepted Fixer/Courier AM3 copies. Reapply the archived playback patch (first check it against current source), rebuild, then repeat Fixer/Courier/Champion plus Angel regression with 39-shot front/side/back captures. Resolve the long walk-start overlay's visible pace lag without returning to the old-base hold or cancelling a live montage. Only after that visual gate passes, generate isolated Sparrow→hero candidates with Sparrow/current/candidate sheets and perform compressed stance plus continuous side-view foot-sliding measurements. No speed tuning is justified yet.
