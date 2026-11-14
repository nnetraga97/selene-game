#include "Lanes/SeleneLaneDirector.h"

#include "Selene.h"
#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "DrawDebugHelpers.h"
#include "Engine/Engine.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "UnrealClient.h"
#include "Misc/Paths.h"
#include "RenderCore.h"
#include "RHI.h"
#include "RenderTimer.h"

namespace
{
	TAutoConsoleVariable<int32> CVarLaneStress(TEXT("selene.LaneStress"), 0,
		TEXT("Debug: spawns this many extra melee minions per team, spread over the lanes, to test frame rate."));
	TAutoConsoleVariable<float> CVarLaneLog(TEXT("selene.LaneLog"), 0.f,
		TEXT("Debug: > 0 logs living minions and frame rate every N seconds."));
	TAutoConsoleVariable<int32> CVarLaneHealth(TEXT("selene.LaneHealthBars"), 1,
		TEXT("Draws a health line over damaged lane units near the player."));
	TAutoConsoleVariable<float> CVarLaneTour(TEXT("selene.LaneTour"), 0.f,
		TEXT("Debug: > 0 moves the view through fixed map viewpoints, N seconds each, saving Saved/LanesMap/tour/NN.png."));
	TAutoConsoleVariable<FString> CVarLaneExecAt(TEXT("selene.LaneExecAt"), TEXT(""),
		TEXT("Debug: 'seconds:command' runs that console command once at that map time (for example 30:ProfileGPU)."));
	TAutoConsoleVariable<int32> CVarLaneFastRender(TEXT("selene.LaneFastRender"), 1,
		TEXT("1: lane maps turn Lumen GI and reflections off and hold the time of day, for frame rate. Read when the map starts."));
	TAutoConsoleVariable<int32> CVarLaneWaves(TEXT("selene.LaneWaves"), 1,
		TEXT("0 stops new minion waves."));

	struct FKindSpec
	{
		const TCHAR* DawnMesh; const TCHAR* DuskMesh;
		const TCHAR* Move; const TCHAR* Attack; const TCHAR* Death; const TCHAR* Idle;
		float Scale, Radius, HalfHeight, Health, Damage, Range, Period, Speed;
		bool bStructure;
	};

#define MINIONS TEXT("/Game/ParagonMinions/Characters/Minions/")
#define DOWN_MESH MINIONS TEXT("Down_Minions/Meshes/")
#define DUSK_MESH MINIONS TEXT("Dusk_Minions/Meshes/")
#define ANIM MINIONS TEXT("Down_Minions/Animations/")
#define HELIX MINIONS TEXT("Prime_Helix/")
	const FKindSpec& Spec(ESeleneUnitKind Kind)
	{
		static const FKindSpec Specs[] = {
			// Melee
			{ DOWN_MESH TEXT("Minion_Lane_Melee_Dawn"), DUSK_MESH TEXT("Minion_Lane_Melee_Dusk"),
			  ANIM TEXT("Melee/Combat_JogFwd"), ANIM TEXT("Melee/Attack_A"), ANIM TEXT("Melee/Death_A"), ANIM TEXT("Melee/NonCombat_Idle"),
			  1.f, 45.f, 90.f, 300.f, 24.f, 190.f, 1.0f, 420.f, false },
			// Ranged
			{ DOWN_MESH TEXT("Minion_Lane_Ranged_Dawn"), DUSK_MESH TEXT("Minion_Lane_Ranged_Dusk"),
			  ANIM TEXT("Ranged/Jog_Fwd_Combat_A"), ANIM TEXT("Ranged/Fire_A"), ANIM TEXT("Ranged/Death_Front_A"), ANIM TEXT("Ranged/Idle_A"),
			  1.f, 45.f, 90.f, 200.f, 18.f, 1100.f, 1.2f, 420.f, false },
			// Siege
			{ DOWN_MESH TEXT("Minion_Lane_Siege_Dawn"), DUSK_MESH TEXT("Minion_Lane_Siege_Dusk"),
			  ANIM TEXT("Siege/Jog_Fwd_Combat"), ANIM TEXT("Siege/Fire_A"), ANIM TEXT("Siege/Death_A"), ANIM TEXT("Siege/Idle"),
			  1.f, 70.f, 100.f, 700.f, 60.f, 1400.f, 2.5f, 350.f, false },
			// Guardian (placeholder: Super minion)
			{ DOWN_MESH TEXT("Minion_Lane_Super_Dawn"), DUSK_MESH TEXT("Minion_Lane_Super_Dusk"),
			  ANIM TEXT("Super/Idle"), ANIM TEXT("Super/Attack_A"), ANIM TEXT("Super/Death_Front"), ANIM TEXT("Super/Idle"),
			  1.8f, 130.f, 220.f, 2500.f, 70.f, 1300.f, 1.0f, 0.f, true },
			// Walker (placeholder: Siege minion, planted)
			{ DOWN_MESH TEXT("Minion_Lane_Siege_Dawn"), DUSK_MESH TEXT("Minion_Lane_Siege_Dusk"),
			  ANIM TEXT("Siege/Idle_Planted"), ANIM TEXT("Siege/Fire_Planted"), ANIM TEXT("Siege/Death_A"), ANIM TEXT("Siege/Idle_Planted"),
			  2.4f, 190.f, 260.f, 5000.f, 120.f, 1500.f, 1.5f, 0.f, true },
			// Patron (placeholder: Prime Helix)
			{ HELIX TEXT("Meshes/Prime_Helix"), HELIX TEXT("Meshes/Prime_Helix"),
			  HELIX TEXT("Animations/Idle"), HELIX TEXT("Animations/Primary_Fire"), HELIX TEXT("Animations/Death"), HELIX TEXT("Animations/Idle"),
			  1.f, 300.f, 350.f, 9000.f, 150.f, 1600.f, 1.2f, 0.f, true },
		};
		return Specs[static_cast<int32>(Kind)];
	}

	template <typename T> T* LoadAsset(const TCHAR* Path)
	{
		const FString Full = FString(Path) + TEXT(".") + FPaths::GetBaseFilename(Path);
		T* Asset = LoadObject<T>(nullptr, *Full);
		if (!Asset) UE_LOG(LogSelene, Warning, TEXT("Lanes: could not load %s"), *Full);
		return Asset;
	}

	const float AggroRange = 1200.f;
	const float CorpseSeconds = 3.f;
}

ASeleneLaneUnit::ASeleneLaneUnit()
{
	PrimaryActorTick.bCanEverTick = false;
	Capsule = CreateDefaultSubobject<UCapsuleComponent>(TEXT("Capsule"));
	SetRootComponent(Capsule);
	Capsule->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Capsule->SetCollisionObjectType(ECC_WorldDynamic);
	Capsule->SetCollisionResponseToAllChannels(ECR_Ignore);
	Capsule->SetCanEverAffectNavigation(false);
	Capsule->SetGenerateOverlapEvents(false);
	Mesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Mesh"));
	Mesh->SetupAttachment(Capsule);
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->SetGenerateOverlapEvents(false);
	Mesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	Mesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
	Mesh->bEnableUpdateRateOptimizations = true;
	Mesh->bComponentUseFixedSkelBounds = true;
	Mesh->SetCanEverAffectNavigation(false);
}

void ASeleneLaneUnit::Play(UAnimSequence* Anim, bool bLoop)
{
	if (!Anim || CurrentAnim == Anim) return;
	CurrentAnim = Anim;
	Mesh->PlayAnimation(Anim, bLoop);
}

void ASeleneLaneDirector::FPath::Build(const TArray<FVector2D>& Points)
{
	P = Points;
	Cum.Reset();
	Length = 0.f;
	for (int32 i = 0; i < P.Num(); ++i)
	{
		if (i > 0) Length += FVector2D::Distance(P[i - 1], P[i]);
		Cum.Add(Length);
	}
}

FVector2D ASeleneLaneDirector::FPath::At(float Dist, FVector2D* OutTangent) const
{
	Dist = FMath::Clamp(Dist, 0.f, Length);
	for (int32 i = 1; i < P.Num(); ++i)
	{
		if (Dist <= Cum[i] || i == P.Num() - 1)
		{
			const float Seg = FMath::Max(Cum[i] - Cum[i - 1], 1.f);
			if (OutTangent) *OutTangent = (P[i] - P[i - 1]) / Seg;
			return FMath::Lerp(P[i - 1], P[i], FMath::Clamp((Dist - Cum[i - 1]) / Seg, 0.f, 1.f));
		}
	}
	return P.Num() ? P[0] : FVector2D::ZeroVector;
}

float ASeleneLaneDirector::FPath::Project(const FVector2D& Point) const
{
	float Best = 0.f, BestSq = TNumericLimits<float>::Max();
	for (int32 i = 1; i < P.Num(); ++i)
	{
		const FVector2D AB = P[i] - P[i - 1];
		const float T = FMath::Clamp(FVector2D::DotProduct(Point - P[i - 1], AB) / FMath::Max(AB.SizeSquared(), 1.f), 0.f, 1.f);
		const float Sq = FVector2D::DistSquared(Point, P[i - 1] + AB * T);
		if (Sq < BestSq) { BestSq = Sq; Best = Cum[i - 1] + (Cum[i] - Cum[i - 1]) * T; }
	}
	return Best;
}

ASeleneLaneDirector::ASeleneLaneDirector()
{
	PrimaryActorTick.bCanEverTick = true;
	SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
}

ASeleneLaneDirector* ASeleneLaneDirector::Get(const UWorld* World)
{
	if (!World) return nullptr;
	TActorIterator<ASeleneLaneDirector> It(World);
	return It ? *It : nullptr;
}

void ASeleneLaneDirector::BeginPlay()
{
	Super::BeginPlay();
	for (const FSeleneLane& Lane : Lanes)
	{
		TArray<FVector2D> Points;
		Points.Add(FVector2D(DawnBase));
		for (const FVector& Point : Lane.Points) Points.Add(FVector2D(Point));
		Points.Add(FVector2D(DuskBase));
		Paths.AddDefaulted_GetRef().Build(Points);
	}
	NextWave = FirstWaveDelay;
	if (CVarLaneFastRender.GetValueOnGameThread() != 0)
	{
		// The project default (Lumen GI + reflections) costs about 10 ms a frame here; this map is for gameplay tests.
		for (const TCHAR* Name : { TEXT("r.DynamicGlobalIlluminationMethod"), TEXT("r.ReflectionMethod") })
		{
			if (IConsoleVariable* Var = IConsoleManager::Get().FindConsoleVariable(Name))
			{
				SavedCVars.Add(Name, Var->GetInt());
				Var->Set(0, ECVF_SetByConsole);
			}
		}
		if (APlayerController* PC = GetWorld()->GetFirstPlayerController()) PC->ConsoleCommand(TEXT("tod.pause 1"));
	}
	SpawnStructures();
	UE_LOG(LogSelene, Log, TEXT("Lanes: %d lanes, %d structures, wave every %.0fs (%d melee + %d ranged)."),
		Paths.Num(), Units.Num(), WaveInterval, MeleePerWave, RangedPerWave);
}

ASeleneLaneUnit* ASeleneLaneDirector::SpawnUnit(ESeleneUnitKind Kind, ESeleneTeam Team, int32 Lane, const FVector2D& At, float S, float Lateral)
{
	const FKindSpec& K = Spec(Kind);
	USkeletalMesh* MeshAsset = LoadAsset<USkeletalMesh>(Team == ESeleneTeam::Dawn ? K.DawnMesh : K.DuskMesh);
	if (!MeshAsset) return nullptr;
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ASeleneLaneUnit* Unit = GetWorld()->SpawnActor<ASeleneLaneUnit>(ASeleneLaneUnit::StaticClass(), FTransform(FVector(At.X, At.Y, K.HalfHeight)), Params);
	if (!Unit) return nullptr;
	Unit->Team = Team; Unit->Kind = Kind; Unit->Lane = Lane; Unit->bStructure = K.bStructure;
	Unit->Pos = At; Unit->S = S; Unit->Lateral = Lateral;
	Unit->Radius = K.Radius; Unit->HalfHeight = K.HalfHeight;
	Unit->Health = Unit->MaxHealth = K.Health;
	Unit->Damage = K.Damage; Unit->Range = K.Range; Unit->AttackPeriod = K.Period; Unit->Speed = K.Speed;
	Unit->AttackTimer = FMath::FRandRange(0.f, K.Period);
	Unit->Capsule->SetCapsuleSize(K.Radius, K.HalfHeight);
	if (K.bStructure)
	{
		Unit->Capsule->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);  // heroes walk round structures
	}
	Unit->Mesh->SetSkeletalMeshAsset(MeshAsset);
	Unit->Mesh->SetRelativeLocationAndRotation(FVector(0, 0, -K.HalfHeight), FRotator(0, -90, 0));
	Unit->Mesh->SetRelativeScale3D(FVector(K.Scale));
	Unit->MoveAnim = LoadAsset<UAnimSequence>(K.Move);
	Unit->AttackAnim = LoadAsset<UAnimSequence>(K.Attack);
	Unit->DeathAnim = LoadAsset<UAnimSequence>(K.Death);
	Unit->IdleAnim = LoadAsset<UAnimSequence>(K.Idle);
	Unit->Play(K.bStructure ? Unit->IdleAnim : Unit->MoveAnim, true);
	Place(*Unit, Team == ESeleneTeam::Dawn ? 0.f : 180.f);
	Units.Add(Unit);
	return Unit;
}

void ASeleneLaneDirector::Place(ASeleneLaneUnit& Unit, float FaceYaw)
{
	Unit.SetActorLocationAndRotation(FVector(Unit.Pos.X, Unit.Pos.Y, Unit.HalfHeight), FRotator(0, FaceYaw, 0), false, nullptr, ETeleportType::TeleportPhysics);
}

void ASeleneLaneDirector::SpawnStructures()
{
	for (int32 Lane = 0; Lane < Lanes.Num(); ++Lane)
	{
		TArray<FVector2D> Points;
		for (const FVector& Point : Lanes[Lane].Points) Points.Add(FVector2D(Point));
		FPath Street; Street.Build(Points);   // fractions are measured on the street itself, base plazas excluded
		for (const ESeleneTeam Team : { ESeleneTeam::Dawn, ESeleneTeam::Dusk })
		{
			for (const ESeleneUnitKind Kind : { ESeleneUnitKind::Walker, ESeleneUnitKind::Guardian })
			{
				const float Own = Kind == ESeleneUnitKind::Walker ? WalkerFraction : GuardianFraction;
				const FVector2D At = Street.At(Street.Length * (Team == ESeleneTeam::Dawn ? Own : 1.f - Own));
				SpawnUnit(Kind, Team, Lane, At, Paths[Lane].Project(At), 0.f);
			}
		}
	}
	SpawnUnit(ESeleneUnitKind::Patron, ESeleneTeam::Dawn, INDEX_NONE, FVector2D(DawnBase), 0.f, 0.f);
	SpawnUnit(ESeleneUnitKind::Patron, ESeleneTeam::Dusk, INDEX_NONE, FVector2D(DuskBase), 0.f, 0.f);
}

int32 ASeleneLaneDirector::CountMinions() const
{
	int32 Count = 0;
	for (const ASeleneLaneUnit* Unit : Units) Count += (Unit && !Unit->bStructure && Unit->IsAlive()) ? 1 : 0;
	return Count;
}

void ASeleneLaneDirector::SpawnWave()
{
	const bool bSiege = SiegeEveryNthWave > 0 && (WaveIndex + 1) % SiegeEveryNthWave == 0;
	const int32 PerLane = MeleePerWave + RangedPerWave + (bSiege ? 1 : 0);
	if (CountMinions() + Pending.Num() + PerLane * Paths.Num() * 2 > MaxMinions)
	{
		UE_LOG(LogSelene, Log, TEXT("Lanes: wave %d skipped, minion cap %d reached."), WaveIndex + 1, MaxMinions);
		++WaveIndex;
		return;
	}
	for (int32 Lane = 0; Lane < Paths.Num(); ++Lane)
	{
		const FPath& Path = Paths[Lane];
		for (const ESeleneTeam Team : { ESeleneTeam::Dawn, ESeleneTeam::Dusk })
		{
			const float Dir = Team == ESeleneTeam::Dawn ? 1.f : -1.f;
			const float Start = Team == ESeleneTeam::Dawn ? 2600.f : Path.Length - 2600.f;  // the lane mouth at the base plaza edge
			for (int32 i = 0; i < PerLane; ++i)
			{
				const ESeleneUnitKind Kind = i < MeleePerWave ? ESeleneUnitKind::Melee
					: i < MeleePerWave + RangedPerWave ? ESeleneUnitKind::Ranged : ESeleneUnitKind::Siege;
				const bool bFront = Kind == ESeleneUnitKind::Melee;
				const float Lateral = bFront ? (i - (MeleePerWave - 1) * 0.5f) * 180.f : (i - MeleePerWave) * 220.f - 110.f;
				const float S = Start - Dir * (bFront ? 0.f : 260.f);
				FVector2D Tangent;
				const FVector2D Centre = Path.At(S, &Tangent);
				Pending.Add({ Kind, Team, Lane, Centre + FVector2D(-Tangent.Y, Tangent.X) * Lateral, S, Lateral });
			}
		}
	}
	++WaveIndex;
	UE_LOG(LogSelene, Log, TEXT("Lanes: wave %d queued, %d minions alive."), WaveIndex, CountMinions());
}

void ASeleneLaneDirector::SpawnStress(int32 PerTeam)
{
	for (int32 i = 0; i < PerTeam && Paths.Num(); ++i)
	{
		const int32 Lane = i % Paths.Num();
		const FPath& Path = Paths[Lane];
		for (const ESeleneTeam Team : { ESeleneTeam::Dawn, ESeleneTeam::Dusk })
		{
			const float Dir = Team == ESeleneTeam::Dawn ? 1.f : -1.f;
			const float S = Path.Length * 0.5f - Dir * (900.f + (i / Paths.Num()) * 120.f);
			const float Lateral = ((i / Paths.Num()) % 5 - 2) * 110.f;
			FVector2D Tangent;
			const FVector2D Centre = Path.At(S, &Tangent);
			Pending.Add({ ESeleneUnitKind::Melee, Team, Lane, Centre + FVector2D(-Tangent.Y, Tangent.X) * Lateral, S, Lateral });
		}
	}
	UE_LOG(LogSelene, Log, TEXT("Lanes: stress spawned %d per team, %d minions alive."), PerTeam, CountMinions());
}

ASeleneLaneUnit* ASeleneLaneDirector::FindTarget(const ASeleneLaneUnit& Unit, float MaxDistance) const
{
	ASeleneLaneUnit* Best = nullptr;
	float BestDist = MaxDistance;
	for (ASeleneLaneUnit* Other : Units)
	{
		if (!Other || Other->Team == Unit.Team || !Other->IsAlive()) continue;
		if (Unit.Lane != INDEX_NONE && Other->Lane != INDEX_NONE && Other->Lane != Unit.Lane) continue;
		const float Dist = FVector2D::Distance(Unit.Pos, Other->Pos) - Other->Radius - Unit.Radius;
		if (Dist < BestDist) { BestDist = Dist; Best = Other; }
	}
	return Best;
}

void ASeleneLaneDirector::ApplyDamage(ASeleneLaneUnit& Target, float Amount)
{
	if (!Target.IsAlive()) return;
	Target.Health -= Amount;
	if (Target.Health > 0.f) return;
	Target.DeadTime = 0.f;
	Target.CurrentAnim = nullptr;
	Target.Play(Target.DeathAnim, false);
	Target.Capsule->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (Target.bStructure)
	{
		static const TCHAR* Names[] = { TEXT("Melee"), TEXT("Ranged"), TEXT("Siege"), TEXT("Guardian"), TEXT("Walker"), TEXT("Patron") };
		const TCHAR* Side = Target.Team == ESeleneTeam::Dawn ? TEXT("Dawn") : TEXT("Dusk");
		UE_LOG(LogSelene, Log, TEXT("Lanes: %s %s destroyed at %.0fs."), Side, Names[static_cast<int32>(Target.Kind)], Clock);
		if (GEngine) GEngine->AddOnScreenDebugMessage(-1, 6.f, FColor::Yellow, FString::Printf(TEXT("%s %s destroyed"), Side, Names[static_cast<int32>(Target.Kind)]));
		if (Target.Kind == ESeleneUnitKind::Patron)
		{
			bGameOver = true;
			const TCHAR* Winner = Target.Team == ESeleneTeam::Dawn ? TEXT("Dusk") : TEXT("Dawn");
			UE_LOG(LogSelene, Log, TEXT("Lanes: %s wins."), Winner);
			if (GEngine) GEngine->AddOnScreenDebugMessage(-1, 30.f, FColor::Green, FString::Printf(TEXT("%s wins"), Winner));
		}
	}
}

int32 ASeleneLaneDirector::HeroStrike(const FVector& Origin, const FVector& Forward, ESeleneTeam AttackerTeam, float Reach, float Amount)
{
	const FVector2D From(Origin), Dir = FVector2D(Forward).GetSafeNormal();
	int32 Hits = 0;
	for (ASeleneLaneUnit* Unit : Units)
	{
		if (!Unit || Unit->Team == AttackerTeam || !Unit->IsAlive()) continue;
		const FVector2D To = Unit->Pos - From;
		const float Dist = To.Size() - Unit->Radius;
		if (Dist > Reach || (Dist > 60.f && FVector2D::DotProduct(To.GetSafeNormal(), Dir) < 0.25f)) continue;
		ApplyDamage(*Unit, Amount);
		++Hits;
	}
	return Hits;
}

void ASeleneLaneDirector::TickUnit(ASeleneLaneUnit& Unit, float DeltaSeconds)
{
	ASeleneLaneUnit* Target = FindTarget(Unit, Unit.bStructure ? Unit.Range : FMath::Max(AggroRange, Unit.Range));
	const float Gap = Target ? FVector2D::Distance(Unit.Pos, Target->Pos) - Target->Radius - Unit.Radius : 0.f;
	if (Target && Gap <= Unit.Range)
	{
		const FVector2D To = Target->Pos - Unit.Pos;
		Unit.Play(Unit.AttackAnim, true);
		Unit.AttackTimer -= DeltaSeconds;
		if (Unit.AttackTimer <= 0.f)
		{
			Unit.AttackTimer += Unit.AttackPeriod;
			ApplyDamage(*Target, Unit.Damage);
		}
		Place(Unit, FMath::RadiansToDegrees(FMath::Atan2(To.Y, To.X)));
		return;
	}
	if (Unit.bStructure)
	{
		Unit.Play(Unit.IdleAnim, true);
		return;
	}
	const FPath& Path = Paths[Unit.Lane];
	const float Dir = Unit.Team == ESeleneTeam::Dawn ? 1.f : -1.f;
	FVector2D Goal;
	if (Target)
	{
		Goal = Target->Pos;
	}
	else
	{
		FVector2D Tangent;
		const float Ahead = Unit.S + Dir * 350.f;
		const FVector2D Centre = Path.At(Ahead, &Tangent);
		const float Edge = FMath::Min(Ahead, Path.Length - Ahead);
		Goal = Centre + FVector2D(-Tangent.Y, Tangent.X) * Unit.Lateral * FMath::Clamp(Edge / 2500.f, 0.f, 1.f);
	}
	FVector2D Step = (Goal - Unit.Pos).GetSafeNormal() * Unit.Speed * DeltaSeconds;
	for (const ASeleneLaneUnit* Other : Units)   // keep units from stacking on one spot
	{
		if (!Other || Other == &Unit || !Other->IsAlive()) continue;
		const FVector2D Away = Unit.Pos - Other->Pos;
		const float Min = Unit.Radius + Other->Radius;
		const float DistSq = Away.SizeSquared();
		if (DistSq < Min * Min && DistSq > 1.f)
		{
			const float Dist = FMath::Sqrt(DistSq);
			Step += Away / Dist * FMath::Min(Min - Dist, Unit.Speed * DeltaSeconds);
		}
	}
	Unit.Pos += Step;
	Unit.S = Path.Project(Unit.Pos);
	Unit.Play(Unit.MoveAnim, true);
	if (!Step.IsNearlyZero()) Place(Unit, FMath::RadiansToDegrees(FMath::Atan2(Goal.Y - Unit.Pos.Y, Goal.X - Unit.Pos.X)));
}

void ASeleneLaneDirector::DrawHealth() const
{
	const APlayerController* PC = GetWorld()->GetFirstPlayerController();
	const APawn* Pawn = PC ? PC->GetPawn() : nullptr;
	if (!Pawn) return;
	const FVector2D Eye(Pawn->GetActorLocation());
	const FVector Right = PC->GetControlRotation().RotateVector(FVector::RightVector);
	for (const ASeleneLaneUnit* Unit : Units)
	{
		if (!Unit || !Unit->IsAlive() || Unit->Health >= Unit->MaxHealth) continue;
		if (FVector2D::DistSquared(Eye, Unit->Pos) > FMath::Square(4000.f)) continue;
		const float Half = Unit->bStructure ? 120.f : 45.f;
		const FVector Mid(Unit->Pos.X, Unit->Pos.Y, Unit->HalfHeight * 2.f + 40.f);
		const FVector A = Mid - Right * Half, B = Mid + Right * Half;
		DrawDebugLine(GetWorld(), A, B, FColor(40, 40, 40), false, -1.f, 0, 6.f);
		DrawDebugLine(GetWorld(), A, FMath::Lerp(A, B, Unit->Health / Unit->MaxHealth),
			Unit->Team == ESeleneTeam::Dawn ? FColor(255, 210, 60) : FColor(180, 100, 255), false, -1.f, 0, 6.f);
	}
}

void ASeleneLaneDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (Paths.IsEmpty()) { LogStats(DeltaSeconds); return; }
	const double TickStart = FPlatformTime::Seconds();
	ON_SCOPE_EXIT { StatDirector += FPlatformTime::Seconds() - TickStart; };
	Clock += DeltaSeconds;
	if (!bGameOver && CVarLaneWaves.GetValueOnGameThread() != 0 && Clock >= NextWave)
	{
		NextWave += FMath::Max(WaveInterval, 1.f);
		SpawnWave();
	}
	if (const int32 Stress = CVarLaneStress.GetValueOnGameThread(); Stress != LastStress)
	{
		if (Stress > LastStress) SpawnStress(Stress - LastStress);
		LastStress = Stress;
	}
	for (int32 Budget = 2; Budget > 0 && Pending.Num(); --Budget)   // spread a wave over a few frames
	{
		const FPendingSpawn Next = Pending.Pop(EAllowShrinking::No);
		SpawnUnit(Next.Kind, Next.Team, Next.Lane, Next.At, Next.S, Next.Lateral);
	}
	for (int32 i = Units.Num() - 1; i >= 0; --i)
	{
		ASeleneLaneUnit* Unit = Units[i];
		if (!Unit) { Units.RemoveAtSwap(i); continue; }
		if (!Unit->IsAlive())
		{
			Unit->DeadTime += DeltaSeconds;
			if (Unit->DeadTime > CorpseSeconds) { Unit->Destroy(); Units.RemoveAtSwap(i); }
			continue;
		}
		if (!bGameOver) TickUnit(*Unit, DeltaSeconds);
	}
	if (!bExecDone)
	{
		FString When, Command;
		if (CVarLaneExecAt.GetValueOnGameThread().Split(TEXT(":"), &When, &Command) && Clock >= FCString::Atof(*When))
		{
			bExecDone = true;
			if (APlayerController* PC = GetWorld()->GetFirstPlayerController()) PC->ConsoleCommand(Command);
		}
	}
	if (CVarLaneHealth.GetValueOnGameThread() != 0) DrawHealth();
	if (const float Hold = CVarLaneTour.GetValueOnGameThread(); Hold > 0.f) TickTour(Hold, DeltaSeconds);
	LogStats(DeltaSeconds);
}

void ASeleneLaneDirector::TickTour(float Hold, float DeltaSeconds)
{
	APlayerController* PC = GetWorld()->GetFirstPlayerController();
	if (!PC) return;
	if (TourStops.IsEmpty())
	{
		TourStops.Add(FTransform(FRotator(-90, 90, 0), FVector(0, 0, 21000)));
		TourStops.Add(FTransform(FRotator(-90, 90, 0), FVector(-8000, 0, 9000)));
		TourStops.Add(FTransform(FRotator(-35, 0, 0), FVector(DawnBase.X - 3000, DawnBase.Y, 2500)));
		for (const FPath& Path : Paths)
		{
			for (const float Fraction : { 0.12f, 0.3f, 0.5f, 0.7f })
			{
				FVector2D Tangent;
				const FVector2D At = Path.At(Path.Length * Fraction, &Tangent);
				TourStops.Add(FTransform(FRotator(-6, FMath::RadiansToDegrees(FMath::Atan2(Tangent.Y, Tangent.X)), 0), FVector(At.X, At.Y, 320)));
			}
		}
		TourCamera = GetWorld()->SpawnActor<ACameraActor>(ACameraActor::StaticClass(), TourStops[0]);
		TourCamera->GetCameraComponent()->bConstrainAspectRatio = false;
		TourCamera->GetCameraComponent()->SetFieldOfView(90.f);
		PC->SetViewTarget(TourCamera);
		TourTime = 0.f; TourIndex = 0; bTourShot = false;
	}
	if (TourIndex >= TourStops.Num() || !TourCamera) return;
	TourCamera->SetActorTransform(TourStops[TourIndex]);
	TourTime += DeltaSeconds;
	if (!bTourShot && TourTime >= Hold * 0.7f)
	{
		bTourShot = true;
		FScreenshotRequest::RequestScreenshot(FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir() / FString::Printf(TEXT("LanesMap/tour/%02d.png"), TourIndex)), false, false);
	}
	if (TourTime >= Hold)
	{
		TourTime = 0.f; bTourShot = false; ++TourIndex;
		if (TourIndex >= TourStops.Num()) { PC->SetViewTarget(PC->GetPawn()); UE_LOG(LogSelene, Log, TEXT("Lanes: tour finished.")); }
	}
}

void ASeleneLaneDirector::LogStats(float DeltaSeconds)
{
	if (const float Every = CVarLaneLog.GetValueOnGameThread(); Every > 0.f)
	{
		StatTime += DeltaSeconds; ++StatFrames; StatWorst = FMath::Max(StatWorst, DeltaSeconds);
		if (StatTime >= Every)
		{
			UE_LOG(LogSelene, Log, TEXT("LaneStats t=%.0f minions=%d units=%d fps_avg=%.1f fps_worst=%.1f game_ms=%.1f render_ms=%.1f gpu_ms=%.1f director_ms=%.2f"),
				Clock, CountMinions(), Units.Num(), StatFrames / StatTime, 1.f / FMath::Max(StatWorst, 0.0001f),
				FPlatformTime::ToMilliseconds(GGameThreadTime), FPlatformTime::ToMilliseconds(GRenderThreadTime),
				FPlatformTime::ToMilliseconds(RHIGetGPUFrameCycles()), StatDirector / FMath::Max(StatFrames, 1) * 1000.0);
			StatDirector = 0.0;
			StatTime = 0.f; StatFrames = 0; StatWorst = 0.f;
		}
	}
}

void ASeleneLaneDirector::EndPlay(const EEndPlayReason::Type Reason)
{
	for (const TPair<FString, int32>& Saved : SavedCVars)
	{
		if (IConsoleVariable* Var = IConsoleManager::Get().FindConsoleVariable(*Saved.Key)) Var->Set(Saved.Value, ECVF_SetByConsole);
	}
	SavedCVars.Reset();
	Super::EndPlay(Reason);
}
