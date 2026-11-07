#pragma once

#include "CoreMinimal.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Movement/SeleneMovementTestDriver.h"
#include "Widgets/SWidget.h"
#include "SeleneMovementComponent.generated.h"

/** Single-player hero movement. The disabled path delegates unchanged to stock CMC. */
UCLASS()
class SELENE_API USeleneMovementComponent : public UCharacterMovementComponent
{
	GENERATED_BODY()
public:
	USeleneMovementComponent();
	virtual ~USeleneMovementComponent() override;
	static bool IsAdvancedMovementEnabled();
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
	virtual float GetMaxSpeed() const override;
	virtual void CalcVelocity(float DeltaTime, float Friction, bool bFluid, float BrakingDeceleration) override;
	virtual FVector GetAirControl(float DeltaTime, float TickAirControl, const FVector& FallAcceleration) override;
	virtual void ProcessLanded(const FHitResult& Hit, float RemainingTime, int32 Iterations) override;
	virtual bool DoJump(bool bReplayingMoves, float DeltaTime) override;
	virtual void PhysCustom(float DeltaTime, int32 Iterations) override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	bool TryDash();
	bool TryAdvancedJump();
	bool TryWallJump();
	virtual void UpdateCharacterStateBeforeMovement(float DeltaSeconds) override;
	bool IsMantling() const { return MovementMode == MOVE_Custom && CustomMovementMode == 3; }
	UFUNCTION(BlueprintCallable, Category="Selene|Slide")
	bool TrySlide();
	UFUNCTION(BlueprintCallable, Category="Selene|Slide")
	void StopSlide();
	/** Visual root compensation for hips-root slides; never moves the capsule. */
	UFUNCTION(BlueprintCallable, Category="Selene|Slide")
	static FTransform GetSlideMeshCompensation(class USkeletalMeshComponent* Mesh, class UAnimSequence* Clip, float Seconds);
	bool IsSliding() const { return MovementMode == MOVE_Custom && CustomMovementMode == 2; }
	/** True while the slide's Out clip still owns DefaultSlot after the physical slide ended. */
	bool IsSlideExitPlaying() const { return bSlideExit; }
	virtual bool CanCrouchInCurrentState() const override;
	bool IsDashing() const { return MovementMode == MOVE_Custom && CustomMovementMode == 1; }
	float GetStamina() const { return Stamina; }
	float GetFOVKick() const { return CurrentFOVKick; }

	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Dash")
	float DashSpeed = 1100.f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Dash")
	float DashSeconds = 0.20f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Dash")
	float DashFOVKick = 7.f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Dash")
	float FOVReturnSpeed = 12.f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Stamina")
	int32 StaminaCharges = 3;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Stamina")
	float ChargeRegenSeconds = 2.f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Stamina")
	float StaminaRegenDelay = 0.8f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Slide")
	float SlideMinSpeed = 480.f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Slide")
	float SlideEndSpeed = 180.f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Slide")
	float SlideHalfHeight = 48.f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Slide")
	float SlideBraking = 100.f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Slide")
	float SlideFriction = 0.12f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Slide")
	float SlideCameraDrop = 40.f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Slide")
	float SlidePoseTime = 0.52f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Slide")
	float SlidePoseMeshDrop = 32.f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Extra Jump")
	float ExtraJumpVelocity = 500.f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Extra Jump")
	float ExtraJumpRedirect = 0.65f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Animation")
	float AbilityBlendIn = 0.10f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Animation")
	float AbilityBlendOut = 0.12f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Wall Jump")
	float WallProbeReach = 55.f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Wall Jump")
	float WallJumpSpeed = 650.f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Wall Jump")
	float WallJumpUpSpeed = 560.f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Mantle")
	float MantleMinHeight = 80.f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Mantle")
	float MantleMaxHeight = 225.f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Mantle")
	float MantleReach = 110.f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Mantle")
	float MantleTopInset = 50.f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Mantle")
	float MantleSeconds = 0.65f;

	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Momentum", meta=(ClampMin="0"))
	float MovingGroundFriction = 5.0f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Momentum", meta=(ClampMin="0"))
	float GroundBraking = 1400.0f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Momentum", meta=(ClampMin="0"))
	float LandingCarrySeconds = 0.30f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Momentum", meta=(ClampMin="0"))
	float LandingFriction = 0.12f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Momentum", meta=(ClampMin="0"))
	float LandingBraking = 90.0f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Momentum", meta=(ClampMin="0"))
	float ExcessSpeedDecay = 125.0f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Momentum", meta=(ClampMin="0", ClampMax="1"))
	float AirSteering = 0.22f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Momentum", meta=(ClampMin="0"))
	float AirAccelerationLimit = 450.0f;
	UPROPERTY(EditAnywhere, Category="Selene|Advanced Movement|Momentum", meta=(ClampMin="0"))
	float ChainJumpBonus = 65.0f;

	float GetLandingCarryRemaining() const { return LandingCarryRemaining; }
	FString GetMoveState() const;

private:
	void TickFeedback(float DeltaTime);
	void FinishDash();
	void PhysSlide(float DeltaTime, int32 Iterations);
	void PlaySlidePose(bool bPlay);
	void TickSlidePose(float DeltaTime);
	void RemoveSlideMeshCompensation();
	void LoadSlideClips();
	void PlayJumpOverlay();
	bool TryMantle();
	void PhysMantle(float DeltaTime, int32 Iterations);
	FVector MantleStart, MantleTarget;
	float MantleElapsed = 0.f;
	bool bExtraJumpUsed = false;
	bool bWallJumped = false;
	TWeakObjectPtr<AActor> LastWall;
	FVector LastWallNormal = FVector::ZeroVector;
	float CurrentCameraDrop = 0.f;
	float OriginalCrouchHalfHeight = 40.f;
	bool bOriginalCanCrouch = false;
	TWeakObjectPtr<class UAnimMontage> SlidePose;
	UPROPERTY(Transient)
	TArray<TObjectPtr<class UAnimSequence>> SlideClips;
	UPROPERTY(Transient)
	TObjectPtr<class UAnimSequence> SlidePhaseClip;
	FTransform CurrentSlideCompensation = FTransform::Identity;
	FTransform AppliedSlideCompensation = FTransform::Identity;
	FName SlideClipHero;
	bool bSlideInto = false;
	bool bSlideExit = false;
	float AppliedSlideMeshDrop = 0.f;
	float Stamina = 3.f;
	float RegenDelayRemaining = 0.f;
	float DashRemaining = 0.f;
	float CurrentFOVKick = 0.f;
	bool bDashFromGround = false;
	FVector DashDirection = FVector::ForwardVector;
	TSharedPtr<SWidget> StaminaWidget;
	TMap<TWeakObjectPtr<class UCameraComponent>, float> OriginalFOV;
	float LandingCarryRemaining = 0.f;
	float MomentumSpeedAllowance = 0.f;
	TUniquePtr<FSeleneMovementTestDriver> TestDriver;
};
