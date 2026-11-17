"""Check Games entry, drawing, and shutter exit on each COLOR profile."""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[1] / "native"), str(_Path(__file__).resolve().parents[1] / "tests")]
from concurrent.futures import ThreadPoolExecutor
import json
import hashlib
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work/separate-games'
BUILD=ROOT/'work/native-build'
digest=hashlib.sha256((OUT/'row-main.bin').read_bytes()).hexdigest()
build=json.loads((OUT/'build.json').read_text())
assert digest==build['candidate_sha256']
for name,want in build['source_sha256'].items():
 assert hashlib.sha256((ROOT/'native'/name).read_bytes()).hexdigest()==want,name

def run(profile):
 env=dict(os.environ,OM_EMU_MODEL='E147')
 for key in ('GAME_STATE','GAME_GC','WATCH','WSTACK','WFROM','WIDS'):env.pop(key,None)
 select=f'main+{profile-1} ' if profile>1 else ''
 script='s1 ok ok '+select+('down '*13)+'ok ok s1'
 name=f'profile-{profile}'
 cmd=['node',str(OUT/'row-replay.mjs'),(ROOT/'work/om-emu/emu').as_uri(),str(OUT/'row-main.bin'),
      str(BUILD/'paired.omsd'),str(OUT/f'{name}.json'),str(OUT/f'{name}.omsd'),script]
 with (OUT/f'{name}.log').open('w',encoding='utf-8') as log:
  subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 result=json.loads((OUT/f'{name}.json').read_text(encoding='utf-8'))
 assert not result['engineErrors'],result['engineErrors']
 game=result['log'][-2]; exit=result['log'][-1]
 assert game['menu'][0]==2 and game['gameDraws']>0 and sum(v!=0 for v in game['board'])==2,(profile,game)
 assert exit['menu'][0]==0 and exit['gui']=='SS_COMMON/ID_ST_CA_REQ_DISP',(profile,exit)
 return f'COLOR{profile}: Games -> 2048 -> shutter exit passed'

with ThreadPoolExecutor(max_workers=2) as pool:
 for result in pool.map(run,range(1,5)):print(result,flush=True)
assert hashlib.sha256((OUT/'row-main.bin').read_bytes()).hexdigest()==digest
(OUT/'profiles-validation.json').write_text(json.dumps({'image_sha256':digest,'profiles':[1,2,3,4],'status':'passed'},indent=2))
