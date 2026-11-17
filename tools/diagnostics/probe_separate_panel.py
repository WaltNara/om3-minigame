"""Non-HSL drawing experiment in OM-Emu; does not produce camera firmware.

Run after native/prepare_emulator.py. Results are isolated from the 2048 build.
The debugger replaces one bitmap call on a Picture Mode row to test whether
that call can place an image there. This is not a launcher or a safe hook.
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[2] / "native"), str(_Path(__file__).resolve().parents[2] / "tests")]
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import zlib

import assets

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / 'work/native-build'
OUT = ROOT / 'work/separate-games'
OUT.mkdir(parents=True, exist_ok=True)

# A static high-contrast image in the format already used by the game.
row_a = assets.pack_row([7] * 16 + [10] * 224 + [7] * 16)
row_b = assets.pack_row([10] * 16 + [7] * 224 + [10] * 16)
image = struct.pack('<I', 0x0b0ff13f) + b''.join(
    row_a if (y // 20) % 2 else row_b for y in range(320))
(OUT / 'panel.bin').write_bytes(image)

source = (BUILD / 'replay.mjs').read_text(encoding='utf-8')
needle = "const dbg = Debugger.attach(lab.sim, { lab });\n  dbg.traceExec((r) => { const g = dbg.regs();"
assert source.count(needle) == 1
injection = """const dbg = Debugger.attach(lab.sim, { lab });
  const panel = lab.alloc(new Uint8Array(fs.readFileSync(process.env.PANEL)), 64);
  let injected = false;
  dbg.traceExec((r) => { const g = dbg.regs();
    if (!injected && curStep === 'down#6' && g.d0 === 0 && g.d1 === 300) {
      dbg.setRegs({d0: 322, d1: 120, a1: panel});
      injected = true;
      console.log('PANEL_INJECTED', panel.toString(16));
    }
"""
script = OUT / 'panel-replay.mjs'
script.write_text(source.replace(needle, injection), encoding='utf-8')
env = dict(os.environ, OM_EMU_MODEL='E147', WATCH='610f784f', PANEL=str(OUT/'panel.bin'))
for name in ('GAME_STATE', 'GAME_GC', 'WSTACK', 'WFROM', 'WIDS'):
    env.pop(name, None)
cmd = ['node', str(script), (ROOT/'work/om-emu/emu').as_uri(), str(BUILD/'base-main.bin'),
       str(BUILD/'paired.omsd'), str(OUT/'panel.json'), str(OUT/'panel-saved.omsd'),
       's1 ok ok down down down shot:work/separate-games/panel.png menu s1']
with (OUT/'panel.log').open('w', encoding='utf-8') as log:
    subprocess.run(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
log = (OUT/'panel.log').read_text(encoding='utf-8')
result = json.loads((OUT/'panel.json').read_text(encoding='utf-8'))
assert log.count('PANEL_INJECTED') == 1, 'Target bitmap call was not reached exactly once'
assert not result['engineErrors'], result['engineErrors']
# The replay writes RGB PNGs with filter 0. Check the alternating bands at a
# point away from other widgets; merely reaching the hook does not prove paint.
png = (OUT/'panel.png').read_bytes()
offset, data = 8, bytearray()
while offset < len(png):
    size = int.from_bytes(png[offset:offset+4], 'big')
    kind = png[offset+4:offset+8]
    if kind == b'IHDR':
        width, height = struct.unpack('>II', png[offset+8:offset+16])
    if kind == b'IDAT':
        data.extend(png[offset+8:offset+8+size])
    offset += size + 12
raw = zlib.decompress(data)
stride = width * 3 + 1
assert (width, height) == (900, 600)
def pixel(x, y):
    assert raw[y * stride] == 0
    return raw[y * stride + 1 + 3*x:y * stride + 4 + 3*x]
assert pixel(400, 130) == pixel(400, 170) != pixel(400, 150), 'Panel bands not visible'
print('Static panel visible on a non-HSL row; inspect work/separate-games/panel.png.')
