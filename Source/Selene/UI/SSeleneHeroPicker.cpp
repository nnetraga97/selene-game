#include "UI/SSeleneHeroPicker.h"

#include "SelenePlayerController.h"
#include "SeleneCharacter.h"
#include "SeleneCharacterSettings.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

namespace
{
	const FLinearColor Cream(0.98f, 0.94f, 0.85f), Petrol(0.05f, 0.27f, 0.33f), Coral(0.96f, 0.42f, 0.33f);

	FString KeyLabel(int32 Index)
	{
		return Index < 9 ? FString::FromInt(Index + 1) : (Index == 9 ? TEXT("0") : TEXT(" "));
	}
}

void SSeleneHeroPicker::Construct(const FArguments& InArgs)
{
	Controller = InArgs._Controller;
	for (const FSelenePlayableCharacter& Entry : GetDefault<USeleneCharacterSettings>()->Roster)
	{
		if (!Entry.Name.IsNone()) Names.Add(Entry.Name);
	}
	const ASeleneCharacter* Character = Controller.IsValid() ? Cast<ASeleneCharacter>(Controller->GetPawn()) : nullptr;
	Selected = Character ? FMath::Max(0, Names.IndexOfByKey(Character->GetActiveCharacterName())) : 0;

	TSharedRef<SVerticalBox> Rows = SNew(SVerticalBox);
	Rows->AddSlot().AutoHeight().Padding(0, 0, 0, 10)
	[
		SNew(STextBlock).Text(FText::FromString(TEXT("Choose hero")))
		.Font(FCoreStyle::GetDefaultFontStyle("Bold", 20)).ColorAndOpacity(Petrol)
	];
	for (int32 Index = 0; Index < Names.Num(); ++Index)
	{
		const FName Name = Names[Index];
		Rows->AddSlot().AutoHeight().Padding(0, 2)
		[
			SNew(SButton)
			.ButtonStyle(&FCoreStyle::Get().GetWidgetStyle<FButtonStyle>("NoBorder"))
			.OnClicked_Lambda([this, Index]() { Pick(Index); return FReply::Handled(); })
			.OnHovered_Lambda([this, Index]() { Selected = Index; })
			[
				SNew(SBorder)
				.BorderImage(FCoreStyle::Get().GetBrush("GenericWhiteBox"))
				.BorderBackgroundColor_Lambda([this, Index]()
				{
					return Index == Selected ? FSlateColor(Petrol) : FSlateColor(FLinearColor(0.f, 0.f, 0.f, 0.f));
				})
				.Padding(FMargin(12.f, 6.f))
				[
					SNew(STextBlock)
					.Text_Lambda([this, Index, Name]()
					{
						const ASeleneCharacter* Active = Controller.IsValid() ? Cast<ASeleneCharacter>(Controller->GetPawn()) : nullptr;
						const bool bActive = Active && Active->GetActiveCharacterName() == Name;
						return FText::FromString(FString::Printf(TEXT("%s   %s%s"), *KeyLabel(Index), *Name.ToString(),
							bActive ? TEXT("   (active)") : TEXT("")));
					})
					.Font(FCoreStyle::GetDefaultFontStyle("Regular", 17))
					.ColorAndOpacity_Lambda([this, Index]() { return Index == Selected ? FSlateColor(Cream) : FSlateColor(Petrol); })
				]
			]
		];
	}
	Rows->AddSlot().AutoHeight().Padding(0, 10, 0, 0)
	[
		SNew(STextBlock).Text(FText::FromString(TEXT("Number or click to pick     C / Esc  close")))
		.Font(FCoreStyle::GetDefaultFontStyle("Regular", 13)).ColorAndOpacity(Coral)
	];

	ChildSlot
	[
		SNew(SOverlay)
		+ SOverlay::Slot().HAlign(HAlign_Left).VAlign(VAlign_Center).Padding(40.f, 0.f, 0.f, 0.f)
		[
			SNew(SBorder)
			.BorderImage(FCoreStyle::Get().GetBrush("GenericWhiteBox"))
			.BorderBackgroundColor(FLinearColor(Cream.R, Cream.G, Cream.B, 0.94f))
			.Padding(FMargin(20.f, 16.f))
			[
				SNew(SBox).MinDesiredWidth(280.f)[Rows]
			]
		]
	];
}

void SSeleneHeroPicker::Pick(int32 Index)
{
	ASelenePlayerController* PC = Controller.Get();
	if (!PC || !Names.IsValidIndex(Index)) return;
	if (ASeleneCharacter* Character = Cast<ASeleneCharacter>(PC->GetPawn()))
	{
		Character->SelectCharacter(Names[Index]);
	}
	PC->CloseHeroPicker();
}

FReply SSeleneHeroPicker::OnKeyDown(const FGeometry& Geometry, const FKeyEvent& Event)
{
	const FKey Key = Event.GetKey();
	static const FKey Digits[] = { EKeys::One, EKeys::Two, EKeys::Three, EKeys::Four, EKeys::Five,
		EKeys::Six, EKeys::Seven, EKeys::Eight, EKeys::Nine, EKeys::Zero };
	static const FKey NumPad[] = { EKeys::NumPadOne, EKeys::NumPadTwo, EKeys::NumPadThree, EKeys::NumPadFour,
		EKeys::NumPadFive, EKeys::NumPadSix, EKeys::NumPadSeven, EKeys::NumPadEight, EKeys::NumPadNine, EKeys::NumPadZero };
	for (int32 Index = 0; Index < UE_ARRAY_COUNT(Digits); ++Index)
	{
		if (Key == Digits[Index] || Key == NumPad[Index])
		{
			Pick(Index);
			return FReply::Handled();
		}
	}
	if (Key == EKeys::C || Key == EKeys::Escape || Key == EKeys::Gamepad_FaceButton_Right)
	{
		if (ASelenePlayerController* PC = Controller.Get()) PC->CloseHeroPicker();
		return FReply::Handled();
	}
	if (Key == EKeys::Up || Key == EKeys::W || Key == EKeys::Gamepad_DPad_Up)
	{
		Selected = (Selected + Names.Num() - 1) % FMath::Max(1, Names.Num());
		return FReply::Handled();
	}
	if (Key == EKeys::Down || Key == EKeys::S || Key == EKeys::Gamepad_DPad_Down || Key == EKeys::Tab)
	{
		Selected = (Selected + 1) % FMath::Max(1, Names.Num());
		return FReply::Handled();
	}
	if (Key == EKeys::Enter || Key == EKeys::SpaceBar || Key == EKeys::Gamepad_FaceButton_Bottom)
	{
		Pick(Selected);
		return FReply::Handled();
	}
	return FReply::Unhandled();
}
