#include "Movement/SeleneMovementInput.h"
#include "Movement/SeleneMovementComponent.h"
#include "Components/InputComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"

void FSeleneMovementInput::Bind(UInputComponent& Input, APlayerController& Controller, TFunction<void()> ToggleWalk)
{
	TWeakObjectPtr<APlayerController> WeakController(&Controller);
	auto Add = [&Input](FKey Key, TFunction<void()> Function, EInputEvent Event = IE_Pressed)
	{
		FInputKeyBinding Binding(FInputChord(Key), Event);
		Binding.bConsumeInput = false;
		Binding.KeyDelegate.GetDelegateForManualSet().BindLambda(MoveTemp(Function));
		Input.KeyBindings.Add(MoveTemp(Binding));
	};
	auto Dash = [WeakController]()
	{
		ACharacter* Character = WeakController.IsValid() ? Cast<ACharacter>(WeakController->GetPawn()) : nullptr;
		if (Character) if (auto* Movement = Cast<USeleneMovementComponent>(Character->GetCharacterMovement())) Movement->TryDash();
	};
	// Left Shift dashes on press; the Enhanced Input sprint on the same key keeps running while it's held.
	Add(EKeys::LeftShift, Dash);
	Add(EKeys::Gamepad_LeftShoulder, Dash);
	for (FKey Key : {EKeys::LeftControl, EKeys::Gamepad_FaceButton_Right})
	{
		Add(Key, [WeakController]() { if (ACharacter* C = WeakController.IsValid() ? Cast<ACharacter>(WeakController->GetPawn()) : nullptr) if (auto* M = Cast<USeleneMovementComponent>(C->GetCharacterMovement())) M->TrySlide(); });
		Add(Key, [WeakController]() { if (ACharacter* C = WeakController.IsValid() ? Cast<ACharacter>(WeakController->GetPawn()) : nullptr) if (auto* M = Cast<USeleneMovementComponent>(C->GetCharacterMovement())) M->StopSlide(); }, IE_Released);
	}
	Add(EKeys::Gamepad_FaceButton_Bottom, [WeakController]() { if (USeleneMovementComponent::IsAdvancedMovementEnabled()) if (ACharacter* C = WeakController.IsValid() ? Cast<ACharacter>(WeakController->GetPawn()) : nullptr) { auto* M = Cast<USeleneMovementComponent>(C->GetCharacterMovement()); if (!M || !M->TryAdvancedJump()) C->Jump(); } });
	Add(EKeys::Gamepad_FaceButton_Bottom, [WeakController]() { if (USeleneMovementComponent::IsAdvancedMovementEnabled()) if (ACharacter* C = WeakController.IsValid() ? Cast<ACharacter>(WeakController->GetPawn()) : nullptr) C->StopJumping(); }, IE_Released);
	Add(EKeys::CapsLock, [ToggleWalk]() { if (USeleneMovementComponent::IsAdvancedMovementEnabled()) ToggleWalk(); });
}
