#include "UI/SSeleneMapView.h"

#include "SelenePlayerController.h"
#include "Engine/TextureRenderTarget2D.h"
#include "GameFramework/Pawn.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"

void SSeleneMapView::Construct(const FArguments& InArgs)
{
	Controller = InArgs._Controller;
	MapBrush.DrawAs = ESlateBrushDrawType::Image;
	MapBrush.SetResourceObject(InArgs._Target);
	MapBrush.ImageSize = FVector2D(1024.f, 1024.f);
	SetVisibility(EVisibility::HitTestInvisible);
}

int32 SSeleneMapView::OnPaint(const FPaintArgs& Args, const FGeometry& Geometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& Out, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	const ASelenePlayerController* PC = Controller.Get();
	const FSlateBrush* White = FCoreStyle::Get().GetBrush("GenericWhiteBox");
	const FVector2f Size = FVector2f(Geometry.GetLocalSize());
	const FLinearColor Coral(0.96f, 0.42f, 0.33f), Cream(0.98f, 0.94f, 0.85f), Petrol(0.05f, 0.27f, 0.33f);

	// Dim the game behind the map.
	FSlateDrawElement::MakeBox(Out, LayerId, Geometry.ToPaintGeometry(), White, ESlateDrawEffect::None, FLinearColor(0.01f, 0.03f, 0.05f, 0.72f));

	const float Side = FMath::Min(Size.X, Size.Y) * 0.84f;
	const FVector2f Origin((Size.X - Side) * 0.5f, (Size.Y - Side) * 0.5f - Size.Y * 0.02f);
	const FPaintGeometry MapGeometry = Geometry.ToPaintGeometry(FVector2f(Side, Side), FSlateLayoutTransform(Origin));
	FSlateDrawElement::MakeBox(Out, LayerId + 1, Geometry.ToPaintGeometry(FVector2f(Side + 8.f, Side + 8.f), FSlateLayoutTransform(Origin - FVector2f(4.f, 4.f))), White, ESlateDrawEffect::None, Cream);
	FSlateDrawElement::MakeBox(Out, LayerId + 2, MapGeometry, &MapBrush, ESlateDrawEffect::None, FLinearColor::White);

	const FSlateFontInfo Title = FCoreStyle::GetDefaultFontStyle("Bold", 20);
	const FSlateFontInfo Small = FCoreStyle::GetDefaultFontStyle("Regular", 14);
	if (!PC)
	{
		return LayerId + 3;
	}
	const float WidthCm = PC->GetMapWidthCm();
	FSlateDrawElement::MakeText(Out, LayerId + 3, Geometry.ToPaintGeometry(FVector2f(Side, 30.f), FSlateLayoutTransform(Origin + FVector2f(0.f, -38.f))),
		FString(TEXT("MAP")), Title, ESlateDrawEffect::None, Cream);
	FSlateDrawElement::MakeText(Out, LayerId + 3, Geometry.ToPaintGeometry(FVector2f(Side, 24.f), FSlateLayoutTransform(Origin + FVector2f(0.f, Side + 12.f))),
		FString::Printf(TEXT("%.0f m across     M  close     Scroll or + / -  zoom (re-centres on you)"), WidthCm / 100.f), Small, ESlateDrawEffect::None, Cream);

	// 50 m scale bar, bottom-left inside the map.
	const float BarPx = Side * 5000.f / WidthCm;
	const FVector2f BarStart = Origin + FVector2f(16.f, Side - 22.f);
	TArray<FVector2f> Bar = { BarStart, BarStart + FVector2f(BarPx, 0.f) };
	FSlateDrawElement::MakeLines(Out, LayerId + 3, Geometry.ToPaintGeometry(), Bar, ESlateDrawEffect::None, Petrol, true, 4.f);
	FSlateDrawElement::MakeText(Out, LayerId + 3, Geometry.ToPaintGeometry(FVector2f(80.f, 20.f), FSlateLayoutTransform(BarStart + FVector2f(0.f, -22.f))),
		FString(TEXT("50 m")), Small, ESlateDrawEffect::None, Petrol);

	const APawn* Pawn = PC->GetPawn();
	if (!Pawn)
	{
		return LayerId + 3;
	}
	// The capture looks straight down with yaw 0: image up is world +X, image right is world +Y.
	const FVector Offset = Pawn->GetActorLocation() - PC->GetMapCenter();
	FVector2f Marker(0.5f + float(Offset.Y) / WidthCm, 0.5f - float(Offset.X) / WidthCm);
	const bool bInside = Marker.X >= 0.f && Marker.X <= 1.f && Marker.Y >= 0.f && Marker.Y <= 1.f;
	Marker = Origin + FVector2f(FMath::Clamp(Marker.X, 0.02f, 0.98f), FMath::Clamp(Marker.Y, 0.02f, 0.98f)) * Side;

	// Arrow points along the pawn's facing; Slate y is down, so world yaw is a clockwise angle from up.
	const float Yaw = FMath::DegreesToRadians(Pawn->GetActorRotation().Yaw);
	const float C = FMath::Cos(Yaw), S = FMath::Sin(Yaw);
	auto Rotate = [&](float X, float Y) { return Marker + FVector2f(X * C - Y * S, X * S + Y * C); };
	TArray<FVector2f> Arrow = { Rotate(0.f, -16.f), Rotate(-10.f, 11.f), Rotate(0.f, 5.f), Rotate(10.f, 11.f), Rotate(0.f, -16.f) };
	FSlateDrawElement::MakeLines(Out, LayerId + 4, Geometry.ToPaintGeometry(), Arrow, ESlateDrawEffect::None, FLinearColor::White, true, 6.f);
	FSlateDrawElement::MakeLines(Out, LayerId + 5, Geometry.ToPaintGeometry(), Arrow, ESlateDrawEffect::None, bInside ? Coral : Coral * 0.6f, true, 3.f);
	return LayerId + 5;
}
