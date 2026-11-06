#include "Animation/SeleneSecondaryAnimInstance.h"

#include "Selene.h"
#include "SeleneCharacter.h"
#include "SeleneCharacterSettings.h"
#include "AnimNode_KawaiiPhysics.h"
#include "Animation/AnimNodeSpaceConversions.h"
#include "Animation/AnimSingleNodeInstanceProxy.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "ReferenceSkeleton.h"

namespace
{
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
		return Chains.IsEmpty() ? nullptr : &ToLocal;
	}

	virtual void GetCustomNodes(TArray<FAnimNode_Base*>& OutNodes) override
	{
		if (Chains.IsEmpty()) return;
		OutNodes.Add(&ToLocal);
		OutNodes.Add(&ToComponent);
		for (const TUniquePtr<FAnimNode_KawaiiPhysics>& Node : Chains) OutNodes.Add(Node.Get());
		OutNodes.Add(&SingleNode);
	}

	virtual bool Evaluate(FPoseContext& Output) override
	{
		// false -> the engine evaluates our root node graph (which pulls SingleNode through the links).
		return Chains.IsEmpty() ? FAnimSingleNodeInstanceProxy::Evaluate(Output) : false;
	}

	virtual void UpdateAnimationNode(const FAnimationUpdateContext& InContext) override
	{
		if (Chains.IsEmpty())
		{
			FAnimSingleNodeInstanceProxy::UpdateAnimationNode(InContext);
		}
		else
		{
			// Updates the graph from the root (increments UpdateCounter like the single-node path does).
			FAnimInstanceProxy::UpdateAnimationNode(InContext);
		}
	}

private:
	void BuildGraph(UAnimInstance* InAnimInstance)
	{
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

		// SingleNode -> LocalToComponent -> Kawaii[0] -> ... -> Kawaii[n-1] -> ComponentToLocal (root)
		ToComponent.LocalPose.SetLinkNode(&SingleNode);
		Chains[0]->ComponentPose.SetLinkNode(&ToComponent);
		for (int32 i = 1; i < Chains.Num(); ++i) Chains[i]->ComponentPose.SetLinkNode(Chains[i - 1].Get());
		ToLocal.ComponentPose.SetLinkNode(Chains.Last().Get());
		UE_LOG(LogSelene, Log, TEXT("%s: Kawaii secondary motion on %d chains, %d sphere + %d capsule colliders"),
			*Entry.Name.ToString(), Chains.Num(), Spheres.Num(), Capsules.Num());
	}

	FAnimNode_ConvertComponentToLocalSpace ToLocal;
	FAnimNode_ConvertLocalToComponentSpace ToComponent;
	TArray<TUniquePtr<FAnimNode_KawaiiPhysics>> Chains;
	bool bBuilt = false;
};

FAnimInstanceProxy* USeleneSecondaryAnimInstance::CreateAnimInstanceProxy()
{
	return new FSeleneSecondaryProxy(this);
}
