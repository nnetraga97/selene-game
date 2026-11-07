#include "SeleneCharacter.h"

// AdvancedMovement hook: all ability/physics logic lives in Movement/.
#include "Movement/SeleneMovementComponent.h"

#include "Selene.h"
#include "Animation/SeleneSecondaryAnimInstance.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimMontage.h"
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
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "DrawDebugHelpers.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "HAL/IConsoleManager.h"
#include "HAL/FileManager.h"
#include "Misc/Paths.h"
#include "UnrealClient.h"
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

ASeleneCharacter::ASeleneCharacter(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer.SetDefaultSubobjectClass<USeleneMovementComponent>(ACharacter::CharacterMovementComponentName))
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
	if (IsNpc())
	{
		// Unpossessed townsperson: keep gravity and floor snapping without a controller.
		GetCharacterMovement()->bRunPhysicsWithNoController = true;
		SelectCharacter(NpcCharacter);
	}
	else if (!Settings->Roster.IsEmpty())
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
	// YSOLDE MATERIAL SLOTS: include named materials in the existing async load.
	for (const auto& SlotMaterial : Entry->SlotMaterials) AddPath(SlotMaterial.Value);
	// END YSOLDE MATERIAL SLOTS
	AddPath(Entry->IdleLoop);
	AddPath(Entry->WalkLoop);
	AddPath(Entry->RunLoop);
	AddPath(Entry->SprintLoop);
	AddPath(Entry->WalkStart);
	AddPath(Entry->RunStart);
	AddPath(Entry->WalkStop);
	AddPath(Entry->RunStop);
	AddPath(Entry->SprintStop);
	AddPath(Entry->WalkPivot);
	AddPath(Entry->RunPivot);
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
	// Skip NPC-only entries.
	for (int32 Step = 1; Step <= Roster.Num(); ++Step)
	{
		const FSelenePlayableCharacter& Next = Roster[(Index + Step + Roster.Num()) % Roster.Num()];
		if (Next.bPlayable)
		{
			SelectCharacter(Next.Name);
			return;
		}
	}
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
	// YSOLDE MATERIAL SLOTS: validate before changing the live pawn.
	for (const auto& SlotMaterial : Entry.SlotMaterials) Validate(SlotMaterial.Value);
	// END YSOLDE MATERIAL SLOTS
	Validate(Entry.IdleLoop);
	Validate(Entry.WalkLoop);
	Validate(Entry.RunLoop);
	Validate(Entry.SprintLoop);
	Validate(Entry.WalkStart);
	Validate(Entry.RunStart);
	Validate(Entry.WalkStop);
	Validate(Entry.RunStop);
	Validate(Entry.SprintStop);
	Validate(Entry.WalkPivot);
	Validate(Entry.RunPivot);
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
		// WANDERER MATERIAL SLOTS: preserve named imported slots (e.g. eye cards).
		const TArray<FName> SlotNames = Mesh->GetMaterialSlotNames();
		for (int32 Slot = 0; Slot < Mesh->GetNumMaterials(); ++Slot)
		{
			if (SlotNames.IsValidIndex(Slot) && Entry.KeepMaterialSlots.Contains(SlotNames[Slot])) continue;
			Mesh->SetMaterial(Slot, Material);
		}
		// END WANDERER MATERIAL SLOTS
	}
	// YSOLDE MATERIAL SLOTS: explicit per-slot overrides take precedence.
	for (const auto& SlotMaterial : Entry.SlotMaterials)
	{
		const int32 Slot = Mesh->GetMaterialIndex(SlotMaterial.Key);
		if (Slot != INDEX_NONE && SlotMaterial.Value.Get()) Mesh->SetMaterial(Slot, SlotMaterial.Value.Get());
	}
	// END YSOLDE MATERIAL SLOTS
	ActiveCharacter = Entry;
	ActiveCharacterName = Entry.Name;
	ActiveCharacterLoad = MoveTemp(PendingCharacterLoad);
	if (UClass* AnimClass = Entry.AnimClass.Get())
	{
		Mesh->SetAnimationMode(EAnimationMode::AnimationBlueprint);
		Mesh->SetAnimInstanceClass(AnimClass);
		SetActorTickEnabled(false);
	}
	else
	{
		// All native clip players need DefaultSlot transitions/crossfades; Kawaii chains are optional.
		// ActiveCharacter is already set: the instance reads its chains from GetActiveCharacterEntry().
		Mesh->SetAnimationMode(EAnimationMode::AnimationBlueprint);
		Mesh->SetAnimInstanceClass(USeleneSecondaryAnimInstance::StaticClass());
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
	// AdvancedMovement hook: the slide owns DefaultSlot; base changes otherwise cancel or retime its held pose.
	if (const auto* Advanced = Cast<USeleneMovementComponent>(GetCharacterMovement()); Advanced && (Advanced->IsSliding() || Advanced->IsSlideExitPlaying()))
	{
		PrevSpeed = GetVelocity().Size2D();
		bHadInput = Advanced->GetCurrentAcceleration().SizeSquared2D() > 1.f;
		return;
	}
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
	const float Speed = GetVelocity().Size2D();
	float LoopRate = 1.f;
	const bool bClipLocomotion = !ActiveCharacter.WalkLoop.IsNull() && ActiveCharacter.WalkLoop.Get();
	if (bClipLocomotion && SingleNodePhase == ESingleNodePhase::Ground)
	{
		Animation = ChooseGroundLoop(Speed, LoopRate);
	}
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
	UAnimInstance* AnimInstance = GetMesh()->GetAnimInstance();
	if (Instance->GetAnimationAsset() != Animation)
	{
		UAnimSequence* PreviousLoop = Cast<UAnimSequence>(Instance->GetAnimationAsset());
		const float PreviousTime = Instance->GetCurrentTime();
		const float PreviousRate = Instance->GetPlayRate();
		const bool bLoopToLoop = bClipLocomotion && SingleNodePhase == ESingleNodePhase::Ground && PreviousLoop &&
			(PreviousLoop == ActiveCharacter.IdleLoop.Get() || PreviousLoop == ActiveCharacter.WalkLoop.Get() ||
			 PreviousLoop == ActiveCharacter.RunLoop.Get() || PreviousLoop == ActiveCharacter.SprintLoop.Get());
		// SetAnimationAsset stops slot montages, so switch first, then cross-fade from the old loop on the slot.
		Instance->SetAnimationAsset(Animation, bLoop);
		Instance->SetPosition(0.f, false);
		Instance->SetPlaying(true);
		if (bLoopToLoop && AnimInstance)
		{
			if (UAnimMontage* Fade = AnimInstance->PlaySlotAnimationAsDynamicMontage(PreviousLoop, TEXT("DefaultSlot"),
				0.f, 0.25f, PreviousRate, 1, -1.f, PreviousTime))
			{
				AnimInstance->Montage_Stop(0.25f, Fade);
				UE_LOG(LogSelene, Verbose, TEXT("Loop crossfade %s -> %s slot=DefaultSlot"), *GetNameSafe(PreviousLoop), *GetNameSafe(Animation));
			}
		}
	}
	if (bClipLocomotion && SingleNodePhase == ESingleNodePhase::Ground)
	{
		if (!FMath::IsNearlyEqual(Instance->GetPlayRate(), LoopRate, 0.01f))
		{
			// UAnimSingleNodeInstance::SetPlayRate also retimes an active montage; restore transitions to 1x.
			Instance->SetPlayRate(LoopRate);
			if (AnimInstance)
			{
				if (UAnimMontage* Active = AnimInstance->GetCurrentActiveMontage()) AnimInstance->Montage_SetPlayRate(Active, 1.f);
			}
		}
		UpdateLocomotionTransitions(Speed, DeltaSeconds);
	}
	if (UBlendSpace* Blend = ActiveCharacter.Locomotion.Get(); Blend && Animation == Blend)
	{
		FVector Input = FVector::ZeroVector;
		const FVector Velocity = GetVelocity();
		// Speed is the outer horizontal speed.
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

namespace
{
	TAutoConsoleVariable<int32> CVarAutoWalk(TEXT("selene.AutoWalk"), 0,
		TEXT("Debug: 1 drives the player on a repeating 12 s loop (walk, sprint, sharp stop, turn, jog, jump) for tuning secondary motion."));
	TAutoConsoleVariable<float> CVarAutoShots(TEXT("selene.AutoShots"), 0.f,
		TEXT("Debug: > 0 takes a game screenshot every N seconds to Saved/AutoShots/."));
	TAutoConsoleVariable<int32> CVarAnimMatch(TEXT("selene.AnimMatch"), 0,
		TEXT("Debug: capture idle/walk/run/sprint/stop/pivot/jump from front/side/back on a temporary platform."));
	TAutoConsoleVariable<FString> CVarAnimMatchLabel(TEXT("selene.AnimMatchLabel"), TEXT("before"),
		TEXT("Debug: evidence subfolder under Saved/AnimMatch/Captures/."));
}

UAnimationAsset* ASeleneCharacter::ChooseGroundLoop(float Speed, float& OutPlayRate) const
{
	OutPlayRate = 1.f;
	const FSelenePlayableCharacter& C = ActiveCharacter;
	if (Speed < 20.f && C.IdleLoop.Get()) return C.IdleLoop.Get();
	struct FLoop { UAnimSequence* Clip; float ClipSpeed; };
	// Thresholds sit between the pace speeds (walk 150 / jog 350 / sprint 600).
	const FLoop Loop = Speed < 250.f ? FLoop{C.WalkLoop.Get(), C.WalkLoopSpeed}
		: Speed < 475.f ? FLoop{C.RunLoop.Get() ? C.RunLoop.Get() : C.WalkLoop.Get(), C.RunLoop.Get() ? C.RunLoopSpeed : C.WalkLoopSpeed}
		: FLoop{C.SprintLoop.Get() ? C.SprintLoop.Get() : C.RunLoop.Get(), C.SprintLoop.Get() ? C.SprintLoopSpeed : C.RunLoopSpeed};
	if (!Loop.Clip) return C.WalkLoop.Get();
	// Feet stay planted when the clip plays at the speed the capsule actually moves.
	OutPlayRate = FMath::Clamp(FMath::Max(Speed, 20.f) / FMath::Max(Loop.ClipSpeed, 1.f), 0.5f, 1.5f);
	return Loop.Clip;
}

void ASeleneCharacter::PlayTransition(UAnimSequence* Clip, float BlendIn, float BlendOut)
{
	UAnimInstance* AnimInstance = GetMesh()->GetAnimInstance();
	if (!Clip || !AnimInstance) return;
	UAnimMontage* Montage = AnimInstance->PlaySlotAnimationAsDynamicMontage(Clip, TEXT("DefaultSlot"), BlendIn, BlendOut, 1.f, 1, -1.f, 0.f);
	if (CVarAnimMatch.GetValueOnGameThread() > 0)
	{
		UE_LOG(LogSelene, Log, TEXT("AnimMatch transition hero=%s clip=%s slot=DefaultSlot montage=%s playing=%d"),
			*ActiveCharacterName.ToString(), *GetNameSafe(Clip), *GetNameSafe(Montage), Montage && AnimInstance->Montage_IsPlaying(Montage));
	}
}

void ASeleneCharacter::UpdateLocomotionTransitions(float Speed, float DeltaSeconds)
{
	const UCharacterMovementComponent* Move = GetCharacterMovement();
	const FVector Accel = Move->GetCurrentAcceleration();
	const bool bHasInput = Accel.SizeSquared2D() > 1.f;
	TransitionCooldown = FMath::Max(0.f, TransitionCooldown - DeltaSeconds);
	const FSelenePlayableCharacter& C = ActiveCharacter;
	const bool bFast = MovementPace != ESelenePace::Walk;
	if (bHasInput && !bHadInput && PrevSpeed < 30.f)
	{
		PlayTransition(bFast && C.RunStart.Get() ? C.RunStart.Get() : C.WalkStart.Get(), 0.1f, 0.25f);
		TransitionCooldown = 0.3f;
	}
	else if (!bHasInput && bHadInput && Speed > 100.f)
	{
		UAnimSequence* Stop = Speed > 450.f && C.SprintStop.Get() ? C.SprintStop.Get()
			: Speed > 200.f && C.RunStop.Get() ? C.RunStop.Get() : C.WalkStop.Get();
		PlayTransition(Stop, 0.1f, 0.3f);
		TransitionCooldown = 0.3f;
	}
	else if (bHasInput && !bHadInput)
	{
		// Input came back mid-stop: drop the stop overlay instead of finishing it.
		if (UAnimInstance* AnimInstance = GetMesh()->GetAnimInstance()) AnimInstance->Montage_Stop(0.15f);
	}
	else if (bHasInput && Speed > 120.f && TransitionCooldown <= 0.f)
	{
		const FVector Velocity2D = GetVelocity().GetSafeNormal2D();
		if (FVector::DotProduct(Accel.GetSafeNormal2D(), Velocity2D) < -0.7f)  // input points > ~135 deg away
		{
			PlayTransition(Speed > 250.f && C.RunPivot.Get() ? C.RunPivot.Get() : C.WalkPivot.Get(), 0.1f, 0.25f);
			TransitionCooldown = 0.6f;
		}
	}
	bHadInput = bHasInput;
	PrevSpeed = Speed;
}

void ASeleneCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	UpdateSingleNodeAnimation(DeltaSeconds);
	TickDebugDrivers(DeltaSeconds);
}

void ASeleneCharacter::TickDebugDrivers(float DeltaSeconds)
{
	if (CVarAnimMatch.GetValueOnGameThread() > 0 && IsLocallyControlled())
	{
		TickAnimMatch(DeltaSeconds);
		return;
	}
	DebugTime += DeltaSeconds;
	if (CVarAutoWalk.GetValueOnGameThread() > 0 && IsLocallyControlled())
	{
		// 12 s loop: 0-3 walk, 3-5.5 sprint, 5.5-7 stop, 7-9 jog back (start), 9-10.5 reverse while jogging (pivot),
		// 10.5-10.6 jump, 10.6-12 idle.
		const float T = FMath::Fmod(DebugTime, 12.f);
		const float Heading = T < 7.f ? 0.f : (T < 9.f ? 180.f : 0.f);
		const FVector Dir = FRotator(0.f, AutoWalkBaseYaw + Heading, 0.f).Vector();
		if (T < 3.f) { SetMovementPace(ESelenePace::Walk); AddMovementInput(Dir); }
		else if (T < 5.5f) { SetMovementPace(ESelenePace::Sprint); AddMovementInput(Dir); }
		else if (T < 7.f) {}
		else if (T < 10.5f) { SetMovementPace(ESelenePace::Jog); AddMovementInput(Dir); }
		else if (T < 10.6f) { Jump(); }
		// Unattended captures: stray mouse deltas drift the pitch until the boom sits under the feet.
		// Hold an ordinary over-the-shoulder view; yaw stays free so the camera still follows.
		if (AController* PC = GetController())
		{
			FRotator View = PC->GetControlRotation();
			View.Pitch = -15.f;
			View.Roll = 0.f;
			PC->SetControlRotation(View);
		}
	}
	else
	{
		AutoWalkBaseYaw = GetActorRotation().Yaw;
	}
	const float Interval = CVarAutoShots.GetValueOnGameThread();
	if (Interval > 0.f && DebugTime >= NextAutoShot)
	{
		NextAutoShot = DebugTime + Interval;
		const FString Dir = FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir() / TEXT("AutoShots"));
		IFileManager::Get().MakeDirectory(*Dir, true);
		FScreenshotRequest::RequestScreenshot(Dir / FString::Printf(TEXT("%s_%05.1f.png"), *ActiveCharacterName.ToString(), DebugTime), false, false);
	}
}

void ASeleneCharacter::TickAnimMatch(float DeltaSeconds)
{
	// Wait for async roster loading and shader warmup before the first reference frame.
	if (!PendingCharacterName.IsNone()) return;
	AnimMatchTime += DeltaSeconds;
	if (AnimMatchTime < 0.f || AnimMatchTime >= 42.f) return;
	const int32 ViewIndex = FMath::FloorToInt(AnimMatchTime / 14.f);
	const float T = FMath::Fmod(AnimMatchTime, 14.f);
	if (ViewIndex != AnimMatchView)
	{
		if (AnimMatchView == INDEX_NONE)
		{
			// A runtime-only level fixture removes town obstacles and camera collision from comparisons.
			AnimMatchOrigin = GetActorLocation() + FVector(0.f, 0.f, 3000.f);
			AStaticMeshActor* Floor = GetWorld()->SpawnActor<AStaticMeshActor>();
			Floor->SetMobility(EComponentMobility::Movable);
			Floor->GetStaticMeshComponent()->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")));
			Floor->SetActorLocation(AnimMatchOrigin - FVector(0.f, 0.f, 139.5f));
			Floor->SetActorScale3D(FVector(120.f, 120.f, 1.f));
			Floor->GetStaticMeshComponent()->SetCollisionProfileName(TEXT("BlockAll"));
			SetCameraMode(ESeleneCameraMode::ThirdPerson);
			CameraBoom->TargetArmLength = 450.f;
			CameraBoom->TargetOffset = FVector(0.f, 0.f, 0.f);
			CameraBoom->bEnableCameraLag = false;
			CameraBoom->bDoCollisionTest = false;
		}
		GetCharacterMovement()->StopMovementImmediately();
		SetActorLocationAndRotation(AnimMatchOrigin, FRotator::ZeroRotator, false, nullptr, ETeleportType::TeleportPhysics);
		AnimMatchView = ViewIndex;
		AnimMatchShot = 0;
		bAnimMatchJumped = false;
	}
	const FVector Direction = T >= 10.f && T < 11.f ? -FVector::ForwardVector : FVector::ForwardVector;
	if (T >= 2.f && T < 4.f) { SetMovementPace(ESelenePace::Walk); AddMovementInput(Direction); }
	else if ((T >= 4.f && T < 6.f) || (T >= 9.f && T < 11.f))
	{ SetMovementPace(ESelenePace::Jog); AddMovementInput(Direction); }
	else if (T >= 6.f && T < 8.f) { SetMovementPace(ESelenePace::Sprint); AddMovementInput(Direction); }
	if (T >= 12.f && !bAnimMatchJumped) { Jump(); bAnimMatchJumped = true; }
	if (T >= 12.1f) StopJumping();
	static const float Yaws[] = {180.f, 90.f, 0.f};
	static const TCHAR* Views[] = {TEXT("front"), TEXT("side"), TEXT("back")};
	GetController()->SetControlRotation(FRotator(-10.f, GetActorRotation().Yaw + Yaws[ViewIndex], 0.f));
	const FVector Base = GetActorLocation() - FVector(0.f, 0.f, 83.f);
	const FVector Travel = GetVelocity().SizeSquared2D() > 1.f ? GetVelocity().GetSafeNormal2D() : GetActorForwardVector();
	DrawDebugDirectionalArrow(GetWorld(), Base, Base + Travel * 160.f, 25.f, FColor::Cyan, false, -1.f, 0, 3.f);
	if (UAnimInstance* Anim = GetMesh()->GetAnimInstance())
	{
		if (UAnimMontage* Montage = Anim->GetCurrentActiveMontage())
		{
			UE_LOG(LogSelene, Log, TEXT("AnimMatch slot hero=%s view=%s t=%.3f montage=%s position=%.3f playing=%d"),
				*ActiveCharacterName.ToString(), Views[ViewIndex], T, *GetNameSafe(Montage),
				Anim->Montage_GetPosition(Montage), Anim->Montage_IsPlaying(Montage));
		}
	}
	static const float Times[] = {1.f, 3.f, 5.f, 7.f, 8.12f, 10.12f, 12.25f};
	static const TCHAR* Phases[] = {TEXT("idle"), TEXT("walk"), TEXT("run"), TEXT("sprint"), TEXT("stop"), TEXT("pivot"), TEXT("jump")};
	if (AnimMatchShot < UE_ARRAY_COUNT(Times) && T >= Times[AnimMatchShot])
	{
		const FString Dir = FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir() / TEXT("AnimMatch/Captures")
			/ CVarAnimMatchLabel.GetValueOnGameThread() / ActiveCharacterName.ToString());
		IFileManager::Get().MakeDirectory(*Dir, true);
		const FString Name = FString::Printf(TEXT("%02d_%s_%s.png"), AnimMatchShot, Phases[AnimMatchShot], Views[ViewIndex]);
		FScreenshotRequest::RequestScreenshot(Dir / Name, false, false);
		UE_LOG(LogSelene, Log, TEXT("AnimMatch %s %s t=%.3f actor=%s mesh=%s velocity=%s anim=%s secondaryChains=%d base=%s playRate=%.3f"),
			*ActiveCharacterName.ToString(), *Name, T, *GetActorRotation().ToString(), *GetMesh()->GetRelativeRotation().ToString(),
			*GetVelocity().ToString(), *GetNameSafe(GetMesh()->GetAnimInstance()), ActiveCharacter.SecondaryChains.Num(),
			*GetNameSafe(GetMesh()->GetSingleNodeInstance() ? GetMesh()->GetSingleNodeInstance()->GetAnimationAsset() : nullptr),
			GetMesh()->GetSingleNodeInstance() ? GetMesh()->GetSingleNodeInstance()->GetPlayRate() : 0.f);
		++AnimMatchShot;
	}
}

void ASeleneCharacter::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	++CharacterRequestId;
	if (PendingCharacterLoad) PendingCharacterLoad->CancelHandle();
	PendingCharacterLoad.Reset();
	ActiveCharacterLoad.Reset();
	Super::EndPlay(EndPlayReason);
}
