#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SeleneLaneDirector.generated.h"

class UAnimSequence;
class UCapsuleComponent;
class USkeletalMeshComponent;
class UParticleSystemComponent;
class ASeleneCharacter;
struct FSeleneTarget;

UENUM()
enum class ESeleneTeam : uint8 { Dawn, Dusk };

UENUM()
enum class ESeleneUnitKind : uint8 { Melee, Ranged, Siege, Guardian, Walker, Patron, BaseGuardian, Shrine };

/** One lane of the 3-lane test map: a polyline running from the Dawn base to the Dusk base (cm, world space). */
USTRUCT(BlueprintType)
struct FSeleneLane
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lane")
	FName LaneName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lane")
	TArray<FVector> Points;
};

/** A lane minion or a placeholder structure. It has no tick of its own: ASeleneLaneDirector drives every unit. */
UCLASS()
class SELENE_API ASeleneLaneUnit : public AActor
{
	GENERATED_BODY()

public:
	ASeleneLaneUnit();

	UPROPERTY(VisibleAnywhere, Category = "Lane")
	TObjectPtr<UCapsuleComponent> Capsule;

	UPROPERTY(VisibleAnywhere, Category = "Lane")
	TObjectPtr<USkeletalMeshComponent> Mesh;

	UPROPERTY() TObjectPtr<UAnimSequence> MoveAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> AttackAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> DeathAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> IdleAnim;
	UPROPERTY() TObjectPtr<UAnimSequence> CurrentAnim;
	UPROPERTY() TArray<TObjectPtr<UAnimSequence>> HitReactAnims;   // front, back, left, right (may be empty)
	UPROPERTY() TArray<TObjectPtr<UAnimSequence>> DeathAnims;

	ESeleneTeam Team = ESeleneTeam::Dawn;
	ESeleneUnitKind Kind = ESeleneUnitKind::Melee;
	int32 Lane = INDEX_NONE;      // INDEX_NONE: belongs to no lane (Patron)
	bool bStructure = false;
	FVector2D Pos = FVector2D::ZeroVector;
	float S = 0.f;                // distance along the lane path
	float Lateral = 0.f;          // preferred sideways offset from the lane centre
	float Radius = 40.f;
	float HalfHeight = 90.f;
	float Health = 1.f;
	float MaxHealth = 1.f;
	float Damage = 0.f;
	float Range = 0.f;
	float AttackPeriod = 1.f;
	float Speed = 0.f;
	float AttackTimer = 0.f;
	float DeadTime = -1.f;        // >= 0 once dead
	float Z = 0.f;                // ground height under the unit (cm)
	float SlowTimer = 0.f;
	/** Map time an enemy hero last damaged this structure (structures regenerate when only troopers fight them). */
	float LastHeroHitTime = -100.f;
	float SlowFactor = 1.f;
	float StunTimer = 0.f;
	float HitReactTimer = 0.f;
	float BaseScale = 1.f;
	float HeroAggroTimer = 0.f;   // > 0: chasing the hero who hit an ally
	TWeakObjectPtr<ASeleneCharacter> AggroHero;
	TWeakObjectPtr<UParticleSystemComponent> StateFx;

	bool IsAlive() const { return DeadTime < 0.f; }
	FVector Center() const { return FVector(Pos.X, Pos.Y, Z + HalfHeight); }
	void Play(UAnimSequence* Anim, bool bLoop);
};

/** Spawns minion waves on each lane, places the placeholder structures and runs all unit movement and combat. */
UCLASS(Config = Game)
class SELENE_API ASeleneLaneDirector : public AActor
{
	GENERATED_BODY()

public:
	ASeleneLaneDirector();
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;

	static ASeleneLaneDirector* Get(const UWorld* World);

	/** Damage from any source (heroes, projectiles, minions). Returns the damage dealt: 0 when the structure is protected. */
	float DamageUnit(ASeleneLaneUnit& Unit, float Amount, const FVector& From, AActor* Instigator);

	/** Walkers are protected while their lane's Guardian stands; a Patron while all of its team's Walkers stand. */
	bool IsProtected(const ASeleneLaneUnit& Unit) const;
	bool IsAnyAlive(ESeleneTeam Team, ESeleneUnitKind Kind) const;
	bool IsAnyDead(ESeleneTeam Team, ESeleneUnitKind Kind, const ASeleneLaneUnit* Except = nullptr) const;

	/** A hero hurt one of Team's units: nearby minions of that team turn on the hero for a few seconds. */
	void DrawAggro(ESeleneTeam Team, ASeleneCharacter* Hero, const FVector& Where);

	const TArray<TObjectPtr<ASeleneLaneUnit>>& GetUnits() const { return Units; }

	struct FObjectives
	{
		int32 Guardians[2] = { 0, 0 };
		int32 Walkers[2] = { 0, 0 };
		int32 BaseGuardians[2] = { 0, 0 };
		int32 Shrines[2] = { 0, 0 };
		float PatronHealth[2] = { 0.f, 0.f };   // fraction
		bool bPatronProtected[2] = { true, true };
		bool bGameOver = false;
		ESeleneTeam Winner = ESeleneTeam::Dawn;
		float Clock = 0.f;
		float NextWave = 0.f;
		int32 Wave = 0;
		bool bHasLanes = false;
	};
	FObjectives GetObjectives() const;

	/** Debug: put a pawn on a lane at a fraction of its length from the Dawn base, facing Dusk. */
	void DebugTeleport(APawn& Pawn, FName LaneName, float Fraction);
	void DebugBreak(ESeleneTeam Team, FName LaneName, ESeleneUnitKind Kind);

	/** Ground height at a point, tracing down from Above (cm). */
	float TraceGround(const FVector2D& At, float Above, float Fallback) const;

	/** Read-only walk over every unit (minions and structures), for the minimap. */
	void ForEachUnit(TFunctionRef<void(const ASeleneLaneUnit&)> Visit) const
	{
		for (const ASeleneLaneUnit* Unit : Units) { if (Unit) Visit(*Unit); }
	}

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lanes")
	TArray<FSeleneLane> Lanes;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lanes")
	FVector DawnBase = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Lanes")
	FVector DuskBase = FVector::ZeroVector;

	UPROPERTY(Config, EditAnywhere, Category = "Waves") float FirstWaveDelay = 5.f;
	UPROPERTY(Config, EditAnywhere, Category = "Waves") float WaveInterval = 25.f;
	UPROPERTY(Config, EditAnywhere, Category = "Waves") int32 MeleePerWave = 3;
	UPROPERTY(Config, EditAnywhere, Category = "Waves") int32 RangedPerWave = 1;
	/** A siege minion joins every Nth wave (0 = never). */
	UPROPERTY(Config, EditAnywhere, Category = "Waves") int32 SiegeEveryNthWave = 3;
	/** Share of trooper damage a structure takes. */
	UPROPERTY(Config, EditAnywhere, Category = "Waves") float TrooperVsStructure = 0.35f;
	/** Max-health share a structure heals per second once no enemy hero has hit it for 8 s (slow, so a push carries over to the next wave). */
	UPROPERTY(Config, EditAnywhere, Category = "Waves") float StructureRegen = 0.003f;
	UPROPERTY(Config, EditAnywhere, Category = "Waves") int32 MaxMinions = 140;
	/** Where the structures stand, as a fraction of the lane measured from their own base. */
	UPROPERTY(Config, EditAnywhere, Category = "Structures") float WalkerFraction = 0.15f;
	UPROPERTY(Config, EditAnywhere, Category = "Structures") float GuardianFraction = 0.36f;
	UPROPERTY(Config, EditAnywhere, Category = "Combat") float HeroDamage = 150.f;
	UPROPERTY(Config, EditAnywhere, Category = "Combat") float HeroReach = 300.f;

private:
	struct FPath
	{
		TArray<FVector2D> P;
		TArray<float> Cum;
		float Length = 0.f;
		void Build(const TArray<FVector2D>& Points);
		FVector2D At(float Dist, FVector2D* OutTangent = nullptr) const;
		float Project(const FVector2D& Point) const;
	};

	ASeleneLaneUnit* SpawnUnit(ESeleneUnitKind Kind, ESeleneTeam Team, int32 Lane, const FVector2D& At, float S, float Lateral, float Power = 1.f);
	void SpawnStructures();
	void SpawnWave();
	void SpawnStress(int32 PerTeam);
	void TickUnit(ASeleneLaneUnit& Unit, float DeltaSeconds);
	FSeleneTarget FindTarget(const ASeleneLaneUnit& Unit, float MaxDistance) const;
	void Kill(ASeleneLaneUnit& Target, const FVector& From);
	void Attack(ASeleneLaneUnit& Unit, const FSeleneTarget& Target);
	void Place(ASeleneLaneUnit& Unit, float FaceYaw);
	void DrawHealth() const;
	int32 CountMinions() const;
	void TickTour(float Hold, float DeltaSeconds);
	void LogStats(float DeltaSeconds);
	TArray<FTransform> TourStops;
	UPROPERTY() TObjectPtr<class ACameraActor> TourCamera;
	float TourTime = 0.f;
	int32 TourIndex = 0;
	bool bTourShot = false;

	struct FPendingSpawn { ESeleneUnitKind Kind; ESeleneTeam Team; int32 Lane; FVector2D At; float S; float Lateral; float Power; };
	TArray<FPendingSpawn> Pending;
	UPROPERTY() TArray<TObjectPtr<ASeleneLaneUnit>> Units;
	/** Unit meshes and clips loaded at map start, held so the first wave doesn't hitch on loads. */
	UPROPERTY(Transient) TArray<TObjectPtr<UObject>> Preloaded;
	TArray<FPath> Paths;
	float Clock = 0.f;
	float NextWave = 0.f;
	int32 WaveIndex = 0;
	bool bGameOver = false;
	ESeleneTeam Winner = ESeleneTeam::Dawn;
	float GameOverTime = 0.f;
	int32 LastStress = 0;
	float StatTime = 0.f;
	float StatWorst = 0.f;
	int32 StatFrames = 0;
	double StatDirector = 0.0;
	bool bExecDone = false;
	bool ScriptParsed = false;
	TArray<TPair<float, FString>> Script;
	TMap<FString, int32> SavedCVars;
};
