#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"

/** Top-right frame-rate readout, averaged over 0.25 s windows. Not drawn in HighResShot/AutoShots captures. */
class SSeleneFpsCounter : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SSeleneFpsCounter) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual void Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime) override;

private:
	FText Label;
	FSlateColor LabelColor;
	double WindowTime = 0.0;
	double WindowWorst = 0.0;
	int32 WindowFrames = 0;
};
