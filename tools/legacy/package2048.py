"""Package only the exact firmware that passed both native and UI checks."""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[2] / "native"), str(_Path(__file__).resolve().parents[2] / "tests")]
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'work/native-build'
DEST=ROOT/'artifacts/om3-2048-experimental'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((OUT/'build.json').read_text())
core=json.loads((OUT/'core-validation.json').read_text())
ui=json.loads((OUT/'2048-validation.json').read_text())
assert core['status']=='passed' and ui['status'].startswith('passed')
assert core['candidate_sha256']==ui['candidate_sha256']==build['candidate_sha256']==sha(OUT/'candidate.bin')
for name in ['2048.s','assets.py','build.py','test2048.py','prepare_emulator.py']:
    assert sha(ROOT/'native'/name)==ui['source_sha256'][name],f'Untested source change: {name}'
assert build['resources']['heap_allocations']==0
assert build['resources']['additional_section_copy_bytes']==26624
for folder in ['card/DCOLYMP','card/OM3MOD','evidence','source']:
    (DEST/folder).mkdir(parents=True,exist_ok=True)
shutil.copyfile(OUT/'candidate.bin',DEST/'card/DCOLYMP/E1479999.BIN')
release=ROOT/'vendor/caduceus-om3/releases/v0.26.2'
checks={Path(line.split()[1].lstrip('*')).name:line.split()[0] for line in (release/'SHA256SUMS').read_text().splitlines() if line.strip()}
for name in ['GUIDES.BIN','LABELS.BIN','TONES.BIN','LOOKS.BIN']:
    assert sha(release/name)==checks[name]
    shutil.copyfile(release/name,DEST/'card/OM3MOD'/name)
for name in ['2048-start.png','2048-playing.png','2048-reset.png','core-validation.json','2048-validation.json','build.json']:
    shutil.copyfile(OUT/name,DEST/'evidence'/name)
for name in ['2048.s','assets.py','build.py','test2048.py','prepare_emulator.py']:
    shutil.copyfile(ROOT/'native'/name,DEST/'source'/name)
for name in ['LICENSE','NOTICE']:
    shutil.copyfile(ROOT/'vendor/caduceus-om3'/name,DEST/name)
readme="""# Native 2048 for OM SYSTEM OM-3

Experimental personal build for OM-3 firmware **1.1 / E147 build 1100**.
Based on Caduceus v0.26.2 at f4d2569eb46817795ec5ffaf931ba058d2c0d029.
**Passed emulator tests; not tested on a physical camera.**

The COLOR1 HSL wheel becomes 2048 while this firmware is installed.
It implements four-way slides, single merges, scoring, two initial tiles,
approximately 90% 2 / 10% 4 spawning after valid moves, game over,
and continued play after 2048. Game state is held in RAM and resets at power-off.

## Files and installation

The two folders inside `card/` are ready for the top of an SD card:

```
DCOLYMP/E1479999.BIN
OM3MOD/GUIDES.BIN
OM3MOD/LABELS.BIN
OM3MOD/TONES.BIN
OM3MOD/LOOKS.BIN
```

Keep firmware and GUIDES.BIN from this package together. Back up your existing
OM3MOD files first; the supplied LOOKS.BIN contains the upstream default looks.
Existing custom LOOKS.BIN, EDITS.BIN and BUNDLES.BIN can be kept.

Use Caduceus's documented SD installation procedure with a fully charged battery:
camera off, hold OK while powering on; steady light means writing, blinking
after about two minutes means finished. Do not interrupt a steady-light update.
Afterwards remove DCOLYMP/E1479999.BIN from the card; retain OM3MOD.
The full upstream instructions are in vendor/caduceus-om3/docs/INSTALL.md in
the local project. This package does not flash or contact a camera automatically.

To restore official firmware, the verified local original is
`work/OLY_E_147_1100_0000_0000.BIN` in the project. Copy it to a separate card's
DCOLYMP/E1479999.BIN and follow the same upstream update procedure.

## Play

Turn the creative dial to COLOR and select COLOR1. Open Picture Mode from
the Super Control Panel and select its HSL / colour-wheel row (the Down step
from the COLOR1 heading). The board appears in the centre of that screen.
Half-press the shutter once first if Caduceus has not yet loaded its card files.

- Four arrow buttons: move in that direction.
- Rear/main dial: up/down; front/sub dial: left/right.
- Hold OK: new game. A short INFO press leaves the board unchanged.
- MENU or shutter half-press: leave the game and restore the camera guides.

## Resource budget and validation

26 KiB of additional section RAM is loaded, including code, assets and scratch.
The byte-exponent board occupies 16 bytes. A fixed 18,052-byte RLE drawing
buffer replaces an 81,920-byte 8-bit framebuffer. There are no heap allocations,
background tasks, animation timers, runtime file writes or external libraries.
Only changed boards are recomposed; blocked moves do not spawn or redraw.
The native slide checks peak at 856 instructions. Rendering in the tested
worst fixture takes 75,069 instructions. Core/renderer stack use peaks at
68 bytes; the enclosing input wrapper adds at most 24 bytes.

617 tests execute the compiled MN10300 code. They check directions, merge
order, score, spawn, terminal states, ABI preservation, no-op handling and
RLE-buffer canaries. Full UI replay checks arrows, both dials, restart,
MENU/half-press exit, unchanged photo settings, three rendered boards and
zero OSD engine errors. See evidence/ for screenshots and reports.

The emulator does not reproduce every camera display plane or its exact
colours. These results are emulator evidence, not hardware validation.

SHA256SUMS verifies every packaged file. Source is under source/; the full
reproducible local build is in D:/om3-minigames/native/.
"""
(DEST/'README.md').write_text(readme,encoding='utf-8')
files=sorted(p for p in DEST.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
(DEST/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(DEST).as_posix()}\n' for p in files))
archive=ROOT/'artifacts/om3-2048-experimental.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(DEST.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(DEST))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
assert sha(DEST/'card/DCOLYMP/E1479999.BIN')==build['candidate_sha256']
print(json.dumps({'package':str(archive),'zip_bytes':archive.stat().st_size,
    'zip_sha256':sha(archive),'firmware_sha256':build['candidate_sha256'],
    'status':'emulator-tested; not camera-tested'},indent=2))
