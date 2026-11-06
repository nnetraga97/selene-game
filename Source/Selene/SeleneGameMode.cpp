#include "SeleneGameMode.h"

#include "SeleneCharacter.h"
#include "SelenePlayerController.h"

ASeleneGameMode::ASeleneGameMode()
{
	DefaultPawnClass = ASeleneCharacter::StaticClass();
	PlayerControllerClass = ASelenePlayerController::StaticClass();
}
