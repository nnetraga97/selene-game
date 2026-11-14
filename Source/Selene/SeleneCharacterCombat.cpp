// Hero combat: primary fire (melee combo or bow), abilities, health, hit reactions, death and respawn,
// combat stance (facing the crosshair) and camera feel. Part of ASeleneCharacter; see SeleneCharacter.h.
#include "SeleneCharacter.h"

#include "Selene.h"
#include "Animation/SeleneSecondaryAnimInstance.h"
#include "Combat/SeleneCombat.h"
#include "Lanes/SeleneLaneDirector.h"
#include "Movement/SeleneMovementComponent.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimSequence.h"
#include "Animation/BlendSpace.h"
#include "Animation/Skeleton.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerStart.h"
#include "GameFramework/SpringArmComponent.h"
#include "Particles/ParticleSystemComponent.h"
#include "TimerManager.h"
#include "HAL/IConsoleManager.h"
#include "Misc/Paths.h"

namespace
{
	TAutoConsoleVariable<int32> CVarAnimLog(TEXT("selene.AnimLog"), 0,
		TEXT("1: log base-animation switches per second, leg weight and action state once a second."));
	TAutoConsoleVariable<int32> CVarInputLog(TEXT("selene.InputLog"), 0,
		TEXT("1: log each attack/ability press and how long until its action started (or that it was dropped)."));
	const double BufferSeconds = 0.35;
	const FName UpperBodyGroup(TEXT("UpperBodyGroup"));
	const TCHAR* const FxRespawn = TEXT("/Game/ParagonMinions/FX/Particles/Minions/Prime_Helix/Abilities/Spawn/FX/P_Prime_Spawn_Landing.P_Prime_Spawn_Landing");
	const TCHAR* const FxDashTrail = TEXT("/Game/ParagonAurora/FX/Particles/Abilities/Dash/FX/P_Aurora_Dash_Flare.P_Aurora_Dash_Flare");
	const TCHAR* const FxSlowed = TEXT("/Game/ParagonMinions/FX/Particles/SharedGameplay/States/Slow/P_Slow_Heroes.P_Slow_Heroes");

	float Smooth(float Current, float Target, float Dt, float Speed) { return FMath::FInterpTo(Current, Target, Dt, Speed); }
}

// ------------------------------------------------------------------ setup

void ASeleneCharacter::PreloadCombatAssets()
{
	CombatAssets.Reset();
	auto Keep = [this](const auto& Soft) { if (!Soft.IsNull()) if (UObject* Obj = Soft.LoadSynchronous()) CombatAssets.Add(Obj); };
	const FSelenePlayableCharacter& C = ActiveCharacter;
	Keep(C.FireClip);
	for (const auto& Clip : C.MovingAttacks) Keep(Clip);
	Keep(C.HitReactFront); Keep(C.HitReactBack); Keep(C.HitReactLeft); Keep(C.HitReactRight); Keep(C.Death);
	Keep(C.StrafeLocomotion); Keep(C.TurnLeft90); Keep(C.TurnRight90); Keep(C.LandMoving);
	Keep(C.DashFwd); Keep(C.DashBwd); Keep(C.DashLeft); Keep(C.DashRight);
	for (const FSeleneAbility& Ability : C.Abilities) Keep(Ability.Clip);
	if (USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(this))
	{
		for (const FSoftObjectPath& Path : { C.ProjectileFx, C.MuzzleFx, C.HitFx }) Combat->Fx(Path);
		for (const FSeleneAbility& Ability : C.Abilities) { Combat->Fx(Ability.CastFx); Combat->Fx(Ability.ImpactFx); }
	}
	// Upper-body swings live in their own slot group, so base crossfades and transitions on DefaultSlot never cancel them.
	if (USkeleton* Skeleton = GetMesh()->GetSkeletalMeshAsset() ? GetMesh()->GetSkeletalMeshAsset()->GetSkeleton() : nullptr)
	{
		Skeleton->AddSlotGroupName(UpperBodyGroup);
		Skeleton->SetSlotGroupName(USeleneSecondaryAnimInstance::UpperBodySlot, UpperBodyGroup);
	}
	bLaneMode = ASeleneLaneDirector::Get(GetWorld()) && !ASeleneLaneDirector::Get(GetWorld())->Lanes.IsEmpty();
	MaxHealth = FMath::Max(1.f, C.MaxHealth);
	if (!bDead) Health = MaxHealth;
	AbilityCooldowns.Init(0.f, C.Abilities.Num());
	PendingCasts.Reset(); Pulses.Reset();
	BuffTimer = 0.f; BuffKind = ESeleneAbilityEffect::None;
	if (UParticleSystemComponent* Fx = BuffFx.Get()) Fx->DeactivateSystem();
	if (auto* Advanced = Cast<USeleneMovementComponent>(GetCharacterMovement())) Advanced->bShowStaminaText = !ASeleneLaneDirector::Get(GetWorld()) || ASeleneLaneDirector::Get(GetWorld())->Lanes.IsEmpty();
}

void ASeleneCharacter::Voice(std::initializer_list<const TCHAR*> Cues, float Chance, float MinGap)
{
	USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(this);
	const float Now = GetWorld()->GetTimeSeconds();
	if (!Combat || ActiveCharacter.VoicePrefix.IsEmpty() || Now - LastVoiceTime < MinGap || FMath::FRand() > Chance) return;
	for (const TCHAR* Cue : Cues)
	{
		const FString Name = FPaths::GetBaseFilename(ActiveCharacter.VoicePrefix) + Cue;
		if (USoundBase* Line = Combat->Sound(ActiveCharacter.VoicePrefix + Cue + TEXT(".") + Name))
		{
			Combat->PlaySoundAt(Line, GetActorLocation(), IsPlayerControlled() ? 0.9f : 0.7f);
			LastVoiceTime = Now;
			return;
		}
	}
}

float ASeleneCharacter::GetDashCharges() const
{
	const auto* Advanced = Cast<USeleneMovementComponent>(GetCharacterMovement());
	return Advanced ? Advanced->GetStamina() : 0.f;
}

UAnimMontage* ASeleneCharacter::PlayAction(UAnimSequence* Clip, bool bFullBody, float Rate, float BlendIn, float BlendOut)
{
	UAnimInstance* Anim = GetMesh()->GetAnimInstance();
	if (!Clip || !Anim) return nullptr;
	// Everything plays on the masked UpperBody slot; bFullBody only asks for the legs while standing still.
	UAnimMontage* Montage = Anim->PlaySlotAnimationAsDynamicMontage(Clip, USeleneSecondaryAnimInstance::UpperBodySlot, BlendIn, BlendOut, Rate, 1, -1.f, 0.f);
	ActionMontage = Montage;
	bActionFullBody = bFullBody;
	bAbilityAction = false;
	ActionEndAt = GetWorld()->GetTimeSeconds() + Clip->GetPlayLength() / FMath::Max(Rate, 0.05f);
	return Montage;
}

bool ASeleneCharacter::IsAttackPlaying() const
{
	// Only death owns DefaultSlot now; locomotion keeps running under every swing and ability.
	return bDead;
}

bool ASeleneCharacter::IsActionLocked() const
{
	return GetWorld() && GetWorld()->GetTimeSeconds() < ActionLockUntil;
}

void ASeleneCharacter::StopAction(float BlendOut)
{
	UAnimInstance* Anim = GetMesh()->GetAnimInstance();
	if (Anim && ActionMontage.IsValid()) Anim->Montage_Stop(BlendOut, ActionMontage.Get());
	ActionMontage.Reset(); AttackMontage.Reset();
	bActionFullBody = false; bActionCommitsLegs = false; bAbilityAction = false;
	++SwingSerial;   // a pending blow from a cancelled swing never lands
}

void ASeleneCharacter::LogActionStart(const TCHAR* What)
{
	if (CVarInputLog.GetValueOnGameThread() == 0 || !IsPlayerControlled() || PressTime < 0.0) return;
	UE_LOG(LogSelene, Log, TEXT("Input %s -> %s started after %.0f ms"), *PressWhat, What, (GetWorld()->GetTimeSeconds() - PressTime) * 1000.0);
	PressTime = -1.0;
}

void ASeleneCharacter::FaceAim()
{
	if (CameraMode != ESeleneCameraMode::ThirdPerson || !Controller) return;
	const float Yaw = Controller->GetControlRotation().Yaw;
	// A turn-in-place step still playing would keep the hips turned under the snapped body (a bow aimed 60-90 degrees
	// off the crosshair): end it with the snap.
	if (FMath::Abs(FRotator::NormalizeAxis(Yaw - GetActorRotation().Yaw)) > 5.f || TurnInPlaceTimer > 0.f)
	{
		if (UAnimInstance* Anim = GetMesh()->GetAnimInstance()) Anim->StopSlotAnimation(0.1f, TEXT("DefaultSlot"));
		TurnInPlaceTimer = 0.f;
	}
	SetActorRotation(FRotator(0.f, Yaw, 0.f));
}

FVector ASeleneCharacter::GetAimPoint(float MaxRange, FVector* OutViewStart) const
{
	FVector ViewLoc = GetActorLocation() + FVector(0, 0, 60.f);
	FRotator ViewRot = Controller ? Controller->GetControlRotation() : GetActorRotation();
	if (const APlayerController* PC = Cast<APlayerController>(Controller)) PC->GetPlayerViewPoint(ViewLoc, ViewRot);
	const FVector Dir = ViewRot.Vector();
	// Start level with the hero so nothing between the camera and the hero blocks the aim.
	const FVector Start = ViewLoc + Dir * FMath::Max(0.f, FVector::DotProduct(GetActorLocation() - ViewLoc, Dir));
	if (OutViewStart) *OutViewStart = Start;
	FHitResult Hit;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(SeleneAim), false, this);
	if (GetWorld()->LineTraceSingleByChannel(Hit, Start, Start + Dir * MaxRange, ECC_Visibility, Params)) return Hit.ImpactPoint;
	return Start + Dir * MaxRange;
}

void ASeleneCharacter::ApplySpeed()
{
	float Speed = JogSpeed;
	switch (MovementPace)
	{
	case ESelenePace::Walk: Speed = WalkSpeed; break;
	case ESelenePace::Sprint: Speed = SprintSpeed; break;
	default: break;
	}
	// Facing the crosshair: move at the speed the strafe clips were authored for, so feet don't slide.
	if (bCombatStance && MovementPace != ESelenePace::Walk)
	{
		UBlendSpace* Strafe = ActiveCharacter.StrafeLocomotion.Get() ? ActiveCharacter.StrafeLocomotion.Get() : ActiveCharacter.Locomotion.Get();
		if (Strafe) Speed = Strafe->GetBlendParameter(1).Max;
	}
	if (bAiming) Speed *= 0.75f;
	if (BuffTimer > 0.f && BuffKind == ESeleneAbilityEffect::Overdrive) Speed *= 1.15f;
	Speed *= SlowFactor;
	if (bDead) Speed = 0.f;
	GetCharacterMovement()->MaxWalkSpeed = FMath::Max(0.f, Speed);
}

// ------------------------------------------------------------------ primary fire

void ASeleneCharacter::Attack()
{
	if (!IsCombatAlive()) return;
	if (IsPlayerControlled() && PressTime < 0.0) { PressTime = GetWorld()->GetTimeSeconds(); PressWhat = TEXT("attack"); }
	bAttackHeld = true;
	CombatTimer = FMath::Max(CombatTimer, 3.5f);
	UpdateStance();
	// Stunned or inside a commit window: remember the press instead of dropping it.
	if (SlowFactor <= 0.f || IsActionLocked())
	{
		if (Buffered.Kind != 2) { Buffered = { 1, 0, GetWorld()->GetTimeSeconds() }; PendingAttacks = FMath::Min(PendingAttacks + 1, 2); }
		return;
	}
	if (ActiveCharacter.Weapon == ESeleneWeapon::Bow) { TryFire(); return; }
	UAnimInstance* Anim = GetMesh()->GetAnimInstance();
	if (!Anim || ActiveCharacter.Attacks.IsEmpty()) return;
	if (auto* Advanced = Cast<USeleneMovementComponent>(GetCharacterMovement()); Advanced && Advanced->IsSliding()) Advanced->StopSlide();
	const int32 Count = ActiveCharacter.Attacks.Num();
	const int32 Index = AttackIndex % Count;
	const bool bMoving = GetVelocity().Size2D() > 150.f || GetCharacterMovement()->IsFalling();
	UAnimSequence* Clip = ActiveCharacter.Attacks[Index].Get();
	if (bMoving && ActiveCharacter.MovingAttacks.IsValidIndex(Index) && ActiveCharacter.MovingAttacks[Index].Get()) Clip = ActiveCharacter.MovingAttacks[Index].Get();
	if (!Clip) return;
	StopAction(0.1f);
	FaceAim();
	const float Rate = 1.2f;
	AttackMontage = PlayAction(Clip, true, Rate, 0.05f, 0.18f);
	AttackClipLength = Clip->GetPlayLength() / Rate;
	AttackResetTimer = AttackClipLength + 0.6f;
	bAttackQueued = false;
	const float HitTime = FMath::Max(AttackClipLength * ActiveCharacter.AttackHitFraction, 0.05f);
	ActionLockUntil = GetWorld()->GetTimeSeconds() + HitTime + 0.05;   // the next swing can start right after the blow
	// Step into the swing on the ground without leaving the walking state.
	if (GetCharacterMovement()->IsMovingOnGround()) GetCharacterMovement()->Velocity += GetActorForwardVector() * 260.f;
	Voice({ TEXT("Effort_Attack"), TEXT("Effort_Swing") }, 0.35f, 1.5f);
	const int32 Serial = ++SwingSerial;
	FTimerHandle StrikeTimer;
	GetWorldTimerManager().SetTimer(StrikeTimer, FTimerDelegate::CreateWeakLambda(this, [this, Index, Serial]() { if (Serial == SwingSerial) MeleeStrike(Index); }), HitTime, false);
	LogActionStart(TEXT("swing"));
	++AttackIndex;
}

void ASeleneCharacter::StopAttack()
{
	bAttackHeld = false;
}

void ASeleneCharacter::TickAttack(float DeltaSeconds)
{
	if (AttackResetTimer > 0.f)
	{
		AttackResetTimer -= DeltaSeconds;
		if (AttackResetTimer <= 0.f) AttackIndex = 0;  // combo dropped: start again from the first swing
	}
	FireCooldown = FMath::Max(0.f, FireCooldown - DeltaSeconds);
	// Swing pause on a hit ends in real time.
	if (HitPauseUntil > 0.0 && GetWorld()->GetRealTimeSeconds() >= HitPauseUntil)
	{
		HitPauseUntil = 0.0;
		if (UAnimInstance* Anim = GetMesh()->GetAnimInstance(); Anim && AttackMontage.IsValid()) Anim->Montage_SetPlayRate(AttackMontage.Get(), 1.2f);
	}
	// Buffered press: run it as soon as the commit window ends; drop it if it is too old.
	if (Buffered.Kind != 0)
	{
		const double Age = GetWorld()->GetTimeSeconds() - Buffered.Time;
		if (Age > (Buffered.Kind == 1 ? 0.6 : BufferSeconds))
		{
			PendingAttacks = 0;
			if (CVarInputLog.GetValueOnGameThread() != 0 && IsPlayerControlled()) UE_LOG(LogSelene, Warning, TEXT("Input %s DROPPED after %.0f ms"), *PressWhat, Age * 1000.0);
			Buffered.Kind = 0; PressTime = -1.0;
		}
		else if (!IsActionLocked() && SlowFactor > 0.f && IsCombatAlive())
		{
			const FBufferedInput Run = Buffered;
			Buffered.Kind = 0;
			if (Run.Kind == 1)
			{
				// Each queued press is its own swing: keep the rest queued behind this one.
				const int32 Left = FMath::Max(0, PendingAttacks - 1);
				PendingAttacks = 0;
				Attack();
				if (Left > 0) { Buffered = { 1, 0, GetWorld()->GetTimeSeconds() }; PendingAttacks = Left; }
			}
			else UseAbility(Run.Index);
		}
	}
	if (ActiveCharacter.Weapon == ESeleneWeapon::Bow)
	{
		if (bAttackHeld && IsCombatAlive() && !IsActionLocked() && SlowFactor > 0.f) TryFire();
		return;
	}
}

void ASeleneCharacter::MeleeStrike(int32 SwingIndex)
{
	if (!IsCombatAlive()) return;
	USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(this);
	if (!Combat) return;
	const int32 Count = FMath::Max(1, ActiveCharacter.Attacks.Num());
	const bool bFinisher = Count >= 3 && SwingIndex == Count - 1;
	TArray<FSeleneTarget> Targets;
	Combat->GatherCone(GetActorLocation(), GetActorForwardVector(), ActiveCharacter.AttackReach * (bFinisher ? 1.15f : 1.f), 0.3f, Team, Targets);
	const float Damage = ActiveCharacter.AttackDamage * (bFinisher ? 1.6f : 1.f);
	int32 Hits = 0;
	for (int32 i = 0; i < Targets.Num() && i < 8; ++i)
	{
		Combat->DealDamage(Targets[i], Damage, Team, GetActorLocation(), this, bFinisher);
		Combat->SpawnFx(ActiveCharacter.HitFx, Targets[i].Location(), (Targets[i].Location() - GetActorLocation()).Rotation(), bFinisher ? 1.3f : 1.f);
		++Hits;
	}
	if (Hits > 0)
	{
		// Weight on contact: pause only the swing for a moment; movement and input keep running.
		if (UAnimInstance* Anim = GetMesh()->GetAnimInstance(); Anim && AttackMontage.IsValid())
		{
			Anim->Montage_SetPlayRate(AttackMontage.Get(), 0.05f);
			HitPauseUntil = GetWorld()->GetRealTimeSeconds() + (bFinisher ? 0.08 : 0.05);
		}
		AddCameraShake(bFinisher ? 0.45f : 0.22f);
	}
}

void ASeleneCharacter::TryFire()
{
	if (FireCooldown > 0.f || !ActiveCharacter.FireClip.Get() || IsActionLocked()) return;
	const bool bOver = BuffTimer > 0.f && BuffKind == ESeleneAbilityEffect::Overdrive;
	FireCooldown = ActiveCharacter.FireInterval * (bOver ? 0.5f : 1.f);
	CombatTimer = FMath::Max(CombatTimer, 3.5f);
	FaceAim();
	PlayAction(ActiveCharacter.FireClip.Get(), false, bOver ? 1.7f : 1.25f, 0.04f, 0.15f);
	LogActionStart(TEXT("shot"));
	FTimerHandle Release;
	GetWorldTimerManager().SetTimer(Release, FTimerDelegate::CreateWeakLambda(this, [this, bOver]() { FireArrow(bOver); }), 0.07f, false);
}

void ASeleneCharacter::FireArrow(bool bOverdrive)
{
	USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(this);
	if (!Combat || !IsCombatAlive()) return;
	const FName Bone = ActiveCharacter.MuzzleBone;
	const FVector Muzzle = GetMesh()->DoesSocketExist(Bone) ? GetMesh()->GetSocketLocation(Bone) : GetActorLocation() + FVector(0, 0, 50.f) + GetActorForwardVector() * 40.f;
	const FVector Aim = GetAimPoint(ActiveCharacter.AttackReach);
	FVector Dir = (Aim - Muzzle).GetSafeNormal();
	if (FVector::DotProduct(Dir, GetActorForwardVector()) < 0.2f) Dir = (GetActorForwardVector() + Dir * 0.5f).GetSafeNormal();
	USeleneCombatSubsystem::FProjectileSpec Spec;
	Spec.TrailFx = ActiveCharacter.ProjectileFx;
	Spec.ImpactFx = ActiveCharacter.HitFx;
	Spec.Speed = ActiveCharacter.ProjectileSpeed;
	Spec.Damage = ActiveCharacter.AttackDamage * (bOverdrive ? 1.35f : 1.f);
	Spec.Range = ActiveCharacter.AttackReach;
	Spec.HitRadius = 28.f;
	Combat->FireStraight(Spec, Muzzle, Dir, Team, this);
	Combat->SpawnFx(ActiveCharacter.MuzzleFx, Muzzle, Dir.Rotation(), 0.8f);
	AddCameraShake(0.06f);
}

// ------------------------------------------------------------------ abilities

void ASeleneCharacter::UseAbility(int32 Index)
{
	const FSeleneAbility* A = GetAbility(Index);
	if (!A || !IsCombatAlive()) return;
	if (IsPlayerControlled() && PressTime < 0.0) { PressTime = GetWorld()->GetTimeSeconds(); PressWhat = FString::Printf(TEXT("ability %d"), Index); }
	if (GetAbilityCooldown(Index) > 0.f) { PressTime = -1.0; return; }
	// Stunned or committed: buffer it. A slide or a swing never blocks an ability: it cancels them.
	if (SlowFactor <= 0.f || (IsActionLocked() && bActionCommitsLegs))
	{
		Buffered = { 2, Index, GetWorld()->GetTimeSeconds() };
		return;
	}
	if (auto* Advanced = Cast<USeleneMovementComponent>(GetCharacterMovement()); Advanced && Advanced->IsSliding()) Advanced->StopSlide();
	StopAction(0.08f);
	CombatTimer = FMath::Max(CombatTimer, 4.f);
	FaceAim();
	FVector Dir = FRotator(0.f, (Controller ? Controller->GetControlRotation() : GetActorRotation()).Yaw, 0.f).Vector();
	FVector Point = GetAimPoint(A->Range);
	if (A->Effect == ESeleneAbilityEffect::LeapSlam || A->Effect == ESeleneAbilityEffect::ArrowRain)
	{
		// Ground target: clamp to range and drop to the floor.
		FVector2D Flat = FVector2D(Point - GetActorLocation());
		if (Flat.Size() > A->Range) Flat = Flat.GetSafeNormal() * A->Range;
		if (Flat.Size() < 150.f) Flat = FVector2D(Dir) * 400.f;
		Point = GetActorLocation() + FVector(Flat, 0.f);
		FHitResult Hit;
		FCollisionQueryParams Params(SCENE_QUERY_STAT(SeleneAbilityGround), false, this);
		FCollisionObjectQueryParams Objects(ECC_WorldStatic);
		if (GetWorld()->LineTraceSingleByObjectType(Hit, Point + FVector(0, 0, 800.f), Point - FVector(0, 0, 3000.f), Objects, Params)) Point = Hit.ImpactPoint;
	}
	AbilityCooldowns[Index] = A->Cooldown;
	bAttackQueued = false;
	if (UAnimSequence* Clip = A->Clip.Get()) PlayAction(Clip, A->bFullBody, A->PlayRate, 0.06f, 0.22f);
	// Locked only until the cast point; movement abilities keep the legs on the clip until they finish.
	const float Cast = A->CastTime / FMath::Max(A->PlayRate, 0.1f);
	bActionCommitsLegs = A->Effect == ESeleneAbilityEffect::DashStrike || A->Effect == ESeleneAbilityEffect::LeapSlam;
	ActionLockUntil = GetWorld()->GetTimeSeconds() + Cast + 0.1 + (A->Effect == ESeleneAbilityEffect::DashStrike ? A->Duration : 0.0);
	// Recovery is short: the clip blends out 0.6 s after the cast point (a leap ends on landing instead).
	bAbilityAction = true;
	ActionEndAt = A->Effect == ESeleneAbilityEffect::LeapSlam ? GetWorld()->GetTimeSeconds() + 3.0
		: FMath::Min(ActionEndAt, ActionLockUntil + 0.6);
	LogActionStart(*A->Name.ToString());
	if (USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(this))
	{
		if (A->Effect != ESeleneAbilityEffect::PiercingShot) Combat->SpawnFx(A->CastFx, GetActorLocation() - FVector(0, 0, 80.f), GetActorRotation(), A->FxScale);
	}
	PendingCasts.Add({ Index, A->CastTime / FMath::Max(A->PlayRate, 0.1f), Point, Dir });
	switch (Index)
	{
	case 0: Voice({ TEXT("Effort_Ability_Q"), TEXT("Effort_Ability_Q_Fire") }, 0.8f, 0.5f); break;
	case 1: Voice({ TEXT("Effort_Ability_E"), TEXT("Effort_Ability_RMB_Loose"), TEXT("Effort_Ability_RMB") }, 0.8f, 0.5f); break;
	default: Voice({ TEXT("Effort_Ability_Ultimate"), TEXT("Effort_Ability_Ultimate_Activate") }, 1.f, 0.f); break;
	}
}

void ASeleneCharacter::CastAbility(int32 Index, const FVector& Point, const FVector& Dir)
{
	const FSeleneAbility* A = GetAbility(Index);
	USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(this);
	if (!A || !Combat || !IsCombatAlive()) return;
	const FVector Feet = GetActorLocation() - FVector(0, 0, GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
	TArray<FSeleneTarget> Targets;
	switch (A->Effect)
	{
	case ESeleneAbilityEffect::DashStrike:
		DashStrikeAbility = Index;
		DashStrikeTimer = FMath::Max(A->Duration, 0.1f);
		DashStrikeDir = Dir.GetSafeNormal2D();
		DashStrikeHits.Reset();
		SetActorRotation(DashStrikeDir.Rotation());
		Combat->AttachFx(FSoftObjectPath(FxDashTrail), GetMesh(), NAME_None, 1.f);
		AddCameraShake(0.2f);
		break;
	case ESeleneAbilityEffect::Nova:
		Combat->GatherEnemies(GetActorLocation(), A->Radius, Team, Targets);
		for (const FSeleneTarget& T : Targets)
		{
			Combat->DealDamage(T, A->Damage, Team, GetActorLocation(), this, true);
			Combat->Slow(T, 0.45f, A->Duration);
			if (A->StunSeconds > 0.f) Combat->Stun(T, A->StunSeconds);
		}
		Combat->SpawnFx(A->ImpactFx, Feet, FRotator::ZeroRotator, A->FxScale);
		if (Targets.Num()) Combat->HitStop(this, 0.07f);
		AddCameraShake(0.4f);
		break;
	case ESeleneAbilityEffect::LeapSlam:
	{
		// Ballistic arc that lands on the target point in a fixed time.
		const float Gravity = FMath::Abs(GetCharacterMovement()->GetGravityZ());
		const float Time = 0.7f;
		const FVector Delta = Point - Feet;
		FVector Launch = FVector(Delta.X, Delta.Y, 0.f) / Time;
		Launch.Z = (Delta.Z + 0.5f * Gravity * Time * Time) / Time;
		LeapAbility = Index;
		LaunchCharacter(Launch, true, true);
		Combat->AttachFx(FSoftObjectPath(TEXT("/Game/ParagonAurora/FX/Particles/Abilities/Leap/FX/P_Aurora_Leap_Trail.P_Aurora_Leap_Trail")), GetMesh(), NAME_None, 1.f);
		break;
	}
	case ESeleneAbilityEffect::ArrowRain:
		Combat->SpawnFx(A->ImpactFx, Point, FRotator::ZeroRotator, A->FxScale);
		for (int32 Pulse = 0; Pulse < 4; ++Pulse) Pulses.Add({ Index, 0.35f + Pulse * 0.35f, Point });
		break;
	case ESeleneAbilityEffect::PiercingShot:
	{
		const FName Bone = ActiveCharacter.MuzzleBone;
		const FVector Muzzle = GetMesh()->DoesSocketExist(Bone) ? GetMesh()->GetSocketLocation(Bone) : GetActorLocation() + FVector(0, 0, 50.f);
		const FVector Aim = GetAimPoint(A->Range);
		USeleneCombatSubsystem::FProjectileSpec Spec;
		Spec.TrailFx = A->ImpactFx;
		Spec.ImpactFx = ActiveCharacter.HitFx;
		Spec.FxScale = A->FxScale;
		Spec.Speed = 14000.f;
		Spec.Damage = A->Damage;
		Spec.Range = A->Range;
		Spec.HitRadius = 60.f;
		Spec.bPierce = true;
		Spec.bHitWorld = true;
		Spec.bHeavy = true;
		Combat->FireStraight(Spec, Muzzle, (Aim - Muzzle).GetSafeNormal(), Team, this);
		Combat->SpawnFx(A->CastFx, Muzzle, (Aim - Muzzle).Rotation(), A->FxScale);
		AddCameraShake(0.3f);
		break;
	}
	case ESeleneAbilityEffect::Overdrive:
	case ESeleneAbilityEffect::Guard:
		BuffKind = A->Effect;
		BuffTimer = A->Duration;
		if (UParticleSystemComponent* Old = BuffFx.Get()) Old->DeactivateSystem();
		BuffFx = Combat->AttachFx(A->ImpactFx, GetMesh(), NAME_None, A->FxScale);
		if (A->Effect == ESeleneAbilityEffect::Guard)
		{
			Combat->GatherEnemies(GetActorLocation(), A->Radius, Team, Targets);
			for (const FSeleneTarget& T : Targets)
			{
				Combat->DealDamage(T, A->Damage, Team, GetActorLocation(), this, true);
				Combat->Stun(T, 0.8f);
			}
			Combat->SpawnFx(A->CastFx, Feet, FRotator::ZeroRotator, A->FxScale);
			AddCameraShake(0.35f);
		}
		ApplySpeed();
		break;
	default:
		break;
	}
}

void ASeleneCharacter::Landed(const FHitResult& Hit)
{
	const float FallSpeed = -GetVelocity().Z;
	Super::Landed(Hit);
	LandDip = FMath::Clamp(FallSpeed / 1000.f * 16.f, 0.f, 20.f);
	if (FallSpeed > 950.f) { AddCameraShake(0.15f); Voice({ TEXT("Effort_LandHeavy"), TEXT("Effort_Land") }, 0.6f); }
	if (LeapAbility != INDEX_NONE)
	{
		ActionEndAt = GetWorld()->GetTimeSeconds() + 0.35;   // land, then hand the body back
		bActionCommitsLegs = false;
		const FSeleneAbility* A = GetAbility(LeapAbility);
		LeapAbility = INDEX_NONE;
		USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(this);
		if (A && Combat)
		{
			TArray<FSeleneTarget> Targets;
			Combat->GatherEnemies(GetActorLocation(), A->Radius, Team, Targets);
			for (const FSeleneTarget& T : Targets)
			{
				Combat->DealDamage(T, A->Damage, Team, GetActorLocation(), this, true);
				Combat->Stun(T, A->Duration);
			}
			Combat->SpawnFx(A->ImpactFx, Hit.ImpactPoint, FRotator::ZeroRotator, A->FxScale);
			Combat->HitStop(this, 0.08f);
			AddCameraShake(0.7f);
		}
	}
}

// ------------------------------------------------------------------ health

float ASeleneCharacter::ReceiveDamage(float Amount, const FVector& From, AActor* Instigator, bool bHeavy)
{
	if (!IsCombatAlive() || Amount <= 0.f) return 0.f;
	if (BuffTimer > 0.f && BuffKind == ESeleneAbilityEffect::Guard) Amount *= 0.4f;
	Health -= Amount;
	LastDamageTime = GetWorld()->GetTimeSeconds();
	CombatTimer = FMath::Max(CombatTimer, 2.5f);
	if (Health <= 0.f)
	{
		Die();
		return Amount + Health;
	}
	// Flinch: an additive upper-body react that never interrupts an action and never locks input.
	UAnimInstance* Anim = GetMesh()->GetAnimInstance();
	const bool bBusy = bDead || (ActionMontage.IsValid() && Anim && Anim->Montage_IsActive(ActionMontage.Get()));
	if (!bBusy && Anim)
	{
		const FVector To = (From - GetActorLocation()).GetSafeNormal2D();
		const float F = FVector::DotProduct(GetActorForwardVector(), To), R = FVector::DotProduct(GetActorRightVector(), To);
		const FSelenePlayableCharacter& C = ActiveCharacter;
		UAnimSequence* Clip = FMath::Abs(F) >= FMath::Abs(R) ? (F >= 0.f ? C.HitReactFront.Get() : C.HitReactBack.Get())
			: (R >= 0.f ? C.HitReactRight.Get() : C.HitReactLeft.Get());
		if (Clip) Anim->PlaySlotAnimationAsDynamicMontage(Clip, USeleneSecondaryAnimInstance::UpperBodySlot, 0.05f, 0.2f, bHeavy ? 1.2f : 1.5f, 1, -1.f, 0.f);
	}
	if (IsPlayerControlled())
	{
		AddCameraShake(bHeavy ? 0.35f : 0.12f);
	}
	Voice({ bHeavy ? TEXT("Effort_PainHeavy") : TEXT("Effort_Pain"), TEXT("Effort_Pain") }, bHeavy ? 0.7f : 0.25f, 1.6f);
	return Amount;
}

void ASeleneCharacter::ApplySlow(float Factor, float Seconds)
{
	if (!IsCombatAlive()) return;
	SlowFactor = FMath::Min(SlowFactor, Factor);
	SlowTimer = FMath::Max(SlowTimer, Seconds);
	ApplySpeed();
	// One state effect per hero (it used to stack a new one per hit): stunned shows the stun loop, slowed the slow.
	if (UParticleSystemComponent* Old = SlowFx.Get()) Old->DestroyComponent();
	if (USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(this))
	{
		SlowFx = Combat->AttachFx(Factor <= 0.f ? FSoftObjectPath(TEXT("/Game/ParagonMinions/FX/Particles/SharedGameplay/States/Stun/P_StunnedLoop.P_StunnedLoop"))
			: FSoftObjectPath(FxSlowed), GetMesh(), NAME_None, 1.f);
		if (Factor <= 0.f) if (UParticleSystemComponent* Fx = SlowFx.Get()) Fx->SetRelativeLocation(FVector(0, 0, 200.f));
	}
	if (Factor <= 0.f) { StopAction(0.15f); }
}

void ASeleneCharacter::Die()
{
	bDead = true;
	Health = 0.f;
	RespawnTimer = 8.f;
	bAttackHeld = false; bAttackQueued = false; bAiming = false;
	PendingCasts.Reset(); Pulses.Reset(); DashStrikeTimer = 0.f; LeapAbility = INDEX_NONE;
	BuffTimer = 0.f;
	if (UParticleSystemComponent* Fx = BuffFx.Get()) Fx->DeactivateSystem();
	if (UAnimInstance* Anim = GetMesh()->GetAnimInstance()) Anim->StopAllMontages(0.1f);
	GetCharacterMovement()->StopMovementImmediately();
	GetCharacterMovement()->DisableMovement();
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Pawn, ECR_Ignore);
	if (UAnimSequence* Death = ActiveCharacter.Death.Get())
	{
		UAnimInstance* Anim = GetMesh()->GetAnimInstance();
		ActionMontage = Anim ? Anim->PlaySlotAnimationAsDynamicMontage(Death, TEXT("DefaultSlot"), 0.1f, 0.f, 1.f, 1, -1.f, 0.f) : nullptr;
		bActionFullBody = true;
	}
	UpdateStance();
	if (USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(this))
	{
		if (IsPlayerControlled())
		{
			Combat->Announce(TEXT("You were slain"), FLinearColor(1.f, 0.3f, 0.3f), 3.f, false);
		}
		else Combat->Announce(FString::Printf(TEXT("%s %s slain"), Team == ESeleneTeam::Dawn ? TEXT("Ally") : TEXT("Enemy"), *ActiveCharacterName.ToString()),
			Team == ESeleneTeam::Dawn ? FLinearColor(1.f, 0.45f, 0.4f) : FLinearColor(0.45f, 0.9f, 1.f), 3.f, false);
		Combat->SpawnFx(TEXT("/Game/ParagonMinions/FX/Particles/SharedGameplay/States/Death/FX/P_Death_Default.P_Death_Default"), GetActorLocation(), FRotator::ZeroRotator, 1.f);
	}
	LastVoiceTime = -100.f;
	Voice({ TEXT("Effort_Death"), TEXT("Death") });
	UE_LOG(LogSelene, Log, TEXT("Hero %s died."), *ActiveCharacterName.ToString());
}

void ASeleneCharacter::Respawn()
{
	FTransform Spawn = GetActorTransform();
	if (Team == ESeleneTeam::Dawn)
	{
		if (TActorIterator<APlayerStart> It(GetWorld()); It) Spawn = It->GetActorTransform();
	}
	else if (const ASeleneLaneDirector* Director = ASeleneLaneDirector::Get(GetWorld()))
	{
		const FVector Base = Director->DuskBase + FVector(-1200.f, 0.f, 0.f);
		Spawn = FTransform(FRotator(0, 180, 0), FVector(Base.X, Base.Y, Director->TraceGround(FVector2D(Base), 3000.f, 0.f) + 100.f));
	}
	bDead = false;
	Health = MaxHealth;
	SlowFactor = 1.f; SlowTimer = 0.f;
	for (float& Cooldown : AbilityCooldowns) Cooldown = 0.f;
	if (UAnimInstance* Anim = GetMesh()->GetAnimInstance()) Anim->StopAllMontages(0.f);
	ActionMontage.Reset(); bActionFullBody = false;
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
	SetActorLocationAndRotation(Spawn.GetLocation() + FVector(0, 0, 10.f), FRotator(0, Spawn.Rotator().Yaw, 0), false, nullptr, ETeleportType::TeleportPhysics);
	if (Controller) Controller->SetControlRotation(FRotator(-10.f, Spawn.Rotator().Yaw, 0));
	GetCharacterMovement()->SetMovementMode(MOVE_Walking);
	ApplySpeed();
	if (USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(this))
	{
		Combat->SpawnFx(FxRespawn, GetActorLocation() - FVector(0, 0, 85.f), FRotator::ZeroRotator, 0.7f);
		if (IsPlayerControlled())
		{
			Combat->Announce(TEXT("Back in the fight"), FLinearColor(0.6f, 1.f, 0.7f), 2.f, false);
		}
	}
}

// ------------------------------------------------------------------ per frame

void ASeleneCharacter::SetAiming(bool bAim)
{
	if (bAim && !IsCombatAlive()) return;
	bAiming = bAim;
	if (bAiming) CombatTimer = FMath::Max(CombatTimer, 1.f);
	UpdateStance();
	ApplySpeed();
}

void ASeleneCharacter::UpdateStance()
{
	const auto* Advanced = Cast<USeleneMovementComponent>(GetCharacterMovement());
	const bool bSliding = Advanced && (Advanced->IsSliding() || Advanced->IsSlideExitPlaying());
	// Lane maps: always face the crosshair (one locomotion mode, no flips). Elsewhere: only after fighting or aiming.
	const bool bWant = !bDead && !IsNpc() && CameraMode == ESeleneCameraMode::ThirdPerson && !bSliding
		&& (bLaneMode || ((bAiming || CombatTimer > 0.f) && MovementPace != ESelenePace::Sprint));
	if (bWant == bCombatStance) return;
	bCombatStance = bWant;
	ApplySpeed();
	if (CameraMode != ESeleneCameraMode::ThirdPerson) return;
	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->bOrientRotationToMovement = !bCombatStance;
	Move->bUseControllerDesiredRotation = bCombatStance;
	Move->RotationRate = FRotator(0.f, bCombatStance ? 900.f : 500.f, 0.f);
	if (USeleneSecondaryAnimInstance* Anim = Cast<USeleneSecondaryAnimInstance>(GetMesh()->GetAnimInstance()); Anim && !Move->IsFalling())
	{
		Anim->StartCrossfade(0.22f);
	}
}

void ASeleneCharacter::TickTurnInPlace(float DeltaSeconds)
{
	UCharacterMovementComponent* Move = GetCharacterMovement();
	if (!bCombatStance || !Controller) return;
	const bool bIdle = GetVelocity().Size2D() < 10.f && !Move->IsFalling() && !IsAttackPlaying();
	if (!bIdle)
	{
		TurnInPlaceTimer = 0.f;
		Move->bUseControllerDesiredRotation = true;
		Move->RotationRate = FRotator(0.f, 900.f, 0.f);
		return;
	}
	const float Delta = FRotator::NormalizeAxis(Controller->GetControlRotation().Yaw - GetActorRotation().Yaw);
	if (TurnInPlaceTimer > 0.f)
	{
		TurnInPlaceTimer -= DeltaSeconds;
		Move->bUseControllerDesiredRotation = true;
		Move->RotationRate = FRotator(0.f, 300.f, 0.f);
		if (FMath::Abs(Delta) < 4.f) TurnInPlaceTimer = 0.f;
		return;
	}
	// Feet stay planted for small aim changes; past 65 degrees the hero steps round with a turn clip.
	Move->bUseControllerDesiredRotation = false;
	if (FMath::Abs(Delta) > 65.f || bAiming)
	{
		UAnimSequence* Turn = Delta < 0.f ? ActiveCharacter.TurnLeft90.Get() : ActiveCharacter.TurnRight90.Get();
		// Turn steps play on DefaultSlot (legs) so they never touch the action layer.
		if (FMath::Abs(Delta) > 65.f && Turn) if (UAnimInstance* Anim = GetMesh()->GetAnimInstance())
			Anim->PlaySlotAnimationAsDynamicMontage(Turn, TEXT("DefaultSlot"), 0.1f, 0.2f, 1.3f, 1, -1.f, 0.f);
		TurnInPlaceTimer = bAiming ? 0.05f : 0.45f;
		Move->bUseControllerDesiredRotation = true;
	}
}

void ASeleneCharacter::TickCamera(float DeltaSeconds)
{
	if (!IsPlayerControlled() || CameraMode != ESeleneCameraMode::ThirdPerson) return;
	const bool bLanes = ASeleneLaneDirector::Get(GetWorld()) && ASeleneLaneDirector::Get(GetWorld())->GetObjectives().bHasLanes;
	const float Boom = ActiveCharacter.BoomLength;
	float ArmTarget = Boom;
	FVector SocketTarget(0.f, 0.f, 0.f);
	float FovTarget = 90.f;
	if (bLanes || bCombatStance)
	{
		// Over the right shoulder, like a third-person shooter; tighter while aiming.
		ArmTarget = bAiming ? 175.f : Boom * 0.82f;
		SocketTarget = bAiming ? FVector(0.f, 62.f, 18.f) : FVector(0.f, 48.f, 22.f);
		FovTarget = bAiming ? 72.f : 90.f;
	}
	if (bDead) { ArmTarget = Boom * 1.3f; SocketTarget = FVector(0.f, 0.f, 80.f); }
	if (CurrentArm <= 0.f) { CurrentArm = CameraBoom->TargetArmLength; CurrentFov = ThirdPersonCamera->FieldOfView; }
	CurrentArm = Smooth(CurrentArm, ArmTarget, DeltaSeconds, 9.f);
	CurrentSocketOffset = FMath::VInterpTo(CurrentSocketOffset, SocketTarget, DeltaSeconds, 9.f);
	CurrentFov = Smooth(CurrentFov, FovTarget, DeltaSeconds, 10.f);
	CameraBoom->TargetArmLength = CurrentArm;
	CameraBoom->SocketOffset = CurrentSocketOffset;
	if (auto* Advanced = Cast<USeleneMovementComponent>(GetCharacterMovement())) Advanced->BaseFOV = CurrentFov;
	else ThirdPersonCamera->SetFieldOfView(CurrentFov);
	// Trauma shake (squared for a punchy falloff) and landing dip.
	ShakeTime += DeltaSeconds;
	ShakeTrauma = FMath::Max(0.f, ShakeTrauma - DeltaSeconds * 1.8f);
	LandDip = FMath::Max(0.f, LandDip - DeltaSeconds * 60.f);
	const float S = ShakeTrauma * ShakeTrauma;
	const FVector Offset(0.f, FMath::PerlinNoise1D(ShakeTime * 23.f) * 9.f * S, FMath::PerlinNoise1D(ShakeTime * 19.f + 7.f) * 9.f * S - LandDip);
	ThirdPersonCamera->SetRelativeLocationAndRotation(Offset, FRotator(FMath::PerlinNoise1D(ShakeTime * 17.f + 3.f) * 2.f * S, 0.f,
		FMath::PerlinNoise1D(ShakeTime * 21.f + 11.f) * 3.f * S));
}

void ASeleneCharacter::TickCombat(float DeltaSeconds)
{
	if (IsNpc()) return;
	const float Now = GetWorld()->GetTimeSeconds();
	if (bDead)
	{
		// Hold the last frame of the death clip, then come back at base.
		if (UAnimInstance* Anim = GetMesh()->GetAnimInstance(); Anim && ActionMontage.IsValid() && ActionMontage->GetPlayLength() > 0.f)
		{
			if (Anim->Montage_GetPosition(ActionMontage.Get()) >= ActionMontage->GetPlayLength() - 0.06f) Anim->Montage_Pause(ActionMontage.Get());
		}
		RespawnTimer -= DeltaSeconds;
		if (RespawnTimer <= 0.f) Respawn();
		TickCamera(DeltaSeconds);
		return;
	}
	CombatTimer = FMath::Max(0.f, CombatTimer - DeltaSeconds);
	for (float& Cooldown : AbilityCooldowns) Cooldown = FMath::Max(0.f, Cooldown - DeltaSeconds);
	if (SlowTimer > 0.f)
	{
		SlowTimer -= DeltaSeconds;
		if (SlowTimer <= 0.f)
		{
			SlowFactor = 1.f; ApplySpeed();
			if (UParticleSystemComponent* Fx = SlowFx.Get()) Fx->DestroyComponent();
		}
	}
	if (BuffTimer > 0.f)
	{
		BuffTimer -= DeltaSeconds;
		if (BuffTimer <= 0.f)
		{
			BuffKind = ESeleneAbilityEffect::None;
			if (UParticleSystemComponent* Fx = BuffFx.Get()) Fx->DeactivateSystem();
			ApplySpeed();
		}
	}
	// Out of combat for 6 s: regenerate; much faster near your own base.
	if (Health < MaxHealth)
	{
		float Regen = Now - LastDamageTime > 6.f ? 25.f : 0.f;
		if (const ASeleneLaneDirector* Director = ASeleneLaneDirector::Get(GetWorld()))
		{
			const FVector Base = Team == ESeleneTeam::Dawn ? Director->DawnBase : Director->DuskBase;
			if (!Base.IsZero() && FVector2D::Distance(FVector2D(Base), FVector2D(GetActorLocation())) < 2200.f) Regen = 150.f;
		}
		Health = FMath::Min(MaxHealth, Health + Regen * DeltaSeconds);
	}
	for (int32 i = PendingCasts.Num() - 1; i >= 0; --i)
	{
		PendingCasts[i].Time -= DeltaSeconds;
		if (PendingCasts[i].Time > 0.f) continue;
		const FPendingCast Cast = PendingCasts[i];
		PendingCasts.RemoveAt(i);
		CastAbility(Cast.Ability, Cast.Point, Cast.Dir);
	}
	if (USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(this))
	{
		for (int32 i = Pulses.Num() - 1; i >= 0; --i)
		{
			Pulses[i].Time -= DeltaSeconds;
			if (Pulses[i].Time > 0.f) continue;
			const FPendingPulse Pulse = Pulses[i];
			Pulses.RemoveAt(i);
			if (const FSeleneAbility* A = GetAbility(Pulse.Ability))
			{
				TArray<FSeleneTarget> Targets;
				Combat->GatherEnemies(Pulse.Point + FVector(0, 0, 90.f), A->Radius, Team, Targets);
				for (const FSeleneTarget& T : Targets)
				{
					Combat->DealDamage(T, A->Damage / 4.f, Team, Pulse.Point + FVector(0, 0, 400.f), this, false);
					Combat->Slow(T, 0.6f, 1.2f);
				}
			}
		}
		if (DashStrikeTimer > 0.f)
		{
			DashStrikeTimer -= DeltaSeconds;
			if (const FSeleneAbility* A = GetAbility(DashStrikeAbility))
			{
				const float Speed = A->Range / FMath::Max(A->Duration, 0.1f);
				GetCharacterMovement()->Velocity = FVector(DashStrikeDir.X * Speed, DashStrikeDir.Y * Speed, GetCharacterMovement()->Velocity.Z);
				TArray<FSeleneTarget> Targets;
				Combat->GatherEnemies(GetActorLocation(), A->Radius, Team, Targets);
				for (const FSeleneTarget& T : Targets)
				{
					if (DashStrikeHits.Contains(T)) continue;
					DashStrikeHits.Add(T);
					Combat->DealDamage(T, A->Damage, Team, GetActorLocation(), this, true);
					Combat->Stun(T, 0.5f);
					Combat->SpawnFx(ActiveCharacter.HitFx, T.Location(), DashStrikeDir.Rotation(), 1.2f);
					Combat->HitStop(this, 0.04f);
					AddCameraShake(0.15f);
				}
			}
			if (DashStrikeTimer <= 0.f)
			{
				GetCharacterMovement()->Velocity *= 0.25f;
				DashStrikeAbility = INDEX_NONE;
			}
		}
	}
	TickActionLayer(DeltaSeconds);
	UpdateStance();
	TickTurnInPlace(DeltaSeconds);
	TickCamera(DeltaSeconds);
}

void ASeleneCharacter::TickActionLayer(float DeltaSeconds)
{
	UAnimInstance* Anim = GetMesh()->GetAnimInstance();
	USeleneSecondaryAnimInstance* Layered = Cast<USeleneSecondaryAnimInstance>(Anim);
	auto* Move = Cast<USeleneMovementComponent>(GetCharacterMovement());
	if (!Anim || !Move) return;
	const bool bActive = ActionMontage.IsValid() && Anim->Montage_IsActive(ActionMontage.Get());
	if (!bActive) { bActionFullBody = false; bActionCommitsLegs = false; }
	const bool bDashing = Move->IsDashing();

	// Dash start: a directional dash clip on the action layer (legs included) for the dash's length.
	if (bDashing && !bWasDashing && !bActionCommitsLegs)
	{
		const FVector Local = GetActorRotation().UnrotateVector(Move->Velocity.GetSafeNormal2D());
		const FSelenePlayableCharacter& C = ActiveCharacter;
		UAnimSequence* Clip = FMath::Abs(Local.X) >= FMath::Abs(Local.Y) ? (Local.X >= 0.f ? C.DashFwd.Get() : C.DashBwd.Get())
			: (Local.Y >= 0.f ? C.DashRight.Get() : C.DashLeft.Get());
		if (!IsActionLocked()) StopAction(0.06f);
		if (Clip)
		{
			DashMontage = Anim->PlaySlotAnimationAsDynamicMontage(Clip, USeleneSecondaryAnimInstance::UpperBodySlot, 0.05f, 0.18f,
				FMath::Max(1.f, Clip->GetPlayLength() / FMath::Max(Move->DashSeconds + 0.12f, 0.05f)), 1, -1.f, 0.f);
		}
	}
	bWasDashing = bDashing;
	// After the commit window, jumping, falling or dashing takes the body back from the action; so does moving after an
	// ability, and every action ends at its recovery time even if the clip is longer.
	const double Now = GetWorld()->GetTimeSeconds();
	const bool bMoveInput = Move->GetCurrentAcceleration().SizeSquared2D() > 1.f;
	if (bActive && !IsActionLocked() && !bActionCommitsLegs &&
		(Move->IsFalling() || bDashing || Now >= ActionEndAt || (bAbilityAction && bMoveInput && Now >= ActionLockUntil + 0.15)))
	{
		StopAction(0.2f);
	}

	// Leg weight: the clip owns the legs while standing still, while committed (charge, leap) and during a dash clip.
	const bool bDashClip = DashMontage.IsValid() && Anim->Montage_IsActive(DashMontage.Get());
	const bool bStill = GetVelocity().Size2D() < 80.f && Move->GetCurrentAcceleration().SizeSquared2D() < 1.f && Move->IsMovingOnGround();
	const float Target = (bActive && (bActionCommitsLegs || (bActionFullBody && bStill))) || bDashClip ? 1.f : 0.f;
	LegWeight = FMath::FInterpConstantTo(LegWeight, Target, DeltaSeconds, Target > LegWeight ? 10.f : 6.f);
	if (Layered) Layered->LegWeight = LegWeight;
	if (CVarAnimLog.GetValueOnGameThread() != 0 && IsPlayerControlled())
	{
		AnimLogTimer += DeltaSeconds;
		if (AnimLogTimer >= 1.f)
		{
			UE_LOG(LogSelene, Log, TEXT("AnimLog switches/s=%d legs=%.2f action=%s locked=%d dash=%d speed=%.0f base=%s"), BaseSwitches, LegWeight,
				*GetNameSafe(ActionMontage.Get()), IsActionLocked() ? 1 : 0, bDashing ? 1 : 0, GetVelocity().Size2D(),
				GetMesh()->GetSingleNodeInstance() ? *GetNameSafe(GetMesh()->GetSingleNodeInstance()->GetAnimationAsset()) : TEXT("-"));
			AnimLogTimer = 0.f; BaseSwitches = 0;
		}
	}
}
