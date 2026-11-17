"""Exercise LCD / EVF changes while Games owns the UI."""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[1] / "native"), str(_Path(__file__).resolve().parents[1] / "tests")]
import hashlib
import json
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
env=dict(os.environ,OM_EMU_MODEL='E147')
for key in ('GAME_STATE','GAME_GC','WATCH','WSTACK','WFROM','WIDS'):env.pop(key,None)
script='s1 ok ok '+('down '*13)+'ok ok left evf up tft right s1'
cmd=['node',str(OUT/'row-replay.mjs'),(ROOT/'work/om-emu/emu').as_uri(),str(OUT/'row-main.bin'),
     str(BUILD/'paired.omsd'),str(OUT/'display.json'),str(OUT/'display.omsd'),script]
with (OUT/'display.log').open('w',encoding='utf-8') as log:
 subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
result=json.loads((OUT/'display.json').read_text())
assert not result['engineErrors'],result['engineErrors']
events={e['step']:e for e in result['log'] if e['step'] in ('evf','tft')}
assert events['evf']['device']=='evf' and events['tft']['device']=='tft',events
for event in events.values():
 assert event['menu'][0]==0 and event['gamesRow']==0 and event['paintValid']==0,event
assert result['log'][-1]['menu'][0]==0
assert hashlib.sha256((OUT/'row-main.bin').read_bytes()).hexdigest()==digest
(OUT/'display-validation.json').write_text(json.dumps({'image_sha256':digest,
 'status':'partial: game state cleared on output changes; post-switch return to shooting not established',
 'final_gui':result['log'][-1]['gui']},indent=2))
print('Games state and drawing pointer cleared on LCD/EVF changes; post-switch shooting remains unverified')
