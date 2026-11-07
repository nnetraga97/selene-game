#include "Lighting/SeleneTimeOfDay.h"

#include "Selene.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/PostProcessComponent.h"
#include "Components/SkyAtmosphereComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/VolumetricCloudComponent.h"
#include "Debug/DebugDrawService.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "Misc/CommandLine.h"
#include "String/LexFromString.h"
#include "Misc/Parse.h"

namespace SeleneTimeOfDay
{
	const FName ParameterNames[] = {
		TEXT("Hour"), TEXT("NightFactor"), TEXT("SunDirection"),
		TEXT("SunColor"), TEXT("MoonDirection"), TEXT("MoonColor")
	};

	float FiniteOr(float Value, float Fallback)
	{
		return FMath::IsFinite(Value) ? Value : Fallback;
	}

	double WrapHour(double Value)
	{
		if (!FMath::IsFinite(Value)) { return 12.0; }
		const double Wrapped = FMath::Fmod(Value, 24.0);
		return Wrapped < 0.0 ? Wrapped + 24.0 : Wrapped;
	}

	void AddKey(FRichCurve& Curve, float Hour, float Value)
	{
		const FKeyHandle Handle = Curve.AddKey(Hour, Value);
		Curve.SetKeyInterpMode(Handle, RCIM_Cubic);
		// Zero user tangents give bounded smoothstep segments, including across midnight.
		Curve.SetKeyTangentMode(Handle, RCTM_User);
		Curve.GetKey(Handle).ArriveTangent = 0.0f;
		Curve.GetKey(Handle).LeaveTangent = 0.0f;
	}

	void AddColorKey(FRuntimeCurveLinearColor& Curve, float Hour, const FLinearColor& Value)
	{
		for (int32 Channel = 0; Channel < 4; ++Channel)
		{
			AddKey(Curve.ColorCurves[Channel], Hour, Value.Component(Channel));
		}
	}

	float Evaluate(const FRuntimeFloatCurve& Curve, float Hour, float Fallback)
	{
		return FiniteOr(Curve.GetRichCurveConst()->Eval(Hour, Fallback), Fallback);
	}

	ASeleneTimeOfDay* Resolve(UWorld* World)
	{
		ASeleneTimeOfDay* Controller = ASeleneTimeOfDay::Get(World);
		if (!Controller)
		{
			FPlatformMisc::LowLevelOutputDebugString(TEXT("Selene: place a SeleneTimeOfDay actor in this world.\n"));
		}
		return Controller;
	}

	bool ParseValue(const TArray<FString>& Args, float& Value)
	{
		return Args.Num() == 1 && LexTryParseString(Value, *Args[0]) && FMath::IsFinite(Value);
	}

	// Deliberately neither ECVF_Cheat nor guarded by UE_BUILD_SHIPPING.
	FAutoConsoleCommandWithWorldAndArgs PauseCommand(TEXT("tod.pause"), TEXT("tod.pause [0|1]: toggle or set pause"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (ASeleneTimeOfDay* Controller = Resolve(World))
			{
				if (Args.IsEmpty()) { Controller->bPaused = !Controller->bPaused; }
				else if (Args.Num() == 1 && (Args[0] == TEXT("0") || Args[0] == TEXT("1")))
				{ Controller->bPaused = Args[0] == TEXT("1"); }
				else { FPlatformMisc::LowLevelOutputDebugString(TEXT("Usage: tod.pause [0|1]\n")); return; }
				Controller->PrintState();
			}
		}));
	FAutoConsoleCommandWithWorldAndArgs SpeedCommand(TEXT("tod.speed"), TEXT("tod.speed <finite multiplier>; negative reverses time"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			float Value;
			if (!ParseValue(Args, Value)) { FPlatformMisc::LowLevelOutputDebugString(TEXT("Usage: tod.speed <finite multiplier>\n")); return; }
			if (ASeleneTimeOfDay* Controller = Resolve(World)) { Controller->Speed = Value; Controller->PrintState(); }
		}));
	FAutoConsoleCommandWithWorldAndArgs SetCommand(TEXT("tod.set"), TEXT("tod.set <hour>; wraps into [0,24)"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			float Value;
			if (!ParseValue(Args, Value)) { FPlatformMisc::LowLevelOutputDebugString(TEXT("Usage: tod.set <finite hour>\n")); return; }
			if (ASeleneTimeOfDay* Controller = Resolve(World)) { Controller->SetHour(Value); Controller->PrintState(); }
		}));
	FAutoConsoleCommandWithWorldAndArgs DayLengthCommand(TEXT("tod.daylength"), TEXT("tod.daylength <minutes>; minimum 0.01"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			float Value;
			if (!ParseValue(Args, Value) || Value < 0.01f)
			{ FPlatformMisc::LowLevelOutputDebugString(TEXT("Usage: tod.daylength <minutes >= 0.01>\n")); return; }
			if (ASeleneTimeOfDay* Controller = Resolve(World)) { Controller->DayLengthMinutes = Value; Controller->PrintState(); }
		}));
	FAutoConsoleCommandWithWorldAndArgs PrintCommand(TEXT("tod.print"), TEXT("Print time, speed, pause, night factor, and sun lux"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>&, UWorld* World)
		{
			if (ASeleneTimeOfDay* Controller = Resolve(World)) { Controller->PrintState(); }
		}));
	FAutoConsoleCommandWithWorldAndArgs OverlayCommand(TEXT("tod.overlay"), TEXT("Toggle time-of-day overlay (Development)"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>&, UWorld* World)
		{
			if (ASeleneTimeOfDay* Controller = Resolve(World)) { Controller->ToggleOverlay(); }
		}));
}

ASeleneTimeOfDay::ASeleneTimeOfDay()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = true;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent->SetMobility(EComponentMobility::Movable);
	Sun = CreateDefaultSubobject<UDirectionalLightComponent>(TEXT("Sun"));
	Moon = CreateDefaultSubobject<UDirectionalLightComponent>(TEXT("Moon"));
	SkyAtmosphere = CreateDefaultSubobject<USkyAtmosphereComponent>(TEXT("SkyAtmosphere"));
	SkyLight = CreateDefaultSubobject<USkyLightComponent>(TEXT("SkyLight"));
	Fog = CreateDefaultSubobject<UExponentialHeightFogComponent>(TEXT("Fog"));
	Clouds = CreateDefaultSubobject<UVolumetricCloudComponent>(TEXT("Clouds"));
	PostProcess = CreateDefaultSubobject<UPostProcessComponent>(TEXT("PostProcess"));
	USceneComponent* Components[] = { Sun, Moon, SkyAtmosphere, SkyLight, Fog, Clouds, PostProcess };
	for (USceneComponent* Component : Components)
	{
		Component->SetupAttachment(RootComponent);
		Component->SetMobility(EComponentMobility::Movable);
	}
	Sun->SetAtmosphereSunLight(true);
	Sun->SetAtmosphereSunLightIndex(0);
	Sun->SetForwardShadingPriority(1);
	Sun->SetLightSourceAngle(1.0f);
	Moon->SetAtmosphereSunLight(true);
	Moon->SetAtmosphereSunLightIndex(1);
	Moon->SetForwardShadingPriority(0);
	// The moon lights atmosphere and geometry but does not create a second blazing solar disk.
	Moon->SetAtmosphereSunDiskColorScale(FLinearColor::Black);
	Moon->SetLightSourceAngle(1.5f);
	Moon->SetLightColor(MoonLightColor);
	SkyLight->SourceType = SLS_CapturedScene;
	SkyLight->CubemapResolution = 128;
	SkyLight->SetRealTimeCapture(true);
	SkyLight->bLowerHemisphereIsBlack = true;
	SkyLight->LowerHemisphereColor = FLinearColor(0.015f, 0.02f, 0.035f);
	Fog->SetVolumetricFog(false);
	Fog->SetFogHeightFalloff(0.25f);
	Clouds->SetVisibility(false);
	Clouds->ViewSampleCountScale = 0.5f;
	Clouds->ShadowViewSampleCountScale = 0.5f;
	PostProcess->bUnbound = true;
	PostProcess->BlendWeight = 1.0f;
	FPostProcessSettings& Grade = PostProcess->Settings;
	Grade.bOverride_AutoExposureBias = true;
	Grade.bOverride_AutoExposureMinBrightness = true;
	Grade.bOverride_AutoExposureMaxBrightness = true;
	// Project enables extended luminance range, so these limits are EV100.
	Grade.AutoExposureMinBrightness = -2.0f;
	Grade.AutoExposureMaxBrightness = 16.0f;
	Grade.bOverride_AutoExposureSpeedUp = true;
	Grade.bOverride_AutoExposureSpeedDown = true;
	Grade.AutoExposureSpeedUp = 1.5f;
	Grade.AutoExposureSpeedDown = 0.6f;
	Grade.bOverride_ColorSaturation = true;
	Grade.ColorSaturation = FVector4(1.02f, 1.02f, 1.02f, 1.0f);
	Grade.bOverride_ColorContrast = true;
	Grade.ColorContrast = FVector4(0.96f, 0.96f, 0.96f, 1.0f);
	Grade.bOverride_ColorGainShadows = true;
	Grade.ColorGainShadows = FVector4(0.96f, 1.0f, 1.06f, 1.0f);
	Grade.bOverride_ColorGainHighlights = true;
	Grade.ColorGainHighlights = FVector4(1.04f, 1.01f, 0.96f, 1.0f);

	struct FLightingKey
	{
		float Hour, Sun, Moon, Sky, Fog, Exposure, Night;
		FLinearColor SunTint, FogTint;
	};
	// Colors are linear RGB, alpha 1. Keys at 0 and 24 match with zero tangents.
	const FLightingKey Keys[] = {
		{ 0,     0, .7f, .45f, .012f, -.25f, 1,    {1,.38f,.20f}, {.12f,.18f,.32f} },
		{ 5,     0, .45f,.5f,  .018f, 0,     .9f,  {1,.40f,.22f}, {.24f,.25f,.38f} },
		{ 6,     0, .15f,.65f, .018f, .3f,   .45f, {1,.48f,.28f}, {.58f,.40f,.42f} },
		{ 8, 30000, 0,  .9f,  .010f, .15f,  0,    {1,.82f,.64f}, {.58f,.68f,.82f} },
		{12.25f,65000,0,1,    .008f, 0,     0,    {1,.95f,.86f}, {.62f,.74f,.90f} },
		{17, 18000, 0,  .8f,  .012f, .1f,   .05f, {1,.65f,.36f}, {.72f,.51f,.40f} },
		{18.5f,  0, .15f,.6f, .016f, -.15f, .65f, {1,.32f,.14f}, {.38f,.27f,.42f} },
		{20,     0, .7f,.45f, .012f, -.25f, 1,    {1,.38f,.20f}, {.12f,.18f,.32f} },
		{24,     0, .7f,.45f, .012f, -.25f, 1,    {1,.38f,.20f}, {.12f,.18f,.32f} }
	};
	for (const FLightingKey& Key : Keys)
	{
		SeleneTimeOfDay::AddKey(*SunIntensity.GetRichCurve(), Key.Hour, Key.Sun);
		SeleneTimeOfDay::AddKey(*MoonIntensity.GetRichCurve(), Key.Hour, Key.Moon);
		SeleneTimeOfDay::AddKey(*SkyLightIntensity.GetRichCurve(), Key.Hour, Key.Sky);
		SeleneTimeOfDay::AddKey(*FogDensity.GetRichCurve(), Key.Hour, Key.Fog);
		SeleneTimeOfDay::AddKey(*ExposureBias.GetRichCurve(), Key.Hour, Key.Exposure);
		SeleneTimeOfDay::AddKey(*NightFactor.GetRichCurve(), Key.Hour, Key.Night);
		SeleneTimeOfDay::AddColorKey(SunColor, Key.Hour, Key.SunTint);
		SeleneTimeOfDay::AddColorKey(FogInscatteringColor, Key.Hour, Key.FogTint);
	}
}

ASeleneTimeOfDay* ASeleneTimeOfDay::Get(const UObject* WorldContext)
{
	UWorld* World = GEngine && WorldContext
		? GEngine->GetWorldFromContextObject(WorldContext, EGetWorldErrorMode::ReturnNull) : nullptr;
	if (!World) { return nullptr; }
	for (TActorIterator<ASeleneTimeOfDay> It(World); It; ++It)
	{
		if (IsValid(*It) && It->bPrimaryController) { return *It; }
	}
	return nullptr;
}

void ASeleneTimeOfDay::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	SetHour(Hour);
}

void ASeleneTimeOfDay::BeginPlay()
{
	Super::BeginPlay();
	if (Get(this) != this)
	{
		bPrimaryController = false;
		SetActorTickEnabled(false);
		RootComponent->SetVisibility(false, true);
		PostProcess->bEnabled = false;
		UE_LOG(LogSelene, Warning, TEXT("Duplicate SeleneTimeOfDay %s disabled; place one in the persistent level."), *GetName());
		return;
	}
	// This is a renderer-wide switch. Set once, never recapture manually every frame.
	if (IConsoleVariable* TimeSlice = IConsoleManager::Get().FindConsoleVariable(TEXT("r.SkyLight.RealTimeReflectionCapture.TimeSlice")))
	{
		TimeSlice->Set(1, ECVF_SetByCode);
	}
	float Value;
	if (FParse::Value(FCommandLine::Get(), TEXT("TodHour="), Value) && FMath::IsFinite(Value)) { Hour = Value; }
	if (FParse::Value(FCommandLine::Get(), TEXT("TodSpeed="), Value) && FMath::IsFinite(Value)) { Speed = Value; }
	if (FParse::Param(FCommandLine::Get(), TEXT("TodPause"))) { bPaused = true; }
	OverlayText.Reserve(256);
	SetHour(Hour);
}

void ASeleneTimeOfDay::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (OverlayHandle.IsValid()) { UDebugDrawService::Unregister(OverlayHandle); OverlayHandle.Reset(); }
	Super::EndPlay(EndPlayReason);
}

void ASeleneTimeOfDay::SetHour(float NewHour)
{
	PreciseHour = SeleneTimeOfDay::WrapHour(NewHour);
	Hour = static_cast<float>(PreciseHour);
	// Float rounding immediately below midnight must not publish 24.
	if (Hour >= 24.0f) { Hour = 0.0f; PreciseHour = 0.0; }
	LastPublishedHour = Hour;
	if (bPrimaryController) { UpdateLighting(); }
}

void ASeleneTimeOfDay::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bPrimaryController) { return; }
	if (Hour != LastPublishedHour) { PreciseHour = SeleneTimeOfDay::WrapHour(Hour); }
	DayLengthMinutes = FMath::Max(0.01f, SeleneTimeOfDay::FiniteOr(DayLengthMinutes, 24.0f));
	Speed = SeleneTimeOfDay::FiniteOr(Speed, 1.0f);
	if (!bPaused)
	{
		PreciseHour = SeleneTimeOfDay::WrapHour(PreciseHour +
			static_cast<double>(SeleneTimeOfDay::FiniteOr(DeltaSeconds, 0.0f)) * Speed * 24.0 / (DayLengthMinutes * 60.0));
	}
	Hour = static_cast<float>(PreciseHour);
	if (Hour >= 24.0f) { Hour = 0.0f; }
	LastPublishedHour = Hour;
	UpdateLighting();
	if (bOverlay)
	{
		OverlayElapsed += DeltaSeconds;
		if (OverlayElapsed >= 0.25f) { OverlayElapsed = 0.0f; RefreshOverlayText(); }
	}
}

void ASeleneTimeOfDay::UpdateLighting()
{
	using namespace SeleneTimeOfDay;
	const double Phi = FMath::DegreesToRadians(FMath::Clamp(FiniteOr(Latitude, 35.0f), -89.0f, 89.0f));
	const double Declination = FMath::DegreesToRadians(FMath::Clamp(FiniteOr(AxialTilt, 5.35f), -23.44f, 23.44f));
	const double HourAngle = FMath::DegreesToRadians(15.0 * (Hour - 12.25));
	const double North = FMath::Cos(Phi) * FMath::Sin(Declination) - FMath::Sin(Phi) * FMath::Cos(Declination) * FMath::Cos(HourAngle);
	const double East = -FMath::Cos(Declination) * FMath::Sin(HourAngle);
	const double Up = FMath::Sin(Phi) * FMath::Sin(Declination) + FMath::Cos(Phi) * FMath::Cos(Declination) * FMath::Cos(HourAngle);
	CurrentSunDirection = FRotator(0.0, FiniteOr(NorthOffset, 0.0f), 0.0).RotateVector(FVector(North, East, Up)).GetSafeNormal();
	Sun->SetWorldRotation((-CurrentSunDirection).Rotation());
	Moon->SetWorldRotation(CurrentSunDirection.Rotation());
	// Smoothly suppress below-horizon light, including when artists change latitude/tilt.
	const float SunHorizon = FMath::SmoothStep(0.0f, 0.035f, static_cast<float>(Up));
	const float MoonHorizon = FMath::SmoothStep(0.0f, 0.035f, static_cast<float>(-Up));
	SunLux = FMath::Max(0.0f, Evaluate(SunIntensity, Hour, 0.0f)) * SunHorizon;
	CurrentSunColor = SunColor.GetLinearColorValue(Hour).GetClamped(0.0f, 1.0f);
	CurrentNightFactor = FMath::Clamp(Evaluate(NightFactor, Hour, 0.0f), 0.0f, 1.0f);
	Sun->SetIntensity(SunLux);
	Sun->SetLightColor(CurrentSunColor);
	Moon->SetIntensity(FMath::Max(0.0f, Evaluate(MoonIntensity, Hour, 0.0f)) * MoonHorizon);
	Moon->SetLightColor(MoonLightColor);
	SkyLight->SetIntensity(FMath::Max(0.0f, Evaluate(SkyLightIntensity, Hour, 1.0f)));
	Fog->SetFogDensity(FMath::Clamp(Evaluate(FogDensity, Hour, 0.01f), 0.0f, 1.0f));
	Fog->SetFogInscatteringColor(FogInscatteringColor.GetLinearColorValue(Hour).GetClamped(0.0f, 1.0f));
	Fog->SetVolumetricFog(bEnableVolumetricFog);
	Clouds->SetVisibility(bEnableVolumetricClouds);
	PostProcess->Settings.AutoExposureBias = Evaluate(ExposureBias, Hour, 0.0f);
	UpdateMPC();
	OnLightingUpdated.Broadcast(this);
	OnTimeOfDayUpdated.Broadcast(this);
}

void ASeleneTimeOfDay::UpdateMPC()
{
	using namespace SeleneTimeOfDay;
	if (!TimeOfDayMPC || !GetWorld())
	{
		CachedMPC.Reset(); MPCInstance = nullptr; MPCParameters = 0;
		return;
	}
	if (CachedMPC.Get() != TimeOfDayMPC || !MPCInstance)
	{
		CachedMPC = TimeOfDayMPC;
		MPCInstance = GetWorld()->GetParameterCollectionInstance(TimeOfDayMPC);
		MPCParameters = 0;
		for (int32 Index = 0; Index < 6; ++Index)
		{
			const bool bExists = Index < 2
				? TimeOfDayMPC->GetScalarParameterByName(ParameterNames[Index]) != nullptr
				: TimeOfDayMPC->GetVectorParameterByName(ParameterNames[Index]) != nullptr;
			if (bExists) { MPCParameters |= 1 << Index; }
		}
	}
	if (!MPCInstance) { return; }
	if (MPCParameters & (1 << 0)) { MPCInstance->SetScalarParameterValue(ParameterNames[0], Hour); }
	if (MPCParameters & (1 << 1)) { MPCInstance->SetScalarParameterValue(ParameterNames[1], CurrentNightFactor); }
	if (MPCParameters & (1 << 2)) { MPCInstance->SetVectorParameterValue(ParameterNames[2], FLinearColor(CurrentSunDirection)); }
	if (MPCParameters & (1 << 3)) { MPCInstance->SetVectorParameterValue(ParameterNames[3], CurrentSunColor); }
	if (MPCParameters & (1 << 4)) { MPCInstance->SetVectorParameterValue(ParameterNames[4], FLinearColor(-CurrentSunDirection)); }
	if (MPCParameters & (1 << 5)) { MPCInstance->SetVectorParameterValue(ParameterNames[5], MoonLightColor); }
}

void ASeleneTimeOfDay::PrintState() const
{
	// Unlike UE_LOG, this remains a useful output path in the default Shipping target.
	FPlatformMisc::LowLevelOutputDebugStringf(TEXT("Selene TOD: hour=%.3f speed=%.3f paused=%d night=%.3f sun=%.1f lux daylength=%.3f min\n"),
		Hour, Speed, bPaused ? 1 : 0, CurrentNightFactor, SunLux, DayLengthMinutes);
}

void ASeleneTimeOfDay::RefreshOverlayText()
{
	TCHAR Buffer[256];
	FCString::Snprintf(Buffer, UE_ARRAY_COUNT(Buffer), TEXT("Selene | Hour %.2f | Speed %.2fx | Paused %s | Night %.3f | Sun %.0f lux"),
		Hour, Speed, bPaused ? TEXT("yes") : TEXT("no"), CurrentNightFactor, SunLux);
	OverlayText.Reset();
	OverlayText.Append(Buffer);
}

void ASeleneTimeOfDay::ToggleOverlay()
{
#if !UE_BUILD_SHIPPING
	if (!bPrimaryController) { return; }
	bOverlay = !bOverlay;
	if (bOverlay)
	{
		OverlayText.Reserve(256);
		RefreshOverlayText();
		OverlayHandle = UDebugDrawService::Register(TEXT("Game"), FDebugDrawDelegate::CreateUObject(this, &ASeleneTimeOfDay::DrawOverlay));
	}
	else if (OverlayHandle.IsValid())
	{
		UDebugDrawService::Unregister(OverlayHandle);
		OverlayHandle.Reset();
	}
#else
	PrintState();
#endif
}

void ASeleneTimeOfDay::DrawOverlay(UCanvas* Canvas, APlayerController* PlayerController)
{
#if !UE_BUILD_SHIPPING
	if (bOverlay && Canvas && PlayerController && PlayerController->GetWorld() == GetWorld() && GEngine)
	{
		Canvas->SetDrawColor(FColor::White);
		Canvas->DrawText(GEngine->GetSmallFont(), OverlayText, 24.0f, 32.0f);
	}
#endif
}
