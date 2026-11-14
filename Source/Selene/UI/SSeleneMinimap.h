#pragma once

#include "CoreMinimal.h"
#include "Widgets/SLeafWidget.h"

class APlayerController;
class ASeleneLaneDirector;

/** Bottom-right live minimap for lane maps: building outlines, lanes, every living unit and the player arrow.
 *  Drawn as vectors each frame (no scene capture). Draws nothing on maps without lanes. */
class SSeleneMinimap : public SLeafWidget
{
public:
	SLATE_BEGIN_ARGS(SSeleneMinimap) {}
		SLATE_ARGUMENT(TWeakObjectPtr<APlayerController>, Controller)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
	virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(320.f, 230.f); }

private:
	void CacheWorld() const;

	TWeakObjectPtr<APlayerController> Controller;
	mutable TWeakObjectPtr<ASeleneLaneDirector> Director;
	mutable TArray<TArray<FVector2f>> Footprints;   // world cm, closed quads
	mutable FBox2f Bounds = FBox2f(ForceInit);
	mutable bool bCached = false;
};
