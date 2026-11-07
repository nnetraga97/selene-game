#pragma once

#include "CoreMinimal.h"
#include "Styling/SlateBrush.h"
#include "Widgets/SLeafWidget.h"

class ASelenePlayerController;
class UTextureRenderTarget2D;

/** Full-screen top-down map: an orthographic capture centred where it was taken, plus a live player arrow. */
class SSeleneMapView : public SLeafWidget
{
public:
	SLATE_BEGIN_ARGS(SSeleneMapView) {}
		SLATE_ARGUMENT(TWeakObjectPtr<ASelenePlayerController>, Controller)
		SLATE_ARGUMENT(UTextureRenderTarget2D*, Target)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
	virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(256.f, 256.f); }

private:
	TWeakObjectPtr<ASelenePlayerController> Controller;
	FSlateBrush MapBrush;
};
