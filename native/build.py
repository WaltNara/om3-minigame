"""Layer an experimental native game onto the exact Caduceus v0.26.2 release.
Build output stays in work/native-build until emulator validation succeeds.
Uses Caduceus's Apache-2.0 container/patch implementation; see vendor NOTICE.
"""
import hashlib
import json
import pathlib
import re
import struct
import subprocess
import sys
import zlib
import assets

ROOT = pathlib.Path(__file__).resolve().parents[1]
UP = ROOT / 'vendor/caduceus-om3'
OUT = ROOT / 'work/native-build'
sys.path.insert(0, str(UP / 'firmware'))
import patch

BASE, START, END = 0x60021020, 0x60f59800, 0x60f99800
RECORD = 0x615adcc4
FONT = {
 '1':['010','110','010','010','111'], '2':['110','001','010','100','111'],
 '3':['110','001','010','001','110'], '4':['101','101','111','001','001'],
 '5':['111','100','110','001','110'], '6':['011','100','111','101','111'],
 '7':['111','001','010','010','010'], '8':['111','101','111','101','111'],
 '9':['111','101','111','001','110'],
 'G':['0111','1000','1011','1001','0111'], 'U':['1001','1001','1001','1001','0110'],
 'E':['111','100','110','100','111'], 'S':['0111','1000','0110','0001','1110'],
 'I':['111','010','010','010','111'], 'N':['1001','1101','1011','1001','1001'],
 'F':['111','100','110','100','100'], 'O':['0110','1001','1001','1001','0110'],
 'C':['0111','1000','1000','1000','0111'], 'H':['101','101','111','101','101'],
 'K':['1001','1010','1100','1010','1001'], 'T':['111','010','010','010','010'],
 'L':['100','100','100','100','111'], 'W':['10001','10001','10101','10101','01010'],
 'Y':['101','101','010','010','010'], ' ':['00']*5,
}

def picture(guess, status):
    pixels = bytearray([7] * (175 * 50))
    for y0, text in [(5, f'GUESS {guess}'), (29, ['INFO CHECK','TOO LOW','TOO HIGH','YOU WIN'][status])]:
        x0 = 6
        for ch in text:
            glyph = FONT[ch]
            for y, row in enumerate(glyph):
                for x, bit in enumerate(row):
                    if bit == '1':
                        for dy in range(3):
                            for dx in range(3):
                                pixels[(y0+y*3+dy)*175+x0+x*3+dx] = 10
            x0 += (len(glyph[0])+1)*3
        assert x0 <= 175
    tokens, i = [], 0
    while i < len(pixels):
        run = 1
        # OSD's decoder rejects a run that spans scanlines.
        while run < min(16, 175-i%175) and i+run < len(pixels) and pixels[i+run] == pixels[i]:
            run += 1
        tokens.append(pixels[i]*16 + run-1)
        i += run
    data = bytearray(struct.pack('<I', 49 | (174 << 12) | (11 << 24)))
    for i in range(0, len(tokens), 5):
        data += sum(t << (12*j) for j, t in enumerate(tokens[i:i+5])).to_bytes(8, 'little')
    return data

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    spec = json.loads((UP / 'releases/v0.26.2/patch.json').read_text())
    stock = (ROOT / 'work' / patch.STOCK_NAME).read_bytes()
    assert patch.sha(stock) == spec['stock_sha256']
    basefile = OUT / 'caduceus-v0.26.2.bin'
    if not basefile.exists():
        basefile.write_bytes(patch.apply(stock, spec))
    basepkg = basefile.read_bytes()
    assert patch.sha(basepkg) == spec['result_sha256']
    comp = patch.parse(basepkg)[0]
    image = bytearray(patch.decode(comp['enc']))
    (OUT / 'base-main.bin').write_bytes(image)
    u32 = lambda addr: struct.unpack_from('<I', image, addr-BASE)[0]
    original = {name: u32(RECORD+offset) for name, offset in [('init',4),('info',44),('event',36)]}
    assert image[0x60415216-BASE] == 0xdc
    original['trig'] = 0x60415216 + struct.unpack_from('<i',image,0x60415217-BASE)[0]
    assert image[0x6125becc-BASE]==0xdc
    original['pm'] = 0x6125becc + struct.unpack_from('<i',image,0x6125becd-BASE)[0]
    assert image[0x610f6016-BASE]==0xdc
    original['gx'] = 0x610f6016 + struct.unpack_from('<i',image,0x610f6017-BASE)[0]
    assert image[0x610f784f-BASE:0x610f7854-BASE] == bytes.fromhex('86432c4728')
    assert all(u32(RECORD+56*k+4)==original['init'] for k in range(4))
    # Branch targets must remain unresolved until link time. An assembler .set
    # makes GAS encode the absolute value as a PC-relative displacement.
    targets = {**{f'original_{k}':v for k,v in original.items()}, 'facade':0x60b8696a,
               'original_bitmap_resume':0x610f7854}
    (OUT / 'original.inc').write_text(''.join(f'.extern {k}\n' for k in targets) +
        '.set GDESC, 0xa49ecdf8\n.set GSELECT, 0xa49edf88\n', encoding='ascii')
    resources = assets.make(OUT/'assets.inc')
    tc = ROOT / 'work/toolchain'
    subprocess.run([str(tc/'gas/as-new.exe'), '-I', str(OUT), '-o', str(OUT/'game.o'), str(ROOT/'native/2048.s')], check=True)
    subprocess.run([str(tc/'ld/ld-new.exe'), '-Ttext', hex(START), '-e', 'game_init',
        *[f'--defsym={k}={v}' for k,v in targets.items()],
        '-o', str(OUT/'game.elf'), str(OUT/'game.o')], check=True)
    subprocess.run([str(tc/'binutils/objcopy.exe'), '-O','binary','-j','.text',str(OUT/'game.elf'),str(OUT/'game.bin')],check=True)
    symbols = subprocess.check_output([str(tc/'binutils/nm-new.exe'),str(OUT/'game.elf')],text=True)
    sy = {p[2]:int(p[0],16) for line in symbols.splitlines() if len(p:=line.split())==3}
    # Regression guard: inspect final machine code, not just source symbols.
    dis = subprocess.check_output([str(tc/'binutils/objdump.exe'),'-d',
        f'--stop-address={sy["game_state"]}',str(OUT/'game.elf')],text=True)
    destinations = [int(x,16) for x in re.findall(r'\b(?:calls|call|jmp)\s+([0-9a-f]+)\s',dis)]
    assert all(START<=v<sy['game_state'] or v in targets.values() for v in destinations)
    assert set(targets.values()) <= set(destinations)
    blob = (OUT/'game.bin').read_bytes()
    assert START+len(blob) <= END
    assert set(image[START-BASE:END-BASE]) == {255}
    assert u32(0x60045e9c) == START
    # Copy only the used 2 KiB pages from the camera-proven extension range.
    # Loading the entire 256 KiB probe range would waste RAM and boot copying.
    loaded_end=START+((len(blob)+0x7ff)//0x800)*0x800
    assert loaded_end<=END
    struct.pack_into('<I', image, 0x60045e9c-BASE, loaded_end)
    image[START-BASE:START-BASE+len(blob)] = blob
    hooks = {4:'game_init',12:'game_up',16:'game_down',20:'game_left',24:'game_right',36:'game_event',44:'game_info'}
    for offset, symbol in hooks.items():
        struct.pack_into('<I', image, RECORD+offset-BASE, sy[symbol])
    for k in range(1,4):
        struct.pack_into('<I', image, RECORD+56*k+4-BASE, sy['other_init'])
    struct.pack_into('<i',image,0x60415217-BASE,sy['leave_game']-0x60415216)
    struct.pack_into('<i',image,0x6125becd-BASE,sy['game_nav']-0x6125becc)
    struct.pack_into('<i',image,0x610f6017-BASE,sy['game_transition']-0x610f6016)
    image[0x610f784f-BASE:0x610f7854-BASE] = b'\xdc'+struct.pack('<i',sy['game_bitmap']-0x610f784f)
    (OUT/'main.bin').write_bytes(image)
    # Replace only component zero, keeping Caduceus's other components intact.
    trailer = bytearray(comp['trl'])
    struct.pack_into('<I', trailer, 28, (-patch.wordsum(comp['hdr'])-patch.wordsum(image)-patch.wordsum(trailer[:28])) & 0xffffffff)
    updated = comp['hdr'] + patch.encode(image) + trailer
    candidate = updated + basepkg[len(updated):]
    assert len(candidate) == len(stock)
    check = patch.parse(candidate)[0]
    assert patch.decode(check['enc']) == image
    assert (patch.wordsum(check['hdr'])+patch.wordsum(image)+patch.wordsum(check['trl'])) & 0xffffffff == 0
    (OUT/'candidate.bin').write_bytes(candidate)
    report = {'status':'built; emulator validation pending; not camera-tested', 'upstream_commit':'f4d2569eb46817795ec5ffaf931ba058d2c0d029',
      'stock_sha256':patch.sha(stock),'base_sha256':patch.sha(basepkg),'candidate_sha256':patch.sha(candidate),
      'main_sha256':patch.sha(image),'game_bytes':len(blob),'symbols':sy,'original':original,
      'loader_end':hex(loaded_end),'proven_extension_limit':hex(END),'record':hex(RECORD),'hooks':hooks,
      'resources':{**resources,'total_loaded_bytes':len(blob),'additional_section_copy_bytes':loaded_end-START,
                   'mutable_state_bytes':sy['tile_rows']-sy['game_state']}}
    (OUT/'build.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ['symbols','hooks']}))

if __name__ == '__main__':
    main()
