# Selene status

Current as of 2026-11-19 (animation and roster statements re-verified against the code; other sections last reviewed 2026-11-07). This is a concise status page, not a replacement for the linked progress records.

## Done / available

- **Playable roster:** Champion, Angel, Sparrow, Fixer, Courier, Fox (Lysara), Wanderer, Ysolde and Base are playable, and Nerine is an NPC, all configured in `Config/DefaultGame.ini`. The roster also now has Warrior (the default character), Warden and Aurora, melee heroes with sword sets: Warrior and Warden use Paragon Aurora clips retargeted by `Tools/Unreal/combat_anims.py`, while Aurora plays the Paragon clips on her own mesh. Ysolde is installed as a UE5-Mannequin-rigged playable hero; her capture review found mesh-quality limitations rather than a failed hookup. Base (bald reusable base body) is a playable draft. Nerine (first modular build: body plus hair, jacket and skirt) is now a non-playable NPC (`bPlayable=False`) standing in the plaza near the start, spawned from `Npcs` in `Config/DefaultGame.ini`. Every hero has the GASP knees-out slide (into, loop, out to run or stand). C opens a numbered hero picker (1–9/0, click, or arrows + Enter).
- **Animation runtime (live in C++):** `ASeleneCharacter::UpdateLocomotionTransitions` (`Source/Selene/SeleneCharacter.cpp`) plays start, stop and pivot clips on `DefaultSlot`. Combat stance drives a directional strafe blend space (`StrafeLocomotion`) in `UpdateSingleNodeAnimation`. `FSeleneUpperBodySlot` (`Source/Selene/Animation/SeleneSecondaryAnimInstance.cpp`) is a masked upper-body slot with a spine gradient (0.35 / 0.7 / 1.0) and a `LegWeight` control. `Source/Selene/SeleneCharacterCombat.cpp` has melee combos with input buffering, hit pause, camera shake, directional hit-react flinches (`ReceiveDamage`), turn-in-place (`TickTurnInPlace`), dash clips (`TickActionLayer`), abilities, and death/respawn. Whether it looks right in play has not been re-captured; see the structural limits below.
- **Character rendering:** `M_Character_Toon` was rebuilt from the Substrate Toon BSDF to a standard-lit Substrate Slab with a rim term. The prior material versions are retained in `Content/Selene/Materials/Character/Backup_ToonBSDF`.
- **Movement/UI:** advanced movement has accepted isolated mechanics in `docs/MOVEMENT-PROGRESS.md`. Current controls include Shift dash/sprint, M for the top-down map, F for the FPS counter, and the pause-menu control text in `Source/Selene/SSelenePauseMenu.cpp`.
- **TownV2 foundation:** sessions 1–5 established the Kailua-Kona site, a built and walk-tested town map, and a tightened plaza/shop-frontage checkpoint. The reports explicitly do not claim final visual quality or packaged-performance proof.
- **New imported buildings:** seaside guesthouse, lighthouse house, boathouse, art-deco tower, and six `metro-*` buildings are present under `Content/Assets/`.

## In progress

- **TownV2 is live.** Sessions 6 and 7 are running: session 6 places the seaside building set, and session 7 previews the city-building cluster. Their scope is in `TOWN-V2-BRIEF.md`; do not treat a result as accepted until it appears in `TOWN-V2-PROGRESS.md`.
- **Animation polish remains open.** The transition and combat hookup is now in C++ (see Done), but `ANIM-MATCH-PROGRESS.md` and `CLIPS-PROGRESS.md` are older records and have not been updated to say so; continuous foot-sliding has no measurement. The GASP migration remains a plan/controller setup, not a completed migration.
- **Character polish remains open.** Sparrow's weapon concern is unresolved; Fox, Wanderer, and Ysolde have retained playable checkpoints with explicitly documented visual limitations.

## Known issues / limits

- TownV2's accepted session-5 report still calls out incomplete plaza enclosure, repeated shells, broad foreground paving, imperfect doorway/storey proportions, and sparse outskirts. FPS figures there are indicative offscreen samples, not packaged GPU performance.
- **Nerine (NPC):** the bald side was fixed in session 3 (hair cap centred; scalp and baked stubble recoloured to the cap colour; run `20261107T111329-cbeedd`). Skirt clipping at stride and underarm strips remain; she now only idles, so they rarely show. A v2 rebuilt on the base body was tried and deleted: it was no better.
- Ysolde needs a separately authorized mesh/weight repair for coat-to-boot clearance, trouser/crotch deformation, and close-up idle fingers. Wanderer lacks an authorized crouch clip and retains skirt/knee visual limitations. Fox retains visible knee/armour and transition limitations.
- **Animation runtime limits** (detail and a proposed direction in `docs/research/animation-runtime-review.md`): locomotion is a hand-written state machine over `UAnimSingleNodeInstance`, one asset at a time. Gait changes at 250 and 475 cm/s swap the asset, restart at frame 0 and hide it with a pose-snapshot crossfade; walk, run and sprint are not phase-synced. Speed matching is play rate clamped to 0.5-1.5 (`ChooseGroundLoop`), not stride warping. Starts, stops and pivots are full-body overlay montages triggered on input edges, with no distance matching. Strafing is a raw direction blend with no orientation warping. The melee hit lands on a timer (`AttackHitFraction` x clip length), tests a cone from actor forward rather than a weapon sweep, and the step-in is a flat 260 cm/s velocity add. There is no foot IK, lean, aim offset or landing additive. The Mixamo-rigged heroes have no root bone (hips are the root), behind several workarounds.
- Advanced movement's isolated mechanics are not the same as whole-roster, real-input, complete-animation acceptance. The progress record identifies outstanding combined-sequence and animation-polish checks.
- No allowed offline scan can prove a Content asset is absent from an Unreal map. The cleanup plan therefore does not mark Content assets for deletion without a permitted map-reference check.

## Next steps

1. Let TownV2 sessions 6/7 finish and append their evidence before deciding on visual/placement follow-up.
2. Decide the animation direction (open proposal in `docs/research/animation-runtime-review.md`, not approved); until then, scope any animation task narrowly and do not reapply rejected/archived patches.
3. Obtain approval before any Ysolde, Wanderer, or Fox mesh/weight repair.
4. Use `docs/CLEANUP-PLAN.md` only after all Selene sessions are idle. Its script is written but deliberately has not been run.

See `docs/INDEX.md` for the status of every document and `docs/INTERVENTION-LOG.md` for the decision history.
