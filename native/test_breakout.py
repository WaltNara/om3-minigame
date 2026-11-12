"""Breakout native rules/render bounds and E147 full-camera button replay."""
import hashlib,json,os,struct,subprocess,zlib
from pathlib import Path
from breakout_assets import RECTS
R=Path(__file__).resolve().parents[1];G=R/'work/combined-game';O=G/'breakout';B=R/'work/native-build'
O.mkdir(exist_ok=True)
build=json.loads((G/'build.json').read_text());sy=build['symbols'];env=dict(os.environ,OM_EMU_MODEL='E147')
for key in ('NCALL','NOUT','GAME_STATE','GAME_GC','WATCH','WSTACK','WFROM','WIDS'):env.pop(key,None)
def replay(name,source,script,extra=None):
    (O/(name+'.mjs')).write_text(source,encoding='utf-8')
    with (O/(name+'.log')).open('w') as log:
        subprocess.run(['node',str(O/(name+'.mjs')),(R/'work/om-emu/emu').as_uri(),str(G/'row-main.bin'),str(B/'paired.omsd'),str(O/(name+'.json')),str(O/(name+'.omsd')),script],cwd=R,env=dict(env,**(extra or {})),stdout=log,stderr=subprocess.STDOUT,check=True)
    j=json.loads((O/(name+'.json')).read_text());assert not j['engineErrors'],j['engineErrors'];return j
base=(B/'replay.mjs').read_text()
s=base.replace('  log.push(e);',f"  e.br=Array.from({{length:9}},(_,i)=>u32({sy['breakout_state']}+i*4)); e.bricks=[...rd({sy['breakout_bricks']},18)]; e.menu=[...rd({sy['games_state']},2)]; e.timer=u16({sy['mario_handle']}); e.ticks=u32({sy['mario_ticks']}); e.touchOn=s.touch_on;\n  log.push(e);")
s=s.replace("  else if (t.startsWith('hold:'))", """  else if(t.startsWith('touch:')) {const [act,x,y]=t.slice(6).split(',');s.touch(act,+x,+y);s.idle_slice(lab.lab_time()+250e6);while(s.pending_touch())s.touch_gui_step();}
  else if(t.startsWith('gui-touch:')) {const [kind,x,y]=t.slice(10).split(',').map(Number);if(!s.touch_index){for(let i=1;i<=334;i++)if(lab.message_for(i)===0x9100){s.touch_index=i;break;}}s.post_touch(kind,x,y);}
  else if(t==='evf'){s.display_input('eye',1);}
  else if (t.startsWith('hold:'))""")
s=s.replace('curStep = t; s.idle_slice(lab.lab_time() + 1200e6)', 'curStep = t; s.idle_slice(lab.lab_time() + 250e6)')
entry='s1 ok ok down '+('down '*12)+'ok down down down '
shots=O.relative_to(R).as_posix()+'/'

def native_checks():
    def st(**kw):
        names='p x y dx dy mode lives remaining active'.split();v=[38,47,99,1,-2,0,3,18,0]
        for k,value in kw.items():v[names.index(k)]=value
        return v
    allbr=[1]*18;last=[1]+[0]*17;none=[0]*18
    cases=[
      ('reset','breakout_reset',st(mode=3,lives=0,remaining=0),none,{},st()),
      ('serve','breakout_serve',st(),allbr,{},st(mode=1)),
      ('extra OK cannot launch again','breakout_serve',st(x=60,y=70,mode=1),allbr,{},st(x=60,y=70,mode=1)),
      ('ready moves','breakout_step',st(),allbr,{'d0':2},st(p=41,x=50)),
      ('left clamp','breakout_step',st(p=2,x=11),allbr,{'d0':1},st(p=2,x=11)),
      ('ball travels','breakout_step',st(mode=1),allbr,{'d0':0},st(mode=1,x=49,y=97)),
      ('left wall','breakout_step',st(x=2,y=60,dx=-1,mode=1),allbr,{'d0':0},st(x=3,y=58,dx=1,mode=1)),
      ('right wall','breakout_step',st(x=92,y=60,mode=1),allbr,{'d0':0},st(x=91,y=58,dx=-1,mode=1)),
      ('ceiling','breakout_step',st(x=20,y=25,mode=1),allbr,{'d0':0},st(x=22,y=26,dy=2,mode=1)),
      ('paddle left','breakout_step',st(x=40,y=99,dy=2,mode=1),allbr,{'d0':0},st(x=40,y=99,dx=-1,dy=-2,mode=1)),
      ('paddle right','breakout_step',st(x=53,y=99,dy=2,mode=1),allbr,{'d0':0},st(x=55,y=99,dx=1,dy=-2,mode=1)),
      ('miss serve','breakout_step',st(x=5,y=107,dy=2,mode=1),allbr,{'d0':0},st(lives=2)),
      ('last miss','breakout_step',st(x=5,y=107,dy=2,mode=1,lives=1),allbr,{'d0':0},st(x=6,y=108,dy=2,mode=3,lives=0)),
      ('last brick','breakout_step',st(x=5,y=35,mode=1,remaining=1),last,{'d0':0},st(x=6,y=35,dy=2,mode=2,remaining=0)),
      ('brick side','breakout_step',st(x=14,y=31,dx=-1,mode=1),allbr,{'d0':0},st(x=15,y=29,dx=1,mode=1,remaining=17)),
      ('won stable','breakout_step',st(mode=2,remaining=0),none,{'d0':0},st(mode=2,remaining=0)),
    ]
    spec=[]
    for name,fn,v,br,regs,want in cases:
        spec.append({'name':name,'pc':'B','regs':dict(d2=0x2222,d3=0x3333,a2=0x4444,a3=0x5555,**regs),'mem':[['B','dd000000000004cb'],['B+1','='+str(sy[fn])+'-B'],[sy['breakout_state'],struct.pack('<9i',*v).hex()],[sy['breakout_bricks'],bytes(br).hex()]],'stop':['B+7'],'max':20000,'read':[[sy['breakout_state'],54]]})
    frames=[st(),st(p=2,x=3,y=60,mode=1,remaining=9),st(p=74,x=83,y=35,mode=2,remaining=0),st(x=6,y=108,mode=3,lives=0)]
    cap=build['mario_resources']['capacity']
    for i,v in enumerate(frames):
        br=allbr if i==0 else [k%2 for k in range(18)] if i==1 else none
        spec.append({'name':f'frame-{i}','pc':'B','regs':{'d2':0x2222,'d3':0x3333,'a2':0x4444,'a3':0x5555},'mem':[['B','dd000000000004cb'],['B+1','='+str(sy['breakout_paint'])+'-B'],[sy['breakout_state'],struct.pack('<9i',*v).hex()],[sy['breakout_bricks'],bytes(br).hex()],[sy['mario_buffer_end'],'dec0ad0b']],'stop':['B+7'],'max':400000,'read':[[sy['mario_buffer'],cap+4]]})
    (O/'spec.json').write_text(json.dumps(spec));replay('native',base,'s1 ncall',{'NCALL':str(O/'spec.json'),'NOUT':str(O/'native-results.json')})
    results=json.loads((O/'native-results.json').read_text())['out'];assert len(results)==len(spec)
    for result in results:
        for reg,value in [('d2',0x2222),('d3',0x3333),('a2',0x4444),('a3',0x5555)]:assert int(result['regs'][reg],16)==value,(result['name'],reg)
    for result,case in zip(results,cases):
        got=list(struct.unpack('<9i',bytes.fromhex(result['mem'][0])[:36]));assert got==case[-1],(case[0],got,case[-1])
        assert result['steps']<20000
        bricks=list(bytes.fromhex(result['mem'][0])[36:]);assert sum(bricks)==got[7],(case[0],bricks,got)
    for i,(result,v) in enumerate(zip(results[len(cases):],frames)):
        assert result['steps']<400000
        raw=bytes.fromhex(result['mem'][0]);assert raw[-4:]==bytes.fromhex('dec0ad0b');assert raw[:4]==struct.pack('<I',0x0b17f1df)
        off=4;raster=[]
        for y in range(480):
            px=[]
            while len(px)<384:
                word=int.from_bytes(raw[off:off+8],'little');off+=8;assert word>>60==0
                for k in range(5):
                    token=(word>>(12*k))&4095;px.extend([token>>4]*((token&15)+1))
            assert len(px)==384;raster+=px
            if 96<=y<432:
                ly=y//4;cells=[int(x<2 or x>=94 or ly==24) for x in range(96)]
                br=allbr if i==0 else [k%2 for k in range(18)] if i==1 else none
                for k,(x1,x2,y1,y2) in enumerate(RECTS):
                    if br[k] and y1<=ly<y2:cells[x1:x2]=[1]*(x2-x1)
                if 102<=ly<104:cells[v[0]:v[0]+20]=[1]*20
                if v[2]<=ly<v[2]+2:cells[v[1]:v[1]+2]=[1]*2
                assert px==[10 if c else 7 for c in cells for _ in range(4)],(i,y)
        assert off<=build['breakout_resources']['max_output_bytes']<=cap
        def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d))
        pixels=b''.join(b'\0'+b''.join(bytes((235,235,230) if c==10 else (26,30,36)) for c in raster[y*384:(y+1)*384]) for y in range(480))
        (O/f'frame-{i}.png').write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',384,480,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(pixels))+chunk(b'IEND',b''))
    print(len(cases),'native rules and',len(frames),'pixel-exact frames passed',flush=True)
    return {'cases':len(cases),'frames':len(frames),'render_max_steps':max(r['steps'] for r in results[len(cases):])}


def playability():
    # Drive only public game inputs from a deterministic paddle bot, starting
    # with reset. No ball/brick state writes: prove the native course can clear.
    js=f"""  else if(t==='autoplay') {{
      const dd=Debugger.attach(lab.sim,{{lab}}),saved=dd.m.getRegs().slice();
      const sp=((saved[8]-0x800)&~3)>>>0,b=((sp-0x6000)&~255)>>>0;
      const invoke=(fn,d0=0,d1=0,a0=0)=>{{
        const code=Buffer.from('dd000000000004cb','hex');code.writeInt32LE(fn-b,1);dd.write(b,code);
        const r=saved.slice();r[0]=d0;r[1]=d1;r[4]=a0;r[8]=sp;r[9]=b;r[14]=0;dd.m.setRegs(r);
        let n=0;while((dd.m.getRegs()[9]>>>0)!==b+7 && n++<20000){{dd.m.step();if(dd.m.getRegs()[14])throw Error('autoplay native fault');}}
        if(n>=20000)throw Error('autoplay timeout');
      }};
      invoke({sy['breakout_reset']});invoke({sy['breakout_serve']});
      let frames=0;
      for(;frames<6000 && u32({sy['breakout_state']+20})===1;frames++){{
        const ball=u32({sy['breakout_state']+4}),offset=frames%137<68?5:15;
        const paddle=Math.max(2,Math.min(74,ball-offset));
        const current=u32({sy['breakout_state']});
        invoke({sy['breakout_step']},current<paddle-1?2:current>paddle+1?1:0);
      }}
      const result={{frames,mode:u32({sy['breakout_state']+20}),lives:u32({sy['breakout_state']+24}),bricks:u32({sy['breakout_state']+28})}};
      dd.m.setRegs(saved);fs.writeFileSync('{(O/'playability-result.json').as_posix()}',JSON.stringify(result));
    }}
"""
    replay('playability',base.replace("  else if (t.startsWith('hold:'))",js+"  else if (t.startsWith('hold:'))"),'s1 autoplay')
    result=json.loads((O/'playability-result.json').read_text());assert result['mode']==2 and result['bricks']==0,result
    print('Native input-driven full clear:',result,flush=True)
    return result

def camera_checks():
    assert 'breakout_touch' not in sy and 'br_touch_anchor' not in sy
    src=s.replace('  log.push(e);', '  e.touchForwarded=globalThis.touchForwarded||0;\n  log.push(e);')
    src=src.replace('const WATCH =', "const ft=Debugger.attach(lab.sim,{lab});ft.traceExec((r)=>{if(r.d0===0x9100)globalThis.touchForwarded=(globalThis.touchForwarded||0)+1;},{pcs:[0x610fd345]});const WATCH =")
    src=src.replace("  else if(t==='evf')", "  else if(t.startsWith('poke:')) {const [a,h]=t.slice(5).split('@');lab.sim.write(parseInt(a,16)>>>0,Uint8Array.from(Buffer.from(h,'hex'))); }\n  else if(t==='evf')")
    src=src.replace("  else if(t==='evf')", f"""  else if(t==='rally') {{
      for(let i=0;i<180 && u32({sy['breakout_state']+20})===1;i++){{
        const target=u32({sy['breakout_state']+4})-9,current=u32({sy['breakout_state']});
        s.key('left',current>target+1?'down':'up');
        s.key('right',current<target-1?'down':'up');s.camapp.pump();
        s.idle_slice(lab.lab_time()+120e6);
      }}
      s.key('left','up');s.key('right','up');s.camapp.pump();
    }} else if(t==='stale-tick') {{
      lab.calls({sy['mario_post_tick']-0x10021020},{{a0:u32({sy['mario_epoch']})-1}});
    }} else if(t==='evf')""")
    def poke(v,br):return f'poke:{sy["breakout_state"]:x}@'+struct.pack('<9i',*v).hex()+f' poke:{sy["breakout_bricks"]:x}@'+bytes(br).hex()
    win=poke([38,5,35,1,-2,1,3,1,0],[1]+[0]*17)
    loss=poke([38,5,107,1,2,1,1,18,0],[1]*18)
    scripts={
      'play':entry+f'shot:{shots}breakout-launcher.png ok shot:{shots}breakout-ready.png '
        f'hold:right info ok rally shot:{shots}breakout-rally.png info {win} wait shot:{shots}breakout-won.png '
        f'info {loss} wait shot:{shots}breakout-lost.png info menu wait stale-tick up ok hold:right menu down ok s1 wait',
      'display':entry+'ok evf wait',
      'touch-stock':entry+'ok gui-touch:1,350,450 gui-touch:6,550,450 gui-touch:3,550,450 gui-touch:4,450,450 wait'
    }
    logs={name:replay(name,src,script)['log'] for name,script in scripts.items()}
    events=logs['play'];find=lambda step:next(e for e in events if e['step']==step)
    for e in logs['touch-stock']:
        if e['step'].startswith('gui-touch:'):
            assert e['touchForwarded']>0 and e['br']==[38,47,99,1,4294967294,0,3,18,0],e
    for e in events:
        if e['step']=='info':assert e['br'][5:8]==[0,3,18]
    assert find('hold:right')['br'][0]>38
    assert find('rally')['br'][7]<18 and find('rally')['br'][6]>0
    for suffix,mode in [('won',2),('lost',3)]:
        e=find(f'shot:{shots}breakout-{suffix}.png');assert e['br'][5]==mode and e['timer']==0
    first=next(i for i,e in enumerate(events) if e['step']=='menu')
    assert events[first]['menu'][0]==1 and events[first]['timer']==0
    assert events[first]['ticks']==events[first+1]['ticks']==events[first+2]['ticks']
    for name in logs:
        assert logs[name][-1]['menu'][0]==0 and logs[name][-1]['timer']==0
        assert logs[name][-1]['ticks']==logs[name][-2]['ticks']
    assert any(e['menu'][0]==4 and e['timer'] for e in events)
    print('Button rally, touch pass-through, endings and lifecycle passed',flush=True)
    return ['touch symbols absent','touch forwarded unchanged with no game action','held buttons','OK serve','button-driven rally','INFO restart','win/loss via near-end states','MENU/shutter/display exits','stale tick ignored','Mario cross-game']

if __name__=='__main__':
    report=native_checks()
    report['full_clear']=playability()
    report.update(status='passed',image_sha256=hashlib.sha256((G/'row-main.bin').read_bytes()).hexdigest(),checks=camera_checks(),limitations=['button-only revision not yet tested on physical camera','previous release froze on Breakout entry; root cause not proven'])
    (O/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
