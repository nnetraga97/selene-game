#include "SSelenePauseMenu.h"

#include "SeleneCharacter.h"
#include "SelenePlayerController.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "Engine/UserInterfaceSettings.h"
#include "Framework/Application/SlateApplication.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Styling/CoreStyle.h"
#include "Brushes/SlateColorBrush.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SDPIScaler.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

namespace
{
	const FLinearColor Cream = FLinearColor::FromSRGBColor(FColor(243, 233, 216));
	const FLinearColor Petrol = FLinearColor::FromSRGBColor(FColor(31, 78, 95));
	const FLinearColor Coral = FLinearColor::FromSRGBColor(FColor(233, 114, 90));
}

void SSelenePauseMenu::Construct(const FArguments& Args)
{
	Controller = Args._Controller;
	ButtonStyle = FCoreStyle::Get().GetWidgetStyle<FButtonStyle>("Button");
	ButtonStyle.SetNormal(FSlateColorBrush(FLinearColor::White));
	ButtonStyle.SetHovered(FSlateColorBrush(FLinearColor::White));
	ButtonStyle.SetPressed(FSlateColorBrush(FLinearColor::White));

	TSharedRef<SVerticalBox> Rows = SNew(SVerticalBox);
	Rows->AddSlot().AutoHeight().HAlign(HAlign_Center)
	[
		SNew(STextBlock).Text(FText::FromString(TEXT("Selene")))
		.Font(FCoreStyle::GetDefaultFontStyle("Bold", 36)).ColorAndOpacity(Petrol)
	];
	Rows->AddSlot().AutoHeight().HAlign(HAlign_Center).Padding(0, 0, 0, 16)
	[
		SNew(STextBlock).Text(FText::FromString(TEXT("Paused")))
		.Font(FCoreStyle::GetDefaultFontStyle("Regular", 18)).ColorAndOpacity(Petrol)
	];
	AddButton(Rows, FText::FromString(TEXT("Resume")), [this]()
	{
		if (Controller.IsValid()) Controller->ClosePauseMenu();
	});
	AddHeading(Rows, TEXT("Character"));
	for (const FSelenePlayableCharacter& Entry : GetDefault<USeleneCharacterSettings>()->Roster)
	{
		const FName Name = Entry.Name;
		AddButton(Rows, FText::FromName(Name), [this, Name]()
		{
			if (ASelenePlayerController* PC = Controller.Get())
			{
				if (ASeleneCharacter* Character = Cast<ASeleneCharacter>(PC->GetPawn()))
					Character->SelectCharacter(Name);
				PC->ClosePauseMenu();
			}
		}, TAttribute<bool>::CreateLambda([this, Name]()
		{
			const ASeleneCharacter* Character = Controller.IsValid()
				? Cast<ASeleneCharacter>(Controller->GetPawn()) : nullptr;
			return Character && Character->GetActiveCharacterName() == Name;
		}));
	}
	AddHeading(Rows, TEXT("Camera"));
	for (const ESeleneCameraMode Mode : {ESeleneCameraMode::FirstPerson, ESeleneCameraMode::ThirdPerson})
	{
		AddButton(Rows, FText::FromString(Mode == ESeleneCameraMode::FirstPerson
			? TEXT("First person") : TEXT("Third person")), [this, Mode]()
		{
			if (Controller.IsValid())
				if (ASeleneCharacter* Character = Cast<ASeleneCharacter>(Controller->GetPawn()))
					Character->SetCameraMode(Mode);
		}, TAttribute<bool>::CreateLambda([this, Mode]()
		{
			const ASeleneCharacter* Character = Controller.IsValid()
				? Cast<ASeleneCharacter>(Controller->GetPawn()) : nullptr;
			return Character && Character->GetCameraMode() == Mode;
		}));
	}
	AddHeading(Rows, TEXT("Controls"));
	Rows->AddSlot().AutoHeight().Padding(0, 0, 0, 12)
	[
		SNew(STextBlock).Text(FText::FromString(TEXT(
			"WASD  Move     Mouse  Look\nShift  Dash, hold to sprint     Ctrl  Slide\nCapsLock  Walk toggle     Space  Jump\nV  Camera     C  Character\nM  Map     F  FPS counter     Esc  Menu")))
		.Font(FCoreStyle::GetDefaultFontStyle("Regular", 16)).ColorAndOpacity(Petrol)
	];
	AddButton(Rows, FText::FromString(TEXT("Quit to desktop")), [this]()
	{
		if (ASelenePlayerController* PC = Controller.Get())
			UKismetSystemLibrary::QuitGame(PC, PC, EQuitPreference::Quit, false);
	});

	ChildSlot
	[
		SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
		.BorderBackgroundColor(FLinearColor(0.f, 0.f, 0.f, 0.55f)).Padding(24)
		[
			SNew(SDPIScaler).DPIScale(this, &SSelenePauseMenu::GetDPIScale)
			[
				SNew(SBox).HAlign(HAlign_Center).VAlign(VAlign_Center)
				[
					SNew(SBox).WidthOverride(460).MaxDesiredHeight(850)
					[
						SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
						.BorderBackgroundColor(Cream).Padding(28)
						[
							SAssignNew(Scroll, SScrollBox)
							+ SScrollBox::Slot()[Rows]
						]
					]
				]
			]
		]
	];
}

void SSelenePauseMenu::AddHeading(const TSharedRef<SVerticalBox>& Rows, const TCHAR* Text)
{
	Rows->AddSlot().AutoHeight().Padding(0, 12, 0, 6)
	[
		SNew(STextBlock).Text(FText::FromString(Text))
		.Font(FCoreStyle::GetDefaultFontStyle("Bold", 18)).ColorAndOpacity(Petrol)
	];
}

void SSelenePauseMenu::AddButton(const TSharedRef<SVerticalBox>& Rows, TAttribute<FText> Label,
	TFunction<void()> Action, TAttribute<bool> Active)
{
	const int32 Index = Actions.Add(MoveTemp(Action));
	TSharedPtr<SButton> Button;
	Rows->AddSlot().AutoHeight().Padding(0, 3)
	[
		SAssignNew(Button, SButton).ButtonStyle(&ButtonStyle).IsFocusable(false)
		.ContentPadding(FMargin(14, 9)).HAlign(HAlign_Center)
		.ButtonColorAndOpacity_Lambda([this, Index, Active]()
		{
			return Selected == Index || Active.Get() ? Coral : Petrol;
		})
		.OnHovered_Lambda([this, Index]() { Selected = Index; })
		.OnClicked_Lambda([this, Index]()
		{
			// Keep the widget alive if an action removes it from the viewport.
			const TSharedRef<SSelenePauseMenu> KeepAlive = SharedThis(this);
			Actions[Index]();
			return FReply::Handled();
		})
		[
			SNew(STextBlock).Text_Lambda([Label, Active]()
			{
				return Active.Get() ? FText::Format(NSLOCTEXT("Selene", "ActiveMenuChoice", "{0} (active)"), Label.Get()) : Label.Get();
			}).Font(FCoreStyle::GetDefaultFontStyle("Bold", 18))
			.ColorAndOpacity_Lambda([this, Index, Active]()
			{
				return Selected == Index || Active.Get() ? Petrol : Cream;
			})
		]
	];
	Buttons.Add(Button);
}

float SSelenePauseMenu::GetDPIScale() const
{
	FVector2D Size(1920, 1080);
	if (Controller.IsValid() && Controller->GetLocalPlayer() && Controller->GetWorld()->GetGameViewport())
		Controller->GetWorld()->GetGameViewport()->GetViewportSize(Size);
	return GetDefault<UUserInterfaceSettings>()->GetDPIScaleBasedOnSize(FIntPoint(FMath::RoundToInt(Size.X), FMath::RoundToInt(Size.Y)));
}

FReply SSelenePauseMenu::OnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
	const FKey Key = Event.GetKey();
	// Leave editor stop shortcuts alone; do not install a global input preprocessor.
	if (Key == EKeys::Escape && Event.IsShiftDown()) return FReply::Unhandled();
	if (Key == EKeys::Escape || Key == EKeys::Gamepad_Special_Right || Key == EKeys::Gamepad_FaceButton_Right)
	{
		if (!Event.IsRepeat() && Controller.IsValid()) Controller->ClosePauseMenu();
		return FReply::Handled();
	}
	const bool bUp = Key == EKeys::Up || Key == EKeys::Gamepad_DPad_Up || Key == EKeys::Gamepad_LeftStick_Up;
	const bool bDown = Key == EKeys::Down || Key == EKeys::Gamepad_DPad_Down || Key == EKeys::Gamepad_LeftStick_Down;
	if (bUp || bDown || Key == EKeys::Tab)
	{
		Selected = (Selected + ((bUp || (Key == EKeys::Tab && Event.IsShiftDown())) ? Actions.Num() - 1 : 1)) % Actions.Num();
		Scroll->ScrollDescendantIntoView(Buttons[Selected], false);
		return FReply::Handled();
	}
	if (Key == EKeys::Enter || Key == EKeys::SpaceBar || Key == EKeys::Gamepad_FaceButton_Bottom)
	{
		const TSharedRef<SSelenePauseMenu> KeepAlive = SharedThis(this);
		if (!Event.IsRepeat()) Actions[Selected]();
		return FReply::Handled();
	}
	return SCompoundWidget::OnKeyDown(Geometry, Event);
}
