#include "SelenePlayerController.h"

#include "Selene.h"
#include "SeleneCharacter.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "InputAction.h"
#include "InputActionValue.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"

void ASelenePlayerController::CreateRuntimeInput()
{
	if (RuntimeMappingContext)
	{
		return;
	}
	RuntimeMappingContext = NewObject<UInputMappingContext>(this, TEXT("SeleneRuntimeInput"), RF_Transient);
	auto MakeAction = [this](const TCHAR* Name, EInputActionValueType Type)
	{
		UInputAction* Action = NewObject<UInputAction>(this, Name, RF_Transient);
		Action->ValueType = Type;
		return Action;
	};
	MoveAction = MakeAction(TEXT("Move"), EInputActionValueType::Axis2D);
	// Summing makes opposite keyboard directions cancel instead of selecting one key.
	MoveAction->AccumulationBehavior = EInputActionAccumulationBehavior::Cumulative;
	LookAction = MakeAction(TEXT("Look"), EInputActionValueType::Axis2D);
	JumpAction = MakeAction(TEXT("Jump"), EInputActionValueType::Boolean);
	SprintAction = MakeAction(TEXT("Sprint"), EInputActionValueType::Boolean);
	WalkAction = MakeAction(TEXT("WalkToggle"), EInputActionValueType::Boolean);
	CharacterAction = MakeAction(TEXT("CharacterCycle"), EInputActionValueType::Boolean);
	CameraAction = MakeAction(TEXT("CameraToggle"), EInputActionValueType::Boolean);

	auto MapMovementKey = [this](FKey Key, bool bNegate, bool bSwizzle)
	{
		FEnhancedActionKeyMapping& Mapping = RuntimeMappingContext->MapKey(MoveAction, Key);
		if (bNegate)
		{
			Mapping.Modifiers.Add(NewObject<UInputModifierNegate>(RuntimeMappingContext));
		}
		if (bSwizzle)
		{
			UInputModifierSwizzleAxis* Swizzle = NewObject<UInputModifierSwizzleAxis>(RuntimeMappingContext);
			Swizzle->Order = EInputAxisSwizzle::YXZ;
			Mapping.Modifiers.Add(Swizzle);
		}
	};
	MapMovementKey(EKeys::W, false, true);
	MapMovementKey(EKeys::S, true, true);
	MapMovementKey(EKeys::A, true, false);
	MapMovementKey(EKeys::D, false, false);
	FEnhancedActionKeyMapping& StickMove = RuntimeMappingContext->MapKey(MoveAction, EKeys::Gamepad_Left2D);
	StickMove.Modifiers.Add(NewObject<UInputModifierDeadZone>(RuntimeMappingContext));

	FEnhancedActionKeyMapping& MouseLook = RuntimeMappingContext->MapKey(LookAction, EKeys::Mouse2D);
	UInputModifierNegate* MousePitch = NewObject<UInputModifierNegate>(RuntimeMappingContext);
	MousePitch->bX = false;
	MousePitch->bY = true;
	MousePitch->bZ = false;
	MouseLook.Modifiers.Add(MousePitch);

	FEnhancedActionKeyMapping& StickLook = RuntimeMappingContext->MapKey(LookAction, EKeys::Gamepad_Right2D);
	StickLook.Modifiers.Add(NewObject<UInputModifierDeadZone>(RuntimeMappingContext));
	UInputModifierScalar* LookRate = NewObject<UInputModifierScalar>(RuntimeMappingContext);
	LookRate->Scalar = FVector(90.f, -90.f, 1.f);
	StickLook.Modifiers.Add(LookRate);
	// Mouse is a per-frame delta; only stick input needs degrees/second scaling.
	StickLook.Modifiers.Add(NewObject<UInputModifierScaleByDeltaTime>(RuntimeMappingContext));

	RuntimeMappingContext->MapKey(JumpAction, EKeys::SpaceBar);
	RuntimeMappingContext->MapKey(SprintAction, EKeys::LeftShift);
	RuntimeMappingContext->MapKey(WalkAction, EKeys::LeftControl);
	RuntimeMappingContext->MapKey(CameraAction, EKeys::V);
	RuntimeMappingContext->MapKey(CharacterAction, EKeys::C);
}

void ASelenePlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();
	CreateRuntimeInput();
	UEnhancedInputComponent* EnhancedInput = Cast<UEnhancedInputComponent>(InputComponent);
	if (!EnhancedInput)
	{
		UE_LOG(LogSelene, Error, TEXT("Selene requires EnhancedInputComponent in the input settings."));
		return;
	}
	EnhancedInput->BindAction(MoveAction, ETriggerEvent::Triggered, this, &ASelenePlayerController::Move);
	EnhancedInput->BindAction(LookAction, ETriggerEvent::Triggered, this, &ASelenePlayerController::Look);
	EnhancedInput->BindAction(JumpAction, ETriggerEvent::Started, this, &ASelenePlayerController::StartJump);
	EnhancedInput->BindAction(JumpAction, ETriggerEvent::Completed, this, &ASelenePlayerController::EndJump);
	EnhancedInput->BindAction(JumpAction, ETriggerEvent::Canceled, this, &ASelenePlayerController::EndJump);
	EnhancedInput->BindAction(SprintAction, ETriggerEvent::Started, this, &ASelenePlayerController::StartSprint);
	EnhancedInput->BindAction(SprintAction, ETriggerEvent::Completed, this, &ASelenePlayerController::EndSprint);
	EnhancedInput->BindAction(SprintAction, ETriggerEvent::Canceled, this, &ASelenePlayerController::EndSprint);
	EnhancedInput->BindAction(WalkAction, ETriggerEvent::Started, this, &ASelenePlayerController::ToggleWalk);
	EnhancedInput->BindAction(CharacterAction, ETriggerEvent::Started, this, &ASelenePlayerController::CycleCharacter);
	EnhancedInput->BindAction(CameraAction, ETriggerEvent::Started, this, &ASelenePlayerController::ToggleCamera);
	AddRuntimeMappingContext();
}

void ASelenePlayerController::AddRuntimeMappingContext()
{
	if (IsLocalPlayerController())
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem =
			ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
		{
			CreateRuntimeInput();
			if (!Subsystem->HasMappingContext(RuntimeMappingContext))
			{
				Subsystem->AddMappingContext(RuntimeMappingContext, 0);
			}
		}
	}
}

void ASelenePlayerController::BeginPlay()
{
	Super::BeginPlay();
	AddRuntimeMappingContext();
}

void ASelenePlayerController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);
	AddRuntimeMappingContext();
	ApplyMovementPace();
}

void ASelenePlayerController::AcknowledgePossession(APawn* InPawn)
{
	Super::AcknowledgePossession(InPawn);
	AddRuntimeMappingContext();
	ApplyMovementPace();
}

void ASelenePlayerController::ReceivedPlayer()
{
	Super::ReceivedPlayer();
	AddRuntimeMappingContext();
}

void ASelenePlayerController::OnUnPossess()
{
	EndJump();
	bSprintHeld = false;
	bWalkToggled = false;
	ApplyMovementPace();
	Super::OnUnPossess();
}

void ASelenePlayerController::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UEnhancedInputLocalPlayerSubsystem* Subsystem =
		ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))
	{
		if (RuntimeMappingContext)
		{
			Subsystem->RemoveMappingContext(RuntimeMappingContext);
		}
	}
	Super::EndPlay(EndPlayReason);
}

void ASelenePlayerController::Move(const FInputActionValue& Value)
{
	if (ASeleneCharacter* Character = Cast<ASeleneCharacter>(GetPawn()))
	{
		const FVector2D Axis = Value.Get<FVector2D>().GetClampedToMaxSize(1.f);
		const FRotationMatrix YawMatrix(FRotator(0.f, GetControlRotation().Yaw, 0.f));
		Character->AddMovementInput(YawMatrix.GetUnitAxis(EAxis::X), Axis.Y);
		Character->AddMovementInput(YawMatrix.GetUnitAxis(EAxis::Y), Axis.X);
	}
}

void ASelenePlayerController::Look(const FInputActionValue& Value)
{
	if (Cast<ASeleneCharacter>(GetPawn()))
	{
		const FVector2D Axis = Value.Get<FVector2D>();
		AddYawInput(Axis.X);
		AddPitchInput(Axis.Y);
	}
}

void ASelenePlayerController::StartJump()
{
	if (ASeleneCharacter* Character = Cast<ASeleneCharacter>(GetPawn()))
	{
		Character->Jump();
	}
}

void ASelenePlayerController::EndJump()
{
	if (ASeleneCharacter* Character = Cast<ASeleneCharacter>(GetPawn()))
	{
		Character->StopJumping();
	}
}

void ASelenePlayerController::StartSprint()
{
	bSprintHeld = true;
	ApplyMovementPace();
}

void ASelenePlayerController::EndSprint()
{
	bSprintHeld = false;
	ApplyMovementPace();
}

void ASelenePlayerController::ToggleWalk()
{
	bWalkToggled = !bWalkToggled;
	ApplyMovementPace();
}

void ASelenePlayerController::ApplyMovementPace()
{
	if (ASeleneCharacter* Character = Cast<ASeleneCharacter>(GetPawn()))
	{
		Character->SetMovementPace(bSprintHeld ? ESelenePace::Sprint
			: (bWalkToggled ? ESelenePace::Walk : ESelenePace::Jog));
	}
}

void ASelenePlayerController::ToggleCamera()
{
	if (ASeleneCharacter* Character = Cast<ASeleneCharacter>(GetPawn()))
	{
		Character->ToggleCameraMode();
	}
}

void ASelenePlayerController::CycleCharacter()
{
	if (ASeleneCharacter* Character = Cast<ASeleneCharacter>(GetPawn()))
	{
		Character->CycleCharacter();
	}
}
