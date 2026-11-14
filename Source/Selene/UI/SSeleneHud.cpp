#include "UI/SSeleneHud.h"

#include "SeleneCharacter.h"
#include "Combat/SeleneCombat.h"
#include "Lanes/SeleneLaneDirector.h"
#include "Engine/World.h"
#include "Fonts/FontMeasure.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/PlayerController.h"
#include "Camera/PlayerCameraManager.h"
#include "HAL/IConsoleManager.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"
#include "Styling/SlateBrush.h"
#include "Brushes/SlateRoundedBoxBrush.h"

namespace
{
	TAutoConsoleVariable<int32> CVarHud(TEXT("selene.Hud"), 1, TEXT("0 hides the combat HUD."));

	const FLinearColor Ink(0.03f, 0.035f, 0.045f, 0.82f);
	const FLinearColor Paper(0.96f, 0.93f, 0.86f, 1.f);
	const FLinearColor Ally(0.42f, 0.86f, 1.f, 1.f);
	const FLinearColor Enemy(1.f, 0.36f, 0.32f, 1.f);
	const FLinearColor Gold(1.f, 0.82f, 0.3f, 1.f);
	const FLinearColor Muted(0.62f, 0.64f, 0.68f, 1.f);

	struct FPainter
	{
		FSlateWindowElementList& Out;
		const FGeometry& Geometry;
		const FSlateBrush* White;
		int32 Layer;

		void Box(const FVector2f& At, const FVector2f& Size, const FLinearColor& Colour, int32 Add = 0) const
		{
			if (Size.X <= 0.f || Size.Y <= 0.f) return;
			FSlateDrawElement::MakeBox(Out, Layer + Add, Geometry.ToPaintGeometry(Size, FSlateLayoutTransform(At)), White, ESlateDrawEffect::None, Colour);
		}
		void Line(const TArray<FVector2f>& Points, const FLinearColor& Colour, float Thickness, int32 Add = 0) const
		{
			FSlateDrawElement::MakeLines(Out, Layer + Add, Geometry.ToPaintGeometry(), Points, ESlateDrawEffect::None, Colour, true, Thickness);
		}
		FVector2f Measure(const FString& Text, const FSlateFontInfo& Font) const
		{
			return FVector2f(FSlateApplication::Get().GetRenderer()->GetFontMeasureService()->Measure(Text, Font));
		}
		/** Align: 0 left, 0.5 centre, 1 right (of At). */
		void Text(const FString& Text, const FVector2f& At, const FSlateFontInfo& Font, const FLinearColor& Colour, float Align = 0.f, int32 Add = 2, bool bShadow = true) const
		{
			const FVector2f Size = Measure(Text, Font);
			const FVector2f Pos(At.X - Size.X * Align, At.Y);
			if (bShadow)
			{
				FSlateDrawElement::MakeText(Out, Layer + Add, Geometry.ToPaintGeometry(Size, FSlateLayoutTransform(Pos + FVector2f(1.5f, 1.5f))), Text, Font, ESlateDrawEffect::None, FLinearColor(0, 0, 0, Colour.A * 0.8f));
			}
			FSlateDrawElement::MakeText(Out, Layer + Add + 1, Geometry.ToPaintGeometry(Size, FSlateLayoutTransform(Pos)), Text, Font, ESlateDrawEffect::None, Colour);
		}
		void Bar(const FVector2f& At, const FVector2f& Size, float Fill, const FLinearColor& Colour, int32 Add = 0) const
		{
			Box(At - FVector2f(1.5f, 1.5f), Size + FVector2f(3.f, 3.f), FLinearColor(0, 0, 0, 0.75f * Colour.A), Add);
			Box(At, Size, FLinearColor(0.12f, 0.12f, 0.14f, 0.85f * Colour.A), Add + 1);
			Box(At, FVector2f(Size.X * FMath::Clamp(Fill, 0.f, 1.f), Size.Y), Colour, Add + 2);
		}
	};

	FSlateFontInfo Font(const char* Style, int32 Size) { return FCoreStyle::GetDefaultFontStyle(Style, Size); }

	const TCHAR* StructureName(ESeleneUnitKind Kind)
	{
		switch (Kind)
		{
		case ESeleneUnitKind::Guardian: return TEXT("GUARDIAN");
		case ESeleneUnitKind::Walker: return TEXT("WALKER");
		case ESeleneUnitKind::Patron: return TEXT("PATRON");
		case ESeleneUnitKind::BaseGuardian: return TEXT("BASE GUARDIAN");
		case ESeleneUnitKind::Shrine: return TEXT("SHRINE");
		default: return TEXT("");
		}
	}
}

void SSeleneHud::Construct(const FArguments& InArgs)
{
	Controller = InArgs._Controller;
	SetVisibility(EVisibility::HitTestInvisible);
}

int32 SSeleneHud::OnPaint(const FPaintArgs& Args, const FGeometry& Geometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& Out, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	APlayerController* PC = Controller.Get();
	if (!PC || CVarHud.GetValueOnGameThread() == 0) return LayerId;
	UWorld* World = PC->GetWorld();
	USeleneCombatSubsystem* Combat = USeleneCombatSubsystem::Get(PC);
	ASeleneCharacter* Hero = Cast<ASeleneCharacter>(PC->GetPawn());
	if (!World || !Combat || !Hero) return LayerId;
	const ASeleneLaneDirector* Director = ASeleneLaneDirector::Get(World);
	const ASeleneLaneDirector::FObjectives Obj = Director ? Director->GetObjectives() : ASeleneLaneDirector::FObjectives();
	const double Now = Combat->Now();
	if (const_cast<SSeleneHud*>(this)->StartTime < 0.0) const_cast<SSeleneHud*>(this)->StartTime = Now;

	const FPainter P{ Out, Geometry, FCoreStyle::Get().GetBrush("GenericWhiteBox"), LayerId };
	const FVector2f Screen = FVector2f(Geometry.GetLocalSize());
	const FVector2f Centre = Screen * 0.5f;
	int32 ViewX = 1, ViewY = 1;
	PC->GetViewportSize(ViewX, ViewY);
	const float PixelToLocal = Screen.X / FMath::Max(ViewX, 1);
	auto Project = [&](const FVector& WorldPos, FVector2f& OutLocal)
	{
		FVector2D Pixel;
		if (!PC->ProjectWorldLocationToScreen(WorldPos, Pixel, false)) return false;
		OutLocal = FVector2f(Pixel) * PixelToLocal;
		return OutLocal.X > -50.f && OutLocal.Y > -50.f && OutLocal.X < Screen.X + 50.f && OutLocal.Y < Screen.Y + 50.f;
	};
	const FVector Eye = PC->PlayerCameraManager ? PC->PlayerCameraManager->GetCameraLocation() : Hero->GetActorLocation();
	const FVector Look = PC->GetControlRotation().Vector();

	// ---------------------------------------------------------------- world: health bars over units and heroes
	if (Director && Obj.bHasLanes)
	{
		for (const ASeleneLaneUnit* Unit : Director->GetUnits())
		{
			if (!Unit || !Unit->IsAlive()) continue;
			const FVector Top = Unit->Center() + FVector(0, 0, Unit->HalfHeight * (Unit->bStructure ? 1.15f : 1.05f) + 35.f);
			const float Dist = FVector::Dist(Eye, Top);
			if (Dist > (Unit->bStructure ? 9000.f : 3800.f) || FVector::DotProduct(Top - Eye, Look) <= 0.f) continue;
			FVector2f At;
			if (!Project(Top, At)) continue;
			const bool bFriend = Unit->Team == Hero->GetTeam();
			const FLinearColor Colour = bFriend ? Ally : Enemy;
			const float Fill = Unit->Health / FMath::Max(Unit->MaxHealth, 1.f);
			if (Unit->bStructure)
			{
				const bool bProtected = Director->IsProtected(*Unit);
				const float W = 150.f;
				P.Bar(At - FVector2f(W * 0.5f, 0.f), FVector2f(W, 9.f), Fill, bProtected ? Muted : Colour);
				P.Text(FString::Printf(TEXT("%s%s"), StructureName(Unit->Kind), bProtected ? TEXT("  ◆ PROTECTED") : TEXT("")),
					At - FVector2f(0.f, 22.f), Font("Bold", 10), bProtected ? Muted : Colour, 0.5f);
			}
			else
			{
				if (Fill >= 0.999f && Dist > 1600.f) continue;
				const float W = Unit->Kind == ESeleneUnitKind::Siege ? 64.f : 46.f;
				P.Bar(At - FVector2f(W * 0.5f, 0.f), FVector2f(W, 5.f), Fill, Colour.CopyWithNewOpacity(0.95f));
			}
		}
	}
	Combat->ForEachHero([&](ASeleneCharacter& Other)
	{
		if (&Other == Hero || !Other.IsCombatAlive()) return;
		FVector2f At;
		const FVector Top = Other.GetActorLocation() + FVector(0, 0, 125.f);
		if (FVector::DotProduct(Top - Eye, Look) <= 0.f || !Project(Top, At)) return;
		const FLinearColor Colour = Other.GetTeam() == Hero->GetTeam() ? Ally : Enemy;
		P.Bar(At - FVector2f(55.f, 0.f), FVector2f(110.f, 8.f), Other.GetHealth() / Other.GetMaxHealth(), Colour);
		P.Text(Other.GetActiveCharacterName().ToString().ToUpper(), At - FVector2f(0.f, 20.f), Font("Bold", 10), Colour, 0.5f);
	});

	// ---------------------------------------------------------------- damage numbers
	for (const FSeleneDamageNumber& N : Combat->DamageNumbers)
	{
		if (N.bToPlayer || N.Amount <= 0.f) continue;
		const float Age = float(Now - N.Time);
		FVector2f At;
		if (!Project(N.Location, At)) continue;
		const float A = FMath::Clamp(1.f - (Age - 0.6f) / 0.5f, 0.f, 1.f);
		const float Pop = 1.f + FMath::Max(0.f, 0.25f - Age) * 2.f;
		const FLinearColor Colour = (N.bHeavy ? Gold : Paper).CopyWithNewOpacity(A);
		P.Text(FString::FromInt(FMath::RoundToInt(N.Amount)), At - FVector2f(0.f, Age * 55.f), Font("Bold", int32((N.bHeavy ? 20 : 15) * Pop)), Colour, 0.5f, 4);
	}

	// ---------------------------------------------------------------- damage taken: vignette and direction
	const float Hurt = FMath::Clamp(1.f - float(Now - Combat->LastPlayerHurtTime) / 0.6f, 0.f, 1.f);
	const float LowHealth = Hero->IsCombatAlive() ? FMath::Clamp(1.f - Hero->GetHealth() / Hero->GetMaxHealth() / 0.3f, 0.f, 1.f) : 0.f;
	const float Vignette = FMath::Max(Hurt * 0.55f, LowHealth * (0.35f + 0.15f * FMath::Sin(Now * 6.0)));
	if (Vignette > 0.01f)
	{
		for (int32 i = 0; i < 6; ++i)
		{
			const float T = 14.f + i * 14.f;
			const FLinearColor C(0.75f, 0.02f, 0.02f, Vignette * (0.32f - i * 0.05f));
			P.Box(FVector2f(0, 0), FVector2f(Screen.X, T), C, 6);
			P.Box(FVector2f(0, Screen.Y - T), FVector2f(Screen.X, T), C, 6);
			P.Box(FVector2f(0, 0), FVector2f(T, Screen.Y), C, 6);
			P.Box(FVector2f(Screen.X - T, 0), FVector2f(T, Screen.Y), C, 6);
		}
	}
	if (Hurt > 0.01f && !Combat->LastPlayerHurtFrom.IsZero())
	{
		const FVector To = (Combat->LastPlayerHurtFrom - Hero->GetActorLocation()).GetSafeNormal2D();
		const float Angle = FMath::DegreesToRadians(FRotator::NormalizeAxis(To.Rotation().Yaw - PC->GetControlRotation().Yaw));
		const FVector2f Dir(FMath::Sin(Angle), -FMath::Cos(Angle));
		const FVector2f Side(-Dir.Y, Dir.X);
		const FVector2f Tip = Centre + Dir * 120.f;
		P.Line({ Tip - Side * 26.f - Dir * 10.f, Tip, Tip + Side * 26.f - Dir * 10.f }, FLinearColor(1.f, 0.15f, 0.1f, Hurt), 5.f, 7);
	}

	// ---------------------------------------------------------------- crosshair and hit marker
	if (Hero->IsCombatAlive() && Hero->GetCameraMode() == ESeleneCameraMode::ThirdPerson)
	{
		const float Gap = Hero->IsAiming() ? 5.f : 8.f, Len = 7.f;
		const FLinearColor C = Paper.CopyWithNewOpacity(0.9f);
		for (const FVector2f& D : { FVector2f(1, 0), FVector2f(-1, 0), FVector2f(0, 1), FVector2f(0, -1) })
		{
			P.Line({ Centre + D * Gap, Centre + D * (Gap + Len) }, FLinearColor(0, 0, 0, 0.6f), 4.f, 8);
			P.Line({ Centre + D * Gap, Centre + D * (Gap + Len) }, C, 2.f, 9);
		}
		P.Box(Centre - FVector2f(1.5f, 1.5f), FVector2f(3.f, 3.f), C, 9);
		const float Hit = FMath::Clamp(1.f - float(Now - Combat->LastHitMarkerTime) / 0.22f, 0.f, 1.f);
		if (Hit > 0.f)
		{
			const FLinearColor HC = (Combat->bLastHitWasKill ? FLinearColor(1.f, 0.3f, 0.25f) : FLinearColor::White).CopyWithNewOpacity(Hit);
			const float R0 = 9.f, R1 = 18.f + (1.f - Hit) * 4.f;
			for (const FVector2f& D : { FVector2f(1, 1), FVector2f(-1, 1), FVector2f(1, -1), FVector2f(-1, -1) })
			{
				const FVector2f N = D.GetSafeNormal();
				P.Line({ Centre + N * R0, Centre + N * R1 }, HC, 3.f, 10);
			}
		}
	}

	// Layout follows the lane-shooter convention (timer and team chips top centre, slanted health bar by the hero,
	// stamina under the crosshair, round ability row bottom centre, minimap bottom right) in Selene's own art.
	// One rounded brush per radius (a corner radius of exactly half the size draws a true circle).
	static TMap<int32, TUniquePtr<FSlateRoundedBoxBrush>> Rounds;
	auto Disc = [&](const FVector2f& C, float R, const FLinearColor& Colour, int32 Add)
	{
		const int32 Key = FMath::RoundToInt(R);
		TUniquePtr<FSlateRoundedBoxBrush>& Brush = Rounds.FindOrAdd(Key);
		if (!Brush) Brush = MakeUnique<FSlateRoundedBoxBrush>(FLinearColor::White, float(Key), FVector2f(Key * 2.f, Key * 2.f));
		FSlateDrawElement::MakeBox(Out, LayerId + Add, Geometry.ToPaintGeometry(FVector2f(Key * 2.f, Key * 2.f), FSlateLayoutTransform(C - FVector2f(Key, Key))), Brush.Get(), ESlateDrawEffect::None, Colour);
	};
	auto Slanted = [&](const FVector2f& At, const FVector2f& Size, const FLinearColor& Colour, int32 Add)
	{
		const FPaintGeometry G = Geometry.ToPaintGeometry(Size, FSlateLayoutTransform(At), FSlateRenderTransform(FShear2D(-0.22f, 0.f)), FVector2f(0.5f, 0.5f));
		FSlateDrawElement::MakeBox(Out, LayerId + Add, G, P.White, ESlateDrawEffect::None, Colour);
	};

	// ---------------------------------------------------------------- health (slanted bar left of the hero)
	{
		const float Fill = FMath::Clamp(Hero->GetHealth() / FMath::Max(Hero->GetMaxHealth(), 1.f), 0.f, 1.f);
		const FVector2f Size(26.f, 170.f);
		const FVector2f At(Screen.X * 0.27f, Screen.Y * 0.56f);
		const FLinearColor Fg = Fill > 0.3f ? FLinearColor(0.42f, 0.95f, 0.38f) : FLinearColor(1.f, 0.32f, 0.26f);
		Slanted(At - FVector2f(3.f, 3.f), Size + FVector2f(6.f, 6.f), FLinearColor(0, 0, 0, 0.7f), 1);
		Slanted(At, Size, FLinearColor(0.1f, 0.12f, 0.1f, 0.85f), 2);
		Slanted(At + FVector2f(0.f, Size.Y * (1.f - Fill)), FVector2f(Size.X, Size.Y * Fill), Fg, 3);
		P.Text(FString::FromInt(FMath::CeilToInt(Hero->GetHealth())), At + FVector2f(Size.X + 12.f, Size.Y * 0.55f), Font("Bold", 30), Paper, 0.f, 5);
		P.Text(FString::Printf(TEXT("/ %d"), FMath::RoundToInt(Hero->GetMaxHealth())), At + FVector2f(Size.X + 14.f, Size.Y * 0.55f + 38.f), Font("Bold", 11), Muted, 0.f, 5);
		if (Hero->IsStunned()) P.Text(TEXT("STUNNED"), At + FVector2f(Size.X + 12.f, Size.Y * 0.55f - 24.f), Font("Bold", 13), Gold, 0.f, 5);
		else if (Hero->GetBuffRemaining() > 0.f)
		{
			const TCHAR* Name = Hero->GetBuffKind() == ESeleneAbilityEffect::Guard ? TEXT("GUARD") : TEXT("OVERDRIVE");
			P.Text(FString::Printf(TEXT("%s %.0f"), Name, FMath::CeilToFloat(Hero->GetBuffRemaining())), At + FVector2f(Size.X + 12.f, Size.Y * 0.55f - 24.f), Font("Bold", 13), Gold, 0.f, 5);
		}
		// Hero name and the out-of-combat state, small, at the left edge.
		P.Text(Hero->GetActiveCharacterName().ToString().ToUpper(), FVector2f(28.f, Screen.Y - 120.f), Font("Bold", 14), Paper);
	}

	// ---------------------------------------------------------------- stamina chevrons under the crosshair
	if (Hero->IsCombatAlive())
	{
		const float Charges = Hero->GetDashCharges();
		for (int32 i = 0; i < 3; ++i)
		{
			const float F = FMath::Clamp(Charges - i, 0.f, 1.f);
			const FVector2f C = Centre + FVector2f((i - 1) * 16.f, 30.f);
			const FLinearColor Col = F >= 1.f ? Paper.CopyWithNewOpacity(0.85f) : FLinearColor(1.f, 0.82f, 0.3f, 0.35f + 0.5f * F);
			P.Line({ C + FVector2f(-6.f, -3.f), C + FVector2f(0.f, 3.f), C + FVector2f(6.f, -3.f) }, FLinearColor(0, 0, 0, 0.5f), 4.f, 8);
			P.Line({ C + FVector2f(-6.f, -3.f), C + FVector2f(0.f, 3.f), C + FVector2f(6.f, -3.f) }, Col, 2.f, 9);
		}
	}

	// ---------------------------------------------------------------- abilities: round icons bottom centre
	{
		const int32 Count = FMath::Min(Hero->GetAbilityCount(), 3);
		const float R = 27.f, Gap = 18.f;
		const float Total = Count * R * 2.f + (Count - 1) * Gap;
		const float Y = Screen.Y - 70.f;
		static const TCHAR* Keys[] = { TEXT("Q"), TEXT("E"), TEXT("R") };
		for (int32 i = 0; i < Count; ++i)
		{
			const FSeleneAbility* A = Hero->GetAbility(i);
			const float Cd = Hero->GetAbilityCooldown(i);
			const bool bReady = Cd <= 0.f && Hero->IsCombatAlive();
			const FVector2f C(Centre.X - Total * 0.5f + R + i * (R * 2.f + Gap), Y);
			Disc(C, R + 3.f, bReady ? FLinearColor(0.95f, 0.9f, 0.78f, 0.9f) : FLinearColor(0, 0, 0, 0.6f), 0);
			Disc(C, R, FLinearColor(0.07f, 0.08f, 0.1f, 0.92f), 1);
			// Cooldown: a dark cap that drains top to bottom, with the seconds left.
			if (Cd > 0.f && A && A->Cooldown > 0.f)
			{
				const float F = Cd / A->Cooldown;
				Disc(C, R * (0.35f + 0.65f * F), FLinearColor(0.25f, 0.27f, 0.32f, 0.9f), 2);
				P.Text(FString::FromInt(FMath::CeilToInt(Cd)), C - FVector2f(0.f, 12.f), Font("Bold", 17), Paper, 0.5f, 4);
			}
			else
			{
				FString Initials;
				if (A) { TArray<FString> Words; A->Name.ToString().ParseIntoArray(Words, TEXT(" ")); for (const FString& W : Words) Initials.AppendChar(W[0]); }
				P.Text(Initials.ToUpper(), C - FVector2f(0.f, 11.f), Font("Bold", 15), bReady ? Gold : Muted, 0.5f, 4);
			}
			// Key cap under the icon.
			P.Box(C + FVector2f(-11.f, R - 2.f), FVector2f(22.f, 16.f), FLinearColor(0, 0, 0, 0.75f), 3);
			P.Text(Keys[i], C + FVector2f(0.f, R - 2.f), Font("Bold", 10), Paper, 0.5f, 4);
		}
	}

	// ---------------------------------------------------------------- top bar: timer, team chips, lane structures
	if (Obj.bHasLanes)
	{
		const int32 Them = static_cast<int32>(Hero->GetTeam() == ESeleneTeam::Dawn ? ESeleneTeam::Dusk : ESeleneTeam::Dawn);
		const int32 Us = 1 - Them;
		const FVector2f Top(Centre.X, 14.f);
		P.Box(Top - FVector2f(42.f, 0.f), FVector2f(84.f, 34.f), Ink, 0);
		const int32 Mins = FMath::FloorToInt(Obj.Clock / 60.f), Secs = FMath::FloorToInt(Obj.Clock) % 60;
		P.Text(FString::Printf(TEXT("%d:%02d"), Mins, Secs), Top + FVector2f(0.f, 5.f), Font("Bold", 16), Paper, 0.5f, 2);
		if (!Obj.bGameOver) P.Text(FString::Printf(TEXT("wave %d"), FMath::Max(0, FMath::CeilToInt(Obj.NextWave - Obj.Clock))), Top + FVector2f(0.f, 37.f), Font("Regular", 9), Muted, 0.5f, 2);
		// Hero chips: ours on the left, theirs on the right; a dead hero shows its respawn seconds.
		TArray<ASeleneCharacter*> Sides[2];
		Combat->ForEachHero([&](ASeleneCharacter& H) { Sides[H.GetTeam() == Hero->GetTeam() ? 0 : 1].Add(&H); });
		for (int32 Side = 0; Side < 2; ++Side)
		{
			const FLinearColor Col = Side == 0 ? Ally : Enemy;
			for (int32 k = 0; k < Sides[Side].Num(); ++k)
			{
				ASeleneCharacter* H = Sides[Side][k];
				const float X = Side == 0 ? Top.X - 76.f - k * 52.f : Top.X + 76.f + k * 52.f;
				const FVector2f C(X, Top.Y + 18.f);
				Disc(C, 21.f, H->IsDead() ? FLinearColor(0.2f, 0.2f, 0.2f, 0.9f) : Col, 0);
				Disc(C, 18.f, FLinearColor(0.08f, 0.09f, 0.11f, 0.95f), 1);
				const FString Label = H->IsDead() ? FString::FromInt(FMath::CeilToInt(H->GetRespawnRemaining())) : H->GetActiveCharacterName().ToString().Left(2).ToUpper();
				P.Text(Label, C - FVector2f(0.f, 10.f), Font("Bold", 13), H->IsDead() ? Muted : Paper, 0.5f, 3);
				// Health sliver under the chip.
				P.Bar(C + FVector2f(-18.f, 25.f), FVector2f(36.f, 3.f), H->GetHealth() / FMath::Max(H->GetMaxHealth(), 1.f), Col, 1);
				if (H == Hero) P.Box(C + FVector2f(-4.f, -30.f), FVector2f(8.f, 4.f), Gold, 3);
			}
		}
		// Lane structures as pips under the chips: Guardians, Walkers, Patron per team.
		auto Pips = [&](int32 T, float X, float Dir, const FLinearColor& Col)
		{
			for (int32 k = 0; k < 3; ++k) P.Box(FVector2f(X + Dir * k * 12.f, Top.Y + 54.f), FVector2f(8.f, 8.f), k < Obj.Guardians[T] ? Col : FLinearColor(0.2f, 0.2f, 0.2f, 0.8f), 2);
			for (int32 k = 0; k < 3; ++k) P.Box(FVector2f(X + Dir * k * 12.f, Top.Y + 66.f), FVector2f(8.f, 8.f), k < Obj.Walkers[T] ? Col : FLinearColor(0.2f, 0.2f, 0.2f, 0.8f), 2);
			for (int32 k = 0; k < 2; ++k) P.Box(FVector2f(X + Dir * k * 12.f, Top.Y + 78.f), FVector2f(8.f, 8.f), k < Obj.BaseGuardians[T] ? Col : FLinearColor(0.2f, 0.2f, 0.2f, 0.8f), 2);
			for (int32 k = 0; k < 2; ++k) P.Box(FVector2f(X + Dir * (k + 2) * 12.f + Dir * 6.f, Top.Y + 78.f), FVector2f(8.f, 8.f), k < Obj.Shrines[T] ? Col.CopyWithNewOpacity(0.7f) : FLinearColor(0.2f, 0.2f, 0.2f, 0.8f), 2);
			P.Bar(FVector2f(X + (Dir < 0.f ? -32.f : 0.f), Top.Y + 92.f), FVector2f(40.f, 4.f), Obj.PatronHealth[T], Obj.bPatronProtected[T] ? Muted : Col, 1);
		};
		Pips(Us, Top.X - 60.f, -1.f, Ally);
		Pips(Them, Top.X + 52.f, 1.f, Enemy);

		// Focused enemy structure: a large bar under the top bar while one is near the crosshair.
		const ASeleneLaneUnit* Focus = nullptr; float Best = 0.97f;
		for (const ASeleneLaneUnit* U : Director->GetUnits())
		{
			if (!U || !U->bStructure || !U->IsAlive() || U->Team == Hero->GetTeam()) continue;
			const FVector To = U->Center() - Eye;
			if (To.Size() > 5000.f) continue;
			const float D = FVector::DotProduct(To.GetSafeNormal(), Look);
			if (D > Best) { Best = D; Focus = U; }
		}
		if (Focus)
		{
			const float W = 420.f; const FVector2f At(Centre.X - W * 0.5f, 120.f);
			const bool bProt = Director->IsProtected(*Focus);
			P.Text(FString::Printf(TEXT("ENEMY %s%s"), StructureName(Focus->Kind), bProt ? TEXT("  -  PROTECTED") : TEXT("")), At + FVector2f(W * 0.5f, -18.f), Font("Bold", 11), bProt ? Muted : Enemy, 0.5f, 3);
			P.Bar(At, FVector2f(W, 10.f), Focus->Health / FMath::Max(Focus->MaxHealth, 1.f), bProt ? Muted : Enemy, 1);
		}
	}

	// ---------------------------------------------------------------- announcements
	{
		float Y = Screen.Y * 0.2f;
		for (const FSeleneAnnouncement& A : Combat->Announcements)
		{
			const float Age = float(Now - A.Time);
			const float Alpha = FMath::Clamp(FMath::Min(Age / 0.15f, (A.Duration - Age) / 0.6f), 0.f, 1.f);
			const bool bBig = A.Text == TEXT("VICTORY") || A.Text == TEXT("DEFEAT");
			P.Text(A.Text, FVector2f(Centre.X, Y), Font("Bold", bBig ? 54 : 22), A.Color.CopyWithNewOpacity(Alpha), 0.5f, 12);
			Y += bBig ? 80.f : 36.f;
		}
	}

	// ---------------------------------------------------------------- death / respawn
	if (Hero->IsDead())
	{
		P.Box(FVector2f(0, 0), Screen, FLinearColor(0.05f, 0.f, 0.f, 0.35f), 11);
		P.Text(FString::Printf(TEXT("RESPAWNING IN %d"), FMath::Max(1, FMath::CeilToInt(Hero->GetRespawnRemaining()))),
			Centre + FVector2f(0.f, 40.f), Font("Bold", 26), Paper, 0.5f, 13);
	}

	// ---------------------------------------------------------------- controls hint (first seconds)
	const float Since = float(Now - StartTime);
	if (Since < 16.f)
	{
		const float A = FMath::Clamp((16.f - Since) / 2.f, 0.f, 1.f);
		P.Text(TEXT("LMB attack (hold to fire)   RMB aim   Q / E / R abilities   Shift dash   Space jump   Ctrl slide   C heroes   M map"),
			FVector2f(Centre.X, Screen.Y - 150.f), Font("Regular", 12), Paper.CopyWithNewOpacity(0.85f * A), 0.5f, 4);
	}
	return LayerId + 16;
}
