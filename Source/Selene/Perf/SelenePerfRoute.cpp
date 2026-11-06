#include "Perf/SelenePerfRoute.h"
#include "Components/SplineComponent.h"

ASelenePerfRoute::ASelenePerfRoute()
{
	PrimaryActorTick.bCanEverTick = false;
	Route = CreateDefaultSubobject<USplineComponent>(TEXT("Route"));
	SetRootComponent(Route);
}

FRotator ASelenePerfRoute::ViewRotationAt(float Distance, const FVector& Eye) const
{
	const FRotator Tangent = Route->GetDirectionAtDistanceAlongSpline(Distance, ESplineCoordinateSpace::World).Rotation();
	if (ViewKeys.IsEmpty()) return Tangent;
	int32 Upper = 0;
	while (Upper < ViewKeys.Num() - 1 && ViewKeys[Upper].Distance < Distance) ++Upper;
	const FSelenePerfViewKey& B = ViewKeys[Upper];
	const FSelenePerfViewKey& A = ViewKeys[FMath::Max(0, Upper - 1)];
	const float Alpha = B.Distance > A.Distance ? FMath::Clamp((Distance - A.Distance) / (B.Distance - A.Distance), 0.f, 1.f) : 1.f;
	if (A.bUseLookAt && B.bUseLookAt)
		return (FMath::Lerp(A.LookAtTarget, B.LookAtTarget, Alpha) - Eye).Rotation();
	const FRotator From = A.bUseLookAt ? (A.LookAtTarget - Eye).Rotation() : Tangent;
	const FRotator To = B.bUseLookAt ? (B.LookAtTarget - Eye).Rotation() : Tangent;
	return FQuat::Slerp(From.Quaternion(), To.Quaternion(), Alpha).Rotator();
}
