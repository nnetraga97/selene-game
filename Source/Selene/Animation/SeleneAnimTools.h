#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SeleneAnimTools.generated.h"

class UBlendSpace;

/** Editor helpers callable from Python (Tools/Unreal). */
UCLASS()
class SELENE_API USeleneAnimTools : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/**
	 * Rebuild a blend space's runtime sample grid after its samples were set from script. Setting sample_data from
	 * Python leaves the grid empty, and an empty grid evaluates to the reference (T) pose. Returns the grid size.
	 */
	UFUNCTION(BlueprintCallable, Category = "Selene|Animation")
	static int32 RebuildBlendSpace(UBlendSpace* BlendSpace);
};
