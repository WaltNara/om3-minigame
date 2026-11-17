"""Native CPU checks for the Minesweeper rules against an independent model.

NCALL cases share one firmware image, so state persists between calls. A few
cases inject a near-win or near-loss board directly to reach the end states
without replaying dozens of cursor moves.
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[1] / "native"), str(_Path(__file__).resolve().parents[1] / "tests")]
import json, os, struct, subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[1]
O = R / 'work/mines-core'
B = R / 'work/native-build'
T = R / 'work/toolchain'
O.mkdir(parents=True, exist_ok=True)


def run(args, **kw):
    return subprocess.run(args, check=True, **kw)


MASK = 0xffffffff


def xorshift(x):
    x ^= (x << 13) & MASK
    x &= MASK
    x ^= x >> 17
    x &= MASK
    x ^= (x << 5) & MASK
    return x & MASK


def i32(x):
    x &= MASK
    return x - 0x100000000 if x >= 0x80000000 else x


def neighbours():
    out = []
    for i in range(64):
        row, col = divmod(i, 8)
        ns = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = row + dr, col + dc
                ns.append(rr * 8 + cc if 0 <= rr < 8 and 0 <= cc < 8 else 255)
        out.append(ns)
    return out


NB = neighbours()


class Model:
    def __init__(self):
        # The initial state matches the assembled data segment. The first
        # replayed call is mines_reset, which advances the RNG once.
        self.rng = 0x6d2b79f5
        self.board = [0] * 64
        self.cursor = 0
        self.flags = 0
        self.revealed = 0
        self.flag_count = 0
        self.boom = -1
        self.moves = 0

    def random(self):
        self.rng = xorshift(self.rng)
        return self.rng

    def reset(self):
        self.board = [0] * 64
        self.cursor = 0
        self.flags = 0
        self.revealed = 0
        self.flag_count = 0
        self.boom = -1
        self.moves = 0
        self.random()

    def move(self, d):
        row, col = divmod(self.cursor, 8)
        if d == 0:
            row = (row - 1) & 7
        elif d == 1:
            row = (row + 1) & 7
        elif d == 2:
            col = (col - 1) & 7
        elif d == 3:
            col = (col + 1) & 7
        else:
            return 0
        new = row * 8 + col
        if new == self.cursor:
            return 0
        self.cursor = new
        self.moves += 1
        return 1

    def flag(self):
        if self.flags & 6:
            return 0
        b = self.board[self.cursor]
        if b & 0x40:
            return 0
        if b & 0x20:
            self.board[self.cursor] = b & 0xdf
            self.flag_count -= 1
        else:
            self.board[self.cursor] = b | 0x20
            self.flag_count += 1
        return 1

    def place(self, safe):
        keep = {safe} | {n for n in NB[safe] if n != 255}
        mines = []
        tries = 0
        while len(mines) < 10 and tries < 256:
            tries += 1
            idx = self.random() & 63
            if idx in keep or idx in mines:
                continue
            mines.append(idx)
        for i in mines:
            self.board[i] |= 0x80
        for i in range(64):
            if self.board[i] & 0x80:
                continue
            count = sum(1 for n in NB[i] if n != 255 and self.board[n] & 0x80)
            self.board[i] |= count

    def reveal(self, i):
        self.board[i] |= 0x40
        self.revealed += 1

    def open(self):
        if self.flags & 6:
            return 0
        if not (self.flags & 1):
            self.place(self.cursor)
            self.flags |= 1
        i = self.cursor
        b = self.board[i]
        if b & 0x60:
            return 0
        if b & 0x80:
            self.flags |= 4
            self.boom = i
            for k in range(64):
                if self.board[k] & 0x80:
                    self.board[k] |= 0x40
            return 1
        self.reveal(i)
        queue = [i]
        head = 0
        while head < len(queue):
            j = queue[head]
            head += 1
            if self.board[j] & 15:
                continue
            for n in NB[j]:
                if n == 255 or self.board[n] & 0xe0:
                    continue
                self.reveal(n)
                if not (self.board[n] & 15):
                    queue.append(n)
        if self.revealed == 54:
            self.flags |= 2
            for k in range(64):
                if self.board[k] & 0x80:
                    self.board[k] |= 0x20
            self.flag_count = 10
        return 1

    def snapshot(self):
        return struct.pack('<64B7i', *self.board, self.cursor, self.flags,
                           self.revealed, self.flag_count, self.boom, i32(self.rng), self.moves)

    def load(self, board, cursor, flags, revealed, flag_count, boom, rng=None, moves=None):
        self.board = list(board)
        self.cursor = cursor
        self.flags = flags
        self.revealed = revealed
        self.flag_count = flag_count
        self.boom = boom
        if rng is not None:
            self.rng = rng
        if moves is not None:
            self.moves = moves


run([str(T / 'gas/as-new.exe'), '-I', str(R / 'work/mines-game'), '-o', str(O / 'core.o'), str(R / 'native/mines_core.s')])
run([str(T / 'gas/as-new.exe'), '-I', str(R / 'work/mines-game'), '-o', str(O / 'render.o'), str(R / 'native/mines_render.s')])
run([str(T / 'ld/ld-new.exe'), '-Ttext', '0x60f59800', '-e', 'mines_reset',
     '-o', str(O / 'core.elf'), str(O / 'core.o'), str(O / 'render.o')])
run([str(T / 'binutils/objcopy.exe'), '-O', 'binary', '-j', '.text', str(O / 'core.elf'), str(O / 'core.bin')])
nm = subprocess.check_output([str(T / 'binutils/nm-new.exe'), str(O / 'core.elf')], text=True)
sy = {s[2]: int(s[0], 16) for line in nm.splitlines() if len(s := line.split()) == 3}
base, start = 0x60021020, 0x60f59800
blob = (O / 'core.bin').read_bytes()
image = bytearray((B / 'base-main.bin').read_bytes())
assert len(blob) < 0x40000 and set(image[start - base:start - base + len(blob)]) == {255}
image[start - base:start - base + len(blob)] = blob
struct.pack_into('<I', image, 0x60045e9c - base, start + ((len(blob) + 0x7ff) // 0x800) * 0x800)
(O / 'main.bin').write_bytes(image)

model = Model()
check_model = Model()
steps = [('mines_reset', 0, None),
         ('mines_move', 3, None), ('mines_move', 3, None), ('mines_move', 3, None),
         ('mines_move', 0, None), ('mines_move', 1, None),
         ('mines_flag', 0, None), ('mines_flag', 0, None),
         ('mines_flag', 0, None), ('mines_open', 0, None),
         ('mines_flag', 0, None), ('mines_open', 0, None),
         ('mines_move', 3, None), ('mines_open', 0, None),
         ('mines_move', 1, None), ('mines_open', 0, None),
         ('mines_move', 3, None), ('mines_flag', 0, None)]
# Replay the same calls in the reference model so it knows the mine layout
# produced by the first opening move before we build the injected endings.
for func, arg, _ in steps:
    if func == 'mines_reset':
        model.reset()
    elif func == 'mines_move':
        model.move(arg)
    elif func == 'mines_flag':
        model.flag()
    elif func == 'mines_open':
        model.open()
spec = []
for i, (func, arg, _) in enumerate(steps):
    spec.append({'name': str(i), 'pc': 'B',
                 'regs': {'d0': arg, 'd2': 0x2222, 'd3': 0x3333, 'a2': 0x4444, 'a3': 0x5555},
                 'mem': [['B', 'dd000000000004cb'], ['B+1', '=' + str(sy[func]) + '-B']],
                 'stop': ['B+7'], 'max': 20000, 'read': [[sy['mines_board'], 92]]})

# Build a near-win board from the model's known mine layout.
safe_cells = [i for i, b in enumerate(model.board) if not (b & 0x80)]
target = safe_cells[0]
win_board = [(b | 0x40) if not (b & 0x80) else (b & 0x9f) for b in model.board]
win_board[target] = model.board[target] & 0x9f
win_state = struct.pack('<64B7i', *win_board, target, 1, 53, 0, -1, i32(model.rng), model.moves)
spec.append({'name': 'near-win-inject', 'pc': 'B', 'regs': {'d0': 0},
             'mem': [['B', 'dd000000000004cb'], ['B+1', '=' + str(sy['mines_open']) + '-B'],
                     [sy['mines_board'], win_state.hex()]],
             'stop': ['B+7'], 'max': 20000, 'read': [[sy['mines_board'], 92]]})
steps.append(('mines_open', 0, 'injected'))

mine_cell = next(i for i, b in enumerate(model.board) if b & 0x80)
loss_board = [b & 0x9f for b in model.board]
loss_state = struct.pack('<64B7i', *loss_board, mine_cell, 1, 0, 10,
                         -1, i32(model.rng), model.moves)
spec.append({'name': 'near-loss-inject', 'pc': 'B', 'regs': {'d0': 0},
             'mem': [['B', 'dd000000000004cb'], ['B+1', '=' + str(sy['mines_open']) + '-B'],
                     [sy['mines_board'], loss_state.hex()]],
             'stop': ['B+7'], 'max': 20000, 'read': [[sy['mines_board'], 92]]})
steps.append(('mines_open', 0, 'injected'))

(O / 'spec.json').write_text(json.dumps(spec))
env = dict(os.environ, OM_EMU_MODEL='E147', NCALL=str(O / 'spec.json'), NOUT=str(O / 'results.json'))
for key in ('GAME_STATE', 'GAME_GC', 'WATCH', 'WSTACK', 'WFROM', 'WIDS'):
    env.pop(key, None)
with (O / 'run.log').open('w') as log:
    run(['node', str(B / 'replay.mjs'), (R / 'work/om-emu/emu').as_uri(), str(O / 'main.bin'),
         str(B / 'paired.omsd'), str(O / 'run.json'), str(O / 'saved.omsd'), 's1 ncall'],
        cwd=R, env=env, stdout=log, stderr=subprocess.STDOUT)
results = json.loads((O / 'results.json').read_text())['out']
assert len(results) == len(spec)
for i, (result, (func, arg, tag)) in enumerate(zip(results, steps)):
    if tag == 'injected':
        continue
    if func == 'mines_reset':
        check_model.reset()
    elif func == 'mines_move':
        check_model.move(arg)
    elif func == 'mines_flag':
        check_model.flag()
    elif func == 'mines_open':
        check_model.open()
    got = bytes.fromhex(result['mem'][0])
    want = check_model.snapshot()
    assert got == want, (i, func, arg, got.hex(), want.hex())
    for reg, value in [('d2', 0x2222), ('d3', 0x3333), ('a2', 0x4444), ('a3', 0x5555)]:
        assert int(result['regs'][reg], 16) == value, (i, reg)
    assert result['steps'] < 20000, (i, result['steps'])
# The two injected endings must resolve to won and lost respectively.
win_model = Model()
win_model.load(win_board, target, 1, 53, 0, -1, model.rng, model.moves)
win_model.open()
assert bytes.fromhex(results[-2]['mem'][0]) == win_model.snapshot(), 'win state mismatch'
assert win_model.flags & 2, 'win flag not set'
loss_model = Model()
loss_model.load(loss_board, mine_cell, 1, 0, 10, -1, model.rng, model.moves)
loss_model.open()
assert bytes.fromhex(results[-1]['mem'][0]) == loss_model.snapshot(), 'loss state mismatch'
assert loss_model.flags & 4, 'loss flag not set'
(O / 'validation.json').write_text(json.dumps({'status': 'passed', 'cases': len(spec),
                                              'checks': ['movement', 'flag toggle', 'first-click safety',
                                                         'mine placement', 'neighbour counts',
                                                         'flood fill', 'win', 'loss']}, indent=2))
print(f'{len(spec)} native Minesweeper rule cases passed')
