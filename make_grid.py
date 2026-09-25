#!/usr/bin/env python3
"""Generate showroom cabinet / module mapping grids from a NovaLCT receiving-card table.

NovaLCT lists every receiving card with its full cabinet size (StartX, StartY,
Width, Height). Cabinets can overlap: a "half" cabinet is configured with the
full 261x348 size but part of it is covered by the cabinet above it. As in the
NovaLCT canvas, the cabinet with the smaller StartY wins the overlap, so only
the uncovered part of the lower cabinet is drawn.

Outputs (in ./output):
  <name>_cabinets.svg / .png   - exact screen raster, one cell per cabinet
  <name>_modules.svg  / .png   - exact screen raster, one cell per module
  *_3840x2160.png              - same, placed at 0,0 on a UHD black canvas
"""
import os

import cairosvg

NAME = "Showroom LED"

# Sending card, port, receiving card, StartX, StartY, Width, Height  (from NovaLCT)
CARDS = [
    (1, 1, 1, 0, 522, 261, 348),
    (1, 1, 2, 261, 522, 261, 348),
    (1, 1, 3, 261, 174, 261, 348),
    (1, 1, 4, 0, 174, 261, 348),
    (1, 1, 5, 0, 0, 261, 348),
    (1, 1, 6, 261, 0, 261, 348),
    (1, 2, 1, 1827, 522, 261, 348),
    (1, 2, 2, 1566, 522, 261, 348),
    (1, 2, 3, 1305, 522, 261, 348),
    (1, 2, 4, 1044, 522, 261, 348),
    (1, 2, 5, 783, 522, 261, 348),
    (1, 2, 6, 522, 522, 261, 348),
]

MODULE_W, MODULE_H = 87, 174  # 3 x 2 modules per 261x348 cabinet

BG = ["#400000", "#004000", "#000040"]      # 25% R / G / B
LINE = ["#ff00ff", "#00ffff", "#ffff00"]    # magenta / cyan / yellow
PORT_COLORS = {1: "#00ff00", 2: "#ffff00", 3: "#00ffff", 4: "#ff00ff"}
FONT = "Arial, 'Liberation Sans', Helvetica, sans-serif"
LABEL_COLOR = "#e6b800"
UHD = (3840, 2160)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def visible_rects(cards):
    """Clip each cabinet vertically by any overlapping cabinet that starts higher."""
    result = []
    for c in cards:
        _, _, _, x, y, w, h = c
        top, bottom = y, y + h
        for o in cards:
            if o is c:
                continue
            _, _, _, ox, oy, ow, oh = o
            if ox >= x + w or ox + ow <= x or oy >= y:
                continue  # no horizontal overlap, or other one is lower -> we win
            if oy + oh > top:
                top = min(max(top, oy + oh), bottom)
        result.append((c, (x, top, w, bottom - top)))
    return [r for r in result if r[1][3] > 0]


def cell(x, y, w, h, bg, line):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{bg}"/>'
            f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{w - 1}" height="{h - 1}" '
            f'fill="none" stroke="{line}" stroke-width="1"/>')


def text(x, y, s, size, fill="#ffffff", anchor="start", weight="normal"):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{s}</text>')


def build(kind, rects, W, H):
    parts = []
    clip = "".join(f'<rect x="{x}" y="{y}" width="{w}" height="{h}"/>' for _, (x, y, w, h) in rects)

    # row index per distinct visible top edge -> physical rows for colour checker
    tops = sorted({r[1] for _, r in rects})
    for card, (x, y, w, h) in rects:
        _, port, rc, cx, cy, cw, ch = card
        cab_id = f"{card[0]}-{port}-{rc}"
        row = tops.index(y)
        col = x // cw
        half = h < ch
        if kind == "cabinets":
            k = (row + col) % 3
            parts.append(cell(x, y, w, h, BG[k], LINE[k]))
            size = 44 if not half else 38
            parts.append(text(x + w / 2, y + h / 2 + size * 0.35, cab_id, size, anchor="middle", weight="bold"))
            parts.append(text(x + 4, y + 18, f"R{row + 1} C{col + 1}", 16))
            parts.append(text(x + w - 4, y + 18, f"P{port}", 16, anchor="end"))
            parts.append(text(x + 4, y + h - 6, f"{x},{y}  {w}x{h}" + ("  (half)" if half else ""), 13, fill="#cccccc"))
        else:
            for my in range(y, y + h, MODULE_H):
                for mx in range(x, x + w, MODULE_W):
                    mr = (my - cy) // MODULE_H   # module row inside the full cabinet
                    mc = (mx - cx) // MODULE_W
                    k = ((my // MODULE_H) + (mx // MODULE_W)) % 3
                    parts.append(cell(mx, my, MODULE_W, MODULE_H, BG[k], LINE[k]))
                    parts.append(text(mx + 3, my + 16, cab_id, 14, weight="bold"))
                    parts.append(text(mx + 3, my + 34, f"M{mr * 3 + mc + 1}", 14))
            # cabinet outline on top of modules
            parts.append(f'<rect x="{x + 1}" y="{y + 1}" width="{w - 2}" height="{h - 2}" '
                         f'fill="none" stroke="#ffffff" stroke-width="2"/>')

    # circle over the whole bounding box, clipped to the actual screen shape
    r = min(W, H) / 2
    parts.append(f'<circle cx="{W / 2}" cy="{H / 2}" r="{r - 0.5}" fill="none" '
                 f'stroke="#ffffff" stroke-width="1" clip-path="url(#screen)"/>')

    # data path per port (cabinet cards in order), like the NovaLCT arrows
    if kind == "cabinets":
        centers = {}
        for card, (x, y, w, h) in rects:
            centers.setdefault(card[1], []).append((card[2], x + w / 2, y + h / 2 + 30))
        for port, pts in centers.items():
            pts.sort()
            col = PORT_COLORS.get(port, "#ffffff")
            d = " ".join(f"{'M' if i == 0 else 'L'}{px},{py}" for i, (_, px, py) in enumerate(pts))
            parts.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="3" '
                         f'stroke-opacity="0.8" marker-mid="url(#arr{port})" marker-end="url(#arr{port})"/>')
            _, sx, sy = pts[0]
            parts.append(f'<circle cx="{sx}" cy="{sy}" r="11" fill="{col}"/>')
            parts.append(text(sx, sy + 6, "S", 16, fill="#000000", anchor="middle", weight="bold"))

    markers = "".join(
        f'<marker id="arr{p}" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="5" markerHeight="5" '
        f'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
        for p, c in PORT_COLORS.items())

    title = f"{NAME} - {'Cabinets' if kind == 'cabinets' else 'Modules'} Mapping  {W}x{H}"
    # title sits in the long bottom strip, right of the tall section
    parts.append(text(526, H - 30, title, 22, fill=LABEL_COLOR))

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'shape-rendering="crispEdges">'
            f'<defs><clipPath id="screen">{clip}</clipPath>{markers}</defs>'
            f'<rect width="{W}" height="{H}" fill="#000000"/>'
            + "".join(parts) + "</svg>")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    rects = visible_rects(CARDS)
    W = max(x + w for _, (x, y, w, h) in rects)
    H = max(y + h for _, (x, y, w, h) in rects)
    base = NAME.replace(" ", "_")
    for kind in ("cabinets", "modules"):
        svg = build(kind, rects, W, H)
        svg_path = os.path.join(OUT_DIR, f"{base}_{kind}.svg")
        with open(svg_path, "w") as f:
            f.write(svg)
        cairosvg.svg2png(bytestring=svg.encode(), write_to=svg_path[:-4] + ".png",
                         output_width=W, output_height=H)
        uhd = svg.replace(f'width="{W}" height="{H}" viewBox="0 0 {W} {H}"',
                          f'width="{UHD[0]}" height="{UHD[1]}" viewBox="0 0 {UHD[0]} {UHD[1]}"', 1)
        uhd = uhd.replace(f'<rect width="{W}" height="{H}" fill="#000000"/>',
                          f'<rect width="{UHD[0]}" height="{UHD[1]}" fill="#000000"/>', 1)
        cairosvg.svg2png(bytestring=uhd.encode(),
                         write_to=svg_path[:-4] + f"_{UHD[0]}x{UHD[1]}.png")
        print("wrote", svg_path, f"{W}x{H}")
    for card, r in rects:
        print(f"  {card[1]}-{card[2]}: visible {r}")


if __name__ == "__main__":
    main()
