"""Build the raw E147 audio copy experiment for OM-Emu."""

import json
from pathlib import Path
import struct
import subprocess

from memory import aligned, BASE, sha, WORK


OUT = WORK / "shutter-sound" / "copy-retrigger"
MENU = WORK / "menu-extension" / "games"
TOOLCHAIN = WORK / "toolchain"
COPY_CALL = 0x60ADC465
STOCK_MEMCPY = 0x50002909
LOAD_END_WORD = 0x60045E9C


def main():
    layout = json.loads(Path(__file__).with_name("layout.json").read_text(encoding="utf-8"))
    image = bytearray((MENU / "row-main.bin").read_bytes())
    menu = json.loads((MENU / "build.json").read_text(encoding="utf-8"))
    if sha(image) != layout["extras_main_sha256"] or sha(image) != menu["candidate_sha256"]:
        raise ValueError("Copy experiment requires the pinned Extras trial")
    region = layout["games_region"]
    start = int(region["runtime_start"], 0)
    address = (start + menu["extension_bytes"] + 3) & ~3
    original_end = struct.unpack_from("<I", image, LOAD_END_WORD - BASE)[0]
    if not start < address < original_end or original_end != start + aligned(address - start):
        raise ValueError("Extension placement inconsistent with Extras loader")
    offset = COPY_CALL - BASE
    original = b"\xdd" + struct.pack("<i", STOCK_MEMCPY - COPY_CALL) + b"\xf0\x1c"
    if image[offset:offset + len(original)] != original:
        raise ValueError("Unexpected stock audio copy call")

    OUT.mkdir(parents=True, exist_ok=True)
    obj, elf, binary = [OUT / f"render.{suffix}" for suffix in ("o", "elf", "bin")]
    source = Path(__file__).with_name("copy_retrigger.s")
    subprocess.run([TOOLCHAIN / "gas/as-new.exe", "-o", obj, source], check=True)
    subprocess.run([TOOLCHAIN / "ld/ld-new.exe", "-Ttext", hex(address), "-e", "render_shutter_pcm",
                    f"--defsym=stock_memcpy={STOCK_MEMCPY}", "-o", elf, obj], check=True)
    subprocess.run([TOOLCHAIN / "binutils/objcopy.exe", "-O", "binary", "-j", ".text", elf, binary],
                   check=True)
    symbols = {}
    for line in subprocess.check_output([TOOLCHAIN / "binutils/nm-new.exe", "-g", elf], text=True).splitlines():
        value, kind, name = line.split()
        if kind == "T":
            symbols[name] = int(value, 16)
    blob = binary.read_bytes()
    end = address + len(blob)
    if end > original_end or image[address - BASE:end - BASE].count(255) != len(blob):
        raise ValueError("Copy experiment exceeds the existing loaded extension pages")
    image[address - BASE:end - BASE] = blob
    image[offset + 1:offset + 5] = struct.pack("<i", symbols["render_shutter_pcm"] - COPY_CALL)
    (OUT / "row-main.bin").write_bytes(image)
    report = {**menu, "schema": 1, "candidate_sha256": sha(image), "extension_bytes": end - start,
              "extras_sha256": menu["candidate_sha256"],
              "render_bytes": len(blob), "runtime_start": address, "load_end": original_end,
              "symbols": {**menu["symbols"], **symbols},
              "scope": "Emulator-only copy renderer with a caller-owned WAV and shot generations"}
    (OUT / "build.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(blob)} byte native renderer in {OUT}")


if __name__ == "__main__":
    main()
