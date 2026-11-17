"""Native application/GUI round trips, gesture lifetime, and branch ABI.

Unlike the withdrawn r3's direct-GUI tests, every touch starts in the real
application queue and must return through its synchronous reply wait. Display
switch coverage ends at teardown: later input also stalls with stock routing
in this harness, independently of the repaired touch completion.
"""
import hashlib,json,os,subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

R=Path(__file__).resolve().parents[1]
G=R/os.environ.get('OM3_FLAPPY_BUILD','work/flappy-touch-v2');O=G/'touch-reply';O.mkdir(exist_ok=True)
B=R/'work/native-build';m=json.loads((G/'build.json').read_text());sy=m['symbols']
end_kinds=m.get('touch_terminal_kinds',[3])
assert m['custom_game_touch']
assert hashlib.sha256((G/'row-main.bin').read_bytes()).hexdigest()==m['candidate_sha256']
src=(B/'replay.mjs').read_text()
src=src.replace('  log.push(e);', '''  e.game=rd(SY.games_state,1)[0]; e.timer=u16(SY.mario_handle);
  e.flight=Array.from({length:9},(_,i)=>u32(SY.flappy_state+4*i));
  e.contact=rd(SY.flappy_contact,1)[0];e.drain=rd(SY.flappy_drain,1)[0];
  e.pending=rd(SY.flappy_pending,1)[0];
  e.touch={...(globalThis.ftStats||{})};delete e.touch.replyWords;
  log.push(e);''')
src=src.replace("const STATE =",'const END_KINDS='+json.dumps(end_kinds)+';\nconst SY='+json.dumps(sy)+';\nconst STATE =')
src=src.replace('const WATCH =', '''globalThis.ftStats={sent:0,replies:0,waits:0,returned:0,owned:0,forwarded:0,abi:0,flaps:0,replyWords:[]};
const ts=globalThis.ftStats, td=Debugger.attach(lab.sim,{lab});let tf=null;
const same=(a,b)=>Buffer.from(a).equals(Buffer.from(b));
td.traceExec((r)=>{
 const g=td.regs();
 if(r.pc===SY.flappy_touch_repaired){
   if(tf)throw new Error('Recursive touch dispatch');
   const payload=u32(g.a3+12);
   tf={g,payload,event:rd(g.a3,28),record:payload?rd(payload,12):null,owned:false};
 }else if(r.pc===0x61294d13 && tf){ts.forwarded++;tf=null;}
 else if(r.pc===0x61294ed2 && tf){
   if(g.a0===tf.g.a3)throw new Error('Owned event used live payload');
   if(u32(g.a0+12)!==0)throw new Error('Shadow payload is not null');
   if(g.sp!==tf.g.sp-36-120)throw new Error('Unexpected stock call frame');
   tf.owned=true;ts.owned++;
 }else if(r.pc===0x61294e57 && tf){
   if(!tf.owned || g.sp!==tf.g.sp || g.d2!==0)throw new Error('Touch epilogue/stack');
   for(const k of ['d0','d1','d3','a0','a1','a2','a3'])if(g[k]!==tf.g[k])throw new Error('Clobbered '+k);
   if(!same(rd(g.a3,28),tf.event) || (tf.payload&&!same(rd(tf.payload,12),tf.record)))throw new Error('Original event changed');
   ts.abi++;tf=null;
 }else if(r.pc===0x610c0e7e){
   const words=Array.from({length:5},(_,i)=>u32(g.a1+4*i));
   if(words[0]===35){ts.replies++;ts.replyWords.push(words);
     if(tf?.owned && words.join(',')!=='35,57,0,0,0')throw new Error('Unexpected owned completion');}
 }else if(r.pc===0x610c829e)ts.waits++;
 else if(r.pc===0x610c82a0)ts.returned++;
 else if(r.pc===SY.flappy_step && rd(SY.flappy_pending,1)[0])ts.flaps++;
},{pcs:[SY.flappy_touch_repaired,0x61294d13,0x61294ed2,0x61294e57,0x610c0e7e,0x610c829e,0x610c82a0,SY.flappy_step]});
function appTouch(kind,x=450,y=300){
 const before={replies:ts.replies,waits:ts.waits,returned:ts.returned};
 const ev=[0,0x03000073,0x03000074,0x03000075,0x03000076,0x03000078,0x03000077,0x03000079][kind];
 if(!ev)throw new Error('Unknown touch kind');
 const b=Buffer.alloc(200);b.writeUInt32LE(ev);b.writeUInt32LE(x,12);b.writeUInt32LE(y,16);b.writeUInt32LE(0x3000,188);
 const caObj=u32(0x6036ee7c),qObj=u32(caObj+208);
 lab.calls(0x510a7450,{a0:qObj,a1:lab.alloc(b,4)},undefined,undefined,2000000);
 ts.sent++;s.settle('native touch round trip');
 for(const k of ['replies','waits','returned'])if(ts[k]-before[k] !== 1)throw new Error('Missing/duplicate reply or blocked sender: '+JSON.stringify(ts));
 if(ts.replies!==ts.waits || ts.waits!==ts.returned)throw new Error('Unbalanced touch wait');
 if(tf)throw new Error('Unfinished GUI touch frame');
}
const WATCH =''')
src=src.replace("  else if (t.startsWith('hold:'))", '''  else if(t.startsWith('app-touch:')){const [k,x,y]=t.slice(10).split(',').map(Number);appTouch(k,x,y);}
  else if(t.startsWith('app-taps:')){for(let i=0;i<Number(t.slice(9));i++){appTouch(1);s.idle_slice(lab.lab_time()+60e6);appTouch(END_KINDS[i%END_KINDS.length]);s.idle_slice(lab.lab_time()+60e6);}}
  else if(t.startsWith('app-burst:')){for(const kind of t.slice(10).split(',').map(Number))appTouch(kind);}
  // Force a GUI transition to test interrupted-gesture cleanup separately
  // from the native application's stock filtering of MENU during contact.
  else if(t==='gui-menu'){for(const message of [0x900e,0x900f]){let idx=0;for(let i=1;i<=334;i++)if(lab.message_for(i)===message){idx=i;break;}if(!idx)throw new Error('MENU index missing');s.event(idx);}}
  else if(t==='evf'){s.display_input('eye',1);}
  else if (t.startsWith('hold:'))''')
src=src.replace('curStep = t; s.idle_slice(lab.lab_time() + 1200e6)','curStep = t; s.idle_slice(lab.lab_time() + 250e6)')
(O/'replay.mjs').write_text(src)
entry='s1 ok ok '+'down '*13+'ok '+'down '*4+'ok '
press='app-touch:1,450,300 ';release='app-touch:3,450,300 ';tap=press+release
scripts={
 'repeated':entry+'app-taps:64 info '+tap+'menu s1',
 'held-and-kinds':entry+press+press+'app-touch:2,460,310 app-touch:6,470,320 app-touch:7,480,330 '+release+'app-touch:4,450,300 app-touch:5,450,300 '+tap+'menu s1',
 'crash-retry':entry+tap+'wait '*26+tap+'info menu s1',
 'held-menu':entry+press+'menu '+release+'menu s1',
 'menu-drain':entry+press+'gui-menu app-touch:2,450,300 '+release+'ok '+tap+'menu s1',
 'shutter-exit':entry+tap+'s1 menu s1',
 'display-drain':entry+press+'evf',
 'fresh-outside':entry+press+'gui-menu '+tap+'menu s1',
}
if end_kinds==[3,4,5]:
    for kind in (4,5):
        terminal=f'app-touch:{kind},450,300 '
        scripts[f'terminal-{kind}']=entry+(press+terminal)*2+'menu s1'
        scripts[f'drain-{kind}']=entry+press+'gui-menu '+terminal+'ok '+tap+'menu s1'
    scripts['mixed-endings']=entry+press+release+'app-touch:4,450,300 '+press+'app-touch:5,450,300 '+release+'menu s1'
    scripts['short-tap']=entry+'app-burst:1,4 menu s1'
env=dict(os.environ,OM_EMU_MODEL='E147')
for k in ('NCALL','NOUT','WATCH','GAME_STATE','GAME_GC','WRANGE','WSTACK'):env.pop(k,None)
summaries={}
def run_case(name,script):
    with (O/(name+'.log')).open('w') as f:
        subprocess.run(['node',str(O/'replay.mjs'),(R/'work/om-emu/emu').as_uri(),str(G/'row-main.bin'),str(B/'paired.omsd'),str(O/(name+'.json')),str(O/(name+'.omsd')),script],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=420)
    return json.loads((O/(name+'.json')).read_text())

# Independent camera sessions use distinct card copies/logs and a read-only ROM.
with ThreadPoolExecutor(max_workers=3) as pool:
    jobs={name:pool.submit(run_case,name,script) for name,script in scripts.items()}
    results={name:job.result() for name,job in jobs.items()}
for name,j in results.items():
    assert not j['engineErrors'];log=j['log']
    events=[e for e in log if e['step'].startswith('app-touch:')]
    if name in ('repeated','held-and-kinds','crash-retry'):
        assert all(e['game']==6 for e in events)
    if name=='repeated':
        burst=next(e for e in log if e['step']=='app-taps:64');assert burst['game']==6 and burst['touch']['owned']==128
        assert burst['touch']['flaps']==64 and burst['contact']==0
        reset=next(e for e in log if e['step']=='info');assert reset['flight'][4:6]==[0,0]
    if name.startswith('terminal-') or name=='mixed-endings':
        assert all(e['game']==6 for e in events)
        assert events[-1]['touch']['flaps']==2 and events[-1]['contact']==0
    if name.startswith('drain-'):
        assert [e['game'] for e in events]==[6,1,6,6]
        assert events[1]['drain']==0 and events[-1]['touch']['flaps']==2
    if name=='short-tap':
        e=next(e for e in log if e['step']=='app-burst:1,4')
        assert e['game']==6 and e['contact']==0 and e['touch']['flaps']==1
    if name=='held-and-kinds':
        assert [e['touch']['flaps'] for e in events[:8]]==[1]*8
        assert events[-1]['touch']['flaps']==2 and events[-1]['contact']==0
    if name=='crash-retry':
        assert any(e['flight'][4]==2 for e in log)
        assert events[-1]['flight'][4]==1 and events[-1]['flight'][5]<8
    if name=='menu-drain':
        assert [e['game'] for e in events]==[6,1,1,6,6]
        assert events[1]['drain']==1 and events[2]['drain']==0
    if name=='held-menu':
        menus=[e for e in log if e['step']=='menu']
        assert [e['game'] for e in menus]==[6,1]
        assert events[-1]['game']==6 and events[-1]['contact']==0
    if name=='shutter-exit':
        assert events[-1]['game']==6
        assert all(e['game']==0 and e['timer']==0 for e in log if e['step']=='s1')
    if name=='display-drain':
        switched=next(e for e in log if e['step']=='evf')
        assert switched['game']==0 and switched['timer']==0 and switched['contact']==0 and switched['drain']==1
        assert switched['touch']['waits']==switched['touch']['returned']==1
    if name=='fresh-outside':
        assert events[1]['drain']==0 and events[-1]['game']==0
        assert events[-1]['touch']['forwarded']==2
    final=log[-1]
    assert final['game']==0 and final['timer']==0 and final['contact']==0 and final['pending']==0
    assert final['drain']==(1 if name=='display-drain' else 0)
    t=final['touch'];assert t['owned']==t['abi'] and t['owned']+t['forwarded']==t['sent']
    summaries[name]=t
    print(name,'PASS',t,flush=True)
(O/'validation.json').write_text(json.dumps(dict(status='PASS emulator native application/GUI protocol',candidate_sha256=m['candidate_sha256'],scenarios=summaries,physical_touch_verified=False,display_switch_scope='Teardown only. Subsequent input unavailable with both stock and repaired routing in this harness; recovery after display switch is not verified.'),indent=2))
