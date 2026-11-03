# Grid_System — Claude instructions

Workspace rules in `D:\Work\CLAUDE.md` apply. Keep `PROJECT.md` and `CHANGELOG.md` current.

## What this is

Python tool that turns a NovaStar NovaLCT screen file (`.scr`) into exact-size cabinet and module mapping grids (SVG + PNG), and can write a `.scr` back from a simple JSON layout. `README.md` documents the decoded `.scr` format and checksum rules. Its reader and drawing are the canonical source that [[projects/wall-player/PROJECT|Wall Player]] (C# port) and [[projects/led-mapping-reviews/PROJECT|LED mapping reviews]] reuse, and it is slated to feed the [[projects/manuals-pipeline/PROJECT|manuals pipeline]]. See `PROJECT.md`.

## How to run / build

```
pip install cairosvg
python make_grid.py screens/Showroom_all.scr
python make_scr.py layouts/Test_2x8.json screens/Test_2x8.scr
```
`cairosvg` is optional (no Cairo on this PC → SVG only; render PNGs with Edge).

## Rules specific to this project

- The repo is **public**. Customer `.scr` files and their grids go in `local\` (git-ignored) — never commit customer data.
- Labels follow NovaLCT numbering (sending card-port-receiving card, 1-based); keep that convention.
- The drawing is mirrored by `CabinetMap.cs` in [[projects/wall-player/PROJECT|Wall Player]] — when you change colours, labels or spacing, change both together.
- When writing a `.scr` with `make_scr.py`, recompute checksums and verify with `make_grid.py` before loading into NovaLCT.
