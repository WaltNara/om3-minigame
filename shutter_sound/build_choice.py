"""Build the E147 Extras sound chooser and its two professional previews."""

import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys

from bank import decode, make_wav
from memory import ALIGN, BASE, ROOT, WORK, aligned, sha

sys.path.insert(0, str(ROOT / "menu_extension"))
from extras_assets import bitmap


OUT = WORK / "shutter-sound" / "choice"
SINGLE_OUT = WORK / "shutter-sound" / "single"
BURST_OUT = WORK / "shutter-sound" / "burst"
SD_OUT = WORK / "shutter-sound" / "sd"
MENU = WORK / "menu-extension" / "games"
TC = WORK / "toolchain"
WAV_START = 0x6031F000
WAV_END = WAV_START + 32 * 1024
WAV_LOADER_END = 0x60045E84
CODE_LOADER_END = 0x60045E9C
CODE_START = 0x60F59800
SD_BUFFER = 0x60326000
SD_MAX_FRAMES = 48000
SD_MAX_BYTES = 112 + SD_MAX_FRAMES * 4


def sd_assets(path, image, menu_symbols):
    # Reuse the existing title and first five label bitmaps.
    rows = menu_symbols["sound_items"] - BASE
    table = [" .balign 4", ".global sd_items", "sd_items:"]
    for index in range(6):
        fields = struct.unpack_from("<III", image, rows + index * 12)
        table.append(" .long " + ",".join(map(str, fields)))
    table.extend([
        " .long 300,430,sd_custom_label+0x40000000",
        " .long 230,480",
        "sd_notice: .long sd_msg_ready+0x40000000",
        " .long 0,0,0",
    ])
    header = make_wav(bytes(4))[:-4]
    if len(header) != 112 or header[104:108] != b"data":
        raise ValueError("Unexpected canonical WAV header")
    for name, data in (
        ("sd_wav_header", header),
        ("sd_custom_label", bitmap("Custom", 5)),
        ("sd_msg_ready", bitmap("SD WAV", 3)),
        ("sd_msg_missing", bitmap("NO WAV", 3)),
        ("sd_msg_bad", bitmap("BAD WAV", 3)),
        ("sd_msg_busy", bitmap("TRY AGAIN", 3)),
    ):
        table.extend([" .balign 4", name + ":"])
        for offset in range(0, len(data), 32):
            table.append(" .byte " + ",".join(map(str, data[offset:offset + 32])))
    path.write_text("\n".join(table) + "\n", encoding="ascii")


def build(out, single, burst=False, sd=False):
    layout = json.loads(Path(__file__).with_name("layout.json").read_text(encoding="utf-8"))
    menu = json.loads((MENU / "build.json").read_text(encoding="utf-8"))
    image = bytearray((MENU / "row-main.bin").read_bytes())
    if sha(image) != layout["extras_main_sha256"] or sha(image) != menu["candidate_sha256"]:
        raise ValueError("Sound chooser requires the pinned Extras trial")
    symbols = menu["symbols"]
    code = CODE_START + menu["extension_bytes"]
    loaded_end = struct.unpack_from("<I", image, CODE_LOADER_END - BASE)[0]
    if code % 4 or loaded_end != CODE_START + aligned(code - CODE_START):
        raise ValueError("Extras code placement changed")
    if image[WAV_START - BASE:WAV_END - BASE].count(255) != WAV_END - WAV_START:
        raise ValueError("The section-1 trial pages are occupied")

    def write_checked(address, original, replacement):
        start = address - BASE
        if len(original) != len(replacement) or image[start:start + len(original)] != original:
            raise ValueError(f"Unexpected bytes at {address:#x}")
        image[start:start + len(original)] = replacement

    def jump(address, original, target):
        expected = bytes.fromhex(original)
        patch = b"\xdc" + struct.pack("<i", target - address)
        write_checked(address, expected, patch + b"\xcb" * (len(expected) - len(patch)))

    imports = {key: symbols[key] for key in ("sound_cursor", "sound_choice", "show_extras", "extra_consumed")}
    imports.update(ui_flag=0x60042FCA, set_flag=0x6004CD21, ui_wait=0x6017B78F,
                   ui_stock_exec=0x6017B861, ui_request=0x6017B9DE,
                   ui_resource_size=0x601D7546, ui_size_resume=0x6017BB25,
                   ui_wave_resume=0x6017BB88)
    bank_dir = WORK / "shutter-sound" / "presets"
    start = WAV_START
    presets = {}
    for label, symbol, filename in (("5D", "wave_5d", "canon5d-burst.BIN"),
                                    ("D850", "wave_d850", "nikond850-burst.BIN")):
        clip = decode((bank_dir / filename).read_bytes())
        wav = clip["wav"]
        end = start + len(wav)
        if end > WAV_END or (start + clip["data_offset"]) % 16:
            raise ValueError(f"Preset {label} exceeds the aligned WAV storage")
        image[start - BASE:end - BASE] = wav
        imports[symbol] = start + 0x40000000
        imports[symbol + "_bytes"] = len(wav)
        presets[label] = dict(wav_sha256=sha(wav), pcm_sha256=sha(clip["pcm"]),
                              frames=clip["frames"], address=imports[symbol], bytes=len(wav))
        start = (end + 15) & -16
    end = aligned(start)
    game_extension_bytes = menu["extension_bytes"]
    if sd:
        # Section 1 contains the embedded WAVs, the chooser code and one
        # working clip. Keep the entire overlay inside the audited erased run.
        code, loaded_end = end, SD_BUFFER
        end = aligned(SD_BUFFER + SD_MAX_BYTES + 1)
        gap_end = BASE + int(layout["candidate_region"]["offset_end"], 0)
        if end > gap_end or image[code - BASE:end - BASE].count(255) != end - code:
            raise ValueError("SD overlay exceeds the erased section-1 run")
    write_checked(WAV_LOADER_END, struct.pack("<I", WAV_START), struct.pack("<I", end))

    out.mkdir(parents=True, exist_ok=True)
    obj, elf, binary = [out / ("choice." + suffix) for suffix in ("o", "elf", "bin")]
    defines = ["--defsym", "SINGLE_SHOT=1"] if single else []
    if burst:
        defines += ["--defsym", "BURST_SHOT=1"]
    if single:
        imports.update(shoot_post_resume=0x60B2AAD3, get_drive=0x603F0111)
    if sd:
        defines += ["--defsym", "SD_CUSTOM=1"]
        imports.update(fopen=0x608D4D22, fread=0x608D4EB7, fclose=0x608D4D2B,
                       extra_redraw=symbols["extra_redraw"], open_sound_resume=symbols["open_sound"]+6,
                       sd_buffer=SD_BUFFER + 0x40000000, wav_limit=SD_MAX_BYTES)
        sd_assets(out / "sd_custom.inc", image, symbols)
    subprocess.run([TC / "gas/as-new.exe", *defines, "-o", obj, Path(__file__).with_name("choice.s")],
                   check=True)
    objects = [obj]
    if sd:
        loader = out / "sd-choice.o"
        subprocess.run([TC / "gas/as-new.exe", "-I", out, "-o", loader,
                        Path(__file__).with_name("sd_choice.s")], check=True)
        objects.append(loader)
    defs = [f"--defsym={name}={address}" for name, address in imports.items()]
    subprocess.run([TC / "ld/ld-new.exe", "-Ttext", hex(code), "-e", "es_save_choice", *defs,
                    "-o", elf, *objects], check=True)
    subprocess.run([TC / "binutils/objcopy.exe", "-O", "binary", "-j", ".text", elf, binary],
                   check=True)
    native = {}
    for line in subprocess.check_output([TC / "binutils/nm-new.exe", "-g", elf], text=True).splitlines():
        value, kind, name = line.split()
        if kind == "T":
            native[name] = int(value, 16)
    blob = binary.read_bytes()
    note = b"" if sd else bitmap("Silent shooting" if burst else "Silent Single" if single else
                                 "OK Plays 5D and D850.", 3)
    footer = (code + len(blob) + 3) & -4
    end_code = footer + len(note)
    if end_code > loaded_end:
        raise ValueError("Sound chooser would expand the game loader")
    write_checked(code, b"\xff" * len(blob), blob)
    if sd:
        old_items = b"\xfc\xdf" + struct.pack("<I", symbols["sound_items"])
        at = image.find(old_items, symbols["menu_paint"] - BASE, symbols["draw_label"] - BASE)
        if at < 0:
            raise ValueError("Unexpected sound table operand")
        write_checked(BASE + at + 2, old_items[2:], struct.pack("<I", native["sd_items"]))
        write_checked(symbols["move_selection"] - 2, b"\x80\x05", b"\x80\x06")
        jump(symbols["open_sound"], "fcaa8233f960", native["es_open_sound"])
    else:
        game_extension_bytes = end_code - CODE_START
        write_checked(footer, b"\xff" * len(note), note)
        footer_record = symbols["sound_items"] + 6 * 12
        if struct.unpack_from("<II", image, footer_record - BASE) != (230, 480):
            raise ValueError("Unexpected sound chooser item layout")
        struct.pack_into("<I", image, footer_record - BASE + 8, footer + 0x40000000)

    jump(symbols["save_sound"], "fcaa8333f960fc8a8233f960cc30ff", native["es_save_choice"])
    write_checked(0x6017B79C, b"\x85\x07", bytes([0x85, 0x1F if single else 0x0F]))
    jump(0x6017B857, "f8e204aa04", native["es_dispatch"])
    jump(0x6017BB1A, "f0678002dd28ba0500e010", native["es_wave"])
    if single:
        jump(0x60B2AACD, "420c872ebc00", native["es_exposure"])
    report = {**menu, "candidate_sha256": sha(image), "extras_sha256": menu["candidate_sha256"],
              "extension_bytes": game_extension_bytes, "symbols": {**symbols, **native},
              "wave_start": WAV_START, "wave_end": end, "presets": presets,
              "single_exposure": single, "burst_exposure": burst, "sd_custom": sd,
              "scope": "SD presets and Silent Single exposure" if sd else
              "Silent Single exposure and menu preview" if single else "Native speaker preview"}
    if sd:
        report.update(sd_buffer=SD_BUFFER + 0x40000000, sd_max_bytes=SD_MAX_BYTES)
    (out / "row-main.bin").write_bytes(image)
    (out / "build.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Built {report['candidate_sha256']} in {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--single", action="store_true")
    modes.add_argument("--burst", action="store_true")
    modes.add_argument("--sd", action="store_true")
    args = parser.parse_args()
    build(SD_OUT if args.sd else BURST_OUT if args.burst else SINGLE_OUT if args.single else OUT,
          args.single or args.burst or args.sd, args.burst, args.sd)
