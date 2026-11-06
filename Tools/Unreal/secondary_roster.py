"""Writes the SecondaryChains/SecondaryColliders of the Champion and Angel roster entries in Config/DefaultGame.ini.

Tuning lives here (Kawaii Physics PhysicsSettings): Damping (higher = calmer), Stiffness (higher = snaps back to the
animated pose), WorldDampingLocation/Rotation (share of the character's own movement the chain ignores; Kawaii's
0.8 default makes cloth barely react), LimitAngle (deg, 0 = free), GravityZ (cm/s^2). Run: python3 Tools/Unreal/secondary_roster.py
"""
import re
from pathlib import Path

G = -490.0
# name, damping, stiffness, world_loc, world_rot, radius, limit_angle, gravity
CHAMPION = (
    [("braid_00", .18, .10, .65, .70, 1.8, 50, G)]
    + [(n, .18, .08, .60, .68, .8, 45, G) for n in ("skirt_front_l_00", "skirt_front_r_00", "skirt_back_l_00")]
    + [(n, .18, .08, .60, .68, 1.0, 45, G) for n in ("skirt_side_front_r_00", "skirt_side_back_r_00", "skirt_back_r_00")]
    + [(n, .12, .05, .55, .60, .4, 70, G) for n in ("ribbon_r1_00", "ribbon_r2_00")]
    + [(n, .20, .10, .60, .65, .35, 25, G * .5) for n in ("hair_front_r_00", "hair_front_l_00", "hair_front_c_00")]
    + [("tassel_hip_r_00", .15, .08, .60, .65, .5, 45, G)]
)
ANGEL = (
    [(f"dress_{n}_00", .18, .09, .62, .70, 2, 40, G) for n in ("front_c", "front_l", "back_l", "back_c", "back_r", "front_r")]
    + [(f"wing_{s}_00", .30, .25, .60, .70, 3, 20, G * .3) for s in "lr"]
    + [(f"hair_{n}_00", .18, .10, .65, .70, 1.5, 40, G) for n in ("side_l", "back_l", "back_r", "side_r")]
)


def body(hips, spine, chest, thigh, calf, arm):
    return [("Hips", None, hips), ("Spine", "Spine2", spine), ("Spine2", "Neck", chest),
            ("LeftUpLeg", "LeftLeg", thigh), ("RightUpLeg", "RightLeg", thigh),
            ("LeftLeg", "LeftFoot", calf), ("RightLeg", "RightFoot", calf),
            ("LeftArm", "LeftForeArm", arm), ("RightArm", "RightForeArm", arm)]


def chains(rows):
    return "SecondaryChains=(" + ",".join(
        '(RootBone="%s",Damping=%g,Stiffness=%g,WorldDampingLocation=%g,WorldDampingRotation=%g,Radius=%g,LimitAngle=%g,GravityZ=%g)' % r
        for r in rows) + ")"


def colliders(rows):
    return "SecondaryColliders=(" + ",".join(
        '(Bone="mixamorig_%s"%s,Radius=%g)' % (b, (',ChildBone="mixamorig_%s"' % c) if c else "", r) for b, c, r in rows) + ")"


def main():
    path = Path(__file__).resolve().parents[2] / "Config" / "DefaultGame.ini"
    text = path.read_text()
    blocks = {"Champion": chains(CHAMPION) + "," + colliders(body(11, 9, 9.5, 6, 4.5, 4)),
              "Angel": chains(ANGEL) + "," + colliders(body(10.5, 8.5, 9, 6.5, 5, 4.5))}
    lines = text.split("\n")
    for i, line in enumerate(lines):
        for name, block in blocks.items():
            if line.startswith('+Roster=(Name="%s"' % name):
                line = re.sub(r",SecondaryChains=\(.*$", "", line.rstrip(")")) if "SecondaryChains" in line else line[:-1]
                lines[i] = line + "," + block + ")"
    path.write_text("\n".join(lines))
    print("updated", path)


if __name__ == "__main__":
    main()
