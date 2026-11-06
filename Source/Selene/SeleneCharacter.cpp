#include "SeleneCharacter.h"

#include "Selene.h"
#include "Animation/SeleneSecondaryAnimInstance.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Animation/AnimSequence.h"
#include "Animation/BlendSpace.h"
#include "Animation/BlendSpace1D.h"
#include "Engine/AssetManager.h"
#include "Engine/StreamableManager.h"
#include "Materials/MaterialInterface.h"
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

	FAutoConsoleCommandWithWorldAndArgs CharacterCommand(
		TEXT("selene.Character"), TEXT("Select a playable character: selene.Character <Name|next|list>"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (Args.Num() != 1)
			{
				UE_LOG(LogSelene, Warning, TEXT("Usage: selene.Character <Name|next|list>"));
				return;
			}
			if (Args[0].Equals(TEXT("list"), ESearchCase::IgnoreCase))
			{
				for (const FSelenePlayableCharacter& Entry : GetDefault<USeleneCharacterSettings>()->Roster)
				{
					UE_LOG(LogSelene, Log, TEXT("Playable character: %s"), *Entry.Name.ToString());
				}
				return;
			}
			if (World)
			{
				for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
				{
					APlayerController* PC = It->Get();
					ASeleneCharacter* Character = PC && PC->IsLocalPlayerController()
						? Cast<ASeleneCharacter>(PC->GetPawn()) : nullptr;
					if (Character)
					{
						if (Args[0].Equals(TEXT("next"), ESearchCase::IgnoreCase)) Character->CycleCharacter();
						else Character->SelectCharacter(FName(*Args[0]));
						return;
					}
				}
			}
			UE_LOG(LogSelene, Warning, TEXT("selene.Character: no local Selene character is possessed."));
		}), ECVF_Default);

}

ASeleneCharacter::ASeleneCharacter()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false;
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
		ActiveCharacterName = TEXT("Manny");
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
	const USeleneCharacterSettings* Settings = GetDefault<USeleneCharacterSettings>();
	if (!Settings->Roster.IsEmpty())
	{
		const bool bHasDefault = Settings->Roster.ContainsByPredicate([Settings](const FSelenePlayableCharacter& Entry)
		{
			return Entry.Name == Settings->DefaultCharacter;
		});
		// A Manny-only roster remains usable even if DefaultCharacter was not overridden.
		SelectCharacter(bHasDefault ? Settings->DefaultCharacter : Settings->Roster[0].Name);
	}
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

void ASeleneCharacter::SelectCharacter(FName Name)
{
	const FSelenePlayableCharacter* Entry = GetDefault<USeleneCharacterSettings>()->Roster.FindByPredicate(
		[Name](const FSelenePlayableCharacter& Candidate) { return Candidate.Name == Name; });
	if (!Entry || Entry->Name.IsNone() || Entry->Mesh.IsNull())
	{
		UE_LOG(LogSelene, Warning, TEXT("selene.Character: unknown or invalid roster entry '%s'; keeping '%s'."),
			*Name.ToString(), *ActiveCharacterName.ToString());
		return;
	}

	const uint64 RequestId = ++CharacterRequestId;
	if (PendingCharacterLoad) PendingCharacterLoad->CancelHandle();
	PendingCharacterLoad.Reset();
	PendingCharacterName = Name;
	TArray<FSoftObjectPath> Paths;
	auto AddPath = [&Paths](const auto& Asset)
	{
		if (!Asset.IsNull()) Paths.AddUnique(Asset.ToSoftObjectPath());
	};
	AddPath(Entry->Mesh);
	AddPath(Entry->AnimClass);
	AddPath(Entry->Locomotion);
	AddPath(Entry->FallLoop);
	AddPath(Entry->Jump);
	AddPath(Entry->Land);
	AddPath(Entry->OverrideMaterial);
	PendingCharacterLoad = UAssetManager::GetStreamableManager().RequestAsyncLoad(Paths,
		FStreamableDelegate::CreateWeakLambda(this, [this, Selection = *Entry, RequestId]()
		{
			ApplyCharacter(Selection, RequestId);
		}), FStreamableManager::DefaultAsyncLoadPriority, false, true);
	if (PendingCharacterLoad)
	{
		// Store the handle before starting, even when every asset is already resident.
		PendingCharacterLoad->StartStalledHandle();
	}
	else
	{
		PendingCharacterName = NAME_None;
		UE_LOG(LogSelene, Warning, TEXT("selene.Character: could not request assets for '%s'; keeping '%s'."),
			*Name.ToString(), *ActiveCharacterName.ToString());
	}
}

void ASeleneCharacter::CycleCharacter()
{
	const TArray<FSelenePlayableCharacter>& Roster = GetDefault<USeleneCharacterSettings>()->Roster;
	if (Roster.IsEmpty())
	{
		UE_LOG(LogSelene, Warning, TEXT("selene.Character: roster is empty."));
		return;
	}
	// Rapid presses advance from the pending selection; the latest request wins.
	const FName From = PendingCharacterName.IsNone() ? ActiveCharacterName : PendingCharacterName;
	const int32 Index = Roster.IndexOfByPredicate([From](const FSelenePlayableCharacter& Entry)
	{
		return Entry.Name == From;
	});
	SelectCharacter(Roster[(Index + 1) % Roster.Num()].Name);
}

void ASeleneCharacter::ApplyCharacter(const FSelenePlayableCharacter& Entry, uint64 RequestId)
{
	if (RequestId != CharacterRequestId) return;
	bool bLoaded = true;
	auto Validate = [this, &Entry, &bLoaded](const auto& Asset)
	{
		if (!Asset.IsNull() && !Asset.Get())
		{
			UE_LOG(LogSelene, Warning, TEXT("selene.Character: '%s' failed to load '%s'; keeping '%s'."),
				*Entry.Name.ToString(), *Asset.ToSoftObjectPath().ToString(), *ActiveCharacterName.ToString());
			bLoaded = false;
		}
	};
	Validate(Entry.Mesh);
	Validate(Entry.AnimClass);
	Validate(Entry.Locomotion);
	Validate(Entry.FallLoop);
	Validate(Entry.Jump);
	Validate(Entry.Land);
	Validate(Entry.OverrideMaterial);
	PendingCharacterName = NAME_None;
	if (!bLoaded)
	{
		PendingCharacterLoad.Reset();
		return;
	}

	// Nothing on the live pawn is changed until all configured assets have loaded successfully.
	USkeletalMeshComponent* Mesh = GetMesh();
	Mesh->SetAnimInstanceClass(nullptr);
	Mesh->SetSkeletalMesh(Entry.Mesh.Get());
	Mesh->EmptyOverrideMaterials();
	Mesh->SetRelativeLocationAndRotation(Entry.MeshOffset, Entry.MeshRotation);
	if (UMaterialInterface* Material = Entry.OverrideMaterial.Get())
	{
		for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot) Mesh->SetMaterial(Slot, Material);
	}
	ActiveCharacter = Entry;
	ActiveCharacterName = Entry.Name;
	ActiveCharacterLoad = MoveTemp(PendingCharacterLoad);
	if (UClass* AnimClass = Entry.AnimClass.Get())
	{
		Mesh->SetAnimationMode(EAnimationMode::AnimationBlueprint);
		Mesh->SetAnimInstanceClass(AnimClass);
		SetActorTickEnabled(false);
	}
	else if (!Entry.SecondaryChains.IsEmpty())
	{
		// Same single-node locomotion, plus Kawaii Physics chains (hair/braid/skirt/wings) in a native graph.
		// ActiveCharacter is already set: the instance reads its chains from GetActiveCharacterEntry().
		Mesh->SetAnimationMode(EAnimationMode::AnimationBlueprint);
		Mesh->SetAnimInstanceClass(USeleneSecondaryAnimInstance::StaticClass());
		SingleNodePhase = ESingleNodePhase::Ground;
		bWasFalling = GetCharacterMovement()->IsFalling();
		ConfigureBlendAxes();
		UpdateSingleNodeAnimation(0.f);
		SetActorTickEnabled(true);
	}
	else
	{
		Mesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
		SingleNodePhase = ESingleNodePhase::Ground;
		bWasFalling = GetCharacterMovement()->IsFalling();
		ConfigureBlendAxes();
		UpdateSingleNodeAnimation(0.f);
		SetActorTickEnabled(true);
	}

	BaseEyeHeight = Entry.EyeHeight - GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight();
	FirstPersonCamera->AttachToComponent(GetCapsuleComponent(), FAttachmentTransformRules::KeepRelativeTransform);
	FirstPersonCamera->SetRelativeLocationAndRotation(FVector(0.f, 0.f, BaseEyeHeight), FRotator::ZeroRotator);
	CameraBoom->TargetArmLength = Entry.BoomLength;
	// Do not call SetCameraMode here: entering 1P can rotate the actor. A swap preserves rotation.
	Mesh->SetOwnerNoSee(CameraMode == ESeleneCameraMode::FirstPerson);
	Mesh->SetCastShadow(true);
	Mesh->bCastHiddenShadow = true;
	Mesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
	UE_LOG(LogSelene, Log, TEXT("Active playable character: %s"), *ActiveCharacterName.ToString());
}

void ASeleneCharacter::ConfigureBlendAxes()
{
	SpeedAxis = 0;
	DirectionAxis = INDEX_NONE;
	UBlendSpace* Blend = ActiveCharacter.Locomotion.Get();
	if (!Blend) return;
	const int32 AxisCount = Blend->IsA<UBlendSpace1D>() ? 1 : 2;
	int32 NamedSpeed = INDEX_NONE;
	int32 NamedDirection = INDEX_NONE;
	for (int32 Axis = 0; Axis < AxisCount; ++Axis)
	{
		const FBlendParameter& Parameter = Blend->GetBlendParameter(Axis);
		UE_LOG(LogSelene, Log, TEXT("%s locomotion axis %d: '%s' [%g, %g]"),
			*ActiveCharacterName.ToString(), Axis, *Parameter.DisplayName, Parameter.Min, Parameter.Max);
		if (Parameter.DisplayName.Contains(TEXT("speed"), ESearchCase::IgnoreCase)) NamedSpeed = Axis;
		if (Parameter.DisplayName.Contains(TEXT("direction"), ESearchCase::IgnoreCase) ||
			Parameter.DisplayName.Contains(TEXT("angle"), ESearchCase::IgnoreCase)) NamedDirection = Axis;
	}
	if (AxisCount == 2)
	{
		if (NamedSpeed != INDEX_NONE) SpeedAxis = NamedSpeed;
		else if (NamedDirection != INDEX_NONE) SpeedAxis = 1 - NamedDirection;
		else
		{
			// Common unnamed template layout: signed direction and nonnegative speed.
			const FBlendParameter& X = Blend->GetBlendParameter(0);
			const FBlendParameter& Y = Blend->GetBlendParameter(1);
			if (X.Min < 0.f && Y.Min >= 0.f) SpeedAxis = 1;
			else if (!(Y.Min < 0.f && X.Min >= 0.f))
			{
				UE_LOG(LogSelene, Warning, TEXT("%s: ambiguous locomotion axes; using X=speed, Y=direction. Verify axis names/ranges."),
					*ActiveCharacterName.ToString());
			}
		}
		DirectionAxis = 1 - SpeedAxis;
	}
	UE_LOG(LogSelene, Log, TEXT("%s locomotion mapping: speed axis=%d (cm/s), direction axis=%d (degrees; -1=unused)."),
		*ActiveCharacterName.ToString(), SpeedAxis, DirectionAxis);
}

void ASeleneCharacter::UpdateSingleNodeAnimation(float DeltaSeconds)
{
	UAnimSingleNodeInstance* Instance = GetMesh()->GetSingleNodeInstance();
	if (!Instance) return;
	const bool bFalling = GetCharacterMovement()->IsFalling();
	if (bFalling)
	{
		if (!bWasFalling && GetVelocity().Z > 0.f && ActiveCharacter.Jump.Get())
		{
			SingleNodePhase = ESingleNodePhase::Jump;
		}
		else if (SingleNodePhase != ESingleNodePhase::Jump || GetVelocity().Z <= 0.f ||
			Instance->GetCurrentTime() + DeltaSeconds >= Instance->GetLength())
		{
			SingleNodePhase = ESingleNodePhase::Fall;
		}
	}
	else if (bWasFalling && ActiveCharacter.Land.Get())
	{
		SingleNodePhase = ESingleNodePhase::Land;
	}
	else if (SingleNodePhase != ESingleNodePhase::Land ||
		Instance->GetCurrentTime() + DeltaSeconds >= FMath::Min(0.2f, Instance->GetLength()))
	{
		SingleNodePhase = ESingleNodePhase::Ground;
	}
	bWasFalling = bFalling;

	UAnimationAsset* Animation = ActiveCharacter.Locomotion.Get();
	bool bLoop = true;
	if (SingleNodePhase == ESingleNodePhase::Jump)
	{
		Animation = ActiveCharacter.Jump.Get();
		bLoop = false;
	}
	else if (SingleNodePhase == ESingleNodePhase::Fall)
	{
		if (ActiveCharacter.FallLoop.Get()) Animation = ActiveCharacter.FallLoop.Get();
		else if (ActiveCharacter.Jump.Get())
		{
			Animation = ActiveCharacter.Jump.Get();
			bLoop = false;
		}
	}
	else if (SingleNodePhase == ESingleNodePhase::Land)
	{
		Animation = ActiveCharacter.Land.Get();
		bLoop = false;
	}
	if (Instance->GetAnimationAsset() != Animation)
	{
		Instance->SetAnimationAsset(Animation, bLoop);
		Instance->SetPosition(0.f, false);
		Instance->SetPlaying(true);
	}
	if (UBlendSpace* Blend = ActiveCharacter.Locomotion.Get(); Blend && Animation == Blend)
	{
		FVector Input = FVector::ZeroVector;
		const FVector Velocity = GetVelocity();
		const float Speed = Velocity.Size2D();
		const FBlendParameter& SpeedParameter = Blend->GetBlendParameter(SpeedAxis);
		Input[SpeedAxis] = FMath::Clamp(Speed, SpeedParameter.Min, SpeedParameter.Max);
		if (DirectionAxis != INDEX_NONE)
		{
			const FVector Local = FRotator(0.f, GetActorRotation().Yaw, 0.f).UnrotateVector(Velocity);
			float Direction = Speed > KINDA_SMALL_NUMBER ? FMath::RadiansToDegrees(FMath::Atan2(Local.Y, Local.X)) : 0.f;
			const FBlendParameter& DirectionParameter = Blend->GetBlendParameter(DirectionAxis);
			if (DirectionParameter.Min >= 0.f && Direction < 0.f) Direction += 360.f;
			Input[DirectionAxis] = FMath::Clamp(Direction, DirectionParameter.Min, DirectionParameter.Max);
		}
		Instance->SetBlendSpacePosition(Input);
	}
}

void ASeleneCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	UpdateSingleNodeAnimation(DeltaSeconds);
}

void ASeleneCharacter::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	++CharacterRequestId;
	if (PendingCharacterLoad) PendingCharacterLoad->CancelHandle();
	PendingCharacterLoad.Reset();
	ActiveCharacterLoad.Reset();
	Super::EndPlay(EndPlayReason);
}
