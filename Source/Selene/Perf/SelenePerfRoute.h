#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SelenePerfRoute.generated.h"

class USplineComponent;

USTRUCT(BlueprintType)
struct SELENE_API FSelenePerfSegment
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Performance")
	FName Tag;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Performance")
	float StartDistance = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Performance")
	float EndDistance = 0;
};

UCLASS(BlueprintType)
class SELENE_API ASelenePerfRoute : public AActor
{
	GENERATED_BODY()
public:
	ASelenePerfRoute();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Performance")
	TObjectPtr<USplineComponent> Route;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Performance")
	FName RouteName;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Performance")
	TArray<FSelenePerfSegment> Segments;
};
