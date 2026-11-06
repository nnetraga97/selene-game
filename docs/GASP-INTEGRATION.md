# GASP integration plan for Selene

Investigation date: **2026-11-06**. Installed sample/engine inspected: **UE 5.8.4-58902052+++UE5+Release-5.8**. This is a read-only investigation and implementation design, not a completed integration. This investigation created only this document in Selene. It migrated no assets, changed no gameplay code or configuration, and made no commits. Other work was running concurrently; the final-state note below distinguishes its changes from this investigation.

## Recommendation

**Choose A: preserve `ASeleneCharacter`, with one correction: use a hidden UEFN mannequin as the animation source, not Manny.** Put a Selene-owned copy of `SandboxCharacter_CMC_ABP` on the inherited `GetMesh()`, implement the sample pawn interface in a Blueprint child of `ASeleneCharacter`, and animate a separate Champion/Angel skeletal mesh through runtime IK retargeting. Retain Selene's controller, cameras, roster commands, pause menu, and perf pawn type.

The installed GASP CMC AnimBP targets `/Game/Characters/UEFN_Mannequin/Meshes/SK_UEFN_Mannequin`; its pawn uses `SKM_UEFN_Mannequin`. Manny is itself a **retargeted visual override** in this sample. Assigning that AnimBP directly to Selene's Manny or Mixamo meshes is not a verified solution. A literal UEFN → Manny → Mixamo chain could reuse the old retargeters but adds a mesh evaluation, another retarget pass, and error accumulation; use direct UEFN → Mixamo retargeters instead.

The measured unmodified migration roots reach **2,861 `/Game` packages / 4,702.55 MB**. The recommended smaller starting roots reach **1,188 packages / 1,079.06 MB**. After the explicitly listed reference edits, the modeled closure is **1,157 packages / 1,046.33 MB** with no traversal animation packages, MetaHumans, sample Mover pawn, traversal component, or Smart Object assets. **The latter is a calculated target based on current file sizes, not a verified post-edit migration.** Compilation, a fresh registry scan, and runtime foot-contact checks are implementation acceptance gates.

## Evidence and reproduction

Raw scripts, logs, JSON, and text exports are under **`/tmp/gasp-investigation/`**. These are temporary artifacts; preserve them separately if this investigation needs a permanent audit trail. Key files:

- `assets.json`, `dependencies.json`, `hard-dependencies.json`: AssetRegistry inventory and recursive hard/soft package dependencies, including dependencies beyond `/Game`.
- `closure-full.json`, `closure-full-hard.json`, `closure-abp.json`, `closure-core-unmodified.json`, `closure-core-proposed.json`: exact roots, package manifests, file bytes, folder totals, and external dependencies.
- `proposed-reference-cuts.json`, `prune.py`: every hypothetical dependency edge removed and the corresponding required asset edit. Nothing was actually removed from GASP.
- `*_parsed.json`, `*-overview.json`, `*-summary.txt`, and `_Game_*.t3d`: exported Blueprint graphs, pins, defaults, interfaces, structs, choosers, databases, and retarget assets. Some T3D exports use UTF-16; `analyze.py` detects the encoding.
- `component-info.json`, `component_*.t3d`: actual Blueprint component templates collected with `SubobjectDataSubsystem`, in addition to native CDO components. CDO `None` entries for Blueprint-created components do **not** mean the components are absent.
- `plugins.json`, `module-plugins.json`, `core-plugin-closure.json`, `api.json`, `api2.json`, `blueprint-api-source.txt`: installed plugin descriptors and verified editor scripting API availability.
- `inspect.py` through `inspect4.py`, `editor-{1,2,3,4}.log`, `complete3.json`, `exports4.json`: commandlet evidence. Launch 1 completed. Launch 2 hit an exporter assertion when passed an object that did not load; launch 3 guarded null objects, reused completed exports, and completed successfully. Launch 4 successfully exported the source post-process AnimBP, mesh, and a shared animation/database for a final dependency check. That earlier exporter failure is not an integration build failure.
- `baseline.json`, `git-before.txt`, and the final `verification.json`: file-change checks.

Before **each** launch, `pgrep -f 'UnrealEditor.*GameAnimationSample'` returned no process; the results were saved in `prelaunch*-pids.txt`. The invocation used was:

```sh
perl -e 'alarm 900; exec @ARGV' \
  '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd' \
  '/Users/nicknetraganti/Documents/Unreal Projects/GameAnimationSample/GameAnimationSample.uproject' \
  -run=pythonscript -script=/tmp/gasp-investigation/inspect.py \
  -unattended -nop4 -nosplash -nullrhi \
  -abslog=/tmp/gasp-investigation/editor-1.log
```

No save, migration, or asset-edit operation was invoked. All visual-quality claims remain untested: `-nullrhi` inspection cannot demonstrate foot planting, silhouette preservation, camera comfort, or performance.

## How GASP drives other skeletons

The relevant directory is **`/Game/Blueprints/RetargetedCharacters/`**, not a top-level `/Game/RetargetedCharacters/`.

| Asset | Verified role |
| --- | --- |
| `/Game/Blueprints/RetargetedCharacters/ABP_GenericRetarget` | Skeleton-independent retarget AnimBP. Its active output is `RetargetPoseFromMesh`, with `RetargetFrom=ParentSkeletalMeshComponent`; the export also contains a CopyPose node, but the compiled output uses retargeting. |
| `/Game/Blueprints/RetargetedCharacters/BP_Manny` | An **Actor**, not a pawn. Contains a Manny skeletal mesh with the generic retarget AnimBP and first component tag `RTG_UEFN_to_UE5_Mannequin`. |
| `/Game/Blueprints/RetargetedCharacters/BP_Quinn`, `BP_UE4_Mannequin`, `BP_Echo`, `BP_Twinblast` | Other visual-override actors. |
| `/Game/Blueprints/AC_VisualOverrideManager` | Actor component: `FindAndApplyVisualOverride` obtains the game mode's `VisualOverrides_Soft`, resolves the CVar choice, asynchronously loads the class, then `ApplyVisualOverride` changes the child actor class. |
| `/Game/Blueprints/GM_Sandbox` | Holds the soft visual-override roster. `CycleVisualOverride` cycles `DDCvar.VisualOverride`; `-1` denotes the no-override choice in its cycle logic. Its default pawn is **SandboxCharacter_Mover**, so do not migrate/use this game mode as Selene's default. |
| `/Game/Characters/UEFN_Mannequin/Rigs/IK_UEFN_Mannequin` | Source IK rig, with pelvis/root retarget settings, leg/arm goals, and full-body IK solver. |
| `/Game/Characters/UE5_Mannequins/Rigs/RTG_UEFN_to_UE5_Mannequin` | Demonstrates the source-to-Manny conversion. Other retargeters exist under the corresponding UE4, Echo, TwinBlast, and MetaHuman rig directories. |

The sample pawn contains a `ChildActorComponent` tagged **`VisualOverride`**, attached beneath the source mesh. The manager searches that tag, sets its child actor class, and hides/shows the attached parent according to whether an override class exists. Its visibility call does **not** propagate to children. `BP_Manny` adds a source-component tick prerequisite after a one-tick delay; its follower mesh ticks in `TG_PostPhysics`. The source uses `AlwaysTickPoseAndRefreshBones`.

`ABP_GenericRetarget` reads **component tag index 0**, looks it up in `IKRetargeter_Map`, loads the soft retargeter, copies its retarget profile, and updates profile settings from animation curves. Its own graph comment warns that no tag means no retargeting and asynchronous loading can yield a few T-pose frames. The map contains six sample retargeters, including two MetaHuman retargeters; migrating it unchanged pulls those references in. The visual manager's game-mode reference pulls in still more sample content.

This is a pose-source/follower arrangement, **not `SetLeaderPoseComponent` across different skeletons**. Champion and Angel need their own AnimInstances to evaluate runtime retargeting and later post-process physics. Attaching a mesh does not by itself establish a safe evaluation order; explicitly add the source tick prerequisite and verify same-frame motion.

For Selene, retain the architecture but author a small follower AnimBP per hero, or one verified skeleton-independent equivalent with an explicit retargeter property. Preload the mesh, AnimBP, retargeter, materials, and physics configuration before changing the visible character. This avoids the sample-wide tag map and preserves Selene's existing latest-request-wins async switching. If the generic sample is copied instead, replace its entire map with the intended roster, initialize the first tag before the AnimInstance, and eliminate the visible async T-pose window.

### Champion and Angel assets

Existing target rigs are `/Game/Selene/Characters/Champion/IK_Champion` and `/Game/Selene/Characters/Angel/IK_Angel`. Existing `RTG_Manny_To_Champion` / `RTG_Manny_To_Angel` must not be silently reconfigured; create **`RTG_UEFN_To_Champion`** and **`RTG_UEFN_To_Angel`** alongside them.

At the initial inspection, `Tools/Unreal/character_retarget.py` and `Saved/Characters/{Champion,Angel}/retarget.json` agreed on the target body's 21 chains and `mixamorig_Hips` retarget root. Concurrent Champion rebuilding later invalidated its success report; see the final-state note. The table describes the inspected body-chain mapping, not certification of the currently rebuilding rig. Examples:

| Chain | Mixamo target |
| --- | --- |
| Spine | `mixamorig_Spine` → `mixamorig_Spine2` |
| Neck / Head | `mixamorig_Neck` / `mixamorig_Head` |
| LeftLeg / RightLeg | `mixamorig_LeftUpLeg` → `mixamorig_LeftFoot`, mirrored on the right |
| LeftFoot / RightFoot | `mixamorig_LeftToeBase`, `mixamorig_RightToeBase` |
| LeftArm / RightArm | `mixamorig_LeftArm` → `mixamorig_LeftHand`, mirrored on the right |

The initially inspected operation stack enables Pelvis Motion, FK Chains, Run IK Rig, and Remap Curves, and disables **Root Motion**. There is no separate Mixamo root bone: blindly transferring source root motion to the hips previously caused an extra pelvis-height offset. Preserve that constraint when constructing the new retargeters, but verify pelvis translation and GASP's visual root-offset behavior together. Capsule movement remains CMC-owned. Fuzzy chain mapping and automatic pose alignment are starting points; inspect toes, leg goals, hands, and root explicitly. Do not assume source twist/metacarpal chains have target equivalents.

The supplied hero heights are 172 and 180 cm. Verify feet-at-ground placement and target proportions without scaling the hidden source to each hero. Angel's wings are additional visible geometry; inspect actual bone weights before assigning a wing physics chain. Runtime retargeting does not invent a flapping animation or missing wing bones.

## CMC pawn and AnimBP contract

`/Game/Blueprints/SandboxCharacter_CMC` derives directly from `/Script/Engine.Character` and implements `/Game/Blueprints/BPI_SandboxCharacter_Pawn`. Components verified from CDOs **and** construction-script templates:

- Native capsule, character mesh, CharacterMovement, and editor arrow.
- `AC_PreCMCTick`, `AC_TraversalLogic`, `MotionWarping`, `AC_FoleyEvents`.
- `AC_VisualOverrideManager` (component variable `BP_VisualOverrideManager`) and `VisualOverride` child actor.
- `AC_SmartObjectAnimation`.
- `GameplayCamera`, `SpringArm`, and `Camera(NotUsedByDefault)`.

Important pawn variables include `CharacterInputState`, `Gait`, `MovementStickMode`, `AnalogWalk/RunThreshold` (0.7), `WalkSpeeds`, `RunSpeeds`, `SprintSpeeds`, `CrouchSpeeds`, `StrafeSpeedMapCurve`, `JustLanded`, `LandVelocity`, `LastUpdateVelocity`, `UsingAttributeBasedRootMotion`, and `IsRagdolling`. The full declarations are in `SandboxCharacter_CMC-overview.json`.

The CMC AnimBP derives from `AnimInstance`. Its normal data update invokes **`BPI_SandboxCharacter_Pawn.Get_PropertiesForAnimation` on `GetOwningActor()`** and caches the returned `S_CharacterPropertiesForAnimation`. It does not require a direct cast to `SandboxCharacter_CMC` for that path. Therefore the hidden source mesh must belong to the Selene pawn implementing this interface, rather than an unrelated visual child actor.

`Update_Trajectory` uses `PoseSearchTrajectoryLibrary.PoseSearchGenerateTransformTrajectory` and `HandleTransformTrajectoryWorldCollisions`, based on the owning character's CMC. The sample explicitly notes limitations for montage root motion and wall/ceiling collision prediction. Its motion-matching graph uses PoseSearch history, Chooser-selected databases, BlendStack, steering/orientation/root-offset warping, and foot placement. Foot placement references `pelvis`, `ik_foot_root`, `foot_l/r`, `ik_foot_l/r`, `ball_l/r`, and **`contact_l` / `contact_r`** curves. Keep the source skeleton, pose history, animation curves, and database/schema references coherent.

### Exact data bridge for option A

Implement the existing Blueprint interface and return its existing user-defined struct; a similarly named C++ interface or struct is **not** type-compatible automatically. Use a small BP wrapper around native getters, or deliberately replace all consumers with new native types in a separate, larger refactor.

| Struct field(s) | Selene provider / required behavior |
| --- | --- |
| `InputState` | Sprint and walk intent from `MovementPace`; strafe/aim intent consistent with the current camera/control mode; crouch false until supported. The nested struct has WantsToSprint/Walk/Strafe/Aim/Crouch. |
| `MovementMode` | Map CMC walking/falling explicitly to sample `OnGround` / `InAir`; sample enum identifiers are `NewEnumerator4` / `NewEnumerator5`, not native CMC enum ordinals. |
| `Stance`, `Gait`, `RotationMode` | Stand; Walk/Run/Sprint (Selene Jog maps to Run); OrientToMovement or Strafe/Aim as appropriate. Use named BP enum entries, not ordinal casts. |
| `ActorTransform`, `Velocity` | Pawn transform and CMC velocity. |
| `InputAcceleration`, `CurrentMaxAcceleration`, `CurrentMaxDeceleration` | `GetCurrentAcceleration()`, `GetMaxAcceleration()`, and current braking deceleration. Match the values actually used for movement. |
| `OrientationIntent` | Pawn/desired facing rotation, following the sample's CMC convention. |
| `AimingRotation` | Local control rotation; base aim rotation for a remote pawn, as in the sample. |
| `JustLanded`, `LandVelocity` | Cache landing event/pre-impact velocity and expose the landing pulse for the animation update. Clear after consumption; do not lose it by tick ordering. |
| `GroundNormal` | CMC current-floor hit normal; use a valid flat-ground fallback when there is no floor hit. |
| `BasedMovementDelta` | Identity initially, matching the CMC graph's unconnected default; moving-platform support needs a deliberate implementation. |
| `MovementDirection`, `SteeringTime`, `GroundLocation` | Also exist in the struct but are not populated by the inspected CMC `MakeStruct` node. Preserve defaults initially and review consumers if extending the graph. |

The complete pawn interface additionally declares `Get_PropertiesForCamera`, `Get_PropertiesForTraversal`, `Get_PropertiesForRagdoll`, `Get_MMIResult`, `Set_CharacterInputState`, `AddTarget`, `RemoveTarget`, `Set_IsPlayingRootMotion`, and `Set_PhysicsProfile`. For the stripped locomotion path, provide safe defaults/no-ops for unused functionality and ensure retained notifies cannot trigger unsupported behavior.

The AnimBP implements `BPI_SandboxCharacter_ABP`: `Get_PoseHistory`, `Get_InteractionTransform`, `Set_InteractionTransform`, `Set_NotifyTransition_ReTransition`, `Set_NotifyTransition_ToLoop`, `Get_Gait`, `Get_Trajectory`, and `Update_MMIConstraints`. It also retains the older `BPI_InteractionTransform`. Keep the required interfaces while retaining corresponding animation notifies; removing an interface without updating its callers is not a valid trim.

### Movement, input, camera, and traversal

The sample capsule is **radius 30 / half-height 86 cm**, source mesh Z **-88**, yaw **-90°**. Selene uses **34 / 87.5**, mesh Z **-87.5**. Start with Selene's collision dimensions and calibrate visual mesh height independently; Angel's wings should not enlarge the navigation capsule or block the spring arm by accident.

GASP speed vectors are forward/side/back: walk **200/180/150**, run **500/350/300**, sprint **700/700/700**, crouch **225/200/180** cm/s. Separate demo vectors are **165/375/600** isotropic; do not mistake them for the active defaults. CDO defaults include jump Z 500, air control .25, max acceleration/braking 500, and braking-friction factor 0. `UpdateMovement_PreCMC` overwrites movement settings dynamically: walk/run acceleration 800, sprint acceleration remaps speed 300–700 to 800–300; ground friction is gait/speed-dependent. Braking chooses 2000 or 500 depending on movement input.

`UpdateRotation_PreCMC` sets grounded rotation rate to **-1** (instant capsule facing) and falling rotation rate to 200, while the animation root offset smooths visible rotation. Selene's existing 500°/s turn rate and 150/350/600 pace are not equivalent. Port the relationship between desired capsule rotation and visual root rotation, then tune at Selene's speeds. Do not let a BP tick overwrite first-person controller yaw or let `SetMovementPace` and sample code fight over speed.

`SetupInput` adds `/Game/Input/IMC_Sandbox` on possession. The pawn binds IA_Move, IA_Move_WorldSpace, IA_Look, IA_Look_Gamepad, IA_Walk, IA_Sprint, IA_Jump, IA_Crouch, IA_Strafe, and IA_Aim. The wider context also contains IA_Traverse, IA_Interact, IA_NextPawn, IA_NextVisualOverride, IA_TwinStick_AimDirection, IA_TeleportToTarget, IA_TriggerRagdoll, and IA_Takedown. Verified conflicts:

- WASD, mouse/sticks, Ctrl walk, Shift sprint, and Space jump overlap Selene.
- **C means crouch in GASP but character cycle in Selene.**
- **Space maps to both jump and traversal in GASP.**
- M/N cycle visual/pawn overrides through sample gameplay; they do not replace Selene's roster lifecycle.

Keep **only Selene's runtime mapping context** for A, at its current priority 0. Forward intent into the animation bridge. Changing context priority alone does not solve duplicate action ownership. For B, remove/replace the sample input installation and bindings deliberately, or use one curated context and adapt every Selene controller cast.

GASP defaults to the **Gameplay Cameras** system (`DDCVar.NewGameplayCameraSystem.Enable=True`), using `/Game/Blueprints/Cameras/CameraAsset_SandboxCharacter`, `CameraDirector_SandboxCharacter`, `CHT_CameraRig`, and camera rigs. `SetupCamera` activates that system or the legacy camera and changes the controller view target. A should not import this camera graph. B must remove/disable its activation before adding Selene's spring-arm and first-person cameras.

`AC_TraversalLogic` depends on traversal chooser outputs, traversal assets, MotionWarping, and the pawn/AnimBP interfaces. Smart Object animation has a separate component and AI/StateTree/SmartObjects/GameplayInteractions dependencies. Removing traversal requires removing components, jump/traverse call paths, chooser rows, normalization memberships, animation references, and unsupported interface/notifies—not just hiding the traversal input. Ordinary jump/fall/land locomotion should remain.

### Configuration that migration will not copy

The ABP queries sample data-driven CVars. Missing CVar registration can silently leave features off. In Selene-owned copies, replace sample CVar reads with explicit project settings, or register the selected CVars intentionally; do not wholesale copy GASP's renderer/collision/game-mode configuration.

Preserve the motion-matching selection (`DDCvar.LocomotionSetupCMC=0`, `DDCvar.MMDatabaseLOD=0` initially); keep experimental state-machine selection disabled. Preserve the engine `a.animnode.offsetrootbone.enable` behavior and deliberate translation-radius setting. The project-wide `DDCvar.FootPlacementMode` defaults to **1** (documented as 0 off, 1 foot-placement node, 2 biped Control Rig), but no read of that CVar was found in the exported CMC ABP. Its `FootPlacementMode=0` member is not proof that the actual node is disabled: the inspected CMC node has alpha 1 / enabled true and binds `Get_FootPlacementPlantSettings` and `Get_FootPlacementInterpolationSettings`. Preserve those bindings and verify the evaluated graph rather than assuming the global switch controls this CMC path. Thread-safe-update and debug CVar reads must stay on the game thread; the sample caches them before worker-thread use. Verify the chosen graph path and actual foot-placement activation in the AnimBP debugger after integration.

## Dependency closure and migration boundary

Method: scan the installed sample with AssetRegistry; recursively traverse **hard and soft package references**, excluding searchable-name and management relationships. Follow external dependencies too. Deduplicate by long package name. Sum existing `.uasset`, `.umap`, `.uexp`, `.ubulk`, and `.uptnl` file sizes for `/Game` packages. All retained project packages had a nonzero file size. **MB means 1,000,000 bytes**; these are uncooked source-content sizes, not cooked builds, RAM, search-index size, or engine/plugin binaries. `/Script`, `/Engine`, and plugin-content dependencies are recorded separately in each manifest and are not charged as migrated project content.

The full roots are:

```text
/Game/Blueprints/SandboxCharacter_CMC
/Game/Blueprints/SandboxCharacter_CMC_ABP
/Game/Blueprints/RetargetedCharacters/ABP_GenericRetarget
/Game/Blueprints/AC_VisualOverrideManager
/Game/Blueprints/RetargetedCharacters/BP_Manny
```

The smaller A roots are:

```text
/Game/Blueprints/SandboxCharacter_CMC_ABP
/Game/Characters/UEFN_Mannequin/Meshes/SKM_UEFN_Mannequin
/Game/Characters/UEFN_Mannequin/Rigs/IK_UEFN_Mannequin
```

**There is no unmodified closure from the requested full roots that satisfies “no traversal, no MetaHumans, no Mover.”** Ignoring soft references produces 2,058 packages / 2,200.18 MB but loses assets selected at runtime; it is not the recommended migration. The ABP alone is 1,187 packages / 1,078.97 MB. Adding the source IK rig gives the smaller unmodified starting set below.

| Folder | Full roots: packages / MB | A roots, unmodified: packages / MB | A target after edits: packages / MB |
| --- | ---: | ---: | ---: |
| `/Game/Audio` | 278 / 11.72 | 278 / 11.72 | 278 / 11.72 |
| `/Game/Blueprints` | 126 / 32.17 | 41 / 5.80 | 39 / 5.79 |
| `/Game/Characters/Echo` | 134 / 1,170.44 | 0 / 0.00 | 0 / 0.00 |
| `/Game/Characters/Paragon` | 198 / 786.40 | 0 / 0.00 | 0 / 0.00 |
| `/Game/Characters/UE4_Mannequin` | 20 / 17.24 | 0 / 0.00 | 0 / 0.00 |
| `/Game/Characters/UE5_Mannequins` | 107 / 365.72 | 0 / 0.00 | 0 / 0.00 |
| `/Game/Characters/UEFN_Mannequin` | 1,592 / 1,966.57 | 868 / 1,061.54 | 839 / 1,028.82 |
| `/Game/Input` | 19 / 0.05 | 0 / 0.00 | 0 / 0.00 |
| `/Game/Levels` | 21 / 37.83 | 0 / 0.00 | 0 / 0.00 |
| `/Game/MetaHumans` | 365 / 314.43 | 0 / 0.00 | 0 / 0.00 |
| `/Game/Misc` | 1 / 0.00 | 1 / 0.00 | 1 / 0.00 |
| **Total** | **2,861 / 4,702.55** | **1,188 / 1,079.06** | **1,157 / 1,046.33** |

Exact byte totals: full = 4702553260, core-unmodified = 1079061624, core-proposed = 1046325697.

The A target is the dependency closure for the specified retained asset set and explicit cuts, **not a claim of an absolute minimum among all possible rewrites**. It retains full locomotion data (including crouch data), ordinary jump/landing, shared notify/audio dependencies, some legacy declarations, and native graph features still referenced by the copied ABP. Further shrinking to only standing locomotion, one database density, no audio, and no debug/Sequencer nodes is possible but changes the behavior/content selection and needs another measured closure. New Selene BP wrappers/retargeters are not yet authored and are not included in these source-byte totals; saving edited assets also changes their bytes slightly.

Required reference edits for the 1,157-package target:

1. Do not use the sample pawn, game mode, visual manager, or generic sample follower as migration roots for A. Recreate their small necessary behaviors in Selene. This removes the route through the whole visual roster, sample levels, and sample Mover pawn.
2. In the copied CMC ABP, remove the unused member **`Mover`** (`MoverComponent`) and **`Update_Trajectory.NewLocalVar`** (`MoverTrajectoryPredictor`). Their serialized types account for the direct Mover dependency found in the inspected graph; no active CMC trajectory call used Mover. Compile and rescan before declaring Mover removable.
3. Remove the experimental state-machine graph branch and references to `Animations/ExperimentalStateMachineData/CHT_CMCCharacterAnimations` and `StrafeOffsetCurveContainer`; preserve the motion-matching graph and its database chooser. Remove invalid leftovers during compilation rather than leaving disconnected references.
4. Remove `*FromTraversal` database rows from **all retained Dense, Sparse, and Relaxed chooser tables and normalization sets** under `/Game/Characters/UEFN_Mannequin/Animations/MotionMatchingData/`. Removing only chooser rows is insufficient because normalization sets retain database references.
5. Remove the traversal sequence entries from `/Game/Characters/UEFN_Mannequin/Animations/ExperimentalStateMachineData/PSD_SM_CMC_Transitions`. This database remains reachable through shared locomotion clips. Example measured path: CMC ABP → `CHT_PoseSearchDatabases` → Dense chooser → `PSD_Dense_Stand_Run_Stops` → `Run/M_Neutral_Run_Stop_F_Lfoot` → `PSD_SM_CMC_Transitions` → hurdle sequence. The fourth commandlet confirmed the clip reference is an `AnimNotifyState_PoseSearchBranchIn.Database` field. Keep the shared non-traversal references unless intentionally replacing their notify behavior.
6. Recompute dependencies from the saved copies and rebuild PoseSearch data after changing database/normalization membership. Do not simply delete excluded files or pass an incomplete handpicked list to the migration tool.

The exact edge list and all 1,157 retained package names are in `proposed-reference-cuts.json` and `closure-core-proposed.json`. The modeled graph has zero traversal animation, MetaHuman, SmartObject, sample Mover pawn, or `AC_TraversalLogic` packages and no `/Script/Mover` reference. The pawn interface still brings small traversal/ragdoll **data types**, not their gameplay systems. Keeping the interface avoids a broader type-contract rewrite.

**Migration procedure:** first migrate the 1,188-package unmodified A roots to a disposable staging project; perform the cuts there, preserving the original sample. Compile/save and rerun the registry report in staging. Only then call `unreal.AssetToolsHelpers.get_asset_tools().migrate_packages(...)` into Selene's actual `Content` directory. Python's exposed overload takes roots, destination, and `MigrationOptions` and gathers dependencies itself; its C++ overload with explicit dependency/exclusion sets is not the exposed Python signature. Keep conflict policy at SKIP initially and audit conflicts; never overwrite Selene's existing `/Game/Characters` assets blindly. Preserve package paths during initial migration to avoid breaking soft references. Staging and migration are future implementation work, not actions taken by this investigation.

## Plugins: exact observed requirements

Do not copy GASP's entire `.uproject` plugin list. For the **proposed A graph described above**, explicitly enable these currently non-default engine plugins:

```text
AnimationWarping
BlendStack
Chooser
CurveExpression
DrawDebugLibrary
MotionWarping
MovieSceneAnimMixer
PoseSearch
```

`BlendStack`, `Chooser`, `AnimationWarping`, and `MotionWarping` are also enabled transitively by PoseSearch/Chooser, but listing the directly used features explicitly makes the project requirements clear. **MotionWarping remains a PoseSearch descriptor dependency even with traversal removed.** The retained graph has CurveExpression, DrawDebugLibrary, and MovieSceneAnimMixer references; removing those features would require separate graph edits and a new dependency audit.

Keep/ensure these other directly referenced plugins are enabled (installed defaults or already enabled by Selene):

```text
ACLPlugin
AnimationData
ControlRig
EnhancedInput
IKRig
Interchange
Metasound
PropertyAccessNode
PythonScriptPlugin  (editor investigation/asset authoring only)
```

The first eight plus the eight runtime/editor asset-support names before Python form the 16 direct feature/asset plugin seeds in `core-plugin-closure.json` (EnhancedInput is added for Selene's controller). `ACLPlugin` is also required by `/ACLPlugin/ACLAnimBoneCompressionSettings`; not every plugin requirement appears as a direct ABP node.

Plugin descriptors automatically bring dependencies such as **RigVM, FullBodyIK, AnimationModifierLibrary, PropertyAccessEditor, GameplayTagsEditor, GameplayInsights**, and the Sequencer/UAF dependencies of MovieSceneAnimMixer. The complete recursively expanded editor dependency union is recorded in `core-plugin-closure.json`; it includes defaults already used by Interchange/editor tooling. Do not confuse that editor support union with extra sample content to migrate or a minimal Shipping module list. Use the installed descriptors' target/platform conditions for the actual build.

| Plugin/group | Required boundary |
| --- | --- |
| **Mover** | Required to load the **unmodified** CMC ABP because of the two typed variables above. Can be excluded from A only after those references are removed, compilation passes, and the saved registry confirms absence. |
| NetworkPrediction, Water, ChaosVD | Mover descriptor dependencies when Mover is retained; do not enable merely because the movement component is named CMC. |
| GameplayCameras | Required for the unmodified sample pawn/cameras (B); A retains Selene cameras and excludes those assets. Installed default is enabled, but it need not be a new locomotion feature. |
| SmartObjects, GameplayInteractions, GameplayStateTree, StateTree | Required by the retained sample Smart Object path; remove that path for the requested scope. Selene already enables the StateTree plugins for other features; do not disable unrelated functionality. |
| **AnimationLocomotionLibrary** | Enabled in GASP's project descriptor, but **no module or content dependency appears in the measured CMC A closure**. Not required for this plan; do not confuse it with `AnimationWarping`. |
| AnimationLayering, Locomotor, ChaosMover, MoverExamples | Not required by the retained CMC A closure. |
| RigLogic, LiveLink, LiveLinkControlRig, HairStrands | No sample-character requirement for Champion/Angel. Some engine tooling (notably Interchange) enables HairStrands transitively; that does not require migrating MetaHumans. |
| KawaiiPhysics | Separate future secondary-motion feature. Initially disabled after the documented Mac link failure; the final refresh found it enabled with Mac binaries produced by concurrent work. Successful build/runtime validation was not independently established here. It is not a prerequisite for proving GASP locomotion. |

For unmodified B/full-root migration, the additional direct sample dependencies include Mover, GameplayCameras, SmartObjects, GameplayInteractions, GameplayStateTree, StateTree, RigLogic, LiveLink, HairStrands, ControlRigSpline, ChaosCloth, and associated support plugins. The exact full `/Script` dependency list is in `closure-full.json`. Enabling plugins alone does not remove sample content references or make B compatible with Selene's controller.

## Options and automation feasibility

| Area | A: Selene pawn + UEFN source, recommended | B: sample CMC pawn or child |
| --- | --- | --- |
| Animation hookup | BP child implements existing pawn interface; copied ABP sees its owning pawn and native CMC. Requires the explicit data bridge and movement/rotation tuning above. | Existing movement/interface/ABP wiring provides a useful animation baseline. |
| Selene controller | Retains `ASeleneCharacter` casts and input ownership. Expose animation state getters and preserve pace/camera semantics. | Current Move/Look/Jump/Pace/V/C handlers cast to `ASeleneCharacter`; an unrelated CMC BP makes them no-op. Replace with a shared native interface/generalized API, or port the controller handlers. |
| Roster | Keep config selection, commands, preloading, cancellation, and generation IDs; change the **visual follower**, never replace the UEFN source. | Replace sample global game-mode/CVar selection with Selene's per-pawn config/async roster, or adapt the visual manager and its lifetime/replication behavior. |
| Cameras / pause | Keep spring arm and capsule-relative 1P camera. Apply OwnerNoSee to follower; keep source evaluating. Pause menu stays controller-owned. | Add both Selene cameras and V logic, remove GameplayCamera activation/view-target takeover. Pause menu can stay on Selene controller only after its jump/sprint callbacks are adapted. |
| Perf / commands | Pawn remains an `ASeleneCharacter`; existing casts survive. Animation update/history still needs correct treatment in teleport versus drive modes. | `selene.Camera`, `selene.Character`, configuration checks, and checked perf casts require changes. A child of sample CMC is still not an `ASeleneCharacter`. |
| Risk | Adapter and animation/CMC tuning; contained gameplay impact. | More sample behavior initially works, but broad changes to input, pawn identity, camera, roster, game mode, and perf contracts. |

Reparenting a copied `SandboxCharacter_CMC` BP to `ASeleneCharacter` is technically available but is **not a shortcut without reconciliation**. Selene's constructor/BeginPlay/roster loader currently replaces the main mesh and AnimInstance, configures cameras, and changes ticking. The sample also sets up input/cameras/movement. Component names, parent calls, initialization order, and native private state must be resolved. A fresh BP child with only the needed interface graph is clearer and avoids importing sample managers.

Verified headless API boundary (installed header sources and live `api2.json`):

| Work | Editor Python support / limitation |
| --- | --- |
| Inventory, recursive dependency closure, defaults and graph text | **Executed here**: AssetRegistry, `ObjectExporterT3D` / `AssetExportTask`, `get_default_object`, `BlueprintEditorLibrary.list_graphs`, component-template gathering. Guard failed loads before exporting. |
| Package migration | `AssetTools.migrate_packages(package_names_to_migrate, destination_path, options)` is exposed. **Not executed** here. Run it only from the pruned staging copies for the small target. |
| Blueprint creation/duplication/reparenting | Exposed AssetTools/EditorAssetLibrary and `BlueprintEditorLibrary.create_blueprint_asset_with_parent`, `reparent_blueprint`; compile and inspect parent/component changes afterward. Availability is verified; the proposed reparent has not been tested. |
| Variables and component defaults | `add_member_variable`, type helpers, compile, CDO `set_editor_property`; `SubobjectDataSubsystem.add_new_subobject` and template editing. BP-generated private fields do not all appear as ordinary Python properties. Initial attempts to read `parent_class` directly failed; use the exposed parent getter or exports. |
| IK rigs and retargeters | Existing Selene script demonstrates `IKRigController` / `IKRetargeterController` creation, chain mapping, operations, pose alignment, and saving. Adapt it to UEFN; do not batch-retarget the whole animation library for runtime followers. |
| Pawn interface implementation and event/function wiring | **Graph-authoring work**, not a component-default edit. The installed Blueprint editor library exposes graph enumeration, function overrides, member-variable helpers, and pin inspection; this investigation did not establish a complete Python-only node creation/interface implementation workflow. Use Blueprint Editor or a tested editor C++ helper. |
| Motion-matching/retarget/post-process AnimGraphs | **Graph-authoring work**: pose links, node bindings, exposed pins, interface functions, and branch removal must compile correctly. Creating an empty AnimBlueprint asset is not sufficient. Do not promise that `set_editor_property` builds these graphs. |
| Chooser/database/normalization pruning | Requires supported controllers/reflected editing or their asset editors, followed by save, index rebuild, and closure rescan. The conceptual edge cuts are verified against the registry; the exact mutation API has not been exercised here. |
| Gameplay/perf adaptation | C++ edits and an editor/game build. No Python-only replacement for native controller/perf contracts. |

For B, headless reparenting/default edits can prepare assets, but the same graph work is needed to remove sample initialization, traversal, camera, input, and manager logic. Option B therefore does not eliminate graph editing; it relocates the complexity to preserving Selene features.

## Toon, outline, and Kawaii compatibility

The source mesh also assigns `/Game/Characters/UEFN_Mannequin/Rigs/ABP_UEFN_Mannequin_PostProcess`. Its exported graph includes source-shape adjustments (head/thigh scaling and an additive lean pose), not Kawaii physics. Decide explicitly whether to retain these source adjustments; compare retargeted target proportions and do not blindly assign this UEFN-specific post-process to a Mixamo mesh.

Retargeting transfers pose data; the **visible follower retains its own material slots, material overrides, overlay material, textures, and render flags**. Keep Champion's `MI_Toon_Champion` and Angel's `MI_Toon_Angel` on their follower components and preserve each skeletal mesh's outline overlay. Selene currently clears and reapplies overrides when switching the main mesh; move that behavior to the follower and inspect overlay state explicitly after every swap. The hidden source should render neither a duplicate body nor a second outline/shadow; retain visible follower hidden shadows in first person as intended. Preserve Selene's current Substrate/toon renderer settings.

Recommended evaluation order:

```text
Selene CMC and input state
  -> hidden UEFN mesh: CMC motion-matching AnimBP, root/foot correction
  -> visible Mixamo mesh: RetargetPoseFromMesh using UEFN-to-hero retargeter
  -> visible mesh post-process AnimBP:
       Input Pose -> Local to Component -> Kawaii hair/skirt/wing nodes
                  -> Component to Local -> Output
  -> toon materials and overlay outline
```

Kawaii belongs **after** retargeting on the hero, so it sees the final Mixamo pose and affects only selected secondary bones. It should not alter the hidden source, locomotion hip/leg chains, or contact curves. Use separate validated per-character chain/collision settings, a deterministic reset on mesh switches/teleports, and a deliberate tick/LOD policy. If the hero already has a post-process AnimBP, compose the physics into it; a mesh does not gain multiple independent post-process classes by assignment.

`docs/KAWAII-PHYSICS.md` proposes a native single-node proxy for the current locomotion system. That recommendation is superseded **for the GASP path**: a single-node proxy would replace the retarget AnimInstance. Use the follower post-process approach (or an equivalent complete retarget-plus-physics graph). The documented plugin version is 1.21.0 for UE 5.8; that document records an earlier Mac editor link failure because the plugin binary output directory was missing, and no Shipping run at that time. A final refresh found enabled plugin configuration and newly produced binaries while the document still described the earlier failure. Reconcile the newer build logs before repeating any fix. This investigation did not validate the plugin build or physics runtime.

## Implementation chunks (each at most 25 minutes)

These are bounded implementation sessions, not a promise that compilation or asset indexing will finish within the allotted wall time. If a build/index job outlasts its session, record its PID/log/checkpoint and verify it in the next session; do not start dependent changes until its gate passes. Keep a reversible checkpoint after each verified chunk. None of these implementation steps was performed by this investigation.

1. **Baseline and conflict audit — 15 min.** Record current Git status, source mesh/roster settings, editor/game build baseline, and known Kawaii limitation. Compare the core manifest against Selene's existing package paths and hashes; record any collision. **Verify:** exact project/engine versions, both hero assets load, and the existing controller/route behavior has a reproducible baseline.
2. **Prepare isolated staging — 15 min.** Create a temporary UE 5.8 staging project; enable the direct asset plugins and temporarily Mover to load the unmodified CMC ABP. Keep GASP read-only. **Verify:** staging opens headless; all required native graph classes resolve; no sample project source/config/content changed.
3. **Stage the small roots — 20 min.** Use `migrate_packages` with the three A roots and explicit destination Content directory. **Verify:** compare actual migrated packages with `closure-core-unmodified.json` (1,188 packages, 1,079.06 MB source baseline), inspect conflicts and errors, and load the CMC ABP/source rig. Do not substitute the full pawn/game-mode roots.
4. **Remove serialized Mover types — 15 min.** Remove the ABP's `Mover` member and `Update_Trajectory.NewLocalVar`; compile/save. **Verify:** no Mover nodes/variable types or `/Script/Mover` reference in the saved ABP; reopen staging with Mover disabled and load/compile successfully. Keep the plugin if any unresolved reference remains.
5. **Retain only the motion-matching branch — 25 min.** Remove the experimental state-machine branch and its two direct data links in the staging copy, preserving motion matching, pose history, root offset, foot placement, and required notify/interface methods. **Verify:** no graph compile errors or missing function bindings; the MM chooser and source skeleton are unchanged. Record any shared legacy data still referenced by clips.
6. **Prune traversal chooser selections — 20 min.** Remove all FromTraversal database selections from Dense/Sparse/Relaxed tables. **Verify:** every remaining row resolves and ordinary ground/jump/land fallback rows remain; record removed rows against the cut manifest.
7. **Prune indirect traversal references — 20 min.** Remove the corresponding normalization memberships and traversal entries in `PSD_SM_CMC_Transitions`. **Verify:** a fresh recursive scan has zero `/Animations/Traversal/` references; investigate every residual path instead of deleting its target file.
8. **Rebuild data and confirm the staging boundary — 25 min.** Rebuild changed PoseSearch databases/normalization indexes and compile retained Blueprints; rescan saved packages. **Verify:** no missing references or empty required database selections; target package count matches the modeled 1,157 or every difference is explained. Record actual post-save bytes. Confirm no MetaHuman, SmartObject, traversal gameplay, or Mover requirement.
9. **Migrate the verified staging closure — 20 min.** Enable the explicit target plugins in Selene and migrate only the saved pruned roots, respecting the conflict audit. Keep Selene's game mode, input, renderer, and cameras. **Verify:** source packages load in Selene with no missing graph classes; compare migrated hashes/paths and launch the existing editor target. If the build is still running, checkpoint and wait in a separate session.
10. **Separate source and visible mesh ownership — 25 min.** Keep inherited `GetMesh()` as the permanent UEFN source; add a visible skeletal follower component with no movement collision, explicit attachment/tick prerequisite, and a deliberate visibility/shadow policy. Stop the single-node update path from driving the source. **Verify:** source AnimInstance is the copied CMC ABP throughout BeginPlay, possession, and roster initialization; no duplicate rendered body/shadow.
11. **Extend the roster safely — 25 min.** Add soft retargeter/follower-AnimBP fields; move mesh/material application to the follower. Retain generation IDs, cancelled pending requests, load validation, and references keeping assets alive. **Verify:** rapid C presses and `selene.Character Champion|Angel` end on the latest requested hero; invalid assets preserve the previous hero; the source mesh/AnimInstance never changes. Decide explicitly whether the existing optional Manny roster entry retains its old separate animation path or receives its own UEFN follower definition.
12. **Provide the native animation-state inputs — 25 min.** Expose pace/camera intent, velocity/acceleration, floor state, orientation, and landing pulse/velocity; establish update ordering relative to CMC and animation. **Verify:** logged values change correctly on start, release, reversal, jump, and landing; zero-input braking and 150/350/600 limits match actual CMC behavior.
13. **Implement the BP pawn interface — 25 min.** Create `BP_SeleneGASPCharacter : ASeleneCharacter`; implement `Get_PropertiesForAnimation` using the existing sample struct and enum types. Add safe unused-interface behavior and configure the game mode to spawn this child. **Verify:** the source AnimBP obtains valid non-default character data; existing controller and perf casts still accept the possessed pawn; compile with no interface warnings.
14. **Reconcile rotation, gait, and configuration — 25 min.** Port the necessary pre-CMC movement/rotation behavior, keep Selene pace values authoritative, and replace/register selected CVar settings. Prevent gameplay camera/context installation. **Verify:** MM is the active branch, foot placement is enabled, 3P turns do not lag/double-rotate, and entering/leaving 1P retains correct control yaw and view target.
15. **Author Champion's direct retargeter — 25 min.** Create `RTG_UEFN_To_Champion` with the UEFN source rig and existing Mixamo target rig; map chains, align pose, inspect IK goals, and preserve the separate-root constraint. **Verify:** representative idle/walk/run/turn poses in retarget preview have ground-height hips, correct facing, and coherent feet/hands; no reference-pose fallback.
16. **Author Angel's direct retargeter — 25 min.** Repeat with `IK_Angel`, preserving wing geometry and target proportions. **Verify:** 180 cm target proportions, feet, shoulders, and wing attachment remain coherent; mark any missing usable wing bones as a physics limitation.
17. **Build and initialize follower AnimGraphs — 25 min.** Author the two retarget AnimBPs, assign the intended retargeters/source selection, and initialize only after preloading. Preserve necessary retarget-profile/curve behavior rather than inheriting sample-specific operation assumptions blindly. **Verify:** both followers evaluate the current source pose, including rapid switches, without a T-pose frame or one-frame lag; leader-pose binding is absent.
18. **Restore cameras, toon, outlines, and pause — 20 min.** Apply hero material/overlay and OwnerNoSee policies to the follower; keep capsule-relative eye heights (Champion 160, Angel 162 cm above feet) and existing boom lengths (350/450). **Verify:** V and swaps in both modes, Esc pause/resume, release of held sprint/jump on pause, first-person hidden shadows, and no camera obstruction by wings or a hidden source.
19. **Champion motion-quality pass — 25 min.** Exercise starts/stops at all three paces, short stick taps, 90°/180° turns, reversals/pivots, jump/land, ramps, stairs, and uneven ground. Tune retarget goals/contact behavior only with captures. **Verify:** visual foot contacts and hip height from player-eye and side views, visible MM pose selections, no persistent sliding/penetration, and measured speed matching intent. Preserve a short reproducible input/capture sequence.
20. **Angel motion-quality pass — 25 min.** Repeat the same sequence at Angel proportions and camera distance, testing wings near walls and during turns. **Verify:** the same contact criteria plus stable shoulders/wing attachments, outline continuity, and no clipping caused by a misplaced capsule or camera collision.
21. **Perf and teleport lifecycle — 25 min.** Use the existing perf runner for both heroes and camera modes. Exercise its normal teleport route and its drive mode separately; reset animation history/root offsets and future secondary physics on real teleports as required. **Verify:** configuration checks and checked casts pass, no stale pose/root offset on route jumps, and source/follower/MM CPU and frame-time costs are recorded against baseline. Teleport-route captures are not evidence of natural CMC locomotion; use drive mode/manual play for that claim.
22. **Cook and regression gate — 25 min.** Validate editor and game builds, existing Shipping packaging, and config-only soft-reference cooking for the new BPs/retargeters. **Verify:** packaged hero switching, cameras, pause, starts/stops/pivots/landing, and perf commands work without editor-only assets or missing plugins. Checkpoint long builds for a following verification session; do not mark completion on compilation alone.

Optional follow-on after locomotion passes:

23. **Kawaii build prerequisite — 25 min.** First reconcile the concurrent job's latest build results. If still necessary, resolve the previously documented output-directory failure; validate the plugin's Mac editor and Shipping builds in separate sessions when needed. **Verify:** actual successful link/build logs; keep physics disabled until both succeed.
24. **Follower post-process physics — 25 min per hero.** Author the post-process graph and validated hair/skirt/wing chain/collision setup on one hero per session. **Verify:** locomotion feet remain unaffected, physics settles after switches/teleports, 1P/3P and outline rendering remain correct, and packaged evaluation works. If chain tuning needs more time, repeat bounded per-hero sessions rather than combining this with locomotion approval.

## Material risks and completion criteria

- **Source-skeleton mismatch:** UEFN is required for the retained ABP/data. Existing Manny retargeters are useful target-rig precedent, not drop-in runtime assets.
- **Static closure versus runnable minimal integration:** the 1,046.33 MB figure is reproducible graph arithmetic over existing package sizes. Only compiled, saved staging copies and a new scan can certify the final closure. Asset migration alone neither prunes references nor copies project CVars/plugins.
- **Missing plugin types:** the CMC ABP genuinely serializes Mover types despite using CMC trajectory calls. Do not disable Mover before removing and verifying those references. Other retained native graph plugins remain required even if a particular runtime branch is inactive.
- **Motion-matching quality depends on CMC behavior:** speed, acceleration, braking, rotation, ground state, and trajectory prediction must agree. Simply assigning the ABP may animate but does not establish good starts/stops/pivots or foot planting at Selene's speeds.
- **Mixed proportions and no separate Mixamo root:** retargeted source contact is not proof that a differently proportioned target foot remains fixed in world space. Target IK/profile tuning, pelvis/root mapping, and visual capture are mandatory for both heroes.
- **Initialization and ticking:** native roster code currently replaces the main mesh and disables actor tick for AnimBP entries. Reconcile that explicitly; a BP data bridge/pre-CMC callback cannot depend on a tick that the native branch disables. Hidden source and owner-hidden follower must keep the pose/bones needed for retargeting and shadows, with correct prerequisites.
- **First person and root offsets:** preserve capsule-relative camera behavior. A visually offset root can be appropriate for 3P turns but should not rotate or bob the 1P camera unexpectedly.
- **Character swapping:** make mesh, AnimBP, retargeter, materials, overlay, and physics settings one validated transition. Cancelled loads or a missing retargeter must not produce a source/follower skeleton mismatch.
- **Perf interpretation:** the default route teleports a pawn with movement deactivated; it is a rendering benchmark, not a locomotion test. Drive mode/manual input is needed to validate trajectories and contacts.
- **Physics is currently unproven:** Kawaii's source installation and earlier compilation reaching a link action do not prove successful Mac/Shipping integration or correctly weighted wing chains.

Completion means both heroes visibly pass the same locomotion/contact sequence, roster and camera features survive runtime switching, pause behavior and existing perf commands remain correct, packaged assets/plugins resolve, and the final saved dependency manifest matches the stated exclusions. None of those runtime acceptance results is claimed by this investigation.


## Final-state verification and concurrent work

The four commandlets only inspected GASP. The file manifest comparison found **no changes to GASP outside the allowed Saved/Intermediate/cache areas**. The final two probe processes exited successfully; no investigation editor process was intentionally left running. This investigation invoked no Selene editor/build, asset save, download, or browser and made no commit.

Selene was not static during the investigation. At the final refresh (approximately 09:37 UTC), other running Selene work had changed `Selene.uproject`, Champion source/mesh/animation assets, `Tools/Unreal/character_retarget.py`, ground-material scripts/assets, and build outputs. Those files were left untouched by this investigation. `verification.json` records all observed differences rather than falsely asserting a globally clean workspace.

Relevant changes to recheck before implementation:

- **Kawaii:** `Selene.uproject` now has `KawaiiPhysics` enabled and both Mac editor plugin dylibs exist. `docs/KAWAII-PHYSICS.md` still reports its earlier failed build. Binaries appearing is not independent proof of successful current editor/Shipping validation; consume the concurrent job's final report/logs first.
- **Champion:** the refreshed retarget report says `failed`, with `IK_Champion: auto retarget definition failed (skeleton not recognised)`. Several prior Champion locomotion assets were absent in the manifest comparison. The script was concurrently extended with manual Mixamo body-chain fallback for additional secondary-physics bones and a warning path when auto FBIK fails. **Revalidate the rebuilt target rig and its solver/goals before using it for runtime foot planting.** Angel's report still says success. These are snapshots of ongoing work, not a finding that the other job has finished or a reason to overwrite its files.
- `Source/Selene` and `Config/DefaultGame.ini` were unchanged in the final manifest comparison, so the native controller/roster/perf contract described here remained applicable at that check.

Raw refresh evidence: `/tmp/gasp-investigation/selene-refresh.json`; baseline/current differences: `/tmp/gasp-investigation/verification.json`. Recheck volatile project and character state at implementation chunk 1.
