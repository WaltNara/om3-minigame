"""Event-driven Extras screens, using the same palette as the game launcher."""
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "native"))
from assets_large import FONT, pack_row

GLYPHS = dict(FONT, **{
    "g": ["011", "101", "011", "001", "110"],
    "B": ["110", "101", "110", "101", "110"], "X": ["101", "101", "010", "101", "101"],
    ">": ["100", "010", "001", "010", "100"],
    "a": ["000", "011", "101", "101", "011"], "c": ["000", "011", "100", "100", "011"],
    "d": ["001", "001", "011", "101", "011"], "e": ["000", "010", "101", "110", "011"],
    "h": ["100", "100", "110", "101", "101"], "i": ["010", "000", "010", "010", "010"],
    "k": ["100", "101", "110", "101", "101"], "l": ["110", "010", "010", "010", "011"],
    "m": ["000", "111", "111", "101", "101"], "n": ["000", "110", "101", "101", "101"],
    "o": ["000", "010", "101", "101", "010"], "r": ["000", "101", "110", "100", "100"],
    "s": ["000", "011", "110", "001", "110"], "t": ["010", "111", "010", "010", "011"],
    "u": ["000", "101", "101", "101", "011"], "x": ["000", "101", "010", "010", "101"],
    "y": ["000", "101", "011", "001", "110"], "b": ["100", "100", "110", "101", "110"],
    ".": ["000", "000", "000", "000", "010"],
})


def bitmap(text, scale):
    width = (4 * len(text) - 1) * scale
    result = bytearray(struct.pack("<I", (5*scale-1) | ((width-1) << 12) | (11 << 24)))
    for row in range(5):
        bits = "0".join(GLYPHS[c][row] for c in text)
        pixels = [10 if bit == "1" else 7 for bit in bits for _ in range(scale)]
        result.extend(pack_row(pixels) * scale)
    return result


def write_assets(path):
    pages = {
        "extras_items": [(250, 80, "Extras", 6), (300, 205, "Games", 5), (300, 285, "Shutter sound", 5)],
        "sound_items": [(250, 64, "Shutter sound", 5),
                        *((300, 140 + i*58, label, 5) for i, label in enumerate(
                            ("Silent", "5D", "D850", "Ciallo", "Man"))),
                        (230, 480, "Session only. Playback stays silent.", 3)],
    }
    labels = {(">", 5): "extras_arrow"}
    output = []
    for name, entries in pages.items():
        output.extend((".balign 4", name + ":"))
        for x, y, text, scale in entries:
            label = labels.setdefault((text, scale), f"extras_text_{len(labels)}")
            output.append(f" .long {x},{y},{label}+0x40000000")
        output.append(" .long 0,0,0")
    for (text, scale), label in labels.items():
        data = bitmap(text, scale)
        output.extend((".balign 4", label + ":"))
        for offset in range(0, len(data), 24):
            output.append(" .byte " + ",".join(map(str, data[offset:offset+24])))
    path.write_text("\n".join(output) + "\n", encoding="ascii")
