# Grid_System

Showroom LED mapping grids (cabinet + module maps) generated from NovaLCT data.

    pip install cairosvg
    python3 make_grid.py screens/Cube.scr --name "Showroom LED" --module 87x174

Without a file argument the built-in `CARDS` table in `make_grid.py` is used.
Outputs land in `output/`: exact-size SVG + PNG, and a PNG placed at 0,0 on the
sending card's output resolution (read from the .scr; 3840x2160 otherwise).

## NovaLCT .scr format (as far as decoded)

| Offset | Type | Meaning |
|---|---|---|
| 0x00 | 4 bytes | `DSCI` magic |
| 0x3C | u16 LE ×2 | sending card output width, height |
| 0x141 | u8 | receiving card count |
| 0x145 | 16-byte records | u8 sending card, u8 port, u16 receiving card (0-based), u16 StartX, u16 StartY, 4 bytes unknown, u16 Width, u16 Height |

Decoded from one sample (1 screen, 1 sending card, standard cabinets). Rotation,
multiple screens/sending cards and the unknown 4 bytes still need more samples.

## Overlapping cabinets

NovaLCT gives each cabinet its full size (261x348); where cabinets overlap, the one
with the smaller StartY wins (as drawn in NovaLCT), so the "half" cabinets 1-1-3 and
1-1-4 show only their uncovered 261x174 part (y 348-522).
