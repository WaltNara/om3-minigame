"""Single build + validation entry point for the combined Games image.

Driven entirely by games.json. It runs the existing firmware composer, then
every registered validation script, then cross-checks all reports against the
built image and writes bundle-build.json. It deliberately never packages:
the camera installs one firmware, so the final zip is emitted once, after all
games are finished, by package.py.
"""
import argparse
import hashlib
import json
import struct
import subprocess
import sys

import manifest

ROOT = manifest.ROOT


def run(script):
    print('==>', script, flush=True)
    subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, check=True)


def main():
    data = manifest.load()
    out = ROOT / data['image']['output_dir']
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-existing',action='store_true',
                        help='verify matching source/image/report hashes without rebuilding or replaying')
    args=parser.parse_args()
    if not args.verify_existing:
        run(data['image']['builder'])
        for test in manifest.tests(data):
            run(test)

    reports = {}
    for name, p in manifest.validation_reports(data):
        report = json.loads(p.read_text(encoding='utf-8'))
        if report.get('status') != 'passed':
            raise SystemExit(f'validation not passed: {p}')
        reports[name] = report

    image = (out / data['image']['main_image']).read_bytes()
    digest = hashlib.sha256(image).hexdigest()
    load_site = int(data['image']['load_end_site'], 16)
    base_addr = int(data['image']['extension_base'], 16)
    load_end = struct.unpack_from('<I', image, load_site - base_addr)[0]
    used = load_end - int(data['image']['extension_start'], 16)
    if not 0 < used <= data['image']['extension_limit_bytes']:
        raise SystemExit(f'extension outside budget: {used} bytes')
    build = json.loads((out / data['image']['build_metadata']).read_text())
    if digest != build['candidate_sha256']:
        raise SystemExit('image hash disagrees with build.json')
    for name, report in reports.items():
        if report.get('image_sha256', digest) != digest:
            raise SystemExit(f'validation report belongs to another image: {name}')
    for name, want in build['source_sha256'].items():
        if manifest.sha256(ROOT / 'native' / name) != want:
            raise SystemExit(f'source changed since build: {name}')

    summary = {
        'status': 'passed',
        'schema': data['schema'],
        'packaging': 'separate command: native/bundle/package.py',
        'main_image_sha256': digest,
        'main_image_bytes': len(image),
        'linked_blob_bytes': (out / 'row.bin').stat().st_size,
        'extension_used_bytes': used,
        'launcher': {'entries': data['launcher']['entries'],
                     'back_index': data['launcher']['back_index'],
                     'state_ids': data['launcher']['state_ids']},
        'games': manifest.game_summary(data),
        'validation_reports': {name: {'status': r['status'],
                                      'cases': r.get('cases'),
                                      'frames': r.get('frames'),
                                      'checks': r.get('checks')}
                               for name, r in reports.items()},
        'source_sha256': manifest.source_hashes(data),
        'evidence_files': [name for name, _ in manifest.evidence_files(data)],
        'notes': ['emulator only; not camera-tested',
                  'no installable package was produced by this command'],
    }
    dest = manifest.metadata_path(data)
    dest.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(f'Bundle build + validation passed: {digest}')
    print(f'Wrote {dest.relative_to(ROOT)} (run package.py separately to package)')


if __name__ == '__main__':
    main()
