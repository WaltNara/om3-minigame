"""Generic, manifest-driven packager for the combined Games firmware.

This is the successor to the game-specific package_mines.py: every game
name, control table, source file, validation report and screenshot comes from
games.json. Registering a new game therefore needs no change here.

Use --dry-run to check inputs without writing anything. Normal execution
creates one combined install image and a separately labelled stock restore
image. Existing release folders are never overwritten.
"""
import argparse
import hashlib
import json
import shutil
import struct
import sys
import zipfile
from pathlib import Path

import manifest

ROOT = manifest.ROOT


def verify(data):
    """Check every precondition. Returns (data, build, reports, main, digest)."""
    out = ROOT / data['image']['output_dir']
    meta = manifest.metadata_path(data)
    if not meta.is_file():
        raise SystemExit('run bundle/build.py before packaging')
    bundle = json.loads(meta.read_text(encoding='utf-8'))
    if bundle.get('status') != 'passed':
        raise SystemExit('bundle build has not passed')
    main = (out / data['image']['main_image']).read_bytes()
    digest = hashlib.sha256(main).hexdigest()
    if digest != bundle['main_image_sha256']:
        raise SystemExit('image changed since the last bundle build')
    build = json.loads((out / data['image']['build_metadata']).read_text())
    if digest != build['candidate_sha256']:
        raise SystemExit('image hash disagrees with build.json')
    reports = {}
    for name, p in manifest.validation_reports(data):
        report = json.loads(p.read_text(encoding='utf-8'))
        if report.get('status') != 'passed':
            raise SystemExit(f'validation not passed: {p}')
        if report.get('image_sha256', digest) != digest:
            raise SystemExit(f'report belongs to another image: {p}')
        reports[name] = report
    for name, want in build['source_sha256'].items():
        if manifest.sha256(ROOT / 'native' / name) != want:
            raise SystemExit(f'source changed since build: {name}')
    if manifest.source_hashes(data) != bundle['source_sha256']:
        raise SystemExit('manifest sources changed since bundle verification')
    missing = [str(p) for _, p in manifest.evidence_files(data) if not p.is_file()]
    if missing:
        raise SystemExit('missing evidence: ' + ', '.join(missing))
    return bundle, build, reports, main, digest


def firmware_container(data, main):
    """Rebuild the installable firmware container from the validated main block."""
    sys.path.insert(0, str(ROOT / data['install']['firmware_package_dir']))
    import patch
    release = ROOT / data['install']['release_dir']
    spec = json.loads((release / 'patch.json').read_text())
    original = (ROOT / 'work' / patch.STOCK_NAME).read_bytes()
    base = (ROOT / data['image']['baseline_dir'] / 'caduceus-v0.26.2.bin').read_bytes()
    assert manifest.sha256(ROOT / 'work' / patch.STOCK_NAME) == spec['stock_sha256']
    assert manifest.sha256(ROOT / data['image']['baseline_dir'] /
                           'caduceus-v0.26.2.bin') == spec['result_sha256']
    comp = patch.parse(base)[0]
    trailer = bytearray(comp['trl'])
    struct.pack_into('<I', trailer, 28,
                     (-patch.wordsum(comp['hdr']) - patch.wordsum(main)
                      - patch.wordsum(trailer[:28])) & 0xffffffff)
    updated = comp['hdr'] + patch.encode(main) + trailer
    candidate = updated + base[len(updated):]
    assert len(candidate) == len(original)
    components = patch.parse(candidate)
    assert patch.decode(components[0]['enc']) == main
    assert candidate[len(updated):] == base[len(updated):]
    # Check the complete container, not only the changed main component.
    for label, raw in [('stock', original), ('games', candidate)]:
        for i, c in enumerate(patch.parse(raw)):
            total = patch.wordsum(c['hdr']) + patch.wordsum(patch.decode(c['enc'])) + patch.wordsum(c['trl'])
            assert total & 0xffffffff == 0, (label, i, 'component checksum')
    return candidate, spec


def readme(data, bundle, reports):
    lines = [
        f"# Experimental Games bundle for OM SYSTEM OM-3",
        '',
        'OM-3 firmware 1.1 / E147 build 1100 only, based on Caduceus '
        f"{data['install']['caduceus']}. **Tested in OM-Emu; never tested on a "
        'physical camera.** This is an unofficial, experimental firmware '
        'modification, including Caduceus photo/film features. Read '
        '`INSTALL_AND_RESTORE.md` before installing and '
        '`HARDWARE_RISK_REVIEW.md` for the remaining risks. '
        '`UPSTREAM_INSTALL.md` is the bundled upstream reference.',
        '',
        'One firmware image carries every game behind a single Games row in '
        'Picture Mode:',
        '',
        '| Game |',
        '| --- |',
    ]
    for game in data['games']:
        lines.append(f"| {game['title']} |")
    lines += [
        '',
        '## Installing together with other games',
        '',
        'The camera accepts exactly one `DCOLYMP/E1479999.BIN`. Game code '
        'lives in the firmware main block, not in the `OM3MOD` data files, so '
        'two game packages cannot be installed side by side: the last '
        'firmware written wins. Coexistence means one combined image with one '
        'launcher. See `COMBINING_GAMES.md` and `BUNDLE_ARCHITECTURE.md` for '
        'the contract used to add a game.',
        '',
        'Copy the contents of `card/` to the SD root. No optional film presets '
        'are needed. Keep existing custom LOOKS/EDITS/BUNDLES files if present. '
        'The separate `restore/DCOLYMP/E1479999.BIN` is original firmware 1.1; '
        'see `INSTALL_AND_RESTORE.md` for full installation and rollback steps.',
        '',
        '## Playing',
        '',
        'From the Super Control Panel on COLOR1-4, open Picture Mode, scroll '
        'to **Games** at the end of the list and press OK. The launcher '
        f"offers {', '.join(data['launcher']['entries'])}; arrows or either "
        'dial change the selection, OK enters.',
    ]
    for game in data['games']:
        lines += ['', f"### {game['title']}", '',
                  '| Input | Action |', '| --- | --- |']
        lines += [f'| {key} | {action} |' for key, action in game['controls']]
        for issue in game.get('known_issues', []):
            lines += ['', f'Known issue `{issue}`: see `KNOWN_ISSUES.md`.']
    lines += [
        '',
        '## Camera-safety design',
        '',
        '- Puzzle games are event driven. Mario and Breakout share a cancellable timer that '
        'posts to the GUI task; no heap or full pixel framebuffer is used.',
        f"- The added loaded section is {bundle['extension_used_bytes']:,} "
        f"bytes of a {data['image']['extension_limit_bytes']:,}-byte ceiling; "
        f"the linked `.text` blob is {bundle['linked_blob_bytes']:,} bytes.",
        '- Display output changes and real screen transitions clear Games '
        'state and pass the event back to the stock camera handler.',
        '- Breakout is button-only. All game touch interception and gesture code '
        'have been removed; ordinary touch messages use the original camera handler.',
        '',
        '## What was verified',
        '',
        f"All registered validation reports passed against main image "
        f"`{bundle['main_image_sha256']}`:",
        '',
    ]
    for name, report in reports.items():
        detail = ', '.join(f'{k}={v}' for k, v in report.items()
                           if k in ('cases', 'frames') and v is not None)
        lines.append(f'- `{name}`{": " + detail if detail else ""}')
    lines += [
        '',
        '## Limitations',
        '',
        '- Emulator evidence is not hardware evidence. Drawing latency, real '
        'button timing, buffer lifetime and concurrent key behaviour need a '
        'physical camera.',
        '- Known issues are listed in `KNOWN_ISSUES.md`.',
        '',
    ]
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dry-run', action='store_true',
                    help='validate every input and print the plan; write nothing')
    args = ap.parse_args()
    data = manifest.load()
    bundle, build, reports, main, digest = verify(data)
    dest = ROOT / 'artifacts' / data['install']['package_name']
    archive = dest.with_suffix('.zip')
    print(f'Games: {", ".join(g["title"] for g in data["games"])}')
    print(f'Main image: {digest}')
    print(f'Validation reports: {len(reports)}')
    print(f'Evidence files: {len(manifest.evidence_files(data))}')
    print(f'Package target: {dest.relative_to(ROOT)}')
    if args.dry_run:
        print('Dry run only: no package was written.')
        return

    if dest.exists() or archive.exists():
        raise SystemExit('release target already exists; use a new package_name to preserve it')
    candidate, spec = firmware_container(data, main)
    for folder in ('card/DCOLYMP', 'card/OM3MOD', 'restore/DCOLYMP',
                   'evidence', 'source'):
        (dest / folder).mkdir(parents=True, exist_ok=True)
    firmware = dest / data['install']['firmware_path']
    firmware.write_bytes(candidate)
    restore = dest / 'restore/DCOLYMP/E1479999.BIN'
    shutil.copyfile(ROOT / 'work' / spec['stock_file'], restore)
    assert manifest.sha256(restore) == spec['stock_sha256']
    release = ROOT / data['install']['release_dir']
    checks = {Path(line.split()[1].lstrip('*')).name: line.split()[0]
              for line in (release / 'SHA256SUMS').read_text().splitlines() if line.strip()}
    for name in data['install']['version_matched_card_files']:
        assert manifest.sha256(release / name) == checks[name], name
        shutil.copyfile(release / name, dest / 'card/OM3MOD' / name)
    looks = data['install']['optional_default_looks']
    assert manifest.sha256(release / looks) == checks[looks]
    # No optional film presets in the button-only games release.

    for name, src in manifest.evidence_files(data):
        shutil.copyfile(src, dest / 'evidence' / name)
    source_paths = set(manifest.source_paths(data)) | {f'native/{name}' for name in build['source_sha256']}
    for rel in sorted(source_paths):
        shutil.copyfile(ROOT / rel, dest / 'source' / Path(rel).name)
    for p in (ROOT / 'native/bundle').glob('*.py'):
        (dest / 'source/bundle').mkdir(exist_ok=True)
        shutil.copyfile(p, dest / 'source/bundle' / p.name)
    shutil.copyfile(manifest.MANIFEST, dest / 'source/bundle/games.json')
    for rel in data['licenses'] + [f"native/{Path(p).name}" for p in data['docs']]:
        shutil.copyfile(ROOT / rel, dest / Path(rel).name)
    (dest / 'README.md').write_text(readme(data, bundle, reports), encoding='utf-8')
    shutil.copyfile(ROOT / 'vendor/caduceus-om3/docs/INSTALL.md', dest / 'UPSTREAM_INSTALL.md')
    shutil.copyfile(ROOT / 'native/bundle/Verify-Package.ps1', dest / 'Verify-Package.ps1')

    load_end = struct.unpack_from(
        '<I', main,
        int(data['image']['load_end_site'], 16) - int(data['image']['extension_base'], 16))[0]
    bundle_manifest = {
        'schema': data['schema'],
        'package': data['install']['package_name'],
        'target': {'camera': 'OM SYSTEM OM-3', 'firmware': '1.1',
                   'model': 'E147', 'build': 1100},
        'baseline': {'caduceus': data['install']['caduceus'],
                     'stock_firmware': spec['stock_file'],
                     'stock_sha256': spec['stock_sha256'],
                     'caduceus_bin_sha256': spec['result_sha256'],
                     'main_image_sha256': digest},
        'installable_firmware': {'path': data['install']['firmware_path'],
                                'sha256': manifest.sha256(firmware)},
        'stock_restore': {'path': 'restore/DCOLYMP/E1479999.BIN',
                          'sha256': manifest.sha256(restore),
                          'unmodified_official_firmware': True},
        'container_checks': {'all_component_checksums': 'passed',
                             'decoded_main_matches_tested_image': True,
                             'other_components_match_pinned_caduceus': True},
        'card_files': {
            'version_matched': data['install']['version_matched_card_files'],
            'keep_existing': data['install']['keep_existing_card_files'],
            'optional_default_looks': None},
        'extension': {'base': data['image']['extension_start'],
                      'limit_bytes': data['image']['extension_limit_bytes'],
                      'used_bytes': load_end - int(data['image']['extension_start'], 16),
                      'linked_blob_bytes': bundle['linked_blob_bytes']},
        'launcher': {'entries': len(data['launcher']['entries']),
                     'back_index': data['launcher']['back_index'],
                     'entries_order': data['launcher']['entries'],
                     'state_ids': data['launcher']['state_ids']},
        'games': [{'name': g['title'], 'id': g['id'],
                   'state_id': g['state_id'], 'buffer': g['buffer'],
                   'sources': g.get('sources', []),
                   'tests': g.get('tests', []),
                   'known_issues': g.get('known_issues', [])}
                  for g in data['games']],
        'integration': {'single_firmware_only': True,
                        'combine_at_build_time': True,
                        'manifest': 'native/bundle/games.json',
                        'build_driver': data['image']['builder'],
                        'contract': 'BUNDLE_ARCHITECTURE.md'},
        'validation': {'status': 'passed', 'emulator_only': True,
                       'reports': {n: r.get('checks', r.get('cases', r.get('frames')))
                                   for n, r in reports.items()}},
        'source_sha256': build['source_sha256'],
    }
    (dest / 'games-bundle.json').write_text(
        json.dumps(bundle_manifest, indent=2) + '\n', encoding='utf-8')

    files = sorted(p for p in dest.rglob('*') if p.is_file())
    (dest / 'SHA256SUMS').write_text(
        ''.join(f"{manifest.sha256(p)}  {p.relative_to(dest).as_posix()}\n" for p in files),
        encoding='ascii')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zf:
        for p in files + [dest / 'SHA256SUMS']:
            zf.write(p, Path(dest.name) / p.relative_to(dest))
    # Read the archive back: CRC and every archived file must match SHA256SUMS.
    with zipfile.ZipFile(archive) as zf:
        assert zf.testzip() is None, 'archive CRC failure'
        for p in files:
            name = (Path(dest.name) / p.relative_to(dest)).as_posix()
            assert hashlib.sha256(zf.read(name)).hexdigest() == manifest.sha256(p), name
    archive.with_suffix('.zip.sha256').write_text(
        f'{manifest.sha256(archive)}  {archive.name}\n', encoding='ascii')
    print(f'Wrote {archive.relative_to(ROOT)} ({len(files) + 1} files)')


if __name__ == '__main__':
    main()
