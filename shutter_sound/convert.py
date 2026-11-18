"""Convert a PCM WAV to the experimental OM-3 sound bank, or generate a click."""
import argparse
import math
from pathlib import Path
import struct

from bank import RATE, MAX_FRAMES, MAX_SECONDS, decode, encode, read_wav


def convert(wav):
    chunks = read_wav(wav)
    fmt = chunks.get(b'fmt ', (0, b''))[1]
    pcm = chunks.get(b'data', (0, b''))[1]
    if len(fmt) != 16:
        raise ValueError('input must have standard PCM fmt')
    codec, channels, rate, byte_rate, align, bits = struct.unpack('<HHIIHH', fmt)
    if codec != 1 or channels not in (1, 2) or bits != 16 or not 8000 <= rate <= 192000 or align != channels*2 or byte_rate != rate*align:
        raise ValueError('input must be PCM16 mono/stereo at 8..192 kHz')
    if not pcm or len(pcm) % align:
        raise ValueError('input has incomplete PCM frames')
    values = list(struct.unpack('<'+'h'*(len(pcm)//2), pcm))
    frames = [values[i:i+channels] for i in range(0, len(values), channels)]
    # Remove leading silence only; never silently truncate a long source clip.
    first = next((i for i, f in enumerate(frames) if max(map(abs, f)) > 32), None)
    if first is None:
        raise ValueError('input is silent')
    frames = frames[first:]
    n = max(1, round(len(frames)*RATE/rate))
    if n > MAX_FRAMES:
        raise ValueError(f'trim source to at most {MAX_SECONDS} s after leading silence')
    peak = max(abs(v) for f in frames for v in f)
    gain = min(1, 16384/peak)
    out = []
    for i in range(n):
        pos = min(i*rate/RATE, len(frames)-1)
        left = int(pos)
        right = min(left+1, len(frames)-1)
        frac = pos-left
        fade = min(1, (i+1)/48, (n-i)/96)
        for c in range(2):
            ch = min(c, channels-1)
            value = frames[left][ch]*(1-frac)+frames[right][ch]*frac
            out.append(round(value*gain*fade))
    return struct.pack('<'+'h'*len(out), *out)


def click(duration_ms=100):
    if not 1 <= duration_ms <= MAX_SECONDS*1000:
        raise ValueError(f'click duration must be 1..{MAX_SECONDS*1000} ms')
    frames = round(RATE*duration_ms/1000)
    values = []
    state = 0x12345678
    for i in range(frames):
        state ^= (state << 13) & 0xffffffff
        state ^= state >> 17
        state ^= (state << 5) & 0xffffffff
        t = i/RATE
        env = min(1, i/24) * math.exp(-t/0.012) * min(1, (frames-i)/96)
        sample = round(6000*env*((state/0xffffffff-0.5)+0.5*math.sin(2*math.pi*900*t)))
        values.extend((sample, sample))
    return struct.pack('<'+'h'*len(values), *values)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument('--input', type=Path)
    source.add_argument('--click', action='store_true')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--sd', action='store_true', help='write a camera-ready WAV of at most one second')
    ap.add_argument('--click-ms', type=int, default=100, help='generated clip duration in ms (1..5000)')
    args = ap.parse_args()
    if args.input and args.input.stat().st_size > 4*1024*1024:
        ap.error('input exceeds 4 MiB; trim it on the PC first')
    try:
        if args.input and args.click_ms != 100:
            ap.error('--click-ms applies only to --click')
        bank = encode(click(args.click_ms) if args.click else convert(args.input.read_bytes()))
        info = decode(bank)
        if args.sd and info['frames'] > RATE:
            raise ValueError('trim the SD sound to at most 1 second after leading silence')
    except ValueError as exc:
        ap.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    output = info['wav'] if args.sd else bank
    args.out.write_bytes(output)
    print(f"Wrote {args.out} ({info['frames']} frames, {info['frames']/48:.1f} ms, {len(output)} bytes)")


if __name__ == '__main__':
    main()
