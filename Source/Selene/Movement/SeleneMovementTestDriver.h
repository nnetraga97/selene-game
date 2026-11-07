#pragma once

#include "CoreMinimal.h"

class USeleneMovementComponent;
class ASeleneCharacter;

/** Opt-in capture driver. Fixture impulses are explicitly labeled, never counted as abilities. */
class FSeleneMovementTestDriver
{
public:
	explicit FSeleneMovementTestDriver(USeleneMovementComponent& InMovement);
	static bool IsRequested();
	static void FinishRegressionWhenCaptured(ASeleneCharacter* Character);
	void BeforeMovement(float DeltaTime);
	void AfterMovement();
private:
	void Capture(const FString& Phase);
	void DriveDash();
	void DriveSlide();
	void DriveExtraJump();
	void DriveWallJump();
	void DriveMantle();
	void DriveRoster();
	void ResetAt(const FVector& Position);
	int32 Action = 0;
	float JumpReleaseAt = -1.f;
	float FirstJumpPhaseTime = 1.f;
	USeleneMovementComponent& Movement;
	ASeleneCharacter* Character = nullptr;
	FString Directory, Stage;
	float Time = -6.f;
	float PhaseTime = 0.f;
	int32 View = -1;
	int32 Shot = 0;
	bool bFixtureImpulse = false;
	bool bChainJump = false;
	bool bFinished = false;
	bool bInitialized = false;
};
