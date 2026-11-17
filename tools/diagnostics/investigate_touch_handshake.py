"""Offline r3 defect reproduction through the native application's event queue.

No controller emulation, package changes or card writes. Inject upstream of GUI
dispatch so the native application's synchronous touch reply wait really runs.
"""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[2] / "native"), str(_Path(__file__).resolve().parents[2] / "tests")]
import argparse, hashlib, json, os, subprocess
from pathlib import Path

R = Path(__file__).resolve().parents[2]
G = R / 'work/flappy-games'
O = G / 'touch-handshake'
O.mkdir(exist_ok=True)
m = json.loads((G / 'build.json').read_text())
s = m['symbols']
assert hashlib.sha256((G / 'row-main.bin').read_bytes()).hexdigest() == 'e085912bde87537af2f6be1b192018b3ee619accb56cf2bf9288b95ad556e880'
parser=argparse.ArgumentParser()
parser.add_argument('--candidate',type=Path,help='Raw build to validate against the recorded r3 defect')
args=parser.parse_args()
src = (R / 'work/native-build/replay.mjs').read_text()
src = src.replace('curStep = t; s.idle_slice(lab.lab_time() + 1200e6)','curStep = t; s.idle_slice(lab.lab_time() + 250e6)')
src = src.replace('  log.push(e);', '''  e.flight=Array.from({length:7},(_,i)=>u32(FLIGHT_STATE+4*i));
  e.game=rd(GAME_STATE,1)[0];e.timer=u16(GAME_TIMER);
  log.push(e);''')
src = src.replace('const WATCH =', '''const handshakeDebug = Debugger.attach(lab.sim,{lab});
const trace = [];
handshakeDebug.traceExec((r)=>{
 const g=handshakeDebug.regs();
 trace.push({pc:r.pc,step:curStep,a0:g.a0,a1:g.a1,d0:g.d0,d1:g.d1,sp:g.sp,
   words:r.pc===0x610c0e7e?Array.from({length:5},(_,i)=>u32(g.a1+4*i)):null});
},{pcs:[0x610c8153,0x610c829e,0x610c82a0,0x610c833e,0x610c0e7e,0x61294ed2]});
const WATCH =''')
src = src.replace('  log.push(e);', '''  e.touchTrace=typeof trace==='undefined'?[]:trace.slice();
  e.replyCount=e.touchTrace.filter(x=>x.pc===0x610c0e7e && x.words[0]===35).length;
  e.waitEntered=e.touchTrace.filter(x=>x.pc===0x610c829e).length;
  e.waitReturned=e.touchTrace.filter(x=>x.pc===0x610c82a0).length;
  log.push(e);''')
# snap('start') precedes declaration of trace: use global for the initial snapshot.
src = src.replace('const trace = [];', 'globalThis.handshakeTrace = []; const trace = globalThis.handshakeTrace;')
src = src.replace("typeof trace==='undefined'?[]:trace.slice()", '(globalThis.handshakeTrace||[]).slice()')
src = src.replace("  else if (t.startsWith('hold:'))", '''  else if(t==='stock-touch') {
    const b=Buffer.alloc(4);b.writeUInt32LE(0x61294d13);lab.sim.write(0x615fbd40,b);
  }
  else if(t.startsWith('app-touch:')) {
    const [kind,x,y]=t.slice(10).split(',').map(Number);
    const ev=[0,0x03000073,0x03000074,0x03000075,0x03000076,0x03000078,0x03000077,0x03000079][kind];
    if(!ev) throw new Error('Unknown kind');
    const b=Buffer.alloc(200);b.writeUInt32LE(ev,0);b.writeUInt32LE(x,12);b.writeUInt32LE(y,16);b.writeUInt32LE(0x3000,188);
    const caObj=u32(0x6036ee7c), qObj=u32(caObj+208);
    if(!caObj||!qObj) throw new Error('Application event queue missing');
    // The stock queue writer copies the event; application task does GUI post/wait.
    lab.calls(0x510a7450,{a0:qObj,a1:lab.alloc(b,4)},undefined,undefined,2000000);
    s.settle('upstream touch');
  }
  else if (t.startsWith('hold:'))''')
entry = 's1 ok ok ' + 'down ' * 13 + 'ok ' + 'down ' * 4 + 'ok '
env = dict(os.environ, OM_EMU_MODEL='E147')
for k in ('NCALL','NOUT','WATCH','GAME_STATE','GAME_GC','WRANGE','WSTACK'):
    env.pop(k,None)
summary = {}
variants=[('r3',G,''),('stock-forward-control',G,'stock-touch ')]
if args.candidate:
    variants=[('buttons',args.candidate.resolve(),'')]
    O=args.candidate.resolve()/'touch-handshake'
    O.mkdir(exist_ok=True)
for name, build, control in variants:
    meta=json.loads((build/'build.json').read_text());symbols=meta['symbols']
    assert hashlib.sha256((build/'row-main.bin').read_bytes()).hexdigest()==meta['candidate_sha256']
    local=src.replace('FLIGHT_STATE',str(symbols['flappy_state'])).replace('u16(GAME_TIMER)',f"u16({symbols['mario_handle']})").replace('rd(GAME_STATE,1)',f"rd({symbols['games_state']},1)")
    (O/'replay.mjs').write_text(local)
    script=entry+control+'app-touch:1,450,300 app-touch:3,450,300 '+('wait '*24)+'info menu s1'
    with (O / (name+'.log')).open('w') as f:
        subprocess.run(['node',str(O/'replay.mjs'),(R/'work/om-emu/emu').as_uri(),str(build/'row-main.bin'),
            str(R/'work/native-build/paired.omsd'),str(O/(name+'.json')),str(O/(name+'.omsd')),script],
            cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240)
    j=json.loads((O/(name+'.json')).read_text())
    assert not j['engineErrors']
    last=j['log'][-1]
    if name=='r3':
        assert (last['replyCount'],last['waitEntered'],last['waitReturned'])==(0,1,0)
        assert last['game']==6 and last['flight'][4]==2
        assert all(e['gui']==last['gui'] for e in j['log'][-3:]),'Blocked application still processed keys'
    else:
        assert (last['replyCount'],last['waitEntered'],last['waitReturned'])==(2,2,2)
        release=next(e for e in j['log'] if e['step'].startswith('app-touch:3'))
        if meta.get('custom_game_touch') and not control:
            assert release['game']==6 and release['timer']!=0 and release['flight'][5]>0
            assert [e['game'] for e in j['log'][-3:]]==[6,1,0]
            assert j['log'][-3]['flight'][4:6]==[0,0]
            assert last['timer']==0 and 'ID_ST_CA_REQ_DISP' in last['gui']
        else:
            assert release['game']==0 and release['timer']==0
            assert 'ID_ST_MENU' in j['log'][-2]['gui'] and 'ID_ST_CA_REQ_DISP' in last['gui']
    summary[name]=[{k:e[k] for k in ('step','game','flight','replyCount','waitEntered','waitReturned')} for e in j['log'] if e['waitEntered']]
    print(name,summary[name][-1] if summary[name] else 'NO NATIVE TOUCH: inspect trace',flush=True)
(O/'summary.json').write_text(json.dumps(dict(status='PASS emulator protocol test',candidate_sha256=meta['candidate_sha256'],observations=summary,
    physical_controller_emulated=False,injection='Native application event queue; real GUI post/reply wait, no wait or reply stub'),indent=2))
