#pragma once

#include "CoreMinimal.h"
#include "Curves/CurveFloat.h"
#include "Curves/CurveLinearColor.h"
#include "GameFramework/Actor.h"
#include "SeleneTimeOfDay.generated.h"

class UDirectionalLightComponent;
class USkyAtmosphereComponent;
class USkyLightComponent;
class UExponentialHeightFogComponent;
class UVolumetricCloudComponent;
class UPostProcessComponent;
class UMaterialParameterCollection;
class UMaterialParameterCollectionInstance;
class UCanvas;
class ASeleneTimeOfDay;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FSeleneTimeOfDayUpdated, ASeleneTimeOfDay*, Controller);
DECLARE_MULTICAST_DELEGATE_OneParam(FSeleneLightingUpdated, ASeleneTimeOfDay*);

/** Place one in the persistent level. All lighting is movable; no baked lighting is required. */
UCLASS(Blueprintable)
class SELENE_API ASeleneTimeOfDay : public AActor
{
	GENERATED_BODY()

public:
	ASeleneTimeOfDay();
	virtual void Tick(float DeltaSeconds) override;
	virtual void OnConstruction(const FTransform& Transform) override;

	UFUNCTION(BlueprintPure, Category="Selene|Time of Day", meta=(WorldContext="WorldContext"))
	static ASeleneTimeOfDay* Get(const UObject* WorldContext);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Lighting")
	TObjectPtr<UDirectionalLightComponent> Sun;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Lighting")
	TObjectPtr<UDirectionalLightComponent> Moon;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Lighting")
	TObjectPtr<USkyAtmosphereComponent> SkyAtmosphere;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Lighting")
	TObjectPtr<USkyLightComponent> SkyLight;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Lighting")
	TObjectPtr<UExponentialHeightFogComponent> Fog;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Lighting")
	TObjectPtr<UVolumetricCloudComponent> Clouds;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Lighting")
	TObjectPtr<UPostProcessComponent> PostProcess;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Time", meta=(ClampMin="0", ClampMax="24", UIMax="23.999"))
	float Hour = 12.0f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Time", meta=(ClampMin="0.01", Units="min"))
	float DayLengthMinutes = 24.0f;
	/** Negative speed runs time backwards; zero holds the current hour. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Time")
	float Speed = 1.0f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Time")
	bool bPaused = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Orbit", meta=(ClampMin="-89", ClampMax="89", Units="deg"))
	float Latitude = 35.0f;
	/** Yaw of north from world +X; east is +Y at zero offset. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Orbit", meta=(Units="deg"))
	float NorthOffset = 0.0f;
	/** Fixed seasonal solar declination (effective axial tilt), not an annual simulation. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Orbit", meta=(ClampMin="-23.44", ClampMax="23.44", Units="deg"))
	float AxialTilt = 5.35f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Lighting")
	bool bEnableVolumetricClouds = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Lighting")
	bool bEnableVolumetricFog = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Lighting")
	FLinearColor MoonLightColor = FLinearColor(0.48f, 0.63f, 1.0f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Curves")
	FRuntimeFloatCurve SunIntensity;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Curves")
	FRuntimeCurveLinearColor SunColor;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Curves")
	FRuntimeFloatCurve MoonIntensity;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Curves")
	FRuntimeFloatCurve SkyLightIntensity;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Curves")
	FRuntimeFloatCurve FogDensity;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Curves")
	FRuntimeCurveLinearColor FogInscatteringColor;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Curves")
	FRuntimeFloatCurve ExposureBias;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Curves")
	FRuntimeFloatCurve NightFactor;

	/** Optional parameters: Hour, NightFactor, SunDirection, SunColor, MoonDirection, MoonColor. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Materials")
	TObjectPtr<UMaterialParameterCollection> TimeOfDayMPC;
	UPROPERTY(BlueprintAssignable, Category="Selene|Time of Day")
	FSeleneTimeOfDayUpdated OnTimeOfDayUpdated;
	/** Native listeners avoid the Blueprint multicast's invocation-list copy for large light populations. */
	FSeleneLightingUpdated OnLightingUpdated;

	UFUNCTION(BlueprintPure, Category="Selene|Time of Day")
	float GetHour() const { return Hour; }
	UFUNCTION(BlueprintPure, Category="Selene|Time of Day")
	float GetNightFactor() const { return CurrentNightFactor; }
	/** World-space unit vectors pointing TOWARDS the celestial bodies (opposite light travel). */
	UFUNCTION(BlueprintPure, Category="Selene|Time of Day")
	FVector GetSunDirection() const { return CurrentSunDirection; }
	UFUNCTION(BlueprintPure, Category="Selene|Time of Day")
	FVector GetMoonDirection() const { return -CurrentSunDirection; }
	UFUNCTION(BlueprintPure, Category="Selene|Time of Day")
	FLinearColor GetSunColor() const { return CurrentSunColor; }
	UFUNCTION(BlueprintPure, Category="Selene|Time of Day")
	FLinearColor GetMoonColor() const { return MoonLightColor; }
	UFUNCTION(BlueprintPure, Category="Selene|Time of Day")
	float GetSunIntensity() const { return SunLux; }

	UFUNCTION(BlueprintCallable, Category="Selene|Time of Day")
	void SetHour(float NewHour);
	void ToggleOverlay();
	void PrintState() const;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	void UpdateLighting();
	void UpdateMPC();
	void RefreshOverlayText();
	void DrawOverlay(UCanvas* Canvas, APlayerController* PlayerController);
	bool bPrimaryController = true;
	bool bOverlay = false;
	float CurrentNightFactor = 0.0f;
	float SunLux = 0.0f;
	FVector CurrentSunDirection = FVector::UpVector;
	FLinearColor CurrentSunColor = FLinearColor::White;
	double PreciseHour = 12.0;
	float LastPublishedHour = 12.0f;
	float OverlayElapsed = 0.0f;
	FString OverlayText;
	FDelegateHandle OverlayHandle;
	TWeakObjectPtr<UMaterialParameterCollection> CachedMPC;
	UPROPERTY(Transient)
	TObjectPtr<UMaterialParameterCollectionInstance> MPCInstance;
	uint8 MPCParameters = 0;
};
