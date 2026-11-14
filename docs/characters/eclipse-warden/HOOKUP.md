# Eclipse Warden: first hookup (2026-11-13)

Draft playable hero "Warden" (roster entry after Base). Not committed.

## Sources (user-generated in Tripo Studio, downloaded 2026-11-13)
- Body: `female figure 3d model.glb`: 49,088 triangles, UE5 Mannequin rig (80 bones), 4K colour map only.
- Cuirass: `chest armor 3d model.glb`: 14,674 triangles, 2K colour, normal and roughness/metal maps.
- Sword: `ornate fantasy sword 3d model.glb`: 47,625 triangles, 4K colour map only.

## Blender build
Scripts and files: `game-asset-workflow/work/repairs/eclipse-warden/` (`fix.py`, `build.py`, `pose2.py`, `warden_assembled.blend`).
1. Knee and elbow weight blends rebuilt (`fix.py`); see `rig-eval/`.
2. Studio wrapper nodes folded in; scale baked to 1.74 m.
3. Cuirass scaled to the torso (x 0.379, y 0.407, z 0.313 of the normalised download), weights copied from the body and limited to spine_03–05. Body vertices under the armor pulled 4–14 mm inside it (1,173 vertices, at most 3.6 cm).
4. Sword scaled to 0.95 m and skinned to a new `weapon_r` bone under `hand_r`, grip at the palm.
5. Joined into one mesh: 111,387 triangles, 3 materials, 81 bones, at most 4 influences.

## Pipeline and Unreal
- Asset `eclipse-warden`, run `20261114T061533-6b1fa3` (mechanical pass), delivered as a draft to `SourceArt/Assets/eclipse-warden/`.
- Imported to `/Game/Assets/eclipse-warden/`: 1.74 m, one skeletal mesh.
- `Tools/Unreal/warden_{retarget,measure,roster}.py` and `warden_run.sh` (copies of the Base scripts): IK rig, retargeter, 15 GASP clips, three toon material instances, roster line and cook directories in `Config/DefaultGame.ini`.
- Loop speeds: walk 207.6, run 522.2, sprint 731.6 cm/s.
- Capture: `Saved/WardenHookup/capture1/` (21 images: idle, walk, run, sprint, stop, pivot, jump).

## Known gaps
- Hand stays open around the sword (shared unarmed clips).
- Sword is 9x and cuirass 1.5x their triangle budgets; the sword is not the Eclipse design.
- Toon material uses colour only; the cuirass normal and roughness maps are imported but unused.
- Bald; bikini still on the body; build is slim.
- No slide clips; no close-range engine review of knees and elbows yet.
- Shoulder clips the armhole trim slightly with the arm forward; armpit texture is smeared.

# Warrior: second hookup (2026-11-13)

User-generated Tripo "fantasy warrior" with Tripo Auto Rig (UE5 Mannequin preset, 80 bones), one fused mesh, 48,156 triangles, one 4K colour map. Roster entry "Warrior" (after Base). Not committed.
- Blender (`game-asset-workflow/work/repairs/eclipse-warrior/prep_champ.py`): wrapper nodes folded, root centred, scaled to 1.88 m including hair and heels. No weight edits.
- Pipeline asset `eclipse-warrior`, run `20261114T063027-9f6e01`, delivered as a draft; imported to `/Game/Assets/eclipse-warrior/` at 1.88 m.
- `Tools/Unreal/warrior_{retarget,measure,roster}.py`, `warrior_run.sh`. Speeds: walk 210.6, run 535.1, sprint 747.4 cm/s.
- Capture: `Saved/WarriorHookup/capture1/` (21 images). Pose tests and captures: `docs/characters/eclipse-warden/warrior/`.
- Known: knee plate crumples at a 90 degree bend; pauldron stretches when the arm lifts; ponytail is rigid (no physics chain); no slide clips.

## Warrior sword (2026-11-13)
- `add_sword.py` (in `game-asset-workflow/work/repairs/eclipse-warrior/`): the user's ornate sword scaled to 1.05 m, skinned to a new `weapon_r` bone under `hand_r`, grip in the right palm. 95,781 triangles, 2 materials, 81 bones.
- Pipeline candidate run `20261114T064017-14459e` (fails only the 60k-triangle and 1-material limits set before the sword), delivered as a draft with `--replace`, re-imported in place. Existing retargeted clips still bind to the skeleton.
- `Tools/Unreal/warrior_sword_material.py` made `MI_Toon_Warrior_Sword`; roster `SlotMaterials` now lists both slots. Capture: `Saved/WarriorHookup/capture-sword/`.
- Not done: no attack input or sword animations exist in the project (only the Mannequin unarmed attacks). Waiting on a Paragon sword hero from Fab (Aurora preferred, Greystone alternative) to retarget from. Fingers are not yet closed on the grip.

## Warrior sword animations from Paragon Aurora (2026-11-13)
- `Content/ParagonAurora/` copied from the Epic vault cache (2.7 GB, untracked), the same as "Add to Project".
- `Tools/Unreal/warrior_aurora_retarget.py`: `IK_Aurora` (FK chains, pelvis retarget root), `RTG_Aurora_To_Warrior`, 21 clips to `/Game/Selene/Characters/Warrior/Anims/Aurora/` with the root locked. Jog stance speed 443.2 cm/s.
- `Tools/Unreal/warrior_aurora_curves.py`: loads those clips in the editor so their curve names are saved on the Warrior skeleton. Without it `-game` crashes in `UAnimSequenceBase::PostLoad` (curve metadata opens an editor transaction).
- Roster: IdleLoop, RunLoop (+speed), RunStart, RunStop, RunPivot, Jump, FallLoop and Land now use Aurora's clips; `Attacks` = Primary_Attack_A/B/C. Walk and sprint are still the unarmed GASP clips. Previous line: `Saved/WarriorHookup/Warrior-roster-line-before-aurora.txt`.
- Code: roster field `Attacks`; `ASeleneCharacter::Attack` (combo on DefaultSlot, a press during a swing queues the next); left mouse and gamepad right trigger; debug `selene.AutoAttack <seconds>` and `selene.AutoAttackYaw`. Built with `Build.sh SeleneEditor Mac Development`.
- Evidence: `Saved/WarriorHookup/attack2/` (69 attacks logged, 253 screenshots in `Saved/AutoShots/`), `Saved/WarriorHookup/capture-aurora/` (21 images).
- Open: she keeps moving if you attack while running (feet slide); no hit detection, damage or effects; abilities Q/E/R and the fast attacks are retargeted but not bound; walk and sprint don't carry the sword properly.
