#include "Lighting/SeleneNightLightComponent.h"

#include "Lighting/SeleneTimeOfDay.h"
#include "Components/LocalLightComponent.h"
#include "Components/MeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "TimerManager.h"

USeleneNightLightComponent::USeleneNightLightComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	const float Factors[] = { 0.0f, 0.5f, 1.0f };
	const float LightValues[] = { 0.0f, 0.35f, 1.0f };
	const float EmissiveValues[] = { 0.05f, 1.5f, 5.0f };
	for (int32 Index = 0; Index < 3; ++Index)
	{
		FRichCurve* Curves[] = { LightIntensityMultiplier.GetRichCurve(), EmissiveStrength.GetRichCurve() };
		const float Values[] = { LightValues[Index], EmissiveValues[Index] };
		for (int32 CurveIndex = 0; CurveIndex < 2; ++CurveIndex)
		{
			const FKeyHandle Key = Curves[CurveIndex]->AddKey(Factors[Index], Values[CurveIndex]);
			Curves[CurveIndex]->SetKeyInterpMode(Key, RCIM_Cubic);
			Curves[CurveIndex]->SetKeyTangentMode(Key, RCTM_User);
			Curves[CurveIndex]->GetKey(Key).ArriveTangent = 0.0f;
			Curves[CurveIndex]->GetKey(Key).LeaveTangent = 0.0f;
		}
	}
}

void USeleneNightLightComponent::BeginPlay()
{
	Super::BeginPlay();
	TInlineComponentArray<ULocalLightComponent*> OwnedLights(GetOwner());
	Lights.Reserve(OwnedLights.Num());
	BaseIntensities.Reserve(OwnedLights.Num());
	for (ULocalLightComponent* Light : OwnedLights)
	{
		// Stationary/static components cannot be relied on for fully dynamic intensity changes.
		Light->SetMobility(EComponentMobility::Movable);
		Lights.Add(Light);
		BaseIntensities.Add(Light->Intensity);
	}
	for (const FComponentReference& Reference : EmissiveMeshes)
	{
		UMeshComponent* Mesh = Cast<UMeshComponent>(Reference.GetComponent(GetOwner()));
		if (!Mesh || Mesh->GetOwner() != GetOwner()) { continue; }
		for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
		{
			UMaterialInterface* Material = Mesh->GetMaterial(Slot);
			float ExistingValue;
			if (!Material || !Material->GetScalarParameterValue(FMaterialParameterInfo(EmissiveParameterName), ExistingValue)) { continue; }
			if (UMaterialInstanceDynamic* DynamicMaterial = Mesh->CreateDynamicMaterialInstance(Slot))
			{
				Materials.AddUnique(DynamicMaterial);
			}
		}
	}
	FindController();
	// Handles a controller streamed/spawned after this actor or replaced later; no frame polling.
	GetWorld()->GetTimerManager().SetTimer(FindControllerTimer, this, &USeleneNightLightComponent::FindController, 1.0f, true);
}

void USeleneNightLightComponent::FindController()
{
	if (Controller.IsValid() && Controller->HasActorBegunPlay() && !Controller->IsActorBeingDestroyed()) { return; }
	if (Controller.IsValid()) { Controller->OnLightingUpdated.Remove(LightingUpdatedHandle); }
	Controller = ASeleneTimeOfDay::Get(this);
	if (Controller.IsValid())
	{
		LastNightFactor = -1.0f;
		LightingUpdatedHandle = Controller->OnLightingUpdated.AddUObject(this, &USeleneNightLightComponent::HandleTimeOfDayUpdated);
		HandleTimeOfDayUpdated(Controller.Get());
	}
}

void USeleneNightLightComponent::HandleTimeOfDayUpdated(ASeleneTimeOfDay* UpdatedController)
{
	if (!UpdatedController) { return; }
	const float Factor = UpdatedController->GetNightFactor();
	if (FMath::Abs(Factor - LastNightFactor) <= 0.005f) { return; }
	LastNightFactor = Factor;
	const float LightValue = LightIntensityMultiplier.GetRichCurveConst()->Eval(Factor, Factor);
	const float EmissiveValue = EmissiveStrength.GetRichCurveConst()->Eval(Factor, Factor);
	const float Multiplier = FMath::IsFinite(LightValue) ? FMath::Max(0.0f, LightValue) : 0.0f;
	const float Emission = FMath::IsFinite(EmissiveValue) ? FMath::Max(0.0f, EmissiveValue) : 0.0f;
	for (int32 Index = 0; Index < Lights.Num(); ++Index)
	{
		if (ULocalLightComponent* Light = Lights[Index].Get()) { Light->SetIntensity(BaseIntensities[Index] * Multiplier); }
	}
	for (UMaterialInstanceDynamic* Material : Materials)
	{
		if (IsValid(Material)) { Material->SetScalarParameterValue(EmissiveParameterName, Emission); }
	}
}

void USeleneNightLightComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (Controller.IsValid())
	{
		Controller->OnLightingUpdated.Remove(LightingUpdatedHandle);
	}
	if (GetWorld()) { GetWorld()->GetTimerManager().ClearTimer(FindControllerTimer); }
	Super::EndPlay(EndPlayReason);
}
