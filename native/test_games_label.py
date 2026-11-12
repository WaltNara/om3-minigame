"""Verify shared Games footer on the unopened row, launcher and all games."""
import hashlib,json,os,subprocess
from pathlib import Path
import struct,zlib
def read_png(path):
 data=path.read_bytes();pos=8;packed=b""
 while pos<len(data):
  n=struct.unpack_from(">I",data,pos)[0];kind=data[pos+4:pos+8];chunk=data[pos+8:pos+8+n];pos+=12+n
  if kind==b"IHDR":w,h,depth,color,comp,filt,inter=struct.unpack(">IIBBBBB",chunk);assert depth==8 and color in (2,6) and inter==0
  if kind==b"IDAT":packed+=chunk
 bpp=3 if color==2 else 4;stride=w*bpp;raw=zlib.decompress(packed);rows=[];prev=bytearray(stride);pos=0
 for y in range(h):
  f=raw[pos];row=bytearray(raw[pos+1:pos+1+stride]);pos+=stride+1
  for x in range(stride):
   a=row[x-bpp] if x>=bpp else 0;b=prev[x];c=prev[x-bpp] if x>=bpp else 0
   if f==4:
    q=a+b-c;ds=[abs(q-a),abs(q-b),abs(q-c)];v=[a,b,c][ds.index(min(ds))]
   else:v=[0,a,b,(a+b)//2][f]
   row[x]=(row[x]+v)&255
  rows.append(row);prev=row
 return w,h,[[tuple(row[x*bpp:x*bpp+3]) for x in range(w)] for row in rows]
R=Path(__file__).resolve().parents[1]; G=R/'work/combined-game'; B=R/'work/native-build'; O=G/'label-review'
O.mkdir(exist_ok=True)
base=(B/'replay.mjs').read_text()
(O/'row.mjs').write_text(base)
script='s1 ok ok down '+('down '*12)+f'shot:{O.relative_to(R).as_posix()}/row.png'
env=dict(os.environ,OM_EMU_MODEL='E147')
for k in ('NCALL','NOUT','GAME_STATE','GAME_GC','WATCH','WSTACK','WFROM','WIDS'):env.pop(k,None)
with (O/'row.log').open('w') as log:
 subprocess.run(['node',str(O/'row.mjs'),(R/'work/om-emu/emu').as_uri(),str(G/'row-main.bin'),str(B/'paired.omsd'),str(O/'row.json'),str(O/'row.omsd'),script],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
assert not json.loads((O/'row.json').read_text())['engineErrors']
paths={'row':O/'row.png','launcher':G/'breakout/breakout-launcher.png','2048':G/'mines-replay/2048-info-lost.png','mines':G/'mines-replay/mines-start.png','mario':G/'mario-replay/start.png','breakout':G/'breakout/breakout-ready.png'}
reference=None
for name,p in paths.items():
 w,h,im=read_png(p);assert (w,h)==(900,600)
 crop=[row[390:510] for row in im[554:586]]
 if reference is None:reference=crop
 assert crop==reference, name+' footer differs'
 bg=crop[0][0];pts=[(x,y) for y in range(32) for x in range(120) if crop[y][x]!=bg]
 assert pts and min(x for x,y in pts)>0 and max(x for x,y in pts)<119 and min(y for x,y in pts)>0 and max(y for x,y in pts)<31,name
 print(name,'footer fits with padding')
(O/'validation.json').write_text(json.dumps({'status':'passed','image_sha256':hashlib.sha256((G/'row-main.bin').read_bytes()).hexdigest(),'checks':list(paths),'footer_rectangle':[390,554,120,32],'glyph_bounds_local':[min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)]},indent=2)+'\n')
