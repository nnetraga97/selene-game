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
	FName Category;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Performance")
	float StartDistance = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Performance")
	float EndDistance = 0;
};

// Keys are sorted by distance. Missing keys use the smoothed look-ahead path.
USTRUCT(BlueprintType)
struct SELENE_API FSelenePerfViewKey
{
	GENERATED_BODY()
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Performance")
	float Distance = 0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Performance")
	FVector LookAtTarget = FVector::ZeroVector;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Performance")
	bool bUseLookAt = false;
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
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Performance")
	TArray<FSelenePerfViewKey> ViewKeys;

	// World-space feet path; the runner adds the possessed capsule half-height.
	UFUNCTION(BlueprintPure, Category="Performance")
	FRotator ViewRotationAt(float Distance, const FVector& Eye) const;

private:
	FRotator PathViewRotationAt(float Distance) const;
};
