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

## Current state

Working generator (`make_grid.py`, `make_scr.py`); last change 2026-10-06 (NovaLCT 1024x2944 sample and comparison). Downloaded to `D:\Work\projects\grid-system` on 2026-10-07; before that it existed only on GitHub.

**Flagged for follow-up:** integrate with the Manuals & LED site pipeline. Older overlapping repos exgrid and led-layout-tool are to be reviewed and archived.

## Milestones

- [ ] Integration plan with manuals pipeline

## Links

- Run: `pip install cairosvg` then `python make_grid.py screens/Showroom_all.scr`
- Related: `projects\manuals-pipeline`
