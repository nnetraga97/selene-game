#include "Combat/SeleneBotController.h"

#include "Selene.h"
#include "SeleneCharacter.h"
#include "Lanes/SeleneLaneDirector.h"
#include "Components/CapsuleComponent.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "HAL/IConsoleManager.h"
#include "Movement/SeleneMovementComponent.h"

namespace
{
	TAutoConsoleVariable<FString> CVarBots(TEXT("selene.Bots"), TEXT("none"),
		TEXT("Bot heroes on lane maps, read when the map starts: 'Team:Hero:lane;...' (Team Dawn = yours, Dusk = enemy). Empty for none."));
}

ASeleneBotController::ASeleneBotController()
{
	PrimaryActorTick.bCanEverTick = true;
	bWantsPlayerState = false;
}

void ASeleneBotController::SpawnBots(UWorld* World)
{
	ASeleneLaneDirector* Director = ASeleneLaneDirector::Get(World);
	if (!Director || Director->Lanes.IsEmpty()) return;
	TArray<FString> Entries;
	if (CVarBots.GetValueOnGameThread().Equals(TEXT("none"), ESearchCase::IgnoreCase)) return;
	CVarBots.GetValueOnGameThread().ParseIntoArray(Entries, TEXT(";"));
	for (const FString& Entry : Entries)
	{
		TArray<FString> Parts;
		Entry.ParseIntoArray(Parts, TEXT(":"));
		if (Parts.Num() < 3) continue;
		const ESeleneTeam Team = Parts[0].Equals(TEXT("Dawn"), ESearchCase::IgnoreCase) ? ESeleneTeam::Dawn : ESeleneTeam::Dusk;
		const int32 Lane = Director->Lanes.IndexOfByPredicate([&](const FSeleneLane& L) { return L.LaneName.ToString().Equals(Parts[2], ESearchCase::IgnoreCase); });
		if (Lane == INDEX_NONE) continue;
		const FVector Base = Team == ESeleneTeam::Dawn ? Director->DawnBase : Director->DuskBase;
		const FVector2D At = FVector2D(Base) + FVector2D(Team == ESeleneTeam::Dawn ? 900.f : -900.f, (Lane - 1) * 600.f);
		const FVector Spawn(At.X, At.Y, Director->TraceGround(At, 3000.f, 0.f) + 100.f);
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;
		ASeleneCharacter* Hero = World->SpawnActorDeferred<ASeleneCharacter>(ASeleneCharacter::StaticClass(),
			FTransform(FRotator(0, Team == ESeleneTeam::Dawn ? 0.f : 180.f, 0), Spawn), nullptr, nullptr, ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn);
		if (!Hero) continue;
		Hero->AutoPossessPlayer = EAutoReceiveInput::Disabled;
		Hero->AutoPossessAI = EAutoPossessAI::Disabled;
		Hero->SetTeam(Team);
		Hero->SetStartCharacter(FName(*Parts[1]));
		Hero->FinishSpawning(FTransform(FRotator(0, Team == ESeleneTeam::Dawn ? 0.f : 180.f, 0), Spawn));
		ASeleneBotController* Bot = World->SpawnActor<ASeleneBotController>(ASeleneBotController::StaticClass(), FTransform(Spawn), Params);
		if (!Bot) continue;
		Bot->Lane = Lane;
		Bot->Possess(Hero);
		UE_LOG(LogSelene, Log, TEXT("Bot %s (%s) on lane %s."), *Parts[1], Team == ESeleneTeam::Dawn ? TEXT("Dawn") : TEXT("Dusk"), *Parts[2]);
	}
}

FSeleneTarget ASeleneBotController::PickTarget(const ASeleneCharacter& Hero) const
{
	const USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(this);
	const ASeleneLaneDirector* Director = ASeleneLaneDirector::Get(GetWorld());
	if (!Combat || !Director) return FSeleneTarget();
	const FVector Me = Hero.GetActorLocation();
	FSeleneTarget Best;
	float BestScore = TNumericLimits<float>::Max();
	auto Consider = [&](const FSeleneTarget& T, float Bias)
	{
		const float Score = FVector::Dist2D(Me, T.Location()) * Bias;
		if (Score < BestScore) { BestScore = Score; Best = T; }
	};
	Combat->ForEachHero([&](ASeleneCharacter& Other)
	{
		if (!Other.IsCombatAlive() || Other.GetTeam() == Hero.GetTeam()) return;
		if (FVector::Dist2D(Me, Other.GetActorLocation()) > 1800.f) return;
		Consider(FSeleneTarget(&Other), 0.6f);   // heroes are the priority when close
	});
	for (ASeleneLaneUnit* Unit : Director->GetUnits())
	{
		if (!Unit || !Unit->IsAlive() || Unit->Team == Hero.GetTeam()) continue;
		const float D = FVector::Dist2D(Me, Unit->Center());
		if (D > 1600.f) continue;
		if (Unit->bStructure)
		{
			// Only siege a structure that can be hurt and while friendly troopers are tanking it.
			if (Director->IsProtected(*Unit)) continue;
			bool bTank = false;
			for (const ASeleneLaneUnit* Friend : Director->GetUnits())
			{
				if (Friend && Friend->IsAlive() && !Friend->bStructure && Friend->Team == Hero.GetTeam() && FVector2D::Distance(Friend->Pos, Unit->Pos) < Unit->Range) { bTank = true; break; }
			}
			if (!bTank) continue;
			Consider(FSeleneTarget(Unit), 1.4f);
		}
		else Consider(FSeleneTarget(Unit), 1.f);
	}
	return Best;
}

FVector ASeleneBotController::LaneGoal(const ASeleneCharacter& Hero) const
{
	const ASeleneLaneDirector* Director = ASeleneLaneDirector::Get(GetWorld());
	if (!Director || !Director->Lanes.IsValidIndex(Lane)) return Hero.GetActorLocation();
	const bool bDawn = Hero.GetTeam() == ESeleneTeam::Dawn;
	if (bRetreating) return bDawn ? Director->DawnBase : Director->DuskBase;
	// Stand just behind the most advanced friendly trooper on the lane; with none, wait at the own Guardian.
	const ASeleneLaneUnit* Front = nullptr;
	const ASeleneLaneUnit* Guardian = nullptr;
	for (const ASeleneLaneUnit* Unit : Director->GetUnits())
	{
		if (!Unit || !Unit->IsAlive() || Unit->Team != Hero.GetTeam() || Unit->Lane != Lane) continue;
		if (Unit->Kind == ESeleneUnitKind::Guardian) Guardian = Unit;
		if (Unit->bStructure) continue;
		if (!Front || (bDawn ? Unit->S > Front->S : Unit->S < Front->S)) Front = Unit;
	}
	const ASeleneLaneUnit* Anchor = Front ? Front : Guardian;
	if (!Anchor) return bDawn ? Director->DawnBase : Director->DuskBase;
	const FVector2D Back = (FVector2D(bDawn ? Director->DawnBase : Director->DuskBase) - Anchor->Pos).GetSafeNormal();
	const FVector2D Goal = Anchor->Pos + Back * (Front ? 450.f : 300.f);
	return FVector(Goal, Hero.GetActorLocation().Z);
}

void ASeleneBotController::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	ASeleneCharacter* Hero = Cast<ASeleneCharacter>(GetPawn());
	if (!Hero || !Hero->IsCombatAlive()) { Target = FSeleneTarget(); return; }
	const float HealthFraction = Hero->GetHealth() / FMath::Max(Hero->GetMaxHealth(), 1.f);
	if (HealthFraction < 0.3f) bRetreating = true;
	if (bRetreating && HealthFraction > 0.92f) bRetreating = false;

	ThinkTimer -= DeltaSeconds;
	if (ThinkTimer <= 0.f || !Target.IsAlive())
	{
		ThinkTimer = 0.4f;
		Target = bRetreating ? FSeleneTarget() : PickTarget(*Hero);
	}
	const FSelenePlayableCharacter& Entry = Hero->GetActiveCharacterEntry();
	const bool bBow = Entry.Weapon == ESeleneWeapon::Bow;
	const FVector Me = Hero->GetActorLocation();
	FVector MoveTo = LaneGoal(*Hero);
	StrafePhase += DeltaSeconds;
	if (Target.IsSet() && Target.IsAlive())
	{
		const FVector At = Target.Location();
		const float Dist = FVector::Dist2D(Me, At) - Target.Radius();
		const float Want = bBow ? 1100.f : 140.f;
		const FVector To = (At - Me).GetSafeNormal2D();
		// Close or keep range, with a slow side-to-side weave so a bot is not a static target.
		const FVector Side = FVector::CrossProduct(FVector::UpVector, To) * FMath::Sin(StrafePhase * 1.7f) * (bBow ? 1.f : 0.4f);
		if (Dist > Want + 60.f) MoveTo = Me + (To + Side * 0.4f) * 400.f;
		else if (bBow && Dist < Want * 0.6f) MoveTo = Me + (-To + Side) * 400.f;
		else MoveTo = Me + Side * 300.f;
		// Aim at the target's chest.
		const FVector View = Me + FVector(0, 0, 60.f);
		SetControlRotation((At + FVector(0, 0, Target.Hero.IsValid() ? 20.f : 0.f) - View).Rotation());
		const bool bInReach = Dist <= (bBow ? Entry.AttackReach * 0.3f : Entry.AttackReach * 0.9f);
		if (bInReach) Hero->Attack(); else Hero->StopAttack();
		// Abilities: try one at a time, a little after the last.
		AbilityTimer -= DeltaSeconds;
		if (AbilityTimer <= 0.f)
		{
			AbilityTimer = FMath::FRandRange(0.8f, 1.6f);
			for (int32 i = 0; i < Hero->GetAbilityCount(); ++i)
			{
				const FSeleneAbility* A = Hero->GetAbility(i);
				if (!A || Hero->GetAbilityCooldown(i) > 0.f) continue;
				const bool bSelf = A->Effect == ESeleneAbilityEffect::Nova || A->Effect == ESeleneAbilityEffect::Guard || A->Effect == ESeleneAbilityEffect::Overdrive;
				const float Reach = bSelf ? (A->Effect == ESeleneAbilityEffect::Overdrive ? 1500.f : A->Radius * 0.9f) : A->Range * 0.85f;
				if (Dist > Reach) continue;
				if (A->Effect == ESeleneAbilityEffect::LeapSlam && !Target.Hero.IsValid() && FMath::FRand() > 0.3f) continue;   // save the ultimate for heroes
				Hero->UseAbility(i);
				break;
			}
		}
	}
	else
	{
		Hero->StopAttack();
		const FVector To = MoveTo - Me;
		if (To.SizeSquared2D() > 1.f) SetControlRotation(FRotator(0.f, To.Rotation().Yaw, 0.f));
	}
	// Never stand inside an enemy structure's range unless friendly troopers are there to take its fire.
	if (const ASeleneLaneDirector* Director = ASeleneLaneDirector::Get(GetWorld()))
	{
		for (const ASeleneLaneUnit* Unit : Director->GetUnits())
		{
			if (!Unit || !Unit->bStructure || !Unit->IsAlive() || Unit->Team == Hero->GetTeam()) continue;
			const float Reach = Unit->Range + Unit->Radius + 150.f;
			if (FVector2D::Distance(FVector2D(MoveTo), Unit->Pos) > Reach) continue;
			bool bTank = false;
			for (const ASeleneLaneUnit* Friend : Director->GetUnits())
			{
				if (Friend && Friend->IsAlive() && !Friend->bStructure && Friend->Team == Hero->GetTeam() && FVector2D::Distance(Friend->Pos, Unit->Pos) < Unit->Range) { bTank = true; break; }
			}
			if (bTank) continue;
			const FVector2D Away = (FVector2D(MoveTo) - Unit->Pos).GetSafeNormal();
			MoveTo = FVector(Unit->Pos + (Away.IsNearlyZero() ? FVector2D(Me - Unit->Center()).GetSafeNormal() : Away) * Reach, MoveTo.Z);
		}
	}
	// Dash out when a fight turns bad.
	if (Hero->GetHealth() < LastHealth - 60.f && HealthFraction < 0.5f)
	{
		if (auto* Move = Cast<USeleneMovementComponent>(Hero->GetCharacterMovement())) Move->TryDash();
	}
	if (ThinkTimer >= 0.39f) LastHealth = Hero->GetHealth();
	const FVector Step = MoveTo - Me;
	if (Step.SizeSquared2D() > FMath::Square(80.f)) Hero->AddMovementInput(Step.GetSafeNormal2D(), 1.f);
}
