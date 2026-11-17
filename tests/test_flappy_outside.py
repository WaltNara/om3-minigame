"""Compare fresh outside-game taps with R2, including camera profile values."""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[1] / "native"), str(_Path(__file__).resolve().parents[1] / "tests")]
import json,os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];G=R/os.environ.get('OM3_FLAPPY_BUILD','work/flappy-buttons');O=G/'outside';O.mkdir(exist_ok=True)
m=json.loads((G/'build.json').read_text());s=m['symbols'];B=R/'work/native-build'
source=(B/'replay.mjs').read_text()
source=source.replace('  log.push(e);',f"  e.game=rd({s['games_state']},1)[0];e.timer=u16({s['mario_handle']});e.valid=rd({s['games_paint_valid']},1)[0];\n  log.push(e);")
source=source.replace("  else if (t.startsWith('hold:'))","  else if(t.startsWith('gui-touch:')){const [k,x,y]=t.slice(10).split(',').map(Number);if(!s.touch_index){for(let i=1;i<=334;i++)if(lab.message_for(i)===0x9100){s.touch_index=i;break;}}s.post_touch(k,x,y);}\n  else if (t.startsWith('hold:'))")
(O/'replay.mjs').write_text(source)
touch='gui-touch:1,450,300 gui-touch:3,450,300 '
script='s1 '+touch+'s1 menu '+touch+'s1 ok ok '+touch+'s1 '
env=dict(os.environ,OM_EMU_MODEL='E147')
for k in ('WATCH','NCALL','NOUT','GAME_STATE','GAME_GC','WRANGE','WSTACK'):env.pop(k,None)
results={}
for name,image in [('r2',R/'work/combined-game/row-main.bin'),('candidate',G/'row-main.bin')]:
    with (O/(name+'.log')).open('w') as f:
        subprocess.run(['node',str(O/'replay.mjs'),(R/'work/om-emu/emu').as_uri(),str(image),str(R/'work/r2-lifecycle-audit/seed.omsd'),str(O/(name+'.json')),str(O/(name+'.omsd')),script],env=env,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
    j=json.loads((O/(name+'.json')).read_text());assert not j['engineErrors']
    keys=('step','state','gui','slots')
    results[name]=[{k:e[k] for k in keys if k in e} for e in j['log']]
    if name=='candidate':assert all(e['game']==0 and e['timer']==0 for e in j['log'])
    print(name,'completed',flush=True)
assert results['r2']==results['candidate']
(O/'validation.json').write_text(json.dumps(dict(status='PASS emulator only',candidate_sha256=m['candidate_sha256'],matching_snapshots=len(results['r2'])),indent=2))
print('PASS outside touch/profile parity')
