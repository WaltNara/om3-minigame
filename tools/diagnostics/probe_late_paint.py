"""Build and replay a deliberately one-frame, emulator-only paint probe."""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[2] / "native"), str(_Path(__file__).resolve().parents[2] / "tests")]
import json
import os
from pathlib import Path
import struct
import subprocess
import zlib

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT/'work/native-build'
OUT = ROOT/'work/separate-games'
TOOLS = ROOT/'work/toolchain'
OUT.mkdir(parents=True, exist_ok=True)
assert (OUT/'panel.bin').is_file(), 'Run tools/diagnostics/probe_separate_panel.py first'
base = bytearray((BUILD/'base-main.bin').read_bytes())
BASE, START, SITE = 0x60021020, 0x60f59800, 0x610f7fe9
assert base[SITE-BASE:SITE-BASE+7] == bytes.fromhex('ddef7ea2ff0004')
assert set(base[START-BASE:START-BASE+0x10000]) == {255}
subprocess.run([str(TOOLS/'gas/as-new.exe'), '-I', str(OUT), '-o', str(OUT/'late.o'),
                str(ROOT/'tools/diagnostics/probe_late_paint.s')], check=True, cwd=OUT)
subprocess.run([str(TOOLS/'ld/ld-new.exe'), '-Ttext', hex(START), '-e', 'probe',
                '--defsym=bitmap=0x610f784f', '--defsym=original_end=0x60b1fed8',
                '--defsym=resume=0x610f7ff0', '-o', str(OUT/'late.elf'), str(OUT/'late.o')], check=True)
subprocess.run([str(TOOLS/'binutils/objcopy.exe'), '-O', 'binary', '-j', '.text',
                str(OUT/'late.elf'), str(OUT/'late.bin')], check=True)
symbols = subprocess.check_output([str(TOOLS/'binutils/nm-new.exe'), str(OUT/'late.elf')], text=True)
sy = {s[2]: int(s[0],16) for line in symbols.splitlines() if len(s:=line.split()) == 3}
blob = (OUT/'late.bin').read_bytes()
assert len(blob) < 0x10000 and sy['probe'] == START
base[START-BASE:START-BASE+len(blob)] = blob
base[SITE-BASE:SITE-BASE+7] = b'\xdc'+struct.pack('<i', START-SITE)+b'\xcb\xcb'
struct.pack_into('<I',base,0x60045e9c-BASE,START+((len(blob)+0x7ff)//0x800)*0x800)
(OUT/'late-main.bin').write_bytes(base)
source = (BUILD/'replay.mjs').read_text(encoding='utf-8')
needle = "  curStep = t + \"#\" + log.length;"
assert source.count(needle) == 1
replacement = needle + "\n  if (curStep === 'down#6') { lab.sim.write(parseInt(process.env.PROBE_FLAG,16), Uint8Array.of(1)); console.log('LATE_ARMED'); }"
(OUT/'late-replay.mjs').write_text(source.replace(needle,replacement), encoding='utf-8')
env = dict(os.environ, OM_EMU_MODEL='E147', PROBE_FLAG=f"{sy['probe_flag']:x}")
for name in ('GAME_STATE','GAME_GC','WATCH','WSTACK','WFROM','WIDS'):
    env.pop(name,None)
cmd = ['node',str(OUT/'late-replay.mjs'),(ROOT/'work/om-emu/emu').as_uri(),str(OUT/'late-main.bin'),
       str(BUILD/'paired.omsd'),str(OUT/'late.json'),str(OUT/'late-saved.omsd'),
       's1 ok ok down down down shot:work/separate-games/late.png menu s1']
with (OUT/'late.log').open('w',encoding='utf-8') as log:
    subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
log = (OUT/'late.log').read_text(encoding='utf-8')
result = json.loads((OUT/'late.json').read_text(encoding='utf-8'))
assert log.count('LATE_ARMED') == 1
assert not result['engineErrors'], result['engineErrors']
draws=[x for x in result['draws'] if x.get('data') == sy['probe_image']+0x40000000]
assert len(draws)==2 and {x['record'] for x in draws}=={0x62b77c44,0x62b77c54},draws
png=(OUT/'late.png').read_bytes(); offset=8; compressed=bytearray()
while offset<len(png):
    size=int.from_bytes(png[offset:offset+4],'big'); kind=png[offset+4:offset+8]
    if kind==b'IHDR': width,height=struct.unpack('>II',png[offset+8:offset+16])
    if kind==b'IDAT': compressed.extend(png[offset+8:offset+8+size])
    offset+=size+12
raw=zlib.decompress(compressed); stride=width*3+1
assert (width,height)==(900,600)
def pixel(x,y):
    assert raw[y*stride]==0
    return raw[y*stride+1+3*x:y*stride+4+3*x]
assert pixel(400,130)==pixel(400,170)!=pixel(400,150), 'Panel bands not visible'
print('Two native bitmap calls and visible panel bands verified; inspect late.png for composition.')
