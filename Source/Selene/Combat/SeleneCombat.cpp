#include "Combat/SeleneCombat.h"

#include "Selene.h"
#include "SeleneCharacter.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "Particles/ParticleSystem.h"
#include "Particles/ParticleSystemComponent.h"
#include "Sound/SoundBase.h"
#include "HAL/IConsoleManager.h"

namespace { TAutoConsoleVariable<int32> CVarDamageLog(TEXT("selene.DamageLog"), 0, TEXT("1 logs every hit a player hero lands or takes.")); }
#include "Sound/SoundAttenuation.h"

// ---------------------------------------------------------------- targets

bool FSeleneTarget::IsAlive() const
{
	if (const ASeleneLaneUnit* U = Unit.Get()) return U->IsAlive();
	if (const ASeleneCharacter* H = Hero.Get()) return H->IsCombatAlive();
	return false;
}

ESeleneTeam FSeleneTarget::Team() const
{
	if (const ASeleneLaneUnit* U = Unit.Get()) return U->Team;
	if (const ASeleneCharacter* H = Hero.Get()) return H->GetTeam();
	return ESeleneTeam::Dawn;
}

FVector FSeleneTarget::Location() const
{
	if (const ASeleneLaneUnit* U = Unit.Get()) return U->Center();
	if (const ASeleneCharacter* H = Hero.Get()) return H->GetActorLocation();
	return FVector::ZeroVector;
}

FVector FSeleneTarget::Feet() const
{
	return Location() - FVector(0, 0, HalfHeight());
}

float FSeleneTarget::Radius() const
{
	if (const ASeleneLaneUnit* U = Unit.Get()) return U->Radius;
	if (const ASeleneCharacter* H = Hero.Get()) return H->GetCapsuleComponent()->GetScaledCapsuleRadius();
	return 0.f;
}

float FSeleneTarget::HalfHeight() const
{
	if (const ASeleneLaneUnit* U = Unit.Get()) return U->HalfHeight;
	if (const ASeleneCharacter* H = Hero.Get()) return H->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	return 0.f;
}

// ---------------------------------------------------------------- subsystem

USeleneCombatSubsystem* USeleneCombatSubsystem::Get(const UObject* WorldContext)
{
	const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	return World ? World->GetSubsystem<USeleneCombatSubsystem>() : nullptr;
}

double USeleneCombatSubsystem::Now() const
{
	return GetWorld() ? GetWorld()->GetRealTimeSeconds() : 0.0;
}

void USeleneCombatSubsystem::Deinitialize()
{
	for (FProjectile& P : Projectiles) if (UParticleSystemComponent* Trail = P.Trail.Get()) Trail->DestroyComponent();
	Projectiles.Reset();
	Super::Deinitialize();
}

UParticleSystem* USeleneCombatSubsystem::Fx(const FSoftObjectPath& Path)
{
	if (Path.IsNull()) return nullptr;
	const FName Key(*Path.ToString());
	if (TObjectPtr<UParticleSystem>* Found = FxCache.Find(Key)) return *Found;
	UParticleSystem* System = Cast<UParticleSystem>(Path.TryLoad());
	if (!System) UE_LOG(LogSelene, Warning, TEXT("Combat: missing effect %s"), *Path.ToString());
	FxCache.Add(Key, System);
	return System;
}

UParticleSystemComponent* USeleneCombatSubsystem::SpawnFx(const FSoftObjectPath& Path, const FVector& Location, const FRotator& Rotation, float Scale)
{
	UParticleSystem* System = Fx(Path);
	if (!System || !GetWorld()) return nullptr;
	return UGameplayStatics::SpawnEmitterAtLocation(GetWorld(), System, FTransform(Rotation, Location, FVector(Scale)), true);
}

UParticleSystemComponent* USeleneCombatSubsystem::AttachFx(const FSoftObjectPath& Path, USceneComponent* To, FName Socket, float Scale)
{
	UParticleSystem* System = Fx(Path);
	if (!System || !To) return nullptr;
	return UGameplayStatics::SpawnEmitterAttached(System, To, Socket, FVector::ZeroVector, FRotator::ZeroRotator, FVector(Scale),
		EAttachLocation::SnapToTarget, true);
}

USoundBase* USeleneCombatSubsystem::Sound(const FString& Path)
{
	if (Path.IsEmpty()) return nullptr;
	const FName Key(*Path);
	if (TObjectPtr<USoundBase>* Found = SoundCache.Find(Key)) return *Found;
	USoundBase* Loaded = Cast<USoundBase>(FSoftObjectPath(Path).TryLoad());
	SoundCache.Add(Key, Loaded);
	return Loaded;
}

void USeleneCombatSubsystem::PlaySoundAt(USoundBase* SoundAsset, const FVector& Location, float Volume, float Pitch)
{
	if (!SoundAsset || !GetWorld()) return;
	if (!Attenuation)
	{
		// Combat sounds carry about one lane screen: full volume within 5 m, silent by 40 m.
		Attenuation = NewObject<USoundAttenuation>(this);
		FSoundAttenuationSettings& A = Attenuation->Attenuation;
		A.bAttenuate = true;
		A.bSpatialize = true;
		A.AttenuationShape = EAttenuationShape::Sphere;
		A.AttenuationShapeExtents = FVector(500.f, 0.f, 0.f);
		A.FalloffDistance = 3500.f;
	}
	UGameplayStatics::PlaySoundAtLocation(GetWorld(), SoundAsset, Location, Volume, Pitch, 0.f, Attenuation);
}

void USeleneCombatSubsystem::HitStop(AActor* Actor, float Seconds)
{
	if (!Actor) return;
	for (FStop& Stop : Stops)
	{
		if (Stop.Actor.Get() == Actor) { Stop.Until = FMath::Max(Stop.Until, Now() + Seconds); return; }
	}
	Stops.Add({ Actor, Now() + Seconds, Actor->CustomTimeDilation });
	Actor->CustomTimeDilation = 0.03f;
}

void USeleneCombatSubsystem::ForEachHero(TFunctionRef<void(ASeleneCharacter&)> Visit) const
{
	if (!GetWorld()) return;
	for (TActorIterator<ASeleneCharacter> It(GetWorld()); It; ++It)
	{
		if (!It->IsNpc()) Visit(**It);
	}
}

void USeleneCombatSubsystem::GatherEnemies(const FVector& Center, float Radius, ESeleneTeam Team, TArray<FSeleneTarget>& Out) const
{
	if (const ASeleneLaneDirector* Director = ASeleneLaneDirector::Get(GetWorld()))
	{
		for (ASeleneLaneUnit* Unit : Director->GetUnits())
		{
			if (!Unit || !Unit->IsAlive() || Unit->Team == Team) continue;
			if (FVector2D::Distance(FVector2D(Center), Unit->Pos) - Unit->Radius > Radius) continue;
			if (FMath::Abs(Unit->Center().Z - Center.Z) > 400.f + Unit->HalfHeight) continue;
			Out.Add(FSeleneTarget(Unit));
		}
	}
	ForEachHero([&](ASeleneCharacter& Hero)
	{
		if (!Hero.IsCombatAlive() || Hero.GetTeam() == Team) return;
		const FVector L = Hero.GetActorLocation();
		if (FVector2D::Distance(FVector2D(Center), FVector2D(L)) - 34.f > Radius || FMath::Abs(L.Z - Center.Z) > 400.f) return;
		Out.Add(FSeleneTarget(&Hero));
	});
}

void USeleneCombatSubsystem::GatherCone(const FVector& Origin, const FVector& Forward, float Reach, float MinCos, ESeleneTeam Team, TArray<FSeleneTarget>& Out) const
{
	TArray<FSeleneTarget> Near;
	GatherEnemies(Origin, Reach, Team, Near);
	const FVector2D Dir = FVector2D(Forward).GetSafeNormal();
	for (const FSeleneTarget& T : Near)
	{
		const FVector2D To = FVector2D(T.Location() - Origin);
		const float Dist = To.Size() - T.Radius();
		if (Dist > 70.f && FVector2D::DotProduct(To.GetSafeNormal(), Dir) < MinCos) continue;
		Out.Add(T);
	}
}

FSeleneTarget USeleneCombatSubsystem::RayEnemy(const FVector& Start, const FVector& Dir, float Length, ESeleneTeam Team, float Slack, float& OutDistance) const
{
	FSeleneTarget Best;
	OutDistance = Length;
	auto Test = [&](const FSeleneTarget& T)
	{
		// Ray against a vertical capsule approximated as a cylinder: closest approach in 2D, then height check.
		const FVector C = T.Location();
		const float Along = FVector::DotProduct(C - Start, Dir);
		if (Along < 0.f || Along > OutDistance) return;
		const FVector P = Start + Dir * Along;
		const float Side = FVector2D::Distance(FVector2D(P), FVector2D(C));
		if (Side > T.Radius() + Slack) return;
		if (FMath::Abs(P.Z - C.Z) > T.HalfHeight() + Slack) return;
		OutDistance = Along; Best = T;
	};
	if (const ASeleneLaneDirector* Director = ASeleneLaneDirector::Get(GetWorld()))
	{
		for (ASeleneLaneUnit* Unit : Director->GetUnits())
		{
			if (Unit && Unit->IsAlive() && Unit->Team != Team) Test(FSeleneTarget(Unit));
		}
	}
	ForEachHero([&](ASeleneCharacter& Hero) { if (Hero.IsCombatAlive() && Hero.GetTeam() != Team) Test(FSeleneTarget(&Hero)); });
	return Best;
}

float USeleneCombatSubsystem::DealDamage(const FSeleneTarget& Target, float Amount, ESeleneTeam FromTeam, const FVector& From, AActor* Instigator, bool bHeavy)
{
	if (!Target.IsAlive() || Target.Team() == FromTeam || Amount <= 0.f) return 0.f;
	float Dealt = 0.f;
	if (ASeleneLaneUnit* Unit = Target.Unit.Get())
	{
		if (ASeleneLaneDirector* Director = ASeleneLaneDirector::Get(GetWorld())) Dealt = Director->DamageUnit(*Unit, Amount, From, Instigator);
	}
	else if (ASeleneCharacter* Hero = Target.Hero.Get())
	{
		Dealt = Hero->ReceiveDamage(Amount, From, Instigator, bHeavy);
		if (Hero->IsPlayerControlled() && Dealt > 0.f)
		{
			LastPlayerHurtTime = Now();
			LastPlayerHurtFrom = From;
			DamageNumbers.Add({ Hero->GetActorLocation() + FVector(0, 0, 60), Dealt, Now(), true, bHeavy });
		}
	}
	// Feedback for hits the local player landed.
	const ASeleneCharacter* Attacker = Cast<ASeleneCharacter>(Instigator);
	if (CVarDamageLog.GetValueOnGameThread() != 0 && Attacker && Attacker->IsPlayerControlled())
	{
		UE_LOG(LogSelene, Warning, TEXT("Damage %.0f -> %.0f on %s"), Amount, Dealt, Target.Unit.IsValid() ? *Target.Unit->GetName() : TEXT("hero"));
	}
	if (Attacker && Attacker->IsPlayerControlled())
	{
		LastHitMarkerTime = Now();
		bLastHitWasKill = !Target.IsAlive();
		DamageNumbers.Add({ Target.Location() + FVector(FMath::FRandRange(-30.f, 30.f), FMath::FRandRange(-30.f, 30.f), Target.HalfHeight() + 30.f),
			Dealt, Now(), false, bHeavy });
	}
	return Dealt;
}

void USeleneCombatSubsystem::Slow(const FSeleneTarget& Target, float Factor, float Seconds)
{
	if (ASeleneLaneUnit* Unit = Target.Unit.Get())
	{
		if (Unit->bStructure) return;
		Unit->SlowFactor = FMath::Min(Unit->SlowFactor, Factor);
		Unit->SlowTimer = FMath::Max(Unit->SlowTimer, Seconds);
	}
	else if (ASeleneCharacter* Hero = Target.Hero.Get()) Hero->ApplySlow(Factor, Seconds);
}

void USeleneCombatSubsystem::Stun(const FSeleneTarget& Target, float Seconds)
{
	if (ASeleneLaneUnit* Unit = Target.Unit.Get())
	{
		if (Unit->bStructure || !Unit->IsAlive()) return;
		Unit->StunTimer = FMath::Max(Unit->StunTimer, Seconds);
		if (!Unit->StateFx.IsValid())
		{
			Unit->StateFx = AttachFx(FSoftObjectPath(TEXT("/Game/ParagonMinions/FX/Particles/SharedGameplay/States/Stun/P_StunnedLoop.P_StunnedLoop")),
				Unit->Mesh, NAME_None, 0.8f);
			if (UParticleSystemComponent* Fx = Unit->StateFx.Get()) Fx->SetRelativeLocation(FVector(0, 0, Unit->HalfHeight * 2.f + 20.f));
		}
	}
	else if (ASeleneCharacter* Hero = Target.Hero.Get()) Hero->ApplySlow(0.f, Seconds);
}

void USeleneCombatSubsystem::Announce(const FString& Text, const FLinearColor& Color, float Duration, bool bChime)
{
	Announcements.Add({ Text, Color, Now(), Duration });
	if (Announcements.Num() > 4) Announcements.RemoveAt(0);
}

// ---------------------------------------------------------------- projectiles

void USeleneCombatSubsystem::FireHoming(const FProjectileSpec& Spec, const FVector& Start, const FSeleneTarget& Target, ESeleneTeam Team, AActor* Instigator)
{
	FProjectile& P = Projectiles.AddDefaulted_GetRef();
	P.Spec = Spec; P.Pos = Start; P.Homing = Target; P.Team = Team; P.Instigator = Instigator;
	P.Dir = (Target.Location() - Start).GetSafeNormal();
	P.Trail = SpawnFx(Spec.TrailFx, Start, P.Dir.Rotation(), Spec.FxScale);
	if (UParticleSystemComponent* Trail = P.Trail.Get()) Trail->bAutoDestroy = false;
}

void USeleneCombatSubsystem::FireStraight(const FProjectileSpec& Spec, const FVector& Start, const FVector& Dir, ESeleneTeam Team, AActor* Instigator)
{
	FProjectile& P = Projectiles.AddDefaulted_GetRef();
	P.Spec = Spec; P.Pos = Start; P.Dir = Dir.GetSafeNormal(); P.Team = Team; P.Instigator = Instigator;
	P.Trail = SpawnFx(Spec.TrailFx, Start, P.Dir.Rotation(), Spec.FxScale);
	if (UParticleSystemComponent* Trail = P.Trail.Get()) Trail->bAutoDestroy = false;
}

void USeleneCombatSubsystem::FinishProjectile(FProjectile& P, const FVector& At, bool bHitSomething)
{
	if (UParticleSystemComponent* Trail = P.Trail.Get())
	{
		Trail->SetWorldLocation(At);
		Trail->DeactivateSystem();
		Trail->bAutoDestroy = true;
	}
	if (bHitSomething || P.Spec.bHitWorld) SpawnFx(P.Spec.ImpactFx, At, (-P.Dir).Rotation(), P.Spec.FxScale > 0.f ? FMath::Max(P.Spec.FxScale, 0.5f) : 1.f);
}

void USeleneCombatSubsystem::Tick(float DeltaSeconds)
{
	// Hit-stop is real time so it does not depend on the stopped actor's own dilation.
	const double T = Now();
	for (int32 i = Stops.Num() - 1; i >= 0; --i)
	{
		if (T < Stops[i].Until) continue;
		if (AActor* Actor = Stops[i].Actor.Get()) Actor->CustomTimeDilation = Stops[i].Saved;
		Stops.RemoveAtSwap(i);
	}
	DamageNumbers.RemoveAll([T](const FSeleneDamageNumber& N) { return T - N.Time > 1.1; });
	Announcements.RemoveAll([T](const FSeleneAnnouncement& A) { return T - A.Time > A.Duration; });

	UWorld* World = GetWorld();
	for (int32 i = Projectiles.Num() - 1; i >= 0; --i)
	{
		FProjectile& P = Projectiles[i];
		const float Step = P.Spec.Speed * DeltaSeconds;
		bool bDone = false;
		if (P.Homing.IsSet())
		{
			if (!P.Homing.IsAlive())
			{
				FinishProjectile(P, P.Pos, false);
				bDone = true;
			}
			else
			{
				const FVector Goal = P.Homing.Location();
				const FVector To = Goal - P.Pos;
				const float Dist = To.Size();
				P.Dir = To / FMath::Max(Dist, 1.f);
				if (Dist <= Step + P.Homing.Radius())
				{
					DealDamage(P.Homing, P.Spec.Damage, P.Team, P.Pos, P.Instigator.Get(), P.Spec.bHeavy);
					FinishProjectile(P, Goal - P.Dir * P.Homing.Radius(), true);
					bDone = true;
				}
				else P.Pos += P.Dir * Step;
			}
		}
		else
		{
			// Straight shot: world hit first, then any enemy capsule along this step.
			float WorldDist = Step;
			FHitResult Hit;
			FCollisionQueryParams Params(SCENE_QUERY_STAT(SeleneProjectile), false, P.Instigator.Get());
			FCollisionObjectQueryParams Objects(ECC_WorldStatic);
			if (P.Spec.bHitWorld && World && World->LineTraceSingleByObjectType(Hit, P.Pos, P.Pos + P.Dir * Step, Objects, Params))
			{
				WorldDist = Hit.Distance;
			}
			float Remaining = WorldDist;
			FVector From = P.Pos;
			while (true)
			{
				float Along = 0.f;
				const FSeleneTarget Victim = RayEnemy(From, P.Dir, Remaining, P.Team, P.Spec.HitRadius, Along);
				if (!Victim.IsSet()) break;
				if (P.AlreadyHit.Contains(Victim)) { From += P.Dir * (Along + 1.f); Remaining -= Along + 1.f; if (Remaining <= 0.f) break; continue; }
				P.AlreadyHit.Add(Victim);
				const FVector At = From + P.Dir * Along;
				DealDamage(Victim, P.Spec.Damage, P.Team, At - P.Dir * 100.f, P.Instigator.Get(), P.Spec.bHeavy);
				if (!P.Spec.bPierce) { FinishProjectile(P, At, true); bDone = true; break; }
				SpawnFx(P.Spec.ImpactFx, At, (-P.Dir).Rotation(), FMath::Max(P.Spec.FxScale, 0.5f));
				From = At + P.Dir; Remaining -= Along + 1.f;
				if (Remaining <= 0.f) break;
			}
			if (!bDone)
			{
				P.Pos += P.Dir * WorldDist;
				P.Travelled += WorldDist;
				if (WorldDist < Step - 0.1f) { FinishProjectile(P, P.Pos, false); bDone = true; }
				else if (P.Travelled >= P.Spec.Range) { FinishProjectile(P, P.Pos, false); bDone = true; }
			}
		}
		if (bDone) { Projectiles.RemoveAtSwap(i); continue; }
		if (UParticleSystemComponent* Trail = P.Trail.Get()) Trail->SetWorldLocationAndRotation(P.Pos, P.Dir.Rotation());
	}
}
