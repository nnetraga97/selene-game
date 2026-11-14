#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "Lanes/SeleneLaneDirector.h"
#include "SeleneCombat.generated.h"

class ASeleneCharacter;
class UParticleSystem;
class UParticleSystemComponent;
class USoundBase;
class USoundAttenuation;

/** Anything that can be hit: a lane unit (minion or structure) or a hero. */
struct SELENE_API FSeleneTarget
{
	TWeakObjectPtr<ASeleneLaneUnit> Unit;
	TWeakObjectPtr<ASeleneCharacter> Hero;

	FSeleneTarget() = default;
	explicit FSeleneTarget(ASeleneLaneUnit* InUnit) : Unit(InUnit) {}
	explicit FSeleneTarget(ASeleneCharacter* InHero) : Hero(InHero) {}

	bool IsSet() const { return Unit.IsValid() || Hero.IsValid(); }
	bool IsAlive() const;
	ESeleneTeam Team() const;
	FVector Location() const;     // capsule centre
	FVector Feet() const;
	float Radius() const;
	float HalfHeight() const;
	bool operator==(const FSeleneTarget& Other) const { return Unit == Other.Unit && Hero == Other.Hero; }
};

/** What the HUD shows over the world for a short time. */
struct FSeleneDamageNumber
{
	FVector Location;
	float Amount = 0.f;
	double Time = 0.0;
	bool bToPlayer = false;   // damage the player took
	bool bHeavy = false;
};

struct FSeleneAnnouncement
{
	FString Text;
	FLinearColor Color = FLinearColor::White;
	double Time = 0.0;
	float Duration = 3.f;
};

/** World-level combat services shared by heroes and the lane director. */
UCLASS()
class SELENE_API USeleneCombatSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	static USeleneCombatSubsystem* Get(const UObject* WorldContext);

	virtual void Tick(float DeltaSeconds) override;
	virtual TStatId GetStatId() const override { RETURN_QUICK_DECLARE_CYCLE_STAT(USeleneCombatSubsystem, STATGROUP_Tickables); }
	virtual void Deinitialize() override;

	// --- effects
	UParticleSystem* Fx(const FSoftObjectPath& Path);
	UParticleSystem* Fx(const TCHAR* Path) { return Fx(FSoftObjectPath(Path)); }
	UParticleSystemComponent* SpawnFx(const FSoftObjectPath& Path, const FVector& Location, const FRotator& Rotation = FRotator::ZeroRotator, float Scale = 1.f);
	UParticleSystemComponent* SpawnFx(const TCHAR* Path, const FVector& Location, const FRotator& Rotation = FRotator::ZeroRotator, float Scale = 1.f)
	{
		return SpawnFx(FSoftObjectPath(Path), Location, Rotation, Scale);
	}
	UParticleSystemComponent* AttachFx(const FSoftObjectPath& Path, USceneComponent* To, FName Socket, float Scale = 1.f);

	// --- sound
	/** Any sound asset by full object path (voice cues). */
	USoundBase* Sound(const FString& Path);
	void PlaySoundAt(USoundBase* Sound, const FVector& Location, float Volume = 1.f, float Pitch = 1.f);

	/** Freezes the actor's animation and movement for a moment (real time), for weight on hits. */
	void HitStop(AActor* Actor, float Seconds);

	// --- targets and damage
	/** Every living enemy of Team within Radius of Center (2D distance minus target radius; heights within 4 m). */
	void GatherEnemies(const FVector& Center, float Radius, ESeleneTeam Team, TArray<FSeleneTarget>& Out) const;
	/** Enemies in a forward cone (cosine of the half angle) up to Reach. */
	void GatherCone(const FVector& Origin, const FVector& Forward, float Reach, float MinCos, ESeleneTeam Team, TArray<FSeleneTarget>& Out) const;
	/** First enemy whose capsule the ray passes within Slack cm of; OutDistance along the ray. */
	FSeleneTarget RayEnemy(const FVector& Start, const FVector& Dir, float Length, ESeleneTeam Team, float Slack, float& OutDistance) const;
	/** Applies damage, effects and HUD feedback. Returns the damage actually dealt (0 if protected). */
	float DealDamage(const FSeleneTarget& Target, float Amount, ESeleneTeam FromTeam, const FVector& From, AActor* Instigator, bool bHeavy = false);
	void Slow(const FSeleneTarget& Target, float Factor, float Seconds);
	void Stun(const FSeleneTarget& Target, float Seconds);

	// --- projectiles
	struct FProjectileSpec
	{
		FSoftObjectPath TrailFx;
		FSoftObjectPath ImpactFx;
		float FxScale = 1.f;
		float Speed = 3000.f;
		float Damage = 20.f;
		float Range = 6000.f;
		float HitRadius = 30.f;    // extra slack round target capsules
		bool bPierce = false;
		bool bHitWorld = true;     // stop on static geometry
		bool bHeavy = false;
	};
	/** Homing shot at a target (minions, structures). */
	void FireHoming(const FProjectileSpec& Spec, const FVector& Start, const FSeleneTarget& Target, ESeleneTeam Team, AActor* Instigator);
	/** Straight shot (hero bow). */
	void FireStraight(const FProjectileSpec& Spec, const FVector& Start, const FVector& Dir, ESeleneTeam Team, AActor* Instigator);

	// --- HUD feed
	TArray<FSeleneDamageNumber> DamageNumbers;
	TArray<FSeleneAnnouncement> Announcements;
	double LastHitMarkerTime = -100.0;
	bool bLastHitWasKill = false;
	double LastPlayerHurtTime = -100.0;
	FVector LastPlayerHurtFrom = FVector::ZeroVector;
	void Announce(const FString& Text, const FLinearColor& Color, float Duration = 3.f, bool bChime = true);
	double Now() const;

	/** Every hero currently in the world (player and bots), alive or not. */
	void ForEachHero(TFunctionRef<void(ASeleneCharacter&)> Visit) const;

private:
	struct FProjectile
	{
		FProjectileSpec Spec;
		FVector Pos;
		FVector Dir;
		FSeleneTarget Homing;
		ESeleneTeam Team;
		TWeakObjectPtr<AActor> Instigator;
		TWeakObjectPtr<UParticleSystemComponent> Trail;
		TArray<FSeleneTarget> AlreadyHit;
		float Travelled = 0.f;
	};
	TArray<FProjectile> Projectiles;
	void FinishProjectile(FProjectile& P, const FVector& At, bool bHitSomething);

	struct FStop { TWeakObjectPtr<AActor> Actor; double Until; float Saved; };
	TArray<FStop> Stops;

	UPROPERTY() TMap<FName, TObjectPtr<UParticleSystem>> FxCache;
	UPROPERTY() TMap<FName, TObjectPtr<USoundBase>> SoundCache;
	UPROPERTY() TObjectPtr<USoundAttenuation> Attenuation;
};
