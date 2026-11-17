"""Decode the native Minesweeper RLE output inside OM-Emu and compare pixels."""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[1] / "native"), str(_Path(__file__).resolve().parents[1] / "tests")]
import json, os, struct, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mines_assets as art

R = Path(__file__).resolve().parents[1]
O = R / 'work/mines-render'
B = R / 'work/native-build'
T = R / 'work/toolchain'
O.mkdir(parents=True, exist_ok=True)


def run(args, **kw):
    return subprocess.run(args, check=True, **kw)


info = art.make(O / 'mines_assets.inc')
for name in ('mines_core', 'mines_render'):
    run([str(T / 'gas/as-new.exe'), '-I', str(O), '-o', str(O / (name + '.o')), str(R / 'native' / (name + '.s'))])
run([str(T / 'ld/ld-new.exe'), '-Ttext', '0x60f59800', '-e', 'mines_paint',
     '-o', str(O / 'render.elf'), str(O / 'mines_core.o'), str(O / 'mines_render.o')])
run([str(T / 'binutils/objcopy.exe'), '-O', 'binary', '-j', '.text', str(O / 'render.elf'), str(O / 'render.bin')])
nm = subprocess.check_output([str(T / 'binutils/nm-new.exe'), str(O / 'render.elf')], text=True)
sy = {s[2]: int(s[0], 16) for line in nm.splitlines() if len(s := line.split()) == 3}
base, start = 0x60021020, 0x60f59800
blob = (O / 'render.bin').read_bytes()
image = bytearray((B / 'base-main.bin').read_bytes())
assert len(blob) < 0x40000 and set(image[start - base:start - base + len(blob)]) == {255}
image[start - base:start - base + len(blob)] = blob
struct.pack_into('<I', image, 0x60045e9c - base, start + ((len(blob) + 0x7ff) // 0x800) * 0x800)
(O / 'main.bin').write_bytes(image)

BG, FG = art.BG, art.FG
modes, cells, styles = art.y_tables()


def classify(board, flags, cursor, boom, index):
    b = board[index]
    if flags & 4 and b & 0x80:
        return 12 if index == boom else 11
    if b & 0x20:
        return 1
    if not (b & 0x40):
        return 0
    if b & 0x80:
        return 11
    n = b & 15
    return 2 if n == 0 else 2 + n


def hud_text(board, flags, revealed, flag_count, footer):
    if footer:
        if flags & 2:
            return list(art.HUD_WON.ljust(32))
        if flags & 4:
            return list(art.HUD_DEAD.ljust(32))
        return list(art.HUD_PLAY.ljust(32))
    top = list(art.HUD_TOP.ljust(32))
    left = max(0, 10 - flag_count)
    op = min(99, revealed)
    fl = min(99, flag_count)
    for start, value in ((6, left), (15, op), (25, fl)):
        top[start:start + 2] = list(f'{value:02d}')
    return top


def reference(board, flags, cursor, revealed, flag_count, boom):
    lines = []
    for y in range(480):
        mode = modes[y]
        if mode == 1:
            lines.append([BG] * 384)
            continue
        if mode == 2:
            text = hud_text(board, flags, revealed, flag_count, y >= 432)
            style = styles[y]
            line = []
            for ch in text:
                glyph = art.FONT.get(ch, art.FONT[' '])
                line += [BG] + [FG if v == '1' else BG for v in glyph[style] for _ in range(3)] + [BG] * 2
            lines.append(line)
            continue
        row, style = cells[y], styles[y]
        line = []
        for col in range(8):
            index = row * 8 + col
            kind = classify(board, flags, cursor, boom, index)
            line += art.tile_pixels(kind, style, index == cursor)
        lines.append(line)
    return lines


# Three representative frames: untouched board, mid-game, and a loss display.
board0 = [0] * 64
board_mid = [0] * 64
for index, value in {0: 0x41, 1: 0x42, 2: 0x43, 8: 0x40, 9: 0x45, 10: 0x20,
                     17: 0x80, 18: 0x47, 27: 0x80 | 0x20, 33: 0x48}.items():
    board_mid[index] = value
board_lost = [b & 0x9f for b in board_mid]
for index in (17, 27):
    board_lost[index] |= 0x40
cases = [
    ('fresh', board0, 0, 0, 0, 0, -1, 0),
    ('mid', board_mid, 0, 10, 4, 1, -1, 2),
    ('lost', board_lost, 4, 10, 4, 1, 17, 17),
]
spec = []
for i, (name, board, flags, cursor, revealed, flag_count, boom, _) in enumerate(cases):
    state = struct.pack('<64B7i', *board, cursor, flags, revealed, flag_count, boom,
                        0x6d2b79f5, 0)
    spec.append({'name': name, 'pc': 'B',
                 'regs': {'d2': 0x2222, 'd3': 0x3333, 'a2': 0x4444, 'a3': 0x5555},
                 'mem': [['B', 'dd000000000004cb'], ['B+1', '=' + str(sy['mines_paint']) + '-B'],
                         [sy['mines_board'], state.hex()], [sy['mines_buffer_end'], 'dec0ad0b']],
                 'stop': ['B+7'], 'max': 500000,
                 'read': [[sy['mines_buffer'], info['capacity'] + 4], [sy['mines_board'], 92]]})
(O / 'spec.json').write_text(json.dumps(spec))
env = dict(os.environ, OM_EMU_MODEL='E147', NCALL=str(O / 'spec.json'), NOUT=str(O / 'results.json'))
for key in ('GAME_STATE', 'GAME_GC', 'WATCH', 'WSTACK', 'WFROM', 'WIDS'):
    env.pop(key, None)
with (O / 'run.log').open('w') as log:
    run(['node', str(B / 'replay.mjs'), (R / 'work/om-emu/emu').as_uri(), str(O / 'main.bin'),
         str(B / 'paired.omsd'), str(O / 'run.json'), str(O / 'saved.omsd'), 's1 ncall'],
        cwd=R, env=env, stdout=log, stderr=subprocess.STDOUT)
results = json.loads((O / 'results.json').read_text())['out']
assert len(results) == len(cases)
for result, (name, board, flags, cursor, revealed, flag_count, boom, _) in zip(results, cases):
    assert result['steps'] < 500000, (name, result['steps'])
    for reg, value in [('d2', 0x2222), ('d3', 0x3333), ('a2', 0x4444), ('a3', 0x5555)]:
        assert int(result['regs'][reg], 16) == value, (name, reg)
    raw = bytes.fromhex(result['mem'][0])
    after = bytes.fromhex(result['mem'][1])[:64]
    assert list(after) == list(board), name + ': paint modified the board'
    assert raw[-4:] == bytes.fromhex('dec0ad0b'), name + ': buffer overflow'
    assert raw[:4] == struct.pack('<I', 0x0b17f1df), name + ': bad header'
    want = reference(board, flags, cursor, revealed, flag_count, boom)
    off = 4
    for line in range(480):
        pixels = []
        while len(pixels) < 384:
            word = int.from_bytes(raw[off:off + 8], 'little')
            off += 8
            assert word >> 60 == 0, (name, line)
            for i in range(5):
                token = (word >> (12 * i)) & 4095
                pixels.extend([token >> 4] * ((token & 15) + 1))
        assert len(pixels) == 384, (name, line, len(pixels))
        if pixels != want[line]:
            diffs = [(i, pixels[i], want[line][i]) for i in range(384) if pixels[i] != want[line][i]]
            print('MISMATCH', name, 'line', line, 'count', len(diffs), 'first', diffs[:16])
            assert False, (name, line)
    assert off <= info['capacity'], (name, off)
(O / 'validation.json').write_text(json.dumps({'status': 'passed', 'frames': len(cases),
                                               'capacity': info['capacity']}, indent=2))
print(f'{len(cases)} native Minesweeper frames decoded and stayed within the buffer')
