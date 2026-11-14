#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Animation/PoseSnapshot.h"
#include "SeleneSecondaryAnimInstance.generated.h"

/**
 * Single-node locomotion (blend space / jump / fall / land, still driven by ASeleneCharacter through
 * GetSingleNodeInstance) followed by Kawaii Physics secondary motion for hair, braid, skirt panels,
 * ribbons and wings — with no hand-authored Animation Blueprint. The proxy builds a native graph:
 *   SingleNode -> DefaultSlot -> UpperBody (masked slot) -> LocalToComponent -> KawaiiPhysics (per chain) -> ComponentToLocal
 * Without chains, UpperBody is the output. Its base keeps advancing during dynamic slot montages.
 * Chains and body colliders come from the owning ASeleneCharacter's active roster entry
 * (Config/DefaultGame.ini, SecondaryChains / SecondaryColliders).
 */
UCLASS(Transient, NotBlueprintable)
class SELENE_API USeleneSecondaryAnimInstance : public UAnimSingleNodeInstance
{
	GENERATED_BODY()

public:
	/** Editor diagnostics: explicitly evaluate a component, then report time/rate/playing.
	 * Negative DeltaSeconds only reads state. The probe disables automatic component ticks. */
	UFUNCTION(BlueprintCallable, Category = "Selene|Animation|Diagnostics", meta = (DevelopmentOnly))
	static FVector ProbeSingleNodeComponent(USkeletalMeshComponent* Component, float DeltaSeconds = -1.f);

	/** Unlike the engine version, a loop change keeps slot montages (upper-body swings, transitions) playing. */
	virtual void SetAnimationAsset(UAnimationAsset* NewAsset, bool bIsLooping = true, float InPlayRate = 1.f) override;

	/** Blends from the pose shown right now to whatever plays next, over Seconds (inertial-style crossfade). */
	void StartCrossfade(float Seconds);

	/** 0: UpperBody montages drive only the spine and above. 1: they drive the whole body (standing / committed). */
	float LegWeight = 0.f;

	/** Name of the masked slot: spine and everything above it, legs keep the base locomotion. */
	static const FName UpperBodySlot;
	/** Bones replaced by the reference pose because the evaluated pose was NaN, since the last call (all instances). */
	static int32 ConsumeNaNBones();

protected:
	virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
	virtual void Montage_Advance(float DeltaTime) override;
	virtual void NativeUpdateAnimation(float DeltaSeconds) override;

private:
	friend struct FSeleneSecondaryProxy;
	FPoseSnapshot PendingSnapshot;
	float PendingCrossfade = 0.f;

	/** selene.SecondaryDebug 1: every 0.5 s log each chain's largest sim-vs-animated displacement (cm). */
	float DebugTimer = 0.f;
	TMap<FName, float> DebugMaxSwing;
};
