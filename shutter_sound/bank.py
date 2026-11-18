"""Experimental one-slot sound bank v1; no camera loader exists yet.

Header: <8s magic, u32 version, u32 payload length, 32s SHA256>.
Payload: canonical PCM16 stereo 48 kHz RIFF, direct-short-sound IKEY,
with samples aligned to 16 bytes relative to the payload. The loader must
also align the payload address. Lengths and checksum are checked before use.
"""
import hashlib
import struct

MAGIC = b'OM3SND\0\0'
HEADER = struct.Struct('<8sII32s')
RATE, MAX_SECONDS = 48000, 5
MAX_FRAMES = RATE * MAX_SECONDS
KEY = b'PRM_AUD_CSHUT1_VOL\0'


def chunk(tag, data):
    return tag + struct.pack('<I', len(data)) + data + b'\0' * (len(data) & 1)


def make_wav(pcm):
    if len(pcm) % 4 or not 4 <= len(pcm) <= MAX_FRAMES * 4:
        raise ValueError(f'PCM must contain 1..{MAX_FRAMES} stereo frames (up to {MAX_SECONDS} s)')
    fmt = chunk(b'fmt ', struct.pack('<HHIIHH', 1, 2, RATE, RATE*4, 4, 16))
    # The native parser supports LIST/INFO; pad INAM rather than adding JUNK.
    for pad in range(16):
        info = chunk(b'LIST', b'INFO'+chunk(b'INAM', b'OM3 custom\0'+bytes(pad))+chunk(b'IKEY', KEY))
        prefix = b'WAVE' + fmt + info
        if (8+len(prefix)+8) % 16 == 0:
            break
    else:
        raise ValueError('cannot align WAV')
    body = prefix + chunk(b'data', pcm)
    return b'RIFF' + struct.pack('<I', len(body)) + body


def read_wav(wav):
    if len(wav) < 12 or wav[:4] != b'RIFF' or wav[8:12] != b'WAVE':
        raise ValueError('not a RIFF WAVE')
    if struct.unpack_from('<I', wav, 4)[0] != len(wav)-8:
        raise ValueError('RIFF length mismatch')
    chunks, at = {}, 12
    while at < len(wav):
        if at+8 > len(wav):
            raise ValueError('truncated chunk header')
        tag, size = struct.unpack_from('<4sI', wav, at)
        start, end = at+8, at+8+size
        if end+(size & 1) > len(wav):
            raise ValueError('truncated chunk')
        if tag in chunks and tag in (b'fmt ', b'data', b'LIST'):
            raise ValueError('duplicate required chunk')
        chunks[tag] = (start, wav[start:end])
        at = end+(size & 1)
    return chunks


def encode(pcm):
    payload = make_wav(pcm)
    return HEADER.pack(MAGIC, 1, len(payload), hashlib.sha256(payload).digest()) + payload


def decode(bank):
    if not HEADER.size <= len(bank) <= HEADER.size + MAX_FRAMES*4 + 512:
        raise ValueError('bank length outside bounds')
    magic, version, size, sha = HEADER.unpack_from(bank)
    if magic != MAGIC or version != 1 or size != len(bank)-HEADER.size:
        raise ValueError('invalid bank header')
    payload = bank[HEADER.size:]
    if hashlib.sha256(payload).digest() != sha:
        raise ValueError('payload checksum mismatch')
    chunks = read_wav(payload)
    expected_fmt = struct.pack('<HHIIHH', 1, 2, RATE, RATE*4, 4, 16)
    if chunks.get(b'fmt ', (None, None))[1] != expected_fmt:
        raise ValueError('unsupported PCM format')
    offset, pcm = chunks.get(b'data', (-1, b''))
    if offset % 16 or len(pcm) % 4 or not 4 <= len(pcm) <= MAX_FRAMES*4:
        raise ValueError('invalid PCM size or alignment')
    if payload != make_wav(pcm):
        raise ValueError('noncanonical WAV metadata or sound key')
    return {'wav': payload, 'pcm': pcm, 'data_offset': offset, 'frames': len(pcm)//4}
