#!/usr/bin/env python3
"""Regenerate the checkpoint map. Run with uv run --with matplotlib."""

import argparse
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from matplotlib.lines import Line2D
from layout_core import ROOT, load, polygon, height, surface_pads, length
from validate_layout import validate


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--layout", default=str(ROOT / "Design/Blockout/layout.json"))
    ap.add_argument("--out", default=str(ROOT / "Design/Blockout/map.png"))
    args = ap.parse_args()
    d = load(args.layout)
    errors = validate(d)
    if errors:
        raise SystemExit("\n".join(errors))
    fig, ax = plt.subplots(figsize=(17, 13), facecolor="#f6f3eb")
    ax.set_facecolor("#f6f3eb")
    colors = {a["id"]: a["color"] for a in d["areas"]}
    x0, y0, x1, y1 = d["terrain"]["bounds"]
    pads = surface_pads(d)
    xs = list(range(x0, x1 + 1, 5))
    ys = list(range(y0, y1 + 1, 5))
    zs = [[height(d, x, y, pads) for x in xs] for y in ys]
    for a in d["areas"]:
        ax.add_patch(
            Polygon(polygon(a), fc=a["color"], ec=a["color"], alpha=0.19, lw=1.5)
        )
    cs = ax.contour(
        xs,
        ys,
        zs,
        levels=[4, 8, 12, 16, 20, 24, 28],
        colors="#8b9982",
        linewidths=0.55,
        alpha=0.7,
    )
    ax.clabel(cs, fmt="%dm", fontsize=7)
    for s in d["slabs"]:
        ax.add_patch(
            Polygon(
                polygon(s),
                fc="#b7c99c" if s["kind"] == "garden" else "#e4d5b7",
                ec="#9c917b",
                lw=0.8,
            )
        )
        if s["id"] in ("central_plaza", "side_square", "overlook", "courtyard"):
            ax.text(
                *s["center"],
                s["id"].replace("_", " ").upper(),
                ha="center",
                va="center",
                fontsize=7,
                color="#554e42",
            )
    for s in d["streets"] + d["stairs"]:
        pts = s["points"]
        ax.plot(
            [p[0] for p in pts],
            [p[1] for p in pts],
            lw=s["width"] * 0.6,
            color="#c5c1b5",
            solid_capstyle="butt",
            zorder=3,
        )
        if s in d["stairs"]:
            for i in range(1, 15):
                a, b = pts
                t = i / 15
                y = a[1] + (b[1] - a[1]) * t
                ax.plot(
                    [a[0] - s["width"] / 2, a[0] + s["width"] / 2],
                    [y, y],
                    color="#766e5f",
                    lw=0.6,
                    zorder=4,
                )
    for l in d["lots"]:
        ax.add_patch(
            Polygon(
                polygon(l["footprint"]),
                fc=colors[l["area"]],
                ec="#494842",
                lw=1.4 if l["hero"] else 0.55,
                zorder=5,
            )
        )
        x, y = l["footprint"]["center"]
        label = f"{l['storeys']}F"
        ax.text(x, y, label, fontsize=6, ha="center", va="center", zorder=7)
        if l["hero"]:
            ax.plot(x - 3, y + 3, "*", color="#6d4720", ms=7, zorder=8)
        if "interior" in l:
            ax.plot(
                x + 3,
                y + 3,
                "s",
                mfc="none" if l["interior"]["optional"] else "#fff",
                mec="#222",
                ms=6,
                zorder=8,
            )
            ax.annotate(
                l["id"].replace("_", " "),
                (x, y),
                xytext=(5, -17),
                textcoords="offset points",
                fontsize=7,
                zorder=9,
            )
            for o in l["interior"]["openings"]:
                if o["kind"] != "door":
                    continue
                w, h = l["footprint"]["size"]
                dx, dy = {
                    "north": (o["offset"], h / 2),
                    "south": (o["offset"], -h / 2),
                    "east": (w / 2, o["offset"]),
                    "west": (-w / 2, o["offset"]),
                }[o["wall"]]
                ax.plot(x + dx, y + dy, "o", color="#fff", mec="#333", ms=4, zorder=9)
    v = d["viaduct"]
    ax.plot(
        [p[0] for p in v["points"]],
        [p[1] for p in v["points"]],
        lw=7,
        color="#646979",
        alpha=0.8,
        zorder=8,
    )
    ax.text(
        -232,
        65,
        "MONORAIL  •  deck +12 m",
        fontsize=8,
        va="bottom",
        color="#343946",
        zorder=10,
    )
    for r, color in zip(d["routes"], ["#bd315a", "#166f8e", "#7440a1"]):
        pts = r["points"]
        ax.plot(
            [p[0] for p in pts],
            [p[1] for p in pts],
            color=color,
            lw=1.5,
            zorder=11,
            alpha=0.9,
        )
        for a, b in zip(pts, pts[1:]):
            if ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 < 5:
                continue
            ax.annotate(
                "",
                xy=(a[0] + 0.6 * (b[0] - a[0]), a[1] + 0.6 * (b[1] - a[1])),
                xytext=(a[0] + 0.4 * (b[0] - a[0]), a[1] + 0.4 * (b[1] - a[1])),
                arrowprops=dict(arrowstyle="->", color=color, lw=1.2),
                zorder=12,
            )
    for a in d["areas"]:
        x, y = a["center"]
        w, h = a["size"]
        ax.text(
            x,
            y + h / 2 + 4,
            a["label"].upper(),
            fontsize=10,
            fontweight="bold",
            ha="center",
            color="#383d3d",
            zorder=15,
        )
    for b in d["boundaries"]:
        ax.plot(
            [p[0] for p in b["points"]],
            [p[1] for p in b["points"]],
            color="#7a8179",
            lw=3,
            zorder=6,
        )
    ax.text(
        20,
        -194,
        "BAY BACKDROP / EMBANKMENT + RAILINGS",
        fontsize=8,
        color="#5b777f",
        ha="center",
    )
    px, py, _ = d["player_start"]["position"]
    ax.plot(px, py, "^", color="#181818", ms=9, zorder=15)
    ax.annotate(
        "Player start",
        (px, py),
        xytext=(20, -35),
        textcoords="offset points",
        fontsize=8,
        arrowprops=dict(arrowstyle="-", color="#222"),
        zorder=16,
    )
    for x, w, c in [(-225, 25, "#333"), (-200, 25, "#fff")]:
        ax.add_patch(Rectangle((x, -188), w, 3, fc=c, ec="#333", zorder=15))
    ax.text(-200, -180, "0      25      50 m", ha="center", fontsize=8)
    ax.annotate(
        "N",
        xy=(224, 189),
        xytext=(224, 165),
        ha="center",
        fontweight="bold",
        arrowprops=dict(arrowstyle="-|>", color="#222", lw=2),
    )
    handles = [
        Line2D([], [], color=c, lw=2, label=f"{r['id']} · {length(d, r):.0f} m")
        for r, c in zip(d["routes"], ["#bd315a", "#166f8e", "#7440a1"])
    ]
    handles += [
        Line2D(
            [],
            [],
            marker="*",
            color="none",
            mfc="#6d4720",
            mec="#6d4720",
            label="Hero façade",
        ),
        Line2D(
            [],
            [],
            marker="s",
            color="none",
            mfc="white",
            mec="#222",
            label="Interior (hollow = optional)",
        ),
    ]
    ax.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(0, -0.055),
        ncol=5,
        frameon=False,
        fontsize=9,
    )
    ax.set(
        xlim=(x0 - 12, x1 + 12),
        ylim=(y0 - 6, y1 + 20),
        xlabel="East / layout X (m)",
        ylabel="North / layout Y (m)",
        aspect="equal",
    )
    ax.set_title(
        "SELENE  /  HILLSIDE TOWN BLOCKOUT\n57 lots · 10 hero façades · 3 required interiors + 1 optional · 480 × 400 m",
        loc="left",
        fontsize=16,
        pad=18,
    )
    ax.grid(alpha=0.12)
    fig.tight_layout()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=170)
    plt.close(fig)
    print(Path(args.out).resolve())


if __name__ == "__main__":
    main()
