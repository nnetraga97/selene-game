#pragma once

#include "CoreMinimal.h"
#include "Async/Future.h"
#include "Subsystems/WorldSubsystem.h"
#include "SelenePerfRouteSubsystem.generated.h"

class ASelenePerfRoute;
class APawn;
class APlayerController;
class FJsonObject;
class FJsonValue;

// One map per process. A world subsystem cannot accidentally retain a route from an old map.
UCLASS()
class SELENE_API USelenePerfRouteSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()
public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

private:
	enum class EPhase : uint8 { Waiting, Warmup, Settle, Lap, ShotHold, ShotWait, Drive, Finishing, Done };
	struct FFrame
	{
		uint64 Index;
		int32 Lap;
		int32 Segment;
		double DeltaMs;
		uint32 GameCycles, RenderCycles, GPUCycles;
		bool bDiscarded;
	};
	void OnFrame();
	bool Start();
	void MovePawn();
	void RestartLap();
	void BeginShot();
	void TickShots(double Now);
	void TickDrive();
	void Event(const FString& Text);
	void Exec(const FString& Command);
	void Finish(const FString& Error = FString());
	void Exit();
	bool WriteMeta();
	int32 SegmentAt(float AtDistance) const;

	UPROPERTY() TObjectPtr<ASelenePerfRoute> PerfRoute;
	UPROPERTY() TObjectPtr<APawn> Pawn;
	UPROPERTY() TObjectPtr<APlayerController> Controller;
	FDelegateHandle FrameHandle;
	EPhase Phase = EPhase::Waiting;
	FString RouteName, Camera = TEXT("3P"), OutDir, Stem, ErrorText;
	float Hour = 12, TimeFlow = 0, Speed = 150, Warmup = 15, Distance = 0;
	int32 Laps = 3, Lap = -1, LastSegment = INDEX_NONE;
	bool bTimeFlow = false, bCSVStarted = false, bDrive = false;
	int32 Shots = 0, ShotIndex = 0;
	FString ShotFilename;
	TArray<TSharedPtr<FJsonValue>> ShotManifest;
	double ShotStartedAt = 0, DriveStartedAt = 0, PathLength = 0;
	TArray<FVector2D> ProgressHistory;
	FVector PreviousLocation = FVector::ZeroVector;
	double CreatedAt = 0, LastTime = 0, PhaseElapsed = 0;
	TArray<FFrame> Frames;
	TArray<int32> SegmentCounts;
	TArray<FString> Warnings;
	TSharedPtr<FJsonObject> Meta;
	TSharedFuture<FString> CaptureFinished;
};
