"""Create a separate experimental package from the checked Games image."""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[2] / "native"), str(_Path(__file__).resolve().parents[2] / "tests")]
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'work/separate-games'
BASE=ROOT/'work/native-build'
UP=ROOT/'vendor/caduceus-om3'
DEST=ROOT/'artifacts/om3-games-experimental'
sys.path.insert(0,str(UP/'firmware'))
import patch

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((OUT/'build.json').read_text())
game=json.loads((OUT/'games-validation.json').read_text())
display=json.loads((OUT/'display-validation.json').read_text())
main=(OUT/'row-main.bin').read_bytes()
digest=hashlib.sha256(main).hexdigest()
assert digest==build['candidate_sha256']==game['image_sha256']==display['image_sha256']
assert game['status']=='passed' and display['status'].startswith('partial:')
for name,want in build['source_sha256'].items():
 assert sha(ROOT/'native'/name)==want,f'Changed after test: {name}'
spec=json.loads((UP/'releases/v0.26.2/patch.json').read_text())
original=(ROOT/'work'/patch.STOCK_NAME).read_bytes()
base=(BASE/'caduceus-v0.26.2.bin').read_bytes()
assert patch.sha(original)==spec['stock_sha256'] and patch.sha(base)==spec['result_sha256']
comp=patch.parse(base)[0]
trailer=bytearray(comp['trl'])
struct.pack_into('<I',trailer,28,(-patch.wordsum(comp['hdr'])-patch.wordsum(main)-patch.wordsum(trailer[:28]))&0xffffffff)
updated=comp['hdr']+patch.encode(main)+trailer
candidate=updated+base[len(updated):]
assert len(candidate)==len(original)
check=patch.parse(candidate)[0]
assert patch.decode(check['enc'])==main
assert (patch.wordsum(check['hdr'])+patch.wordsum(main)+patch.wordsum(check['trl']))&0xffffffff==0
for folder in ('card/DCOLYMP','card/OM3MOD','evidence','source'):(DEST/folder).mkdir(parents=True,exist_ok=True)
firmware=DEST/'card/DCOLYMP/E1479999.BIN'
firmware.write_bytes(candidate)
release=UP/'releases/v0.26.2'
checks={Path(line.split()[1].lstrip('*')).name:line.split()[0] for line in (release/'SHA256SUMS').read_text().splitlines() if line.strip()}
for name in ('GUIDES.BIN','LABELS.BIN','LOOKS.BIN','TONES.BIN'):
 assert sha(release/name)==checks[name]
 shutil.copyfile(release/name,DEST/'card/OM3MOD'/name)
for name in ('games-row.png','launcher0.png','launcher1.png','separate-2048.png','separate-2048-play.png',
             'games-validation.json','display-validation.json','build.json'):
 shutil.copyfile(OUT/name,DEST/'evidence'/name)
for name in build['source_sha256']:
 shutil.copyfile(ROOT/'native'/name,DEST/'source'/name)
for name in ('2048-host.s','assets.inc'):
 shutil.copyfile(OUT/name,DEST/'source'/name)
for name in ('LICENSE','NOTICE'):shutil.copyfile(UP/name,DEST/name)
load_end=struct.unpack_from('<I',main,0x60045e9c-0x60021020)[0]
readme=f'''# Experimental Games for OM SYSTEM OM-3

OM-3 firmware 1.1 / E147 build 1100 only. Based on Caduceus v0.26.2.
**Tested in OM-Emu; not tested on a physical camera.** The emulator does not
model drawing latency, and this build still needs physical-camera validation.

Open Picture Mode from the Super Control Panel on COLOR1–4. Scroll to Games
at the end of the list and press OK. Choose 2048 or Back with arrows or a
dial; OK selects. In 2048, arrows move; main dial moves up/down, sub dial
moves left/right; INFO starts a new round. MENU returns to the launcher, and
MENU or Back from the launcher returns to Picture Mode. A shutter half-press
exits. Changing between LCD and EVF closes the Games session; returning to
shooting after the switch has not been verified in the emulator.

The board is 384 × 480 pixels. It uses an event-driven renderer, a bounded
{build['resources']['compressed_board_capacity']:,}-byte RLE buffer, no heap
and no animation timer. The added loaded section is {load_end-0x60f59800:,}
bytes. The native drawing path waits for an OSD completion event, but real
timing, display output and responsiveness remain unverified on hardware.

The `card` directory contains the patched firmware and the matching upstream
OM3MOD support files. Back up existing OM3MOD files: the included LOOKS.BIN
contains upstream default looks. The existing experimental HSL-based 2048
package is separate. The stock Caduceus installation and recovery procedures
are in `vendor/caduceus-om3/docs/INSTALL.md` in the project.

Evidence and source are included. Games row and 2048 controls were checked
against the independent rules reference for this exact main image. Earlier
replays checked HSL, WB, and COLOR1–4; LCD/EVF switching clears the Games
state, but the emulator did not establish normal shooting after a switch.

Main image SHA-256: {digest}
Firmware SHA-256: {sha(firmware)}
'''
(DEST/'README.md').write_text(readme,encoding='utf-8')
files=sorted(p for p in DEST.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
(DEST/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(DEST).as_posix()}\n' for p in files),encoding='utf-8')
archive=ROOT/'artifacts/om3-games-experimental.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(DEST.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(DEST).as_posix())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
print(f'Experimental package: {archive}\nFirmware SHA-256: {sha(firmware)}')
