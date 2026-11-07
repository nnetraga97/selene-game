#include "SeleneGameMode.h"

#include "Selene.h"
#include "SeleneCharacter.h"
#include "SeleneCharacterSettings.h"
#include "SelenePlayerController.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerStart.h"

ASeleneGameMode::ASeleneGameMode()
{
	DefaultPawnClass = ASeleneCharacter::StaticClass();
	PlayerControllerClass = ASelenePlayerController::StaticClass();
}

void ASeleneGameMode::StartPlay()
{
	Super::StartPlay();
	SpawnNpcs();
}

void ASeleneGameMode::SpawnNpcs()
{
	UWorld* World = GetWorld();
	const TArray<FSeleneNpcSpawn>& Npcs = GetDefault<USeleneCharacterSettings>()->Npcs;
	if (!World || Npcs.IsEmpty()) return;
	TActorIterator<APlayerStart> Start(World);
	if (!Start)
	{
		UE_LOG(LogSelene, Warning, TEXT("Selene NPCs: no PlayerStart in this map; none spawned."));
		return;
	}
	const FTransform Anchor(FRotator(0.f, Start->GetActorRotation().Yaw, 0.f), Start->GetActorLocation());
	for (const FSeleneNpcSpawn& Npc : Npcs)
	{
		FVector Location = Anchor.TransformPosition(Npc.Offset);
		FHitResult Hit;
		FCollisionQueryParams Params(SCENE_QUERY_STAT(SeleneNpcGround), false);
		if (World->LineTraceSingleByChannel(Hit, Location + FVector(0, 0, 300), Location - FVector(0, 0, 1000), ECC_Visibility, Params))
		{
			Location = Hit.ImpactPoint;
		}
		const FTransform Transform(FRotator(0.f, Anchor.Rotator().Yaw + Npc.Yaw, 0.f), Location);
		ASeleneCharacter* Character = World->SpawnActorDeferred<ASeleneCharacter>(ASeleneCharacter::StaticClass(), Transform,
			nullptr, nullptr, ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn);
		if (!Character) continue;
		Character->AutoPossessPlayer = EAutoReceiveInput::Disabled;
		Character->AutoPossessAI = EAutoPossessAI::Disabled;
		Character->SetNpcCharacter(Npc.Character);
		FTransform Final = Transform;
		Final.AddToTranslation(FVector(0, 0, Character->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()));
		Character->FinishSpawning(Final);
		UE_LOG(LogSelene, Log, TEXT("Selene NPC '%s' spawned at %s."), *Npc.Character.ToString(), *Final.GetLocation().ToString());
	}
}
