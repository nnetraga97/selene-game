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
	float Damping = 0.12f;

	UPROPERTY(EditAnywhere, Category = "Secondary")
	float Stiffness = 0.05f;

	/** How much of the character's own movement/rotation the chain ignores (Kawaii default 0.8 = barely reacts). */
	UPROPERTY(EditAnywhere, Category = "Secondary")
	float WorldDampingLocation = 0.35f;

	UPROPERTY(EditAnywhere, Category = "Secondary")
	float WorldDampingRotation = 0.45f;

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

	// WANDERER MATERIAL SLOTS: empty preserves the existing all-slot override behavior.
	/** Named mesh slots that retain their imported material when OverrideMaterial is applied. */
	UPROPERTY(EditAnywhere, Category = "Character")
	TArray<FName> KeepMaterialSlots;
	// END WANDERER MATERIAL SLOTS

	// YSOLDE MATERIAL SLOTS: named overrides applied after the global override.
	UPROPERTY(EditAnywhere, Category = "Character")
	TMap<FName, TSoftObjectPtr<UMaterialInterface>> SlotMaterials;
	// END YSOLDE MATERIAL SLOTS

	/**
	 * Borrowed mocap locomotion (Epic Game Animation Sample clips, retargeted to the hero). When WalkLoop is set it
	 * replaces the Locomotion blend space on the ground: the loop is picked by speed and played at
	 * actual speed / the loop's measured ground speed (no foot sliding); starts, stops and 180-degree
	 * pivots play as short slot overlays. Speeds are cm/s, measured from the retargeted clips.
	 */
	UPROPERTY(EditAnywhere, Category = "Locomotion")
	TSoftObjectPtr<UAnimSequence> IdleLoop;

	UPROPERTY(EditAnywhere, Category = "Locomotion")
	TSoftObjectPtr<UAnimSequence> WalkLoop;

	UPROPERTY(EditAnywhere, Category = "Locomotion")
	TSoftObjectPtr<UAnimSequence> RunLoop;

	UPROPERTY(EditAnywhere, Category = "Locomotion")
	TSoftObjectPtr<UAnimSequence> SprintLoop;

	UPROPERTY(EditAnywhere, Category = "Locomotion")
	float WalkLoopSpeed = 206.f;

	UPROPERTY(EditAnywhere, Category = "Locomotion")
	float RunLoopSpeed = 520.f;

	UPROPERTY(EditAnywhere, Category = "Locomotion")
	float SprintLoopSpeed = 735.f;

	UPROPERTY(EditAnywhere, Category = "Locomotion")
	TSoftObjectPtr<UAnimSequence> WalkStart;

	UPROPERTY(EditAnywhere, Category = "Locomotion")
	TSoftObjectPtr<UAnimSequence> RunStart;

	UPROPERTY(EditAnywhere, Category = "Locomotion")
	TSoftObjectPtr<UAnimSequence> WalkStop;

	UPROPERTY(EditAnywhere, Category = "Locomotion")
	TSoftObjectPtr<UAnimSequence> RunStop;

	UPROPERTY(EditAnywhere, Category = "Locomotion")
	TSoftObjectPtr<UAnimSequence> SprintStop;

	UPROPERTY(EditAnywhere, Category = "Locomotion")
	TSoftObjectPtr<UAnimSequence> WalkPivot;

	UPROPERTY(EditAnywhere, Category = "Locomotion")
	TSoftObjectPtr<UAnimSequence> RunPivot;

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
