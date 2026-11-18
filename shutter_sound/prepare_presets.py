"""Prepare local shutter banks and listening previews from presets.json.

Downloads require --fetch. Personal originals stay in place; generated outputs
and third-party downloads live under work/. No camera files are installed.
"""
import argparse
from array import array
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen

from bank import RATE, MAX_FRAMES, make_wav, encode, decode
from convert import convert

ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path(__file__).with_name('presets.json')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def samples(pcm):
    values = array('h')
    values.frombytes(pcm)
    if sys.byteorder != 'little':
        values.byteswap()
    return values


def pcm_bytes(values):
    values = array('h', values)
    if sys.byteorder != 'little':
        values.byteswap()
    return values.tobytes()


def camera_edit(pcm, duration_ms):
    """Keep the first significant shutter onset, then fade a bounded excerpt."""
    values = samples(pcm)
    if not values:
        raise ValueError('empty recording')
    peak = max(abs(x) for x in values)
    if peak < 64:
        raise ValueError('recording is effectively silent')
    threshold = max(64, peak*0.10)
    onset = next(i//2 for i in range(0, len(values), 2)
                 if max(abs(values[i]), abs(values[i+1])) >= threshold)
    start = max(0, onset-48)  # retain 1 ms before transient
    end = min(len(values)//2, start+round(duration_ms*RATE/1000))
    out = values[2*start:2*end]
    gain = min(1, 16384/max(abs(x) for x in out))
    frames = len(out)//2
    for i in range(frames):
        fade = min(1, i/24, (frames-1-i)/96)
        for c in range(2):
            out[2*i+c] = round(out[2*i+c]*gain*fade)
    return pcm_bytes(out), start/RATE


def burst_preview(pcm, fps=10, shots=10):
    """Offline preview of restart semantics, never a camera timing claim."""
    period = round(RATE/fps)
    if shots*period > MAX_FRAMES:
        raise ValueError('preview exceeds bank duration bound')
    out = bytearray(shots*period*4)
    for shot in range(shots):
        # Copy only until the next shot; cut the old tail rather than mix it.
        segment = pcm[:period*4]
        at = shot*period*4
        out[at:at+len(segment)] = segment
    return bytes(out)


def ffmpeg_path(explicit=None):
    if explicit:
        return explicit
    found = shutil.which('ffmpeg')
    if found:
        return found
    deps = ROOT/'work/shutter-sound/python-deps'
    if deps.is_dir():
        sys.path.insert(0, str(deps))
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as exc:
        raise ValueError('Supply --ffmpeg PATH or install imageio-ffmpeg into work/shutter-sound/python-deps') from exc


def build(out, ffmpeg, fetch=False, public_only=False):
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    if catalog['default'] != 'silent' or catalog['silent']['bank'] is not None:
        raise ValueError('Silent must be the default and must not require a sound bank')
    entries = [{**catalog['silent'], 'frames': 0, 'behavior': 'no custom playback request'}]
    out.mkdir(parents=True, exist_ok=True)
    sources = [source for source in catalog['sources'] if not public_only or source['kind'] == 'camera']
    for source in sources:
        path = ROOT/source['file']
        if not path.exists() and fetch and source.get('download'):
            data = urlopen(source['download'], timeout=30).read(4*1024*1024+1)
            if sha(data) != source['sha256']:
                raise ValueError(f"{source['id']}: downloaded hash mismatch")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        raw = path.read_bytes()
        if source.get('sha256') and sha(raw) != source['sha256']:
            raise ValueError(f"{source['id']}: source hash mismatch")
        result = subprocess.run([str(ffmpeg), '-nostdin', '-v', 'error', '-i', str(path),
                                 '-vn', '-ac', '2', '-ar', str(RATE), '-f', 's16le', 'pipe:1'],
                                capture_output=True, timeout=60, check=True)
        pcm = result.stdout
        variants = [('burst', 60), ('single', 300)] if source['kind'] == 'camera' else [('full', None)]
        for variant, ms in variants:
            if ms:
                edited, start = camera_edit(pcm, ms)
            else:
                # Preserve complete personal clips, including trailing audio.
                edited = convert(make_wav(pcm))
                start = None
            key = source['id']+'-'+variant
            bank = encode(edited)
            info = decode(bank)
            (out/(key+'.BIN')).write_bytes(bank)
            (out/(key+'.wav')).write_bytes(info['wav'])
            duration_ms = info['frames']/48
            record = {'id': key, 'label': source['label']+' '+variant.title(),
                      'bank': key+'.BIN', 'preview': key+'.wav', 'frames': info['frames'],
                      'duration_ms': duration_ms, 'source_start_seconds': start,
                      'source_duration_ms': len(pcm)/192,
                      'source_sha256': sha(raw), 'bank_sha256': sha(bank),
                      'pcm_sha256': sha(edited), 'source': source.get('source', source['file']),
                      'license': source['license'], 'kind': source['kind'],
                      'at_10fps': 'fits between shots' if duration_ms < 100 else 'interrupted by following shot',
                      'edits': 'onset selection, crop, peak limit and edge fades' if ms else 'leading silence trim, peak limit and edge fades; no tail truncation'}
            for fps in [10, 20]:
                name = f'{key}-{fps}fps.wav'
                (out/name).write_bytes(make_wav(burst_preview(edited, fps=fps)))
                record[f'preview_{fps}fps'] = name
            entries.append(record)
    report = {'schema': 1, 'default': 'silent', 'camera_ready': False,
              'preview_scope': 'offline restart simulation; no native playback or cadence proof',
              'ffmpeg': str(ffmpeg), 'presets': entries}
    (out/'presets.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    (out/'CREDITS.txt').write_text('\n\n'.join(
        f"{s['label']}: {s.get('creator', 'user supplied')}\n{s.get('source', s['file'])}\n{s['license']}\n{s.get('license_url', '')}"
        for s in sources)+'\n\nDerived clips were trimmed/faded/level-limited and converted to PCM16 stereo 48 kHz.\n', encoding='utf-8')
    print(json.dumps([{'id': x['id'], 'ms': x.get('duration_ms', 0)} for x in entries], indent=2))
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, default=ROOT/'work/shutter-sound/presets')
    ap.add_argument('--ffmpeg')
    ap.add_argument('--fetch', action='store_true', help='download missing pinned public recordings')
    ap.add_argument('--public-only', action='store_true', help='prepare the built-in recordings without personal files')
    args = ap.parse_args()
    build(args.out, ffmpeg_path(args.ffmpeg), args.fetch, args.public_only)


if __name__ == '__main__':
    main()
