"""Compare unmodified Caduceus and Games probe HSL/WB emulator behavior."""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[1] / "native"), str(_Path(__file__).resolve().parents[1] / "tests")]
import json
import hashlib
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'work/separate-games'
BUILD=ROOT/'work/native-build'
env=dict(os.environ,OM_EMU_MODEL='E147')
digest=hashlib.sha256((OUT/'row-main.bin').read_bytes()).hexdigest()
build=json.loads((OUT/'build.json').read_text())
assert digest==build['candidate_sha256']
for name,want in build['source_sha256'].items():
 assert hashlib.sha256((ROOT/'native'/name).read_bytes()).hexdigest()==want,name
for name in ('GAME_STATE','GAME_GC','WATCH','WSTACK','WFROM','WIDS'):env.pop(name,None)

def replay(case,image,script):
 cmd=['node',str(OUT/'row-replay.mjs'),(ROOT/'work/om-emu/emu').as_uri(),str(image),
      str(BUILD/'paired.omsd'),str(OUT/f'{case}.json'),str(OUT/f'{case}.omsd'),script]
 with (OUT/f'{case}.log').open('w',encoding='utf-8') as log:
  subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 result=json.loads((OUT/f'{case}.json').read_text(encoding='utf-8'))
 assert not result['engineErrors'],result['engineErrors']
 return result['log']

def comparable(log):
 return [{k:e.get(k) for k in ('step','gui','slots','gdesc','gselect')} for e in log]

for case,actions in [('hsl','down right info left'),('wb','down down down down down down ok')]:
 runs=[]
 for label,image in [('stock',BUILD/'base-main.bin'),('games',OUT/'row-main.bin')]:
  name=f'{case}-{label}'; shot=f'work/separate-games/{name}.png'
  runs.append(replay(name,image,f's1 ok ok {actions} shot:{shot} menu s1'))
 # Screenshot paths differ, while all other snapshot fields must match.
 for run in runs:
  for e in run:
   if e['step'].startswith('shot:'):e['step']='shot'
 assert comparable(runs[0])==comparable(runs[1]),case
 assert (OUT/f'{case}-stock.png').read_bytes()==(OUT/f'{case}-games.png').read_bytes(),case
 print(f'{case}: matches unmodified Caduceus in emulator')
assert hashlib.sha256((OUT/'row-main.bin').read_bytes()).hexdigest()==digest
(OUT/'features-validation.json').write_text(json.dumps({'image_sha256':digest,'hsl':'passed','wb':'passed'},indent=2))
