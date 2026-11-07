#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "SeleneCharacterSettings.h"
#include "SeleneCharacter.generated.h"

class UCameraComponent;
class USpringArmComponent;
struct FStreamableHandle;

UENUM(BlueprintType)
enum class ESeleneCameraMode : uint8
{
	ThirdPerson,
	FirstPerson
};

UENUM(BlueprintType)
enum class ESelenePace : uint8
{
	Walk,
	Jog,
	Sprint
};

/** Navigation and camera controls for the town visual demo. */
UCLASS()
class SELENE_API ASeleneCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	// AdvancedMovement hook: select the CMC subclass without changing animation ownership.
	ASeleneCharacter(const FObjectInitializer& ObjectInitializer = FObjectInitializer::Get());

	UFUNCTION(BlueprintCallable, Category = "Selene|Character")
	void SelectCharacter(FName Name);

	UFUNCTION(BlueprintCallable, Category = "Selene|Character")
	void CycleCharacter();

	/** Set before BeginPlay to make this an unpossessed NPC wearing that roster entry. */
	void SetNpcCharacter(FName Name) { NpcCharacter = Name; }
	bool IsNpc() const { return !NpcCharacter.IsNone(); }

	UFUNCTION(BlueprintPure, Category = "Selene|Character")
	FName GetActiveCharacterName() const { return ActiveCharacterName; }

	/** Roster entry of the active character (read by USeleneSecondaryAnimInstance when it builds its graph). */
	const FSelenePlayableCharacter& GetActiveCharacterEntry() const { return ActiveCharacter; }

	UFUNCTION(BlueprintCallable, Category = "Selene|Camera")
	void SetCameraMode(ESeleneCameraMode NewMode);

	UFUNCTION(BlueprintPure, Category = "Selene|Camera")
	ESeleneCameraMode GetCameraMode() const { return CameraMode; }

	UFUNCTION(BlueprintCallable, Category = "Selene|Camera")
	void ToggleCameraMode();

	UFUNCTION(BlueprintCallable, Category = "Selene|Movement")
	void SetMovementPace(ESelenePace NewPace);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Selene|Movement", meta = (ClampMin = "0"))
	float WalkSpeed = 150.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Selene|Movement", meta = (ClampMin = "0"))
	float JogSpeed = 350.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Selene|Movement", meta = (ClampMin = "0"))
	float SprintSpeed = 600.f;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Selene|Camera")
	TObjectPtr<USpringArmComponent> CameraBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Selene|Camera")
	TObjectPtr<UCameraComponent> ThirdPersonCamera;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Selene|Camera")
	TObjectPtr<UCameraComponent> FirstPersonCamera;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Selene|Camera")
	ESeleneCameraMode CameraMode = ESeleneCameraMode::ThirdPerson;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Selene|Movement")
	ESelenePace MovementPace = ESelenePace::Jog;

private:
	void ApplyCharacter(const FSelenePlayableCharacter& Entry, uint64 RequestId);
	void ConfigureBlendAxes();
	void UpdateSingleNodeAnimation(float DeltaSeconds);
	void TickDebugDrivers(float DeltaSeconds);
	void TickAnimMatch(float DeltaSeconds);
	float AnimMatchTime = -5.f;
	int32 AnimMatchView = INDEX_NONE;
	int32 AnimMatchShot = 0;
	FVector AnimMatchOrigin = FVector::ZeroVector;
	bool bAnimMatchJumped = false;
	float DebugTime = 0.f;
	float NextAutoShot = 0.f;
	float AutoWalkBaseYaw = 0.f;

	// Streamable handles keep all loaded soft assets alive, including inactive jump/land clips.
	TSharedPtr<FStreamableHandle> PendingCharacterLoad;
	TSharedPtr<FStreamableHandle> ActiveCharacterLoad;
	FSelenePlayableCharacter ActiveCharacter;
	FName ActiveCharacterName;
	FName PendingCharacterName;
	FName NpcCharacter;
	uint64 CharacterRequestId = 0;
	int32 SpeedAxis = 0;
	int32 DirectionAxis = INDEX_NONE;
	bool bWasFalling = false;
	enum class ESingleNodePhase : uint8 { Ground, Jump, Fall, Land };
	ESingleNodePhase SingleNodePhase = ESingleNodePhase::Ground;

	// Borrowed-clip locomotion (roster WalkLoop etc.): ground loop choice, speed matching and transitions.
	UAnimationAsset* ChooseGroundLoop(float Speed, float& OutPlayRate) const;
	void UpdateLocomotionTransitions(float Speed, float DeltaSeconds);
	void PlayTransition(UAnimSequence* Clip, float BlendIn, float BlendOut);
	float PrevSpeed = 0.f;
	bool bHadInput = false;
	float TransitionCooldown = 0.f;
};
