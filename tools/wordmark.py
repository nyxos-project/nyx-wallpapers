#!/usr/bin/env python3
"""Draw the NyxOS wordmark wallpapers for every built-in Nyx theme.

    tools/wordmark.py [--themes builtin-themes.json] [--only ID…]

Writes, for each theme, <theme>/wordmark/nyx_wordmark_desktop_4K.png (NYXOS, centred)
and nyx_wordmark_lock_4K.png (N, Y and X stacked on the right, clear of the lock
screen's clock and card), and wordmark/*.svg, the two marks alone in `currentColor`.
The colours are the theme's background and logo colour from nyx-design's
builtin-themes.json. Needs rsvg-convert.
"""

import argparse
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
W, H = 3840, 2160

# Backgrounds that differ from the theme's surface: Mocha's is its mantle, a shade darker.
BACKGROUND = {"catppuccin-mocha": "#181825"}

# NYXOS: 14 rows, a 3-cell stroke, 2-cell gaps.
NYXOS = [
    ["..######..", ".########."] + ["###....###"] * 10 + [".##....##.", "..#....#.."],
    [".##...###"]
    + ["###...###"] * 5
    + [".########", "..#######", "......###", "..##..###"]
    + [".###..###"] * 2
    + [".#######.", "..#####.."],
    ["###...###"] * 4
    + [".###.###.", "..#####..", "...###...", "..#####..", ".###.###."]
    + ["###...###"] * 4
    + [".##...##."],
    ["..#####..", ".#######."] + ["###...###"] * 10 + [".#######.", "..#####.."],
    [
        "..#######", ".########", "###...###", "###...###", "###......", "###......", "########.",
        ".########", "......###", "###...###", "###...###", "###...###", "########.", "#######..",
    ],
]
NYXOS_GAP = 2

# N, Y and X stacked: 13 × 17 each, a 4-cell stroke, 3-cell gaps. The Y's stem sits half
# a cell right so it centres under the bowl.
STACKED = [
    [
        ".##......##..", "####.....###.", "#####....####", "######...####", "#######..####",
        "#######..####", "########.####", "####.###.####", "####..#######", "####...######",
        "####...######", "####....#####", "####.....####", "####.....####", "####.....####",
        "####.....####", "####.....###.",
    ],
    ["####.....####"] * 6
    + ["#####...#####", ".###########.", "..#########..", "...#######..."]
    + ["....####....."] * 7,
    ["####.....####"] * 4
    + [".####...####.", "..####.####..", "..#########..", "...#######...", "....#####....",
       "...#######...", "..####.####..", ".####...####."]
    + ["####.....####"] * 5,
]
STACKED_HALF = {(1, r) for r in range(10, 17)}
STACKED_GAP = 3

# One wordmark pixel on the 4K wallpaper: about 1.1% of the height. Even, so half
# cells land on whole pixels. Nyx Plymouth draws NYXOS at the same size.
CELL = 24


def runs(row):
    x = 0
    while x < len(row):
        if row[x] == "#":
            start = x
            while x < len(row) and row[x] == "#":
                x += 1
            yield start, x - start
        else:
            x += 1


def nyxos_rects(ox, oy, cell):
    rects, x = [], 0
    for glyph in NYXOS:
        for r, row in enumerate(glyph):
            rects += [(ox + (x + s) * cell, oy + r * cell, n * cell, cell) for s, n in runs(row)]
        x += len(glyph[0]) + NYXOS_GAP
    return rects


def stacked_rects(ox, oy, cell):
    rects, y = [], 0
    for i, glyph in enumerate(STACKED):
        for r, row in enumerate(glyph):
            shift = cell / 2 if (i, r) in STACKED_HALF else 0
            rects += [(ox + s * cell + shift, oy + (y + r) * cell, n * cell, cell) for s, n in runs(row)]
        y += len(glyph) + STACKED_GAP
    return rects


def nyxos_size():
    return sum(len(g[0]) for g in NYXOS) + NYXOS_GAP * (len(NYXOS) - 1), len(NYXOS[0])


def stacked_size():
    return len(STACKED[0][0]), sum(len(g) for g in STACKED) + STACKED_GAP * (len(STACKED) - 1)


def group(rects, fill):
    body = "".join(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}"/>' for x, y, w, h in rects)
    return f'<g fill="{fill}" shape-rendering="crispEdges">{body}</g>'


def svg(w, h, body, bg=None):
    back = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{back}{body}</svg>\n'


def render(doc, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["rsvg-convert", "-o", str(out)], input=doc.encode(), check=True)


def desktop(bg, fill):
    cw, ch = nyxos_size()
    ox, oy = (W - cw * CELL) // 2, (H - ch * CELL) // 2
    return svg(W, H, group(nyxos_rects(ox, oy, CELL), fill), bg)


def lock(bg, fill):
    sw, sh = stacked_size()
    ox, oy = round(W * 0.858 - sw * CELL / 2), (H - sh * CELL) // 2
    return svg(W, H, group(stacked_rects(ox, oy, CELL), fill), bg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--themes", default=str(HERE.parent / "nyx-design/crates/nyx-theme-core/builtin-themes.json"))
    ap.add_argument("--only", nargs="*", default=[])
    a = ap.parse_args()

    cw, ch = nyxos_size()
    sw, sh = stacked_size()
    (HERE / "wordmark").mkdir(exist_ok=True)
    (HERE / "wordmark/nyxos.svg").write_text(svg(cw, ch, group(nyxos_rects(0, 0, 1), "currentColor")))
    (HERE / "wordmark/nyx-stacked.svg").write_text(svg(sw, sh, group(stacked_rects(0, 0, 1), "currentColor")))

    themes = json.loads(Path(a.themes).read_text())
    for tid, theme in themes.items():
        if a.only and tid not in a.only:
            continue
        colours = theme["colors"]
        bg, fill = BACKGROUND.get(tid, colours["surface.primary"]), colours["brand.logo"]
        render(desktop(bg, fill), HERE / tid / "wordmark/nyx_wordmark_desktop_4K.png")
        render(lock(bg, fill), HERE / tid / "wordmark/nyx_wordmark_lock_4K.png")
        print(tid)


if __name__ == "__main__":
    main()
