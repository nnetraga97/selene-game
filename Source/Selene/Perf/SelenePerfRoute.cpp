#include "Perf/SelenePerfRoute.h"
#include "Components/SplineComponent.h"

ASelenePerfRoute::ASelenePerfRoute()
{
	PrimaryActorTick.bCanEverTick = false;
	Route = CreateDefaultSubobject<USplineComponent>(TEXT("Route"));
	SetRootComponent(Route);
}

FRotator ASelenePerfRoute::PathViewRotationAt(float Distance) const
{
	// A 2.5 m chord removes individual tread/kerb tangents. Low-pass it in
	// distance space (a 2 m triangular window) so laps and frame rates agree.
	const float Length = Route->GetSplineLength();
	const float Span = FMath::Min(250.f, Length);
	FVector Direction = FVector::ZeroVector;
	for (int32 Sample = -10; Sample <= 10; ++Sample)
	{
		const float Start = FMath::Clamp(Distance + Sample * 10.f, 0.f, Length - Span);
		const FVector From = Route->GetLocationAtDistanceAlongSpline(Start, ESplineCoordinateSpace::World);
		const FVector To = Route->GetLocationAtDistanceAlongSpline(Start + Span, ESplineCoordinateSpace::World);
		Direction += (To - From).GetSafeNormal() * (11 - FMath::Abs(Sample));
	}
	FRotator View = Direction.Rotation();
	View.Pitch = FMath::Clamp(View.Pitch, -25.f, 25.f);
	View.Roll = 0;
	return View;
}

FRotator ASelenePerfRoute::ViewRotationAt(float Distance, const FVector& Eye) const
{
	if (ViewKeys.IsEmpty()) return PathViewRotationAt(Distance);
	int32 Upper = 0;
	while (Upper < ViewKeys.Num() - 1 && ViewKeys[Upper].Distance < Distance) ++Upper;
	const FSelenePerfViewKey& B = ViewKeys[Upper];
	const FSelenePerfViewKey& A = ViewKeys[FMath::Max(0, Upper - 1)];
	const float Alpha = B.Distance > A.Distance ? FMath::Clamp((Distance - A.Distance) / (B.Distance - A.Distance), 0.f, 1.f) : 1.f;
	if (A.bUseLookAt && B.bUseLookAt)
		return (FMath::Lerp(A.LookAtTarget, B.LookAtTarget, Alpha) - Eye).Rotation();
	const FRotator PathView = PathViewRotationAt(Distance);
	const FRotator From = A.bUseLookAt ? (A.LookAtTarget - Eye).Rotation() : PathView;
	const FRotator To = B.bUseLookAt ? (B.LookAtTarget - Eye).Rotation() : PathView;
	return FQuat::Slerp(From.Quaternion(), To.Quaternion(), Alpha).Rotator();
}
