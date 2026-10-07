---
name: Grid_System
status: follow-up
priority:
version:
deadline:
next: Plan how it feeds the Manuals & LED site pipeline (shared data format with site.json)
updated: 2026-10-07
repo: daveleo/Grid_System
url:
---

# Grid_System

Generates showroom LED mapping grids (cabinet and module maps) from NovaLCT screen data (`.scr`).

## What it is for

Turns a NovaStar NovaLCT screen file (`.scr`) into mapping grids for an LED installation: exact-size cabinet maps and module maps (SVG and PNG) showing each cabinet's sending card, port and receiving card, plus an overview padded to the processor's output resolution. It can also go the other way and write a `.scr` from a simple JSON layout. Used for showroom screens and installation documentation.

## How to run

```
pip install cairosvg
python make_grid.py screens/Showroom_all.scr
python make_grid.py screens/Cube.scr --names "Showroom LED" --module 87x174
python make_scr.py layouts/Test_2x8.json screens/Test_2x8.scr
```

Without a file argument, `make_grid.py` uses its built-in `CARDS` table.

## How to use

1. In NovaLCT, save the screen configuration as `.scr` and put it in `screens\`.
2. Run `make_grid.py` on it. Screen names and module sizes come from the `PRODUCTS` table (keyed by cabinet size); override them with `--names "A,B,..."` and `--module WxH`.
3. Collect the results from `output\`: per screen `<name>_cabinets` and `<name>_modules` (SVG + PNG), and for multi-screen files an overview plus a PNG at the sending card's output resolution.
4. To design a layout without NovaLCT, write a JSON listing each port's receiving cards in data order (see `layouts\Test_2x8.json`), run `make_scr.py`, then check it with `make_grid.py` before loading it into NovaLCT.

Labels follow NovaLCT numbering: sending card-port-receiving card, 1-based.

## What is what

- `make_grid.py`: reads `.scr`, draws cabinet and module grids.
- `make_scr.py`: writes a `.scr` from JSON (uses `screens\Cube.scr` as template and recomputes the checksums).
- `screens\`: NovaLCT screen files (showroom, Cube, test layouts, samples).
- `layouts\`: JSON layouts for `make_scr.py`.
- `output\`: generated grids.
- `README.md`: the decoded `.scr` file format, overlapping cabinets, checksum rules.

## Current state

Working generator (`make_grid.py`, `make_scr.py`); last change 2026-10-06 (NovaLCT 1024x2944 sample and comparison). Downloaded to `D:\Work\projects\grid-system` on 2026-10-07; before that it existed only on GitHub.

**Flagged for follow-up:** integrate with the Manuals & LED site pipeline. Older overlapping repos exgrid and led-layout-tool are to be reviewed and archived.

## Milestones

- [ ] Integration plan with manuals pipeline

## Links

- Run: `pip install cairosvg` then `python make_grid.py screens/Showroom_all.scr`
- Related: `projects\manuals-pipeline`
