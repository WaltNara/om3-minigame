"""Audit E147's load regions and build a raw emulator-only section-1 probe."""

import hashlib
import json
from pathlib import Path
import struct

from bank import decode


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
OUT = WORK / "shutter-sound" / "memory-probe"
BASE = 0x60021020
TABLE = 0x60029B28
END_TABLE = 0x600477B0
ALIGN = 2048


def aligned(size):
    return (size + ALIGN - 1) & -ALIGN


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    layout = json.loads(Path(__file__).with_name("layout.json").read_text(encoding="utf-8"))
    image = bytearray((WORK / "current-games/row-main.bin").read_bytes())
    if sha(image) != layout["r5_main_sha256"]:
        raise ValueError("Memory probe requires the pinned r5 image")

    u32 = lambda address: struct.unpack_from("<I", image, address - BASE)[0]
    sections = []
    for i in range(10):
        dest, flash, flag = struct.unpack_from("<3I", image, TABLE - BASE + i * 12)
        getter = u32(END_TABLE + i * 4)
        end = u32(getter + 2)
        if image[getter - BASE:getter - BASE + 2] != b"\xfc\xcc" or not dest < end:
            raise ValueError(f"Unexpected section {i + 1} loader instruction")
        if end % ALIGN or flash != dest - BASE + 0x50000020:
            raise ValueError(f"Unexpected section {i + 1} NAND mapping")
        sections.append(dict(number=i + 1, dest=dest, flash=flash, flag=flag,
                             end=end, end_word=getter + 2))
    if any(a["end"] > b["dest"] for a, b in zip(sections, sections[1:])):
        raise ValueError("Overlapping load regions in r5 baseline")

    first = sections[0]
    trial_start = first["end"]
    gap_limit = BASE + int(layout["candidate_region"]["offset_end"], 0)
    if trial_start != 0x6031F000 or first["flag"] != 0 or not trial_start < gap_limit < sections[1]["dest"]:
        raise ValueError("Unexpected section-1 gap")
    if image[trial_start - BASE:gap_limit - BASE].count(255) != gap_limit - trial_start:
        raise ValueError("Section-1 gap contains occupied bytes")

    stock_alloc_limit = 0x6002407B
    if image[stock_alloc_limit - BASE:stock_alloc_limit - BASE + 8] != bytes.fromhex("fac84040c50b8002"):
        raise ValueError("Unexpected E147 small-pool allocation limit")

    presets = {}
    preset_dir = WORK / "shutter-sound/presets"
    for label, names in {
        "5D": ("canon5d-single", "canon5d-burst"),
        "D850": ("nikond850-single", "nikond850-burst"),
        "Ciallo": ("ciallo-full",),
        "Man": ("man-full",),
    }.items():
        presets[label] = {}
        for name in names:
            bank = (preset_dir / f"{name}.BIN").read_bytes()
            info = decode(bank)
            presets[label][name] = dict(bank_bytes=len(bank), wav_bytes=len(info["wav"]),
                                        frames=info["frames"])

    # Only one short-lived experiment uses this gap. Use the real 5D WAV
    # to test placement, DMA alignment and byte residency with one payload.
    preview = decode((preset_dir / "canon5d-single.BIN").read_bytes())
    wav = preview["wav"]
    trial_end = trial_start + aligned(len(wav))
    if trial_end != 0x60327000 or trial_end > gap_limit:
        raise ValueError("Section-1 probe exceeds the 32 KiB trial")
    image[trial_start - BASE:trial_start - BASE + len(wav)] = wav
    struct.pack_into("<I", image, first["end_word"] - BASE, trial_end)

    code_start = int(layout["games_region"]["runtime_start"], 0)
    loaded = sections[5]["end"] - code_start
    limit = layout["games_region"]["limit_bytes"]
    reserve = layout["games_region"]["reserve_bytes"]
    bank_sizes = [sum(item["bank_bytes"] for item in family.values()) for family in presets.values()]
    report = {
        "schema": 1, "scope": "Emulator-only loader and playback evidence",
        "sha256": sha(image), "baseline_sha256": layout["r5_main_sha256"],
        "main_runtime_base": BASE, "sections_before_probe": sections,
        "games_loaded_bytes": loaded, "games_tested_limit_bytes": limit,
        "games_reserved_bytes": reserve, "games_loadable_before_reserve_bytes": limit - reserve - loaded,
        "erased_beyond_section_1_bytes": gap_limit - trial_start,
        "additional_section_1_load_bytes": trial_end - trial_start,
        "stock_malloc_max_request_bytes": 16448,
        "all_bank_bytes": sum(bank_sizes), "max_selected_bank_bytes": max(bank_sizes),
        "trial_start": trial_start, "trial_end": trial_end,
        "wav_bytes": len(wav), "wav_sha256": sha(wav), "data_offset": preview["data_offset"],
        "presets": presets,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "main.bin").write_bytes(image)
    (OUT / "memory.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Built {trial_end-trial_start} byte section-1 probe for OM-Emu in {OUT}")


if __name__ == "__main__":
    main()
