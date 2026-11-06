#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "SeleneCharacter.generated.h"

class UCameraComponent;
class USpringArmComponent;

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
	ASeleneCharacter();

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
};
