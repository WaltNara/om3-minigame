"""Seal the Flappy tap-ending fix (v2) as a NEW release: five-r5.

Source: work/flappy-touch-v2, raw SHA256 a3b5e0aa... (20 bytes larger than the
sealed r4 image). Reports are the three v2 reports tied to that exact hash.
This packager refuses to overwrite r4, withdrawn r3, or any existing release.
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[2] / "native"), str(_Path(__file__).resolve().parents[2] / "tests")]
import hashlib, json, shutil, struct, sys, zipfile
from pathlib import Path

R = Path(__file__).resolve().parents[2]
G = R / 'work/flappy-touch-v2'
D = R / 'artifacts/om3-games-bundle-five-r5'
Z = D.with_suffix('.zip')
RAW_SHA = 'a3b5e0aa720f3703f6d3adcf771edb855ac99d63c24c116816976ff37c203ed8'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

# Reports tied to the EXACT v2 candidate image; v2 has no touch-handshake summary.
REPORTS = [
    'validation/validation.json',
    'outside/validation.json',
    'touch-reply/validation.json',
]
IMAGES = ['validation/ready.png', 'validation/flight.png', 'validation/reset.png']
DOCS = ['FLAPPY_TOUCH_MISSES.md', 'FLAPPY_TOUCH_REPAIR_STATUS.md',
        'TOUCH_FREEZE_R3.md', 'FLAPPY_STATUS.md', 'COMPACT_MEMORY_STATUS.md']


def seal():
    assert not D.exists() and not Z.exists() and not Z.with_suffix('.zip.sha256').exists(), \
        'Preserve releases; choose a new name'
    m = json.loads((G / 'build.json').read_text(encoding='utf-8'))
    raw = (G / 'row-main.bin').read_bytes()
    digest = sha(G / 'row-main.bin')
    assert digest == m['candidate_sha256'] == RAW_SHA, ('candidate changed', digest)
    assert sha(G / 'main.bin') == digest, 'main.bin differs from row-main.bin'
    assert m['custom_game_touch'] and m['extension_bytes'] == 236268
    for name, want in m['source_sha256'].items():
        assert sha(R / 'native' / name) == want, ('source changed since build', name)

    reports = {}
    for rel in REPORTS:
        report = json.loads((G / rel).read_text(encoding='utf-8'))
        assert report['status'].lower().startswith('pass'), rel
        assert report.get('candidate_sha256') == digest, ('stale report', rel)
        reports[rel] = report
    assert sum(v['sent'] for v in reports['touch-reply/validation.json']['scenarios'].values()) == 181
    assert all(v['replies'] == v['sent'] == v['waits'] == v['returned']
               for v in reports['touch-reply/validation.json']['scenarios'].values())
    assert reports['outside/validation.json']['matching_snapshots'] == 14
    assert reports['validation/validation.json']['physics_cases'] == 1750

    loaded = struct.unpack_from('<I', raw, 0x60045e9c - 0x60021020)[0] - 0x60f59800
    assert loaded == 237568 and loaded <= 256 * 1024 and m['extension_bytes'] <= 240 * 1024

    sys.path.insert(0, str(R / 'native/bundle'))
    from package import firmware_container
    config = json.loads((R / 'build/games.json').read_text(encoding='utf-8'))
    candidate, spec = firmware_container(config, raw)

    for folder in ('card/DCOLYMP', 'card/OM3MOD', 'restore/DCOLYMP', 'evidence', 'source/native'):
        (D / folder).mkdir(parents=True, exist_ok=True)
    firmware = D / 'card/DCOLYMP/E1479999.BIN'
    firmware.write_bytes(candidate)
    restore = D / 'restore/DCOLYMP/E1479999.BIN'
    shutil.copyfile(R / 'work' / spec['stock_file'], restore)
    assert sha(restore) == spec['stock_sha256']

    release = R / 'vendor/caduceus-om3/releases/v0.26.2'
    checks = {Path(line.split()[1].lstrip('*')).name: line.split()[0]
              for line in (release / 'SHA256SUMS').read_text(encoding='utf-8').splitlines() if line.strip()}
    for name in ('GUIDES.BIN', 'LABELS.BIN', 'TONES.BIN'):
        assert sha(release / name) == checks[name]
        shutil.copyfile(release / name, D / 'card/OM3MOD' / name)

    for rel in REPORTS + IMAGES + ['build.json']:
        dest = D / 'evidence' / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(G / rel, dest)

    sources = set(m['source_sha256']) | {
        'package_flappy_touch_v2.py', 'test_flappy.py', 'test_flappy_touch.py',
        'test_flappy_outside.py', 'test_flappy_touch_reply.py', 'test2048_large.py'}
    for name in sorted(sources):
        shutil.copyfile(R / 'native' / name, D / 'source/native' / name)
    shutil.copytree(R / 'native/bundle', D / 'source/native/bundle',
                    ignore=shutil.ignore_patterns('__pycache__'))
    for name in DOCS:
        shutil.copyfile(R / 'native' / name, D / name)

    install = (R / 'docs/INSTALL_FIVE_GAMES.md').read_text(encoding='utf-8')
    note = ('<!-- r5: Flappy tap-ending fix over r4. Same card layout, hold-OK flash '
            'and rollback procedure as the standard instructions below. Updating '
            'over r4, withdrawn r3 or four-game r2 uses these identical steps. -->\n\n')
    (D / 'INSTALL_AND_RESTORE.md').write_text(note + install, encoding='utf-8')
    for name in ('LICENSE', 'NOTICE'):
        shutil.copyfile(R / 'vendor/caduceus-om3' / name, D / name)
    shutil.copyfile(R / 'vendor/caduceus-om3/docs/INSTALL.md', D / 'UPSTREAM_INSTALL.md')
    shutil.copyfile(R / 'build/Verify-Package.ps1', D / 'Verify-Package.ps1')

    info = dict(package=D.name, target='OM SYSTEM OM-3 1.1 / E147 build 1100',
                candidate_sha256=digest, firmware_sha256=sha(firmware),
                stock_restore_sha256=sha(restore),
                loaded_extension_bytes=loaded, ceiling_bytes=262144,
                headroom_bytes=262144 - loaded,
                games=['2048', 'Minesweeper', 'Mini Mario', 'Breakout', 'Flappy'],
                supersedes='om3-games-bundle-five-r4 (camera: no freeze, >50% taps missed)',
                validation=dict(emulator_only=True, physical_flappy_touch_verified=False,
                                native_application_protocol_verified=True,
                                reports=REPORTS),
                container_checks=dict(all_components_valid=True,
                                      decoded_main_matches_tested_image=True,
                                      other_components_unchanged=True),
                optional_files_included=False)
    (D / 'games-bundle.json').write_text(json.dumps(info, indent=2) + '\n', encoding='utf-8')

    (D / 'README.md').write_text('''# OM-3 five games — r5 (Flappy tap-ending / missed-tap fix)

2048, Minesweeper, scrolling Mini Mario, Breakout and slow tap-controlled Flappy.
This release supersedes r4: the camera stop freezing after the r4 touch-reply
repair, but more than half of normal taps were missed. r5 clears a latched
contact on alternative tap endings (kinds 3/4/5) and cleans up interrupted
gestures, without adding a second flap on completion.

For standard OM-3 firmware 1.1 / E147 build 1100, based on Caduceus v0.26.2.

## What changed

r4 accepted a kind-1 contact only when none was latched, and cleared that latch
only on kind 3. Gestures ending in kind 4/5 (tap / double tap) left the latch
set and could suppress later presses or produce no flap. r5 clears the latch
and interrupt drain on 3/4/5. The reply path, button input, timer and physics
are unchanged; no extra state, allocation, timer or SD writes.

Local validation: 14 native application/GUI protocol scenarios, 181 touch events
with 181 replies / 181 entered and returned waits, preserved original event
bytes, registers and stack; 64-tap stress; 1,750 physics cases; 26 raster frames;
seven GUI scenarios; 17 x 3,000-tick playability streams; 14 outside-game
touch/profile snapshots matching R2.

## Still unverified

**This is an experimental camera trial, not a validated release.** OM-Emu does
not model the physical E147 touch controller. Whether kind-4/5 endings explain
the camera's missed taps remains a hypothesis; actual event kinds, timing,
long-session stability and touch recovery after an LCD/EVF switch are NOT
verified. If the camera freezes or behaves incorrectly, power off and use the
rollback instructions. Do not keep retrying or run Games unattended.

## Install / rollback

Read **INSTALL_AND_RESTORE.md**. Only `card/` contents go on the SD; `restore/`
stays on the PC unless restoring. Hold OK during power-on until updating starts;
wait for the steady writing phase to finish. After completion, power off and
remove only `DCOLYMP/E1479999.BIN`, keeping OM3MOD. The same procedure works when
updating over r4, withdrawn r3 or four-game r2. Rollback uses the separate
four-game r2 package or this package's official restore image — never mix BINs.

In COLOR1-4, open Picture Mode from the Super Control Panel and scroll to Games.
Flappy: tap or Up/OK to flap, INFO reset, MENU launcher, shutter exits. Lift the
finger before pressing MENU (stock ignores MENU while a finger is held). Only
Flappy owns touch; other games keep stock touch behavior.

Loaded games section: 232 KiB of 256 KiB, leaving 24 KiB. Verification reports,
previews and source are included. Verify-Package.ps1 checks files and can verify
the card copies; it never writes.

Keep this local package private; it contains manufacturer firmware.
''', encoding='utf-8')

    files = sorted(p for p in D.rglob('*') if p.is_file())
    (D / 'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(D).as_posix()}\n' for p in files),
                                  encoding='ascii')
    with zipfile.ZipFile(Z, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in files + [D / 'SHA256SUMS']:
            z.write(p, Path(D.name) / p.relative_to(D))
    with zipfile.ZipFile(Z) as z:
        assert z.testzip() is None
        for p in files:
            assert hashlib.sha256(z.read((Path(D.name) / p.relative_to(D)).as_posix())).hexdigest() == sha(p)
    Z.with_suffix('.zip.sha256').write_text(f'{sha(Z)}  {Z.name}\n', encoding='ascii')
    print(json.dumps(dict(archive=str(Z), zip_bytes=Z.stat().st_size,
                          zip_sha256=sha(Z), **info), indent=2))


if __name__ == '__main__':
    seal()
