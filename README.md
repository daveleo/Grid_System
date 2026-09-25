# Grid_System

Showroom LED mapping grids generated from the NovaLCT receiving-card table.

    pip install cairosvg
    python3 make_grid.py

Edit `CARDS` / `MODULE_W` / `MODULE_H` in `make_grid.py` for another screen.
Outputs land in `output/` (exact-size SVG + PNG, and a PNG placed at 0,0 on a 3840x2160 canvas).

NovaLCT gives each cabinet its full size (261x348); where cabinets overlap, the one
with the smaller StartY wins (as drawn in NovaLCT), so the "half" cabinets 1-1-3 and
1-1-4 show only their uncovered 261x174 part (y 348-522).
