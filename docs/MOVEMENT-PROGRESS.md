# Advanced movement progress

## Session 1 — 2026-11-06, started 21:37 UTC

The brief is authoritative. Mechanics are verified in priority order before implementing the next. No animation patch is reapplied. The existing AnimMatch offsets and interrupted overlays are pre-existing limitations.

### Baseline checkpoint and one diagnosed correction — 21:41 UTC

- Entry source/config copies and Content size/mtime manifest: `Saved/MovementTest/session-1/`.
- Baseline `SeleneEditor Mac Development` build succeeded: `Saved/MovementTest/s1-baseline-build/console.log`.
- Initial original-runtime Champion capture hit its 75-second alarm after 17/21 screenshots. This is an **incomplete harness run**, not a passing baseline. The log shows the sequence reached back-view run after startup, then the deadline cut it off. Evidence remains in `Saved/MovementTest/s1-before-champion/` and `Saved/AnimMatch/Captures/movement-s1-before-champion/Champion/`.
- **One recorded correction:** increase baseline/regression alarm from 75 to 120 seconds (within the brief's permitted game-launch range). Retry uses a new label. No launcher was edited while running. Any further execution failure stops the session without another retry.
- Known AgentSkill/PythonTestRunner startup errors are classified as cleared by this brief; other errors are not ignored.
- In progress: CMC momentum foundation and opt-in capture driver; new test map generator. Not yet built or accepted. Dash and subsequent abilities have not started.

### Intended bindings

When the corresponding mechanics are implemented: LeftAlt / gamepad left bumper = dash; LeftControl / gamepad face-right = crouch/slide; CapsLock = walk toggle; LeftShift stays sprint; Space / gamepad face-bottom = jump. With advanced movement off, LeftControl must remain the original walk toggle. Current checkpoint has not changed any bindings.

### Stopped on build failure — 21:47 UTC

**No advanced mechanic is accepted or active.** The first momentum build failed, so feature work stopped before creating the map or launching the candidate. The one correction was already used on the baseline timeout. The entire candidate is archived, and the two constructor hooks were restored byte-for-byte to session entry. No pre-existing AnimMatch change was overwritten; the archived playback patch was not applied.

Compiler diagnosis: UHT's generated `DEFINE_VTABLE_PTR_HELPER_CTOR_NS` instantiates destruction of `TUniquePtr<FSeleneMovementTestDriver>` with only a forward declaration visible in `SeleneMovementComponent.h`. Clang treats deleting the incomplete type as an error. The component's explicitly out-of-line destructor does not prevent this generated-constructor cleanup instantiation. See `Saved/MovementTest/s1-momentum-build/console.log`, lines 43–58. Build exit 6; no link of the candidate succeeded. No correction/retry of this build was attempted.

#### Done and evidence

- Guarded, immutable-label launcher: `Tools/Unreal/movement_run.sh`. Each invocation checks the process, acquires `/tmp/selene-unreal.lock`, rechecks, uses `perl` alarm, and releases the lock through EXIT. Baselines use 120 seconds after the recorded correction; candidate game stages use 90. The user's process was never killed.
- **Original-runtime baselines:** 21 Champion + 21 Sparrow PNGs, all visually reviewed through contact sheets. Walk/run/sprint log samples are 150/350/600 cm/s. Native player remains `SeleneSecondaryAnimInstance`; Champion has 13 and Sparrow 8 configured secondary chains, with nonzero swing logged. These are baseline observations, **not post-change regression or all-roster verification**.
- Champion screenshots: `Saved/AnimMatch/Captures/movement-s1-before-champion-fixed/Champion/`; sheet `Saved/MovementTest/session-1/champion-before.jpg`; log `Saved/MovementTest/s1-before-champion-fixed/editor.log`.
- Sparrow screenshots: `Saved/AnimMatch/Captures/movement-s1-before-sparrow/Sparrow/`; sheet `Saved/MovementTest/session-1/sparrow-before.jpg`; log `Saved/MovementTest/s1-before-sparrow/editor.log`.
- Both complete baseline launches ended with expected alarm exit 142. The incomplete first Champion attempt is preserved separately. Only the brief-cleared AgentSkill/PythonTestRunner exceptions appear in their error lines.
- New **unexecuted** Python generator: `Tools/Unreal/movement_test_level.py`. Defines a flat lane, 16-degree ramp, wall, four 100/140/180/220 cm ledges, 700 cm gap, and 220 cm double-jump platform. Refuses to overwrite an existing MovementTest map. **No MovementTest asset exists from this session.**
- New capture-sheet and evidence-summary helpers: `Tools/Unreal/movement_contacts.swift`, `Tools/Unreal/movement_report.py`. Swift generated the reviewed sheets; both Python sources parse, launcher passes `bash -n`. Summary reports deliberately do not assert visual acceptance. Baseline screenshots live under AnimMatch rather than each log directory, so `report.json`'s local `captures` field is empty; `session-1/verification.json` records their actual counts and paths are above.
- Candidate archive: `Saved/MovementTest/session-1/unaccepted-momentum/Source/Selene/Movement/` and `candidate.patch`. It contains the CMC momentum implementation and an opt-in `selene.MoveTest` momentum-only driver, with per-frame CSV and 3P/1P screenshots. The fixture impulse is labeled explicitly and is **not dash implementation**. Trace stamina is `-1` (not implemented). No candidate trace or capture exists.
- Preservation: `Saved/MovementTest/session-1/verification.json` and `source-restoration.json`. All eight snapshotted source/config files match entry SHA-256 after rollback. All **3,313** pre-existing Content files retain size and mtime; zero Content files were added. This is a metadata manifest check, not a fresh full-asset hash claim. `DefaultEngine.ini` and `DefaultGame.ini` match their entry hashes.

#### Tunables in the archived candidate (not live or accepted)

All new tunables were `UPROPERTY(EditAnywhere)` fields in `USeleneMovementComponent`; values are original to this candidate.

| Field | Value | Units / intent |
| --- | ---: | --- |
| MovingGroundFriction | 5.0 | Ground steering/friction |
| GroundBraking | 1400 | cm/s² |
| LandingCarrySeconds | 0.30 | seconds |
| LandingFriction | 0.12 | During landing carry |
| LandingBraking | 90 | cm/s² during carry |
| ExcessSpeedDecay | 125 | cm/s² toward selected pace (600 while sprinting) |
| AirSteering | 0.22 | Input acceleration multiplier, no low-speed boost |
| AirAccelerationLimit | 450 | cm/s² |
| ChainJumpBonus | 65 | cm/s for a jump within landing carry |

The candidate cvar defaults `selene.AdvancedMovement` to 1 and delegates to stock CMC when 0. **Neither path was run**, and the cvar is absent again after source rollback. No stamina, custom dash/slide physics, camera feedback, extra jump, wall jump, or mantle has been implemented. No gameplay tuning is retained live.

#### Bindings, animation, regression, and feel

- **Active keys unchanged:** WASD/mouse, Space jump, LeftShift sprint, LeftControl walk toggle, V camera, C hero, Esc menu. New bindings above remain proposals; none were installed. Existing source maps gamepad sticks/menu, but does not explicitly map gamepad jump/sprint in this controller; do not claim the proposed pad actions work.
- No new movement animation or montage was installed. Champion still uses `MM_Jump_Champion`, `MM_Fall_Loop_Champion`, `MM_Land_Champion`; Sparrow uses `Jump_Start`, `Jump_Apex`, `Jump_Land`. The archived momentum candidate relies on the unchanged existing jump/fall/land path, not new DefaultSlot overlays. Future double/wall-jump DefaultSlot hookups remain undone.
- New per-hero crouch, slide, dash, and mantle clips are still needed from permitted later GASP/Sparrow work. No migration or retargeting started.
- Regression with `selene.AdvancedMovement 0` **not reached**. Full roster cycling, Angel chains, first-person advanced movement, stamina, and all seven requested scripted-sequence stages remain unverified.
- Feel cannot be evaluated for the unrun candidate. The baseline still shows previously documented animation imperfections: some non-neutral idle/stop samples and interrupted transitions. No claim of fixing those or foot sliding.

#### Exact next step

1. Review `Saved/MovementTest/session-1/unaccepted-momentum/candidate.patch` against the current entry state, then restore that candidate. Before building, include `Movement/SeleneMovementTestDriver.h` in `SeleneMovementComponent.h` **before** the generated header so the UHT helper constructor sees the complete type (or use an equivalently complete-type-safe ownership arrangement). This is the diagnosed but **unapplied** fix.
2. Build with `bash Tools/Unreal/movement_run.sh build s2-momentum-build`. If successful, create the still-missing map with `bash Tools/Unreal/movement_run.sh map s2-map` and capture with `bash Tools/Unreal/movement_run.sh momentum s2-momentum Champion 1`.
3. Inspect the per-frame trace and every 3P/1P key frame for air steering, uninterrupted surplus speed, carry, chain jump, decay, and floor/capsule safety. Fix no later mechanic before this stage is accepted. Then implement dash in `PhysCustom`, stamina/HUD/FOV and input hooks; verify before slide, extra jump, wall jump, and mantle.
4. After accepted movement, run fresh disabled-mode Sparrow/Champion captures against the baselines above, verify all-roster cycling and Kawaii motion with the feature enabled, and implement/run the complete ordered course sequence. No further gameplay launches were made after the build failure in this session.

### Final restoration verification — 21:48 UTC

- Restored `SeleneEditor Mac Development` build **succeeded**, exit 0, 15.74 seconds: `Saved/MovementTest/s1-restored-build/console.log`. This is rollback verification only; no candidate retry or editor/game launch occurred.
- Final process check: no Selene editor; `/tmp/selene-unreal.lock` absent. `Saved/MovementTest/session-1/final-checkpoint.json` records the final state. No commits, browser, downloads, paid services, config edits, or Content mutations.
- Stopped early under the failure rule, approximately 11 minutes into the bounded session. Retained deliverables are baseline evidence, tooling, progress documentation, and the archived unaccepted candidate; the requested movement implementation remains unfinished.

## Session 2 — 2026-11-06, started 21:49 UTC

Read the entire brief including the clarification: one fix per distinct diagnosed failure; normal clear compile errors are fixable. Entry hashes/source copies and Content manifest are in `Saved/MovementTest/session-2/`. Restored the archived candidate and included the complete test-driver type before the generated header. Build `s2-momentum-build` passed (15.83 s). Generated only the new MovementTest map with `s2-map`; commandlet exit 0.

### Momentum accepted — 21:51 UTC

`s2-momentum` completed with 653 trace frames and all 18 3P/1P captures; reviewed `session-2/momentum.jpg` and the landing frame at full size. Both views show sprint 600, fixture impulse ~956, responsive lateral air steering, landing ~829 followed by chain jump ~889, second landing ~763–765, 0.30 s carry, decay back to 600, then stop. No floor/capsule fault observed. The impulse is a test fixture, not a dash. Existing Champion jump/fall/land animation remains in use; 13 Kawaii chains remain active with nonzero swing. Evidence: `Saved/MovementTest/s2-momentum/{trace.csv,editor.log,report.json,*.png}`; acceptance record and accepted-source snapshot under `Saved/MovementTest/session-2/`. Proceeding to dash.

### Dash accepted — 21:56 UTC

Build `s2-dash-build` passed. `s2-dash` completed with 1,039 trace frames and 22 reviewed 3P/1P captures (`session-2/dash.jpg`). Ground/air/no-input dashes reach 1,100 cm/s; charge spends 3→2→1→0, next request rejected, recharge reaches 3. Both gap jumps land beyond x=2,117 on the far platform. FOV rises by 5.67/6.09 degrees in sampled frames and returns to zero. HUD agrees. Screenshot capture stalls skip the first short dash in per-frame state samples, but later ground/air dash captures show the state. No floor/capsule fault observed. New keys compile (Alt/left bumper dash, CapsLock walk, Ctrl reserved; disabled Ctrl retains original toggle). Script invokes ability functions; physical key dispatch remains to verify. Current animation reuses existing locomotion/jump/fall/land; no dedicated dash montage yet. Accepted-source snapshot and acceptance JSON are in `session-2/accepted-dash` and `session-2/dash-acceptance.json`. Proceeding to slide.

### Slide accepted after one diagnosed visual correction — 22:04 UTC

Initial `s2-slide` physics worked, but its pose was overwritten by ordinary locomotion. Read-only `s2-slide-pose-audit` proved Champion sprint-stop has locked hips Y≈-550.5 cm (explains out-of-frame body) and measured the jump pose. One correction (`session-2/slide-correction.json`): small marked character hook defers normal base/transition updates while slide owns DefaultSlot; hold Jump at 0.52 s and lower visual mesh32 cm, restoring it on exit. No assets changed. Landing capture keeps forward input through landing; inherited Champion stop-offset fault outside slide is explicitly still present.

`s2-slide-fixed-build` passed; `s2-slide-fixed` completed with 1,132 trace frames and22 reviewed 3P/1P images (`session-2/slide-fixed.jpg`). Downhill accelerates to about660; flat decelerates560→386→exit; uphill slows to exit; slide-jump carries speed; slow request rejected. Capsule half-height48 during slide and87.5 afterwards, no penetration/sticking observed. Low pose now remains visible. Native crouch dimensions restored; camera lowers40 cm in addition to capsule drop. New gamepad face-bottom jump and face-right slide bindings are installed, with added keys inert when disabled. Physical dispatch remains to verify. Proceeding to extra jump.

### Extra jump accepted after diagnosed harness correction — 22:09 UTC

Initial `s2-extra` was invalid: capture hitch caused jump press/release in one tick; lateral fixture left the lane before landing, contaminating next view. Recorded correction in `session-2/extra-harness-correction.json`: release relative to actual press, extra timing relative to actual first jump, earlier warmup shot, lateral fixture starts at y=-350. Gameplay physics unchanged by this correction. `s2-extra-fixed-build` passed; `s2-extra-fixed` has16 reviewed 3P/1P captures (`session-2/extra-fixed.jpg`). Both views land on220cm platform (capsule Z309.65), spend one charge, reject repeated/empty requests, redirect laterally and land safely. Full trace ends grounded in both views. Extra jump uses active hero Jump clip through DefaultSlot; existing fall/land remains. Proceeding to wall jump.

### Wall jump accepted — 22:12 UTC

`s2-wall-build` passed; `s2-wall` completed with14 reviewed3P/1P images (`session-2/wall.jpg`) and trace. Outward/upward kick650/560, samewall attempt rejected, real landing restores eligibility, no-wall request rejected, stamina unchanged, ends grounded. No camera roll added. Active Jump clip is requested through DefaultSlot. Harness note: forced reset before open-air negative test preserves the historical wall-air label until landing; request log/zero horizontal velocity prove no new kick. This is a trace-label limitation, not another kick. Proceeding to mantle.

### Mantle mechanics accepted — 22:15 UTC

`s2-mantle-build` passed; `s2-mantle` completed with20 reviewed3P/1P frames (`session-2/mantle.jpg`). Forward capsule sweep, top trace, capsule clearance check, then swept scripted lift/forward move. All100/140/180/220cm ledges end on top (capsule Z189.65/229.65/269.65/309.65);460cm wall rejected. No stuck capsule. This is mechanics acceptance with an upright placeholder pose, not polished climbing animation. The code requests Jump overlay but ordinary base updates can replace it; captures show standing/locomotion during lift. A proper mantle clip/pose ownership needs later work. CMC velocity remains zero during scripted mantle; position columns show its movement.

Regression build `s2-regression-build` passed after adding a bounded six-hero roster driver. Disabled-mode regression launches now exit normally once the existing21 AnimMatch screenshots are physically written; guards/lock/alarm remain. No launcher was edited while running. Full combined seven-step `sequence` stage is still NOT implemented (it refuses unsupported stage); individual mechanics were tested in priority order. The default MoveTest stage remains momentum.

### Current tunables (all new gameplay fields in USeleneMovementComponent)

| Property | Default |
| --- | ---: |
| DashSpeed | 1100.f |
| DashSeconds | 0.20f |
| DashFOVKick | 7.f |
| FOVReturnSpeed | 12.f |
| StaminaCharges | 3 |
| ChargeRegenSeconds | 2.f |
| StaminaRegenDelay | 0.8f |
| SlideMinSpeed | 480.f |
| SlideEndSpeed | 180.f |
| SlideHalfHeight | 48.f |
| SlideBraking | 100.f |
| SlideFriction | 0.12f |
| SlideCameraDrop | 40.f |
| SlidePoseTime | 0.52f |
| SlidePoseMeshDrop | 32.f |
| ExtraJumpVelocity | 500.f |
| ExtraJumpRedirect | 0.65f |
| AbilityBlendIn | 0.10f |
| AbilityBlendOut | 0.12f |
| WallProbeReach | 55.f |
| WallJumpSpeed | 650.f |
| WallJumpUpSpeed | 560.f |
| MantleMinHeight | 80.f |
| MantleMaxHeight | 225.f |
| MantleReach | 110.f |
| MantleTopInset | 50.f |
| MantleSeconds | 0.65f |
| MovingGroundFriction | 5.0f |
| GroundBraking | 1400.0f |
| LandingCarrySeconds | 0.30f |
| LandingFriction | 0.12f |
| LandingBraking | 90.0f |
| ExcessSpeedDecay | 125.0f |
| AirSteering | 0.22f |
| AirAccelerationLimit | 450.0f |
| ChainJumpBonus | 65.0f |

Speeds/accelerations/distances use cm, cm/s, cm/s²; durations seconds; FOV degrees. Existing paces stay150/350/600, normal jump500.

### Controls and animation at this checkpoint

- Advanced on: LeftAlt/left bumper dash; LeftControl/gamepad face-right slide (slow crouch does nothing); CapsLock walk toggle; Shift sprint; Space/gamepad face-bottom jump and contextual extra/wall/slide/dash jump; V camera; C cycle; Esc menu. No new pad sprint binding. Advanced off: Ctrl original walk toggle; added Alt/Caps/pad actions inert. Physical input dispatch has not been exercised by the scripted ability calls. The existing pause-menu help still says Ctrl=walk; changing that existing file is outside the allowed hooks and remains a UI follow-up.
- Champion verified clips: `MM_Jump_Champion`, `MM_Fall_Loop_Champion`, `MM_Land_Champion`; dash uses ordinary locomotion/air path; extra/wall jumps request Jump DefaultSlot overlay; slide holds Jump0.52s with32cm mesh drop; mantle currently looks like an upright standing/locomotion pose. Existing per-hero roster chooses clips; no new clip asset installed. Sparrow keeps Jump_Start/Jump_Apex/Jump_Land.
- Needed: proper per-hero dash, crouch, slide, mantle clips, plus visual validation of extra/wall overlays across the roster. No retargeting/migration started.
- Feel limitations: slide is a frozen tucked jump pose; mantle is an upright scripted lift; Champion stop clip offset remains outside slide; screenshot stalls affect exact action/capture timing. Advanced gameplay has only been individually captured with Champion; no claim of all-hero ability polish.

### Disabled Champion regression — 22:17 UTC

`s2-disabled-champion` exited normally after all21 screenshots. Reviewed `session-2/champion-disabled.jpg` against `session-1/champion-before.jpg`: walk/run/sprint framing and locomotion match, speeds150/350/600 and the same source loops. Timing-dependent stop/pivot imperfections remain; no pixel-identical claim. HUD absent, native SeleneSecondaryAnimInstance and13 Kawaii chains active with nonzero swing. Comparison samples are in `session-2/disabled-comparison.json`. Sparrow disabled regression is running; full-roster stage is built but not yet launched.

### Preservation and remaining integration checks

Entry3313 Content files all retain size/mtime; config and secondary-animation source hashes match entry. The movement generator created only `Content/Selene/Maps/MovementTest.umap`. The final inventory also found five new fox-spirit assets outside the movement scope; this session did not generate/copy/edit them. Their metadata is recorded in `session-2/unattributed-new-assets.json`; they were left untouched. Do not misreport those additions as this session movement output.

The complete combined seven-stage sequence is still missing, so accepted isolated stages do not prove final combined chaining (especially after automatic mantle was added). Full-roster cycling/Angel Kawaii with advanced movement enabled and real keyboard/gamepad dispatch remain unverified. No commits, browser, downloads, paid work, DefaultEngine edits, existing-asset edits, or unaccepted AnimMatch patch reapplication.
