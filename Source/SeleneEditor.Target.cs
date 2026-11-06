// Selene editor target.

using UnrealBuildTool;
using System.Collections.Generic;

public class SeleneEditorTarget : TargetRules
{
	public SeleneEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.V7;
		IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;
		ExtraModuleNames.Add("Selene");
	}
}
