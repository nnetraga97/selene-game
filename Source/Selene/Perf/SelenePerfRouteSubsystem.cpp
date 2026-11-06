#include "Perf/SelenePerfRouteSubsystem.h"
#include "Perf/SelenePerfRoute.h"
#include "Selene.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/SplineComponent.h"
#include "Dom/JsonObject.h"
#include "DynamicRHI.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PawnMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "HAL/FileManager.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformMisc.h"
#include "HAL/PlatformTime.h"
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/CoreDelegates.h"
#include "Misc/EngineVersion.h"
#include "Misc/FileHelper.h"
#include "Misc/Guid.h"
#include "Misc/OutputDeviceNull.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "ProfilingDebugging/CsvProfiler.h"
#include "RenderTimer.h"
#include "Serialization/JsonSerializer.h"
#include "UnrealClient.h"
#include <cstdlib>

#if CSV_PROFILER && !UE_BUILD_SHIPPING
CSV_DEFINE_CATEGORY(SelenePerf, true);
#endif

namespace SelenePerf
{
	void RequestExit(uint8 Status)
	{
		FPlatformMisc::RequestExitWithStatus(false, Status);
#if PLATFORM_MAC
		// UE 5.8 Mac inherits the generic implementation, which ignores ReturnCode.
		// Call only after our files are closed and the CSV EndCapture future is ready.
		if (Status != 0) std::_Exit(Status);
#endif
	}
	FString SafeName(FString Value)
	{
		for (TCHAR& C : Value)
		{
			if (!FChar::IsAlnum(C) && C != TEXT('-') && C != TEXT('_') && C != TEXT('.')) C = TEXT('_');
		}
		return Value;
	}
	FString Quote(FString Value)
	{
		return TEXT("\"") + Value.Replace(TEXT("\""), TEXT("\"\"")) + TEXT("\"");
	}
	FString Timer(uint32 Cycles)
	{
		return Cycles ? FString::Printf(TEXT("%.6f"), FPlatformTime::ToMilliseconds(Cycles)) : FString();
	}
}

bool USelenePerfRouteSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* World = Cast<UWorld>(Outer);
	FString Name;
	return World && World->WorldType == EWorldType::Game &&
		FParse::Value(FCommandLine::Get(), TEXT("PerfRoute="), Name);
}

void USelenePerfRouteSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	const TCHAR* Cmd = FCommandLine::Get();
	FParse::Value(Cmd, TEXT("PerfRoute="), RouteName);
	FParse::Value(Cmd, TEXT("PerfCam="), Camera);
	Camera = Camera.ToUpper();
	bool bInvalidNumber = false;
	auto ParseNumber = [Cmd, &bInvalidNumber](const TCHAR* Key, auto& Value)
	{
		FString Raw;
		if (!FParse::Value(Cmd, Key, Raw)) return false;
		auto Parsed = Value;
		if (!LexTryParseString(Parsed, *Raw) || !FMath::IsFinite(static_cast<double>(Parsed))) bInvalidNumber = true;
		else Value = Parsed;
		return true;
	};
	ParseNumber(TEXT("PerfHour="), Hour);
	bTimeFlow = ParseNumber(TEXT("PerfTimeFlow="), TimeFlow);
	ParseNumber(TEXT("PerfLaps="), Laps);
	ParseNumber(TEXT("PerfWarmup="), Warmup);
	ParseNumber(TEXT("PerfSpeed="), Speed);
	OutDir = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Perf"));
	FParse::Value(Cmd, TEXT("PerfOut="), OutDir);
	OutDir = FPaths::ConvertRelativePathToFull(OutDir);
	const FString Timestamp = FDateTime::UtcNow().ToString(TEXT("%Y%m%dT%H%M%S")) + TEXT("-") + FGuid::NewGuid().ToString(EGuidFormats::Digits).Left(8);
	Stem = FPaths::Combine(OutDir, Timestamp + TEXT("_") + SelenePerf::SafeName(RouteName) + TEXT("_") + SelenePerf::SafeName(Camera) + TEXT("_") + SelenePerf::SafeName(FString::SanitizeFloat(Hour)));
	Meta = MakeShared<FJsonObject>();
	Meta->SetNumberField(TEXT("schema_version"), 1);
	Meta->SetStringField(TEXT("build_config"), LexToString(FApp::GetBuildConfiguration()));
	Meta->SetStringField(TEXT("engine_version"), FEngineVersion::Current().ToString());
	Meta->SetStringField(TEXT("map"), GetWorld()->GetPackage()->GetName());
	Meta->SetStringField(TEXT("route"), RouteName);
	Meta->SetStringField(TEXT("camera"), Camera);
	Meta->SetNumberField(TEXT("hour"), Hour);
	Meta->SetBoolField(TEXT("time_flow_enabled"), bTimeFlow);
	Meta->SetNumberField(TEXT("time_flow_speed"), TimeFlow);
	Meta->SetNumberField(TEXT("warm_laps"), Laps);
	Meta->SetNumberField(TEXT("warmup_seconds"), Warmup);
	Meta->SetNumberField(TEXT("speed_cm_s"), Speed);
	Meta->SetStringField(TEXT("command_line"), Cmd);
	Meta->SetStringField(TEXT("saved_dir"), FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir()));
	Meta->SetStringField(TEXT("frame_log"), Stem + TEXT(".frames.csv"));
	Meta->SetStringField(TEXT("status"), TEXT("running"));
	Meta->SetStringField(TEXT("timer_notes"), TEXT("delta_ms is monotonic begin-frame interval, not clamped game delta. GT/RT exclude engine idle accounting; GPU is latest completed GPU busy interval. Diagnostic timers may lag/repeat across frames; zero cycles are empty, never interpreted as zero cost. COLD is first recorded traversal after warm-up, not a cleared shader/OS cache."));
	CreatedAt = FPlatformTime::Seconds();
	FrameHandle = FCoreDelegates::OnBeginFrame.AddUObject(this, &ThisClass::OnFrame);
	if (!IFileManager::Get().MakeDirectory(*OutDir, true) || !WriteMeta())
	{
		Finish(TEXT("Cannot create output directory or metadata: ") + OutDir);
	}
	else if (bInvalidNumber || RouteName.IsEmpty() || (Camera != TEXT("3P") && Camera != TEXT("1P")) ||
		Laps < 1 || Laps > 1000 || !FMath::IsFinite(Speed) || Speed <= 0 ||
		!FMath::IsFinite(Warmup) || Warmup < 0 || !FMath::IsFinite(Hour) || Hour < 0 || Hour >= 24 ||
		!FMath::IsFinite(TimeFlow) || TimeFlow < 0)
	{
		Finish(TEXT("Invalid PerfRoute/PerfCam/PerfLaps/PerfSpeed/PerfWarmup/PerfHour/PerfTimeFlow option"));
	}
}

void USelenePerfRouteSubsystem::Deinitialize()
{
	FCoreDelegates::OnBeginFrame.Remove(FrameHandle);
	if (Phase != EPhase::Done)
	{
		ErrorText = TEXT("World destroyed before capture completed");
		Meta->SetStringField(TEXT("status"), TEXT("error"));
		Meta->SetStringField(TEXT("error"), ErrorText);
		WriteMeta();
		SelenePerf::RequestExit(2);
	}
	Super::Deinitialize();
}

void USelenePerfRouteSubsystem::Exec(const FString& Command)
{
	FOutputDeviceNull Output;
	// The exec path (including registered console commands) exists without an interactive Shipping console.
	if (!GEngine->Exec(GetWorld(), *Command, Output) && !Controller->ProcessConsoleExec(*Command, Output, nullptr))
	{
		const FString Warning = TEXT("Unknown/unhandled console command: ") + Command;
		Warnings.Add(Warning);
		UE_LOG(LogSelene, Warning, TEXT("%s"), *Warning);
		FPlatformMisc::LowLevelOutputDebugStringf(TEXT("SelenePerf WARNING: %s\n"), *Warning);
	}
}

bool USelenePerfRouteSubsystem::Start()
{
	for (TActorIterator<ASelenePerfRoute> It(GetWorld()); It; ++It)
	{
		if (It->RouteName == FName(*RouteName))
		{
			if (PerfRoute) { Finish(TEXT("Duplicate route name: ") + RouteName); return false; }
			PerfRoute = *It;
		}
	}
	if (!PerfRoute) { Finish(TEXT("Route not found: ") + RouteName); return false; }
	const float Length = PerfRoute->Route->GetSplineLength();
	if (!FMath::IsFinite(Length) || Length <= 0 || PerfRoute->Segments.IsEmpty())
	{
		Finish(TEXT("Route must have a nonzero spline and declared segments")); return false;
	}
	TArray<TSharedPtr<FJsonValue>> Segments;
	TSet<FName> Tags;
	for (const FSelenePerfSegment& S : PerfRoute->Segments)
	{
		if (S.Tag.IsNone() || Tags.Contains(S.Tag) || !FMath::IsFinite(S.StartDistance) || !FMath::IsFinite(S.EndDistance) ||
			S.StartDistance < 0 || S.EndDistance <= S.StartDistance || S.EndDistance > Length + 0.01f)
		{
			Finish(TEXT("Invalid or duplicate segment: ") + S.Tag.ToString()); return false;
		}
		for (const FSelenePerfSegment& Other : PerfRoute->Segments)
		{
			if (&S != &Other && S.StartDistance < Other.EndDistance && Other.StartDistance < S.EndDistance)
			{ Finish(TEXT("Overlapping segments are ambiguous")); return false; }
		}
		Tags.Add(S.Tag);
		TSharedPtr<FJsonObject> Item = MakeShared<FJsonObject>();
		Item->SetStringField(TEXT("tag"), S.Tag.ToString());
		Item->SetNumberField(TEXT("start_distance"), S.StartDistance);
		Item->SetNumberField(TEXT("end_distance"), S.EndDistance);
		Segments.Add(MakeShared<FJsonValueObject>(Item));
	}
	Meta->SetArrayField(TEXT("segments"), Segments);
	Meta->SetNumberField(TEXT("route_length_cm"), Length);
	SegmentCounts.Init(0, (Laps + 1) * PerfRoute->Segments.Num());
	Controller->SetIgnoreMoveInput(true);
	Controller->SetIgnoreLookInput(true);
	if (UPawnMovementComponent* Movement = Pawn->GetMovementComponent())
	{
		Movement->StopMovementImmediately();
		Movement->Deactivate();
		Movement->SetComponentTickEnabled(false);
	}
	Exec(TEXT("selene.Camera ") + Camera.ToLower());
	Exec(FString::Printf(TEXT("tod.set %g"), Hour));
	Exec(TEXT("tod.pause 1"));
	if (bTimeFlow)
	{
		Exec(FString::Printf(TEXT("tod.speed %g"), TimeFlow));
		Exec(TEXT("tod.pause 0"));
	}
	TSharedPtr<FJsonObject> Settings = MakeShared<FJsonObject>();
	// Include all registered sg.*, Lumen, VSM and Nanite settings, plus presentation controls.
	IConsoleManager::Get().ForEachConsoleObjectThatStartsWith(FConsoleObjectVisitor::CreateLambda(
		[&Settings](const TCHAR* Name, IConsoleObject* Object)
		{
			const FString Key(Name);
			if (Key.StartsWith(TEXT("sg.")) || Key.StartsWith(TEXT("r.Lumen.")) ||
				Key.StartsWith(TEXT("r.Shadow.Virtual.")) || Key.StartsWith(TEXT("r.Nanite")) ||
				Key.StartsWith(TEXT("r.RayTracing")) || Key.StartsWith(TEXT("r.DynamicRes.")) ||
				Key == TEXT("r.ScreenPercentage") || Key == TEXT("r.SecondaryScreenPercentage.GameViewport") ||
				Key == TEXT("r.AntiAliasingMethod") || Key == TEXT("r.DynamicGlobalIlluminationMethod") ||
				Key == TEXT("r.ReflectionMethod") || Key == TEXT("r.VSync") || Key == TEXT("t.MaxFPS"))
			{
				if (IConsoleVariable* Variable = Object->AsVariable()) Settings->SetStringField(Key, Variable->GetString());
			}
		}), TEXT(""));
	Meta->SetObjectField(TEXT("console_variables"), Settings);
	const FIntPoint Size = GEngine->GameViewport->Viewport->GetSizeXY();
	Meta->SetNumberField(TEXT("res_x"), Size.X);
	Meta->SetNumberField(TEXT("res_y"), Size.Y);
	Meta->SetStringField(TEXT("rhi"), GDynamicRHI ? GDynamicRHI->GetName() : TEXT("unknown"));
	Meta->SetStringField(TEXT("window_mode"), LexToString(static_cast<int32>(GEngine->GameViewport->Viewport->GetWindowMode())));
	// Reserve outside measurement; fail instead of growing unbounded during a run.
	const double ExpectedSeconds = Warmup + (Laps + 1) * (Length / Speed + 2.0);
	const double Capacity = FMath::CeilToDouble(ExpectedSeconds * 1000.0 + 10000.0);
	if (Capacity > 10000000) { Finish(TEXT("Route duration exceeds in-memory capture limit")); return false; }
	Frames.Reserve(static_cast<int32>(Capacity));
	Phase = EPhase::Warmup;
	LastTime = FPlatformTime::Seconds();
	MovePawn();
	if (Controller->PlayerCameraManager) Controller->PlayerCameraManager->SetGameCameraCutThisFrame();
	if (!WriteMeta()) { Finish(TEXT("Cannot write metadata")); return false; }
	return true;
}

int32 USelenePerfRouteSubsystem::SegmentAt(float AtDistance) const
{
	for (int32 I = 0; I < PerfRoute->Segments.Num(); ++I)
	{
		const FSelenePerfSegment& S = PerfRoute->Segments[I];
		if (AtDistance >= S.StartDistance && (AtDistance < S.EndDistance ||
			(AtDistance == PerfRoute->Route->GetSplineLength() && AtDistance <= S.EndDistance))) return I;
	}
	return INDEX_NONE;
}

void USelenePerfRouteSubsystem::MovePawn()
{
	const FRotator Rotation = PerfRoute->Route->GetDirectionAtDistanceAlongSpline(Distance, ESplineCoordinateSpace::World).Rotation();
	Pawn->SetActorLocationAndRotation(PerfRoute->Route->GetLocationAtDistanceAlongSpline(Distance, ESplineCoordinateSpace::World),
		Rotation, false, nullptr, ETeleportType::TeleportPhysics);
	Controller->SetControlRotation(Rotation);
}

void USelenePerfRouteSubsystem::Event(const FString& Text)
{
#if CSV_PROFILER && !UE_BUILD_SHIPPING
	if (bCSVStarted) CSV_EVENT(SelenePerf, TEXT("%s"), *Text);
#endif
}

void USelenePerfRouteSubsystem::RestartLap()
{
	Distance = 0;
	PhaseElapsed = 0;
	LastSegment = INDEX_NONE;
	Phase = EPhase::Settle;
	MovePawn();
	if (Controller->PlayerCameraManager) Controller->PlayerCameraManager->SetGameCameraCutThisFrame();
	Event(FString::Printf(TEXT("SETTLE lap=%d"), Lap));
}

void USelenePerfRouteSubsystem::OnFrame()
{
	const double Now = FPlatformTime::Seconds();
	if (Phase == EPhase::Done) return;
	if (Phase == EPhase::Finishing)
	{
		// Never block the game thread: EndCapture needs subsequent engine frames to drain.
		if (CaptureFinished.IsValid() && !CaptureFinished.IsReady()) return;
		if (CaptureFinished.IsValid())
		{
			const FString Path = CaptureFinished.Get();
			Meta->SetStringField(TEXT("profiler_file"), Path);
			if (Path.IsEmpty() || IFileManager::Get().FileSize(*Path) <= 0)
				ErrorText += TEXT(" CSV profiler failed to write capture.");
		}
		Exit(); return;
	}
	if (Phase == EPhase::Waiting)
	{
		if (Now - CreatedAt > 60) { Finish(TEXT("Timed out waiting for begin play, streaming, possessed pawn and viewport")); return; }
		UWorld* World = GetWorld();
		if (!World->HasBegunPlay() || World->GetNumStreamingLevelsBeingLoaded() != 0) return;
		Controller = World->GetFirstPlayerController();
		Pawn = Controller ? Controller->GetPawn() : nullptr;
		if (!Pawn || !GEngine || !GEngine->GameViewport || !GEngine->GameViewport->Viewport ||
			GEngine->GameViewport->Viewport->GetSizeXY().GetMin() <= 0) return;
		Start(); return;
	}
	if (!IsValid(Pawn) || !IsValid(Controller) || !IsValid(PerfRoute) || Controller->GetPawn() != Pawn)
	{ Finish(TEXT("Route, pawn or possession lost during capture")); return; }
	const double Delta = Now - LastTime;
	LastTime = Now;
	if (Frames.Num() == Frames.Max()) { Finish(TEXT("Frame buffer full")); return; }
	const int32 Segment = SegmentAt(Distance);
	const bool bDiscarded = Phase != EPhase::Lap;
	Frames.Add({GFrameCounter - 1, Lap, Segment, Delta * 1000.0,
		GGameThreadTime, GRenderThreadTime, RHIGetGPUFrameCycles(), bDiscarded});
	if (!bDiscarded && Segment != INDEX_NONE)
		++SegmentCounts[Lap * PerfRoute->Segments.Num() + Segment];
	PhaseElapsed += Delta;
	if (Phase == EPhase::Warmup)
	{
		if (PhaseElapsed >= Warmup)
		{
			Lap = 0;
#if CSV_PROFILER && !UE_BUILD_SHIPPING
			FCsvProfiler::Get()->BeginCapture(-1, OutDir, FPaths::GetCleanFilename(Stem) + TEXT(".profile.csv"));
			bCSVStarted = true;
#endif
			RestartLap();
		}
		else
		{
			Distance = FMath::Fmod(Distance + Speed * Delta, PerfRoute->Route->GetSplineLength());
			MovePawn();
		}
		return;
	}
	if (Phase == EPhase::Settle)
	{
#if CSV_PROFILER && !UE_BUILD_SHIPPING
		if (!FCsvProfiler::IsCapturing())
		{
			if (PhaseElapsed > 60) Finish(TEXT("CSV profiler did not start"));
			return;
		}
#endif
		if (PhaseElapsed >= 2.0)
		{
			Phase = EPhase::Lap;
			PhaseElapsed = 0;
			Event(FString::Printf(TEXT("BEGIN lap=%d %s"), Lap, Lap == 0 ? TEXT("COLD") : TEXT("WARM")));
			LastSegment = SegmentAt(Distance);
			Event(TEXT("BEGIN segment=") + (LastSegment < 0 ? TEXT("unsegmented") : PerfRoute->Segments[LastSegment].Tag.ToString()));
		}
		return;
	}
	if (Distance >= PerfRoute->Route->GetSplineLength())
	{
		Event(TEXT("END segment=") + (LastSegment < 0 ? TEXT("unsegmented") : PerfRoute->Segments[LastSegment].Tag.ToString()));
		Event(FString::Printf(TEXT("END lap=%d"), Lap));
		if (Lap == Laps) Finish();
		else { ++Lap; RestartLap(); }
		return;
	}
	Distance = FMath::Min(Distance + Speed * Delta, static_cast<double>(PerfRoute->Route->GetSplineLength()));
	const int32 NextSegment = SegmentAt(Distance);
	if (NextSegment != LastSegment)
	{
		Event(TEXT("END segment=") + (LastSegment < 0 ? TEXT("unsegmented") : PerfRoute->Segments[LastSegment].Tag.ToString()));
		Event(TEXT("BEGIN segment=") + (NextSegment < 0 ? TEXT("unsegmented") : PerfRoute->Segments[NextSegment].Tag.ToString()));
		LastSegment = NextSegment;
	}
	MovePawn();
}

void USelenePerfRouteSubsystem::Finish(const FString& Error)
{
	if (Phase == EPhase::Finishing || Phase == EPhase::Done) return;
	ErrorText = Error;
	int32 MeasuredFrames = 0;
	for (const FFrame& Frame : Frames) if (!Frame.bDiscarded) ++MeasuredFrames;
	if (MeasuredFrames == 0) ErrorText += TEXT(" Frame log contains no measured frames.");
	if (PerfRoute)
	{
		for (int32 I = 0; I < SegmentCounts.Num(); ++I)
			if (SegmentCounts[I] == 0) ErrorText += FString::Printf(TEXT(" Zero frames: lap=%d segment=%s."),
				I / PerfRoute->Segments.Num(), *PerfRoute->Segments[I % PerfRoute->Segments.Num()].Tag.ToString());
	}
	TSharedPtr<FJsonObject> TimerSamples = MakeShared<FJsonObject>();
	int32 GameSamples = 0, RenderSamples = 0, GPUSamples = 0;
	for (const FFrame& Frame : Frames)
	{
		if (!Frame.bDiscarded)
		{
			GameSamples += Frame.GameCycles != 0;
			RenderSamples += Frame.RenderCycles != 0;
			GPUSamples += Frame.GPUCycles != 0;
		}
	}
	TimerSamples->SetNumberField(TEXT("game_thread_ms"), GameSamples);
	TimerSamples->SetNumberField(TEXT("render_thread_ms"), RenderSamples);
	TimerSamples->SetNumberField(TEXT("gpu_ms"), GPUSamples);
	Meta->SetObjectField(TEXT("valid_timer_samples"), TimerSamples);
	Meta->SetNumberField(TEXT("measured_frames"), MeasuredFrames);
	Meta->SetNumberField(TEXT("total_frames"), Frames.Num());
	TUniquePtr<FArchive> File(IFileManager::Get().CreateFileWriter(*(Stem + TEXT(".frames.csv"))));
	if (File)
	{
		auto Write = [&File](const FString& Line)
		{
			FTCHARToUTF8 UTF8(*Line);
			File->Serialize(const_cast<ANSICHAR*>(UTF8.Get()), UTF8.Length());
		};
		Write(TEXT("frame_index,lap,segment_tag,delta_ms,game_thread_ms,render_thread_ms,gpu_ms,is_discarded\n"));
		for (const FFrame& Frame : Frames)
		{
			const FString Tag = Frame.Segment < 0 ? TEXT("unsegmented") : PerfRoute->Segments[Frame.Segment].Tag.ToString();
			Write(FString::Printf(TEXT("%llu,%d,%s,%.6f,%s,%s,%s,%d\n"), Frame.Index, Frame.Lap, *SelenePerf::Quote(Tag),
				Frame.DeltaMs, *SelenePerf::Timer(Frame.GameCycles), *SelenePerf::Timer(Frame.RenderCycles),
				*SelenePerf::Timer(Frame.GPUCycles), Frame.bDiscarded ? 1 : 0));
		}
		if (!File->Close() || File->IsError()) ErrorText += TEXT(" Frame log write failed.");
	}
	else ErrorText += TEXT(" Cannot open frame log.");
#if CSV_PROFILER && !UE_BUILD_SHIPPING
	if (bCSVStarted) CaptureFinished = FCsvProfiler::Get()->EndCapture();
#endif
	Phase = EPhase::Finishing;
	Meta->SetStringField(TEXT("status"), TEXT("finishing"));
	WriteMeta();
}

bool USelenePerfRouteSubsystem::WriteMeta()
{
	TArray<TSharedPtr<FJsonValue>> Values;
	for (const FString& Warning : Warnings) Values.Add(MakeShared<FJsonValueString>(Warning));
	Meta->SetArrayField(TEXT("warnings"), Values);
	if (!ErrorText.IsEmpty()) Meta->SetStringField(TEXT("error"), ErrorText);
	FString JSON;
	const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JSON);
	return FJsonSerializer::Serialize(Meta.ToSharedRef(), Writer) &&
		FFileHelper::SaveStringToFile(JSON, *(Stem + TEXT(".meta.json")), FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
}

void USelenePerfRouteSubsystem::Exit()
{
	Meta->SetStringField(TEXT("status"), ErrorText.IsEmpty() ? TEXT("complete") : TEXT("error"));
	if (!WriteMeta()) ErrorText += TEXT(" Metadata write failed.");
	if (!ErrorText.IsEmpty())
	{
		UE_LOG(LogSelene, Error, TEXT("SelenePerf: %s"), *ErrorText);
		FPlatformMisc::LowLevelOutputDebugStringf(TEXT("SelenePerf ERROR: %s\n"), *ErrorText);
	}
	Phase = EPhase::Done;
	SelenePerf::RequestExit(ErrorText.IsEmpty() ? 0 : 2);
}
