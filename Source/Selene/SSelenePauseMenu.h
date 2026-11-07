#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Styling/SlateTypes.h"

class ASelenePlayerController;
class SVerticalBox;
class SScrollBox;

/** Asset-free modal menu. Root retains focus; mouse and keyboard share a selected row. */
class SSelenePauseMenu : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SSelenePauseMenu) {}
		SLATE_ARGUMENT(TWeakObjectPtr<ASelenePlayerController>, Controller)
	SLATE_END_ARGS()

	void Construct(const FArguments& Args);
	virtual bool SupportsKeyboardFocus() const override { return true; }
	// Background clicks must not bubble to the viewport and steal menu focus.
	virtual FReply OnMouseButtonDown(const FGeometry&, const FPointerEvent&) override
	{
		return FReply::Handled().SetUserFocus(AsShared(), EFocusCause::Mouse);
	}
	virtual FReply OnMouseButtonDoubleClick(const FGeometry& Geometry, const FPointerEvent& Event) override
	{
		return OnMouseButtonDown(Geometry, Event);
	}
	virtual FReply OnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event) override;

private:
	void AddButton(const TSharedRef<SVerticalBox>& Rows, TAttribute<FText> Label,
		TFunction<void()> Action, TAttribute<bool> Active = false);
	void AddHeading(const TSharedRef<SVerticalBox>& Rows, const TCHAR* Text);
	float GetDPIScale() const;
	TWeakObjectPtr<ASelenePlayerController> Controller;
	TArray<TFunction<void()>> Actions;
	TArray<TSharedPtr<SWidget>> Buttons;
	TSharedPtr<SScrollBox> Scroll;
	FButtonStyle ButtonStyle;
	int32 Selected = 0;
};
