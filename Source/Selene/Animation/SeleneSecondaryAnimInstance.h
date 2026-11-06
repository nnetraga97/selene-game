#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "SeleneSecondaryAnimInstance.generated.h"

/**
 * Single-node locomotion (blend space / jump / fall / land, still driven by ASeleneCharacter through
 * GetSingleNodeInstance) followed by Kawaii Physics secondary motion for hair, braid, skirt panels,
 * ribbons and wings — with no hand-authored Animation Blueprint. The proxy builds a native graph:
 *   SingleNode -> LocalToComponent -> KawaiiPhysics (one node per chain) -> ComponentToLocal -> output
 * Chains and body colliders come from the owning ASeleneCharacter's active roster entry
 * (Config/DefaultGame.ini, SecondaryChains / SecondaryColliders).
 */
UCLASS(Transient, NotBlueprintable)
class SELENE_API USeleneSecondaryAnimInstance : public UAnimSingleNodeInstance
{
	GENERATED_BODY()

protected:
	virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
	virtual void NativeUpdateAnimation(float DeltaSeconds) override;

private:
	/** selene.SecondaryDebug 1: every 0.5 s log each chain's largest sim-vs-animated displacement (cm). */
	float DebugTimer = 0.f;
	TMap<FName, float> DebugMaxSwing;
};
