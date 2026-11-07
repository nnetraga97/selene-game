# Kawaii Physics installation and proposed native hookup

## Status — 2026-11-06

Source installed, but **build validation is incomplete**. The plugin was enabled
for the requested editor build, then explicitly disabled in `Selene.uproject`
after its link failure so the project does not require a missing Mac module.
No character hookup or plugin source changes were made. No retry was attempted,
as required by the task's stop-on-failure rule.

## Provenance and files

- Version: **1.21.0**, tag `20260624-v1.21.0`, official UE **5.8** release asset.
- Release: https://github.com/pafuhana1213/KawaiiPhysics/releases/tag/20260624-v1.21.0
- Download: https://github.com/pafuhana1213/KawaiiPhysics/releases/download/20260624-v1.21.0/KawaiiPhysics_5.8_1.21.0.zip
- Archive SHA-256: `2876aa19090ee28f3e8ed96a5d621a793baeafd5b475986f21510182998fe6e2`
- License: **MIT**, copyright 2019–2026 pafuhana1213. Preserve the copyright and
  permission notice when distributing copies or substantial portions.
- License source: https://github.com/pafuhana1213/KawaiiPhysics/blob/20260624-v1.21.0/LICENSE
- Exact license retained as `Plugins/KawaiiPhysics/LICENSE`; the release ZIP
  does not include it, so it was retrieved from the same official tag.
- Initial empty staging folder:
  `/var/folders/n9/rpnnb70115z66f19pt397fh80000gn/T/selene-kawaii-6a3s6ikz`.

Inspected all 64 archive entries before installation. Windows-style archive
separators were normalized and traversal paths rejected. Installed only the
`KawaiiPhysics` plugin: `KawaiiPhysics.uplugin`, `Config/FilterPlugin.ini`,
`Resources/Icon128.png`, and `Source/KawaiiPhysics` plus `Source/KawaiiPhysicsEd`.
The five bundled Windows binary/debug/module files were omitted. The 59
installed release files are byte-for-byte unchanged. The descriptor reports
`EngineVersion: 5.8.0`, `VersionName: 1.21.0`, and `Installed: true`.

## Build evidence

Command run from the project root, under the prescribed Unreal lock and
900-second alarm:

```sh
"/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh" SeleneEditor Mac Development -Project="$PWD/Selene.uproject" -WaitMutex
```

Exit code **6**. Compilation reached the Mac link action; this is an output
directory failure, not evidence of an incompatible C++ API:

```text
[28/33] Link [Apple] libUnrealEditor-KawaiiPhysics.dylib
ld: open() failed, errno=2 (No such file or directory) for '/Users/nicknetraganti/Desktop/Developer Stuff/Misc/selene-game/Plugins/KawaiiPhysics/Binaries/Mac/libUnrealEditor-KawaiiPhysics.dylib'
clang++: error: linker command failed with exit code 1 (use -v to see invocation)
[30/33] Compile [Apple] AnimGraphNode_KawaiiPhysics.cpp
[31/33] Compile [Apple] KawaiiPhysicsEditMode.cpp
Total time in Unreal Build Accelerator local executor: 66.25 seconds
Result: Failed (OtherCompilationError)
Total execution time: 82.30 seconds
```

`Binaries/Mac` was absent after the source-only installation. No directory fix
or build retry was attempted. The requested `Selene Mac Shipping` build was
**not run** after the editor failure. No runtime, packaging, or simulation
validation is claimed. A future continuation should first address the output
directory, enable the plugin, and validate both original build commands.

## Hookup investigation — plan only

**Recommend a native subclass of `UAnimSingleNodeInstance` with a derived
`FAnimSingleNodeInstanceProxy`.** This preserves the existing character's
`SetAnimationAsset` and `SetBlendSpacePosition` controls and requires no manually
authored AnimBP. This recommendation is based on source inspection, not a working
prototype.

The current roster path in `Source/Selene/SeleneCharacter.cpp` selects
`AnimationSingleNode`; `ASeleneCharacter::UpdateSingleNodeAnimation` drives the
ground/jump/fall/land assets through `GetSingleNodeInstance()`. UE's
`USkeletalMeshComponent::GetSingleNodeInstance` casts the active instance to
`UAnimSingleNodeInstance`, so a subclass can retain that interface.

Proposed future files: `Source/Selene/Animation/SeleneKawaiiAnimInstance.h/.cpp`.
Override `CreateAnimInstanceProxy` and its destruction counterpart. Derive the
proxy from `FAnimSingleNodeInstanceProxy` and use its protected `SingleNode`
as the locomotion source. Build a native pose chain:

```text
SingleNode -> LocalToComponentSpace -> Kawaii hair/clothing nodes
           -> ComponentToLocalSpace -> output
```

Wire pose links once; initialize and cache bones through the chain; update and
evaluate each frame exactly once. Override `Initialize`, `CacheBones`,
`UpdateAnimationNode`, and `Evaluate` with the base proxy's counter and asset
update requirements preserved. Do not update the base single node twice.
Expose the native nodes through `FAnimInstanceProxy::GetCustomNodes`, including
Kawaii's required `OnInitializeAnimInstance` game-thread initialization and
dynamic-reset lifecycle. Keep referenced data assets GC-visible and copy mutable
game-thread configuration into the proxy before evaluation.

Relevant plugin implementation:

- `Source/KawaiiPhysics/Public/AnimNode_KawaiiPhysics.h`:
  `FAnimNode_KawaiiPhysics`, derived from `FAnimNode_SkeletalControlBase`.
- `Source/KawaiiPhysics/Private/AnimNode_KawaiiPhysics.cpp`:
  `Initialize_AnyThread`, `CacheBones_AnyThread`, `UpdateInternal`,
  `OnInitializeAnimInstance`, `EvaluateSkeletalControl_AnyThread`.
- The node requests `NeedsOnInitializeAnimInstance()` and `NeedsDynamicReset()`;
  skipping these hooks is unsafe. Use the normal skeletal-control evaluation
  chain, not a raw call to `EvaluateSkeletalControl_AnyThread` alone.
- Future project module dependencies: `KawaiiPhysics` and `AnimGraphRuntime`.
  Select the native class in the roster's single-node branch via
  `SetAnimInstanceClass`; do not subsequently replace it with the default
  `AnimationSingleNode` instance. Preserve the existing custom AnimBP branch.
- Configure validated root/excluded bones and collision limits per character;
  reset on mesh switches and teleports. Verify locomotion, jump/landing,
  character switching, LOD changes, and Shipping before visual tuning.

**Post Process AnimBP alternative:** the Kawaii skeletal-control node can run
after an existing single-node locomotion instance. UE 5.8's
`USkeletalMeshComponent::EvaluatePostProcessMeshInstance` copies the main pose,
curves, and attributes into `FAnimNode_LinkedInputPose` before evaluating the
post-process instance. A graph would be Input Pose -> local/component conversion
-> `UAnimGraphNode_KawaiiPhysics` -> local conversion -> result, assigned as the
mesh's post-process class. The plugin exposes that graph node in
`Source/KawaiiPhysicsEd/Public/AnimGraphNode_KawaiiPhysics.h`.

Editor Python can create an AnimBlueprint asset via `AnimBlueprintFactory`, but
asset creation alone does not author or connect its animation graph. A complete
Python-only node/pin authoring path was not established here; it would need a
verified editor graph API or a small editor C++ helper. Prefer the native proxy
for this project rather than assuming Python can produce a valid graph unaided.
