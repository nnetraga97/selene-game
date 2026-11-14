#include "Lanes/SeleneLaneDirector.h"

#include "Selene.h"
#include "SeleneCharacter.h"
#include "Combat/SeleneCombat.h"
#include "Movement/SeleneMovementComponent.h"
#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Particles/ParticleSystemComponent.h"
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
	TAutoConsoleVariable<int32> CVarLaneHealth(TEXT("selene.LaneHealthBars"), 0,
		TEXT("Debug: draws the old debug-line health bars (the HUD draws the real ones)."));
	TAutoConsoleVariable<float> CVarLaneTour(TEXT("selene.LaneTour"), 0.f,
		TEXT("Debug: > 0 moves the view through fixed map viewpoints, N seconds each, saving Saved/LanesMap/tour/NN.png."));
	TAutoConsoleVariable<FString> CVarLaneExecAt(TEXT("selene.LaneExecAt"), TEXT(""),
		TEXT("Debug: 'seconds:command' runs that console command once at that map time (for example 30:ProfileGPU)."));
	TAutoConsoleVariable<int32> CVarLaneFastRender(TEXT("selene.LaneFastRender"), 1,
		TEXT("1: lane maps turn Lumen GI and reflections off and hold the time of day, for frame rate. Read when the map starts."));
	TAutoConsoleVariable<int32> CVarLaneWaves(TEXT("selene.LaneWaves"), 1,
		TEXT("0 stops new minion waves."));
	TAutoConsoleVariable<FString> CVarLaneScript(TEXT("selene.LaneScript"), TEXT(""),
		TEXT("Debug: 'seconds:command;seconds:command' runs each console command once at that map time (test runs)."));

	FAutoConsoleCommandWithWorldAndArgs GoToCommand(TEXT("selene.GoTo"),
		TEXT("Debug: selene.GoTo <north|mid|south> <fraction 0..1 from the Dawn base> - moves the player there, facing Dusk."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			ASeleneLaneDirector* Director = ASeleneLaneDirector::Get(World);
			APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;
			if (!Director || !PC || !PC->GetPawn() || Args.Num() < 2) return;
			Director->DebugTeleport(*PC->GetPawn(), FName(*Args[0]), FCString::Atof(*Args[1]));
		}));

	FAutoConsoleCommandWithWorldAndArgs AbilityCommand(TEXT("selene.Ability"),
		TEXT("Debug: selene.Ability <0|1|2> casts the player's Q/E/R ability toward the crosshair."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;
			if (ASeleneCharacter* Hero = PC ? Cast<ASeleneCharacter>(PC->GetPawn()) : nullptr; Hero && Args.Num())
			{
				Hero->UseAbility(FCString::Atoi(*Args[0]));
			}
		}));

	ASeleneCharacter* PlayerHero(UWorld* World)
	{
		APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;
		return PC ? Cast<ASeleneCharacter>(PC->GetPawn()) : nullptr;
	}
	FAutoConsoleCommandWithWorldAndArgs MoveCommand(TEXT("selene.Move"),
		TEXT("Debug: selene.Move <forward -1..1> <right -1..1> <seconds> holds that movement input on the player."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (ASeleneCharacter* Hero = PlayerHero(World); Hero && Args.Num() >= 3) Hero->DebugMove(FCString::Atof(*Args[0]), FCString::Atof(*Args[1]), FCString::Atof(*Args[2]));
		}));
	FAutoConsoleCommandWithWorldAndArgs DashCommand(TEXT("selene.Dash"), TEXT("Debug: the player dashes (as Shift)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>&, UWorld* World)
		{
			if (ASeleneCharacter* Hero = PlayerHero(World)) if (auto* M = Cast<USeleneMovementComponent>(Hero->GetCharacterMovement())) M->TryDash();
		}));
	FAutoConsoleCommandWithWorldAndArgs SlideCommand(TEXT("selene.Slide"), TEXT("Debug: selene.Slide 1|0 starts or stops a slide (as Ctrl)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (ASeleneCharacter* Hero = PlayerHero(World)) if (auto* M = Cast<USeleneMovementComponent>(Hero->GetCharacterMovement()))
			{
				if (Args.Num() && FCString::Atoi(*Args[0]) != 0) M->TrySlide(); else M->StopSlide();
			}
		}));
	FAutoConsoleCommandWithWorldAndArgs AttackCommand(TEXT("selene.Attack"), TEXT("Debug: one primary-fire press (as left mouse)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>&, UWorld* World)
		{
			if (ASeleneCharacter* Hero = PlayerHero(World)) { Hero->Attack(); Hero->StopAttack(); }
		}));

	FAutoConsoleCommandWithWorldAndArgs BreakCommand(TEXT("selene.Break"),
		TEXT("Debug: selene.Break <dawn|dusk> <north|mid|south> <guardian|walker> destroys that structure."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			if (ASeleneLaneDirector* Director = ASeleneLaneDirector::Get(World); Director && Args.Num() >= 3)
			{
				Director->DebugBreak(Args[0].Equals(TEXT("dawn"), ESearchCase::IgnoreCase) ? ESeleneTeam::Dawn : ESeleneTeam::Dusk, FName(*Args[1]),
					Args[2].Equals(TEXT("walker"), ESearchCase::IgnoreCase) ? ESeleneUnitKind::Walker : ESeleneUnitKind::Guardian);
			}
		}));

	FAutoConsoleCommandWithWorldAndArgs PitchCommand(TEXT("selene.Pitch"),
		TEXT("Debug: selene.Pitch <degrees> [yaw offset] sets the player's camera pitch (and turns by the yaw offset)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;
			if (!PC || !Args.Num()) return;
			FRotator R = PC->GetControlRotation();
			R.Pitch = FCString::Atof(*Args[0]);
			if (Args.Num() > 1) R.Yaw += FCString::Atof(*Args[1]);
			PC->SetControlRotation(R);
		}));

	FAutoConsoleCommandWithWorldAndArgs AimCommand(TEXT("selene.Aim"),
		TEXT("Debug: selene.Aim 0|1 holds or releases the player's aim (combat stance)."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;
			if (ASeleneCharacter* Hero = PC ? Cast<ASeleneCharacter>(PC->GetPawn()) : nullptr; Hero && Args.Num()) Hero->SetAiming(FCString::Atoi(*Args[0]) != 0);
		}));

	TAutoConsoleVariable<float> CVarLaneRestart(TEXT("selene.LaneRestartDelay"), 15.f,
		TEXT("Seconds after a Patron falls before the match restarts (0 = never)."));

	struct FKindSpec
	{
		const TCHAR* DawnMesh; const TCHAR* DuskMesh;
		const TCHAR* Move; const TCHAR* Attack; const TCHAR* Death; const TCHAR* Idle;
		const TCHAR* HitReacts[4];   // front, back, left, right
		const TCHAR* ExtraDeaths[2];
		float Scale, Radius, HalfHeight, Health, Damage, Range, Period, Speed;
		bool bStructure;
		/** Seconds into the attack loop at which the blow or shot leaves (fraction of the period). */
		float ShotFraction;
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
			  { ANIM TEXT("Melee/HitReact_Front"), ANIM TEXT("Melee/HitReact_Back"), ANIM TEXT("Melee/HitReact_Left"), ANIM TEXT("Melee/HitReact_Right") },
			  { ANIM TEXT("Melee/Death_B"), ANIM TEXT("Melee/Death_C") },
			  1.f, 45.f, 90.f, 300.f, 24.f, 190.f, 1.0f, 420.f, false, 0.45f },
			// Ranged
			{ DOWN_MESH TEXT("Minion_Lane_Ranged_Dawn"), DUSK_MESH TEXT("Minion_Lane_Ranged_Dusk"),
			  ANIM TEXT("Ranged/Jog_Fwd_Combat_A"), ANIM TEXT("Ranged/Fire_A"), ANIM TEXT("Ranged/Death_Front_A"), ANIM TEXT("Ranged/Idle_A"),
			  { ANIM TEXT("Ranged/HitReact_Front_A"), ANIM TEXT("Ranged/HitReact_Back_A"), ANIM TEXT("Ranged/HitReact_Left_A"), ANIM TEXT("Ranged/HitReact_Right_A") },
			  { ANIM TEXT("Ranged/Death_Front_B"), ANIM TEXT("Ranged/Death_Back_A") },
			  1.f, 45.f, 90.f, 200.f, 18.f, 1100.f, 1.2f, 420.f, false, 0.3f },
			// Siege
			{ DOWN_MESH TEXT("Minion_Lane_Siege_Dawn"), DUSK_MESH TEXT("Minion_Lane_Siege_Dusk"),
			  ANIM TEXT("Siege/Jog_Fwd_Combat"), ANIM TEXT("Siege/Fire_A"), ANIM TEXT("Siege/Death_A"), ANIM TEXT("Siege/Idle"),
			  { ANIM TEXT("Siege/HitReact_Front"), ANIM TEXT("Siege/HitReact_Back"), ANIM TEXT("Siege/HitReact_Left"), ANIM TEXT("Siege/HitReact_Right") },
			  { ANIM TEXT("Siege/Death_B"), ANIM TEXT("Siege/Death_C") },
			  1.f, 70.f, 100.f, 700.f, 60.f, 1400.f, 2.5f, 350.f, false, 0.3f },
			// Guardian (placeholder: Super minion)
			{ DOWN_MESH TEXT("Minion_Lane_Super_Dawn"), DUSK_MESH TEXT("Minion_Lane_Super_Dusk"),
			  ANIM TEXT("Super/Idle"), ANIM TEXT("Super/Attack_A"), ANIM TEXT("Super/Death_Front"), ANIM TEXT("Super/Idle"),
			  { nullptr, nullptr, nullptr, nullptr }, { nullptr, nullptr },
			  1.8f, 130.f, 220.f, 2500.f, 70.f, 1300.f, 1.0f, 0.f, true, 0.4f },
			// Walker (placeholder: Siege minion, planted)
			{ DOWN_MESH TEXT("Minion_Lane_Siege_Dawn"), DUSK_MESH TEXT("Minion_Lane_Siege_Dusk"),
			  ANIM TEXT("Siege/Idle_Planted"), ANIM TEXT("Siege/Fire_Planted"), ANIM TEXT("Siege/Death_A"), ANIM TEXT("Siege/Idle_Planted"),
			  { nullptr, nullptr, nullptr, nullptr }, { nullptr, nullptr },
			  2.4f, 190.f, 260.f, 5000.f, 120.f, 1500.f, 1.5f, 0.f, true, 0.3f },
			// Patron (placeholder: Prime Helix)
			{ HELIX TEXT("Meshes/Prime_Helix"), HELIX TEXT("Meshes/Prime_Helix"),
			  HELIX TEXT("Animations/Idle"), HELIX TEXT("Animations/Primary_Fire"), HELIX TEXT("Animations/Death"), HELIX TEXT("Animations/Idle"),
			  { nullptr, nullptr, nullptr, nullptr }, { nullptr, nullptr },
			  1.f, 300.f, 350.f, 9000.f, 150.f, 1600.f, 1.2f, 0.f, true, 0.4f },
			// Base Guardian (placeholder: Super minion, smaller): a pair in front of each base
			{ DOWN_MESH TEXT("Minion_Lane_Super_Dawn"), DUSK_MESH TEXT("Minion_Lane_Super_Dusk"),
			  ANIM TEXT("Super/Idle"), ANIM TEXT("Super/Attack_A"), ANIM TEXT("Super/Death_Front"), ANIM TEXT("Super/Idle"),
			  { nullptr, nullptr, nullptr, nullptr }, { nullptr, nullptr },
			  1.5f, 110.f, 185.f, 2000.f, 60.f, 1200.f, 1.0f, 0.f, true, 0.4f },
			// Shrine (placeholder: Prime Helix, small, passive): two per base, guard the Patron
			{ HELIX TEXT("Meshes/Prime_Helix"), HELIX TEXT("Meshes/Prime_Helix"),
			  HELIX TEXT("Animations/Idle"), HELIX TEXT("Animations/Idle"), HELIX TEXT("Animations/Death"), HELIX TEXT("Animations/Idle"),
			  { nullptr, nullptr, nullptr, nullptr }, { nullptr, nullptr },
			  0.55f, 170.f, 195.f, 3500.f, 0.f, 0.f, 1.0f, 0.f, true, 0.4f },
		};
		return Specs[static_cast<int32>(Kind)];
	}

	const TCHAR* const FxMinionShot = TEXT("/Game/ParagonMinions/FX/Particles/Minions/Prime_Helix/Abilities/SpecialAttack1/FX/P_Prime_Helix_SpecialAttack1_Projectile.P_Prime_Helix_SpecialAttack1_Projectile");
	const TCHAR* const FxStructureShot = TEXT("/Game/ParagonMinions/FX/Particles/Minions/Dragon/FX/P_Dragon_Fireball_Projectile.P_Dragon_Fireball_Projectile");
	const TCHAR* const FxShotImpact = TEXT("/Game/ParagonMinions/FX/Particles/Minions/Dragon/FX/P_Dragon_FireBall_CharacterImpact.P_Dragon_FireBall_CharacterImpact");
	const TCHAR* const FxMeleeImpact = TEXT("/Game/ParagonMinions/FX/Particles/Minions/Shared/P_Minion_Melee_Impact.P_Minion_Melee_Impact");
	const TCHAR* const FxMuzzle = TEXT("/Game/ParagonMinions/FX/Particles/Minions/Shared/P_MinionMuzzle.P_MinionMuzzle");
	const TCHAR* const FxSiegeMuzzle = TEXT("/Game/ParagonMinions/FX/Particles/Minions/Shared/P_Minion_Seige_Muzzle.P_Minion_Seige_Muzzle");
	const TCHAR* const FxMinionDeath = TEXT("/Game/ParagonMinions/FX/Particles/Minions/Minion_melee/FX/Death/P_MeleeMinion_Chunks_Ranged.P_MeleeMinion_Chunks_Ranged");
	const TCHAR* const FxStructureDeath = TEXT("/Game/ParagonMinions/FX/Particles/Minions/Minion_Super/FX/Death/P_SuperMinion_Chunks.P_SuperMinion_Chunks");
	const TCHAR* const FxPatronDeath = TEXT("/Game/ParagonMinions/FX/Particles/Minions/Prime_Helix/Abilities/SpecialAttack2/FX/P_PH_Shockwave.P_PH_Shockwave");
	const TCHAR* const FxSpawn = TEXT("/Game/ParagonMinions/FX/Particles/Minions/Shared/P_MinionSpawn.P_MinionSpawn");
	const TCHAR* const FxStun = TEXT("/Game/ParagonMinions/FX/Particles/SharedGameplay/States/Stun/P_StunnedLoop.P_StunnedLoop");
	const TCHAR* const FxShielded = TEXT("/Game/ParagonMinions/FX/Particles/Minions/Prime_Helix/Abilities/SpecialAttack2/FX/P_PH_Bubble.P_PH_Bubble");

	template <typename T> T* LoadAsset(const TCHAR* Path)
	{
		if (!Path) return nullptr;
		const FString Full = FString(Path) + TEXT(".") + FPaths::GetBaseFilename(Path);
		T* Asset = LoadObject<T>(nullptr, *Full);
		if (!Asset) UE_LOG(LogSelene, Warning, TEXT("Lanes: could not load %s"), *Full);
		return Asset;
	}

	const float AggroRange = 1200.f;
	const float HeroNoticeRange = 700.f;     // minions turn on a hero this close when nothing else is nearer
	const float CorpseSeconds = 3.f;
	const TCHAR* KindName(ESeleneUnitKind Kind)
	{
		static const TCHAR* Names[] = { TEXT("Trooper"), TEXT("Ranged trooper"), TEXT("Siege trooper"), TEXT("Guardian"), TEXT("Walker"), TEXT("Patron"), TEXT("Base Guardian"), TEXT("Shrine") };
		return Names[static_cast<int32>(Kind)];
	}
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
	if (Paths.IsEmpty()) return;
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
	if (USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(this))
	{
		Combat->Announce(TEXT("Push a lane: Guardian, Walker, then the Base Guardians, Shrines and Patron"), FLinearColor(1.f, 0.85f, 0.35f), 7.f);
	}
	UE_LOG(LogSelene, Log, TEXT("Lanes: %d lanes, %d structures, wave every %.0fs (%d melee + %d ranged)."),
		Paths.Num(), Units.Num(), WaveInterval, MeleePerWave, RangedPerWave);
}

float ASeleneLaneDirector::TraceGround(const FVector2D& At, float Above, float Fallback) const
{
	FHitResult Hit;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(SeleneLaneGround), false);
	FCollisionObjectQueryParams Objects(ECC_WorldStatic);
	if (GetWorld()->LineTraceSingleByObjectType(Hit, FVector(At.X, At.Y, Above), FVector(At.X, At.Y, Above - 2500.f), Objects, Params))
	{
		return Hit.ImpactPoint.Z;
	}
	return Fallback;
}

ASeleneLaneUnit* ASeleneLaneDirector::SpawnUnit(ESeleneUnitKind Kind, ESeleneTeam Team, int32 Lane, const FVector2D& At, float S, float Lateral, float Power)
{
	const FKindSpec& K = Spec(Kind);
	USkeletalMesh* MeshAsset = LoadAsset<USkeletalMesh>(Team == ESeleneTeam::Dawn ? K.DawnMesh : K.DuskMesh);
	if (!MeshAsset) return nullptr;
	const float Ground = TraceGround(At, 1500.f, 0.f);
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	ASeleneLaneUnit* Unit = GetWorld()->SpawnActor<ASeleneLaneUnit>(ASeleneLaneUnit::StaticClass(), FTransform(FVector(At.X, At.Y, Ground + K.HalfHeight)), Params);
	if (!Unit) return nullptr;
	Unit->Team = Team; Unit->Kind = Kind; Unit->Lane = Lane; Unit->bStructure = K.bStructure;
	Unit->Pos = At; Unit->S = S; Unit->Lateral = Lateral; Unit->Z = Ground;
	Unit->Radius = K.Radius; Unit->HalfHeight = K.HalfHeight;
	Unit->Health = Unit->MaxHealth = K.Health * Power;
	Unit->Damage = K.Damage * Power; Unit->Range = K.Range; Unit->AttackPeriod = K.Period; Unit->Speed = K.Speed;
	Unit->AttackTimer = FMath::FRandRange(0.f, K.Period);
	Unit->Capsule->SetCapsuleSize(K.Radius, K.HalfHeight);
	if (K.bStructure)
	{
		Unit->Capsule->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);  // heroes walk round structures
	}
	// Heroes' aim traces and projectiles find units on Visibility.
	Unit->Capsule->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	Unit->Mesh->SetSkeletalMeshAsset(MeshAsset);
	Unit->Mesh->SetRelativeLocationAndRotation(FVector(0, 0, -K.HalfHeight), FRotator(0, -90, 0));
	Unit->Mesh->SetRelativeScale3D(FVector(K.Scale));
	Unit->BaseScale = K.Scale;
	Unit->MoveAnim = LoadAsset<UAnimSequence>(K.Move);
	Unit->AttackAnim = LoadAsset<UAnimSequence>(K.Attack);
	// Some Paragon fire clips are additive (a single-node mesh can't play them): try the sibling fire clips.
	if (Unit->AttackAnim && Unit->AttackAnim->IsValidAdditive())
	{
		const FString Dir = FPaths::GetPath(FString(K.Attack));
		UAnimSequence* Found = nullptr;
		for (const TCHAR* Alt : { TEXT("Fire_B"), TEXT("Fire_A_1"), TEXT("Fire_A_2"), TEXT("Fire_C") })
		{
			const FString Path = Dir / Alt;
			UAnimSequence* Clip = LoadObject<UAnimSequence>(nullptr, *(Path + TEXT(".") + Alt), nullptr, LOAD_Quiet | LOAD_NoWarn);
			if (Clip && !Clip->IsValidAdditive()) { Found = Clip; break; }
		}
		Unit->AttackAnim = Found;
	}
	Unit->DeathAnim = LoadAsset<UAnimSequence>(K.Death);
	Unit->IdleAnim = LoadAsset<UAnimSequence>(K.Idle);
	// Additive reacts can't play on a single-node mesh; those units stagger procedurally instead.
	for (const TCHAR* Path : K.HitReacts)
	{
		if (UAnimSequence* React = Path ? LoadAsset<UAnimSequence>(Path) : nullptr; React && !React->IsValidAdditive()) Unit->HitReactAnims.Add(React);
	}
	Unit->DeathAnims.Add(Unit->DeathAnim);
	for (const TCHAR* Path : K.ExtraDeaths) if (Path) if (UAnimSequence* Extra = LoadAsset<UAnimSequence>(Path)) Unit->DeathAnims.Add(Extra);
	if (!Unit->AttackAnim) Unit->AttackAnim = Unit->IdleAnim;
	Unit->Play(K.bStructure ? Unit->IdleAnim : Unit->MoveAnim, true);
	Place(*Unit, Team == ESeleneTeam::Dawn ? 0.f : 180.f);
	if (!K.bStructure)
	{
		if (USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(this)) Combat->SpawnFx(FxSpawn, FVector(At.X, At.Y, Ground), FRotator::ZeroRotator, 0.6f);
	}
	Units.Add(Unit);
	return Unit;
}

void ASeleneLaneDirector::Place(ASeleneLaneUnit& Unit, float FaceYaw)
{
	Unit.SetActorLocationAndRotation(Unit.Center(), FRotator(0, FaceYaw, 0), false, nullptr, ETeleportType::TeleportPhysics);
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
	// Base layer: two Base Guardians at the front of each base plaza, two Shrines beside the Patron.
	for (const ESeleneTeam Team : { ESeleneTeam::Dawn, ESeleneTeam::Dusk })
	{
		const FVector2D Base = FVector2D(Team == ESeleneTeam::Dawn ? DawnBase : DuskBase);
		const FVector2D Fwd = (FVector2D::ZeroVector - Base).GetSafeNormal();   // toward the map centre
		const FVector2D Side(-Fwd.Y, Fwd.X);
		for (const float S : { -1.f, 1.f })
		{
			SpawnUnit(ESeleneUnitKind::BaseGuardian, Team, INDEX_NONE, Base + Fwd * 1450.f + Side * S * 650.f, 0.f, 0.f);
			SpawnUnit(ESeleneUnitKind::Shrine, Team, INDEX_NONE, Base + Fwd * 450.f + Side * S * 950.f, 0.f, 0.f);
		}
	}
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
			// Deadlock-style: waves stay symmetric. A broken enemy structure only moves this team's wave forward (it starts
			// further up the lane, like the zipline being pushed), so the fight settles nearer the enemy instead of mid.
			// Troopers get stronger only once the enemy has lost a Shrine (the late game, meant to end it).
			float Start = Team == ESeleneTeam::Dawn ? 2600.f : Path.Length - 2600.f;   // the lane mouth at the base plaza edge
			bool bEnemyShrineDown = false;
			for (const ASeleneLaneUnit* Unit : Units)
			{
				if (!Unit || !Unit->bStructure || Unit->IsAlive() || Unit->Team == Team) continue;
				if (Unit->Kind == ESeleneUnitKind::Shrine) bEnemyShrineDown = true;
				// The wave enters at the farthest broken enemy structure in this lane.
				if (Unit->Lane == Lane) Start = Dir > 0.f ? FMath::Max(Start, Unit->S - 1200.f) : FMath::Min(Start, Unit->S + 1200.f);
			}
			const float Power = bEnemyShrineDown ? 1.35f : 1.f;
			const int32 Melee = MeleePerWave;
			const int32 Count = Melee + RangedPerWave + (bSiege ? 1 : 0);
			for (int32 i = 0; i < Count; ++i)
			{
				const ESeleneUnitKind Kind = i < Melee ? ESeleneUnitKind::Melee
					: i < Melee + RangedPerWave ? ESeleneUnitKind::Ranged : ESeleneUnitKind::Siege;
				const bool bFront = Kind == ESeleneUnitKind::Melee;
				const float Lateral = bFront ? (i - (Melee - 1) * 0.5f) * 160.f : (i - Melee) * 220.f - 110.f;
				const float S = Start - Dir * (bFront ? 0.f : 260.f);
				FVector2D Tangent;
				const FVector2D Centre = Path.At(S, &Tangent);
				Pending.Add({ Kind, Team, Lane, Centre + FVector2D(-Tangent.Y, Tangent.X) * Lateral, S, Lateral, Power });
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
			Pending.Add({ ESeleneUnitKind::Melee, Team, Lane, Centre + FVector2D(-Tangent.Y, Tangent.X) * Lateral, S, Lateral, 1.f });
		}
	}
	UE_LOG(LogSelene, Log, TEXT("Lanes: stress spawned %d per team, %d minions alive."), PerTeam, CountMinions());
}

bool ASeleneLaneDirector::IsProtected(const ASeleneLaneUnit& Unit) const
{
	// Ladder: lane Guardian -> that lane's Walker -> (any Walker down) Base Guardians -> (both down) Shrines ->
	// (both down) Patron.
	if (!Unit.bStructure || Unit.Kind == ESeleneUnitKind::Guardian) return false;
	auto AnyAlive = [&](ESeleneUnitKind Kind, int32 Lane)
	{
		for (const ASeleneLaneUnit* Other : Units)
		{
			if (Other && Other->IsAlive() && Other->Team == Unit.Team && Other->Kind == Kind && (Lane == INDEX_NONE || Other->Lane == Lane)) return true;
		}
		return false;
	};
	auto AnyDead = [&](ESeleneUnitKind Kind)
	{
		for (const ASeleneLaneUnit* Other : Units)
		{
			if (Other && !Other->IsAlive() && Other->Team == Unit.Team && Other->Kind == Kind) return true;
		}
		return false;
	};
	switch (Unit.Kind)
	{
	case ESeleneUnitKind::Walker: return AnyAlive(ESeleneUnitKind::Guardian, Unit.Lane);
	case ESeleneUnitKind::BaseGuardian: return !AnyDead(ESeleneUnitKind::Walker);
	case ESeleneUnitKind::Shrine: return AnyAlive(ESeleneUnitKind::BaseGuardian, INDEX_NONE);
	case ESeleneUnitKind::Patron: return AnyAlive(ESeleneUnitKind::Shrine, INDEX_NONE);
	default: return false;
	}
}

FSeleneTarget ASeleneLaneDirector::FindTarget(const ASeleneLaneUnit& Unit, float MaxDistance) const
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
	// Heroes: a hero who just hurt an ally is chased; otherwise a hero is fair game when nearer than any trooper.
	// Structures shoot heroes only when no enemy trooper is in range (stand behind your minions to siege).
	ASeleneCharacter* BestHero = nullptr;
	float BestHeroDist = TNumericLimits<float>::Max();
	if (const USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(this))
	{
		Combat->ForEachHero([&](ASeleneCharacter& Hero)
		{
			if (!Hero.IsCombatAlive() || Hero.GetTeam() == Unit.Team) return;
			const FVector HeroLoc = Hero.GetActorLocation();
			if (FMath::Abs(HeroLoc.Z - Unit.Center().Z) > 900.f) return;
			const float Dist = FVector2D::Distance(Unit.Pos, FVector2D(HeroLoc)) - 40.f - Unit.Radius;
			const bool bAggro = Unit.HeroAggroTimer > 0.f && Unit.AggroHero.Get() == &Hero;
			const float Reach = Unit.bStructure ? Unit.Range : (bAggro ? AggroRange : HeroNoticeRange);
			if (Dist > Reach || Dist >= BestHeroDist) return;
			if (Unit.bStructure && Best && !Best->bStructure) return;
			if (!Unit.bStructure && !bAggro && Best && BestDist < Dist) return;
			BestHero = &Hero; BestHeroDist = Dist;
		});
	}
	if (BestHero) return FSeleneTarget(BestHero);
	return Best ? FSeleneTarget(Best) : FSeleneTarget();
}

void ASeleneLaneDirector::DrawAggro(ESeleneTeam Team, ASeleneCharacter* Hero, const FVector& Where)
{
	if (!Hero) return;
	for (ASeleneLaneUnit* Unit : Units)
	{
		if (!Unit || Unit->bStructure || !Unit->IsAlive() || Unit->Team != Team) continue;
		if (FVector2D::DistSquared(Unit->Pos, FVector2D(Where)) > FMath::Square(AggroRange)) continue;
		Unit->HeroAggroTimer = 3.f;
		Unit->AggroHero = Hero;
	}
}

float ASeleneLaneDirector::DamageUnit(ASeleneLaneUnit& Target, float Amount, const FVector& From, AActor* Instigator)
{
	if (!Target.IsAlive() || Amount <= 0.f) return 0.f;
	USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(this);
	if (IsProtected(Target))
	{
		if (Combat && !Target.StateFx.IsValid())
		{
			UParticleSystemComponent* Fx = Combat->SpawnFx(FxShielded, Target.Center(), FRotator::ZeroRotator, Target.Radius / 120.f);
			Target.StateFx = Fx;
		}
		return 0.f;
	}
	// Structures resist troopers (Deadlock's Guardians do too): waves alone grind a structure slowly and it heals
	// back between waves; a hero is what breaks it.
	const ASeleneLaneUnit* FromUnit = Cast<ASeleneLaneUnit>(Instigator);
	if (Target.bStructure && FromUnit && !FromUnit->bStructure) Amount *= TrooperVsStructure;
	if (Target.bStructure && Cast<ASeleneCharacter>(Instigator)) Target.LastHeroHitTime = Clock;
	Target.Health -= Amount;
	if (ASeleneCharacter* Hero = Cast<ASeleneCharacter>(Instigator)) DrawAggro(Target.Team, Hero, Target.Center());
	if (Target.Health > 0.f)
	{
		// Troopers stagger: a directional flinch clip when one exists, otherwise a knock back with a brief freeze.
		if (!Target.bStructure && Target.HitReactTimer <= 0.f && Target.StunTimer <= 0.f)
		{
			const FVector Fwd = Target.GetActorForwardVector();
			const FVector To = (From - Target.Center()).GetSafeNormal2D();
			const float F = FVector::DotProduct(Fwd, To), R = FVector::DotProduct(FVector::CrossProduct(FVector::UpVector, Fwd), To);
			const int32 Index = FMath::Abs(F) >= FMath::Abs(R) ? (F >= 0.f ? 0 : 1) : (R >= 0.f ? 3 : 2);
			if (Target.HitReactAnims.Num() == 4 && Target.HitReactAnims[Index])
			{
				Target.CurrentAnim = nullptr;
				Target.Play(Target.HitReactAnims[Index], false);
				Target.HitReactTimer = FMath::Min(Target.HitReactAnims[Index]->GetPlayLength(), 0.45f);
			}
			else
			{
				const float Push = Cast<ASeleneCharacter>(Instigator) ? 45.f : 12.f;
				Target.Pos -= FVector2D(To) * Push;
				Target.HitReactTimer = Cast<ASeleneCharacter>(Instigator) ? 0.18f : 0.06f;
				Target.Mesh->GlobalAnimRateScale = 0.1f;
				Target.Mesh->SetRelativeScale3D(FVector(Target.BaseScale * 1.08f, Target.BaseScale * 1.08f, Target.BaseScale * 0.95f));   // squash pop
				Place(Target, Target.GetActorRotation().Yaw);
			}
		}
		return Amount;
	}
	Kill(Target, From);
	return Amount + Target.Health;   // Health is now <= 0
}

void ASeleneLaneDirector::Kill(ASeleneLaneUnit& Target, const FVector& From)
{
	Target.Health = 0.f;
	Target.DeadTime = 0.f;
	Target.CurrentAnim = nullptr;
	UAnimSequence* Death = Target.DeathAnims.Num() ? Target.DeathAnims[FMath::RandRange(0, Target.DeathAnims.Num() - 1)].Get() : Target.DeathAnim.Get();
	Target.Play(Death ? Death : Target.DeathAnim.Get(), false);
	Target.Mesh->GlobalAnimRateScale = 1.f;
	Target.Mesh->SetRelativeScale3D(FVector(Target.BaseScale));
	Target.Capsule->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (UParticleSystemComponent* Fx = Target.StateFx.Get()) Fx->DeactivateSystem();
	USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(this);
	if (Combat)
	{
		const TCHAR* Fx = Target.Kind == ESeleneUnitKind::Patron ? FxPatronDeath : Target.bStructure ? FxStructureDeath : FxMinionDeath;
		Combat->SpawnFx(Fx, Target.Center(), (Target.Center() - From).GetSafeNormal2D().Rotation(), Target.bStructure ? 2.f : 1.f);
	}
	if (!Target.bStructure) return;
	const bool bDawn = Target.Team == ESeleneTeam::Dawn;
	const FString Side = bDawn ? TEXT("Your") : TEXT("Enemy");
	UE_LOG(LogSelene, Log, TEXT("Lanes: %s %s destroyed at %.0fs."), bDawn ? TEXT("Dawn") : TEXT("Dusk"), KindName(Target.Kind), Clock);
	if (Combat)
	{
		const FString LaneName = Lanes.IsValidIndex(Target.Lane) ? Lanes[Target.Lane].LaneName.ToString().ToUpper() + TEXT(" ") : FString();
		Combat->Announce(FString::Printf(TEXT("%s %s%s destroyed"), *Side, *LaneName, KindName(Target.Kind)),
			bDawn ? FLinearColor(1.f, 0.35f, 0.3f) : FLinearColor(0.45f, 0.9f, 1.f), 4.f);
		if (Target.Kind == ESeleneUnitKind::Walker && !IsAnyDead(Target.Team, ESeleneUnitKind::Walker, &Target))
		{
			Combat->Announce(bDawn ? TEXT("Your Base Guardians are exposed") : TEXT("The enemy Base Guardians are exposed"), FLinearColor(1.f, 0.85f, 0.35f), 4.f);
		}
		if (Target.Kind == ESeleneUnitKind::Shrine && !IsAnyAlive(Target.Team, ESeleneUnitKind::Shrine))
		{
			Combat->Announce(bDawn ? TEXT("Your Patron is exposed") : TEXT("The enemy Patron is exposed"), FLinearColor(1.f, 0.85f, 0.35f), 4.f);
		}
	}
	if (Target.Kind == ESeleneUnitKind::Patron)
	{
		bGameOver = true;
		GameOverTime = Clock;
		Winner = bDawn ? ESeleneTeam::Dusk : ESeleneTeam::Dawn;
		UE_LOG(LogSelene, Log, TEXT("Lanes: %s wins."), Winner == ESeleneTeam::Dawn ? TEXT("Dawn") : TEXT("Dusk"));
		if (Combat) Combat->Announce(Winner == ESeleneTeam::Dawn ? TEXT("VICTORY") : TEXT("DEFEAT"),
			Winner == ESeleneTeam::Dawn ? FLinearColor(1.f, 0.85f, 0.3f) : FLinearColor(1.f, 0.3f, 0.3f), 12.f);
	}
}

void ASeleneLaneDirector::Attack(ASeleneLaneUnit& Unit, const FSeleneTarget& Target)
{
	USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(this);
	if (!Combat) return;
	if (Unit.Kind == ESeleneUnitKind::Melee)
	{
		const float Dealt = Combat->DealDamage(Target, Unit.Damage * (Target.Hero.IsValid() ? 0.35f : 1.f), Unit.Team, Unit.Center(), &Unit);
		if (Dealt > 0.f) Combat->SpawnFx(FxMeleeImpact, Target.Location(), FRotator::ZeroRotator, 0.7f);
		return;
	}
	// Troopers mostly fight troopers: a hero takes a third of their damage. Structures hit heroes at full strength.
	const float Scale = (Target.Hero.IsValid() && !Unit.bStructure) ? 0.35f : 1.f;
	USeleneCombatSubsystem::FProjectileSpec Shot;
	Shot.Damage = Unit.Damage * Scale;
	Shot.bHitWorld = false;
	Shot.ImpactFx = FSoftObjectPath(FxShotImpact);
	if (Unit.bStructure)
	{
		Shot.TrailFx = FSoftObjectPath(FxStructureShot); Shot.FxScale = Unit.Kind == ESeleneUnitKind::Guardian ? 0.6f : 0.8f;
		Shot.Speed = 2600.f; Shot.bHeavy = true;
	}
	else
	{
		Shot.TrailFx = FSoftObjectPath(FxMinionShot); Shot.FxScale = Unit.Kind == ESeleneUnitKind::Siege ? 0.6f : 0.35f;
		Shot.Speed = Unit.Kind == ESeleneUnitKind::Siege ? 1800.f : 2600.f;
		Shot.bHeavy = Unit.Kind == ESeleneUnitKind::Siege;
	}
	const FVector Muzzle = Unit.Center() + Unit.GetActorForwardVector() * Unit.Radius + FVector(0, 0, Unit.HalfHeight * 0.35f);
	Combat->SpawnFx(Unit.Kind == ESeleneUnitKind::Siege ? FxSiegeMuzzle : FxMuzzle, Muzzle, Unit.GetActorRotation(), Unit.bStructure ? 1.5f : 0.8f);
	Combat->FireHoming(Shot, Muzzle, Target, Unit.Team, &Unit);
}

void ASeleneLaneDirector::TickUnit(ASeleneLaneUnit& Unit, float DeltaSeconds)
{
	Unit.HeroAggroTimer = FMath::Max(0.f, Unit.HeroAggroTimer - DeltaSeconds);
	Unit.SlowTimer = FMath::Max(0.f, Unit.SlowTimer - DeltaSeconds);
	if (Unit.SlowTimer <= 0.f) Unit.SlowFactor = 1.f;
	if (Unit.StunTimer > 0.f)
	{
		Unit.StunTimer -= DeltaSeconds;
		Unit.Mesh->GlobalAnimRateScale = Unit.StunTimer > 0.f ? 0.f : 1.f;
		if (Unit.StunTimer <= 0.f) if (UParticleSystemComponent* Fx = Unit.StateFx.Get()) { Fx->DeactivateSystem(); Unit.StateFx.Reset(); }
		return;
	}
	if (Unit.HitReactTimer > 0.f)
	{
		Unit.HitReactTimer -= DeltaSeconds;
		if (Unit.HitReactTimer > 0.f) return;
		Unit.Mesh->GlobalAnimRateScale = 1.f;
		Unit.Mesh->SetRelativeScale3D(FVector(Unit.BaseScale));
		if (Unit.CurrentAnim && Unit.HitReactAnims.Contains(Unit.CurrentAnim)) Unit.CurrentAnim = nullptr;
	}
	if (Unit.bStructure && Unit.Health < Unit.MaxHealth && Clock - Unit.LastHeroHitTime > 8.f)
	{
		Unit.Health = FMath::Min(Unit.MaxHealth, Unit.Health + Unit.MaxHealth * StructureRegen * DeltaSeconds);
	}
	if (Unit.bStructure && Unit.StateFx.IsValid() && !IsProtected(Unit))
	{
		Unit.StateFx->DeactivateSystem(); Unit.StateFx.Reset();
	}
	const FSeleneTarget Target = FindTarget(Unit, Unit.bStructure ? Unit.Range : FMath::Max(AggroRange, Unit.Range));
	const FVector2D TargetPos = Target.IsSet() ? FVector2D(Target.Location()) : FVector2D::ZeroVector;
	const float Gap = Target.IsSet() ? FVector2D::Distance(Unit.Pos, TargetPos) - Target.Radius() - Unit.Radius : 0.f;
	const float Rate = Unit.SlowFactor;
	Unit.Mesh->GlobalAnimRateScale = Rate;
	if (Target.IsSet() && Gap <= Unit.Range)
	{
		const FVector2D To = TargetPos - Unit.Pos;
		if (Unit.CurrentAnim != Unit.AttackAnim) Unit.AttackTimer = FMath::Min(Unit.AttackTimer, Unit.AttackPeriod * Spec(Unit.Kind).ShotFraction);
		Unit.Play(Unit.AttackAnim, true);
		Unit.AttackTimer -= DeltaSeconds * Rate;
		if (Unit.AttackTimer <= 0.f)
		{
			Unit.AttackTimer += Unit.AttackPeriod;
			Attack(Unit, Target);
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
	if (Target.IsSet())
	{
		Goal = TargetPos;
	}
	else
	{
		FVector2D Tangent;
		const float Ahead = Unit.S + Dir * 350.f;
		const FVector2D Centre = Path.At(Ahead, &Tangent);
		const float Edge = FMath::Min(Ahead, Path.Length - Ahead);
		Goal = Centre + FVector2D(-Tangent.Y, Tangent.X) * Unit.Lateral * FMath::Clamp(Edge / 2500.f, 0.f, 1.f);
	}
	FVector2D Step = (Goal - Unit.Pos).GetSafeNormal() * Unit.Speed * Rate * DeltaSeconds;
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
	// Follow the terrain: trace from just above the current ground so overpass decks overhead are ignored.
	const float NewZ = TraceGround(Unit.Pos, Unit.Z + 120.f, Unit.Z);
	Unit.Z = FMath::FInterpTo(Unit.Z, NewZ, DeltaSeconds, 20.f);
	Unit.Play(Unit.MoveAnim, true);
	if (!Step.IsNearlyZero()) Place(Unit, FMath::RadiansToDegrees(FMath::Atan2(Goal.Y - Unit.Pos.Y, Goal.X - Unit.Pos.X)));
}

bool ASeleneLaneDirector::IsAnyAlive(ESeleneTeam Team, ESeleneUnitKind Kind) const
{
	for (const ASeleneLaneUnit* U : Units) if (U && U->IsAlive() && U->Team == Team && U->Kind == Kind) return true;
	return false;
}

bool ASeleneLaneDirector::IsAnyDead(ESeleneTeam Team, ESeleneUnitKind Kind, const ASeleneLaneUnit* Except) const
{
	for (const ASeleneLaneUnit* U : Units) if (U && U != Except && !U->IsAlive() && U->Team == Team && U->Kind == Kind) return true;
	return false;
}

ASeleneLaneDirector::FObjectives ASeleneLaneDirector::GetObjectives() const
{
	FObjectives O;
	O.bHasLanes = !Paths.IsEmpty();
	O.bGameOver = bGameOver; O.Winner = Winner; O.Clock = Clock; O.NextWave = NextWave; O.Wave = WaveIndex;
	for (const ASeleneLaneUnit* Unit : Units)
	{
		if (!Unit || !Unit->bStructure) continue;
		const int32 T = static_cast<int32>(Unit->Team);
		if (Unit->Kind == ESeleneUnitKind::Guardian && Unit->IsAlive()) ++O.Guardians[T];
		if (Unit->Kind == ESeleneUnitKind::Walker && Unit->IsAlive()) ++O.Walkers[T];
		if (Unit->Kind == ESeleneUnitKind::BaseGuardian && Unit->IsAlive()) ++O.BaseGuardians[T];
		if (Unit->Kind == ESeleneUnitKind::Shrine && Unit->IsAlive()) ++O.Shrines[T];
		if (Unit->Kind == ESeleneUnitKind::Patron)
		{
			O.PatronHealth[T] = Unit->IsAlive() ? Unit->Health / Unit->MaxHealth : 0.f;
			O.bPatronProtected[T] = IsProtected(*Unit);
		}
	}
	return O;
}

void ASeleneLaneDirector::DebugTeleport(APawn& Pawn, FName LaneName, float Fraction)
{
	for (int32 i = 0; i < Lanes.Num() && i < Paths.Num(); ++i)
	{
		if (Lanes[i].LaneName != LaneName) continue;
		FVector2D Tangent;
		const FVector2D At = Paths[i].At(Paths[i].Length * FMath::Clamp(Fraction, 0.f, 1.f), &Tangent);
		const float Ground = TraceGround(At, 1500.f, 0.f);
		const float Yaw = FMath::RadiansToDegrees(FMath::Atan2(Tangent.Y, Tangent.X));
		Pawn.SetActorLocationAndRotation(FVector(At.X, At.Y, Ground + 100.f), FRotator(0, Yaw, 0), false, nullptr, ETeleportType::TeleportPhysics);
		if (AController* C = Pawn.GetController()) C->SetControlRotation(FRotator(-12.f, Yaw, 0));   // level, behind the hero
		return;
	}
}

void ASeleneLaneDirector::DebugBreak(ESeleneTeam Team, FName LaneName, ESeleneUnitKind Kind)
{
	const int32 Lane = Lanes.IndexOfByPredicate([&](const FSeleneLane& L) { return L.LaneName == LaneName; });
	for (ASeleneLaneUnit* Unit : Units)
	{
		if (Unit && Unit->IsAlive() && Unit->Team == Team && Unit->Kind == Kind && Unit->Lane == Lane) Kill(*Unit, Unit->Center());
	}
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
		const FVector Mid = Unit->Center() + FVector(0, 0, Unit->HalfHeight + 40.f);
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
	if (bGameOver)
	{
		const float Delay = CVarLaneRestart.GetValueOnGameThread();
		if (Delay > 0.f && Clock - GameOverTime >= Delay)
		{
			if (APlayerController* PC = GetWorld()->GetFirstPlayerController()) PC->ConsoleCommand(TEXT("RestartLevel"));
			GameOverTime = TNumericLimits<float>::Max() * 0.5f;
		}
	}
	if (const int32 Stress = CVarLaneStress.GetValueOnGameThread(); Stress != LastStress)
	{
		if (Stress > LastStress) SpawnStress(Stress - LastStress);
		LastStress = Stress;
	}
	for (int32 Budget = 2; Budget > 0 && Pending.Num(); --Budget)   // spread a wave over a few frames
	{
		const FPendingSpawn Next = Pending.Pop(EAllowShrinking::No);
		SpawnUnit(Next.Kind, Next.Team, Next.Lane, Next.At, Next.S, Next.Lateral, Next.Power);
	}
	for (int32 i = Units.Num() - 1; i >= 0; --i)
	{
		ASeleneLaneUnit* Unit = Units[i];
		if (!Unit) { Units.RemoveAtSwap(i); continue; }
		if (!Unit->IsAlive())
		{
			Unit->DeadTime += DeltaSeconds;
			if (!Unit->bStructure && Unit->DeadTime > CorpseSeconds - 1.f)   // sink into the ground before removal
			{
				Unit->Z -= DeltaSeconds * 80.f;
				Place(*Unit, Unit->GetActorRotation().Yaw);
			}
			if (Unit->DeadTime > CorpseSeconds && !Unit->bStructure) { Unit->Destroy(); Units.RemoveAtSwap(i); }
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
	if (!ScriptParsed)
	{
		ScriptParsed = true;
		TArray<FString> Steps;
		CVarLaneScript.GetValueOnGameThread().ParseIntoArray(Steps, TEXT(";"));
		for (const FString& Step : Steps)
		{
			FString When, Command;
			if (Step.Split(TEXT(":"), &When, &Command)) Script.Add({ FCString::Atof(*When), Command.TrimStartAndEnd() });
		}
	}
	for (int32 i = Script.Num() - 1; i >= 0; --i)
	{
		if (Clock < Script[i].Key) continue;
		if (APlayerController* PC = GetWorld()->GetFirstPlayerController()) PC->ConsoleCommand(Script[i].Value);
		Script.RemoveAt(i);
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
			// Balance view: where each lane's fight is (0 = Dawn base, 1 = Dusk base) and each structure's health.
			FString LaneText;
			for (int32 Lane = 0; Lane < Paths.Num(); ++Lane)
			{
				float DawnFront = 0.f, DuskFront = 1.f;
				for (const ASeleneLaneUnit* U : Units)
				{
					if (!U || !U->IsAlive() || U->bStructure || U->Lane != Lane) continue;
					const float F = U->S / FMath::Max(Paths[Lane].Length, 1.f);
					if (U->Team == ESeleneTeam::Dawn) DawnFront = FMath::Max(DawnFront, F); else DuskFront = FMath::Min(DuskFront, F);
				}
				LaneText += FString::Printf(TEXT(" L%d front=%.2f/%.2f"), Lane, DawnFront, DuskFront);
			}
			FString Hp;
			for (const ASeleneLaneUnit* U : Units)
			{
				if (U && U->bStructure) Hp += FString::Printf(TEXT(" %c%s%d=%.0f%%"), U->Team == ESeleneTeam::Dawn ? 'A' : 'U', KindName(U->Kind), U->Lane, U->IsAlive() ? U->Health / U->MaxHealth * 100.f : 0.f);
			}
			UE_LOG(LogSelene, Log, TEXT("LaneBalance t=%.0f%s |%s"), Clock, *LaneText, *Hp);
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
