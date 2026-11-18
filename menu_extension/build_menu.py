"""Build the E147 full-menu candidate in its own directory from verified inputs."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from extras_assets import write_assets


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
OUT = WORK / "menu-extension" / "games"
TC = WORK / "toolchain"
BASE, START = 0x60021020, 0x60F59800
MODE = 0x7E01


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked(path, digest):
    data = path.read_bytes()
    if sha(data) != digest:
        raise ValueError(f"Unexpected input hash for {path}")
    return data


def build():
    accepted = WORK / "current-games"
    base = checked(WORK / "native-build/base-main.bin",
                   "22d6ab711acb495f365c89a3e3f6b155c285c98fb4203097145995a65a5815b6")
    image = bytearray(base)
    # Include only the linked game code and assets. Starting from Caduceus
    # preserves its Picture Mode list, row switches, strings and key handler.
    game = checked(accepted / "row.bin",
                   "36d2053eda76a3a3f6ecd2baffda56a0507faa7ce7ca9482c4e000ea399c37bb")
    old_build = json.loads((accepted / "build.json").read_text())
    old = old_build["symbols"]
    if sha(json.dumps(old, sort_keys=True, separators=(",", ":")).encode()) != (
            "1e8dbee6249c3d93ae02aa721100d42243fc2134ef1a090cab9af61ca3d87e65"):
        raise ValueError("Unexpected r5 symbol map")
    position = START

    def allocate(data):
        nonlocal position
        address = position
        position = (position + len(data) + 3) & ~3
        if position > START + 240 * 1024:
            raise ValueError("Extension would use the reserved 16 KiB")
        if any(v != 255 for v in image[address-BASE:position-BASE]):
            raise ValueError(f"Occupied extension space at {address:#x}")
        image[address-BASE:address-BASE+len(data)] = data
        return address

    def replace(address, expected, data):
        offset = address - BASE
        if len(data) != len(expected) or image[offset:offset+len(data)] != expected:
            raise ValueError(f"Unexpected instruction or table at {address:#x}")
        image[offset:offset+len(data)] = data

    def jump(address, expected, target):
        original = bytes.fromhex(expected)
        replace(address, original, b"\xdc" + struct.pack("<i", target-address)
                + b"\xcb" * (len(original)-5))

    allocate(game)
    OUT.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).with_name("menu_host.s")
    obj, elf, binary = [OUT / ("menu-host." + suffix) for suffix in ("o", "elf", "bin")]
    write_assets(OUT / "extras.inc")
    subprocess.run([TC / "gas/as-new.exe", "-I", OUT, "-o", obj, source], check=True)
    native = dict(native_keys_resume=0x612540EE, native_set_variable=0x610CD5C4,
                  native_panel_id=0x6037E8CC, native_panel_prepare=0x61298E18,
                  native_panel_resume=0x61296E95, native_rectangle=0x610F74E6, native_gui_state=0x603713BC)
    required = subprocess.check_output([TC / "binutils/nm-new.exe", "-u", obj], text=True)
    imports = {**old, **native}
    defs = [f"--defsym={name}={imports[name]}" for name in
            (line.split()[-1] for line in required.splitlines())]
    subprocess.run([TC / "ld/ld-new.exe", "-Ttext", hex(position), "-e", "menu_keys",
                    *defs, "-o", elf, obj], check=True)
    subprocess.run([TC / "binutils/objcopy.exe", "-O", "binary", "-j", ".text", elf, binary], check=True)
    allocate(binary.read_bytes())
    symbols = dict(old)
    for line in subprocess.check_output([TC / "binutils/nm-new.exe", elf], text=True).splitlines():
        address, kind, name = line.split()
        if kind.upper() == "T":
            symbols[name] = int(address, 16)

    # Setup tab 7, Information Record (236). Its label, help and cursor order
    # are separate lists. The original three rows and all value lists stay intact.
    record, order = 0x61587E8C, 0x6152960C
    old_keys = (5072, 179, 3356)
    new_lists = []
    for address, title in [(0x6158797C, b"Extras"), (0x61586FEC, b"Games and shutter sound")]:
        rows = base[address-BASE:address-BASE+36]
        if tuple(struct.unpack_from("<I", rows, i)[0] for i in (0, 12, 24)) != old_keys:
            raise ValueError("Unexpected Setup rows")
        text = allocate(title + b"\0")
        new_lists.append(allocate(rows + struct.pack("<IHHI", MODE, 5, 0, text)))
    replace(record, struct.pack("<3I", 3, 0x6158797C, 0x61586FEC),
            struct.pack("<3I", 4, *new_lists))
    new_order = allocate(struct.pack("<4H", *old_keys, MODE))
    replace(order, struct.pack("<HHI", 0, 3, 0x615294CA), struct.pack("<HHI", 0, 4, new_order))

    jump(0x612540E9, "cff0f8fecc", symbols["menu_keys"])
    jump(0x61296E90, "cd881f0000", symbols["menu_panel"])
    replace(0x611FFC91, bytes.fromhex("dd33d9ecffa010"),
            b"\xdd" + struct.pack("<i", symbols["menu_view"] - 0x611FFC91) + b"\xa0\x10")
    jump(0x610F6016, "dce456e5ffcb", symbols["menu_transition"])
    jump(0x610F48EF, "3cf89304201c", old["games_queue_hook"])
    jump(0x610F7FE9, "ddef7ea2ff0004", symbols["menu_paint"])
    jump(0x60177B7D, "8818dff024", old["games_dial_hook"])
    jump(0x610FD05C, "cde9020004", old["mario_gui_hook"])
    replace(0x615FBD40, struct.pack("<I", 0x61294D13), struct.pack("<I", symbols["menu_touch"]))
    # Games' CALLS handler is now private to ListMenu. An unused game key
    # uses its handled return, never the Picture Mode callback.
    jump(old["pm_stock"] + 2, "dc9315ffff", old["consumed"] + 2)
    jump(old["render_done"], "fca8d4a2f560", old["footer_done"])
    replace(0x60045E9C, struct.pack("<I", START), struct.pack("<I", (position+2047) & ~2047))
    manifest = {"candidate_sha256": sha(image), "base_sha256": sha(base),
                "extension_bytes": position-START, "mode": MODE, "symbols": symbols,
                "host": "list-menu", "custom_game_touch": True, "touch_terminal_kinds": [3, 4, 5],
                "mario_resources": old_build["mario_resources"], "flappy_resources": old_build["flappy_resources"]}
    (OUT / "row-main.bin").write_bytes(image)
    (OUT / "build.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"MENU game candidate {manifest['candidate_sha256']} ({position-START} bytes)")


if __name__ == "__main__":
    build()
