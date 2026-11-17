"""Native compact 2048: full raster, worst-case bound, ABI and cost vs R2."""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[1] / "native"), str(_Path(__file__).resolve().parents[1] / "tests")]
import json, os, random, struct, subprocess, zlib
from pathlib import Path
from mines_assets import FONT  # Includes F, supplied to the combined build by Mario.

R=Path(__file__).resolve().parents[1]; B=R/'work/native-build'
O=R/'work/compact-games/2048-render'; O.mkdir(parents=True,exist_ok=True)
rng=random.Random(2048)
cases=[([e]*16,12345678,0) for e in range(18)]
cases += [([255]*16,99999999,0), (list(range(2,18)),2048,2),
          ([1,2,1,2,2,1,2,1]*2,98765432,1)]
cases += [([rng.randrange(18) for _ in range(16)],rng.randrange(100000000),i%4) for i in range(16)]

def expected(board,score,flags):
    pixels=bytearray([7])*(384*480)
    for cell,e in enumerate(board):
        ox=(cell%4)*96; oy=48+(cell//4)*96
        for y in range(6,96):
            start=(oy+y)*384+ox+6;pixels[start:start+90]=bytes([10])*90
        if not e:continue
        text=str(1<<min(e,17)); scale=min(6,80//(4*len(text)-1))
        x0=ox+6+(90-(4*len(text)-1)*scale)//2
        for i,ch in enumerate(text):
            for gy,row in enumerate(FONT[ch]):
                for gx,bit in enumerate(row):
                    if bit!='1':continue
                    for yy in range(6):
                        start=(oy+36+gy*6+yy)*384+x0+(i*4+gx)*scale
                        pixels[start:start+scale]=bytes([7])*scale
    bottom='GAME OVER  INFO NEW GAME' if flags&1 else ('2048! KEEP PLAYING' if flags&2 else 'ARROWS MOVE  INFO NEW')
    for oy,text in [(0,f'2048 SCORE {score:08}'),(432,bottom)]:
        for i,ch in enumerate(text.ljust(32)):
            for gy,row in enumerate(FONT.get(ch,FONT[' '])):
                for gx,bit in enumerate(row):
                    if bit!='1':continue
                    for yy in range(3):
                        start=(oy+12+gy*3+yy)*384+i*12+1+gx*3
                        pixels[start:start+3]=bytes([10])*3
    return pixels

def decode(raw,size):
    assert raw[:4]==struct.pack('<I',0x0b17f1df)
    pixels=bytearray()
    for off in range(4,size,8):
        word=int.from_bytes(raw[off:off+8],'little');assert word>>60==0
        for shift in range(0,60,12):
            token=(word>>shift)&4095;length=(token&15)+1
            assert len(pixels)%384+length<=384
            pixels.extend([token>>4]*length)
    assert len(pixels)==384*480
    return pixels

def save_png(path,pixels):
    colors={7:bytes.fromhex('087d80'),10:bytes.fromhex('ff8080')}
    raw=b''.join(b'\0'+b''.join(colors[p] for p in pixels[y*384:(y+1)*384]) for y in range(480))
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',384,480,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))

results={}
for label,directory in [('r2','work/combined-game'),('compact','work/compact-games')]:
    G=R/directory;meta=json.loads((G/'build.json').read_text());s=meta['symbols'];cap=meta['resources']['compressed_board_capacity']
    spec=[]
    for i,(board,score,flags) in enumerate(cases):
        state=bytes(board)+struct.pack('<4I',score,0x6d2b79f5,0,flags)
        spec.append(dict(name=str(i),pc='B',regs=dict(d2=0x2222,d3=0x3333,a2=0x4444,a3=0x5555),
            mem=[['B','dd000000000004cb'],['B+1','='+str(s['paint'])+'-B'],[s['game_state'],state.hex()],
                 [s['board_buffer_end'],'dec0ad0b']],stop=['B+7'],max=500000,
            read=[[s['board_buffer'],cap+4],[s['game_state'],40]]))
    (O/(label+'-spec.json')).write_text(json.dumps(spec))
    env=dict(os.environ,OM_EMU_MODEL='E147',NCALL=str(O/(label+'-spec.json')),NOUT=str(O/(label+'-results.json')))
    for k in ('WATCH','GAME_STATE','GAME_GC','WRANGE','WSTACK'):env.pop(k,None)
    with (O/(label+'.log')).open('w') as f:
        subprocess.run(['node',str(B/'replay.mjs'),(R/'work/om-emu/emu').as_uri(),str(G/'row-main.bin'),str(B/'paired.omsd'),
            str(O/(label+'.json')),str(O/(label+'.omsd')),'s1 ncall'],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=300)
    j=json.loads((O/(label+'-results.json')).read_text());checked=[]
    assert len(j['out'])==len(cases)
    for i,(result,case) in enumerate(zip(j['out'],cases)):
        assert result['steps']<500000
        assert int(result['regs']['sp'],16)==int(j['SP'],16)
        for reg,val in spec[i]['regs'].items():assert int(result['regs'][reg],16)==val
        raw=bytes.fromhex(result['mem'][0]);assert raw[-4:]==bytes.fromhex('dec0ad0b')
        state=bytes.fromhex(result['mem'][1]);assert state[:32].hex()==spec[i]['mem'][2][1]
        size=struct.unpack_from('<I',state,36)[0];assert 4<size<=cap
        pixels=decode(raw,size)
        if label=='compact':
            assert pixels==expected(*case),f'Raster mismatch in case {i}'
            if i==19:save_png(O/'large-digits.png',pixels)
        checked.append(dict(bytes=size,steps=result['steps'],stack=result['stackBytes']))
    assert not json.loads((O/(label+'.json')).read_text())['engineErrors']
    results[label]=checked
    print(label,len(checked),'native frames verified',flush=True)

for old,new in zip(results['r2'],results['compact']):
    assert new['steps']<=old['steps'],(old,new)
    assert new['stack']<=old['stack'],(old,new)
assert max(x['bytes'] for x in results['compact'])==cap,'Worst-case allocation bound not exercised'
report=dict(status='PASS',candidate_sha256=meta['candidate_sha256'],frames=len(cases),pixel_exact=True,
    sentinels_intact=True,max_output_bytes=cap,stack_bytes_max=max(x['stack'] for x in results['compact']),
    instruction_reduction_percent=[round(100*(1-b['steps']/a['steps']),1) for a,b in zip(results['r2'],results['compact'])])
(O/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
