"""Exercise Games navigation as native MN10300 instructions in OM-Emu."""
import json
import os
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'work/separate-games'
BUILD = ROOT/'work/native-build'
TC = ROOT/'work/toolchain'
START, BASE = 0x60f59800, 0x60021020
OUT.mkdir(parents=True,exist_ok=True)
subprocess.run([str(TC/'gas/as-new.exe'),'-o',str(OUT/'menu.o'),str(ROOT/'native/games_menu.s')],check=True)
subprocess.run([str(TC/'ld/ld-new.exe'),'-Ttext',hex(START),'-e','games_event',
                '-o',str(OUT/'menu.elf'),str(OUT/'menu.o')],check=True)
subprocess.run([str(TC/'binutils/objcopy.exe'),'-O','binary','-j','.text',str(OUT/'menu.elf'),str(OUT/'menu.bin')],check=True)
nm = subprocess.check_output([str(TC/'binutils/nm-new.exe'),str(OUT/'menu.elf')],text=True)
sy = {s[2]:int(s[0],16) for line in nm.splitlines() if len(s:=line.split())==3}
blob = (OUT/'menu.bin').read_bytes()
image = bytearray((BUILD/'base-main.bin').read_bytes())
assert set(image[START-BASE:START-BASE+len(blob)])=={255}
image[START-BASE:START-BASE+len(blob)]=blob
struct.pack_into('<I',image,0x60045e9c-BASE,START+((len(blob)+0x7ff)//0x800)*0x800)
(OUT/'menu-main.bin').write_bytes(image)
# Each case starts from a defined state; pairs test boundaries and passthrough.
cases = [
 (0,0,1,1,0,1), (0,1,2,0,1,0), (0,0,6,0,0,0),
 (1,0,2,1,1,1), (1,1,3,1,0,1), (1,0,4,2,0,2),
 (1,1,4,0,1,3), (1,0,5,0,0,3), (1,1,6,0,1,4),
 (2,0,5,1,0,1), (2,0,6,0,0,4), (2,0,2,2,0,0),
 (2,0,4,2,0,0), (1,0,99,1,0,0), (0,0,5,0,0,0)]
spec=[]
for i,(state,sel,event,*_) in enumerate(cases):
    spec.append({'name':str(i),'pc':'B','regs':{'d0':event,'d2':0x2222},
      'mem':[['B','dd000000000004cb'],['B+1','='+str(sy['games_event'])+'-B'],
             [sy['games_state'],bytes([state,sel]).hex()]],
      'stop':['B+7'],'max':2000,'read':[[sy['games_state'],2]]})
(OUT/'menu-spec.json').write_text(json.dumps(spec),encoding='utf-8')
env=dict(os.environ,OM_EMU_MODEL='E147',NCALL=str(OUT/'menu-spec.json'),NOUT=str(OUT/'menu-results.json'))
for key in ('GAME_STATE','GAME_GC','WATCH','WSTACK','WFROM','WIDS'):
    env.pop(key,None)
cmd=['node',str(BUILD/'replay.mjs'),(ROOT/'work/om-emu/emu').as_uri(),str(OUT/'menu-main.bin'),
     str(BUILD/'paired.omsd'),str(OUT/'menu-run.json'),str(OUT/'menu-saved.omsd'),'s1 ncall']
with (OUT/'menu.log').open('w',encoding='utf-8') as log:
    subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
results=json.loads((OUT/'menu-results.json').read_text())['out']
assert len(results)==len(cases)
for result,(_,_,_,state,sel,effect) in zip(results,cases):
    assert result['steps']<2000 and result['mem'][0]==bytes([state,sel]).hex(),result
    assert int(result['regs']['d0'],16)==effect and int(result['regs']['d2'],16)==0x2222,result
print(f'{len(results)} native Games navigation checks passed.')
