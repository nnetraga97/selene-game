# Animation runtime review

Written 2026-11-19. Scope: why Selene's movement and combat still look unrefined even with studio-grade clips, which outside clip sources were looked at, and a proposed direction. Everything under "Structural limits" was checked by reading the code on 2026-11-19. Section 3 is a **proposal that has not been approved and nothing in it has been built**.

## 1. Structural limits of the animation runtime

The clips (GASP, Paragon Aurora) are not the bottleneck. The thing that plays them is. Selene already has locomotion transitions, a strafe blend space, an upper-body slot, melee combos, flinches, turn-in-place, dashes and abilities; the limits below are about how those are built.

- **Locomotion is a hand-written C++ state machine over `UAnimSingleNodeInstance`**, which plays one asset at a time (`ASeleneCharacter::UpdateSingleNodeAnimation`, `Source/Selene/SeleneCharacter.cpp`). Gait changes at 250 and 475 cm/s (`ChooseGroundLoop`) swap the asset, reset it to frame 0, and cover the switch with a pose-snapshot crossfade (`FSeleneSnapshotBlend` in `Source/Selene/Animation/SeleneSecondaryAnimInstance.cpp`). Walk, run and sprint are separate clips that are not phase-synced, so the feet can jump at a gait change.
- **Speed matching is play rate, not stride warping.** `ChooseGroundLoop` scales play rate by `Speed / ClipSpeed`, clamped to 0.5-1.5. Outside that range, or between measured clip speeds, feet slide or the clip looks slowed or sped up.
- **Starts, stops and pivots are full-body overlay montages** played on `DefaultSlot` by `UpdateLocomotionTransitions` when input starts, stops or reverses. There is no distance matching, so the deceleration baked into the clip and the capsule's actual deceleration are unrelated.
- **Strafing is a raw direction blend.** In combat stance the `StrafeLocomotion` blend space is driven by velocity direction relative to the actor and move speed is pinned to the blend space's max (`ApplySpeed`, `Source/Selene/SeleneCharacterCombat.cpp`). There is no orientation warping, so directions between the authored ones blend two legs cycles rather than rotating one.
- **Melee timing and hit detection are loose.** The hit lands on a timer set to `AttackHitFraction` x clip length (`Attack`, `SeleneCharacterCombat.cpp`; fractions in `Config/DefaultGame.ini`). `MeleeStrike` tests a cone from the actor's forward vector (`GatherCone`), not a sweep along the weapon, so the damage does not follow the visible blade. The step-in is a flat 260 cm/s added to velocity, skipped only when an enemy is already within 0.7 of reach.
- **Missing procedural layers.** A search of `Source/Selene` found no foot IK or foot placement, no lean, no aim offset and no landing additive (landing is a plain clip, `Land` / `LandMoving`).
- **The Mixamo-rigged heroes have no root bone; the hips are the root.** `docs/ANIM-MATCH-PROGRESS.md` records this for Fixer and Courier and says the other non-Sparrow heroes also disable Root Motion for the same reason. It is behind several workarounds, such as `ANIM_FIRST_FRAME` root locking and the normalized transition clips in `AnimMatchS3`, and it blocks root-motion-based techniques.

What does work, so it is not redone: the masked upper-body slot with a spine gradient (0.35 / 0.7 / 1.0) and `LegWeight` (`FSeleneUpperBodySlot`), input buffering and hit pause, directional hit-react flinches (`ReceiveDamage`), turn-in-place (`TickTurnInPlace`) and directional dash clips (`TickActionLayer`).

## 2. External clip sources investigated and not adopted

- **toyxyz RGB MoCap** (https://github.com/toyxyz/toyxyz_RGBMocap): a video-to-animation app that retargets to Mixamo FBX, VRM and PMX. It is Windows plus NVIDIA only. The app code is MIT, but its best models (ExMR, GVHMR, PromptHMR, MAMMA) and the SMPL body models are research or non-commercial licensed. It was **not run**: the project has been built on a Mac, so it cannot run on the current machine. Not adopted.
- **Mixamo (Adobe):** an auto-rigger plus a library of roughly 2,500 clips. Download is manual only (no API) and the rigs are hips-as-root. It would help with breadth (emotes, NPC idles) but not with movement or combat, because its clips feed the same playback path described above. Not adopted for that purpose.
- **Conclusion:** the clip sources already in use (GASP, Paragon) are fine. More clips would not fix the look; the playback runtime is the limit.

## 3. Proposed direction (UNAPPROVED PROPOSAL, under discussion, nothing built)

A Paragon/Lyra-style layered animation graph rather than GASP motion matching:

- speed blend driven by sync markers, with stride warping
- orientation warping for strafing
- distance-matched starts and stops
- foot placement, lean and landing additives
- mesh-space upper-body blend with an aim offset
- data-driven melee: startup, active and recovery phases, weapon-socket sweeps, and motion warping to the target
- inertialization for transitions

Foundations it would need first:

1. Add a root bone to the Mixamo-rigged heroes.
2. Add a foot-slip metric (planted-foot world speed per gait and direction), built from the existing capture harnesses (the `anim_match_*` and movement harnesses under `Tools/Unreal`), so any change can be measured.

**How this differs from `docs/research/movement-animation-plan.md`.** That plan (2026-11-09) recommends GASP motion matching in a new project. This proposal keeps it inside Selene, with a layered graph instead of motion matching, for two reasons: lanes and combat have since been built in Selene (see `STATUS.md`), and the GASP route costs a hidden source mesh plus a runtime retarget for every hero and bot.

**Open questions for the user:**

1. Is Selene the game, or the pre-project demo?
2. Can the editor MCP plugin author animation blueprints? This is unverified.
3. Locomotion first, or melee first?
