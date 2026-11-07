#include "Movement/SeleneMovementComponent.h"
#include "Movement/SeleneMovementTestDriver.h"
#include "GameFramework/Character.h"
#include "HAL/IConsoleManager.h"
#include "Camera/CameraComponent.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/Controller.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"
#include "Styling/CoreStyle.h"
#include "SeleneCharacter.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Engine/SkeletalMesh.h"

namespace
{
	TAutoConsoleVariable<int32> CVarAdvancedMovement(TEXT("selene.AdvancedMovement"), 1,
		TEXT("1: Selene hero momentum. 0: original CMC movement and original controls."));
}

USeleneMovementComponent::USeleneMovementComponent() = default;
USeleneMovementComponent::~USeleneMovementComponent() = default;

bool USeleneMovementComponent::IsAdvancedMovementEnabled()
{
	return CVarAdvancedMovement.GetValueOnGameThread() != 0;
}

void USeleneMovementComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	if (FSeleneMovementTestDriver::IsRequested() && !TestDriver && CharacterOwner && CharacterOwner->IsLocallyControlled())
		TestDriver = MakeUnique<FSeleneMovementTestDriver>(*this);
	if (TestDriver) TestDriver->BeforeMovement(DeltaTime);
	if (!IsAdvancedMovementEnabled() && IsDashing()) FinishDash();
	if (!IsAdvancedMovementEnabled() && IsSliding()) StopSlide();
	if (!IsAdvancedMovementEnabled() && IsMantling()) SetMovementMode(MOVE_Falling);
	if (IsAdvancedMovementEnabled())
	{
		RegenDelayRemaining = FMath::Max(0.f, RegenDelayRemaining - DeltaTime);
		if (RegenDelayRemaining == 0.f) Stamina = FMath::Min(float(StaminaCharges), Stamina + DeltaTime / FMath::Max(0.1f, ChargeRegenSeconds));
	}
	LandingCarryRemaining = IsAdvancedMovementEnabled() ? FMath::Max(0.f, LandingCarryRemaining - DeltaTime) : 0.f;
	LoadSlideClips();
	RemoveSlideMeshCompensation();
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	TickSlidePose(DeltaTime);
	TickFeedback(DeltaTime);
	if (TestDriver) TestDriver->AfterMovement();
	FSeleneMovementTestDriver::FinishRegressionWhenCaptured(Cast<ASeleneCharacter>(CharacterOwner));
}

float USeleneMovementComponent::GetMaxSpeed() const
{
	const float Base = Super::GetMaxSpeed();
	return IsAdvancedMovementEnabled() ? FMath::Max(Base, MomentumSpeedAllowance) : Base;
}

void USeleneMovementComponent::CalcVelocity(float DeltaTime, float Friction, bool bFluid, float BrakingDeceleration)
{
	if (!IsAdvancedMovementEnabled() || (!IsMovingOnGround() && !IsFalling()) || HasAnimRootMotion())
	{
		Super::CalcVelocity(DeltaTime, Friction, bFluid, BrakingDeceleration);
		return;
	}
	const float BaseSpeed = Super::GetMaxSpeed();
	const float Speed = Velocity.Size2D();
	if (Speed > BaseSpeed && LandingCarryRemaining <= 0.f)
	{
		// Bleed surplus gradually; never clip a dash/landing directly to the selected pace.
		const float NewSpeed = FMath::Max(BaseSpeed, Speed - ExcessSpeedDecay * DeltaTime);
		Velocity.X *= NewSpeed / Speed;
		Velocity.Y *= NewSpeed / Speed;
	}
	MomentumSpeedAllowance = FMath::Max(BaseSpeed, Velocity.Size2D());
	if (IsMovingOnGround())
	{
		Friction = LandingCarryRemaining > 0.f ? LandingFriction : MovingGroundFriction;
		BrakingDeceleration = LandingCarryRemaining > 0.f ? LandingBraking : GroundBraking;
	}
	Super::CalcVelocity(DeltaTime, Friction, bFluid, BrakingDeceleration);
	MomentumSpeedAllowance = 0.f;
}

FVector USeleneMovementComponent::GetAirControl(float DeltaTime, float TickAirControl, const FVector& FallAcceleration)
{
	if (!IsAdvancedMovementEnabled()) return Super::GetAirControl(DeltaTime, TickAirControl, FallAcceleration);
	// No low-speed boost to full ground acceleration in the advanced air model.
	return (FallAcceleration * AirSteering).GetClampedToMaxSize(AirAccelerationLimit);
}

void USeleneMovementComponent::ProcessLanded(const FHitResult& Hit, float RemainingTime, int32 Iterations)
{
	bExtraJumpUsed = false;
	bWallJumped = false;
	LastWall.Reset();
	if (IsAdvancedMovementEnabled()) LandingCarryRemaining = LandingCarrySeconds;
	Super::ProcessLanded(Hit, RemainingTime, Iterations);
}

bool USeleneMovementComponent::DoJump(bool bReplayingMoves, float DeltaTime)
{
	const bool bChain = IsAdvancedMovementEnabled() && IsMovingOnGround() && LandingCarryRemaining > 0.f;
	if (!Super::DoJump(bReplayingMoves, DeltaTime)) return false;
	if (bChain && Velocity.Size2D() >= MaxWalkSpeed)
		Velocity += Velocity.GetSafeNormal2D() * ChainJumpBonus;
	LandingCarryRemaining = 0.f;
	return true;
}

FString USeleneMovementComponent::GetMoveState() const
{
	if (IsDashing()) return TEXT("dash");
	if (IsSliding()) return TEXT("slide");
	if (IsMantling()) return TEXT("mantle");
	if (IsFalling()) return bWallJumped ? TEXT("wall-air") : (bExtraJumpUsed ? TEXT("extra-air") : TEXT("air"));
	return LandingCarryRemaining > 0.f ? TEXT("landing-carry") : TEXT("ground");
}

bool USeleneMovementComponent::TryDash()
{
	if (!IsAdvancedMovementEnabled() || !CharacterOwner || Stamina < 1.f || (!IsMovingOnGround() && !IsFalling())) return false;
	DashDirection = GetCurrentAcceleration().GetSafeNormal2D();
	if (DashDirection.IsNearlyZero()) DashDirection = CharacterOwner->GetLastMovementInputVector().GetSafeNormal2D();
	if (DashDirection.IsNearlyZero()) DashDirection = FRotationMatrix(FRotator(0.f, CharacterOwner->GetControlRotation().Yaw, 0.f)).GetUnitAxis(EAxis::X);
	Stamina -= 1.f;
	RegenDelayRemaining = StaminaRegenDelay;
	bDashFromGround = IsMovingOnGround();
	DashRemaining = DashSeconds;
	Velocity = DashDirection * FMath::Max(DashSpeed, Velocity.Size2D());
	SetMovementMode(MOVE_Custom, 1);
	return true;
}

void USeleneMovementComponent::FinishDash()
{
	DashRemaining = 0.f;
	FFindFloorResult Floor;
	FindFloor(UpdatedComponent->GetComponentLocation(), Floor, false);
	SetMovementMode(bDashFromGround && Floor.IsWalkableFloor() && Floor.FloorDist <= MAX_FLOOR_DIST ? MOVE_Walking : MOVE_Falling);
}

bool USeleneMovementComponent::TryAdvancedJump()
{
	if (TryWallJump()) return true;
	if (IsAdvancedMovementEnabled() && IsFalling() && !bExtraJumpUsed && Stamina >= 1.f)
	{
		const FVector Input = GetCurrentAcceleration().GetSafeNormal2D();
		const float Speed = Velocity.Size2D();
		if (!Input.IsNearlyZero()) Velocity = FMath::Lerp(Velocity.GetSafeNormal2D(), Input, ExtraJumpRedirect).GetSafeNormal2D() * Speed;
		Velocity.Z = ExtraJumpVelocity;
		bExtraJumpUsed = true;
		bWallJumped = false;
		Stamina -= 1.f;
		RegenDelayRemaining = StaminaRegenDelay;
		PlayJumpOverlay();
		return true;
	}
	if (IsAdvancedMovementEnabled() && IsSliding())
	{
		StopSlide();
		if (CharacterOwner->bIsCrouched) return true;
		SetMovementMode(MOVE_Falling);
		Velocity.Z = JumpZVelocity;
		return true;
	}
	if (!IsAdvancedMovementEnabled() || !IsDashing() || !bDashFromGround) return false;
	DashRemaining = 0.f;
	SetMovementMode(MOVE_Falling);
	Velocity.Z = JumpZVelocity;
	return true;
}

void USeleneMovementComponent::PhysCustom(float DeltaTime, int32 Iterations)
{
	if (IsSliding()) { PhysSlide(DeltaTime, Iterations); return; }
	if (IsMantling()) { PhysMantle(DeltaTime, Iterations); return; }
	if (!IsDashing()) { Super::PhysCustom(DeltaTime, Iterations); return; }
	const float Step = FMath::Min(DeltaTime, DashRemaining);
	if (!bDashFromGround) Velocity.Z += GetGravityZ() * Step;
	FHitResult Hit;
	SafeMoveUpdatedComponent(Velocity * Step, UpdatedComponent->GetComponentQuat(), true, Hit);
	DashRemaining -= Step;
	if (Hit.IsValidBlockingHit())
	{
		HandleImpact(Hit, Step, Velocity * Step);
		SlideAlongSurface(Velocity * Step, 1.f - Hit.Time, Hit.Normal, Hit, true);
		DashRemaining = 0.f;
	}
	if (DashRemaining <= KINDA_SMALL_NUMBER)
	{
		FinishDash();
		if (DeltaTime > Step) StartNewPhysics(DeltaTime - Step, Iterations + 1);
	}
}

void USeleneMovementComponent::TickFeedback(float DeltaTime)
{
	if (!CharacterOwner || !CharacterOwner->IsLocallyControlled()) return;
	const bool bEnabled = IsAdvancedMovementEnabled();
	CurrentFOVKick = bEnabled ? FMath::FInterpTo(CurrentFOVKick, IsDashing() ? DashFOVKick : 0.f, DeltaTime, FOVReturnSpeed) : 0.f;
	const float PreviousCameraDrop = CurrentCameraDrop;
	CurrentCameraDrop = bEnabled ? FMath::FInterpTo(CurrentCameraDrop, IsSliding() ? SlideCameraDrop : 0.f, DeltaTime, FOVReturnSpeed) : 0.f;
	TArray<UCameraComponent*> Cameras;
	CharacterOwner->GetComponents(Cameras);
	for (UCameraComponent* Camera : Cameras)
	{
		if (!OriginalFOV.Contains(Camera)) OriginalFOV.Add(Camera, Camera->FieldOfView);
		Camera->SetFieldOfView(OriginalFOV[Camera] + CurrentFOVKick);
		Camera->AddRelativeLocation(FVector(0, 0, PreviousCameraDrop - CurrentCameraDrop));
	}
	UGameViewportClient* Viewport = GetWorld()->GetGameViewport();
	if (!Viewport) return;
	if (bEnabled && !StaminaWidget)
	{
		StaminaWidget = SNew(SVerticalBox)
		+ SVerticalBox::Slot().VAlign(VAlign_Bottom).HAlign(HAlign_Center).Padding(16.f)
		[
			SNew(SBorder).Padding(FMargin(18.f, 8.f)).BorderBackgroundColor(FLinearColor(0.06f, 0.18f, 0.23f, 0.9f))
			[
				SNew(STextBlock).Font(FCoreStyle::GetDefaultFontStyle("Bold", 16))
				.ColorAndOpacity(FLinearColor(0.95f, 0.90f, 0.82f))
				.Text_Lambda([this]() { return FText::FromString(FString::Printf(TEXT("STAMINA  %d / %d   |   %.0f%%"), FMath::FloorToInt(Stamina), StaminaCharges, FMath::Frac(Stamina) * 100.f)); })
			]
		];
		StaminaWidget->SetVisibility(EVisibility::HitTestInvisible);
		Viewport->AddViewportWidgetContent(StaminaWidget.ToSharedRef(), 5);
	}
	else if (!bEnabled && StaminaWidget)
	{
		Viewport->RemoveViewportWidgetContent(StaminaWidget.ToSharedRef());
		StaminaWidget.Reset();
	}
}

void USeleneMovementComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (StaminaWidget && GetWorld() && GetWorld()->GetGameViewport()) GetWorld()->GetGameViewport()->RemoveViewportWidgetContent(StaminaWidget.ToSharedRef());
	StaminaWidget.Reset();
	Super::EndPlay(EndPlayReason);
}

bool USeleneMovementComponent::CanCrouchInCurrentState() const
{
	return (IsAdvancedMovementEnabled() && IsSliding()) || Super::CanCrouchInCurrentState();
}

bool USeleneMovementComponent::TrySlide()
{
	// Slow crouch intentionally does nothing until a proper crouch clip exists.
	if (!IsAdvancedMovementEnabled() || !IsMovingOnGround() || Velocity.Size2D() < SlideMinSpeed || CharacterOwner->bIsCrouched) return false;
	RemoveSlideMeshCompensation();
	OriginalCrouchHalfHeight = GetCrouchedHalfHeight();
	bOriginalCanCrouch = NavAgentProps.bCanCrouch;
	SetCrouchedHalfHeight(SlideHalfHeight);
	NavAgentProps.bCanCrouch = true;
	bWantsToCrouch = true;
	Crouch(false);
	if (!CharacterOwner->bIsCrouched) { bWantsToCrouch = false; SetCrouchedHalfHeight(OriginalCrouchHalfHeight); NavAgentProps.bCanCrouch = bOriginalCanCrouch; return false; }
	SetMovementMode(MOVE_Custom, 2);
	LoadSlideClips();
	AppliedSlideMeshDrop = SlideClips.Num() == 4 ? 0.f : SlidePoseMeshDrop;
	CharacterOwner->GetMesh()->AddRelativeLocation(FVector(0, 0, -AppliedSlideMeshDrop));
	PlaySlidePose(true);
	return true;
}

void USeleneMovementComponent::StopSlide()
{
	if (!IsSliding()) return;
	RemoveSlideMeshCompensation();
	PlaySlidePose(false);
	CharacterOwner->GetMesh()->AddRelativeLocation(FVector(0, 0, AppliedSlideMeshDrop));
	AppliedSlideMeshDrop = 0.f;
	SetMovementMode(MOVE_Walking);
	bWantsToCrouch = false;
	UnCrouch(false);
	SetCrouchedHalfHeight(OriginalCrouchHalfHeight);
	NavAgentProps.bCanCrouch = bOriginalCanCrouch;
}

void USeleneMovementComponent::PhysSlide(float DeltaTime, int32 Iterations)
{
	float Remaining = DeltaTime;
	while (Remaining >= MIN_TICK_TIME && IsSliding() && Iterations < MaxSimulationIterations)
	{
		++Iterations;
		const float Step = GetSimulationTimeStep(Remaining, Iterations);
		Remaining -= Step;
		FFindFloorResult Floor;
		FindFloor(UpdatedComponent->GetComponentLocation(), Floor, false);
		if (!Floor.IsWalkableFloor() || Floor.FloorDist > MaxStepHeight)
		{
			StopSlide(); SetMovementMode(MOVE_Falling); StartNewPhysics(Remaining + Step, Iterations); return;
		}
		const FVector Normal = Floor.HitResult.ImpactNormal;
		Velocity = FVector::VectorPlaneProject(Velocity, Normal);
		Velocity += FVector::VectorPlaneProject(FVector(0, 0, GetGravityZ()), Normal) * Step;
		const float Speed = Velocity.Size();
		Velocity = Velocity.GetSafeNormal() * FMath::Max(0.f, Speed - (SlideBraking + SlideFriction * Speed) * Step);
		if (Velocity.Size2D() < SlideEndSpeed) { StopSlide(); StartNewPhysics(Remaining + Step, Iterations); return; }
		FHitResult Hit;
		SafeMoveUpdatedComponent(Velocity * Step, UpdatedComponent->GetComponentQuat(), true, Hit);
		if (Hit.IsValidBlockingHit()) SlideAlongSurface(Velocity * Step, 1.f - Hit.Time, Hit.Normal, Hit, true);
		FindFloor(UpdatedComponent->GetComponentLocation(), CurrentFloor, false);
		if (CurrentFloor.IsWalkableFloor() && CurrentFloor.FloorDist <= MaxStepHeight) AdjustFloorHeight();
	}
}

void USeleneMovementComponent::LoadSlideClips()
{
	const ASeleneCharacter* Character = Cast<ASeleneCharacter>(CharacterOwner);
	if (!Character || Character->GetActiveCharacterName() == SlideClipHero) return;
	SlideClipHero = Character->GetActiveCharacterName();
	SlideClips.Reset();
	const auto& Entry = Character->GetActiveCharacterEntry();
	CurrentSlideCompensation = AppliedSlideCompensation = FTransform::Identity;
	SlidePhaseClip = nullptr;
	const USkeletalMesh* Mesh = Character->GetMesh()->GetSkeletalMeshAsset();
	if (!Mesh) return;
	if (Entry.SlideInto.IsNull() || Entry.SlideLoop.IsNull() || Entry.SlideOutMoving.IsNull() || Entry.SlideOutStand.IsNull()) return;
	for (const auto& Soft : {Entry.SlideInto, Entry.SlideLoop, Entry.SlideOutMoving, Entry.SlideOutStand})
	{
		UAnimSequence* Clip = Soft.LoadSynchronous();
		if (!Clip || Clip->GetSkeleton() != Character->GetMesh()->GetSkeletalMeshAsset()->GetSkeleton())
		{
			SlideClips.Reset();
			return;
		}
		SlideClips.Add(Clip);
	}
}

FTransform USeleneMovementComponent::GetSlideMeshCompensation(USkeletalMeshComponent* Mesh, UAnimSequence* Clip, float Seconds)
{
	const USkeletalMesh* Asset = Mesh ? Mesh->GetSkeletalMeshAsset() : nullptr;
	if (!Asset || !Clip || Asset->GetRefSkeleton().GetNum() == 0 ||
		Asset->GetRefSkeleton().GetBoneName(0) != TEXT("mixamorig_Hips")) return FTransform::Identity;
	const FTransform& Reference = Asset->GetRefSkeleton().GetRefBonePose()[0];
	FTransform Authored = Clip->ExtractRootTrackTransform(FAnimExtractContext(FMath::Clamp(Seconds, 0.f, Clip->GetPlayLength())), nullptr);
	// Pin horizontal pelvis travel to its reference position. Preserve only the
	// authored height and orientation, with rotation about the hips, not the feet.
	Authored.SetTranslation(FVector(Reference.GetTranslation().X, Reference.GetTranslation().Y, Authored.GetTranslation().Z));
	Authored.SetScale3D(Reference.GetScale3D());
	return Reference.Inverse() * Authored;
}

void USeleneMovementComponent::RemoveSlideMeshCompensation()
{
	if (CharacterOwner && CharacterOwner->GetMesh() && !AppliedSlideCompensation.Equals(FTransform::Identity))
		CharacterOwner->GetMesh()->SetRelativeTransform(AppliedSlideCompensation.Inverse() * CharacterOwner->GetMesh()->GetRelativeTransform());
	AppliedSlideCompensation = FTransform::Identity;
}

void USeleneMovementComponent::TickSlidePose(float DeltaTime)
{
	UAnimInstance* Anim = CharacterOwner && CharacterOwner->GetMesh() ? CharacterOwner->GetMesh()->GetAnimInstance() : nullptr;
	if (!Anim) return;
	// StopSlide can be followed immediately by MOVE_Falling (ledge or slide-jump).
	if (bSlideExit && IsFalling())
	{
		if (SlidePose.IsValid()) Anim->Montage_Stop(AbilityBlendOut, SlidePose.Get());
		SlidePose.Reset();
		bSlideExit = false;
	}
	// The Out clip has finished or was stopped: hand DefaultSlot back to locomotion.
	if (bSlideExit && !(SlidePose.IsValid() && Anim->Montage_IsActive(SlidePose.Get()))) bSlideExit = false;
	if (IsSliding() && bSlideInto && SlideClips.Num() == 4 && SlidePose.IsValid() &&
		Anim->Montage_GetPosition(SlidePose.Get()) >= FMath::Min(1.25f, SlideClips[0]->GetPlayLength() - 0.08f))
	{
		SlidePose = Anim->PlaySlotAnimationAsDynamicMontage(SlideClips[1], TEXT("DefaultSlot"), 0.08f, 0.10f, 1.f, MAX_int32);
		SlidePhaseClip = SlideClips[1];
		bSlideInto = false;
	}
	FTransform Target = FTransform::Identity;
	if (SlidePose.IsValid() && SlidePhaseClip && Anim->Montage_IsActive(SlidePose.Get()))
		Target = GetSlideMeshCompensation(CharacterOwner->GetMesh(), SlidePhaseClip,
			FMath::Fmod(Anim->Montage_GetPosition(SlidePose.Get()), SlidePhaseClip->GetPlayLength()));
	// Carry the visual transform across Into/Loop/Out; ease to the normal mesh on
	// cancellation or falling without changing capsule, speed or crouch physics.
	CurrentSlideCompensation.Blend(CurrentSlideCompensation, Target, FMath::Clamp(DeltaTime * 30.f, 0.f, 1.f));
	AppliedSlideCompensation = CurrentSlideCompensation;
	CharacterOwner->GetMesh()->SetRelativeTransform(AppliedSlideCompensation * CharacterOwner->GetMesh()->GetRelativeTransform());
}

void USeleneMovementComponent::PlaySlidePose(bool bPlay)
{
	ASeleneCharacter* Character = Cast<ASeleneCharacter>(CharacterOwner);
	UAnimInstance* Anim = Character ? Character->GetMesh()->GetAnimInstance() : nullptr;
	if (!Anim) return;
	bSlideInto = false;
	bSlideExit = false;
	if (!bPlay)
	{
		if (SlidePose.IsValid()) Anim->Montage_Stop(AbilityBlendOut, SlidePose.Get());
		SlidePose.Reset();
		if (SlideClips.Num() == 4)
		{
			const float Speed = Velocity.Size2D();
			const bool bMoving = !Acceleration.IsNearlyZero() || !Character->GetPendingMovementInputVector().IsNearlyZero() || Speed > 150.f;
			// Match the base loop before starting Out: SetAnimationAsset otherwise cancels DefaultSlot.
			const auto& Entry = Character->GetActiveCharacterEntry();
			UAnimSequence* Base = Speed < 20.f ? Entry.IdleLoop.Get() : Speed < 250.f ? Entry.WalkLoop.Get() : Speed < 475.f ? Entry.RunLoop.Get() : Entry.SprintLoop.Get();
			if (UAnimSingleNodeInstance* Single = Character->GetMesh()->GetSingleNodeInstance(); Single && Base && Single->GetAnimationAsset() != Base)
				Single->SetAnimationAsset(Base, true);
			SlidePose = Anim->PlaySlotAnimationAsDynamicMontage(SlideClips[bMoving ? 2 : 3], TEXT("DefaultSlot"), 0.08f, 0.12f, 1.f);
			SlidePhaseClip = SlideClips[bMoving ? 2 : 3];
			bSlideExit = SlidePose.IsValid();
		}
		return;
	}
	if (SlideClips.Num() == 4)
	{
		SlidePose = Anim->PlaySlotAnimationAsDynamicMontage(SlideClips[0], TEXT("DefaultSlot"), 0.08f, 0.10f, 1.f, 1, -1.f, 0.55f);
		if (SlidePose.IsValid()) SlidePose->bEnableAutoBlendOut = false;
		SlidePhaseClip = SlideClips[0];
		bSlideInto = SlidePose.IsValid();
	}
	else if (UAnimSequence* Clip = Character->GetActiveCharacterEntry().Jump.Get())
	{
		// Preserve the original held jump pose and mesh drop for incomplete slide sets.
		SlidePose = Anim->PlaySlotAnimationAsDynamicMontage(Clip, TEXT("DefaultSlot"), AbilityBlendIn, AbilityBlendOut, 0.f, 1, -1.f, FMath::Min(SlidePoseTime, Clip->GetPlayLength()));
	}
}

void USeleneMovementComponent::PlayJumpOverlay()
{
	ASeleneCharacter* Character = Cast<ASeleneCharacter>(CharacterOwner);
	if (Character) if (UAnimInstance* Anim = Character->GetMesh()->GetAnimInstance())
		if (UAnimSequence* Clip = Character->GetActiveCharacterEntry().Jump.Get())
			Anim->PlaySlotAnimationAsDynamicMontage(Clip, TEXT("DefaultSlot"), AbilityBlendIn, AbilityBlendOut, 1.f);
}

bool USeleneMovementComponent::TryWallJump()
{
	if (!IsAdvancedMovementEnabled() || !IsFalling()) return false;
	FVector Direction = GetCurrentAcceleration().GetSafeNormal2D();
	if (Direction.IsNearlyZero()) Direction = FRotationMatrix(FRotator(0, CharacterOwner->GetControlRotation().Yaw, 0)).GetUnitAxis(EAxis::X);
	FHitResult Hit;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(SeleneWallJump), false, CharacterOwner);
	const FVector Start = UpdatedComponent->GetComponentLocation();
	if (!GetWorld()->SweepSingleByChannel(Hit, Start, Start + Direction * WallProbeReach, FQuat::Identity, UpdatedComponent->GetCollisionObjectType(), FCollisionShape::MakeSphere(CharacterOwner->GetCapsuleComponent()->GetScaledCapsuleRadius() * 0.9f), Params)) return false;
	if (FMath::Abs(Hit.ImpactNormal.Z) > 0.2f || FVector::DotProduct(Direction, Hit.ImpactNormal) > -0.2f) return false;
	if (LastWall == Hit.GetActor() && FVector::DotProduct(LastWallNormal, Hit.ImpactNormal) > 0.9f) return false;
	LastWall = Hit.GetActor(); LastWallNormal = Hit.ImpactNormal;
	Velocity = Hit.ImpactNormal.GetSafeNormal2D() * WallJumpSpeed + FVector(0, 0, WallJumpUpSpeed);
	bWallJumped = true;
	PlayJumpOverlay();
	return true;
}

void USeleneMovementComponent::UpdateCharacterStateBeforeMovement(float DeltaSeconds)
{
	Super::UpdateCharacterStateBeforeMovement(DeltaSeconds);
	if (IsAdvancedMovementEnabled() && (IsMovingOnGround() || (IsFalling() && Velocity.Z <= 0.f))) TryMantle();
}

bool USeleneMovementComponent::TryMantle()
{
	const FVector Direction = Acceleration.GetSafeNormal2D();
	if (Direction.IsNearlyZero()) return false;
	const UCapsuleComponent* Capsule = CharacterOwner->GetCapsuleComponent();
	const float Half = Capsule->GetScaledCapsuleHalfHeight();
	const float Radius = Capsule->GetScaledCapsuleRadius();
	const FVector Start = UpdatedComponent->GetComponentLocation();
	const float Feet = Start.Z - Half;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(SeleneMantle), false, CharacterOwner);
	FHitResult Front, Top;
	const ECollisionChannel Channel = UpdatedComponent->GetCollisionObjectType();
	if (!GetWorld()->SweepSingleByChannel(Front, Start, Start + Direction * MantleReach, FQuat::Identity, Channel, FCollisionShape::MakeCapsule(Radius, Half), Params) || FMath::Abs(Front.ImpactNormal.Z) > 0.3f) return false;
	FVector Probe = Front.ImpactPoint + Direction * MantleTopInset;
	Probe.Z = Feet + MantleMaxHeight + Radius;
	if (!GetWorld()->LineTraceSingleByChannel(Top, Probe, FVector(Probe.X, Probe.Y, Feet + MantleMinHeight - 1.f), Channel, Params) || !IsWalkable(Top)) return false;
	const float Height = Top.ImpactPoint.Z - Feet;
	if (Height < MantleMinHeight || Height > MantleMaxHeight) return false;
	const FVector Target(Probe.X, Probe.Y, Top.ImpactPoint.Z + Half + 2.15f);
	if (GetWorld()->OverlapBlockingTestByChannel(Target, FQuat::Identity, Channel, FCollisionShape::MakeCapsule(Radius, Half), Params)) return false;
	MantleStart = Start; MantleTarget = Target; MantleElapsed = 0.f;
	Velocity = FVector::ZeroVector;
	SetMovementMode(MOVE_Custom, 3);
	PlayJumpOverlay();
	return true;
}

void USeleneMovementComponent::PhysMantle(float DeltaTime, int32 Iterations)
{
	MantleElapsed += DeltaTime;
	const float T = FMath::Clamp(MantleElapsed / FMath::Max(0.1f, MantleSeconds), 0.f, 1.f);
	const FVector Raised(MantleStart.X, MantleStart.Y, MantleTarget.Z);
	const FVector Desired = T < 0.6f ? FMath::Lerp(MantleStart, Raised, FMath::SmoothStep(0.f, 0.6f, T))
		: FMath::Lerp(Raised, MantleTarget, FMath::SmoothStep(0.6f, 1.f, T));
	FHitResult Hit;
	SafeMoveUpdatedComponent(Desired - UpdatedComponent->GetComponentLocation(), UpdatedComponent->GetComponentQuat(), true, Hit);
	Velocity = FVector::ZeroVector;
	if (Hit.IsValidBlockingHit()) { SetMovementMode(MOVE_Falling); return; }
	if (T >= 1.f) { SetMovementMode(MOVE_Walking); bExtraJumpUsed = false; bWallJumped = false; LastWall.Reset(); }
}
