"""Read-only firmware audit. Writes JSON evidence, never firmware."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def audit(stock, baseline, layout):
    def digest(data):
        return hashlib.sha256(data).hexdigest()
    if digest(stock) != layout['stock_main_sha256']:
        raise ValueError('stock digest does not match pinned input')
    if digest(baseline) not in (layout['r5_main_sha256'], layout.get('extras_main_sha256')):
        raise ValueError('baseline digest does not match pinned input')
    if len(stock) != len(baseline):
        raise ValueError('main block lengths differ')
    notation, runtime = (int(layout[k], 0) for k in ['notation_base', 'runtime_base'])
    functions = {}
    for name, rec in layout['functions'].items():
        at = int(rec['notation'], 0)
        offset = at - notation
        expected = bytes.fromhex(rec['expected'])
        if stock[offset:offset + len(expected)] != expected:
            raise ValueError(f'{name}: expected stock bytes mismatch')
        if baseline[offset:offset + len(expected)] != expected:
            raise ValueError(f'{name}: baseline overlaps candidate function prefix')
        functions[name] = {**rec, 'offset': hex(offset), 'runtime': hex(runtime + offset),
                           'verified_bytes': len(expected), 'abi_verified': False}
    region = layout['candidate_region']
    start, end = (int(region[k], 0) for k in ['offset_start', 'offset_end'])
    if not 0 <= start < end <= len(baseline):
        raise ValueError('invalid candidate region')
    if any(x != 255 for x in baseline[start:end]):
        raise ValueError('candidate region contains occupied bytes')
    return {'schema': 1, 'status': 'static-audit-only',
            'stock_sha256': digest(stock), 'baseline_sha256': digest(baseline),
            'functions': functions, 'globals': layout['globals'],
            'candidate_region': {**region, 'bytes': end-start,
                                 'runtime_start': hex(runtime+start),
                                 'runtime_end': hex(runtime+end),
                                 'loader_verified': False, 'ownership_verified': False},
            'camera_ready': False}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stock', type=Path, default=ROOT/'work/om-emu/unpacked/E147/OLY_E_147_1100_0000_0000.BIN.blk00000000.OE.0100.bin')
    ap.add_argument('--baseline', type=Path, default=ROOT/'work/current-games/row-main.bin')
    ap.add_argument('--out', type=Path, default=ROOT/'work/shutter-sound/audit.json')
    args = ap.parse_args()
    report = audit(args.stock.read_bytes(), args.baseline.read_bytes(),
                   json.loads(Path(__file__).with_name('layout.json').read_text()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(f"PASS {len(report['functions'])} function prefixes; {report['candidate_region']['bytes']} erased candidate bytes; {args.out}")


if __name__ == '__main__':
    main()
