#!/usr/bin/env python3
"""Write a NovaLCT screen-connection file (.scr) from a layout description.

The layout is a JSON file listing, per sending-card port, the receiving cards in
data order (the first entry is where the cable from the processor enters):

  {
    "output": [3840, 2160],                 # optional, value at 0x3C (see below)
    "ports": {
      "1": [[0, 640, 512, 384], [0, 256, 512, 384], [0, 0, 512, 256]],
      "2": [[512, 640, 512, 384], ...]
    }
  }

Each cabinet is [StartX, StartY, Width, Height]. All ports go on sending card 1
and form one complex screen.

The file is built on screens/Cube.scr as a template: only the screen table, the
output resolution and the checksums are replaced. File layout (see make_grid.load_scr):
  0x04  u16  byte sum of 0x06 .. end of the JSON block
  0x0A  u32  length of 0xB6 .. end of the JSON block
  0x0E  u32  length of the trailing section (after the JSON block)
  0x36  section 1001: u16 id, u16 byte sum of 0x3A..0xB5, payload; u16 W/H at 0x3C
        (NovaLCT stores the dialog's "Screen Area" there; it does not limit the layout)
  0xB6  section 1006: u16 id, u16 byte sum of 0xBA..end of JSON, screens + JSON
  0xD2  u32  length of 0xB6 .. end of the screen blocks (start of the JSON block)
  ...   section 1002: u16 id, u16 byte sum of its payload (per-screen settings)

Usage:
  python3 make_scr.py layouts/Test_2x8.json screens/Test_2x8.scr
"""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "screens", "Cube.scr")


def u16sum(b):
    return sum(b) & 0xFFFF


def build_scr(cabinets, output=None, template=TEMPLATE):
    """cabinets: list of (sending card, port, receiving card, x, y, w, h), 1-based indices."""
    with open(template, "rb") as f:
        t = bytearray(f.read())
    if t[0x13A] != 1:
        raise ValueError("template must contain exactly one screen")
    old_size = struct.unpack_from("<I", t, 0x13B)[0]
    old_end = 0x13F + old_size                       # JSON length field follows the screens
    json_len = struct.unpack_from("<H", t, old_end)[0]
    tail = t[old_end:]                               # JSON block + section 1002, kept as is

    records = b"".join(
        struct.pack("<BBHHHIHH", s - 1, p - 1, rc - 1, x, y, 0, w, h)
        for s, p, rc, x, y, w, h in sorted(cabinets, key=lambda c: c[:3]))
    block = struct.pack("<BBHH", 2, 0, len(cabinets), 0) + records

    d = t[:0x13A] + bytes([1]) + struct.pack("<I", len(block)) + block + tail
    if output:
        struct.pack_into("<HH", d, 0x3C, *output)
    send = 0x13F + len(block)                        # end of screens = JSON length field
    jend = send + 2 + json_len

    struct.pack_into("<I", d, 0xD2, send - 0xB6)            # inside section 1006: before its sum
    struct.pack_into("<H", d, 0x38, u16sum(d[0x3A:0xB6]))   # section 1001
    struct.pack_into("<H", d, 0xB8, u16sum(d[0xBA:jend]))   # section 1006
    struct.pack_into("<I", d, 0x0A, jend - 0xB6)
    struct.pack_into("<I", d, 0x0E, len(d) - jend)
    struct.pack_into("<H", d, 0x04, u16sum(d[0x06:jend]))   # whole file
    return bytes(d)


def check_scr(d):
    """Return a list of problems with the length and checksum fields of a .scr file."""
    n = d[0x13A]
    send = 0x13B + 4 * n + sum(struct.unpack_from(f"<{n}I", d, 0x13B))
    jend = send + 2 + struct.unpack_from("<H", d, send)[0]
    want = {
        "file checksum @0x04": (struct.unpack_from("<H", d, 0x04)[0], u16sum(d[0x06:jend])),
        "length @0x0A": (struct.unpack_from("<I", d, 0x0A)[0], jend - 0xB6),
        "trailer length @0x0E": (struct.unpack_from("<I", d, 0x0E)[0], len(d) - jend),
        "section 1001 checksum": (struct.unpack_from("<H", d, 0x38)[0], u16sum(d[0x3A:0xB6])),
        "section 1006 checksum": (struct.unpack_from("<H", d, 0xB8)[0], u16sum(d[0xBA:jend])),
        "screens length @0xD2": (struct.unpack_from("<I", d, 0xD2)[0], send - 0xB6),
        "section 1002 checksum": (struct.unpack_from("<H", d, jend + 2)[0], u16sum(d[jend + 4:])),
    }
    return [f"{k}: {have} != {exp}" for k, (have, exp) in want.items() if have != exp]


def load_layout(path):
    with open(path) as f:
        spec = json.load(f)
    cabinets = []
    for port, chain in spec["ports"].items():
        for i, (x, y, w, h) in enumerate(chain):
            cabinets.append((1, int(port), i + 1, x, y, w, h))
    return cabinets, spec.get("output")


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__.split("Usage:")[1])
    cabinets, output = load_layout(sys.argv[1])
    data = build_scr(cabinets, output)
    problems = check_scr(data)
    if problems:
        sys.exit("internal error, not writing file:\n  " + "\n  ".join(problems))
    with open(sys.argv[2], "wb") as f:
        f.write(data)
    print(f"wrote {sys.argv[2]}: {len(cabinets)} receiving cards, {len(data)} bytes")


if __name__ == "__main__":
    main()
