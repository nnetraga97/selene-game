#pragma once

#include "CoreMinimal.h"
#include "Widgets/SLeafWidget.h"

class APlayerController;

/**
 * Combat HUD, drawn as vectors each frame: crosshair and hit markers, health and dash charges, ability bar with
 * cooldowns, objective tracker, world-space health bars and damage numbers, damage direction, announcements,
 * respawn and end-of-match screens. Lane-only parts draw nothing on maps without lanes.
 */
class SSeleneHud : public SLeafWidget
{
public:
	SLATE_BEGIN_ARGS(SSeleneHud) {}
		SLATE_ARGUMENT(TWeakObjectPtr<APlayerController>, Controller)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
	virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(1920.f, 1080.f); }

private:
	TWeakObjectPtr<APlayerController> Controller;
	double StartTime = -1.0;
};
