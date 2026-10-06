# Grid_System

Showroom LED mapping grids (cabinet + module maps) generated from NovaLCT data.

    pip install cairosvg
    python3 make_grid.py screens/Showroom_all.scr
    python3 make_grid.py screens/Cube.scr --names "Showroom LED" --module 87x174

Without a file argument the built-in `CARDS` table in `make_grid.py` is used.
Screen names and module sizes default from the `PRODUCTS` table (keyed by cabinet
size); override with `--names "A,B,..."` and `--module WxH`.

Outputs land in `output/`: per screen, exact-size cabinet and module maps (SVG + PNG);
for multi-screen files also an overview with every screen at its sending-card position,
plus a PNG padded to the sending card's output resolution.

## NovaLCT .scr format (as far as decoded)

| Offset | Type | Meaning |
|---|---|---|
| 0x00 | 4 bytes | `DSCI` magic |
| 0x3C | u16 LE ×2 | "Screen Area" width, height from the dialog (not enforced) |
| 0x13A | u8 + N×u32 | screen count N, then the byte size of each screen block |
| … | blocks | screen blocks back to back, then u16 length + JSON (per-screen corner points) |

Standard screen block (type `01`): u8 type, u8 ?, u16 X, u16 Y, u16 cols, u16 rows, u8 ?,
then cols×rows 17-byte records (u8 port, u16 receiving card, u16 StartX, u16 StartY,
u16 col, u16 row, u16 Width, u16 Height, u16 ?), then a 14-byte trailer.

Complex screen block (type `02`): u8 type, u8 ?, u16 count, u16 ?, then count 16-byte
records (u8 sending card, u8 port, u16 receiving card, u16 StartX, u16 StartY, 4 bytes ?,
u16 Width, u16 Height).

Indices in the file are 0-based; the grids show them 1-based like NovaLCT
(sending card-port-receiving card). Decoded from two samples with one sending card;
multiple sending cards and rotation are not confirmed yet.

## Overlapping cabinets

NovaLCT gives each cabinet its full size (261x348); where cabinets overlap, the one
with the smaller StartY wins (as drawn in NovaLCT), so the "half" cabinets 1-1-3 and
1-1-4 show only their uncovered 261x174 part (y 348-522).

## Writing .scr files

`make_scr.py` goes the other way: it writes a NovaLCT `.scr` from a JSON layout
listing each port's receiving cards in data order (`[StartX, StartY, Width, Height]`,
first entry = where the cable from the processor enters):

    python3 make_scr.py layouts/Test_2x8.json screens/Test_2x8.scr
    python3 make_grid.py screens/Test_2x8.scr --names "Test 2x8"   # check it visually

The writer uses `screens/Cube.scr` as a template (one complex screen on sending card 1),
replaces the screen table and recomputes the checksums: the u16 at 0x04 is the byte sum
of 0x06 to the end of the JSON block, and sections 1001/1006/1002 each carry a u16 byte
sum of their payload. Rebuilding Cube.scr from its own data gives a byte-identical file,
and the 2x8 test layout with `"output": [2304, 1536]` is byte-identical to
`screens/Working_2x8.scr`, the same screen built by hand in NovaLCT.
