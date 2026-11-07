#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "SeleneSecondaryAnimInstance.generated.h"

/**
 * Single-node locomotion (blend space / jump / fall / land, still driven by ASeleneCharacter through
 * GetSingleNodeInstance) followed by Kawaii Physics secondary motion for hair, braid, skirt panels,
 * ribbons and wings — with no hand-authored Animation Blueprint. The proxy builds a native graph:
 *   SingleNode -> DefaultSlot -> LocalToComponent -> KawaiiPhysics (per chain) -> ComponentToLocal
 * Without chains, DefaultSlot is the output. Its base keeps advancing during dynamic slot montages.
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

protected:
	virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
	virtual void Montage_Advance(float DeltaTime) override;
	virtual void NativeUpdateAnimation(float DeltaSeconds) override;

private:
	/** selene.SecondaryDebug 1: every 0.5 s log each chain's largest sim-vs-animated displacement (cm). */
	float DebugTimer = 0.f;
	TMap<FName, float> DebugMaxSwing;
};
