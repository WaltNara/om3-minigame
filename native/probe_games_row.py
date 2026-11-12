"""Add an experimental, non-launching Games row to an emulator image only."""
import json
import hashlib
import os
from pathlib import Path
import struct
import subprocess
import sys
import launcher_assets
import assets_large
from test2048 import reference

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work/separate-games'
BUILD=ROOT/'work/native-build'
TC=ROOT/'work/toolchain'
BASE, START=0x60021020,0x60f59800
OUT.mkdir(parents=True,exist_ok=True)
image=bytearray((BUILD/'base-main.bin').read_bytes())
sys.path.insert(0,str(ROOT/'vendor/caduceus-om3/firmware'))
import patch
spec=json.loads((ROOT/'vendor/caduceus-om3/releases/v0.26.2/patch.json').read_text())
package=(BUILD/'caduceus-v0.26.2.bin').read_bytes()
assert patch.sha(package)==spec['result_sha256'], 'Caduceus baseline hash mismatch'
assert bytes(image)==patch.decode(patch.parse(package)[0]['enc']), 'Decoded baseline mismatch'
source_paths=[ROOT/'native'/name for name in ('probe_games_row.py','probe_games_row.s','games_menu.s',
 'launcher_assets.py','assets.py','assets_large.py','2048_large.s','test2048.py','test2048_large.py',
 'test_games_features.py','test_games_profiles.py','test_games_display.py')]
sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
def u32(a): return struct.unpack_from('<I',image,a-BASE)[0]
def put32(a,v): struct.pack_into('<I',image,a-BASE,v)
def data(a,n): return bytes(image[a-BASE:a-BASE+n])
# Rechain the existing Caduceus string hook; preserve every other string.
site=0x610f56a6
assert data(site,1)==b'\xdc'
original=(site+struct.unpack_from('<i',image,site+1-BASE)[0])&0xffffffff
def previous_jump(a):
 assert data(a,1)==b'\xdc'
 return (a+struct.unpack_from('<i',image,a+1-BASE)[0])&0xffffffff
hooks={'original_update':previous_jump(0x611d04ec), 'original_pm':previous_jump(0x6125becc),
       'original_transition':previous_jump(0x610f6016),'queue_resume':0x610f48f5,'queue_entry':0x610f48ef,
       'original_end':0x60b1fed8,'paint_resume':0x610f7ff0,'bitmap':0x610f784f,'invalidate':0x610deaab}
launcher_assets.make(OUT)
resources=assets_large.make(OUT/'assets.inc')
asset_text=(OUT/'assets.inc').read_text(encoding='ascii')
asset_text=asset_text.replace('ARROWS MOVE  HOLD OK NEW'.ljust(32),'ARROWS MOVE  INFO NEW'.ljust(32))
(OUT/'assets.inc').write_text(asset_text,encoding='ascii')
source=(ROOT/'native/2048_large.s').read_text(encoding='utf-8')
old=''' mov GDESC,a0
 mov d0,(12,a0)
 mov GSELECT,a1
 mov d0,(12,a1)
 mov board_buffer+0x40000000,d0
 mov d0,(16,a0)
 mov d0,(16,a1)
'''
assert source.count(old)==1
(OUT/'2048-host.s').write_text(source.replace(old,''),encoding='utf-8')
(OUT/'original.inc').write_text((BUILD/'original.inc').read_text(encoding='utf-8'),encoding='utf-8')
subprocess.run([str(TC/'gas/as-new.exe'),'-I',str(OUT),'-o',str(OUT/'row.o'),str(ROOT/'native/probe_games_row.s')],check=True,cwd=OUT)
subprocess.run([str(TC/'gas/as-new.exe'),'-o',str(OUT/'menu-row.o'),str(ROOT/'native/games_menu.s')],check=True)
subprocess.run([str(TC/'gas/as-new.exe'),'-I',str(OUT),'-o',str(OUT/'game-host.o'),str(OUT/'2048-host.s')],check=True)
orig=json.loads((BUILD/'build.json').read_text())['original']
targets={**{f'original_{k}':v for k,v in orig.items()},'facade':0x60b8696a,'original_bitmap_resume':0x610f7854}
subprocess.run([str(TC/'ld/ld-new.exe'),'-Ttext',hex(START),'-e','games_string',
                f'--defsym=original_string={original}', *[f'--defsym={k}={v}' for k,v in hooks.items()],
                *[f'--defsym={k}={v}' for k,v in targets.items()],
                '-o',str(OUT/'row.elf'),str(OUT/'row.o'),str(OUT/'menu-row.o'),str(OUT/'game-host.o')],check=True)
subprocess.run([str(TC/'binutils/objcopy.exe'),'-O','binary','-j','.text',str(OUT/'row.elf'),str(OUT/'row.bin')],check=True)
blob=(OUT/'row.bin').read_bytes(); pos=(START+len(blob)+3)&~3
nm=subprocess.check_output([str(TC/'binutils/nm-new.exe'),str(OUT/'row.elf')],text=True)
sy={s[2]:int(s[0],16) for line in nm.splitlines() if len(s:=line.split())==3}
assert set(data(START,0x40000))=={255}
image[START-BASE:START-BASE+len(blob)]=blob
put32(site+1,(START-site)&0xffffffff)
for a,name in ((0x611d04ec,'games_update'),(0x6125becc,'games_pm'),(0x610f6016,'games_transition')):
 put32(a+1,(sy[name]-a)&0xffffffff)
assert data(0x610f48ef,6)==bytes.fromhex('3cf89304201c')
image[0x610f48ef-BASE:0x610f48f5-BASE]=b'\xdc'+struct.pack('<i',sy['games_queue_hook']-0x610f48ef)+b'\xcb'
assert data(0x610f7fe9,7)==bytes.fromhex('ddef7ea2ff0004')
image[0x610f7fe9-BASE:0x610f7ff0-BASE]=b'\xdc'+struct.pack('<i',sy['games_render_hook']-0x610f7fe9)+b'\xcb\xcb'
assert data(0x60177b7d,5)==bytes.fromhex('8818dff024')
image[0x60177b7d-BASE:0x60177b82-BASE]=b'\xdc'+struct.pack('<i',sy['games_dial_hook']-0x60177b7d)
def alloc(payload):
 global pos
 addr=pos; image[addr-BASE:addr-BASE+len(payload)]=payload
 pos=(addr+len(payload)+3)&~3
 return addr
old_list=[111,5397,8,5398,5386,5385,5384,7,5394,5389,5399,5382,5400]
assert list(struct.unpack('<13I',data(0x60f49a74,52)))==old_list
assert u32(0x60f49a63)==0x60f49a74 and u32(0x60f49a69)==13
new_list=alloc(struct.pack('<14I',*old_list,5380))
put32(0x60f49a63,new_list); put32(0x60f49a69,14)
# The WB choice row is used solely as a temporary row-structure template.
old_table=u32(0x611d040f)
assert old_table==u32(0x611d0848)==0x60f49e08
table=bytearray(data(old_table,25*40))
idx=next(i for i in range(25) if struct.unpack_from('<I',table,i*40)[0]==5384)
row=bytearray(table[idx*40:(idx+1)*40]); struct.pack_into('<I',row,0,5380)
title=alloc(struct.pack('<HHI',4,0x7f08,0x6154b480))
option=alloc(struct.pack('<IHHI',0,4,0x7f08,0x6154b480))
cell_option=alloc(struct.pack('<IHHI',0,4,0x7f09,0x6154b480))
struct.pack_into('<I',row,4,title)
for off in (8,20,32): struct.pack_into('<I',row,off,option)
struct.pack_into('<I',row,20,cell_option)
new_table=alloc(table+row)
for a,c in ((0x611d040f,0x611d0422),(0x611d0848,0x611d0859)):
 assert u32(a)==old_table and data(c,2)==b'\xa5\x19'
 put32(a,new_table); image[c+1-BASE]=26
# Insert an additional key into each existing open-addressed row switch.
for a in (0x61536a2c,0x61536b2c,0x61536c2c,0x61536d2c,0x61536f2c,
          0x615510cc,u32(0x611d05ed),0x6155124c,u32(0x611d1a5b)):
 entries=[struct.unpack('<II',data(a+8*i,8)) for i in range(32)]
 matches=[target for key,target in entries if key==5384-6]
 assert len(matches)==1 and not any(key==5380-6 for key,target in entries)
 i=(5380-6)&31
 while entries[i][0]: i=(i+1)%32
 put32(a+8*i,5380-6);put32(a+8*i+4,matches[0])
assert pos<START+0x40000
put32(0x60045e9c,START+((pos-START+0x7ff)//0x800)*0x800)
(OUT/'row-main.bin').write_bytes(image)
(OUT/'main.bin').write_bytes(image)
(OUT/'paired.omsd').write_bytes((BUILD/'paired.omsd').read_bytes())
(OUT/'replay.mjs').write_text((BUILD/'replay.mjs').read_text(encoding='utf-8'),encoding='utf-8')
digest=hashlib.sha256(image).hexdigest()
(OUT/'build.json').write_text(json.dumps({'candidate_sha256':digest,'symbols':sy,'resources':resources,'source_sha256':sources,
 'status':'emulator-only raw main block; not an installable package'},indent=2),encoding='utf-8')
env=dict(os.environ,OM_EMU_MODEL='E147')
for name in ('GAME_STATE','GAME_GC','WATCH','WSTACK','WFROM','WIDS'):env.pop(name,None)
replay=(BUILD/'replay.mjs').read_text(encoding='utf-8')
display_needle="  else if (t.startsWith('hold:'))"
assert replay.count(display_needle)==1
replay=replay.replace(display_needle,"  else if (t === 'evf') { s.display_input('eye', 1); }\n  else if (t === 'tft') { s.display_input('eye', 0); }\n"+display_needle)
needle='  log.push(e);'
assert replay.count(needle)==1
replay=replay.replace(needle,f"  e.device=s.device; e.menu = [...rd({sy['games_state']},2)]; e.gamesRow = rd({sy['games_row_selected']},1)[0]; e.paintValid=rd({sy['games_paint_valid']},1)[0]; e.gameDraws=u32({sy['games_draw_count']}); e.renderSeen=u32({sy['games_render_seen']}); e.renderState=rd({sy['games_render_state']},1)[0]; e.board=[...rd({sy['board']},16)]; e.moves=u32({sy['moves']}); e.score=u32({sy['score']}); e.rng=u32({sy['rng']});\n"+needle)
(OUT/'row-replay.mjs').write_text(replay,encoding='utf-8')
cmd=['node',str(OUT/'row-replay.mjs'),(ROOT/'work/om-emu/emu').as_uri(),str(OUT/'row-main.bin'),
 str(BUILD/'paired.omsd'),str(OUT/'row.json'),str(OUT/'row-saved.omsd'),
 's1 ok ok down vals '+('down '*12)+'shot:work/separate-games/games-row.png ok shot:work/separate-games/launcher0.png main+1 shot:work/separate-games/launcher1.png main-1 ok shot:work/separate-games/separate-2048.png left up right down main+1 main-1 sub+1 sub-1 shot:work/separate-games/separate-2048-play.png menu ok info menu menu shot:work/separate-games/row-returned.png vals s1']
with (OUT/'row.log').open('w',encoding='utf-8') as log:
 subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
result=json.loads((OUT/'row.json').read_text(encoding='utf-8'))
assert not result['engineErrors'],result['engineErrors']
log=result['log']
open_index=next(i for i,e in enumerate(log) if e['step'].endswith('games-row.png'))
sequence=[e for e in log[open_index+1:] if e['step'] in ('ok','main+1','main-1')][:4]
assert [e['menu'] for e in sequence]==[[1,0],[1,1],[1,0],[2,0]],[(e['step'],e['menu'],e['gui']) for e in sequence]
assert all(e['paintValid']==1 for e in sequence),sequence
assert sequence[1]['gameDraws']>sequence[0]['gameDraws']>0,[(e['step'],e['gameDraws'],e['renderSeen'],e['renderState']) for e in sequence]
assert (OUT/'launcher0.png').read_bytes() != (OUT/'launcher1.png').read_bytes(), 'Launcher selection did not repaint'
played=[e for e in log if e['step'] in ('left','up','right','down','main+1','main-1','sub+1','sub-1') and e['menu'][0]==2]
assert played and played[-1]['moves']>0,[(e['step'],e['moves']) for e in played]
directions={'up':0,'down':1,'left':2,'right':3,'main+1':0,'main-1':1,'sub+1':2,'sub-1':3}
initial=next(e for e in log if e['step'].endswith('separate-2048.png'))
board=initial['board']; score=initial['score']; seed=initial['rng']; moves=initial['moves']
def rand(v):
 v^=(v<<13)&0xffffffff; v^=v>>17; v^=(v<<5)&0xffffffff
 return v
for event in played:
 board,score,changed=reference(board,directions[event['step']],score)
 if changed:
  moves+=1
  empty=[i for i,v in enumerate(board) if not v]
  seed=rand(seed); index=empty[((seed&65535)*len(empty))>>16]
  seed=rand(seed); board[index]=2 if ((seed&65535)*10)>>16==0 else 1
 assert (board,score,seed,moves)==(event['board'],event['score'],event['rng'],event['moves']),event['step']
last_moves=played[-1]['moves']; game_exit=next(i for i,e in enumerate(log) if e['step'].endswith('separate-2048-play.png'))
nav=[e for e in log[game_exit+1:] if e['step'] in ('ok','menu')][:4]
assert [e['menu'][0] for e in nav]==[1,2,1,0],[(e['step'],e['menu']) for e in nav]
assert nav[1]['moves']==last_moves,'Game did not resume on re-entry'
assert (OUT/'row-returned.png').read_bytes()==(OUT/'games-row.png').read_bytes(),'Games panel did not clear on exit'
reset=next(e for e in log[game_exit+1:] if e['step']=='info')
assert reset['moves']==0 and reset['score']==0 and sum(v!=0 for v in reset['board'])==2,reset
lines=[x for x in (OUT/'row.log').read_text(encoding='utf-8').splitlines() if x.startswith('VALS ')]
assert len(lines)==2 and lines[0]==lines[1],'Settings changed during row navigation'
assert hashlib.sha256((OUT/'row-main.bin').read_bytes()).hexdigest()==digest
(OUT/'games-validation.json').write_text(json.dumps({'image_sha256':digest,'status':'passed',
 'checks':['Games row','launcher selection','repaint','four arrows','both dials against reference',
           'score and spawns','INFO restart','menu and session resume','photo settings unchanged']},indent=2))
print('Games row and 2048 replay passed; inspect work/separate-games screenshots.')
