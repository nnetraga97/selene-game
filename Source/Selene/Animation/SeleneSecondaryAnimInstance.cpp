#include "Animation/SeleneSecondaryAnimInstance.h"

#include "Selene.h"
#include "SeleneCharacter.h"
#include "SeleneCharacterSettings.h"
#include "AnimNode_KawaiiPhysics.h"
#include "AnimNodes/AnimNode_Slot.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimNodeSpaceConversions.h"
#include "Animation/AnimSingleNodeInstanceProxy.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "ReferenceSkeleton.h"
#include "HAL/IConsoleManager.h"
#include <atomic>

namespace
{
	/** A blended into B by Alpha, tolerating unnormalized or degenerate inputs (BlendWith checks both). */
	FTransform SafeBlend(FTransform A, FTransform B, float Alpha)
	{
		if (A.GetRotation().SizeSquared() < 0.25 || B.GetRotation().SizeSquared() < 0.25 || A.ContainsNaN() || B.ContainsNaN()) return A;
		A.NormalizeRotation(); B.NormalizeRotation();
		A.BlendWith(B, Alpha);
		A.NormalizeRotation();
		return A;
	}

	TAutoConsoleVariable<int32> CVarSecondaryDebug(TEXT("selene.SecondaryDebug"), 0,
		TEXT("1: log each Kawaii chain's largest simulated-vs-animated bone displacement (cm) every 0.5 s."));

	/** Component-space reference transform of a bone (accumulated local ref pose). */
	FTransform RefComponentSpace(const FReferenceSkeleton& Ref, int32 Index)
	{
		FTransform Result = FTransform::Identity;
		while (Index != INDEX_NONE)
		{
			Result = Result * Ref.GetRefBonePose()[Index];
			Index = Ref.GetParentIndex(Index);
		}
		return Result;
	}

	EBoneForwardAxis DominantAxis(const FVector& Dir)
	{
		const FVector A = Dir.GetAbs();
		if (A.X >= A.Y && A.X >= A.Z) return Dir.X >= 0 ? EBoneForwardAxis::X_Positive : EBoneForwardAxis::X_Negative;
		if (A.Y >= A.Z) return Dir.Y >= 0 ? EBoneForwardAxis::Y_Positive : EBoneForwardAxis::Y_Negative;
		return Dir.Z >= 0 ? EBoneForwardAxis::Z_Positive : EBoneForwardAxis::Z_Negative;
	}

	int32 FirstChild(const FReferenceSkeleton& Ref, int32 Parent)
	{
		for (int32 i = Parent + 1; i < Ref.GetNum(); ++i)
		{
			if (Ref.GetParentIndex(i) == Parent) return i;
		}
		return INDEX_NONE;
	}
}

const FName USeleneSecondaryAnimInstance::UpperBodySlot(TEXT("UpperBody"));

namespace { std::atomic<int32> GNaNBones{0}; }
int32 USeleneSecondaryAnimInstance::ConsumeNaNBones() { return GNaNBones.exchange(0); }

/**
 * A slot whose montage only drives the spine and everything above it. Bones below (root, pelvis, legs) keep the
 * source pose, and the first two spine bones blend partially so the twist spreads up the back.
 */
struct FSeleneUpperBodySlot : public FAnimNode_Slot
{
	virtual void CacheBones_AnyThread(const FAnimationCacheBonesContext& Context) override
	{
		FAnimNode_Slot::CacheBones_AnyThread(Context);
		const FBoneContainer& Bones = Context.AnimInstanceProxy->GetRequiredBones();
		const FReferenceSkeleton& Ref = Bones.GetReferenceSkeleton();
		int32 SpineRoot = INDEX_NONE;
		for (const TCHAR* Name : { TEXT("spine_01"), TEXT("Spine"), TEXT("spine"), TEXT("Spine1"), TEXT("spine_02") })
		{
			SpineRoot = Ref.FindBoneIndex(Name);
			if (SpineRoot != INDEX_NONE) break;
		}
		Mask.Reset();
		Mask.SetNumZeroed(Bones.GetCompactPoseNumBones());
		for (int32 i = 0; i < Mask.Num(); ++i)
		{
			const int32 MeshIndex = Bones.MakeMeshPoseIndex(FCompactPoseBoneIndex(i)).GetInt();
			if (SpineRoot == INDEX_NONE) { Mask[i] = 1.f; continue; }
			int32 Depth = 0;
			for (int32 B = MeshIndex; B != INDEX_NONE; B = Ref.GetParentIndex(B), ++Depth)
			{
				if (B == SpineRoot) { Mask[i] = Depth == 0 ? 0.35f : Depth == 1 ? 0.7f : 1.f; break; }
			}
		}
	}

	virtual void Evaluate_AnyThread(FPoseContext& Output) override
	{
		bHaveBase = false;
		FAnimNode_Slot::Evaluate_AnyThread(Output);
		// Cheap guard: a bad montage pose must never reach the rest of the graph.
		for (FCompactPoseBoneIndex Index : Output.Pose.ForEachBoneIndex())
		{
			if (Output.Pose[Index].ContainsNaN()) { Output.Pose[Index] = Output.Pose.GetRefPose(Index); ++GNaNBones; }
		}
		if (!bHaveBase || Base.GetNumBones() != Output.Pose.GetNumBones() || Mask.Num() != Output.Pose.GetNumBones()) return;
		for (FCompactPoseBoneIndex Index : Output.Pose.ForEachBoneIndex())
		{
			const float M = Mask[Index.GetInt()];
			const float W = M + (1.f - M) * LegWeight;
			if (W >= 1.f) continue;
			Output.Pose[Index] = W > 0.f ? SafeBlend(Base[Index], Output.Pose[Index], W) : Base[Index];
		}
	}

protected:
	virtual void PostEvaluateSourcePose(FPoseContext& SourceContext) override
	{
		if (WeightData.SlotNodeWeight <= ZERO_ANIMWEIGHT_THRESH) return;
		// At full montage weight the engine skips evaluating the source, but the legs still need it.
		if (WeightData.SourceWeight <= ZERO_ANIMWEIGHT_THRESH) Source.Evaluate(SourceContext);
		Base.CopyBonesFrom(SourceContext.Pose);
		bHaveBase = true;
	}

public:
	float LegWeight = 0.f;

private:
	TArray<float> Mask;
	FCompactHeapPose Base;
	bool bHaveBase = false;
};

/** Fades from a captured pose to the live pose: covers switches between base assets the slot crossfade can't. */
struct FSeleneSnapshotBlend : public FAnimNode_Base
{
	FPoseLink Source;
	FPoseSnapshot Snapshot;
	float Duration = 0.f;
	float Elapsed = 0.f;

	virtual void Initialize_AnyThread(const FAnimationInitializeContext& Context) override { Source.Initialize(Context); }
	virtual void CacheBones_AnyThread(const FAnimationCacheBonesContext& Context) override { Source.CacheBones(Context); }
	virtual void Update_AnyThread(const FAnimationUpdateContext& Context) override
	{
		Source.Update(Context);
		Elapsed += Context.GetDeltaTime();
	}
	virtual void Evaluate_AnyThread(FPoseContext& Output) override
	{
		Source.Evaluate(Output);
		if (!Snapshot.bIsValid || Duration <= 0.f || Elapsed >= Duration) return;
		const float T = FMath::Clamp(Elapsed / Duration, 0.f, 1.f);
		const float Alpha = 1.f - T * T * (3.f - 2.f * T);   // smoothstep out
		const FBoneContainer& Bones = Output.Pose.GetBoneContainer();
		for (FCompactPoseBoneIndex Index : Output.Pose.ForEachBoneIndex())
		{
			const int32 MeshIndex = Bones.MakeMeshPoseIndex(Index).GetInt();
			if (!Snapshot.LocalTransforms.IsValidIndex(MeshIndex)) continue;
			Output.Pose[Index] = SafeBlend(Output.Pose[Index], Snapshot.LocalTransforms[MeshIndex], Alpha);
		}
	}
	virtual void GatherDebugData(FNodeDebugData& DebugData) override { Source.GatherDebugData(DebugData); }
};

struct FSeleneSecondaryProxy : public FAnimSingleNodeInstanceProxy
{
	explicit FSeleneSecondaryProxy(UAnimInstance* InAnimInstance)
		: FAnimSingleNodeInstanceProxy(InAnimInstance)
	{
	}

	virtual void Initialize(UAnimInstance* InAnimInstance) override
	{
		// The base Initialize asks GetCustomRootNode() for the graph, so build it first (once per instance).
		if (!bBuilt)
		{
			BuildGraph(InAnimInstance);
			bBuilt = true;
		}
		FAnimSingleNodeInstanceProxy::Initialize(InAnimInstance);
	}

	virtual FAnimNode_Base* GetCustomRootNode() override
	{
		return Chains.IsEmpty() ? static_cast<FAnimNode_Base*>(&Crossfade) : &ToLocal;
	}

	virtual void GetCustomNodes(TArray<FAnimNode_Base*>& OutNodes) override
	{
		if (!Chains.IsEmpty())
		{
			OutNodes.Add(&ToLocal);
			OutNodes.Add(&ToComponent);
			for (const TUniquePtr<FAnimNode_KawaiiPhysics>& Node : Chains) OutNodes.Add(Node.Get());
		}
		OutNodes.Add(&Crossfade);
		OutNodes.Add(&UpperSlot);
		OutNodes.Add(&DefaultSlot);
		OutNodes.Add(&SingleNode);
	}

	virtual void PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds) override
	{
		FAnimSingleNodeInstanceProxy::PreUpdate(InAnimInstance, DeltaSeconds);
		// Game thread: hand the leg weight and any requested crossfade to the nodes before the worker update.
		if (USeleneSecondaryAnimInstance* Instance = Cast<USeleneSecondaryAnimInstance>(InAnimInstance)) UpperSlot.LegWeight = Instance->LegWeight;
		if (USeleneSecondaryAnimInstance* Instance = Cast<USeleneSecondaryAnimInstance>(InAnimInstance); Instance && Instance->PendingCrossfade > 0.f)
		{
			Crossfade.Snapshot = Instance->PendingSnapshot;
			Crossfade.Duration = Instance->PendingCrossfade;
			Crossfade.Elapsed = 0.f;
			Instance->PendingCrossfade = 0.f;
		}
	}

	virtual bool Evaluate(FPoseContext& Output) override
	{
		// false -> the engine evaluates our root node graph (which pulls SingleNode through the links).
		return false;
	}

	virtual void UpdateAnimationNode(const FAnimationUpdateContext& InContext) override
	{
		// Traverse the slot even without chains; the single-node shortcut would bypass its weights.
		FAnimInstanceProxy::UpdateAnimationNode(InContext);
	}

	/** Game-thread debug read: largest |simulated - animated| bone offset per chain (racy, debug only). */
	void GatherSwing(TMap<FName, float>& InOutMax) const
	{
		for (const TUniquePtr<FAnimNode_KawaiiPhysics>& Node : Chains)
		{
			float Max = 0.f;
			for (const FKawaiiPhysicsModifyBone& Bone : Node->ModifyBones)
			{
				if (!Bone.bDummy) Max = FMath::Max(Max, FVector::Dist(Bone.Location, Bone.PoseLocation));
			}
			float& Slot = InOutMax.FindOrAdd(Node->RootBone.BoneName);
			Slot = FMath::Max(Slot, Max);
		}
	}

private:
	void BuildGraph(UAnimInstance* InAnimInstance)
	{
		DefaultSlot.SlotName = FAnimSlotGroup::DefaultSlotName;
		DefaultSlot.bAlwaysUpdateSourcePose = true;
		DefaultSlot.Source.SetLinkNode(&SingleNode);
		UpperSlot.SlotName = USeleneSecondaryAnimInstance::UpperBodySlot;
		UpperSlot.bAlwaysUpdateSourcePose = true;
		UpperSlot.Source.SetLinkNode(&DefaultSlot);
		Crossfade.Source.SetLinkNode(&UpperSlot);

		const ASeleneCharacter* Character = Cast<ASeleneCharacter>(InAnimInstance->GetOwningActor());
		const USkeletalMeshComponent* Component = InAnimInstance->GetSkelMeshComponent();
		const USkeletalMesh* Mesh = Component ? Component->GetSkeletalMeshAsset() : nullptr;
		if (!Character || !Mesh) return;
		const FSelenePlayableCharacter& Entry = Character->GetActiveCharacterEntry();
		const FReferenceSkeleton& Ref = Mesh->GetRefSkeleton();

		TArray<FSphericalLimit> Spheres;
		TArray<FCapsuleLimit> Capsules;
		for (const FSeleneSecondaryCollider& Collider : Entry.SecondaryColliders)
		{
			const int32 Bone = Ref.FindBoneIndex(Collider.Bone);
			if (Bone == INDEX_NONE)
			{
				UE_LOG(LogSelene, Warning, TEXT("%s: secondary collider bone '%s' not found"), *Entry.Name.ToString(), *Collider.Bone.ToString());
				continue;
			}
			const int32 Child = Collider.ChildBone.IsNone() ? INDEX_NONE : Ref.FindBoneIndex(Collider.ChildBone);
			if (Child == INDEX_NONE)
			{
				FSphericalLimit Sphere;
				Sphere.DrivingBone.BoneName = Collider.Bone;
				Sphere.Radius = Collider.Radius;
				Spheres.Add(Sphere);
				continue;
			}
			// Capsule along the bone toward its child, expressed in the driving bone's local frame.
			const FVector Local = RefComponentSpace(Ref, Bone).InverseTransformPosition(RefComponentSpace(Ref, Child).GetLocation());
			FCapsuleLimit Capsule;
			Capsule.DrivingBone.BoneName = Collider.Bone;
			Capsule.Radius = Collider.Radius;
			Capsule.Length = Local.Size();
			Capsule.OffsetLocation = Local * 0.5;
			Capsule.OffsetRotation = FRotationMatrix::MakeFromZ(Local.GetSafeNormal()).Rotator();
			Capsules.Add(Capsule);
		}

		for (const FSeleneSecondaryChain& Setup : Entry.SecondaryChains)
		{
			const int32 Root = Ref.FindBoneIndex(Setup.RootBone);
			if (Root == INDEX_NONE)
			{
				UE_LOG(LogSelene, Warning, TEXT("%s: secondary chain root '%s' not found"), *Entry.Name.ToString(), *Setup.RootBone.ToString());
				continue;
			}
			TUniquePtr<FAnimNode_KawaiiPhysics> Node = MakeUnique<FAnimNode_KawaiiPhysics>();
			Node->RootBone.BoneName = Setup.RootBone;
			Node->PhysicsSettings.Damping = Setup.Damping;
			Node->PhysicsSettings.Stiffness = Setup.Stiffness;
			Node->PhysicsSettings.WorldDampingLocation = Setup.WorldDampingLocation;
			Node->PhysicsSettings.WorldDampingRotation = Setup.WorldDampingRotation;
			Node->PhysicsSettings.Radius = Setup.Radius;
			Node->PhysicsSettings.LimitAngle = Setup.LimitAngle;
			Node->Gravity = FVector(0.f, 0.f, Setup.GravityZ);
			// A dummy tip bone lets the last real bone rotate too; size it from the chain's first segment.
			if (const int32 Next = FirstChild(Ref, Root); Next != INDEX_NONE)
			{
				const FVector Segment = Ref.GetRefBonePose()[Next].GetTranslation();
				Node->BoneForwardAxis = DominantAxis(Segment);
				Node->DummyBoneLength = Segment.Size();
			}
			Node->SphericalLimits = Spheres;
			Node->CapsuleLimits = Capsules;
			Chains.Add(MoveTemp(Node));
		}
		if (Chains.IsEmpty()) return;

		// SingleNode -> DefaultSlot -> UpperBody -> LocalToComponent -> Kawaii[] -> ComponentToLocal (root)
		ToComponent.LocalPose.SetLinkNode(&Crossfade);
		Chains[0]->ComponentPose.SetLinkNode(&ToComponent);
		for (int32 i = 1; i < Chains.Num(); ++i) Chains[i]->ComponentPose.SetLinkNode(Chains[i - 1].Get());
		ToLocal.ComponentPose.SetLinkNode(Chains.Last().Get());
		UE_LOG(LogSelene, Log, TEXT("%s: Kawaii secondary motion on %d chains, %d sphere + %d capsule colliders"),
			*Entry.Name.ToString(), Chains.Num(), Spheres.Num(), Capsules.Num());
	}

	FAnimNode_Slot DefaultSlot;
	FSeleneUpperBodySlot UpperSlot;
	FSeleneSnapshotBlend Crossfade;
	FAnimNode_ConvertComponentToLocalSpace ToLocal;
	FAnimNode_ConvertLocalToComponentSpace ToComponent;
	TArray<TUniquePtr<FAnimNode_KawaiiPhysics>> Chains;
	bool bBuilt = false;
};

FAnimInstanceProxy* USeleneSecondaryAnimInstance::CreateAnimInstanceProxy()
{
	return new FSeleneSecondaryProxy(this);
}

FVector USeleneSecondaryAnimInstance::ProbeSingleNodeComponent(USkeletalMeshComponent* Component, float DeltaSeconds)
{
#if WITH_EDITOR
	if (Component)
	{
		if (DeltaSeconds >= 0.f)
		{
			Component->TickAnimation(DeltaSeconds, false);
			Component->RefreshBoneTransforms();
		}
		if (const UAnimSingleNodeInstance* Instance = Component->GetSingleNodeInstance())
		{
			return FVector(Instance->GetCurrentTime(), Instance->GetPlayRate(), Instance->IsPlaying() ? 1.f : 0.f);
		}
	}
#endif
	return FVector::ZeroVector;
}

void USeleneSecondaryAnimInstance::StartCrossfade(float Seconds)
{
	USkeletalMeshComponent* Component = GetSkelMeshComponent();
	if (!Component || Seconds <= 0.f) return;
	Component->SnapshotPose(PendingSnapshot);
	if (PendingSnapshot.bIsValid) PendingCrossfade = Seconds;
}

void USeleneSecondaryAnimInstance::SetAnimationAsset(UAnimationAsset* NewAsset, bool bIsLooping, float InPlayRate)
{
	if (Cast<UAnimMontage>(NewAsset))
	{
		Super::SetAnimationAsset(NewAsset, bIsLooping, InPlayRate);
		return;
	}
	CurrentAsset = NewAsset;
	USkeletalMeshComponent* MeshComponent = GetSkelMeshComponent();
	if (MeshComponent && (!MeshComponent->GetSkeletalMeshAsset() || (CurrentAsset && !CurrentAsset->GetSkeleton()))) CurrentAsset = nullptr;
	// The engine stops all montages here; slot overlays are owned by ASeleneCharacter and stopped explicitly.
	GetProxyOnGameThread<FAnimSingleNodeInstanceProxy>().SetAnimationAsset(CurrentAsset, MeshComponent, bIsLooping, InPlayRate);
}

void USeleneSecondaryAnimInstance::Montage_Advance(float DeltaTime)
{
	if (Cast<UAnimMontage>(GetAnimationAsset()))
	{
		Super::Montage_Advance(DeltaTime);
	}
	else
	{
		// Single-node's montage-preview override copies montage time into the base player.
		// Slot overlays must leave the sequence/blend-space clock running independently.
		UAnimInstance::Montage_Advance(DeltaTime);
	}
}

void USeleneSecondaryAnimInstance::NativeUpdateAnimation(float DeltaSeconds)
{
	Super::NativeUpdateAnimation(DeltaSeconds);
	if (CVarSecondaryDebug.GetValueOnGameThread() <= 0) return;
	GetProxyOnGameThread<FSeleneSecondaryProxy>().GatherSwing(DebugMaxSwing);
	DebugTimer += DeltaSeconds;
	if (DebugTimer < 0.5f) return;
	const APawn* Pawn = Cast<APawn>(GetOwningActor());
	FString Line = FString::Printf(TEXT("speed=%.0f"), Pawn ? Pawn->GetVelocity().Size2D() : 0.f);
	for (const TPair<FName, float>& Pair : DebugMaxSwing) Line += FString::Printf(TEXT(" %s=%.1f"), *Pair.Key.ToString(), Pair.Value);
	UE_LOG(LogSelene, Log, TEXT("Secondary swing cm: %s"), *Line);
	DebugTimer = 0.f;
	DebugMaxSwing.Reset();
}
