// Selene runtime module.

using UnrealBuildTool;

public class Selene : ModuleRules
{
	public Selene(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		// Several UI files share short anonymous-namespace names (colours); unity blobs would collide.
		bUseUnity = false;

		PublicDependencyModuleNames.AddRange(new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"DeveloperSettings",
			"InputCore",
			"EnhancedInput",
			"AIModule",
			"UMG",
			"Slate",
			"SlateCore",
			"RenderCore",
			"RHI",
			"Json",
			"AnimGraphRuntime",
			"KawaiiPhysics"
		});

		PublicIncludePaths.Add("Selene");
	}
}
