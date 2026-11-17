"""Historical r3 branch-only checks; NOT validation of a safe touch implementation.

r3 drops the application reply and deadlocks. Use test_flappy_touch_reply.py
for the repaired candidate and its native upstream producer/wait tests.
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[1] / "native"), str(_Path(__file__).resolve().parents[1] / "tests")]
import json,os,struct,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];G=R/'work/flappy-games';O=G/'touch-abi';O.mkdir(exist_ok=True)
B=R/'work/native-build';m=json.loads((G/'build.json').read_text());s=m['symbols']
# game,row,valid,root,kind,contact,pending,drain -> consume and resulting latch bytes.
cases=[
 ('press',6,1,1,123,1,0,0,0,True,(1,1,0)),
 ('held',6,1,1,123,1,1,0,0,True,(0,1,0)),
 ('move',6,1,1,123,2,1,0,0,True,(0,1,0)),
 ('release',6,1,1,123,3,1,0,0,True,(0,0,0)),
 ('unknown owned',6,1,1,123,9,0,0,0,True,(0,0,0)),
 ('2048 stock',2,1,1,123,1,0,0,0,False,(0,0,0)),
 ('launcher stock',1,1,1,123,3,0,0,0,False,(0,0,0)),
 ('shooting stock',0,0,0,0,3,0,0,0,False,(0,0,0)),
 ('invalid paint',6,1,0,123,1,0,0,0,False,(0,0,0)),
 ('invalid row',6,0,1,123,1,0,0,0,False,(0,0,0)),
 ('null root',6,1,1,0,1,0,0,0,False,(0,0,0)),
 ('interrupted release',1,1,1,123,3,0,0,1,True,(0,0,0)),
 ('fresh outside contact cancels drain',0,0,0,0,1,0,0,1,False,(0,0,0)),
 ('outside move preserves drain',0,0,0,0,2,0,0,1,False,(0,0,1)),
]
spec=[];payload=0xa1000000
for name,game,row,valid,root,kind,contact,pending,drain,consume,want in cases:
    spec.append(dict(name=name,pc=s['flappy_touch'],regs=dict(d0=0x1111,d1=0x2222,d2=0x3333,d3=0x4444,a0=0x61294d13,a1=0x6666,a2=0x7777,a3=payload,mdr=0x9876),
        mem=[[s['games_state'],bytes([game]).hex()],[s['games_row_selected'],bytes([row]).hex()],
             [s['games_paint_valid'],bytes([valid]).hex()],[s['games_screen'],struct.pack('<I',root).hex()],
             [payload,struct.pack('<4I',0x9100,0,0,payload+32).hex()],[payload+32,bytes([kind]).hex()],[s['flappy_pending'],bytes([pending,contact,drain]).hex()]],
        stop=[0x61294d13,0x61294e57],max=2000,read=[[s['flappy_pending'],3]]))
(O/'spec.json').write_text(json.dumps(spec));env=dict(os.environ,OM_EMU_MODEL='E147',NCALL=str(O/'spec.json'),NOUT=str(O/'results.json'))
for k in ('WATCH','GAME_STATE','GAME_GC','WRANGE','WSTACK'):env.pop(k,None)
with (O/'test.log').open('w') as f:
    subprocess.run(['node',str(B/'replay.mjs'),(R/'work/om-emu/emu').as_uri(),str(G/'row-main.bin'),str(B/'paired.omsd'),str(O/'replay.json'),str(O/'saved.omsd'),'s1 ncall'],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
j=json.loads((O/'results.json').read_text());assert len(j['out'])==len(cases)
for result,case,cs in zip(j['out'],cases,spec):
    consume=case[-2];regs={k:int(v,16) for k,v in result['regs'].items()}
    assert regs['sp']==int(j['SP'],16) and result['stackBytes']==12
    assert regs['pc']==(0x61294e57 if consume else 0x61294d13)
    for reg,val in cs['regs'].items():assert regs[reg]==(0 if consume and reg=='d2' else val),(case[0],reg)
    assert tuple(bytes.fromhex(result['mem'][0]))==case[-1],(case[0],result['mem'],case[-1])
assert not json.loads((O/'replay.json').read_text())['engineErrors']
(O/'validation.json').write_text(json.dumps(dict(status='PASS emulator only',cases=len(cases),stack_bytes=12,candidate_sha256=m['candidate_sha256']),indent=2))
print('PASS:',len(cases),'touch ownership/ABI/gesture cases')
