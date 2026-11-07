#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "SelenePlayerController.generated.h"

class SSelenePauseMenu;
class SSeleneFpsCounter;
class SSeleneMapView;
class SSeleneHeroPicker;
class USceneCaptureComponent2D;
class UTextureRenderTarget2D;
class UInputAction;
class UInputMappingContext;
struct FInputActionValue;

/** Owns the transient Enhanced Input setup; requires no input assets. */
UCLASS()
class SELENE_API ASelenePlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	void TogglePauseMenu();
	void ClosePauseMenu();
	void ToggleMap();
	void ToggleFpsCounter();
	void ToggleHeroPicker();
	void CloseHeroPicker();
	FVector GetMapCenter() const { return MapCenter; }
	float GetMapWidthCm() const { return MapWidthCm; }

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
	void ZoomMap(const FInputActionValue& Value);
	void CaptureMap();
	void CloseMap();
	bool IsCaptureRun() const;

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

	TSharedPtr<SSelenePauseMenu> PauseMenu;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> MenuAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> MapAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> MapZoomAction;

	UPROPERTY(Transient)
	TObjectPtr<UInputAction> FpsAction;

	UPROPERTY(Transient)
	TObjectPtr<USceneCaptureComponent2D> MapCapture;

	UPROPERTY(Transient)
	TObjectPtr<UTextureRenderTarget2D> MapTarget;

	TSharedPtr<SSeleneMapView> MapView;
	TSharedPtr<SSeleneHeroPicker> HeroPicker;
	TSharedPtr<SSeleneFpsCounter> FpsCounter;
	FVector MapCenter = FVector::ZeroVector;
	float MapWidthCm = 40000.f;

	bool bSprintHeld = false;
	bool bWalkToggled = false;
};
