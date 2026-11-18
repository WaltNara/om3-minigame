"""Build native Shutter sound settings and capture playback on the five-game r5 image."""

import json
from pathlib import Path
import struct
import subprocess

from bank import KEY, decode, make_wav
from memory import BASE, WORK, aligned, sha


OUT = WORK / 'shutter-sound' / 'native'
TC = WORK / 'toolchain'
SOURCE = Path(__file__).resolve().parent
CHOICES = ('Silent', '5D', 'D850', 'Ciallo', 'Man', 'Custom')
CODE_START = 0x60F59800
WAV_START = 0x6031F000
WAV_END = WAV_START + 32 * 1024
WAV_LOADER_END = 0x60045E84
SD_BUFFER = 0x60326000
SD_MAX_BYTES = 112 + 48000 * 4


def labels():
    for table, names in (
        ('choice_labels', CHOICES),
        ('edit_labels', tuple(f'< {label} >' for label in CHOICES)),
        ('error_labels', ('No WAV on card', 'Invalid WAV', 'Player busy')),
    ):
        yield '.balign 4'
        yield f'{table}: .long ' + ','.join(f'{table}_{i}' for i in range(len(names)))
        for i, label in enumerate(names):
            yield f'{table}_{i}: .short ' + ','.join(str(ord(c)) for c in label) + ',0'


def build():
    layout = json.loads((SOURCE / 'layout.json').read_text())
    game_dir = WORK / 'current-games'
    meta = json.loads((game_dir / 'build.json').read_text())
    original = (game_dir / 'row-main.bin').read_bytes()
    digest = sha(original)
    if digest != layout['r5_main_sha256'] or digest != meta['candidate_sha256']:
        raise ValueError('Expected the camera-tested five-game r5 image')
    image = bytearray(original)

    def read(address, size):
        return bytes(image[address - BASE:address - BASE + size])

    def patch(address, expected, replacement):
        if len(expected) != len(replacement) or read(address, len(expected)) != expected:
            raise ValueError(f'Unexpected layout at {address:#x}')
        image[address - BASE:address - BASE + len(expected)] = replacement

    def branch(address, expected, name, call=False):
        before = bytes.fromhex(expected)
        code = b'\xdd' if call else b'\xdc'
        tail = before[-2:] if call else b'\xcb' * (len(before) - 5)
        patch(address, before, code + struct.pack('<i', symbols[name] - address) + tail)

    end = aligned(SD_BUFFER + SD_MAX_BYTES + 1)
    if end > BASE + int(layout['candidate_region']['offset_end'], 0):
        raise ValueError('Sound overlay exceeds the section-1 erased run')
    if read(WAV_START, end - WAV_START).count(255) != end - WAV_START:
        raise ValueError('Section-1 sound storage is occupied')
    patch(WAV_LOADER_END, struct.pack('<I', WAV_START), struct.pack('<I', end))

    defs = dict(meta['symbols'])
    defs.update(native_set_variable=0x610CD5C4, native_keys_resume=0x612540EE,
                native_panel_id=0x6037E8CC, native_gui_state=0x603713BC,
                ui_flag=0x60042FCA, set_flag=0x6004CD21, ui_wait_resume=0x6017B799,
                ui_complete_resume=0x6017B7C3,
                ui_stock_exec=0x6017B861, ui_request=0x6017B9DE,
                ui_resource_size=0x601D7546, ui_size_resume=0x6017BB25,
                ui_wave_resume=0x6017BB88, get_drive=0x603F0111, ui_end=0x6017BD85,
                ui_close_only=0x6017BDAF,
                audio_wait=0x60A8537C, audio_end_resume=0x60AE18B4,
                stock_prepare_player=0x60ADE989,
                copy_resume=0x60ADCCAB,
                capbuf_append=0x60BBE8C0, capbuf_taken_picture=0x60BC1F9A,
                capbuf_main_resume=0x60BBF690, capbuf_fast_resume=0x60BC22C0,
                through_permit=0x601F1FBD, through_resume=0x601F1EA3,
                fopen=0x608D4D22, fread=0x608D4EB7, fclose=0x608D4D2B,
                sd_buffer=SD_BUFFER + 0x40000000, wav_limit=SD_MAX_BYTES)
    pos = WAV_START
    presets = {}
    for label, name, filename in (('5D', 'wave_5d', 'canon5d-burst.BIN'),
                                  ('D850', 'wave_d850', 'nikond850-burst.BIN')):
        clip = decode((OUT.parent / 'presets' / filename).read_bytes())
        wav = bytearray(clip['wav'])
        key = wav.index(KEY)
        wav[key:key + len(KEY)] = b'PRM_AUD_SHUT1_VOL\0'.ljust(len(KEY), b'\0')
        if pos + len(wav) > WAV_END or (pos + clip['data_offset']) % 16:
            raise ValueError(f'{label} exceeds aligned WAV storage')
        patch(pos, b'\xff' * len(wav), wav)
        defs[name] = pos + 0x40000000
        defs[name + '_bytes'] = len(wav)
        presets[label] = dict(frames=clip['frames'], pcm_sha256=sha(clip['pcm']))
        pos = (pos + len(wav) + 15) & -16

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'native_labels.inc').write_text('\n'.join(labels()) + '\n', encoding='ascii')
    header = make_wav(bytes(4))[:-4]
    if len(header) != 112 or header.index(KEY) % 4:
        raise ValueError('Unexpected canonical WAV header')
    (OUT / 'native_wav.inc').write_text(
        f'.set wav_key_offset,{header.index(KEY)}\nsd_wav_header: .byte '
        + ','.join(map(str, header)) + '\n', encoding='ascii')
    objects = []
    sources = [SOURCE / (name + '.s') for name in ('native_menu', 'choice', 'sd_choice', 'capture_sound')]
    sources.append(SOURCE.parent / 'native' / 'game_preview.s')
    for source in sources:
        obj = OUT / (source.stem + '.o')
        subprocess.run([TC / 'gas/as-new.exe', '-I', OUT, '-o', obj, source], check=True)
        objects.append(obj)
    imports = set()
    for obj in objects:
        imports.update(line.split()[-1] for line in subprocess.check_output(
            [TC / 'binutils/nm-new.exe', '-u', obj], text=True).splitlines())
    elf, blob = OUT / 'shutter.elf', OUT / 'shutter.bin'
    subprocess.run([TC / 'ld/ld-new.exe', '-Ttext', hex(pos), '-e', 'es_menu_keys',
                    *(f'--defsym={name}={defs[name]}' for name in sorted(imports & defs.keys())),
                    '-o', elf, *objects], check=True)
    subprocess.run([TC / 'binutils/objcopy.exe', '-O', 'binary', '-j', '.text', elf, blob], check=True)
    payload = blob.read_bytes()
    if pos + len(payload) >= SD_BUFFER:
        raise ValueError('Sound code crosses into the SD WAV buffer')
    patch(pos, b'\xff' * len(payload), payload)
    symbols = dict(meta['symbols'])
    for line in subprocess.check_output([TC / 'binutils/nm-new.exe', '-g', elf], text=True).splitlines():
        addr, kind, name = line.split()
        if kind == 'T':
            symbols[name] = int(addr, 16)

    # Setup / Information Record. Extend the native labels, help and cursor
    # tables without changing the existing settings or Game launcher.
    mode = 0x7E01
    old_keys = (5072, 179, 3356)
    lists = []
    pos = (pos + len(payload) + 3) & -4

    def allocate(data):
        nonlocal pos
        start = pos
        pos = (start + len(data) + 3) & -4
        if pos > SD_BUFFER:
            raise ValueError('Menu data crosses into the SD WAV buffer')
        patch(start, b'\xff' * len(data), data)
        return start

    for address, title in ((0x6158797C, b'ES sound'),
                           (0x61586FEC, b'OK to choose. Arrows to change. MENU to cancel.')):
        rows = read(address, 36)
        if tuple(struct.unpack_from('<I', rows, i)[0] for i in (0, 12, 24)) != old_keys:
            raise ValueError('Unexpected Setup rows')
        literal = allocate(title + b'\0')
        lists.append(allocate(rows + struct.pack('<IHHI', mode, 5, 0, literal)))
    patch(0x61587E8C, struct.pack('<3I', 3, 0x6158797C, 0x61586FEC),
          struct.pack('<3I', 4, *lists))
    order = allocate(struct.pack('<4H', *old_keys, mode))
    patch(0x6152960C, struct.pack('<HHI', 0, 3, 0x615294CA), struct.pack('<HHI', 0, 4, order))

    branch(0x612540E9, 'cff0f8fecc', 'es_menu_keys')
    branch(0x611FFC91, 'dd33d9ecffa010', 'es_menu_view', call=True)
    branch(0x610F6016, 'dcba40e6ffcb', 'es_menu_transition')
    branch(0x6017B78F, '80ff4204fcacca2f0460', 'es_wait')
    patch(0x6017B79C, b'\x85\x07', b'\x85\x17')
    branch(0x6017B7BE, 'cdc7050048', 'es_stock_complete')
    branch(0x6017B857, 'f8e204aa04', 'es_dispatch')
    branch(0x6017BB13, 'dd762e9600e03c', 'es_prepare_player', call=True)
    branch(0x6017BB1A, 'f0678002dd28ba0500e010', 'es_wave')
    branch(0x60BBF68B, 'cd35f2f01c', 'es_capture_main')
    branch(0x60BC22BB, 'cddffc2014', 'es_capture_fast')
    branch(0x60AE18AD, 'ddcf3afafff038', 'es_end_wait')
    branch(0x60ADCCA6, '430c421c0c', 'es_rewind_copy')
    branch(0x601F1E9E, 'cd1f01e010', 'game_preview_permit')

    # Keep the accepted game overlay (including assets and row tables) exact.
    games_end = CODE_START + meta['extension_bytes']
    if read(CODE_START, games_end - CODE_START) != original[CODE_START - BASE:games_end - BASE]:
        raise ValueError('Game overlay differs from r5')
    output = dict(meta, base_sha256=meta['candidate_sha256'], candidate_sha256=sha(image),
                  host='picture-mode', sound_menu='inline', mode=mode, symbols=symbols, presets=presets,
                  capture_sites=[0x60BBF68B, 0x60BC22BB], single_exposure=True,
                  burst_exposure=True, sd_custom=True, sd_max_bytes=SD_MAX_BYTES,
                  game_preview_gate=0x601F1E9E,
                  wave_start=WAV_START, wave_end=end,
                  scope='Native Setup labels and CapBuf requests for Silent Single and Silent Sequential')
    (OUT / 'row-main.bin').write_bytes(image)
    (OUT / 'build.json').write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    print(f"Built {output['candidate_sha256']} in {OUT}")


if __name__ == '__main__':
    build()
