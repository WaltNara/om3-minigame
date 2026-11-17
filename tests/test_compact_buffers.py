"""Compare native render bytes, instruction counts and stack use to sealed R2.
Stress every Mines tile kind and cursor edges plus deterministic mixed boards.
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[1] / "native"), str(_Path(__file__).resolve().parents[1] / "tests")]
import json,os,random,struct,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'work/compact-games/parity';B=R/'work/native-build'
O.mkdir(parents=True,exist_ok=True)
cases=[]
for v in [0,32,64,*range(65,73),192]:
 for cursor in (0,63):cases.append(([v]*64,cursor,1,0,0,-1))
cases.append(([192]*64,63,5,0,0,63))
rng=random.Random(1611)
for i in range(16):cases.append(([rng.choice([0,32,64,*range(65,73),192]) for _ in range(64)],i*4,i%3*2+1,20,5,3))
results={}
for label,directory in [('r2','work/combined-game'),('compact','work/compact-games')]:
 G=R/directory;meta=json.loads((G/'build.json').read_text());s=meta['symbols'];cap=meta['mines_resources']['capacity']
 spec=[]
 for i,(board,cursor,flags,opened,flagged,boom) in enumerate(cases):
  state=struct.pack('<64B7i',*board,cursor,flags,opened,flagged,boom,0x6d2b79f5,0)
  spec.append(dict(name=str(i),pc='B',regs=dict(d2=0x2222,d3=0x3333,a2=0x4444,a3=0x5555),
   mem=[['B','dd000000000004cb'],['B+1','='+str(s['mines_paint'])+'-B'],[s['mines_board'],state.hex()],
        [s['mines_buffer_end'],'dec0ad0b']],stop=['B+7'],max=500000,
   read=[[s['mines_buffer'],cap+4],[s['mines_board'],92]]))
 (O/(label+'-spec.json')).write_text(json.dumps(spec))
 env=dict(os.environ,OM_EMU_MODEL='E147',NCALL=str(O/(label+'-spec.json')),NOUT=str(O/(label+'-results.json')))
 for k in ('WATCH','GAME_STATE','GAME_GC','WRANGE','WSTACK'):env.pop(k,None)
 with (O/(label+'.log')).open('w') as f:
  subprocess.run(['node',str(B/'replay.mjs'),(R/'work/om-emu/emu').as_uri(),str(G/'row-main.bin'),str(B/'paired.omsd'),
   str(O/(label+'.json')),str(O/(label+'.omsd')),'s1 ncall'],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=300)
 j=json.loads((O/(label+'-results.json')).read_text()); parsed=[]
 for result,case in zip(j['out'],cases):
  assert result['steps']<500000
  assert int(result['regs']['sp'],16)==int(j['SP'],16)
  for reg,val in spec[0]['regs'].items():assert int(result['regs'][reg],16)==val
  raw=bytes.fromhex(result['mem'][0]);assert raw[-4:]==bytes.fromhex('dec0ad0b')
  assert bytes.fromhex(result['mem'][1])[:64]==bytes(case[0])
  assert raw[:4]==struct.pack('<I',0x0b17f1df)
  offset=4
  for y in range(480):
   x=0
   while x<384:
    assert offset+8<=cap
    word=int.from_bytes(raw[offset:offset+8],'little');offset+=8
    assert word>>60==0
    x+=sum(((word>>(12*k))&15)+1 for k in range(5))
   assert x==384
  parsed.append((raw[:offset].hex(),result['steps'],result['stackBytes']))
 assert len(parsed)==len(cases)
 assert not json.loads((O/(label+'.json')).read_text())['engineErrors']
 results[label]=parsed;print(label,len(parsed),'native render frames verified',flush=True)
assert results['r2']==results['compact'],'bytes, instruction counts or stack changed'
(O/'validation.json').write_text(json.dumps(dict(status='PASS',frames=len(cases),
 byte_exact=True,instruction_counts_identical=True,stack_use_identical=True,sentinels_intact=True,
 max_output_bytes=max(len(x[0])//2 for x in results['compact'])),indent=2)+'\n')
print('PASS: exact render bytes, instruction counts, stack usage and intact end guards')
