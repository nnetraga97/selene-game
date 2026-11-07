from pathlib import Path
import numpy as np
r=Path(__file__).resolve().parents[2]/'Saved/TownV2/session-3/meshes'
z=np.load(r/'graded-elevation-metres.npy');z.astype('<f4').T.tofile(r/'graded-elevation-ue.f32')
