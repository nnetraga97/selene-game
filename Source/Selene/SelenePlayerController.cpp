#include "SelenePlayerController.h"

// AdvancedMovement hooks: ability implementation and additional bindings live in Movement/.
#include "Movement/SeleneMovementComponent.h"
#include "Movement/SeleneMovementInput.h"

#include "Selene.h"
#include "SSelenePauseMenu.h"
#include "UI/SSeleneFpsCounter.h"
#include "UI/SSeleneMapView.h"
#include "UI/SSeleneHeroPicker.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Perf/SelenePerfRouteSubsystem.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "HAL/IConsoleManager.h"
#include "SeleneCharacter.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "InputAction.h"
#include "InputActionValue.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"

namespace
{
	TAutoConsoleVariable<int32> CVarShowFps(
		TEXT("selene.ShowFPS"), 1, TEXT("Show the frame-rate counter at startup (F toggles it in game)."), ECVF_Default);

	ASelenePlayerController* FindLocalSeleneController(UWorld* World)
	{
		if (!World) return nullptr;
		for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
		{
			ASelenePlayerController* PC = Cast<ASelenePlayerController>(It->Get());
			if (PC && PC->IsLocalPlayerController()) return PC;
		}
		return nullptr;
	}

	FAutoConsoleCommandWithWorldAndArgs MapCommand(
		TEXT("selene.Map"), TEXT("Toggle the top-down map (M)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>&, UWorld* World)
		{
			if (ASelenePlayerController* PC = FindLocalSeleneController(World)) PC->ToggleMap();
		}), ECVF_Default);

	FAutoConsoleCommandWithWorldAndArgs FpsCommand(
		TEXT("selene.FPS"), TEXT("Toggle the frame-rate counter (F)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>&, UWorld* World)
		{
			if (ASelenePlayerController* PC = FindLocalSeleneController(World)) PC->ToggleFpsCounter();
		}), ECVF_Default);

	FAutoConsoleCommandWithWorldAndArgs MenuCommand(
		TEXT("selene.Menu"), TEXT("Toggle the local pause menu."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (!World) return;
			for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
			{
				ASelenePlayerController* PC = Cast<ASelenePlayerController>(It->Get());
				if (PC && PC->IsLocalPlayerController())
				{
					PC->TogglePauseMenu();
					return;
				}
			}
		}), ECVF_Default);
}

void ASelenePlayerController::TogglePauseMenu()
{
	if (PauseMenu.IsValid())
	{
		ClosePauseMenu();
		return;
	}
	// The subsystem is created only for PerfRoute processes; block even during warmup/startup.
	if (!IsLocalPlayerController() || !GetWorld() ||
		GetWorld()->GetSubsystem<USelenePerfRouteSubsystem>() || IsPaused()) return;
	UGameViewportClient* Viewport = GetWorld()->GetGameViewport();
	if (!Viewport || !SetPause(true)) return;

	CloseHeroPicker();
	EndJump();
	EndSprint();
	FlushPressedKeys();
	SAssignNew(PauseMenu, SSelenePauseMenu).Controller(this);
	Viewport->AddViewportWidgetContent(PauseMenu.ToSharedRef(), 100);
	bShowMouseCursor = true;
	FInputModeUIOnly Mode;
	Mode.SetWidgetToFocus(PauseMenu);
	Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
	SetInputMode(Mode);
}

void ASelenePlayerController::ClosePauseMenu()
{
	if (!PauseMenu.IsValid()) return;
	if (!SetPause(false)) return;
	if (GetWorld() && GetWorld()->GetGameViewport())
		GetWorld()->GetGameViewport()->RemoveViewportWidgetContent(PauseMenu.ToSharedRef());
	PauseMenu.Reset();
	bShowMouseCursor = false;
	SetInputMode(FInputModeGameOnly());
}

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
	MenuAction = MakeAction(TEXT("MenuToggle"), EInputActionValueType::Boolean);
	MenuAction->bTriggerWhenPaused = true;
	RuntimeMappingContext->MapKey(MenuAction, EKeys::Escape);
	RuntimeMappingContext->MapKey(MenuAction, EKeys::Gamepad_Special_Right);
	CameraAction = MakeAction(TEXT("CameraToggle"), EInputActionValueType::Boolean);
	MapAction = MakeAction(TEXT("MapToggle"), EInputActionValueType::Boolean);
	MapZoomAction = MakeAction(TEXT("MapZoom"), EInputActionValueType::Axis1D);
	FpsAction = MakeAction(TEXT("FpsToggle"), EInputActionValueType::Boolean);
	RuntimeMappingContext->MapKey(MapAction, EKeys::M);
	RuntimeMappingContext->MapKey(FpsAction, EKeys::F);
	RuntimeMappingContext->MapKey(MapZoomAction, EKeys::MouseWheelAxis);
	RuntimeMappingContext->MapKey(MapZoomAction, EKeys::Equals);
	RuntimeMappingContext->MapKey(MapZoomAction, EKeys::Add);
	RuntimeMappingContext->MapKey(MapZoomAction, EKeys::Hyphen).Modifiers.Add(NewObject<UInputModifierNegate>(RuntimeMappingContext));
	RuntimeMappingContext->MapKey(MapZoomAction, EKeys::Subtract).Modifiers.Add(NewObject<UInputModifierNegate>(RuntimeMappingContext));

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
	// C opens the hero picker (numbered list); `selene.Character next` still cycles.
	EnhancedInput->BindAction(CharacterAction, ETriggerEvent::Started, this, &ASelenePlayerController::ToggleHeroPicker);
	EnhancedInput->BindAction(CameraAction, ETriggerEvent::Started, this, &ASelenePlayerController::ToggleCamera);
	EnhancedInput->BindAction(MenuAction, ETriggerEvent::Started, this, &ASelenePlayerController::TogglePauseMenu);
	EnhancedInput->BindAction(MapAction, ETriggerEvent::Started, this, &ASelenePlayerController::ToggleMap);
	EnhancedInput->BindAction(MapZoomAction, ETriggerEvent::Started, this, &ASelenePlayerController::ZoomMap);
	EnhancedInput->BindAction(FpsAction, ETriggerEvent::Started, this, &ASelenePlayerController::ToggleFpsCounter);
	// AdvancedMovement hook: gated keys remain inert when the feature is off.
	FSeleneMovementInput::Bind(*EnhancedInput, *this, [this]() { bWalkToggled = !bWalkToggled; ApplyMovementPace(); });
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
	if (CVarShowFps.GetValueOnGameThread() != 0 && !FpsCounter.IsValid())
	{
		ToggleFpsCounter();
	}
}

bool ASelenePlayerController::IsCaptureRun() const
{
	// PerfRoute processes keep the screen clean.
	return GetWorld() && GetWorld()->GetSubsystem<USelenePerfRouteSubsystem>();
}

void ASelenePlayerController::ToggleFpsCounter()
{
	UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr;
	if (FpsCounter.IsValid())
	{
		if (Viewport) Viewport->RemoveViewportWidgetContent(FpsCounter.ToSharedRef());
		FpsCounter.Reset();
		return;
	}
	if (!IsLocalPlayerController() || !Viewport || IsCaptureRun()) return;
	SAssignNew(FpsCounter, SSeleneFpsCounter);
	Viewport->AddViewportWidgetContent(FpsCounter.ToSharedRef(), 40);
}

void ASelenePlayerController::ToggleHeroPicker()
{
	if (HeroPicker.IsValid())
	{
		CloseHeroPicker();
		return;
	}
	UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr;
	if (!IsLocalPlayerController() || !Viewport || !GetPawn() || IsPaused() || IsCaptureRun()) return;
	CloseMap();
	EndSprint();
	FlushPressedKeys();
	SAssignNew(HeroPicker, SSeleneHeroPicker).Controller(this);
	Viewport->AddViewportWidgetContent(HeroPicker.ToSharedRef(), 60);
	bShowMouseCursor = true;
	// Game keeps running; the picker takes keyboard focus so number keys reach it.
	FInputModeGameAndUI Mode;
	Mode.SetWidgetToFocus(HeroPicker);
	Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
	Mode.SetHideCursorDuringCapture(false);
	SetInputMode(Mode);
}

void ASelenePlayerController::CloseHeroPicker()
{
	if (!HeroPicker.IsValid()) return;
	if (GetWorld() && GetWorld()->GetGameViewport())
		GetWorld()->GetGameViewport()->RemoveViewportWidgetContent(HeroPicker.ToSharedRef());
	HeroPicker.Reset();
	bShowMouseCursor = false;
	SetInputMode(FInputModeGameOnly());
}

void ASelenePlayerController::ToggleMap()
{
	if (MapView.IsValid())
	{
		CloseMap();
		return;
	}
	UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr;
	if (!IsLocalPlayerController() || !Viewport || !GetPawn() || IsPaused() || IsCaptureRun()) return;
	CaptureMap();
	if (!MapTarget) return;
	SAssignNew(MapView, SSeleneMapView).Controller(this).Target(MapTarget.Get());
	Viewport->AddViewportWidgetContent(MapView.ToSharedRef(), 50);
}

void ASelenePlayerController::CloseMap()
{
	if (!MapView.IsValid()) return;
	if (GetWorld() && GetWorld()->GetGameViewport())
		GetWorld()->GetGameViewport()->RemoveViewportWidgetContent(MapView.ToSharedRef());
	MapView.Reset();
}

void ASelenePlayerController::ZoomMap(const FInputActionValue& Value)
{
	const float Direction = Value.Get<float>();
	if (!MapView.IsValid() || FMath::IsNearlyZero(Direction)) return;
	MapWidthCm = FMath::Clamp(MapWidthCm * (Direction > 0.f ? 0.8f : 1.25f), 8000.f, 300000.f);
	CaptureMap();
}

void ASelenePlayerController::CaptureMap()
{
	APawn* MapPawn = GetPawn();
	if (!MapPawn || !GetWorld()) return;
	if (!MapTarget)
	{
		MapTarget = NewObject<UTextureRenderTarget2D>(this, TEXT("SeleneMapTarget"), RF_Transient);
		MapTarget->RenderTargetFormat = RTF_RGBA8;
		MapTarget->ClearColor = FLinearColor(0.02f, 0.05f, 0.08f, 1.f);
		MapTarget->InitAutoFormat(1536, 1536);
		MapTarget->UpdateResourceImmediate(true);
	}
	if (!MapCapture)
	{
		MapCapture = NewObject<USceneCaptureComponent2D>(this, TEXT("SeleneMapCapture"), RF_Transient);
		MapCapture->bCaptureEveryFrame = false;
		MapCapture->bCaptureOnMovement = false;
		// Without a persistent view state the capture can't run eye adaptation and renders the sunlit town
		// at a fixed exposure (pure white). Keeping the state lets it auto-expose like the game camera.
		MapCapture->bAlwaysPersistRenderingState = true;
		MapCapture->ProjectionType = ECameraProjectionMode::Orthographic;
		MapCapture->bAutoCalculateOrthoPlanes = false;
		MapCapture->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
		MapCapture->TextureTarget = MapTarget;
		MapCapture->ShowFlags.SetFog(false);
		MapCapture->ShowFlags.SetVolumetricFog(false);
		MapCapture->ShowFlags.SetMotionBlur(false);
		MapCapture->RegisterComponentWithWorld(GetWorld());
	}
	// Straight down with yaw 0, so the image's up is world +X (SSeleneMapView relies on this).
	MapCenter = MapPawn->GetActorLocation();
	MapCapture->OrthoWidth = MapWidthCm;
	MapCapture->HiddenActors = { MapPawn };
	MapCapture->SetWorldLocationAndRotation(MapCenter + FVector(0.f, 0.f, 60000.f), FRotator(-90.f, 0.f, 0.f));
	MapCapture->CaptureScene();
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
	if (PauseMenu.IsValid())
	{
		if (GetWorld() && GetWorld()->GetGameViewport())
			GetWorld()->GetGameViewport()->RemoveViewportWidgetContent(PauseMenu.ToSharedRef());
		PauseMenu.Reset();
	}
	CloseMap();
	if (HeroPicker.IsValid() && GetWorld() && GetWorld()->GetGameViewport())
		GetWorld()->GetGameViewport()->RemoveViewportWidgetContent(HeroPicker.ToSharedRef());
	HeroPicker.Reset();
	if (FpsCounter.IsValid())
	{
		if (GetWorld() && GetWorld()->GetGameViewport())
			GetWorld()->GetGameViewport()->RemoveViewportWidgetContent(FpsCounter.ToSharedRef());
		FpsCounter.Reset();
	}
	if (MapCapture)
	{
		MapCapture->DestroyComponent();
		MapCapture = nullptr;
	}
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
		// AdvancedMovement hook: a ground dash can become a momentum-carrying jump.
		if (auto* Movement = Cast<USeleneMovementComponent>(Character->GetCharacterMovement()))
			if (Movement->TryAdvancedJump()) return;
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
	// AdvancedMovement hook: Ctrl is reserved for slide; CapsLock invokes the new walk binding.
	if (USeleneMovementComponent::IsAdvancedMovementEnabled()) return;
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
