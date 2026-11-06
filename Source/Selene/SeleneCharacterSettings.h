#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "SeleneCharacterSettings.generated.h"

class USkeletalMesh;
class UAnimInstance;
class UBlendSpace;
class UAnimSequence;
class UMaterialInterface;

USTRUCT(BlueprintType)
struct SELENE_API FSelenePlayableCharacter
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, Category = "Character")
	FName Name;

	UPROPERTY(EditAnywhere, Category = "Character")
	TSoftObjectPtr<USkeletalMesh> Mesh;

	UPROPERTY(EditAnywhere, Category = "Animation")
	TSoftClassPtr<UAnimInstance> AnimClass;

	UPROPERTY(EditAnywhere, Category = "Animation")
	TSoftObjectPtr<UBlendSpace> Locomotion;

	UPROPERTY(EditAnywhere, Category = "Animation")
	TSoftObjectPtr<UAnimSequence> FallLoop;

	UPROPERTY(EditAnywhere, Category = "Animation")
	TSoftObjectPtr<UAnimSequence> Jump;

	UPROPERTY(EditAnywhere, Category = "Animation")
	TSoftObjectPtr<UAnimSequence> Land;

	UPROPERTY(EditAnywhere, Category = "Character")
	TSoftObjectPtr<UMaterialInterface> OverrideMaterial;

	/** Centimeters above the capsule's feet, independent of skeleton bone names. */
	UPROPERTY(EditAnywhere, Category = "Camera", meta = (ClampMin = "0"))
	float EyeHeight = 151.5f;

	UPROPERTY(EditAnywhere, Category = "Camera", meta = (ClampMin = "0"))
	float BoomLength = 350.f;

	/** Default matches ASeleneCharacter's capsule half height. */
	UPROPERTY(EditAnywhere, Category = "Character")
	FVector MeshOffset = FVector(0.f, 0.f, -87.5f);

	UPROPERTY(EditAnywhere, Category = "Character")
	FRotator MeshRotation = FRotator(0.f, -90.f, 0.f);
};

UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Selene Characters"))
class SELENE_API USeleneCharacterSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UPROPERTY(Config, EditAnywhere, Category = "Characters")
	TArray<FSelenePlayableCharacter> Roster;

	UPROPERTY(Config, EditAnywhere, Category = "Characters")
	FName DefaultCharacter = TEXT("Champion");
};
