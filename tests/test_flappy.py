"""Native flight rules, render guards/raster and GUI lifecycle for both variants."""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[1] / "native"), str(_Path(__file__).resolve().parents[1] / "tests")]
import json,os,struct,subprocess,random
from mines_assets import FONT
from pathlib import Path
R=Path(__file__).resolve().parents[1];G=R/os.environ.get('OM3_FLAPPY_BUILD','work/flappy-buttons');O=G/'validation';B=R/'work/native-build'
O.mkdir(exist_ok=True);meta=json.loads((G/'build.json').read_text());s=meta['symbols']
base=(B/'replay.mjs').read_text()
env=dict(os.environ,OM_EMU_MODEL='E147')
for k in ('WATCH','NCALL','NOUT','GAME_STATE','GAME_GC','WRANGE','WSTACK'):env.pop(k,None)
def replay(name,script,source=base,extra=None):
    (O/(name+'.mjs')).write_text(source)
    with (O/(name+'.log')).open('w') as f:
        subprocess.run(['node',str(O/(name+'.mjs')),(R/'work/om-emu/emu').as_uri(),str(G/'row-main.bin'),str(B/'paired.omsd'),str(O/(name+'.json')),str(O/(name+'.omsd')),script],cwd=R,env=dict(env,**(extra or {})),stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240)
    j=json.loads((O/(name+'.json')).read_text());assert not j['engineErrors'];return j
def next_pipe(seed,x,gap):
    seed^=(seed<<13)&0xffffffff;seed^=seed>>17;seed^=(seed<<5)&0xffffffff
    spacing=56+16*(seed&3)
    delta=(seed>>2)&7
    if spacing==56:delta=min(delta,3)
    elif spacing>=88:delta=min(delta*2,12)
    if seed&32:delta=-delta
    return seed,x+spacing,max(32,min(63,gap+delta))

def initial(seed=0x6d2b79f5):
    seed,x,gap=next_pipe(seed,90,45)
    return [240,0,90,45,0,0,seed,x,gap]
def step(v,tap):
    v=v.copy()
    if v[4]==2:
        if not tap:return v
        v=initial()
    if tap:v[4]=1;v[1]=-10
    if v[4]!=1:return v
    v[1]=min(10,v[1]+1);v[0]+=v[1]
    if v[0]<104 or v[0]>412:v[4]=2;return v
    v[5]=min(99999999,v[5]+1)
    v[2]-=1;v[7]-=1
    for slot,other in [(2,7),(7,2)]:
        if v[slot]<-12:
            v[6],v[slot],v[slot+1]=next_pipe(v[6],v[other],v[other+1])
        if v[slot]<30 and v[slot]+12>24:
            if v[0]<v[slot+1]*4 or v[0]+16>(v[slot+1]+32)*4:v[4]=2
    return v
def pilot(v):
    ahead=[i for i in (2,7) if v[i]+12>24]
    slot=min(ahead,key=lambda i:v[i])
    return int(v[4]==0 or (v[0]>(v[slot+1]+17)*4 and v[1]>=0))

# Independent playability/property check across many streams; this strategy
# uses one press per flap with ample release time, no coordinate teleporting.
spacings=set();pair_count=0;min_flap_interval=9999
for seed in [0x6d2b79f5]+list(range(1,17)):
    pv=initial(seed);last_flap=-9999
    for tick in range(3000):
        press=pilot(pv)
        if press:min_flap_interval=min(min_flap_interval,tick-last_flap);last_flap=tick
        old=pv;pv=step(pv,press)
        assert pv[4]==1,(seed,tick,pv)
        for slot,other in [(2,7),(7,2)]:
            if old[slot]==-12:
                spacing=pv[slot]-pv[other];spacings.add(spacing);pair_count+=1
                assert spacing in (56,72,88,104)
                assert abs(pv[slot+1]-pv[other+1])<={56:3,72:7,88:12,104:12}[spacing]
        assert 32<=pv[3]<=63 and 32<=pv[8]<=63
    assert pv[5]==3000
assert spacings=={56,72,88,104} and min_flap_interval>=10
cases=[];v=initial()
for i in range(1500):
    tap=pilot(v)
    w=step(v,tap);cases.append((v.copy(),tap,w));v=w
assert v[5]==1500 and v[4]==1,v
rng=random.Random(6)
for _ in range(250):
    x=rng.randrange(-12,97);spacing=rng.choice([56,72,88,104]);gap=rng.randrange(32,64)
    v=[rng.randrange(95,420),rng.randrange(-10,11),x,gap,rng.randrange(3),rng.randrange(99999990,100000000),rng.randrange(1,2**32),x+spacing,max(32,min(63,gap+rng.randrange(-3,4)))]
    if rng.randrange(2):v[2],v[7],v[3],v[8]=v[7],v[2],v[8],v[3]
    tap=rng.randrange(2);cases.append((v,tap,step(v,tap)))
spec=[]
for i,(v,tap,w) in enumerate(cases):
    spec.append(dict(name=str(i),pc='B',regs=dict(d2=0x2222,d3=0x3333,a2=0x4444,a3=0x5555),mem=[['B','dd000000000004cb'],['B+1','='+str(s['flappy_step'])+'-B'],[s['flappy_state'],struct.pack('<9I',*[x&0xffffffff for x in v]).hex()],[s['flappy_pending'],bytes([tap]).hex()]],stop=['B+7'],max=10000,read=[[s['flappy_state'],37]]))
frames=[initial()]
frames += [[y,0,x,g,m,99999999,1,x+spacing,max(32,min(63,g+3))] for y,x,g,m in [(104,-12,32,0),(412,96,63,2),(240,24,45,1),(300,29,63,1),(128,3,32,1),(400,82,60,2)] for spacing in (56,72,88,104)]
swapped=frames[3].copy();swapped[2],swapped[7],swapped[3],swapped[8]=swapped[7],swapped[2],swapped[8],swapped[3];frames.append(swapped)
cap=meta['mario_resources']['capacity']
for i,v in enumerate(frames):
    spec.append(dict(name='frame'+str(i),pc='B',regs=dict(d2=0x2222,d3=0x3333,a2=0x4444,a3=0x5555),mem=[['B','dd000000000004cb'],['B+1','='+str(s['flappy_paint'])+'-B'],[s['flappy_state'],struct.pack('<9I',*[x&0xffffffff for x in v]).hex()],[s['mario_buffer_end'],'dec0ad0b']],stop=['B+7'],max=500000,read=[[s['mario_buffer'],cap+4],[s['fp_score_text'],32]]))
(O/'spec.json').write_text(json.dumps(spec));replay('native','s1 ncall',extra=dict(NCALL=str(O/'spec.json'),NOUT=str(O/'native-results.json')))
j=json.loads((O/'native-results.json').read_text());assert len(j['out'])==len(spec)
for result,cs in zip(j['out'],spec):
    assert result['steps']<cs['max'];assert int(result['regs']['sp'],16)==int(j['SP'],16)
    for reg,val in cs['regs'].items():assert int(result['regs'][reg],16)==val
for r,(v,tap,w) in zip(j['out'],cases):
    raw=bytes.fromhex(r['mem'][0]);actual=list(struct.unpack('<6iI2i',raw[:36]));assert actual==w,(r['name'],actual,w)
    assert raw[36]==0
for r,v in zip(j['out'][len(cases):],frames):
    hud=f'DISTANCE {v[5]:08}M              '
    assert bytes.fromhex(r['mem'][1]).decode()==hud
    raw=bytes.fromhex(r['mem'][0]);assert raw[-4:]==bytes.fromhex('dec0ad0b')
    pixels=[];off=4
    for y in range(480):
        row=[]
        while len(row)<384:
            word=int.from_bytes(raw[off:off+8],'little');off+=8;assert word>>60==0
            for k in range(5):
                t=(word>>(12*k))&4095;row += [t>>4]*((t&15)+1)
        assert len(row)==384
        if 48<=y<96:
            want=[7]*384
            if 60<=y<75:
                gy=(y-60)//3
                for i,ch in enumerate(hud):
                    for gx,bit in enumerate(FONT.get(ch,FONT[' '])[gy]):
                        if bit=='1':want[i*12+1+gx*3:i*12+4+gx*3]=[10]*3
            assert row==want,(r['name'],'distance HUD',y)
        if 96<=y<432:
            yy=y//4
            want=[10 if x<2 or x>=94 or any((yy<v[i+1] or yy>=v[i+1]+32) and v[i]<=x<v[i]+12 for i in (2,7)) or (v[0]//4<=yy<v[0]//4+4 and 24<=x<30) else 7 for x in range(96) for _ in range(4)]
            assert row==want,(r['name'],y)
        pixels+=row
    assert off<=meta['flappy_resources']['max_output_bytes']<=cap
print('PASS native:',len(cases),'physics ticks,',len(frames),'frames; 1500-tick autopilot score',cases[1499][2][5],flush=True)
touch_enabled=meta.get('custom_game_touch',False)
if not touch_enabled:assert not any(k in s for k in ('flappy_touch','flappy_touch_repaired','flappy_contact','flappy_drain'))
raw=(G/'row-main.bin').read_bytes()
assert struct.unpack_from('<I',raw,0x615fbd40-0x60021020)[0]==(s['flappy_touch_repaired'] if touch_enabled else 0x61294d13)
source=base.replace('  log.push(e);',f"  e.flight=Array.from({{length:9}},(_,i)=>u32({s['flappy_state']}+4*i)); e.game=rd({s['games_state']},1)[0];e.pending=rd({s['flappy_pending']},1)[0];e.timer=u16({s['mario_handle']});\n  log.push(e);")
source=source.replace("  else if (t.startsWith('hold:'))","  else if(t.startsWith('gui-touch:')){const [k,x,y]=t.slice(10).split(',').map(Number);if(!s.touch_index){for(let i=1;i<=334;i++)if(lab.message_for(i)===0x9100){s.touch_index=i;break;}}s.post_touch(k,x,y);}\n  else if(t==='evf'){s.display_input('eye',1);}\n  else if (t.startsWith('hold:'))")
source=source.replace('curStep = t; s.idle_slice(lab.lab_time() + 1200e6)','curStep = t; s.idle_slice(lab.lab_time() + 250e6)')
entry='s1 ok ok '+('down '*13)+'ok '+('down '*4)+'ok '
touch='gui-touch:1,450,300 gui-touch:3,450,300 '
shots=O.relative_to(R).as_posix()+'/'
scripts=dict(play=entry+f'shot:{shots}ready.png ok up ok info '+f'shot:{shots}reset.png ok wait wait '+f'shot:{shots}flight.png menu s1',
    held=entry+'hold:ok menu s1',
    restart=entry+'ok '+('wait '*26)+'up info menu s1',
    menu=entry+'ok menu ok up s1',
    shutter=entry+'ok s1',
    display=entry+'up evf',
    stock_touch=entry+touch+'menu s1')
for name,script in scripts.items():
    log=replay(name,script,source)['log']
    entered=next(e for e in log if e['game']==6);assert entered['flight'][4]==0 and entered['flight'][5]==0 and entered['timer']!=0
    if name=='play':
        assert any(e['flight'][5]>0 for e in log),'Button never advanced distance'
        reset=next(e for e in log if e['step']=='info');assert reset['flight'][5]==0
    if name=='held':
        held=next(e for e in log if e['step']=='hold:ok')
        assert held['game']==6 and held['flight'][1]>0,held
    elif name=='restart':
        assert any(e['flight'][4]==2 for e in log)
        restarted=next(e for e in log if e['step']=='up')
        assert restarted['game']==6 and restarted['flight'][4]==1 and 0<restarted['flight'][5]<5
    elif name=='menu':
        exited=next(e for e in log if e['step']=='menu')
        assert exited['game']==1 and exited['timer']==0
    elif name=='stock_touch':
        ev=[e for e in log if e['step'].startswith('gui-touch:')]
        if touch_enabled:
            assert all(e['game']==6 and e['flight'][4]==1 and e['timer']!=0 for e in ev)
        else:
            assert ev[0]['game']==6 and ev[0]['flight'][4]==0 and ev[0]['pending']==0
            assert ev[1]['game']==0 and ev[1]['timer']==0
    assert log[-1]['game']==0 and log[-1]['timer']==0 and log[-1]['pending']==0
    print(name,'PASS',flush=True)
(O/'validation.json').write_text(json.dumps(dict(status='PASS emulator only',candidate_sha256=meta['candidate_sha256'],physics_cases=len(cases),render_frames=len(frames),gui_scenarios=list(scripts),playability=dict(streams=17,ticks_per_stream=3000,recycled_pairs=pair_count,spacings=sorted(spacings),min_flap_interval_ms=min_flap_interval*120),custom_game_touch=touch_enabled,physical_build_validated=False),indent=2))
