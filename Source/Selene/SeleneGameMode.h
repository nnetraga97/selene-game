#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "SeleneGameMode.generated.h"

UCLASS()
class SELENE_API ASeleneGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ASeleneGameMode();
	virtual void StartPlay() override;

private:
	/** Spawns the configured idle NPCs (USeleneCharacterSettings::Npcs) around the first PlayerStart. */
	void SpawnNpcs();
};
