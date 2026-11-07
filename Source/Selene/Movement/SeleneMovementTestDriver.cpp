#include "Movement/SeleneMovementTestDriver.h"
#include "Movement/SeleneMovementComponent.h"
#include "SeleneCharacter.h"
#include "Selene.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Controller.h"
#include "GameFramework/SpringArmComponent.h"
#include "HAL/IConsoleManager.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMisc.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "UnrealClient.h"

namespace
{
	TAutoConsoleVariable<int32> CVarRegressionExit(TEXT("selene.MoveTestExitAfterAnimMatch"), 0, TEXT("Graceful exit after all21 regression screenshots are written."));
	TAutoConsoleVariable<int32> CVarMoveTest(TEXT("selene.MoveTest"), 0, TEXT("Opt-in, bounded MovementTest capture sequence."));
	TAutoConsoleVariable<FString> CVarMoveTestLabel(TEXT("selene.MoveTestLabel"), TEXT("manual"), TEXT("Fresh Saved/MovementTest evidence folder."));
	TAutoConsoleVariable<FString> CVarMoveTestStage(TEXT("selene.MoveTestStage"), TEXT("momentum"), TEXT("Verified stage to capture; session 1 begins with momentum."));
}

bool FSeleneMovementTestDriver::IsRequested() { return CVarMoveTest.GetValueOnGameThread() > 0; }

FSeleneMovementTestDriver::FSeleneMovementTestDriver(USeleneMovementComponent& InMovement) : Movement(InMovement)
{
	Character = Cast<ASeleneCharacter>(Movement.GetOwner());
	FString Label = CVarMoveTestLabel.GetValueOnGameThread();
	for (TCHAR& C : Label) if (!FChar::IsAlnum(C) && C != '-' && C != '_') C = '_';
	Directory = FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir() / TEXT("MovementTest") / Label);
	Stage = CVarMoveTestStage.GetValueOnGameThread();
}

void FSeleneMovementTestDriver::BeforeMovement(float DeltaTime)
{
	if (!Character || bFinished || !IsRequested()) return;
	Time += DeltaTime;
	if (JumpReleaseAt >= 0.f && Time >= JumpReleaseAt) { Character->StopJumping(); JumpReleaseAt = -1.f; }
	if (Time < 0.f) return;
	if (!bInitialized)
	{
		if (!Character->GetWorld()->GetMapName().Contains(TEXT("MovementTest")) || (Stage != TEXT("momentum") && Stage != TEXT("dash") && Stage != TEXT("slide") && Stage != TEXT("extra") && Stage != TEXT("wall") && Stage != TEXT("mantle") && Stage != TEXT("roster")) ||
			IFileManager::Get().FileExists(*(Directory / TEXT("trace.csv"))))
		{
			UE_LOG(LogSelene, Error, TEXT("MoveTest refuses wrong map, unsupported stage, or existing trace"));
			bFinished = true;
			return;
		}
		IFileManager::Get().MakeDirectory(*Directory, true);
		FFileHelper::SaveStringToFile(TEXT("time,view,stage,state,speed,x,y,z,vx,vy,vz,stamina,carry,hero,fov_kick,capsule_half_height\n"), *(Directory / TEXT("trace.csv")));
		bInitialized = true;
	}
	const float ViewSeconds = Stage == TEXT("roster") ? 24.f : Stage == TEXT("mantle") ? 16.f : Stage == TEXT("wall") ? 10.f : Stage == TEXT("extra") ? 16.f : (Stage != TEXT("momentum") ? 20.f : 12.f);
	if (Time >= ViewSeconds * (Stage == TEXT("roster") ? 1.f : 2.f))
	{
		FFileHelper::SaveStringToFile(TEXT("Capture sequence completed; review screenshots and trace for acceptance.\n"), *(Directory / TEXT("complete.txt")));
		bFinished = true;
		FPlatformMisc::RequestExit(false);
		return;
	}
	const int32 NextView = Time < ViewSeconds ? 0 : 1;
	PhaseTime = FMath::Fmod(Time, ViewSeconds);
	if (View != NextView)
	{
		View = NextView;
		Action = 0; FirstJumpPhaseTime = 1.f; Shot = 0; bFixtureImpulse = false; bChainJump = false;
		Movement.StopMovementImmediately();
		Character->SetActorLocationAndRotation(FVector(0, 0, 90), FRotator::ZeroRotator, false, nullptr, ETeleportType::TeleportPhysics);
		Movement.SetMovementMode(MOVE_Walking);
		Character->SetCameraMode(View == 0 ? ESeleneCameraMode::ThirdPerson : ESeleneCameraMode::FirstPerson);
		if (USpringArmComponent* Boom = Character->FindComponentByClass<USpringArmComponent>())
		{
			Boom->bEnableCameraLag = false;
			Boom->TargetArmLength = 420.f;
		}
	}
	Character->GetController()->SetControlRotation(FRotator(View == 0 ? -12.f : -6.f, 0.f, 0.f));
	Character->SetMovementPace(ESelenePace::Sprint);
	if (Stage == TEXT("dash")) { DriveDash(); return; }
	if (Stage == TEXT("slide")) { DriveSlide(); return; }
	if (Stage == TEXT("extra")) { DriveExtraJump(); return; }
	if (Stage == TEXT("wall")) { DriveWallJump(); return; }
	if (Stage == TEXT("mantle")) { DriveMantle(); return; }
	if (Stage == TEXT("roster")) { DriveRoster(); return; }
	if (PhaseTime >= 0.5f && PhaseTime < 9.f)
		Character->AddMovementInput(PhaseTime >= 2.25f && PhaseTime < 2.6f ? FVector::RightVector : FVector::ForwardVector);
	if (PhaseTime >= 2.f && !bFixtureImpulse)
	{
		// Test fixture: emulate an incoming 960 cm/s move until dash is implemented and verified.
		Movement.AddImpulse(FVector(360.f, 0.f, 0.f), true);
		Character->Jump();
		bFixtureImpulse = true;
	}
	if (PhaseTime >= 2.1f) Character->StopJumping();
	if (PhaseTime >= 3.f && PhaseTime < 3.5f && Movement.IsMovingOnGround() && !bChainJump)
	{
		Character->Jump();
		bChainJump = true;
	}
}

void FSeleneMovementTestDriver::AfterMovement()
{
	if (!bInitialized || bFinished || !IsRequested()) return;
	const FVector P = Character->GetActorLocation(), V = Movement.Velocity;
	if (GEngine) GEngine->AddOnScreenDebugMessage(81580, 0.2f, FColor::White,
		FString::Printf(TEXT("Movement test: %s | %s | %.0f cm/s | t %.2f"), *Stage, *Movement.GetMoveState(), V.Size2D(), PhaseTime));
	const FString Line = FString::Printf(TEXT("%.4f,%s,%s,%s,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%s,%.3f,%.3f\n"),
		Time, View == 0 ? TEXT("3p") : TEXT("1p"), *Stage, *Movement.GetMoveState(), V.Size2D(),
		P.X, P.Y, P.Z, V.X, V.Y, V.Z, Movement.GetStamina(), Movement.GetLandingCarryRemaining(), *Character->GetActiveCharacterName().ToString(), Movement.GetFOVKick(), Character->GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
	FFileHelper::SaveStringToFile(Line, *(Directory / TEXT("trace.csv")), FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM, &IFileManager::Get(), FILEWRITE_Append);
	if (Stage == TEXT("dash"))
	{
		static const float DashTimes[] = {0.9f, 1.08f, 1.58f, 2.08f, 2.58f, 5.8f, 7.08f, 7.5f, 8.3f, 10.28f, 18.8f};
		static const TCHAR* DashNames[] = {TEXT("sprint"), TEXT("ground-dash"), TEXT("second-charge"), TEXT("air-dash"), TEXT("empty-rejected"), TEXT("regeneration"), TEXT("dash-jump"), TEXT("gap-air"), TEXT("gap-landed"), TEXT("no-input-dash"), TEXT("fully-regenerated")};
		if (Shot < UE_ARRAY_COUNT(DashTimes) && PhaseTime >= DashTimes[Shot]) Capture(DashNames[Shot++]);
		return;
	}
	if (Stage == TEXT("slide"))
	{
		static const float SlideTimes[] = {1.4f, 1.75f, 2.5f, 3.1f, 4.3f, 6.4f, 7.5f, 9.5f, 11.4f, 12.3f, 16.2f};
		static const TCHAR* Names[] = {TEXT("ramp-sprint"), TEXT("downhill-slide"), TEXT("downhill-speed"), TEXT("slide-jump"), TEXT("landed"), TEXT("flat-slide"), TEXT("flat-deceleration"), TEXT("flat-exit"), TEXT("uphill-slide"), TEXT("uphill-exit"), TEXT("slow-rejected")};
		if (Shot < UE_ARRAY_COUNT(SlideTimes) && PhaseTime >= SlideTimes[Shot]) Capture(Names[Shot++]);
		return;
	}
	if (Stage == TEXT("extra"))
	{
		const float Times[] = {0.2f, FirstJumpPhaseTime + 0.15f, FirstJumpPhaseTime + 0.53f, FirstJumpPhaseTime + 0.75f, FirstJumpPhaseTime + 1.1f, FirstJumpPhaseTime + 1.6f, 6.2f, 9.2f};
		static const TCHAR* Names[] = {TEXT("approach"), TEXT("first-jump"), TEXT("extra-jump"), TEXT("repeat-rejected"), TEXT("platform-apex"), TEXT("platform-landed"), TEXT("empty-rejected"), TEXT("redirect")};
		if (Shot < UE_ARRAY_COUNT(Times) && PhaseTime >= Times[Shot]) Capture(Names[Shot++]);
		return;
	}
	if (Stage == TEXT("wall"))
	{
		static const float Times[] = {0.2f, 1.05f, 1.32f, 1.9f, 3.95f, 5.95f, 7.5f};
		static const TCHAR* Names[] = {TEXT("wall-approach"), TEXT("contact-jump"), TEXT("wall-kick"), TEXT("same-wall-rejected"), TEXT("reset-after-landing"), TEXT("no-wall-rejected"), TEXT("landed")};
		if (Shot < UE_ARRAY_COUNT(Times) && PhaseTime >= Times[Shot]) Capture(Names[Shot++]);
		return;
	}
	if (Stage == TEXT("mantle"))
	{
		static const float Times[] = {0.2f, 1.3f, 2.2f, 4.3f, 5.2f, 7.3f, 8.2f, 10.3f, 11.2f, 14.f};
		static const TCHAR* Names[] = {TEXT("approach"), TEXT("100-climb"), TEXT("100-top"), TEXT("140-climb"), TEXT("140-top"), TEXT("180-climb"), TEXT("180-top"), TEXT("220-climb"), TEXT("220-top"), TEXT("too-high-rejected")};
		if (Shot < UE_ARRAY_COUNT(Times) && PhaseTime >= Times[Shot]) Capture(Names[Shot++]);
		return;
	}
	if (Stage == TEXT("roster"))
	{
		const float CaptureTime = (Shot / 2) * 4.f + (Shot % 2 == 0 ? 2.5f : 3.3f);
		if (Shot < 12 && PhaseTime >= CaptureTime) { ++Shot; Capture(Character->GetActiveCharacterName().ToString() + TEXT("-cycle-walk")); }
		return;
	}
	static const float Times[] = {1.5f, 2.05f, 2.5f, 3.05f, 3.5f, 4.15f, 5.2f, 8.5f, 9.5f};
	static const TCHAR* Names[] = {TEXT("sprint"), TEXT("fixture-impulse-jump"), TEXT("air-steer"), TEXT("chain-jump"), TEXT("chain-air"), TEXT("landing-carry"), TEXT("decay"), TEXT("sprint-restored"), TEXT("stop")};
	if (Shot < UE_ARRAY_COUNT(Times) && PhaseTime >= Times[Shot]) Capture(Names[Shot++]);
}

void FSeleneMovementTestDriver::Capture(const FString& Phase)
{
	const FString Name = FString::Printf(TEXT("%s_%02d_%s.png"), View == 0 ? TEXT("3p") : TEXT("1p"), Shot, *Phase);
	FScreenshotRequest::RequestScreenshot(Directory / Name, true, false);
	UE_LOG(LogSelene, Log, TEXT("MoveTest capture=%s t=%.3f state=%s speed=%.2f position=%s hero=%s chains=%d"),
		*Name, Time, *Movement.GetMoveState(), Movement.Velocity.Size2D(), *Character->GetActorLocation().ToString(),
		*Character->GetActiveCharacterName().ToString(), Character->GetActiveCharacterEntry().SecondaryChains.Num());
}

void FSeleneMovementTestDriver::ResetAt(const FVector& Position)
{
	Movement.StopMovementImmediately();
	Character->StopJumping();
	Character->SetActorLocationAndRotation(Position, FRotator::ZeroRotator, false, nullptr, ETeleportType::TeleportPhysics);
	Movement.SetMovementMode(MOVE_Walking);
	UE_LOG(LogSelene, Log, TEXT("MoveTest fixture reset t=%.3f position=%s"), Time, *Position.ToString());
}

void FSeleneMovementTestDriver::DriveDash()
{
	if ((PhaseTime >= 0.5f && PhaseTime < 3.f) || (PhaseTime >= 6.3f && PhaseTime < 8.5f)) Character->AddMovementInput(FVector::ForwardVector);
	static const float Times[] = {1.f, 1.5f, 1.9f, 2.f, 2.5f, 6.f, 7.f, 7.1f, 10.f, 10.2f};
	if (Action < UE_ARRAY_COUNT(Times) && PhaseTime >= Times[Action])
	{
		switch (Action)
		{
		case 2: Character->Jump(); break;
		case 5: ResetAt(FVector(600, 3000, 90)); break;
		case 7: Movement.TryAdvancedJump(); break;
		case 8: ResetAt(FVector(0, 0, 90)); break;
		default:
			{ const bool bStarted = Movement.TryDash();
			UE_LOG(LogSelene, Log, TEXT("MoveTest dash request action=%d t=%.3f accepted=%d stamina=%.3f"), Action, Time, bStarted, Movement.GetStamina()); }
		}
		++Action;
	}
	if (PhaseTime > 2.05f) Character->StopJumping();
}

void FSeleneMovementTestDriver::DriveSlide()
{
	if (Action == 0) { ResetAt(FVector(-200, 1600, 450)); ++Action; }
	if ((PhaseTime >= 0.5f && PhaseTime < 4.8f) || (PhaseTime >= 5.2f && PhaseTime < 6.2f)) Character->AddMovementInput(FVector::ForwardVector);
	if (PhaseTime >= 10.2f && PhaseTime < 11.2f) Character->AddMovementInput(-FVector::ForwardVector);
	if (PhaseTime >= 10.f && PhaseTime < 14.f) Character->GetController()->SetControlRotation(FRotator(-12, 180, 0));
	static const float Times[] = {0.f, 1.5f, 2.9f, 5.f, 6.2f, 10.f, 11.2f, 15.f, 16.f};
	if (Action < UE_ARRAY_COUNT(Times) && PhaseTime >= Times[Action])
	{
		switch (Action)
		{
		case 2: Movement.TryAdvancedJump(); break;
		case 3: Movement.StopSlide(); ResetAt(FVector(0, 0, 90)); break;
		case 5: Movement.StopSlide(); ResetAt(FVector(1200, 1600, 190)); break;
		case 7: Movement.StopSlide(); ResetAt(FVector(0, 0, 90)); break;
		default: { const bool bStarted = Movement.TrySlide(); UE_LOG(LogSelene, Log, TEXT("MoveTest slide request action=%d t=%.3f accepted=%d speed=%.2f"), Action, Time, bStarted, Movement.Velocity.Size2D()); }
		}
		++Action;
	}
}

void FSeleneMovementTestDriver::DriveExtraJump()
{
	if (Action == 0) { ResetAt(FVector(0, 4400, 90)); ++Action; }
	if (PhaseTime >= 0.5f && PhaseTime < 2.8f) Character->AddMovementInput(FVector::ForwardVector);
	if (PhaseTime >= 8.1f && PhaseTime < 8.7f) Character->AddMovementInput(FVector::ForwardVector);
	if (PhaseTime >= 8.7f && PhaseTime < 9.f) Character->AddMovementInput(FVector::RightVector);
	const float Times[] = {0.f, 1.f, FirstJumpPhaseTime + 0.45f, FirstJumpPhaseTime + 0.6f, 4.f, 4.2f, 4.5f, 4.8f, 5.5f, 6.f, 8.f, 8.3f, 8.8f};
	if (Action < UE_ARRAY_COUNT(Times) && PhaseTime >= Times[Action])
	{
		switch (Action)
		{
		case 1: case 8: case 11: Character->Jump(); JumpReleaseAt = Time + 0.08f; if (Action == 1) FirstJumpPhaseTime = PhaseTime; break;
		case 4: ResetAt(FVector(0, 0, 90)); break;
		case 10: ResetAt(FVector(0, -350, 90)); break;
		case 5: case 6: case 7: Movement.TryDash(); break;
		default: { const bool bStarted = Movement.TryAdvancedJump(); UE_LOG(LogSelene, Log, TEXT("MoveTest extra request action=%d t=%.3f accepted=%d stamina=%.3f"), Action, Time, bStarted, Movement.GetStamina()); }
		}
		++Action;
	}
}

void FSeleneMovementTestDriver::DriveWallJump()
{
	if (Action == 0) { ResetAt(FVector(550, 5800, 90)); ++Action; }
	if ((PhaseTime >= 0.5f && PhaseTime < 1.2f) || (PhaseTime >= 3.1f && PhaseTime < 3.8f)) Character->AddMovementInput(FVector::ForwardVector);
	static const float Times[] = {0.f, 0.9f, 1.2f, 1.8f, 3.f, 3.5f, 3.8f, 5.f, 5.5f, 5.8f};
	if (Action < UE_ARRAY_COUNT(Times) && PhaseTime >= Times[Action])
	{
		switch (Action)
		{
		case 1: case 5: case 8: Character->Jump(); JumpReleaseAt = Time + 0.08f; break;
		case 4: ResetAt(FVector(700, 5800, 90)); break;
		case 7: ResetAt(FVector(0, 0, 90)); break;
		case 3:
			Character->SetActorLocation(FVector(720, 5800, 240), false, nullptr, ETeleportType::TeleportPhysics);
			Movement.Velocity = FVector::ZeroVector;
			UE_LOG(LogSelene, Log, TEXT("MoveTest fixture return to same wall while still airborne"));
			[[fallthrough]];
		default: { const bool bStarted = Movement.TryWallJump(); UE_LOG(LogSelene, Log, TEXT("MoveTest wall request action=%d t=%.3f accepted=%d"), Action, Time, bStarted); }
		}
		++Action;
	}
}

void FSeleneMovementTestDriver::DriveMantle()
{
	const int32 Fixture = FMath::Min(4, FMath::FloorToInt(PhaseTime / 3.f));
	if (Action <= Fixture)
	{
		ResetAt(Fixture < 4 ? FVector(0, 7300 + Fixture * 1000, 90) : FVector(550, 5800, 90));
		Action = Fixture + 1;
	}
	const float Local = FMath::Fmod(PhaseTime, 3.f);
	if (Local >= 0.5f && Local < 2.f) Character->AddMovementInput(FVector::ForwardVector);
}

void FSeleneMovementTestDriver::FinishRegressionWhenCaptured(ASeleneCharacter* Character)
{
	if (!Character || CVarRegressionExit.GetValueOnGameThread() == 0) return;
	auto* Label = IConsoleManager::Get().FindConsoleVariable(TEXT("selene.AnimMatchLabel"));
	if (!Label) return;
	const FString Folder = FPaths::ProjectSavedDir() / TEXT("AnimMatch/Captures") / Label->GetString() / Character->GetActiveCharacterName().ToString();
	TArray<FString> Files; IFileManager::Get().FindFiles(Files, *(Folder / TEXT("*.png")), true, false);
	if (Files.Num() == 21) { UE_LOG(LogSelene, Log, TEXT("Movement regression21 screenshots written; graceful exit")); FPlatformMisc::RequestExit(false); }
}

void FSeleneMovementTestDriver::DriveRoster()
{
	const int32 Index = FMath::FloorToInt(PhaseTime / 4.f);
	if (Action <= Index)
	{
		ResetAt(FVector(0, 0, 90));
		if (Index > 0) Character->CycleCharacter();
		Action = Index + 1;
	}
	if (FMath::Fmod(PhaseTime, 4.f) > 0.8f && FMath::Fmod(PhaseTime, 4.f) < 3.5f) Character->AddMovementInput(FVector::ForwardVector);
}
