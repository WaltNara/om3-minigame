"""Full-camera replay for the separate platform-game integration."""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[1] / "native"), str(_Path(__file__).resolve().parents[1] / "tests")]
import hashlib, json, os, subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]; G=R/os.environ.get('OM3_GAME_BUILD','work/combined-game'); O=G/'mario-replay'; B=R/'work/native-build'
O.mkdir(parents=True,exist_ok=True)
sy=json.loads((G/'build.json').read_text())['symbols']
s=(B/'replay.mjs').read_text()
s=s.replace('  log.push(e);',f"  e.menu=[...rd({sy['games_state']},2)]; e.mario=[...rd({sy['mario_state']},20)]; e.x=u32({sy['mario_state']}); e.y=u32({sy['mario_state']+4})|0; e.camera=u32({sy['mario_state']+20}); e.coins=u32({sy['mario_state']+28}); e.ticks=u32({sy['mario_ticks']}); e.timer=u16({sy['mario_handle']}); e.epoch=u32({sy['mario_epoch']}); e.keys=rd({sy['mario_keys']},1)[0]; e.result=u32({sy['mario_state']+16}); e.moves=u32({sy['moves']}); e.paintValid=rd({sy['games_paint_valid']},1)[0];\n  log.push(e);")
s=s.replace("  else if (t.startsWith('hold:'))", "  else if (t === 'jump-right') { s.key('right','down'); s.key('up','down'); s.camapp.pump(); s.idle_slice(lab.lab_time()+800e6); s.key('up','up'); s.key('right','up'); s.camapp.pump(); }\n  else if (t === 'evf') { s.display_input('eye',1); }\n  else if (t.startsWith('hold:'))")
special=f"""  else if (t === 'quick-tap') {{ s.key('up','down'); s.camapp.pump(); s.key('up','up'); s.camapp.pump(); s.idle_slice(lab.lab_time()+130e6); }}
  else if (t === 'dual-jump') {{ s.key('up','down'); s.key('ok','down'); s.key('up','up'); s.camapp.pump(); }}
  else if (t === 'release-ok') {{ s.key('ok','up'); s.camapp.pump(); }}
  else if (t === 'solve' || t === 'fall' || t === 'scroll') {{
    const trace=[];
    s.key('right','down'); s.camapp.pump();
    for(let i=0;u32({sy['mario_state']+16})===0 && i<650;i++) {{
      const x=u32({sy['mario_state']}), y=u32({sy['mario_state']+4})|0, vy=u32({sy['mario_state']+8})|0;
      const floor=(px)=>{{let v=rd({sy['mario_heights']}+(px>>4),1)[0];return v>127?v-256:v;}};
      const enemy=u32({sy['mario_state']+36}), dead=u32({sy['mario_state']+40});
      const step=floor(Math.min(1151,x+15))>y;
      const gap=t!=='fall' && floor(Math.min(1151,x+32))===-64;
      const foe=t!=='fall' && !dead && enemy-x>10 && enemy-x<48;
      const jump=vy===0 && (step||gap||foe);
      s.key('up',jump?'down':'up'); s.camapp.pump();
      s.idle_slice(lab.lab_time()+120e6);
      trace.push([x,y,vy,jump,u32({sy['mario_state']+20})]);
      if(t==='scroll' && x>=500)break;
    }}
    fs.writeFileSync('{(O/'trajectory-').as_posix()}'+t+'.json',JSON.stringify(trace));
    s.key('right','up'); s.key('up','up'); s.camapp.pump();
  }}
"""
s=s.replace("  else if (t.startsWith('hold:'))",special+"  else if (t.startsWith('hold:'))")
s=s.replace('curStep = t; s.idle_slice(lab.lab_time() + 1200e6)', "curStep = t; s.idle_slice(lab.lab_time() + (t === 'wait' ? 1200e6 : 250e6))")
(O/'play.mjs').write_text(s)
env=dict(os.environ,OM_EMU_MODEL='E147')
for key in ('GAME_STATE','GAME_GC','WATCH','WSTACK','WFROM','WIDS','NCALL'):env.pop(key,None)
entry='s1 ok ok down '+('down '*12)+'ok '+('down down ' if sy['MARIO_GAME_STATE']==4 else 'down ')
shots=O.relative_to(R).as_posix()+'/'
back_to_2048='up up' if sy['MARIO_GAME_STATE']==4 else 'up'
back_to_mario='down down' if sy['MARIO_GAME_STATE']==4 else 'down'
scenarios={
 'play':entry+f'shot:{shots}mario-launcher.png ok shot:{shots}start.png wait hold:right shot:{shots}walk.png jump-right shot:{shots}jump.png info quick-tap info dual-jump release-ok info scroll shot:{shots}scroll.png solve shot:{shots}won.png info fall shot:{shots}lost.png info menu wait {back_to_2048} ok right menu {back_to_mario} ok s1 wait',
 'display':entry+'ok hold:right evf wait'
}
reports={}
for name,script in scenarios.items():
 with (O/(name+'.log')).open('w') as log:
  subprocess.run(['node',str(O/'play.mjs'),(R/'work/om-emu/emu').as_uri(),str(G/'row-main.bin'),str(B/'paired.omsd'),str(O/(name+'.json')),str(O/(name+'-saved.omsd')),script],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 j=json.loads((O/(name+'.json')).read_text());assert not j['engineErrors'],j['engineErrors']
 events=j['log']; reports[name]=events
 if name=='play':
  find=lambda step:next(e for e in events if e['step']==step)
  assert find('hold:right')['x']>find(f'shot:{shots}start.png')['x']
  assert find('jump-right')['y']>0
  assert find('solve')['x']>=1104 and find('solve')['camera']==768
  assert find('scroll')['camera']>0
  assert find('quick-tap')['y']>0 and find('quick-tap')['keys']==0
  assert find('dual-jump')['keys'] & 8 and not(find('dual-jump')['keys'] & 4)
  assert find('release-ok')['keys']==0
  assert all(e['camera']==0 and e['x']==18 for e in events if e['step']=='info')
  assert find('solve')['result']==1 and find('solve')['timer']==0
  assert find('fall')['result']==2 and find('fall')['timer']==0
  paused=next(i for i,e in enumerate(events) if e['step']=='menu')
  assert events[paused]['menu'][0]==1 and events[paused]['timer']==0
  assert events[paused+1]['ticks']==events[paused]['ticks']
  puzzle=next(e for e in events if e['step']=='right' and e['menu'][0]==2)
  assert puzzle['moves']>0 and puzzle['timer']==0
  assert events[-2]['step']=='s1' and events[-2]['menu'][0]==0
 else:
  switched=next(e for e in events if e['step']=='evf')
  assert switched['menu'][0]==0 and switched['paintValid']==0
 assert events[-1]['timer']==0 and events[-1]['keys']==0
 assert events[-1]['ticks']==events[-2]['ticks']
 print(name,'passed')
report={'status':'passed','image_sha256':hashlib.sha256((G/'row-main.bin').read_bytes()).hexdigest(),
 'checks':['launcher','horizontal camera scrolling','full three-screen course','short tap latch','independent Up and OK','held movement','simultaneous jump','course win','gap loss','INFO restart',
 'MENU stops timer','2048 still moves','shutter stops timer','display switch clears state and stops timer'],
 'limitations':['emulator only','physical timing and input untested']}
(O/'validation.json').write_text(json.dumps(report,indent=2))
