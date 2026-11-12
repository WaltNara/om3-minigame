"""Run the actual native firmware in om-emu, retaining reviewable evidence."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'work/native-build'
build = json.loads((OUT/'build.json').read_text())
env = dict(os.environ, OM_EMU_MODEL='E147',
           GAME_STATE=f"{build['symbols']['game_state']:x}",
           GAME_CARD_FILES=str(ROOT/'vendor/caduceus-om3/releases/v0.26.2'))
mode = sys.argv[1] if len(sys.argv)>1 else 'explore'
script = {
 'seed':'s1 seed',
 'explore': 's1 ok ok down shot:work/native-build/entry.png info shot:work/native-build/high.png left info shot:work/native-build/win.png left info shot:work/native-build/low.png main+1 main-1 sub+1 sub-1 hold:ok shot:work/native-build/reset.png menu s1',
 'validate': 's1 vals ok ok down shot:work/native-build/entry.png info shot:work/native-build/high.png left info shot:work/native-build/win.png left info shot:work/native-build/low.png right right right right right right right left main+1 main-1 sub+1 sub-1 hold:ok vals up right down shot:work/native-build/color2.png menu s1',
}[mode]
card = 'blank.omsd' if mode=='seed' else 'paired.omsd'
save = 'paired.omsd' if mode=='seed' else f'{mode}-saved.omsd'
if os.environ.get('NATIVE_TRACE'):
    env['WATCH'] = ','.join(f"{build['symbols'][k]:x}" for k in ['game_init','game_info','game_up','game_down','game_event'])
else:
    env.pop('WATCH',None)
with (OUT/f'{mode}.log').open('w',encoding='utf-8') as log:
    p=subprocess.run(['node',str(OUT/'replay.mjs'),(ROOT/'work/om-emu/emu').as_uri(),
          str(OUT/'main.bin'),str(OUT/card),str(OUT/f'{mode}.json'),str(OUT/save),script],
          cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
if p.returncode:
    print((OUT/f'{mode}.log').read_text(encoding='utf-8')[-5000:])
    raise SystemExit(p.returncode)
r=json.loads((OUT/f'{mode}.json').read_text())
for e in r['log']:
    print(e['step'],e.get('game'),e['gui'],e.get('gdesc'))
print('native handler hits:',len(r['hits']))
if mode=='validate':
    rows=r['log']
    games=[e['game'][:3] for e in rows]
    checks={}
    for label,state in [('high',[5,4,2]),('win',[4,4,3]),('low',[3,4,1]),('wrap_up',[1,4,0]),('wrap_down',[9,4,0]),('reset',[5,8,0])]:
        assert state in games,(label,state,games)
        checks[label]=True
    opening=next(e for e in rows if e['step']=='down')
    assert opening['game']==[5,4,0,1] and int(opening['gptr'],16)!=0
    other=next(e for e in rows if e['step'].endswith('color2.png'))
    assert other['edk']==1 and other['game'][3]==0,other
    assert other['gdesc']==[4022,'a49ebe40']
    assert not (0xa0f59800<=int(other['gselect'][1],16)<0xa0f99800)
    assert rows[-2]['gui']=='SS_MENU/ID_ST_MENU'
    assert rows[-1]['gui']=='SS_COMMON/ID_ST_CA_REQ_DISP'
    assert rows[-1]['game'][3]==0
    vals=[json.loads(line[5:]) for line in (OUT/f'{mode}.log').read_text().splitlines() if line.startswith('VALS ')]
    assert len(vals)==2 and all('X' not in row for v in vals for row in v)
    # The last two slash fields are editor cursors; compare all photo settings.
    assert [x.rsplit('/',2)[0] for x in vals[0]]==[x.rsplit('/',2)[0] for x in vals[1]],vals
    slots=[e['slots'] for e in rows if 'slots' in e]
    assert all(v==slots[0] for v in slots)
    checks.update(paired_guides_loaded=True,other_color_restored=True,menu_exit=True,half_press_exit=True,photo_settings_unchanged=True)
    def guide_pixels(path):
        png=path.read_bytes(); o=8; data=b''
        while o<len(png):
            n=int.from_bytes(png[o:o+4],'big'); kind=png[o+4:o+8]
            if kind==b'IDAT': data+=png[o+8:o+8+n]
            o+=12+n
        raw=zlib.decompress(data); stride=900*3+1
        assert len(raw)==stride*600 and all(raw[y*stride]==0 for y in range(600))
        return b''.join(raw[y*stride+1+360*3:y*stride+1+540*3] for y in range(528,578))
    panels=[guide_pixels(OUT/f'{n}.png') for n in ['entry','high','win','low']]
    assert len(set(panels))==4,'Game images did not reach the composed screen'
    checks['four_distinct_rendered_panels']=True
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(OUT/'candidate.bin')==build['candidate_sha256']
    report={'status':'passed in om-emu; not camera-tested',
            'candidate_sha256':build['candidate_sha256'],'main_sha256':build['main_sha256'],
            'checks':checks,'steps':len(rows),
            'source_sha256':{p.name:sha(p) for p in (ROOT/'native').iterdir() if p.is_file()}}
    (OUT/'validation.json').write_text(json.dumps(report,indent=2))
    print('PASS:',', '.join(checks))
