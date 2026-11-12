"""Probe an OM-3 periodic timer without touching GUI state."""
import json, os, struct, subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]; O=R/'work/mario-timer'; B=R/'work/native-build'; T=R/'work/toolchain'; O.mkdir(parents=True,exist_ok=True)
def run(a,**kw): subprocess.run(a,check=True,**kw)
run([str(T/'gas/as-new.exe'),'-o',str(O/'timer.o'),str(R/'native/mario_timer_probe.s')])
run([str(T/'gas/as-new.exe'),'-o',str(O/'core.o'),str(R/'native/mario_core.s')])
run([str(T/'ld/ld-new.exe'),'-Ttext','0x60f59800','-e','mario_timer_start','--defsym=timer_create=0x6007662a','--defsym=timer_delete=0x60076665','-o',str(O/'timer.elf'),str(O/'timer.o'),str(O/'core.o')])
run([str(T/'binutils/objcopy.exe'),'-O','binary','-j','.text',str(O/'timer.elf'),str(O/'timer.bin')])
nm=subprocess.check_output([str(T/'binutils/nm-new.exe'),str(O/'timer.elf')],text=True); sy={s[2]:int(s[0],16) for line in nm.splitlines() if len(s:=line.split())==3}
base=0x60021020; start=0x60f59800; blob=(O/'timer.bin').read_bytes(); image=bytearray((B/'base-main.bin').read_bytes())
assert set(image[start-base:start-base+len(blob)])=={255}; image[start-base:start-base+len(blob)]=blob
struct.pack_into('<I',image,0x60045e9c-base,start+((len(blob)+0x7ff)//0x800)*0x800); (O/'main.bin').write_bytes(image)
spec=[{'name':'arm','pc':'B','regs':{},'mem':[['B','dd000000000004cb'],['B+1','='+str(sy['mario_timer_start'])+'-B']], 'stop':['B+7'],'max':300000,'read':[[sy['mario_timer_handle'],2]]}]
(O/'spec.json').write_text(json.dumps(spec))
stop=[{'name':'stop','pc':'B','regs':{},'mem':[['B','dd000000000004cb'],['B+1','='+str(sy['mario_timer_stop'])+'-B']], 'stop':['B+7'],'max':300000}]
(O/'stop.json').write_text(json.dumps(stop))
s=(B/'replay.mjs').read_text(); needle='  log.push(e);'; assert s.count(needle)==1
s=s.replace("t === 'ncall'","t === 'ncall' || t === 'stop'").replace("fs.readFileSync(process.env.NCALL, 'utf8')","fs.readFileSync(t === 'stop' ? process.env.NSTOP : process.env.NCALL, 'utf8')")
s=s.replace('process.env.NOUT, rec)', "(t === 'stop' ? process.env.NSTOP_OUT : process.env.NOUT), rec)")
s=s.replace(needle,f"  e.timerCount=u32({sy['mario_timer_count']}); e.playerX=u32({sy['mario_state']});\n"+needle); (O/'replay.mjs').write_text(s)
env=dict(os.environ,OM_EMU_MODEL='E147',NCALL=str(O/'spec.json'),NOUT=str(O/'results.json'),NSTOP=str(O/'stop.json'),NSTOP_OUT=str(O/'stop-result.json'))
for key in ('GAME_STATE','GAME_GC','WATCH','WSTACK','WFROM','WIDS'): env.pop(key,None)
with (O/'run.log').open('w') as log:
 run(['node',str(O/'replay.mjs'),(R/'work/om-emu/emu').as_uri(),str(O/'main.bin'),str(B/'paired.omsd'),str(O/'run.json'),str(O/'saved.omsd'),'s1 ncall wait wait stop wait'],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
result=json.loads((O/'results.json').read_text())['out'][0]; assert result['steps']<300000,result
handle=int.from_bytes(bytes.fromhex(result['mem'][0]),'little'); assert handle, result
log=json.loads((O/'run.json').read_text())['log']; counts=[e['timerCount'] for e in log if e['step'] in ('ncall','wait','stop')]
assert len(counts)==5 and counts[2]>counts[1]>counts[0] and counts[4]==counts[3],counts
xs=[e['playerX'] for e in log if e['step'] in ('ncall','wait','stop')]
assert xs[2]>xs[1]>xs[0] and xs[4]==xs[3],xs
print('Timer and player advance and stop in OM-Emu:',counts,xs)
