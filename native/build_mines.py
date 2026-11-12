"""Build an isolated 2048 + Minesweeper firmware main block for OM-Emu.

This is a separate emulator-only branch. It does not touch the published
2048 package, the Mario prototype, or any Mario source file. Minesweeper is
event driven, so this build installs no periodic timer and no GUI queue hook.
"""
import json
import hashlib
import os
from pathlib import Path
import struct
import subprocess
import sys
import mines_launcher_assets as launcher_assets
import mines_assets
import assets_large
from test2048 import reference

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'work/mines-game'
BUILD = ROOT / 'work/native-build'
TC = ROOT / 'work/toolchain'
BASE, START = 0x60021020, 0x60f59800
OUT.mkdir(parents=True, exist_ok=True)
image = bytearray((BUILD / 'base-main.bin').read_bytes())
sys.path.insert(0, str(ROOT / 'vendor/caduceus-om3/firmware'))
import patch
spec = json.loads((ROOT / 'vendor/caduceus-om3/releases/v0.26.2/patch.json').read_text())
package = (BUILD / 'caduceus-v0.26.2.bin').read_bytes()
assert patch.sha(package) == spec['result_sha256'], 'Caduceus baseline hash mismatch'
assert bytes(image) == patch.decode(patch.parse(package)[0]['enc']), 'Decoded baseline mismatch'
source_paths = [ROOT / 'native' / name for name in (
    'build_mines.py', 'mines_host.s', 'mines_menu.s', 'mines_launcher_assets.py',
    'mines_core.s', 'mines_render.s', 'mines_assets.py',
    'assets.py', 'assets_large.py', '2048_large.s', 'test2048.py',
    'test_mines_core.py', 'test_mines_render.py', 'test_mines_game.py')]
sources = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}


def u32(a):
    return struct.unpack_from('<I', image, a - BASE)[0]


def put32(a, v):
    struct.pack_into('<I', image, a - BASE, v)


def data(a, n):
    return bytes(image[a - BASE:a - BASE + n])


# Rechain the existing Caduceus string hook; preserve every other string.
site = 0x610f56a6
assert data(site, 1) == b'\xdc'
original = (site + struct.unpack_from('<i', image, site + 1 - BASE)[0]) & 0xffffffff


def previous_jump(a):
    assert data(a, 1) == b'\xdc'
    return (a + struct.unpack_from('<i', image, a + 1 - BASE)[0]) & 0xffffffff


hooks = {'original_update': previous_jump(0x611d04ec), 'original_pm': previous_jump(0x6125becc),
         'original_transition': previous_jump(0x610f6016), 'queue_resume': 0x610f48f5,
         'queue_entry': 0x610f48ef, 'original_end': 0x60b1fed8, 'paint_resume': 0x610f7ff0,
         'bitmap': 0x610f784f, 'invalidate': 0x610deaab}
launcher_assets.make(OUT)
# The published 2048 glyph table has no F or B. Add them for this build only,
# so assets_large.py stays byte-identical to the released 2048 package.
assets_large.FONT.setdefault('F', ['111', '100', '110', '100', '100'])
assets_large.FONT.setdefault('B', ['110', '101', '110', '101', '110'])
board_resources = assets_large.make(OUT / 'assets.inc')
# A held OK is no longer a restart input; INFO starts a new 2048 round.
asset_text = (OUT / 'assets.inc').read_text(encoding='ascii')
for before, after in (('ARROWS MOVE  HOLD OK NEW', 'ARROWS MOVE  INFO NEW'),
                      ('GAME OVER  HOLD OK NEW', 'GAME OVER  INFO NEW GAME')):
    assert asset_text.count(before.ljust(32)) == 1, before
    asset_text = asset_text.replace(before.ljust(32), after.ljust(32))
(OUT / 'assets.inc').write_text(asset_text, encoding='ascii')
resources = mines_assets.make(OUT / 'mines_assets.inc')
resources['board_2048_capacity'] = board_resources['compressed_board_capacity']
source = (ROOT / 'native/2048_large.s').read_text(encoding='utf-8')
old = ''' mov GDESC,a0
 mov d0,(12,a0)
 mov GSELECT,a1
 mov d0,(12,a1)
 mov board_buffer+0x40000000,d0
 mov d0,(16,a0)
 mov d0,(16,a1)
'''
assert source.count(old) == 1
source = source.replace(old, '')
# Remove the leftover 2048 held-OK restart hook as well.
hold = '''game_event:
 cmp 0x903e,d0
 beq restart
 jmp original_event
'''
assert source.count(hold) == 1
source = source.replace(hold, '''game_event:
 jmp original_event
''')
(OUT / '2048-host.s').write_text(source, encoding='utf-8')
(OUT / 'original.inc').write_text((BUILD / 'original.inc').read_text(encoding='utf-8'), encoding='utf-8')
gas = str(TC / 'gas/as-new.exe')
subprocess.run([gas, '-I', str(OUT), '-o', str(OUT / 'row.o'), str(ROOT / 'native/mines_host.s')], check=True, cwd=OUT)
subprocess.run([gas, '-o', str(OUT / 'menu-row.o'), str(ROOT / 'native/mines_menu.s')], check=True)
subprocess.run([gas, '-I', str(OUT), '-o', str(OUT / 'game-host.o'), str(OUT / '2048-host.s')], check=True)
for name in ('mines_core', 'mines_render'):
    subprocess.run([gas, '-I', str(OUT), '-o', str(OUT / (name + '.o')), str(ROOT / 'native' / (name + '.s'))], check=True)
orig = json.loads((BUILD / 'build.json').read_text())['original']
targets = {**{f'original_{k}': v for k, v in orig.items()}, 'facade': 0x60b8696a,
           'original_bitmap_resume': 0x610f7854}
subprocess.run([str(TC / 'ld/ld-new.exe'), '-Ttext', hex(START), '-e', 'games_string',
                f'--defsym=original_string={original}', *[f'--defsym={k}={v}' for k, v in hooks.items()],
                *[f'--defsym={k}={v}' for k, v in targets.items()],
                '-o', str(OUT / 'row.elf'), str(OUT / 'row.o'), str(OUT / 'menu-row.o'),
                str(OUT / 'game-host.o'), str(OUT / 'mines_core.o'), str(OUT / 'mines_render.o')], check=True)
subprocess.run([str(TC / 'binutils/objcopy.exe'), '-O', 'binary', '-j', '.text', str(OUT / 'row.elf'), str(OUT / 'row.bin')], check=True)
blob = (OUT / 'row.bin').read_bytes()
pos = (START + len(blob) + 3) & ~3
nm = subprocess.check_output([str(TC / 'binutils/nm-new.exe'), str(OUT / 'row.elf')], text=True)
sy = {s[2]: int(s[0], 16) for line in nm.splitlines() if len(s := line.split()) == 3}
assert set(data(START, 0x40000)) == {255}
image[START - BASE:START - BASE + len(blob)] = blob
put32(site + 1, (START - site) & 0xffffffff)
for a, name in ((0x611d04ec, 'games_update'), (0x6125becc, 'games_pm'), (0x610f6016, 'games_transition')):
    put32(a + 1, (sy[name] - a) & 0xffffffff)
assert data(0x610f48ef, 6) == bytes.fromhex('3cf89304201c')
image[0x610f48ef - BASE:0x610f48f5 - BASE] = b'\xdc' + struct.pack('<i', sy['games_queue_hook'] - 0x610f48ef) + b'\xcb'
assert data(0x610f7fe9, 7) == bytes.fromhex('ddef7ea2ff0004')
image[0x610f7fe9 - BASE:0x610f7ff0 - BASE] = b'\xdc' + struct.pack('<i', sy['games_render_hook'] - 0x610f7fe9) + b'\xcb\xcb'
assert data(0x60177b7d, 5) == bytes.fromhex('8818dff024')
image[0x60177b7d - BASE:0x60177b82 - BASE] = b'\xdc' + struct.pack('<i', sy['games_dial_hook'] - 0x60177b7d)


def alloc(payload):
    global pos
    addr = pos
    image[addr - BASE:addr - BASE + len(payload)] = payload
    pos = (addr + len(payload) + 3) & ~3
    return addr


old_list = [111, 5397, 8, 5398, 5386, 5385, 5384, 7, 5394, 5389, 5399, 5382, 5400]
assert list(struct.unpack('<13I', data(0x60f49a74, 52))) == old_list
assert u32(0x60f49a63) == 0x60f49a74 and u32(0x60f49a69) == 13
new_list = alloc(struct.pack('<14I', *old_list, 5380))
put32(0x60f49a63, new_list)
put32(0x60f49a69, 14)
# The WB choice row is used solely as a temporary row-structure template.
old_table = u32(0x611d040f)
assert old_table == u32(0x611d0848) == 0x60f49e08
table = bytearray(data(old_table, 25 * 40))
idx = next(i for i in range(25) if struct.unpack_from('<I', table, i * 40)[0] == 5384)
row = bytearray(table[idx * 40:(idx + 1) * 40])
struct.pack_into('<I', row, 0, 5380)
title = alloc(struct.pack('<HHI', 4, 0x7f08, 0x6154b480))
option = alloc(struct.pack('<IHHI', 0, 4, 0x7f08, 0x6154b480))
cell_option = alloc(struct.pack('<IHHI', 0, 4, 0x7f09, 0x6154b480))
struct.pack_into('<I', row, 4, title)
for off in (8, 20, 32):
    struct.pack_into('<I', row, off, option)
struct.pack_into('<I', row, 20, cell_option)
new_table = alloc(table + row)
for a, c in ((0x611d040f, 0x611d0422), (0x611d0848, 0x611d0859)):
    assert u32(a) == old_table and data(c, 2) == b'\xa5\x19'
    put32(a, new_table)
    image[c + 1 - BASE] = 26
# Insert an additional key into each existing open-addressed row switch.
for a in (0x61536a2c, 0x61536b2c, 0x61536c2c, 0x61536d2c, 0x61536f2c,
          0x615510cc, u32(0x611d05ed), 0x6155124c, u32(0x611d1a5b)):
    entries = [struct.unpack('<II', data(a + 8 * i, 8)) for i in range(32)]
    matches = [target for key, target in entries if key == 5384 - 6]
    assert len(matches) == 1 and not any(key == 5380 - 6 for key, target in entries)
    i = (5380 - 6) & 31
    while entries[i][0]:
        i = (i + 1) % 32
    put32(a + 8 * i, 5380 - 6)
    put32(a + 8 * i + 4, matches[0])
assert pos < START + 0x40000
put32(0x60045e9c, START + ((pos - START + 0x7ff) // 0x800) * 0x800)
(OUT / 'row-main.bin').write_bytes(image)
(OUT / 'main.bin').write_bytes(image)
(OUT / 'paired.omsd').write_bytes((BUILD / 'paired.omsd').read_bytes())
(OUT / 'replay.mjs').write_text((BUILD / 'replay.mjs').read_text(encoding='utf-8'), encoding='utf-8')
digest = hashlib.sha256(image).hexdigest()
(OUT / 'build.json').write_text(json.dumps({
    'candidate_sha256': digest, 'symbols': sy, 'resources': resources,
    'source_sha256': sources,
    'status': 'emulator-only 2048 + Minesweeper main block; not an installable package'},
    indent=2), encoding='utf-8')
print('Built emulator-only Minesweeper variant:', len(blob), 'bytes', digest)
