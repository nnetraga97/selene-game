# Selene status

Current as of 2026-11-07. This is a concise status page, not a replacement for the linked progress records.

## Done / available

- **Playable roster:** Champion, Angel, Sparrow, Fixer, Courier, Fox (Lysara), Wanderer, and Ysolde are configured in `Config/DefaultGame.ini`. Ysolde is installed as a UE5-Mannequin-rigged playable hero; her capture review found mesh-quality limitations rather than a failed hookup.
- **Character rendering:** `M_Character_Toon` was rebuilt from the Substrate Toon BSDF to a standard-lit Substrate Slab with a rim term. The prior material versions are retained in `Content/Selene/Materials/Character/Backup_ToonBSDF`.
- **Movement/UI:** advanced movement has accepted isolated mechanics in `docs/MOVEMENT-PROGRESS.md`. Current controls include Shift dash/sprint, M for the top-down map, F for the FPS counter, and the pause-menu control text in `Source/Selene/SSelenePauseMenu.cpp`.
- **TownV2 foundation:** sessions 1–5 established the Kailua-Kona site, a built and walk-tested town map, and a tightened plaza/shop-frontage checkpoint. The reports explicitly do not claim final visual quality or packaged-performance proof.
- **New imported buildings:** seaside guesthouse, lighthouse house, boathouse, art-deco tower, and six `metro-*` buildings are present under `Content/Assets/`.

## In progress

- **TownV2 is live.** Sessions 6 and 7 are running: session 6 places the seaside building set, and session 7 previews the city-building cluster. Their scope is in `TOWN-V2-BRIEF.md`; do not treat a result as accepted until it appears in `TOWN-V2-PROGRESS.md`.
- **Animation/transition work remains open.** `ANIM-MATCH-PROGRESS.md` retains accepted facing work but has unverified transition/continuous-foot-sliding work. `CLIPS-PROGRESS.md` has a verified slot probe but not a completed in-game C++ hookup. The GASP migration remains a plan/controller setup, not a completed migration.
- **Character polish remains open.** Sparrow's weapon concern is unresolved; Fox, Wanderer, and Ysolde have retained playable checkpoints with explicitly documented visual limitations.

## Known issues / limits

- TownV2's accepted session-5 report still calls out incomplete plaza enclosure, repeated shells, broad foreground paving, imperfect doorway/storey proportions, and sparse outskirts. FPS figures there are indicative offscreen samples, not packaged GPU performance.
- Ysolde needs a separately authorized mesh/weight repair for coat-to-boot clearance, trouser/crotch deformation, and close-up idle fingers. Wanderer lacks an authorized crouch clip and retains skirt/knee visual limitations. Fox retains visible knee/armour and transition limitations.
- Advanced movement's isolated mechanics are not the same as whole-roster, real-input, complete-animation acceptance. The progress record identifies outstanding combined-sequence and animation-polish checks.
- No allowed offline scan can prove a Content asset is absent from an Unreal map. The cleanup plan therefore does not mark Content assets for deletion without a permitted map-reference check.

## Next steps

1. Let TownV2 sessions 6/7 finish and append their evidence before deciding on visual/placement follow-up.
2. Resume transition inspection and the real gameplay integration only under a scoped animation task; do not reapply rejected/archived patches.
3. Obtain approval before any Ysolde, Wanderer, or Fox mesh/weight repair.
4. Use `docs/CLEANUP-PLAN.md` only after all Selene sessions are idle. Its script is written but deliberately has not been run.

See `docs/INDEX.md` for the status of every document and `docs/INTERVENTION-LOG.md` for the decision history.
