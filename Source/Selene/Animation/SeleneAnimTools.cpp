#include "Animation/SeleneAnimTools.h"

#include "Animation/BlendSpace.h"

int32 USeleneAnimTools::RebuildBlendSpace(UBlendSpace* BlendSpace)
{
	if (!BlendSpace) return -1;
#if WITH_EDITOR
	BlendSpace->Modify();
	BlendSpace->ValidateSampleData();
	BlendSpace->ResampleData();
	BlendSpace->MarkPackageDirty();
	return BlendSpace->GetGridSamples().Num();
#else
	return 0;
#endif
}
