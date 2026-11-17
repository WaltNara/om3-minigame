"""Read-only replay of the sealed r3 image: crash timer/redraw and touch routing."""
import hashlib,json,os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];G=R/'work/flappy-games';O=G/'r3-investigation'
O.mkdir(exist_ok=True);m=json.loads((G/'build.json').read_text());s=m['symbols']
assert hashlib.sha256((G/'row-main.bin').read_bytes()).hexdigest()=='e085912bde87537af2f6be1b192018b3ee619accb56cf2bf9288b95ad556e880'
src=(G/'validation/play.mjs').read_text()
src=src.replace('const WATCH =',f'''const fd=Debugger.attach(lab.sim,{{lab}});
fd.traceExec((r)=>{{if(r.pc==={s['flappy_paint']})globalThis.fpaints=(globalThis.fpaints||0)+1;
if(r.pc==={s['flappy_touch']})globalThis.fhooks=(globalThis.fhooks||0)+1;
if(r.pc===0x61294ed2)globalThis.fdecode=(globalThis.fdecode||0)+1;
}},{{pcs:[{s['flappy_paint']},{s['flappy_touch']},0x61294ed2]}});
const WATCH =''')
src=src.replace('  log.push(e);',f"  e.ticks=u32({s['mario_ticks']});e.paints=globalThis.fpaints||0;e.hooks=globalThis.fhooks||0;e.decodes=globalThis.fdecode||0;\n  log.push(e);")
(O/'replay.mjs').write_text(src)
entry='s1 ok ok '+('down '*13)+'ok '+('down '*4)+'ok '
scripts={'button-crash':entry+'ok '+('wait '*28)+'menu s1',
         'tap-release':entry+'gui-touch:1,450,300 gui-touch:3,450,300 '+('wait '*28)+'menu s1'}
env=dict(os.environ,OM_EMU_MODEL='E147')
for k in ('NCALL','NOUT','WATCH','GAME_STATE','GAME_GC','WRANGE','WSTACK'):env.pop(k,None)
summary={}
for name,commands in scripts.items():
    with (O/(name+'.log')).open('w') as f:
        subprocess.run(['node',str(O/'replay.mjs'),(R/'work/om-emu/emu').as_uri(),str(G/'row-main.bin'),str(R/'work/native-build/paired.omsd'),str(O/(name+'.json')),str(O/(name+'.omsd')),commands],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
    j=json.loads((O/(name+'.json')).read_text());assert not j['engineErrors']
    events=[e for e in j['log'] if e.get('game')==6]
    summary[name]=[{k:e[k] for k in ('step','flight','timer','ticks','paints','hooks','decodes')} for e in events]
    dead=[e for e in events if e['flight'][4]==2]
    assert len(dead)>=2
    assert dead[-1]['timer']!=0 and dead[-1]['paints']>dead[0]['paints']
    if name=='tap-release':
        taps=[e for e in events if e['step'].startswith('gui-touch:')]
        assert len(taps)==2 and taps[-1]['flight'][5]>0
        assert taps[-1]['hooks']==2 and taps[-1]['decodes']==0
    print(name,'completed; repeated redraws after crash confirmed',flush=True)
(O/'summary.json').write_text(json.dumps(dict(candidate_sha256=m['candidate_sha256'],observations=summary,
    conclusion='Emulator confirms touch routing but not hardware behavior; dead flight retains timer and repeatedly repaints. Hardware freeze not reproduced.'),indent=2))
