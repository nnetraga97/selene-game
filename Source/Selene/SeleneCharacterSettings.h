#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "SeleneCharacterSettings.generated.h"

class USkeletalMesh;
class UAnimInstance;
class UBlendSpace;
class UAnimSequence;
class UMaterialInterface;

UENUM(BlueprintType)
enum class ESeleneWeapon : uint8
{
	Melee,
	Bow
};

/** What an ability does when its cast point is reached (implemented in SeleneCharacterCombat.cpp). */
UENUM(BlueprintType)
enum class ESeleneAbilityEffect : uint8
{
	None,
	DashStrike,    // charge along the aim, hitting everything in the path
	Nova,          // burst round the hero: damage + slow
	LeapSlam,      // leap to the aimed ground point, damage + stun on landing
	ArrowRain,     // pulses of damage + slow on the aimed ground point
	PiercingShot,  // fast arrow through every enemy on the line
	Overdrive,     // buff: faster, stronger primary fire
	Guard          // buff: damage reduction, knock nearby enemies back
};

/** One hero ability (Q / E / R in roster order). Times are seconds from the press. */
USTRUCT(BlueprintType)
struct SELENE_API FSeleneAbility
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, Category = "Ability") FName Name;
	UPROPERTY(EditAnywhere, Category = "Ability") ESeleneAbilityEffect Effect = ESeleneAbilityEffect::None;
	UPROPERTY(EditAnywhere, Category = "Ability") TSoftObjectPtr<UAnimSequence> Clip;
	UPROPERTY(EditAnywhere, Category = "Ability") float PlayRate = 1.f;
	UPROPERTY(EditAnywhere, Category = "Ability") float Cooldown = 8.f;
	/** When the effect lands, seconds after the press (cast point). */
	UPROPERTY(EditAnywhere, Category = "Ability") float CastTime = 0.3f;
	UPROPERTY(EditAnywhere, Category = "Ability") float Damage = 150.f;
	/** cm */
	UPROPERTY(EditAnywhere, Category = "Ability") float Radius = 400.f;
	/** cm */
	UPROPERTY(EditAnywhere, Category = "Ability") float Range = 1200.f;
	/** Buff / slow / stun length in seconds. */
	UPROPERTY(EditAnywhere, Category = "Ability") float Duration = 2.f;
	/** Nova only: also stun everything hit for this long (0 = slow only). */
	UPROPERTY(EditAnywhere, Category = "Ability") float StunSeconds = 0.f;
	/** Plays on the whole body (true) or only above the spine while the legs keep moving (false). */
	UPROPERTY(EditAnywhere, Category = "Ability") bool bFullBody = true;
	/** Cascade particle systems: one at the hero on cast, one where the effect lands. */
	UPROPERTY(EditAnywhere, Category = "Ability") FSoftObjectPath CastFx;
	UPROPERTY(EditAnywhere, Category = "Ability") FSoftObjectPath ImpactFx;
	UPROPERTY(EditAnywhere, Category = "Ability") float FxScale = 1.f;
};

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

	/** False keeps the entry out of the hero picker and C-cycling; NPC spawns can still use it. */
	UPROPERTY(EditAnywhere, Category = "Character")
	bool bPlayable = true;

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

	/** Optional in-place slide phases, played on DefaultSlot by the movement component. */
	UPROPERTY(EditAnywhere, Category = "Slide")
	TSoftObjectPtr<UAnimSequence> SlideInto;

	UPROPERTY(EditAnywhere, Category = "Slide")
	TSoftObjectPtr<UAnimSequence> SlideLoop;

	UPROPERTY(EditAnywhere, Category = "Slide")
	TSoftObjectPtr<UAnimSequence> SlideOutMoving;

	UPROPERTY(EditAnywhere, Category = "Slide")
	TSoftObjectPtr<UAnimSequence> SlideOutStand;

	/** Optional melee combo, played in order on DefaultSlot by ASeleneCharacter::Attack. */
	UPROPERTY(EditAnywhere, Category = "Combat")
	TArray<TSoftObjectPtr<UAnimSequence>> Attacks;

	/** Primary fire: melee combo (Attacks) or a bow (FireClip + projectile). */
	UPROPERTY(EditAnywhere, Category = "Combat")
	ESeleneWeapon Weapon = ESeleneWeapon::Melee;

	/** Optional swing variants played on the upper body while moving (same order as Attacks). */
	UPROPERTY(EditAnywhere, Category = "Combat")
	TArray<TSoftObjectPtr<UAnimSequence>> MovingAttacks;

	UPROPERTY(EditAnywhere, Category = "Combat")
	TSoftObjectPtr<UAnimSequence> FireClip;

	UPROPERTY(EditAnywhere, Category = "Combat") float MaxHealth = 650.f;
	UPROPERTY(EditAnywhere, Category = "Combat") float AttackDamage = 70.f;
	/** Melee reach or bow range, cm. */
	UPROPERTY(EditAnywhere, Category = "Combat") float AttackReach = 330.f;
	/** Fraction of the swing at which the blow lands. */
	UPROPERTY(EditAnywhere, Category = "Combat") float AttackHitFraction = 0.35f;
	/** Seconds between bow shots while the button is held. */
	UPROPERTY(EditAnywhere, Category = "Combat") float FireInterval = 0.45f;
	UPROPERTY(EditAnywhere, Category = "Combat") float ProjectileSpeed = 9000.f;
	/** Cascade systems: projectile trail, muzzle flash and impact on a hit. */
	UPROPERTY(EditAnywhere, Category = "Combat") FSoftObjectPath ProjectileFx;
	UPROPERTY(EditAnywhere, Category = "Combat") FSoftObjectPath MuzzleFx;
	UPROPERTY(EditAnywhere, Category = "Combat") FSoftObjectPath HitFx;
	/** Bone or socket the bow shot leaves from (falls back to the chest). */
	UPROPERTY(EditAnywhere, Category = "Combat") FName MuzzleBone = TEXT("hand_l");

	/** Voice cue path prefix, e.g. /Game/ParagonSparrow/Audio/Cues/Sparrow_ (cues: Effort_Attack, Effort_Pain, Effort_Death, ...). */
	UPROPERTY(EditAnywhere, Category = "Combat") FString VoicePrefix;

	/** Q, E, R in order. */
	UPROPERTY(EditAnywhere, Category = "Combat")
	TArray<FSeleneAbility> Abilities;

	UPROPERTY(EditAnywhere, Category = "Reactions") TSoftObjectPtr<UAnimSequence> HitReactFront;
	UPROPERTY(EditAnywhere, Category = "Reactions") TSoftObjectPtr<UAnimSequence> HitReactBack;
	UPROPERTY(EditAnywhere, Category = "Reactions") TSoftObjectPtr<UAnimSequence> HitReactLeft;
	UPROPERTY(EditAnywhere, Category = "Reactions") TSoftObjectPtr<UAnimSequence> HitReactRight;
	UPROPERTY(EditAnywhere, Category = "Reactions") TSoftObjectPtr<UAnimSequence> Death;

	/** Combat stance (facing the crosshair): directional blend space, speed + direction axes. Falls back to Locomotion. */
	UPROPERTY(EditAnywhere, Category = "Locomotion") TSoftObjectPtr<UBlendSpace> StrafeLocomotion;
	UPROPERTY(EditAnywhere, Category = "Locomotion") TSoftObjectPtr<UAnimSequence> TurnLeft90;
	UPROPERTY(EditAnywhere, Category = "Locomotion") TSoftObjectPtr<UAnimSequence> TurnRight90;
	/** Directional dash clips (forward, back, left, right relative to facing), played for the dash's length. */
	UPROPERTY(EditAnywhere, Category = "Locomotion") TSoftObjectPtr<UAnimSequence> DashFwd;
	UPROPERTY(EditAnywhere, Category = "Locomotion") TSoftObjectPtr<UAnimSequence> DashBwd;
	UPROPERTY(EditAnywhere, Category = "Locomotion") TSoftObjectPtr<UAnimSequence> DashLeft;
	UPROPERTY(EditAnywhere, Category = "Locomotion") TSoftObjectPtr<UAnimSequence> DashRight;
	/** Played instead of Land when the hero lands while moving (optional). */
	UPROPERTY(EditAnywhere, Category = "Locomotion") TSoftObjectPtr<UAnimSequence> LandMoving;

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

/** An idle townsperson spawned at play start from a roster entry, placed relative to the first PlayerStart. */
USTRUCT(BlueprintType)
struct SELENE_API FSeleneNpcSpawn
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, Category = "NPC")
	FName Character;

	/** Centimetres in the PlayerStart's frame: X ahead, Y right. Z is found by tracing to the ground. */
	UPROPERTY(EditAnywhere, Category = "NPC")
	FVector Offset = FVector(500.f, 0.f, 0.f);

	/** Degrees relative to the PlayerStart's facing (180 faces the player). */
	UPROPERTY(EditAnywhere, Category = "NPC")
	float Yaw = 180.f;
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

	UPROPERTY(Config, EditAnywhere, Category = "Characters")
	TArray<FSeleneNpcSpawn> Npcs;
};
