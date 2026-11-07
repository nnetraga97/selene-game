#pragma once
#include "CoreMinimal.h"
class UInputComponent;
class APlayerController;

/** Asset-free extra bindings. Existing Enhanced Input actions retain their original ownership. */
struct FSeleneMovementInput
{
	static void Bind(UInputComponent& Input, APlayerController& Controller, TFunction<void()> ToggleWalk);
};
