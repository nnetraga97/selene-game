#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "SeleneCharacterSettings.generated.h"

class USkeletalMesh;
class UAnimInstance;
class UBlendSpace;
class UAnimSequence;
class UMaterialInterface;

/** One Kawaii Physics chain: RootBone and every bone below it sway (hair, braid, skirt panel, wing). */
USTRUCT(BlueprintType)
struct SELENE_API FSeleneSecondaryChain
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, Category = "Secondary")
	FName RootBone;

	/** Kawaii PhysicsSettings: Damping 0..1 (higher = calmer), Stiffness 0..1 (higher = returns to pose faster). */
	UPROPERTY(EditAnywhere, Category = "Secondary")
	float Damping = 0.3f;

	UPROPERTY(EditAnywhere, Category = "Secondary")
	float Stiffness = 0.25f;

	/** Bone collision radius in cm. */
	UPROPERTY(EditAnywhere, Category = "Secondary")
	float Radius = 1.f;

	/** Max swing from the animated pose in degrees (0 = unlimited). */
	UPROPERTY(EditAnywhere, Category = "Secondary")
	float LimitAngle = 0.f;

	/** Gravity in cm/s^2 (Z). Kawaii defaults to none; cloth reads better with some. */
	UPROPERTY(EditAnywhere, Category = "Secondary")
	float GravityZ = -490.f;
};

/** Body collider for secondary chains: a capsule from Bone to ChildBone, or a sphere at Bone when ChildBone is None. */
USTRUCT(BlueprintType)
struct SELENE_API FSeleneSecondaryCollider
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, Category = "Secondary")
	FName Bone;

	UPROPERTY(EditAnywhere, Category = "Secondary")
	FName ChildBone;

	/** cm */
	UPROPERTY(EditAnywhere, Category = "Secondary")
	float Radius = 8.f;
};

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

	/** Kawaii Physics secondary motion (requires single-node locomotion, i.e. no AnimClass). */
	UPROPERTY(EditAnywhere, Category = "Secondary")
	TArray<FSeleneSecondaryChain> SecondaryChains;

	/** Colliders shared by every secondary chain of this character. */
	UPROPERTY(EditAnywhere, Category = "Secondary")
	TArray<FSeleneSecondaryCollider> SecondaryColliders;

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
