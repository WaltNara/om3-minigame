"""Actual MN10300 CPU rule checks and full camera UI replays; stdlib only."""
import hashlib
import json
import os
from pathlib import Path
import random
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work/native-build'
build=json.loads((OUT/'build.json').read_text()); sy=build['symbols']
env=dict(os.environ,OM_EMU_MODEL='E147',GAME_STATE=f"{sy['game_state']:x}")
env.pop('WATCH',None)
env['GAME_GC']=f"{sy['game_gc']:x}"
if os.environ.get('NATIVE_TRACE'):env['WATCH']=f"{sy['game_bitmap']:x}"

def run(name,script,extra=None):
    with (OUT/f'{name}.log').open('w',encoding='utf-8') as log:
        r=subprocess.run(['node',str(OUT/'replay.mjs'),(ROOT/'work/om-emu/emu').as_uri(),str(OUT/'main.bin'),
            str(OUT/'paired.omsd'),str(OUT/f'{name}.json'),str(OUT/f'{name}-saved.omsd'),script],
            cwd=ROOT,env={**env,**(extra or {})},stdout=log,stderr=subprocess.STDOUT)
    if r.returncode:
        print((OUT/f'{name}.log').read_text()[-5000:]); raise SystemExit(r.returncode)
    return json.loads((OUT/f'{name}.json').read_text())

def lines(direction):
    if direction==0:return [[y*4+x for y in range(4)] for x in range(4)]
    if direction==1:return [[y*4+x for y in range(3,-1,-1)] for x in range(4)]
    if direction==2:return [[y*4+x for x in range(4)] for y in range(4)]
    return [[y*4+x for x in range(3,-1,-1)] for y in range(4)]

def reference(board,direction,score=0):
    out=board.copy()
    for indices in lines(direction):
        values=[board[i] for i in indices if board[i]]; result=[]; i=0
        while i<len(values):
            v=values[i]
            if i+1<len(values) and v==values[i+1]:
                v+=1; score+=1<<v; i+=1
            result.append(v); i+=1
        for index,value in zip(indices,result+[0]*4):out[index]=value
    return out,score,int(out!=board)

def call_spec(label,function,board,direction=0,score=0,seed=0x6d2b79f5):
    state=bytes(board)+struct.pack('<IIII',score,seed,0,0)
    return {'name':label,'pc':'B','regs':{'d0':direction,'d2':0x2222,'d3':0x3333,'a2':0x4444,'a3':0x5555},
            'mem':[['B','dd000000000004cb'],['B+1','='+str(sy[function])+'-B'],[sy['game_state'],state.hex()]],
            'stop':['B+7'],'max':300000,'read':[[sy['game_state'],40]]}

def core():
    rand=random.Random(2048); cases=[]; expected=[]
    boards=[[0]*16,[1,1,1,1]+[0]*12,[1,1,2,0]+[0]*12,[2,2,2,2]*4,
            [10,10,0,0]+[0]*12,[16,16,0,0]+[0]*12,[1,2,1,2,2,1,2,1]*2]
    boards += [[rand.choice([0,0,0,1,1,2,3,4,5,6]) for _ in range(16)] for _ in range(128)]
    for board in boards:
        for direction in range(4):
            cases.append(call_spec(str(len(cases)),'slide',board,direction,score=1234))
            expected.append(('slide',reference(board,direction,1234)))
    dead=[1,2,1,2,2,1,2,1]*2
    for b,flags in [(dead,1),([11]+dead[1:],3),([0]+dead[1:],0),([1]*16,0),([11]*16,2)]:
        cases.append(call_spec(str(len(cases)),'check_over',b));expected.append(('flags',flags))
    for seed in range(1,65):
        b=[1]*16;b[3]=b[12]=0
        cases.append(call_spec(str(len(cases)),'spawn',b,seed=seed));expected.append(('spawn',b))
    cases.append(call_spec(str(len(cases)),'spawn',dead));expected.append(('full',dead))
    cases.append(call_spec(str(len(cases)),'new_round',dead,score=888));expected.append(('new',None))
    for b,score in [([0]*16,0),([1,2,3,4]*4,2048),(list(range(2,18)),12345678)]:
        cs=call_spec(str(len(cases)),'paint',b,score=score)
        cs['mem'].append([sy['board_buffer_end'],'dec0ad0b'])
        cs['read'] += [[sy['board_buffer'],build['resources']['compressed_board_capacity']+4],[sy['score_digits'],8]]
        cases.append(cs);expected.append(('paint',score))
    for b,dir in [([1]+[0]*15,0),([1]+[0]*15,3),(dead,2)]:
        cs=call_spec(str(len(cases)),'play_move',b,direction=dir)
        cases.append(cs);expected.append(('play',(b,dir)))
    (OUT/'core-spec.json').write_text(json.dumps(cases))
    run('core','s1 ncall',{'NCALL':str(OUT/'core-spec.json'),'NOUT':str(OUT/'core-results.json')})
    results=json.loads((OUT/'core-results.json').read_text())['out']
    for result,(kind,want) in zip(results,expected):
        assert result['steps']<300000,result
        for reg,v in [('d2',0x2222),('d3',0x3333),('a2',0x4444),('a3',0x5555)]:
            assert int(result['regs'][reg],16)==v,(result['name'],reg,result['regs'])
        raw=bytes.fromhex(result['mem'][0]); b=list(raw[:16]); score=struct.unpack_from('<I',raw,16)[0]
        flags=struct.unpack_from('<I',raw,28)[0]; retval=int(result['regs']['d0'],16)
        if kind=='slide':assert (b,score,retval)==want,(result['name'],(b,score,retval),want)
        elif kind=='flags':assert flags==want,(b,flags,want)
        elif kind=='spawn':
            changed=[i for i in range(16) if b[i]!=want[i]]
            assert len(changed)==1 and changed[0] in (3,12) and b[changed[0]] in (1,2),(b,want)
        elif kind=='full':assert b==want and retval==0
        elif kind=='new':assert sum(v!=0 for v in b)==2 and max(b)<=2 and score==0 and flags==0
        elif kind=='paint':
            data=bytes.fromhex(result['mem'][1]); assert data[-4:]==bytes.fromhex('dec0ad0b')
            size=struct.unpack_from('<I',raw,36)[0]
            assert 0<size<=build['resources']['compressed_board_capacity']
            assert bytes.fromhex(result['mem'][2]).decode()==f'{want:08}'
            pixels=0
            for off in range(4,size,8):
                word=int.from_bytes(data[off:off+8],'little');assert word>>60==0
                for shift in range(0,60,12):
                    token=(word>>shift)&4095; length=(token&15)+1
                    assert pixels%256+length<=256,'RLE crosses row'
                    pixels+=length
            assert pixels==256*320
        elif kind=='play':
            prev,direction=want; slid,sc,changed=reference(prev,direction)
            assert score==sc
            if not changed:
                assert b==prev and struct.unpack_from('<I',raw,20)[0]==0x6d2b79f5
                assert struct.unpack_from('<I',raw,24)[0]==0
            else:
                differences=[i for i in range(16) if b[i]!=slid[i]]
                assert len(differences)==1 and slid[differences[0]]==0 and b[differences[0]] in (1,2)
                assert struct.unpack_from('<I',raw,24)[0]==1
    report={'candidate_sha256':build['candidate_sha256'],'native_cpu_cases':len(results),
            'slide_steps_max':max(v['steps'] for v in results[:len(boards)*4]),
            'core_stack_bytes_max':max(v['stackBytes'] for v in results),
            'render_steps_max':max(v['steps'] for v,(k,w) in zip(results,expected) if k=='paint'),'status':'passed'}
    (OUT/'core-validation.json').write_text(json.dumps(report,indent=2));print(report)

def ui():
    r=run('2048-ui',os.environ.get('UI_SCRIPT','s1 vals ok ok down shot:work/native-build/2048-start.png left up right down main+1 main-1 sub+1 sub-1 shot:work/native-build/2048-playing.png info hold:ok shot:work/native-build/2048-reset.png menu s1 vals'))
    for e in r['log']:print(e['step'],e['game'],e['score'],e['moves'],e['active'],e['gui'],e.get('gdesc'))
    if os.environ.get('UI_SCRIPT'):return
    b=[0]*16;seed=0x6d2b79f5;score=0;moves=0;started=False
    def rand():
        nonlocal seed
        seed^=(seed<<13)&0xffffffff;seed^=seed>>17;seed^=(seed<<5)&0xffffffff
        return seed
    def spawn():
        empty=[i for i in range(16) if b[i]==0]
        if empty:
            at=empty[((rand()&65535)*len(empty))>>16]
            b[at]=2 if ((rand()&65535)*10)>>16==0 else 1
    dirs={'up':0,'down':1,'left':2,'right':3,'main+1':0,'main-1':1,'sub+1':2,'sub-1':3}
    for e in r['log']:
        t=e['step']
        if t=='down' and not started or t=='hold:ok':
            b=[0]*16;score=0;moves=0;spawn();spawn();started=True
        elif started and t in dirs:
            b,score,changed=reference(b,dirs[t],score)
            if changed:moves+=1;spawn()
        assert (e['game'],e['score'],e['rng'],e['moves'])==(b,score,seed,moves),(t,e,b,score,seed,moves)
    vals=[json.loads(line[5:]) for line in (OUT/'2048-ui.log').read_text().splitlines() if line.startswith('VALS ')]
    assert len(vals)==2
    assert [x.rsplit('/',2)[0] for x in vals[0]]==[x.rsplit('/',2)[0] for x in vals[1]],vals
    slots=[e['slots'] for e in r['log'] if 'slots' in e]
    assert all(v==slots[0] for v in slots),'Camera look settings changed'
    menu=next(e for e in r['log'] if e['step']=='menu')
    assert menu['active']==0 and menu['gdesc']==[4022,'a49ebe40'] and menu['gselect']==[4471,'a49ece10']
    assert r['log'][-1]['gui']=='SS_COMMON/ID_ST_CA_REQ_DISP'
    assert not r['engineErrors'],r['engineErrors']
    import zlib
    def panel(name):
        png=(OUT/name).read_bytes();o=8;data=b''
        while o<len(png):
            n=int.from_bytes(png[o:o+4],'big')
            if png[o+4:o+8]==b'IDAT':data+=png[o+8:o+8+n]
            o+=n+12
        raw=zlib.decompress(data);stride=2701
        return b''.join(raw[y*stride+1+322*3:y*stride+1+578*3] for y in range(120,440))
    panels=[panel(n) for n in ['2048-start.png','2048-playing.png','2048-reset.png']]
    assert len(set(panels))==3,'Screens did not change with the board'
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    report={'status':'passed in om-emu; NOT camera-tested','candidate_sha256':build['candidate_sha256'],
            'steps':len(r['log']),'checks':['all four arrows','both dials','score and spawning match reference',
                'restart','INFO leaves board unchanged','MENU restores both guides','live view exit',
                'photo settings unchanged','three distinct rendered boards','no OSD engine errors'],
            'source_sha256':{p.name:sha(p) for p in (ROOT/'native').iterdir() if p.is_file()}}
    (OUT/'2048-validation.json').write_text(json.dumps(report,indent=2));print('UI PASS')

if __name__=='__main__':
    {'core':core,'ui':ui}[sys.argv[1]]()
