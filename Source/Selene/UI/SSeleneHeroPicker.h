#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"

class ASelenePlayerController;
class SVerticalBox;

/** Quick hero picker on C: numbered roster list, picks with 1-9/0, click, or arrows + Enter. Does not pause. */
class SSeleneHeroPicker : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SSeleneHeroPicker) {}
		SLATE_ARGUMENT(TWeakObjectPtr<ASelenePlayerController>, Controller)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual bool SupportsKeyboardFocus() const override { return true; }
	virtual FReply OnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;
	virtual FReply OnMouseButtonDown(const FGeometry&, const FPointerEvent&) override
	{
		return FReply::Handled().SetUserFocus(AsShared(), EFocusCause::Mouse);
	}

private:
	void Pick(int32 Index);
	TWeakObjectPtr<ASelenePlayerController> Controller;
	TArray<FName> Names;
	int32 Selected = 0;
};
