#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Curves/CurveFloat.h"
#include "Engine/EngineTypes.h"
#include "SeleneNightLightComponent.generated.h"

class ASeleneTimeOfDay;
class ULocalLightComponent;
class UMaterialInstanceDynamic;

/** Scales owned point/spot/rect lights and explicitly selected emissive meshes. No component tick. */
UCLASS(ClassGroup=(Selene), meta=(BlueprintSpawnableComponent))
class SELENE_API USeleneNightLightComponent : public UActorComponent
{
	GENERATED_BODY()
public:
	USeleneNightLightComponent();
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Night Lighting")
	FRuntimeFloatCurve LightIntensityMultiplier;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Night Lighting")
	FRuntimeFloatCurve EmissiveStrength;
	/** Only these meshes on the owning actor receive dynamic material instances. */
	UPROPERTY(EditAnywhere, Category="Night Lighting", meta=(UseComponentPicker, AllowedClasses="/Script/Engine.MeshComponent"))
	TArray<FComponentReference> EmissiveMeshes;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Night Lighting")
	FName EmissiveParameterName = TEXT("EmissiveStrength");

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	void FindController();
	void HandleTimeOfDayUpdated(ASeleneTimeOfDay* UpdatedController);
	TWeakObjectPtr<ASeleneTimeOfDay> Controller;
	FDelegateHandle LightingUpdatedHandle;
	TArray<TWeakObjectPtr<ULocalLightComponent>> Lights;
	TArray<float> BaseIntensities;
	UPROPERTY(Transient)
	TArray<TObjectPtr<UMaterialInstanceDynamic>> Materials;
	FTimerHandle FindControllerTimer;
	float LastNightFactor = -1.0f;
};
