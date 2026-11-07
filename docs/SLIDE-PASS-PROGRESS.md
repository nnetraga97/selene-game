# GASP slide pass progress

## 2026-11-07 session 1 — checkpoint at 10:43 UTC (work ongoing)

- Read SLIDE-PASS-BRIEF, GASP-INTEGRATION and existing gasp export/import/retarget/in-place/session/capture tooling first. No commits, browser, paid generation, mesh/retargeter edits or dash changes.
- Exported the four Neutral KneesOut clips in memory through GASP's existing UEFN→Manny retargeter. FBX receipts/hashes: `Saved/SlidePass/session-1/export.json`; no GASP packages saved.
- Imported four new Manny clips, stripped source root XY travel, and created 40 hero clips beside each hero's current GASP locomotion clips with existing retargeters (Fixer/Courier use their existing Facing variants). All clips use force_root_lock + REF_POSE, root motion disabled. Source/hero reloads: `source-reload.json`, `retarget.json`, `measure.json` in that directory.
- One import script dependency-iteration error occurred AFTER all four source assets were saved. Fixed the null dependency handling and reconciled/reloaded those saves with `slide_verify.py`; did not replay import/export. `import.json` retains the original failed stage receipt.
- Added four optional roster fields; appended only these fields to the ten requested existing roster lines. Non-slide config contents byte-equivalent after stripping added fields. Manny is the optional legacy entry, outside the ten named heroes.
- Added Into→Loop→Out slot handling, 0.55–1.25 s Into window based on source hip-height measurements, input/speed exit selection, falling blend-out and legacy fallback. Physics and dash functions unchanged. Initial and current builds succeeded (`build-initial.log`, `build.log`).
- First 156 offscreen native-slot sampled captures complete. Contact sheets: `slides-side.jpg`, `slides-front.jpg`, `slides-all-heroes.jpg`, `regression.jpg` under `Saved/SlidePass/session-1/`. These are diagnostic poses, NOT live CMC or continuity proof.
- Sol round 1 (`openai/gpt-6.1-sol`): **not ready**; five hips-root heroes float, Fixer/Courier also lose heading. Five real-root heroes reach the ground. Panel-cited verdict: `Saved/SlidePass/session-1/sol-review.md`.
- Applying exactly one recommended correction: slide-only mesh transform compensation recovering hips-root authored height AND orientation relative to reference, with horizontal pelvis travel pinned and all required asset flags retained. This modifies only movement-component animation behavior. Build passed; round-2 captures pending.
- At 10:43 UTC another worker began a Selene `UnrealEditor-Cmd` import of Nerine v2. Our capture launcher refused to run. Did not kill/close it or take its lock; waiting and preserving concurrent edits.

Remaining acceptance: corrected capture review; live Into/Loop/Out and early/falling exits; no phase/T-pose flashes; moving exit continuity; matched locomotion regression. Exact immediate next step: once the other editor exits, run `SELENE_SLIDE_SESSION=session-2 SELENE_SLIDE_COMPENSATE=1 bash Tools/Unreal/slide_run.sh capture`, then `swift Tools/Unreal/slide_sheets.swift session-2`, and obtain Sol's second/final review. Stop on repeated diagnosed failures or by about 10:56 UTC.

### 10:46 UTC update

The other worker's import/retarget commandlets exited normally. Round-2 offscreen capture acquired the shared lock and started. Compensation now uses the authored root transform relative to the mesh reference transform (height + orientation), with authored horizontal pelvis travel pinned. Static capture calls the same native compensation helper. The capture harness does not exercise the runtime smoothing, capsule physics or Out ownership.

Source inspection identifies an additional acceptance risk to test before declaring delivery: `ASeleneCharacter::UpdateSingleNodeAnimation` skips locomotion updates only while the CMC is physically sliding. After `StopSlide`, a later base-loop switch calls `SetAnimationAsset` and may cancel the Out montage. The movement component preselects the immediate exit base loop, but this does not prove that the Out survives subsequent speed-threshold/input changes. `SeleneCharacter.cpp` is outside this brief's edit allowlist and was not changed.

### 10:49 UTC verified corrected-pose checkpoint

- Second capture pass succeeded: 156/156 native DefaultSlot panels. Corrected contact sheets are `Saved/SlidePass/session-2/slides-all-heroes.jpg`, `slides-side.jpg`, `slides-front.jpg`, and `regression.jpg`.
- Sol round 2/final: **sampled pose compensation passes for all ten; full acceptance pending runtime**. Floating and Fixer/Courier heading loss resolved. Full panel-cited notes: `Saved/SlidePass/session-2/sol-review.md`. No third review/correction round.
- Measured corrected loop hip height is 18.8–22.6 cm for all ten. Both rounds used the same source clips and required asset flags; no FootOut substitution.
- Matched static regression: all 16 Ysolde/Sparrow side/front walk/run/sprint/jump samples have 0 cm measured hip/knee displacement before/after correction. Sol finds matching silhouettes at sheet scale. PNGs are not byte-identical; this is sampled pose evidence, not a full live locomotion regression. Receipt: `Saved/SlidePass/session-2/regression-comparison.json`.
- Concurrent `NerineV2` roster addition is preserved and was not assigned slide fields by this pass (the brief names ten existing heroes).
- Live PIE exit probe attempt 1 reached Champion selection but failed before movement because Python exposes the movement component through `get_component_by_class`, not `get_character_movement`. Saved failed receipt/log under `runtime-probe-attempt1*`; corrected this clear script error once and launched attempt 2. No gameplay action was replayed from the first attempt.

## Final checkpoint — 2026-11-07 10:51 UTC (about 20 minutes)

**State: partial.** Assets, compiled animation code, corrected sampled poses and two Sol reviews are complete. Full gameplay slide acceptance is blocked by the existing locomotion update outside the allowed file list.

Live PIE probe attempt 2 completed successfully and exited normally (`Saved/SlidePass/session-2/runtime-probe.json`, `runtime_probe-editor.log`). It recorded 396 samples:

| Event | Time | Speed | Evidence |
| --- | ---: | ---: | --- |
| TrySlide accepted | 1.211 s | 600.0 cm/s | Custom movement 2; Into montage at clip time 0.55 |
| Into → Loop | 1.928 s | 481.7 cm/s | `M_Neutral_Slide_KneesOut_Loop_Champion` active |
| StopSlide / moving Out | 2.309 s | 422.9 cm/s | Out_Moving_Run active; base RunLoop |
| Out canceled | 2.338 s | 481.6 cm/s | No montage; base switched to SprintLoop |

The moving exit lasts only about **0.029 s** before `ASeleneCharacter::UpdateSingleNodeAnimation` calls `SetAnimationAsset`. This is a diagnosed gameplay failure, not a visual-quality pass. No attempt was made to edit the prohibited character file or hide the failure. Stand exit, ledge/falling exit and dense transition captures remain unverified.

**Exact next step:** authorize the narrow additional edit to `Source/Selene/SeleneCharacter.cpp` so its single-node locomotion update preserves slide animation ownership through the active Out montage (using a movement-component animation-state query, without changing physical `IsSliding`). Then rerun the live threshold-crossing probe, add stand/falling exits, and record continuous side/front per-hero transition captures. Preserve all accepted assets and both existing capture rounds; do not repeat import/retarget. `slide_runtime_probe.py` refuses an existing receipt: use a new evidence directory/report for the next run.

Verification retained:

- 4 new Manny source clips + 40 hero clips; all 44 asset hashes match the first checkpoint.
- `Build.sh SeleneEditor Mac Development` succeeded after the compensation change; `Saved/SlidePass/session-2/build-compensation.log`.
- Two complete 156-panel rounds; all-ten contact sheet at `Saved/SlidePass/session-2/slides-all-heroes.jpg` with detailed side/front sheets beside it.
- Sol final: sampled compensation passes; runtime acceptance pending. After that final review the live probe established the cancellation above. No third Sol round.
- Sixteen matched static Ysolde/Sparrow regression samples show 0 cm measured hip/knee deltas; visual silhouettes match at sheet scale. This does not certify full live regression or every bone.
- All ten original roster lines preserve their non-slide fields; concurrent NerineV2 line is preserved. No existing character content was modified by the slide pass. Source comparison confirms TryDash, FinishDash, PhysCustom and PhysSlide bodies unchanged.
- Initial preexisting DefaultEngine.ini edits were left alone. No commits. No paid or externally published action was performed. Own Unreal sessions ended and their lock was released.

## Exit fix — 2026-11-07 (Claude)

Diagnosed cancel: `ASeleneCharacter::UpdateSingleNodeAnimation` swapped Run→Sprint loop 0.029 s into the moving Out clip, cancelling DefaultSlot.
Fix: `USeleneMovementComponent::IsSlideExitPlaying()` (true while the Out montage is active; cleared in `TickSlidePose` when it ends or on a falling exit), and the locomotion update now also yields while it is true.
Build succeeded. Live probe re-run (`Saved/SlidePass/session-2/runtime-probe.json`; previous receipt kept as `runtime-probe-before-exitfix.json`): Into 1.208 s → Loop 1.920 s → Out_Moving_Run 2.301 s, still playing at 1.50 s clip time when the probe ended at 3.81 s. No cancel.
Not verified: standing exit and ledge/falling exit live; Out clip length feel in play. NerineV2 has no slide clips (falls back to the old stand-in).
