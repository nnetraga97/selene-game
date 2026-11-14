#include "UI/SSeleneMinimap.h"

#include "Lanes/SeleneLaneDirector.h"
#include "SeleneCharacter.h"
#include "Combat/SeleneCombat.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"

namespace
{
	TAutoConsoleVariable<int32> CVarMinimap(TEXT("selene.Minimap"), 1, TEXT("0 hides the lane minimap."));
	TAutoConsoleVariable<float> CVarMinimapWidth(TEXT("selene.MinimapWidth"), 440.f, TEXT("Minimap width in screen units."));
}

void SSeleneMinimap::Construct(const FArguments& InArgs)
{
	Controller = InArgs._Controller;
	SetVisibility(EVisibility::HitTestInvisible);
}

void SSeleneMinimap::CacheWorld() const
{
	const APlayerController* PC = Controller.Get();
	UWorld* World = PC ? PC->GetWorld() : nullptr;
	ASeleneLaneDirector* Found = ASeleneLaneDirector::Get(World);
	if (!Found || Found->Lanes.IsEmpty()) return;
	Director = Found;
	bCached = true;
	Bounds = FBox2f(ForceInit);
	Bounds += FVector2f(FVector2D(Found->DawnBase));
	Bounds += FVector2f(FVector2D(Found->DuskBase));
	for (const FSeleneLane& Lane : Found->Lanes)
	{
		for (const FVector& Point : Lane.Points) Bounds += FVector2f(FVector2D(Point));
	}
	Bounds = Bounds.ExpandBy(3600.f);
	// Building footprints: every static mesh actor taller than a wall whose centre is on the map.
	for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
	{
		const UStaticMeshComponent* Component = It->GetStaticMeshComponent();
		const UStaticMesh* Mesh = Component ? Component->GetStaticMesh() : nullptr;
		if (!Mesh) continue;
		const FBox Local = Mesh->GetBoundingBox();
		const FTransform& Xf = Component->GetComponentTransform();
		const float Height = Local.GetSize().Z * Xf.GetScale3D().Z;
		const FVector Centre = Xf.TransformPosition(Local.GetCenter());
		if (Height < 550.f || !Bounds.IsInside(FVector2f(FVector2D(Centre)))) continue;
		TArray<FVector2f>& Quad = Footprints.AddDefaulted_GetRef();
		for (const FVector2D& Corner : { FVector2D(Local.Min.X, Local.Min.Y), FVector2D(Local.Max.X, Local.Min.Y),
			FVector2D(Local.Max.X, Local.Max.Y), FVector2D(Local.Min.X, Local.Max.Y), FVector2D(Local.Min.X, Local.Min.Y) })
		{
			Quad.Add(FVector2f(FVector2D(Xf.TransformPosition(FVector(Corner.X, Corner.Y, 0.0)))));
		}
	}
}

int32 SSeleneMinimap::OnPaint(const FPaintArgs& Args, const FGeometry& Geometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& Out, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	if (CVarMinimap.GetValueOnGameThread() == 0) return LayerId;
	if (!bCached) CacheWorld();
	const ASeleneLaneDirector* Lanes = Director.Get();
	if (!Lanes) { bCached = false; return LayerId; }

	const FSlateBrush* White = FCoreStyle::Get().GetBrush("GenericWhiteBox");
	const FVector2f Screen = FVector2f(Geometry.GetLocalSize());
	const FVector2f World = Bounds.GetSize();
	const float Width = FMath::Clamp(CVarMinimapWidth.GetValueOnGameThread(), 160.f, Screen.X * 0.6f);
	const float Scale = Width / World.X;
	const FVector2f Size(Width, World.Y * Scale);
	const FVector2f Origin(Screen.X - Size.X - 18.f, Screen.Y - Size.Y - 18.f);
	// World +X runs right and world +Y runs down the screen, which matches the layout diagram.
	auto ToMap = [&](const FVector2f& P) { return Origin + (P - Bounds.Min) * Scale; };
	const FPaintGeometry Full = Geometry.ToPaintGeometry();
	auto Dot = [&](int32 Layer, const FVector2f& At, float Half, const FLinearColor& Colour)
	{
		FSlateDrawElement::MakeBox(Out, Layer, Geometry.ToPaintGeometry(FVector2f(Half * 2.f, Half * 2.f), FSlateLayoutTransform(At - FVector2f(Half, Half))), White, ESlateDrawEffect::None, Colour);
	};

	FSlateDrawElement::MakeBox(Out, LayerId, Geometry.ToPaintGeometry(Size + FVector2f(6.f, 6.f), FSlateLayoutTransform(Origin - FVector2f(3.f, 3.f))), White, ESlateDrawEffect::None, FLinearColor(0.85f, 0.82f, 0.74f, 0.9f));
	FSlateDrawElement::MakeBox(Out, LayerId + 1, Geometry.ToPaintGeometry(Size, FSlateLayoutTransform(Origin)), White, ESlateDrawEffect::None, FLinearColor(0.035f, 0.045f, 0.06f, 0.88f));

	TArray<FVector2f> Line;
	for (const TArray<FVector2f>& Quad : Footprints)
	{
		Line.Reset();
		for (const FVector2f& Corner : Quad) Line.Add(ToMap(Corner));
		FSlateDrawElement::MakeLines(Out, LayerId + 2, Full, Line, ESlateDrawEffect::None, FLinearColor(0.42f, 0.46f, 0.52f, 0.9f), false, 1.f);
	}
	static const FLinearColor LaneColours[] = { FLinearColor(0.91f, 0.76f, 0.35f), FLinearColor(0.35f, 0.69f, 0.91f), FLinearColor(0.48f, 0.85f, 0.56f) };
	for (int32 i = 0; i < Lanes->Lanes.Num(); ++i)
	{
		Line.Reset();
		Line.Add(ToMap(FVector2f(FVector2D(Lanes->DawnBase))));
		for (const FVector& Point : Lanes->Lanes[i].Points) Line.Add(ToMap(FVector2f(FVector2D(Point))));
		Line.Add(ToMap(FVector2f(FVector2D(Lanes->DuskBase))));
		FSlateDrawElement::MakeLines(Out, LayerId + 3, Full, Line, ESlateDrawEffect::None, LaneColours[i % 3].CopyWithNewOpacity(0.55f), true, 2.f);
	}

	const FLinearColor Dawn(1.f, 0.82f, 0.25f), Dusk(0.72f, 0.42f, 1.f);
	Lanes->ForEachUnit([&](const ASeleneLaneUnit& Unit)
	{
		if (!Unit.IsAlive()) return;
		const FLinearColor Colour = Unit.Team == ESeleneTeam::Dawn ? Dawn : Dusk;
		const FVector2f At = ToMap(FVector2f(Unit.Pos));
		if (!Unit.bStructure) { Dot(LayerId + 4, At, 2.4f, Colour); return; }
		const float Half = Unit.Kind == ESeleneUnitKind::Patron ? 7.f : Unit.Kind == ESeleneUnitKind::Walker ? 5.f : 4.f;
		Dot(LayerId + 5, At, Half + 1.5f, FLinearColor::Black);
		Dot(LayerId + 6, At, Half, Colour);
		// health: the lit part of a bar under the structure
		const float Health = FMath::Clamp(Unit.Health / FMath::Max(Unit.MaxHealth, 1.f), 0.f, 1.f);
		FSlateDrawElement::MakeBox(Out, LayerId + 6, Geometry.ToPaintGeometry(FVector2f((Half * 2.f + 3.f) * Health, 2.f), FSlateLayoutTransform(At + FVector2f(-Half - 1.5f, Half + 3.f))), White, ESlateDrawEffect::None, FLinearColor(0.45f, 1.f, 0.5f));
	});

	const APlayerController* PC = Controller.Get();
	// Other heroes: ringed team-coloured dots.
	if (const USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(PC))
	{
		Combat->ForEachHero([&](ASeleneCharacter& Hero)
		{
			if (Hero.IsPlayerControlled() || !Hero.IsCombatAlive()) return;
			const FVector2f At = ToMap(FVector2f(FVector2D(Hero.GetActorLocation())));
			Dot(LayerId + 6, At, 6.f, FLinearColor::Black);
			Dot(LayerId + 7, At, 4.5f, Hero.GetTeam() == ESeleneTeam::Dawn ? FLinearColor(0.42f, 0.86f, 1.f) : FLinearColor(1.f, 0.36f, 0.32f));
		});
	}
	if (const APawn* Pawn = PC ? PC->GetPawn() : nullptr)
	{
		const FVector2f Raw = ToMap(FVector2f(FVector2D(Pawn->GetActorLocation())));
		const FVector2f At(FMath::Clamp(Raw.X, Origin.X + 4.f, Origin.X + Size.X - 4.f), FMath::Clamp(Raw.Y, Origin.Y + 4.f, Origin.Y + Size.Y - 4.f));
		// Screen x = world X and screen y = world Y, so world yaw is the screen angle directly.
		const float Yaw = FMath::DegreesToRadians(Pawn->GetActorRotation().Yaw);
		const float C = FMath::Cos(Yaw), S = FMath::Sin(Yaw);
		auto Rotate = [&](float Forward, float Side) { return At + FVector2f(Forward * C - Side * S, Forward * S + Side * C); };
		TArray<FVector2f> Arrow = { Rotate(9.f, 0.f), Rotate(-6.f, -6.f), Rotate(-2.f, 0.f), Rotate(-6.f, 6.f), Rotate(9.f, 0.f) };
		FSlateDrawElement::MakeLines(Out, LayerId + 7, Full, Arrow, ESlateDrawEffect::None, FLinearColor::Black, true, 5.f);
		FSlateDrawElement::MakeLines(Out, LayerId + 8, Full, Arrow, ESlateDrawEffect::None, FLinearColor::White, true, 2.5f);
		// view cone: where the camera looks
		const float View = FMath::DegreesToRadians(PC->GetControlRotation().Yaw);
		for (const float Edge : { -0.6f, 0.6f })
		{
			TArray<FVector2f> Ray = { At, At + FVector2f(FMath::Cos(View + Edge), FMath::Sin(View + Edge)) * 26.f };
			FSlateDrawElement::MakeLines(Out, LayerId + 7, Full, Ray, ESlateDrawEffect::None, FLinearColor(1.f, 1.f, 1.f, 0.45f), true, 1.f);
		}
	}
	return LayerId + 8;
}
