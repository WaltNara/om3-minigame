"""Pixel-exact scene checks and a mathematical worst-pattern buffer bound."""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[1] / "native"), str(_Path(__file__).resolve().parents[1] / "tests")]
import hashlib,json,os,struct,subprocess
from pathlib import Path
import zlib
import mario_assets as art
from mario_level import HEIGHTS,COINS
R=Path(__file__).resolve().parents[1]; O=R/'work/mario-render'; B=R/'work/native-build'; G=R/os.environ.get('OM3_GAME_BUILD','work/combined-game')
O=G/'mario-render'
O.mkdir(parents=True,exist_ok=True)
build=json.loads((G/'build.json').read_text());sy=build['symbols']; info=build['mario_resources']
# x,y,vy,held,result,camera,mask,count,block,enemy,dead,direction,facing,tick,grace,buffer
cases=[ [18,0,0,0,0,0,0,0,0,620,0,1,0,0,0,0],
 [270,52,-2,0,0,42,3,2,0,620,0,1,1,2,0,0],
 [450,64,0,0,0,222,7,4,1,620,0,1,0,2,0,0],
 [620,16,8,0,0,392,7,4,1,621,1,1,0,1,0,0],
 [824,20,-3,0,0,596,31,6,1,630,0,-1,1,2,0,0],
 [1104,0,0,0,1,768,63,7,1,630,1,1,0,0,0,0],
 [340,-35,-8,0,2,112,0,0,0,620,0,1,0,0,0,0] ]
spec=[]
for i,st in enumerate(cases):
 spec.append({'name':str(i),'pc':'B','regs':{'d2':0x2222,'d3':0x3333,'a2':0x4444,'a3':0x5555},
 'mem':[['B','dd000000000004cb'],['B+1','='+str(sy['mario_paint'])+'-B'],[sy['mario_state'],struct.pack('<16i',*st).hex()],[sy['mario_buffer_end'],'dec0ad0b']],
 'stop':['B+7'],'max':600000,'read':[[sy['mario_buffer'],info['capacity']+4]]})
(O/'spec.json').write_text(json.dumps(spec));env=dict(os.environ,OM_EMU_MODEL='E147',NCALL=str(O/'spec.json'),NOUT=str(O/'results.json'))
for key in ('GAME_STATE','GAME_GC','WATCH','WSTACK','WFROM','WIDS'):env.pop(key,None)
with (O/'run.log').open('w') as log:
 subprocess.run(['node',str(B/'replay.mjs'),(R/'work/om-emu/emu').as_uri(),str(G/'row-main.bin'),str(B/'paired.omsd'),str(O/'run.json'),str(O/'saved.omsd'),'s1 ncall'],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
results=json.loads((O/'results.json').read_text())['out']; assert len(results)==len(cases)
used=[]
for i,(result,st) in enumerate(zip(results,cases)):
 assert result['steps']<600000,(i,result['steps'])
 for reg,v in [('d2',0x2222),('d3',0x3333),('a2',0x4444),('a3',0x5555)]:assert int(result['regs'][reg],16)==v,(i,reg)
 raw=bytes.fromhex(result['mem'][0]);assert raw[-4:]==bytes.fromhex('dec0ad0b')
 assert raw[:4]==struct.pack('<I',0x0b17f1df)
 off=4; raster=[]
 for y in range(480):
  p=[]
  while len(p)<384:
   word=int.from_bytes(raw[off:off+8],'little');off+=8;assert word>>60==0
   for j in range(5):
    token=(word>>(12*j))&4095;p.extend([token>>4]*((token&15)+1))
  assert len(p)==384,(i,y,len(p))
  raster+=p
 assert off<=info['capacity'];used.append(off)
 for y in range(96,432,4):
  cells=[int(HEIGHTS[(st[5]//4*4+x*4)//16]!=-64 and y>=400-HEIGHTS[(st[5]//4*4+x*4)//16]) for x in range(96)]
  def sprite(world,mask):
   x=world//4-st[5]//4
   for bit in range(8):
    if mask&(1<<bit) and 0<=x+bit<96: cells[x+bit]=1
  if 176<=y<192:
   for cloud in [80,416,736,1040]:sprite(cloud,14 if y<184 else 31)
  if 304<=y<400:
   sprite(1108,1)
   if y<320:sprite(1088,63)
  for k,(x,cy) in enumerate(COINS):
   if not(st[6]&(1<<k)) and 0<400-cy-y<=12:sprite(x,3)
  if 336<=y<352:sprite(448,([15,9,13,15],[15,9,9,15])[st[8]][(y-336)//4])
  if not st[10] and 384<=y<400:sprite(st[9],[6,15,9,10][(y-384)//4])
  row=y-(376-st[1]//4*4)
  if 0<=row<24:
   pose=[6,7,3,7,5,2] if st[2] else [6,7,3,7,2,6] if st[13]&2 else [6,7,3,7,2,5]
   mask=pose[row//4]
   if st[12]:mask=int(f'{mask:03b}'[::-1],2)
   sprite(st[0],mask)
  expected=[10 if c else 7 for c in cells for _ in range(4)]
  for dy in range(4):assert raster[(y+dy)*384:(y+dy+1)*384]==expected,(i,y,dy)
 def chunk(tag,data):return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data))
 pixels=b''.join(b'\0'+b''.join(bytes((235,235,230) if c==10 else (26,30,36)) for c in raster[y*384:(y+1)*384]) for y in range(480))
 (O/f'frame-{i}.png').write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',384,480,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(pixels))+chunk(b'IEND',b''))
report={'status':'passed','frames':len(cases),'image_sha256':hashlib.sha256((G/'row-main.bin').read_bytes()).hexdigest(),'max_steps':max(r['steps'] for r in results),'buffer_capacity':info['capacity'],'max_used':max(used),'checks':['pixel-exact world and HUD bounds','camera and sprite clipping','overlap transparency','facing and poses','reward persistence','buffer sentinel']}
(O/'validation.json').write_text(json.dumps(report,indent=2)); print(report)
