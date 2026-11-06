#include "Perf/SelenePerfRoute.h"
#include "Components/SplineComponent.h"

ASelenePerfRoute::ASelenePerfRoute()
{
	PrimaryActorTick.bCanEverTick = false;
	Route = CreateDefaultSubobject<USplineComponent>(TEXT("Route"));
	SetRootComponent(Route);
}
