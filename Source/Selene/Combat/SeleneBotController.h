#pragma once

#include "CoreMinimal.h"
#include "AIController.h"
#include "Combat/SeleneCombat.h"
#include "SeleneBotController.generated.h"

class ASeleneCharacter;

/**
 * A lane-pushing bot hero: walks its lane just behind its own troopers, fights the nearest threat (heroes first
 * when close), keeps its weapon's range, uses abilities when they would land, and walks home to heal when hurt.
 * Movement and aim go through the same ASeleneCharacter calls the player uses.
 */
UCLASS()
class SELENE_API ASeleneBotController : public AAIController
{
	GENERATED_BODY()

public:
	ASeleneBotController();
	virtual void Tick(float DeltaSeconds) override;

	/** Lane index in ASeleneLaneDirector::Lanes. */
	int32 Lane = 1;

	/** Spawns the bots listed in selene.Bots on a lane map. */
	static void SpawnBots(UWorld* World);

private:
	FSeleneTarget PickTarget(const ASeleneCharacter& Hero) const;
	FVector LaneGoal(const ASeleneCharacter& Hero) const;
	float StrafePhase = 0.f;
	float ThinkTimer = 0.f;
	float AbilityTimer = 0.f;
	bool bRetreating = false;
	float LastHealth = 0.f;
	FSeleneTarget Target;
};
