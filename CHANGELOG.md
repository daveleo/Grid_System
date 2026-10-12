# Changelog

Newest first.

## 2026-10-12

- `make_grid.py`: standard-screen blocks read as a 10-byte header plus 17-byte records that start with the sending card; no trailer assumed. The old reading ran off the end of the block on files without the 15-byte tail (a customer file with a 6x9 standard screen). Same cabinets as before for every sample in `screens/`.
- Overview drawn per sending card when screens use more than one (each card has its own input); padded overview also written as SVG.
- Small cabinets (under 100 px) show only their ID, with the data path below it and no title; strips under 10 px tall are solid colour bars with no text. Output for the existing samples is unchanged.
- `cairosvg` optional: without the Cairo library only SVGs are written. `--out DIR` option.
- `local/` git-ignored for customer files (the repo is public).

## 2026-10-07

- PROJECT.md: added What it is for, How to run, How to use and What is what (shown on the workspace dashboard).
- Downloaded to D:\Work\projects\grid-system; added PROJECT.md.
