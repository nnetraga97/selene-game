#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "SelenePlayerController.generated.h"

class UInputAction;
class UInputMappingContext;
struct FInputActionValue;

/** Owns the transient Enhanced Input setup; requires no input assets. */
UCLASS()
class SELENE_API ASelenePlayerController : public APlayerController
{
	GENERATED_BODY()

protected:
	virtual void BeginPlay() override;
	virtual void SetupInputComponent() override;
	virtual void OnPossess(APawn* InPawn) override;
	virtual void OnUnPossess() override;
	virtual void AcknowledgePossession(APawn* InPawn) override;
	virtual void ReceivedPlayer() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	void CreateRuntimeInput();
	void AddRuntimeMappingContext();
	void Move(const FInputActionValue& Value);
	void Look(const FInputActionValue& Value);
	void StartJump();
	void EndJump();
	void StartSprint();
	void EndSprint();
	void ToggleWalk();
	void ToggleCamera();
	void CycleCharacter();
	void ApplyMovementPace();

	UPROPERTY(Transient)
	TObjectPtr<UInputMappingContext> RuntimeMappingContext;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> MoveAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> LookAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> JumpAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> SprintAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> WalkAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> CameraAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> CharacterAction;

	bool bSprintHeld = false;
	bool bWalkToggled = false;
};
