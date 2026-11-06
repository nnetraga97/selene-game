#include "SeleneCharacter.h"

#include "Selene.h"
#include "Animation/AnimInstance.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "HAL/IConsoleManager.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	// ECVF_Default (not Cheat) and no build guards: perf runners can invoke this in Shipping.
	FAutoConsoleCommandWithWorldAndArgs CameraCommand(
		TEXT("selene.Camera"), TEXT("Set the local camera: selene.Camera 1p|3p|toggle"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (!World || Args.Num() != 1 ||
				(!Args[0].Equals(TEXT("1p"), ESearchCase::IgnoreCase) &&
				 !Args[0].Equals(TEXT("3p"), ESearchCase::IgnoreCase) &&
				 !Args[0].Equals(TEXT("toggle"), ESearchCase::IgnoreCase)))
			{
				UE_LOG(LogSelene, Warning, TEXT("Usage: selene.Camera 1p|3p|toggle"));
				return;
			}

			for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
			{
				APlayerController* PC = It->Get();
				if (PC && PC->IsLocalPlayerController())
				{
					if (ASeleneCharacter* Character = Cast<ASeleneCharacter>(PC->GetPawn()))
					{
						if (Args[0].Equals(TEXT("toggle"), ESearchCase::IgnoreCase))
						{
							Character->ToggleCameraMode();
						}
						else
						{
							Character->SetCameraMode(Args[0].Equals(TEXT("1p"), ESearchCase::IgnoreCase)
								? ESeleneCameraMode::FirstPerson : ESeleneCameraMode::ThirdPerson);
						}
						return;
					}
				}
			}
			UE_LOG(LogSelene, Warning, TEXT("selene.Camera: no local Selene character is possessed."));
		}));
}

ASeleneCharacter::ASeleneCharacter()
{
	PrimaryActorTick.bCanEverTick = false;
	GetCapsuleComponent()->InitCapsuleSize(34.f, 87.5f);
	BaseEyeHeight = 64.f;
	bUseControllerRotationPitch = false;
	bUseControllerRotationYaw = false;
	bUseControllerRotationRoll = false;

	UCharacterMovementComponent* Movement = GetCharacterMovement();
	Movement->bOrientRotationToMovement = true;
	Movement->RotationRate = FRotator(0.f, 500.f, 0.f);
	Movement->MaxWalkSpeed = JogSpeed;
	Movement->JumpZVelocity = 500.f;
	Movement->AirControl = 0.35f;
	Movement->BrakingDecelerationWalking = 2000.f;

	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(GetCapsuleComponent());
	CameraBoom->TargetArmLength = 350.f;
	CameraBoom->bUsePawnControlRotation = true;
	CameraBoom->bEnableCameraLag = true;
	CameraBoom->CameraLagSpeed = 10.f;
	CameraBoom->TargetOffset = FVector(0.f, 0.f, 50.f);

	ThirdPersonCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("ThirdPersonCamera"));
	ThirdPersonCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	ThirdPersonCamera->bUsePawnControlRotation = false;

	FirstPersonCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FirstPersonCamera"));
	FirstPersonCamera->SetupAttachment(GetCapsuleComponent());
	FirstPersonCamera->SetRelativeLocation(FVector(0.f, 0.f, BaseEyeHeight));
	FirstPersonCamera->bUsePawnControlRotation = true;
	FirstPersonCamera->SetAutoActivate(false);

	GetMesh()->SetRelativeLocationAndRotation(FVector(0.f, 0.f, -87.5f), FRotator(0.f, -90.f, 0.f));
	GetMesh()->bCastHiddenShadow = true;
	// A head-attached camera and hidden shadows still need an updated pose when owner-hidden.
	GetMesh()->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;

	static ConstructorHelpers::FObjectFinderOptional<USkeletalMesh> Manny(
		TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple"));
	if (Manny.Succeeded())
	{
		GetMesh()->SetSkeletalMesh(Manny.Get());
	}
	else
	{
		UE_LOG(LogSelene, Warning, TEXT("Selene: default SKM_Manny_Simple mesh is missing."));
	}

	static ConstructorHelpers::FClassFinder<UAnimInstance> UnarmedAnim(
		TEXT("/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed"));
	if (UnarmedAnim.Succeeded())
	{
		GetMesh()->SetAnimInstanceClass(UnarmedAnim.Class);
	}
	else
	{
		UE_LOG(LogSelene, Warning, TEXT("Selene: default ABP_Unarmed animation blueprint is missing."));
	}
}

void ASeleneCharacter::BeginPlay()
{
	Super::BeginPlay();
	// Resolve after Blueprint defaults have been applied; DoesSocketExist also recognizes head bones.
	if (GetMesh()->DoesSocketExist(TEXT("head")))
	{
		FirstPersonCamera->AttachToComponent(GetMesh(), FAttachmentTransformRules::SnapToTargetNotIncludingScale,
			TEXT("head"));
	}
	else
	{
		FirstPersonCamera->AttachToComponent(GetCapsuleComponent(), FAttachmentTransformRules::KeepRelativeTransform);
		FirstPersonCamera->SetRelativeLocationAndRotation(FVector(0.f, 0.f, 64.f), FRotator::ZeroRotator);
	}
	SetCameraMode(CameraMode);
	SetMovementPace(MovementPace);
}

void ASeleneCharacter::SetCameraMode(ESeleneCameraMode NewMode)
{
	CameraMode = NewMode;
	const bool bFirstPerson = CameraMode == ESeleneCameraMode::FirstPerson;
	FirstPersonCamera->SetActive(bFirstPerson);
	ThirdPersonCamera->SetActive(!bFirstPerson);
	bUseControllerRotationYaw = bFirstPerson;
	GetCharacterMovement()->bOrientRotationToMovement = !bFirstPerson;
	GetMesh()->SetOwnerNoSee(bFirstPerson);
	if (bFirstPerson && Controller)
	{
		SetActorRotation(FRotator(0.f, Controller->GetControlRotation().Yaw, 0.f));
	}
}

void ASeleneCharacter::ToggleCameraMode()
{
	SetCameraMode(CameraMode == ESeleneCameraMode::ThirdPerson
		? ESeleneCameraMode::FirstPerson : ESeleneCameraMode::ThirdPerson);
}

void ASeleneCharacter::SetMovementPace(ESelenePace NewPace)
{
	MovementPace = NewPace;
	float Speed = JogSpeed;
	switch (MovementPace)
	{
	case ESelenePace::Walk: Speed = WalkSpeed; break;
	case ESelenePace::Sprint: Speed = SprintSpeed; break;
	default: break;
	}
	GetCharacterMovement()->MaxWalkSpeed = FMath::Max(0.f, Speed);
}
