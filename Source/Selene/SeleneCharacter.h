#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "SeleneCharacterSettings.h"
#include "Combat/SeleneCombat.h"
#include "SeleneCharacter.generated.h"

class UCameraComponent;
class USpringArmComponent;
struct FStreamableHandle;

UENUM(BlueprintType)
enum class ESeleneCameraMode : uint8
{
	ThirdPerson,
	FirstPerson
};

UENUM(BlueprintType)
enum class ESelenePace : uint8
{
	Walk,
	Jog,
	Sprint
};

/** Navigation and camera controls for the town visual demo. */
UCLASS()
class SELENE_API ASeleneCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	// AdvancedMovement hook: select the CMC subclass without changing animation ownership.
	ASeleneCharacter(const FObjectInitializer& ObjectInitializer = FObjectInitializer::Get());

	UFUNCTION(BlueprintCallable, Category = "Selene|Character")
	void SelectCharacter(FName Name);

	UFUNCTION(BlueprintCallable, Category = "Selene|Character")
	void CycleCharacter();

	/** Set before BeginPlay to start as that roster entry instead of the default (bot heroes). */
	void SetStartCharacter(FName Name) { StartCharacter = Name; }

	/** Set before BeginPlay to make this an unpossessed NPC wearing that roster entry. */
	void SetNpcCharacter(FName Name) { NpcCharacter = Name; }
	bool IsNpc() const { return !NpcCharacter.IsNone(); }

	UFUNCTION(BlueprintPure, Category = "Selene|Character")
	FName GetActiveCharacterName() const { return ActiveCharacterName; }

	/** Roster entry of the active character (read by USeleneSecondaryAnimInstance when it builds its graph). */
	const FSelenePlayableCharacter& GetActiveCharacterEntry() const { return ActiveCharacter; }

	UFUNCTION(BlueprintCallable, Category = "Selene|Camera")
	void SetCameraMode(ESeleneCameraMode NewMode);

	UFUNCTION(BlueprintPure, Category = "Selene|Camera")
	ESeleneCameraMode GetCameraMode() const { return CameraMode; }

	UFUNCTION(BlueprintCallable, Category = "Selene|Camera")
	void ToggleCameraMode();

	UFUNCTION(BlueprintCallable, Category = "Selene|Movement")
	void SetMovementPace(ESelenePace NewPace);

	/** Primary fire pressed: melee combo swing (a press during a swing queues the next) or bow shot (repeats while held). */
	void Attack();
	/** Primary fire released. */
	void StopAttack();
	/** Q / E / R = 0 / 1 / 2. */
	void UseAbility(int32 Index);
	/** Right mouse: tighter over-the-shoulder view, hero faces the crosshair. */
	void SetAiming(bool bAim);

	// --- combat state (read by the HUD, the lane director and bots)
	ESeleneTeam GetTeam() const { return Team; }
	void SetTeam(ESeleneTeam InTeam) { Team = InTeam; }
	bool IsCombatAlive() const { return !bDead && !IsNpc(); }
	bool IsDead() const { return bDead; }
	float GetHealth() const { return Health; }
	float GetMaxHealth() const { return MaxHealth; }
	float GetRespawnRemaining() const { return RespawnTimer; }
	bool IsInCombatStance() const { return bCombatStance; }
	bool IsAiming() const { return bAiming; }
	bool IsStunned() const { return SlowFactor <= 0.f && SlowTimer > 0.f; }
	float GetBuffRemaining() const { return BuffTimer; }
	ESeleneAbilityEffect GetBuffKind() const { return BuffKind; }
	int32 GetAbilityCount() const { return ActiveCharacter.Abilities.Num(); }
	const FSeleneAbility* GetAbility(int32 Index) const { return ActiveCharacter.Abilities.IsValidIndex(Index) ? &ActiveCharacter.Abilities[Index] : nullptr; }
	float GetAbilityCooldown(int32 Index) const { return AbilityCooldowns.IsValidIndex(Index) ? AbilityCooldowns[Index] : 0.f; }
	float GetDashCharges() const;
	/** Applies incoming damage with hit reaction and feedback. Returns the damage taken. */
	float ReceiveDamage(float Amount, const FVector& From, AActor* Instigator, bool bHeavy);
	/** Factor 0 = rooted / stunned. */
	void ApplySlow(float Factor, float Seconds);
	/** Debug: hold a movement input (forward, right in camera space) for Seconds. */
	void DebugMove(float Forward, float Right, float Seconds) { DebugMoveInput = FVector2D(Forward, Right); DebugMoveUntil = DebugTime + Seconds; }

	/** Camera-driven aim: where the crosshair points (first hit up to MaxRange) and the view origin. */
	FVector GetAimPoint(float MaxRange, FVector* OutViewStart = nullptr) const;
	void AddCameraShake(float Trauma) { ShakeTrauma = FMath::Min(1.f, ShakeTrauma + Trauma); }

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Selene|Movement", meta = (ClampMin = "0"))
	float WalkSpeed = 150.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Selene|Movement", meta = (ClampMin = "0"))
	float JogSpeed = 350.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Selene|Movement", meta = (ClampMin = "0"))
	float SprintSpeed = 600.f;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void Landed(const FHitResult& Hit) override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Selene|Camera")
	TObjectPtr<USpringArmComponent> CameraBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Selene|Camera")
	TObjectPtr<UCameraComponent> ThirdPersonCamera;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Selene|Camera")
	TObjectPtr<UCameraComponent> FirstPersonCamera;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Selene|Camera")
	ESeleneCameraMode CameraMode = ESeleneCameraMode::ThirdPerson;

	UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category = "Selene|Movement")
	ESelenePace MovementPace = ESelenePace::Jog;

private:
	void ApplyCharacter(const FSelenePlayableCharacter& Entry, uint64 RequestId);
	void ConfigureBlendAxes();
	void ConfigureBlendAxesOf(class UBlendSpace* Blend);
	/** Speed / direction axis of a blend space (cached; direction INDEX_NONE for 1D). */
	void BlendAxesFor(class UBlendSpace* Blend, int32& OutSpeed, int32& OutDirection);
	TMap<TWeakObjectPtr<class UBlendSpace>, FIntPoint> BlendAxisCache;
	void UpdateSingleNodeAnimation(float DeltaSeconds);
	void TickDebugDrivers(float DeltaSeconds);
	void TickAnimMatch(float DeltaSeconds);
	float AnimMatchTime = -5.f;
	int32 AnimMatchView = INDEX_NONE;
	int32 AnimMatchShot = 0;
	FVector AnimMatchOrigin = FVector::ZeroVector;
	bool bAnimMatchJumped = false;
	float DebugTime = 0.f;
	float NextAutoShot = 0.f;
	float AutoWalkBaseYaw = 0.f;

	// Streamable handles keep all loaded soft assets alive, including inactive jump/land clips.
	TSharedPtr<FStreamableHandle> PendingCharacterLoad;
	TSharedPtr<FStreamableHandle> ActiveCharacterLoad;
	FSelenePlayableCharacter ActiveCharacter;
	FName ActiveCharacterName;
	FName PendingCharacterName;
	FName NpcCharacter;
	FName StartCharacter;
	uint64 CharacterRequestId = 0;
	int32 SpeedAxis = 0;
	int32 DirectionAxis = INDEX_NONE;
	bool bWasFalling = false;
	enum class ESingleNodePhase : uint8 { Ground, Jump, Fall, Land };
	ESingleNodePhase SingleNodePhase = ESingleNodePhase::Ground;

	// Borrowed-clip locomotion (roster WalkLoop etc.): ground loop choice, speed matching and transitions.
	UAnimationAsset* ChooseGroundLoop(float Speed, float& OutPlayRate) const;
	void UpdateLocomotionTransitions(float Speed, float DeltaSeconds);
	void PlayTransition(UAnimSequence* Clip, float BlendIn, float BlendOut);
	float PrevSpeed = 0.f;
	bool bHadInput = false;
	float TransitionCooldown = 0.f;

	// Melee combo (roster Attacks): a standing swing owns DefaultSlot, a moving one the UpperBody slot.
	void TickAttack(float DeltaSeconds);
	/** True while a full-body action (swing, ability, death) owns DefaultSlot and locomotion must not change it. */
	bool IsAttackPlaying() const;
	void TickCombat(float DeltaSeconds);
	void TickCamera(float DeltaSeconds);
	void TickTurnInPlace(float DeltaSeconds);
	void UpdateStance();
	void MeleeStrike(int32 SwingIndex);
	void FireArrow(bool bOverdrive);
	void TryFire();
	void CastAbility(int32 Index, const FVector& Point, const FVector& Dir);
	void FaceAim();
	void Die();
	void Respawn();
	void PreloadCombatAssets();
	void ApplySpeed();
	/** Voice line from the hero's cue set (first cue that exists), with a chance and a minimum gap. */
	void Voice(std::initializer_list<const TCHAR*> Cues, float Chance = 1.f, float MinGap = 1.2f);
	float LastVoiceTime = -100.f;
	UAnimMontage* PlayAction(UAnimSequence* Clip, bool bFullBody, float Rate = 1.f, float BlendIn = 0.08f, float BlendOut = 0.2f);
	ESeleneTeam Team = ESeleneTeam::Dawn;
	float Health = 650.f;
	float MaxHealth = 650.f;
	bool bDead = false;
	float RespawnTimer = 0.f;
	float LastDamageTime = -100.f;
	float CombatTimer = 0.f;
	bool bCombatStance = false;
	bool bAiming = false;
	bool bAttackHeld = false;
	float FireCooldown = 0.f;
	float SlowTimer = 0.f;
	float SlowFactor = 1.f;
	float BuffTimer = 0.f;
	ESeleneAbilityEffect BuffKind = ESeleneAbilityEffect::None;
	TWeakObjectPtr<class UParticleSystemComponent> BuffFx;
	TArray<float> AbilityCooldowns;
	struct FPendingCast { int32 Ability; float Time; FVector Point; FVector Dir; };
	TArray<FPendingCast> PendingCasts;
	struct FPendingPulse { int32 Ability; float Time; FVector Point; };
	TArray<FPendingPulse> Pulses;
	float DashStrikeTimer = 0.f;
	int32 DashStrikeAbility = INDEX_NONE;
	FVector DashStrikeDir = FVector::ForwardVector;
	TArray<FSeleneTarget> DashStrikeHits;
	int32 LeapAbility = INDEX_NONE;
	float ShakeTrauma = 0.f;
	float ShakeTime = 0.f;
	float LandDip = 0.f;
	float CurrentArm = 0.f;
	float CurrentFov = 90.f;
	FVector CurrentSocketOffset = FVector::ZeroVector;
	float TurnInPlaceTimer = 0.f;
	float RegenAccum = 0.f;
	TWeakObjectPtr<class UAnimMontage> ActionMontage;
	bool bActionFullBody = false;
	// Action layer: every swing/ability plays on the masked UpperBody slot; LegWeight (0..1) says how much of the
	// legs follow the clip (1 standing still or committed, 0 while moving). Inputs during a commit window are buffered.
	double ActionLockUntil = 0.0;
	double ActionEndAt = 0.0;
	bool bAbilityAction = false;
	int32 PendingAttacks = 0;
	bool bActionCommitsLegs = false;
	float LegWeight = 0.f;
	struct FBufferedInput { uint8 Kind = 0; int32 Index = 0; double Time = -10.0; };   // Kind 1 attack, 2 ability
	FBufferedInput Buffered;
	double PressTime = -1.0;
	FString PressWhat;
	int32 SwingSerial = 0;
	double HitPauseUntil = 0.0;
	bool bLaneMode = false;
	TWeakObjectPtr<class UParticleSystemComponent> SlowFx;
	bool IsActionLocked() const;
	void LogActionStart(const TCHAR* What);
	void StopAction(float BlendOut);
	void TickActionLayer(float DeltaSeconds);
	TWeakObjectPtr<class UAnimMontage> DashMontage;
	bool bWasDashing = false;
	FVector2D DebugMoveInput = FVector2D::ZeroVector;
	float DebugMoveUntil = 0.f;
	int32 BaseSwitches = 0;
	float AnimLogTimer = 0.f;
	float NaNLogTimer = 0.f;
	UPROPERTY(Transient) TArray<TObjectPtr<UObject>> CombatAssets;
	TWeakObjectPtr<class UAnimMontage> AttackMontage;
	int32 AttackIndex = 0;
	float AttackClipLength = 0.f;
	float AttackResetTimer = 0.f;
	bool bAttackQueued = false;
	float NextAutoAttack = 0.f;
};
