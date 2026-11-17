"""Native boundary and lifecycle checks on the exact linked Mario core."""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[1] / "native"), str(_Path(__file__).resolve().parents[1] / "tests")]
import hashlib,json,os,struct,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]; O=R/'work/mario-core'; B=R/'work/native-build'; G=R/os.environ.get('OM3_GAME_BUILD','work/combined-game')
O=G/'mario-core'
O.mkdir(parents=True,exist_ok=True)
sy=json.loads((G/'build.json').read_text())['symbols']

def state(**kw):
    names='x y vy held result camera mask coins block enemy dead direction facing tick grace buffer'.split()
    v=[18,0,0,0,0,0,0,0,0,620,0,1,0,0,0,0]
    for k,n in kw.items():v[names.index(k)]=n
    return v
# Each expected field is an externally visible rule, not an assembly trace.
cases=[
 ('idle',state(),0,{'x':18,'y':0}),
 ('right',state(),2,{'x':21}),
 ('left edge',state(x=0),1,{'x':0}),
 ('jump',state(),4,{'y':12,'vy':11}),
 ('held no repeat',state(held=4),4,{'y':0}),
 ('latched tap',state(),16,{'y':12,'held':0}),
 ('both jump keys',state(held=12),8,{'y':0,'held':8}),
 ('grace jump',state(x=330,y=-1,vy=-1,grace=1),16,{'y':11}),
 ('no infinite grace',state(x=330,y=-1,vy=-1),16,{'y':-2}),
 ('buffer landing',state(y=2,vy=-3),16,{'y':0,'buffer':1}),
 ('buffer takeoff',state(buffer=1),0,{'y':12,'buffer':0}),
 ('stair wall',state(x=147),2,{'x':147}),
 ('stair clear',state(x=147,y=20,vy=2),2,{'x':150,'y':22}),
 ('stair land',state(x=198,y=34,vy=-3),0,{'y':32,'vy':0}),
 ('camera threshold',state(x=228,y=48),2,{'camera':3,'x':231}),
 ('camera forward only',state(x=600,camera=372),1,{'camera':372,'x':597}),
 ('visible left edge',state(x=400,camera=400),1,{'x':400}),
 ('map end',state(x=1099,camera=768),2,{'camera':768,'result':0}),
 ('win',state(x=1102,camera=768),2,{'result':1}),
 ('result freezes',state(x=1105,result=1),1,{'x':1105}),
 ('pit loss',state(x=340,y=-31,vy=-3),0,{'result':2}),
 ('coin once',state(x=120,y=30,vy=0),0,{'mask':1,'coins':1}),
 ('coin persists',state(x=120,y=30,mask=1,coins=1),0,{'coins':1}),
 ('block reward',state(x=450,y=20,vy=8),0,{'block':1,'coins':1,'y':24,'vy':0}),
 ('block used',state(x=450,y=20,vy=8,block=1,coins=1),0,{'coins':1}),
 ('block landing',state(x=450,y=66,vy=-4),0,{'y':64,'vy':0}),
 ('enemy stomp',state(x=620,y=19,vy=-5,camera=392),0,{'dead':1,'vy':8,'y':16,'result':0}),
 ('enemy side',state(x=620,camera=392),0,{'result':2}),
 ('enemy gone',state(x=620,camera=392,dead=1),0,{'result':0}),
]
spec=[]
for name,st,keys,want in cases:
 spec.append({'name':name,'pc':'B','regs':{'d0':keys,'d2':0x2222,'d3':0x3333,'a2':0x4444,'a3':0x5555},
 'mem':[['B','dd000000000004cb'],['B+1','='+str(sy['mario_step'])+'-B'],[sy['mario_state'],struct.pack('<16i',*st).hex()]],
 'stop':['B+7'],'max':10000,'read':[[sy['mario_state'],64]]})
# Reset must restore camera, enemy, coins, result and forgiveness as one run.
spec.append({'name':'reset','pc':'B','mem':[['B','dd000000000004cb'],['B+1','='+str(sy['mario_reset'])+'-B']], 'stop':['B+7'],'max':10000,'read':[[sy['mario_state'],64]]})
(O/'spec.json').write_text(json.dumps(spec)); env=dict(os.environ,OM_EMU_MODEL='E147',NCALL=str(O/'spec.json'),NOUT=str(O/'results.json'))
for key in ('GAME_STATE','GAME_GC','WATCH','WSTACK','WFROM','WIDS'):env.pop(key,None)
with (O/'run.log').open('w') as log:
 subprocess.run(['node',str(B/'replay.mjs'),(R/'work/om-emu/emu').as_uri(),str(G/'row-main.bin'),str(B/'paired.omsd'),str(O/'run.json'),str(O/'saved.omsd'),'s1 ncall'],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
results=json.loads((O/'results.json').read_text())['out']; assert len(results)==len(spec)
names='x y vy held result camera mask coins block enemy dead direction facing tick grace buffer'.split()
for result,(_,_,_,want) in zip(results,cases):
 got=dict(zip(names,struct.unpack('<16i',bytes.fromhex(result['mem'][0]))))
 for k,v in want.items():assert got[k]==v,(result['name'],k,got,want)
 for reg,v in [('d2',0x2222),('d3',0x3333),('a2',0x4444),('a3',0x5555)]:assert int(result['regs'][reg],16)==v,(result['name'],reg)
 assert result['steps']<10000
assert list(struct.unpack('<16i',bytes.fromhex(results[-1]['mem'][0])))==state(grace=1)
(O/'validation.json').write_text(json.dumps({'status':'passed','cases':len(spec),'image_sha256':hashlib.sha256((G/'row-main.bin').read_bytes()).hexdigest(),'max_steps':max(r['steps'] for r in results)},indent=2))
print(len(spec),'native Mario checks passed')
