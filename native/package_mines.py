"""Package the validated 2048 + Minesweeper image as a standalone Games bundle.

The camera installs one firmware file, so games are combined into a single
image at build time. This package is a strict superset of the earlier 2048
Games package: it keeps 2048, the same Caduceus v0.26.2 baseline and the same
version-matched card files, and adds Minesweeper behind one launcher.

It never writes to the existing 2048 or Mario artifacts. See
COMBINING_GAMES.md for the module contract needed to add another game.
"""
import hashlib
import json
import shutil
import struct
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'work/mines-game'
CORE = ROOT / 'work/mines-core'
RENDER = ROOT / 'work/mines-render'
BASE = ROOT / 'work/native-build'
UP = ROOT / 'vendor/caduceus-om3'
RELEASE = UP / 'releases/v0.26.2'
DEST = ROOT / 'artifacts/om3-minesweeper-experimental'
ARCHIVE = ROOT / 'artifacts/om3-minesweeper-experimental.zip'
START, BASE_ADDR, LIMIT = 0x60f59800, 0x60021020, 0x40000
LOAD_END_SITE = 0x60045e9c

sys.path.insert(0, str(UP / 'firmware'))
import patch

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
build = json.loads((OUT / 'build.json').read_text())
main = (OUT / 'row-main.bin').read_bytes()
digest = hashlib.sha256(main).hexdigest()
game = json.loads((OUT / 'mines-validation.json').read_text())
core = json.loads((CORE / 'validation.json').read_text())
render = json.loads((RENDER / 'validation.json').read_text())
assert digest == build['candidate_sha256'] == game['image_sha256'], 'image hash mismatch'
assert all(r['status'] == 'passed' for r in (game, core, render)), 'validation not passed'
for name, want in build['source_sha256'].items():
    assert sha(ROOT / 'native' / name) == want, f'changed since build: {name}'

# Rebuild the installable firmware container from the validated main block.
spec = json.loads((RELEASE / 'patch.json').read_text())
original = (ROOT / 'work' / patch.STOCK_NAME).read_bytes()
base = (BASE / 'caduceus-v0.26.2.bin').read_bytes()
assert patch.sha(original) == spec['stock_sha256'], 'stock firmware hash mismatch'
assert patch.sha(base) == spec['result_sha256'], 'Caduceus baseline hash mismatch'
comp = patch.parse(base)[0]
trailer = bytearray(comp['trl'])
struct.pack_into('<I', trailer, 28,
                 (-patch.wordsum(comp['hdr']) - patch.wordsum(main)
                  - patch.wordsum(trailer[:28])) & 0xffffffff)
updated = comp['hdr'] + patch.encode(main) + trailer
candidate = updated + base[len(updated):]
assert len(candidate) == len(original)
check = patch.parse(candidate)[0]
assert patch.decode(check['enc']) == main
assert (patch.wordsum(check['hdr']) + patch.wordsum(main)
        + patch.wordsum(check['trl'])) & 0xffffffff == 0

for folder in ('card/DCOLYMP', 'card/OM3MOD', 'optional/OM3MOD', 'evidence', 'source'):
    (DEST / folder).mkdir(parents=True, exist_ok=True)
firmware = DEST / 'card/DCOLYMP/E1479999.BIN'
firmware.write_bytes(candidate)
checks = {Path(line.split()[1].lstrip('*')).name: line.split()[0]
          for line in (RELEASE / 'SHA256SUMS').read_text().splitlines() if line.strip()}
for name in ('GUIDES.BIN', 'LABELS.BIN', 'TONES.BIN'):
    assert sha(RELEASE / name) == checks[name], name
    shutil.copyfile(RELEASE / name, DEST / 'card/OM3MOD' / name)
# LOOKS.BIN holds the user's own film simulations. Keep it optional so
# installing this bundle never overwrites the card's existing copy.
assert sha(RELEASE / 'LOOKS.BIN') == checks['LOOKS.BIN']
shutil.copyfile(RELEASE / 'LOOKS.BIN', DEST / 'optional/OM3MOD/LOOKS.BIN')

screenshots = ('launcher.png', 'mines-start.png', 'mines-move.png', 'mines-open.png',
               'mines-flag.png', 'mines-won.png', 'mines-restarted.png', 'mines-hold.png',
               'mines-back.png', 'puzzle-2048.png', '2048-hold.png', 'mines-resume.png',
               'mines-exit.png', 'mines-display-start.png', 'mines-display-after.png',
               'mines-after-switch.png')
for name in screenshots:
    assert (OUT / name).is_file(), name
    shutil.copyfile(OUT / name, DEST / 'evidence' / name)
for src, name in ((OUT / 'build.json', 'build.json'),
                  (OUT / 'mines-validation.json', 'mines-validation.json'),
                  (CORE / 'validation.json', 'mines-core-validation.json'),
                  (RENDER / 'validation.json', 'mines-render-validation.json')):
    shutil.copyfile(src, DEST / 'evidence' / name)
shutil.copyfile(ROOT / 'native/MINES_STATUS.md', DEST / 'evidence/MINES_STATUS.md')

for name in build['source_sha256']:
    shutil.copyfile(ROOT / 'native' / name, DEST / 'source' / name)
for name in ('2048-host.s', 'assets.inc', 'mines_assets.inc', 'original.inc',
             'launcher0.bin', 'launcher1.bin', 'launcher2.bin'):
    shutil.copyfile(OUT / name, DEST / 'source' / name)
shutil.copyfile(ROOT / 'native/package_mines.py', DEST / 'source/package_mines.py')
for name in ('LICENSE', 'NOTICE'):
    shutil.copyfile(UP / name, DEST / name)
shutil.copyfile(ROOT / 'native/COMBINING_GAMES.md', DEST / 'COMBINING_GAMES.md')

load_end = struct.unpack_from('<I', main, LOAD_END_SITE - BASE_ADDR)[0]
used = load_end - START
linked = (OUT / 'row.bin').stat().st_size
assert 0 < used <= LIMIT and 0 < linked < used + LIMIT
manifest = {
    'package': 'om3-minesweeper-experimental',
    'contents': 'one firmware image with a shared Games launcher for 2048 and Minesweeper',
    'target': {'camera': 'OM SYSTEM OM-3', 'firmware': '1.1', 'model': 'E147', 'build': 1100},
    'baseline': {'caduceus': 'v0.26.2',
                 'stock_firmware': patch.STOCK_NAME,
                 'stock_sha256': spec['stock_sha256'],
                 'caduceus_bin_sha256': spec['result_sha256'],
                 'main_image_sha256': digest},
    'installable_firmware': {'path': 'card/DCOLYMP/E1479999.BIN', 'sha256': sha(firmware)},
    'card_files': {'version_matched': ['GUIDES.BIN', 'LABELS.BIN', 'TONES.BIN'],
                   'keep_existing': ['LOOKS.BIN', 'EDITS.BIN', 'BUNDLES.BIN'],
                   'optional_default_looks': 'optional/OM3MOD/LOOKS.BIN'},
    'extension': {'base': hex(START), 'limit_bytes': LIMIT, 'used_bytes': used,
                  'linked_blob_bytes': linked, 'load_end_site': hex(LOAD_END_SITE)},
    'launcher': {'entries': 3, 'back_index': 2,
                 'entries_order': ['2048', 'MINESWEEPER', 'BACK'],
                 'state_ids': {'closed': 0, 'launcher': 1, '2048': 2, 'minesweeper': 3}},
    'games': [{'name': '2048', 'state_id': 2, 'buffer': 'board_buffer',
               'buffer_bytes': build['resources']['board_2048_capacity']},
              {'name': 'MINESWEEPER', 'state_id': 3, 'buffer': 'mines_buffer',
               'buffer_bytes': build['resources']['capacity']}],
    'hook_sites': {'string': '0x610f56a6', 'picture_mode_update': '0x611d04ec',
                   'picture_mode_cal': '0x6125becc', 'screen_transition': '0x610f6016',
                   'queue_hook': '0x610f48ef', 'render_hook': '0x610f7fe9',
                   'dial_hook': '0x60177b7d', 'row_list': '0x60f49a63',
                   'row_table': ['0x611d040f', '0x611d0848']},
    'integration': {'single_firmware_only': True,
                    'combine_at_build_time': True,
                    'contract': 'COMBINING_GAMES.md',
                    'host_dispatch': 'mines_host.s / games_pm, games_render_hook',
                    'menu': 'mines_menu.s / games_event',
                    'launcher_bitmaps': 'mines_launcher_assets.py',
                    'build_driver': 'build_mines.py'},
    'validation': {'status': 'passed', 'emulator_only': True,
                   'native_rule_cases': core['cases'],
                   'decoded_render_frames': render['frames'],
                   'whole_camera_checks': game['checks'],
                   'display_switch': game['display_switch']},
    'source_sha256': build['source_sha256'],
}
(DEST / 'games-bundle.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')

readme = f'''# Experimental Games bundle: 2048 + Minesweeper for OM SYSTEM OM-3

OM-3 firmware 1.1 / E147 build 1100 only, based on Caduceus v0.26.2.
**Tested in OM-Emu; never tested on a physical camera.** This is an
unofficial, experimental firmware modification. Read
`vendor/caduceus-om3/docs/INSTALL.md` in the project before installing.

One firmware image carries **both** games behind a single Games row in
Picture Mode. It is a strict superset of the earlier `om3-games-experimental`
package: 2048 is unchanged, the Caduceus baseline and the version-matched
card files are the same, and Minesweeper is added to the launcher.

## Installing together with other games

The camera accepts exactly one `DCOLYMP/E1479999.BIN`. Game code lives in the
firmware main block, **not** in the `OM3MOD` data files, so two game packages
cannot be installed side by side: the last firmware written wins. Coexistence
means one combined image with one launcher. This package is such a combined
image; [COMBINING_GAMES.md](COMBINING_GAMES.md) and `games-bundle.json` give
the contract for compiling a future game (for example Mini Mario) into the
same image. Do not flash two game packages and expect both to appear.

Copy `card/DCOLYMP/E1479999.BIN` and the three version-matched files
`card/OM3MOD/GUIDES.BIN`, `LABELS.BIN`, `TONES.BIN` to the top of the SD card.
**Keep your existing** `LOOKS.BIN`, `EDITS.BIN` and `BUNDLES.BIN`: they hold
your film simulations and edits. A default `LOOKS.BIN` is provided under
`optional/` only, so installing this bundle does not overwrite them. Never
mix `OM3MOD` files from different Caduceus versions. After the update,
delete `DCOLYMP/E1479999.BIN` from the card so it is not installed again.

## Playing

From the Super Control Panel on COLOR1-4, open Picture Mode, scroll to
**Games** at the end of the list and press OK. The launcher offers 2048,
MINESWEEPER and Back; arrows or either dial change the selection, OK enters.

| Input | Minesweeper | 2048 |
| --- | --- | --- |
| Arrows / main and sub dials | Move the cursor | Move tiles |
| OK | Open a cell; **after a win or loss, start a new round** | Select / confirm |
| INFO | Toggle a flag; after a win or loss, start a new round | Start a new round |
| MENU | Back to the launcher; re-entering resumes | Back to the launcher |
| Shutter half-press | Leave Games through the camera's own path | Leave Games |
| LCD / EVF switch | Clear the Games session | Clear the Games session |

**A held OK is deliberately not a control.** Long presses are ambiguous on
this body and are ignored; a new round is only started in the normal way after
a round has ended, or with INFO in 2048.

Minesweeper is 8x8 with 10 mines. Mines are placed on the first opening move
outside that cell's 3x3 neighbourhood, so the first click is always safe.
Empty areas expand automatically; the HUD shows remaining mines, opened cells
and flags. There is one board, no pause, no timer and no chording.

## Camera-safety design

- Event driven: **no periodic timer and no GUI queue hook**, no heap, no
  full framebuffer, no runtime scanline encoding. Rendering copies prepacked
  RLE words into a bounded buffer ({manifest['games'][1]['buffer_bytes']:,} bytes
  for Minesweeper, {manifest['games'][0]['buffer_bytes']:,} bytes for 2048).
- Only the two palette indices already proven by the 2048 guide images are
  used. A buffer sentinel is checked in the render test.
- The added loaded section is {used:,} bytes of a {LIMIT:,}-byte ceiling; the
  linked `.text` blob is {linked:,} bytes.
- Display output changes and real screen transitions clear Games state and
  pass the event back to the stock camera handler. Key releases are consumed
  only while Games owns input.

## What was verified

All three layers run inside OM-Emu on this exact image (SHA-256 of the main
block: `{digest}`): {core['cases']} native CPU rule cases against an
independent model, {render['frames']} decoded 384x480 render frames compared
pixel by pixel, and a whole-camera replay covering the Games row, both games,
the launcher, end-of-round restart, ignored held-OK presses, shutter exit,
display-switch cleanup and the return to shooting. The same display-switch
script was replayed on the untouched Caduceus main block and produced the
same stock GUI trajectory.

After leaving Games with a shutter half-press, a display switch re-enters the
shooting GUI state (`0x0108`) and a full shutter press is handled without
leaving that state or producing engine errors. OM-Emu has no live-view scene
in this replay, so no photograph is actually captured and the shooting screen
composes as a flat frame; the GUI state is the evidence.

## Limitations

- Emulator evidence is not hardware evidence. Drawing latency, real button
  timing, buffer lifetime and concurrent key behaviour need a physical camera.
- Switching displays **while the Games menu is open** clears the session and
  leaves the camera in the stock Picture Mode screen. OM-Emu cannot model the
  re-entry to live view from that state; this is identical on the untouched
  baseline and remains a hardware-only check.
- The 3x5 bitmap font is coarse. Physical camera behaviour after an LCD/EVF
  switch must be confirmed before calling this build camera-safe.

`evidence/` contains the validation reports, build metadata and screenshots;
`source/` contains the build, test and packaging files, generated assets and
launcher bitmaps, all covered by `games-bundle.json` source hashes.

Main image SHA-256: {digest}
Firmware SHA-256: {sha(firmware)}
'''
(DEST / 'README.md').write_text(readme, encoding='utf-8')

files = sorted(p for p in DEST.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
(DEST / 'SHA256SUMS').write_text(
    ''.join(f'{sha(p)}  {p.relative_to(DEST).as_posix()}\n' for p in files), encoding='utf-8')
with zipfile.ZipFile(ARCHIVE, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for p in sorted(DEST.rglob('*')):
        if p.is_file():
            z.write(p, p.relative_to(DEST).as_posix())
with zipfile.ZipFile(ARCHIVE) as z:
    assert z.testzip() is None
print(f'Games bundle: {ARCHIVE}')
print(f'Firmware SHA-256: {sha(firmware)}')
print(f'Main image SHA-256: {digest}')
print(f'Loaded extension: {used:,} / {LIMIT:,} bytes')
