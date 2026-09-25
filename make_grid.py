#!/usr/bin/env python3
"""Generate showroom cabinet / module mapping grids from NovaLCT screen-connection data.

NovaLCT lists every receiving card with its full cabinet size (StartX, StartY,
Width, Height). Cabinets can overlap: a "half" cabinet is configured with the
full cabinet size but part of it is covered by the cabinet above it. As in the
NovaLCT canvas, the cabinet with the smaller StartY wins the overlap, so only
the uncovered part of the lower cabinet is drawn.

Outputs (in ./output):
  <prefix>_cabinets.svg / .png   - per screen, exact screen raster, one cell per cabinet
  <prefix>_modules.svg  / .png   - per screen, exact screen raster, one cell per module
  <file>_overview_*.svg / .png   - all screens at their sending-card position (multi-screen files)
  <file>_*_<W>x<H>.png           - same, on the sending card's output resolution

Usage:
  python3 make_grid.py                          # built-in CARDS table below
  python3 make_grid.py screens/Showroom_all.scr # NovaLCT screen-connection file
  python3 make_grid.py screens/Cube.scr --names "Cube" --module 87x174
"""
import argparse
import os
import struct

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

# Showroom products by cabinet size: name and module size (from the Pixl Grid setup).
# Used for titles and module grids when nothing is given on the command line.
PRODUCTS = {
    (261, 348): ("Cube", (87, 174)),
    (192, 192): ("Curved 2.6mm", (96, 48)),
    (640, 360): ("Ultra 0.9mm", (160, 180)),
    (480, 270): ("1.25mm", (120, 135)),
    (384, 216): ("1.5mm", (96, 108)),
    (320, 180): ("1.9mm", (80, 90)),
    (240, 135): ("2.5mm", (60, 135)),
}

BG = ["#400000", "#004000", "#000040"]      # 25% R / G / B
LINE = ["#ff00ff", "#00ffff", "#ffff00"]    # magenta / cyan / yellow
PORT_COLORS = ["#00ff00", "#ffff00", "#00ffff", "#ff00ff", "#ff8000", "#ffffff"]
FONT = "Arial, 'Liberation Sans', Helvetica, sans-serif"
LABEL_COLOR = "#e6b800"
UHD = (3840, 2160)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def load_scr(path):
    """Read a NovaLCT screen-connection file (.scr, "DSCI" header).

    Layout reverse-engineered from sample files (one sending card):
      0x3C   u16 LE x2   sending card output width, height
      0x13A  u8          number of screens N, then N x u32 LE screen block sizes,
                         then the screen blocks back to back
      Standard screen block (type 1):
        u8 1, u8 ?, u16 X, u16 Y, u16 cols, u16 rows, u8 ?,
        cols*rows x 17-byte records:
          u8 port, u16 receiving card (0-based), u16 StartX, u16 StartY,
          u16 col, u16 row, u16 Width, u16 Height, u16 ? (1)
        then a 14-byte trailer
      Complex screen block (type 2):
        u8 2, u8 ?, u16 count, u16 ?,
        count x 16-byte records:
          u8 sending card, u8 port, u16 receiving card (all 0-based),
          u16 StartX, u16 StartY, 4 bytes ?, u16 Width, u16 Height
    Returns (screens, (out_w, out_h)); each screen is a list of cabinet tuples
    (sending card, port, receiving card, x, y, w, h) with 1-based indices like NovaLCT.
    """
    with open(path, "rb") as f:
        d = f.read()
    if d[:4] != b"DSCI":
        raise ValueError(f"{path}: not a NovaLCT .scr file (missing DSCI header)")
    out = struct.unpack_from("<HH", d, 0x3C)
    n = d[0x13A]
    sizes = struct.unpack_from(f"<{n}I", d, 0x13B)
    off = 0x13B + 4 * n
    screens = []
    for size in sizes:
        b = d[off:off + size]
        cabinets = []
        if b[0] == 1:
            _, _, _, cols, rows, _ = struct.unpack_from("<BHHHHB", b, 1)
            for i in range(cols * rows):
                p, rc, x, y, _col, _row, w, h, _ = struct.unpack_from("<BHHHHHHHH", b, 11 + i * 17)
                cabinets.append((1, p + 1, rc + 1, x, y, w, h))
        elif b[0] == 2:
            count = struct.unpack_from("<H", b, 2)[0]
            for i in range(count):
                s, p, rc, x, y, _, w, h = struct.unpack_from("<BBHHHIHH", b, 6 + i * 16)
                cabinets.append((s + 1, p + 1, rc + 1, x, y, w, h))
        else:
            raise ValueError(f"{path}: unknown screen type {b[0]} at offset {off:#x}")
        screens.append(cabinets)
        off += size
    return screens, out


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


def bbox(rects):
    x0 = min(x for _, (x, y, w, h) in rects)
    y0 = min(y for _, (x, y, w, h) in rects)
    x1 = max(x + w for _, (x, y, w, h) in rects)
    y1 = max(y + h for _, (x, y, w, h) in rects)
    return x0, y0, x1, y1


def cell(x, y, w, h, bg, line):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{bg}"/>'
            f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{w - 1}" height="{h - 1}" '
            f'fill="none" stroke="{line}" stroke-width="1"/>')


def text(x, y, s, size, fill="#ffffff", anchor="start", weight="normal"):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size:.0f}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{s}</text>')


def port_color(port):
    return PORT_COLORS[(port - 1) % len(PORT_COLORS)]


def draw_screen(kind, screen, idx):
    """SVG elements for one screen, in sending-card (absolute) coordinates."""
    rects, name, (mod_w, mod_h) = screen["rects"], screen["name"], screen["module"]
    X0, Y0, X1, Y1 = bbox(rects)
    parts = []
    clip = "".join(f'<rect x="{x}" y="{y}" width="{w}" height="{h}"/>' for _, (x, y, w, h) in rects)
    parts.append(f'<clipPath id="screen{idx}">{clip}</clipPath>')

    tops = sorted({r[1] for _, r in rects})
    lefts = sorted({r[0] for _, r in rects})
    for card, (x, y, w, h) in rects:
        s, port, rc, cx, cy, cw, ch = card
        cab_id = f"{s}-{port}-{rc}"
        row, col = tops.index(y), lefts.index(x)
        half = h < ch
        unit = min(w, ch)  # font scale from the full cabinet size
        if kind == "cabinets":
            k = (row + col) % 3
            parts.append(cell(x, y, w, h, BG[k], LINE[k]))
            big = min(unit * 0.2, 44, w / len(cab_id) * 1.6)
            small = max(10, min(16, unit * 0.085))
            parts.append(text(x + w / 2, y + h / 2 + big * 0.35, cab_id, big, anchor="middle", weight="bold"))
            parts.append(text(x + 4, y + small + 2, f"R{row + 1} C{col + 1}", small))
            parts.append(text(x + w - 4, y + small + 2, f"P{port}", small, anchor="end"))
            parts.append(text(x + 4, y + h - 5, f"{x - X0},{y - Y0}  {w}x{h}" + ("  (half)" if half else ""),
                              max(9, small * 0.8), fill="#cccccc"))
        else:
            per_row = max(1, cw // mod_w)
            fs = max(9, min(15, mod_w / 6, mod_h / 3))
            for my in range(y, y + h, mod_h):
                for mx in range(x, x + w, mod_w):
                    mr, mc = (my - cy) // mod_h, (mx - cx) // mod_w
                    k = ((my - Y0) // mod_h + (mx - X0) // mod_w) % 3
                    mw, mh = min(mod_w, x + w - mx), min(mod_h, y + h - my)
                    parts.append(cell(mx, my, mw, mh, BG[k], LINE[k]))
                    if mh >= fs * 2.4:
                        parts.append(text(mx + 3, my + fs + 1, cab_id, fs, weight="bold"))
                        parts.append(text(mx + 3, my + fs * 2.2 + 1, f"M{mr * per_row + mc + 1}", fs))
                    else:
                        parts.append(text(mx + 3, my + fs + 1, f"{cab_id} M{mr * per_row + mc + 1}", fs))
            parts.append(f'<rect x="{x + 1}" y="{y + 1}" width="{w - 2}" height="{h - 2}" '
                         f'fill="none" stroke="#ffffff" stroke-width="2"/>')

    # circle inscribed in the screen's bounding box, clipped to the actual screen shape
    W, H = X1 - X0, Y1 - Y0
    parts.append(f'<circle cx="{X0 + W / 2}" cy="{Y0 + H / 2}" r="{min(W, H) / 2 - 0.5}" fill="none" '
                 f'stroke="#ffffff" stroke-width="1" clip-path="url(#screen{idx})"/>')

    # data path per port (receiving cards in order), like the NovaLCT arrows
    if kind == "cabinets":
        chains = {}
        for card, (x, y, w, h) in rects:
            unit = min(w, card[6])
            chains.setdefault((card[0], card[1]), []).append((card[2], x + w / 2, y + h / 2 + unit * 0.09))
        for (_, port), pts in chains.items():
            pts.sort()
            col = port_color(port)
            mid = f"arr{(port - 1) % len(PORT_COLORS)}"
            d = " ".join(f"{'M' if i == 0 else 'L'}{px},{py}" for i, (_, px, py) in enumerate(pts))
            parts.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="3" '
                         f'stroke-opacity="0.8" marker-mid="url(#{mid})" marker-end="url(#{mid})"/>')
            _, sx, sy = pts[0]
            parts.append(f'<circle cx="{sx}" cy="{sy}" r="9" fill="{col}"/>')
            parts.append(text(sx, sy + 5, "S", 13, fill="#000000", anchor="middle", weight="bold"))

    title = f"{name} - {'Cabinets' if kind == 'cabinets' else 'Modules'} Mapping  {W}x{H}"
    fs = max(12, min(22, W / len(title) * 1.7))
    tx = min(x for _, (x, y, w, h) in rects if y + h == Y1)
    ty = Y1 - max(18, fs + 8)
    parts.append(f'<rect x="{tx + 2}" y="{ty - fs}" width="{len(title) * fs * 0.56 + 6:.0f}" '
                 f'height="{fs * 1.3:.0f}" fill="#000000" fill-opacity="0.75"/>')
    parts.append(text(tx + 4, ty, title, fs, fill=LABEL_COLOR))
    return parts


def svg_doc(parts, x0, y0, W, H):
    markers = "".join(
        f'<marker id="arr{i}" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="5" markerHeight="5" '
        f'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
        for i, c in enumerate(PORT_COLORS))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="{x0} {y0} {W} {H}" '
            f'shape-rendering="crispEdges"><defs>{markers}</defs>'
            f'<rect x="{x0}" y="{y0}" width="{W}" height="{H}" fill="#000000"/>'
            + "".join(parts) + "</svg>")


def write(svg, path, W, H):
    with open(path + ".svg", "w") as f:
        f.write(svg)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=path + ".png", output_width=W, output_height=H)
    print(f"wrote {path}.svg/.png  {W}x{H}")


def safe(s):
    return "".join(ch if ch.isalnum() or ch in ".-" else "_" for ch in s)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("scr", nargs="?", help="NovaLCT .scr file (default: built-in CARDS)")
    ap.add_argument("--names", help="comma-separated screen names, in file order")
    ap.add_argument("--module", help="module size WxH in pixels for all screens "
                                     "(default: from PRODUCTS by cabinet size)")
    args = ap.parse_args()

    if args.scr:
        raw, out = load_scr(args.scr)
        base = os.path.splitext(os.path.basename(args.scr))[0]
    else:
        raw, out, base = [CARDS], UHD, NAME
    names = [n.strip() for n in args.names.split(",")] if args.names else []

    os.makedirs(OUT_DIR, exist_ok=True)
    screens = []
    for i, cards in enumerate(raw):
        size = (cards[0][5], cards[0][6])
        product, module = PRODUCTS.get(size, (None, size))
        if args.module:
            module = tuple(int(v) for v in args.module.lower().split("x"))
        if i < len(names):
            name = names[i]
        elif len(raw) == 1:
            name = base
        else:
            name = f"S{i + 1} {product or f'{size[0]}x{size[1]}'}"
        rects = visible_rects(cards)
        screens.append({"name": name, "rects": rects, "module": module})
        x0, y0, x1, y1 = bbox(rects)
        print(f"screen {i + 1}: {name}  at {x0},{y0}  {x1 - x0}x{y1 - y0}  "
              f"{len(cards)} cabinets {size[0]}x{size[1]}  modules {module[0]}x{module[1]}")

    for i, sc in enumerate(screens):
        x0, y0, x1, y1 = bbox(sc["rects"])
        prefix = safe(base) if len(screens) == 1 else f"{safe(base)}_{safe(sc['name'])}"
        for kind in ("cabinets", "modules"):
            write(svg_doc(draw_screen(kind, sc, i), x0, y0, x1 - x0, y1 - y0),
                  os.path.join(OUT_DIR, f"{prefix}_{kind}"), x1 - x0, y1 - y0)

    # all screens at their position on the sending card output
    _, _, x1, y1 = bbox([r for sc in screens for r in sc["rects"]])
    if x1 > out[0] or y1 > out[1]:
        print(f"note: screens reach {x1}x{y1}, beyond the sending card output {out[0]}x{out[1]}")
    for kind in ("cabinets", "modules"):
        parts = [p for i, sc in enumerate(screens) for p in draw_screen(kind, sc, i)]
        name = f"{safe(base)}_overview_{kind}" if len(screens) > 1 else f"{safe(base)}_{kind}"
        if len(screens) > 1:
            write(svg_doc(parts, 0, 0, x1, y1), os.path.join(OUT_DIR, name), x1, y1)
        W, H = max(out[0], x1), max(out[1], y1)
        cairosvg.svg2png(bytestring=svg_doc(parts, 0, 0, W, H).encode(), output_width=W, output_height=H,
                         write_to=os.path.join(OUT_DIR, f"{name}_{W}x{H}.png"))


if __name__ == "__main__":
    main()
