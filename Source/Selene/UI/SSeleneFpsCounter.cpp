#include "UI/SSeleneFpsCounter.h"

#include "Misc/App.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

void SSeleneFpsCounter::Construct(const FArguments& InArgs)
{
	Label = FText::FromString(TEXT("-- fps"));
	LabelColor = FLinearColor::White;
	SetVisibility(EVisibility::HitTestInvisible);
	ChildSlot
	[
		SNew(SOverlay)
		+ SOverlay::Slot().HAlign(HAlign_Right).VAlign(VAlign_Top).Padding(0.f, 14.f, 16.f, 0.f)
		[
			SNew(SBorder)
			.BorderImage(FCoreStyle::Get().GetBrush("GenericWhiteBox"))
			.BorderBackgroundColor(FLinearColor(0.f, 0.f, 0.f, 0.45f))
			.Padding(FMargin(10.f, 4.f))
			[
				SNew(STextBlock)
				.Text_Lambda([this]() { return Label; })
				.ColorAndOpacity_Lambda([this]() { return LabelColor; })
				.Font(FCoreStyle::GetDefaultFontStyle("Bold", 15))
				.ShadowOffset(FVector2D(1.f, 1.f))
			]
		]
	];
}

void SSeleneFpsCounter::Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime)
{
	SCompoundWidget::Tick(AllottedGeometry, InCurrentTime, InDeltaTime);
	// Real (undilated) frame time, so pause and slomo don't distort the readout.
	const double Delta = FApp::GetDeltaTime();
	if (Delta <= 0.0) return;
	WindowTime += Delta;
	WindowWorst = FMath::Max(WindowWorst, Delta);
	++WindowFrames;
	if (WindowTime < 0.25) return;

	const double Fps = WindowFrames / WindowTime;
	const double Ms = 1000.0 * WindowTime / WindowFrames;
	Label = FText::FromString(FString::Printf(TEXT("%.0f fps   %.1f ms   worst %.1f ms"), Fps, Ms, WindowWorst * 1000.0));
	LabelColor = Fps >= 58.0 ? FLinearColor(0.55f, 1.f, 0.6f) : (Fps >= 30.0 ? FLinearColor(1.f, 0.82f, 0.35f) : FLinearColor(1.f, 0.4f, 0.35f));
	WindowTime = 0.0;
	WindowWorst = 0.0;
	WindowFrames = 0;
}
