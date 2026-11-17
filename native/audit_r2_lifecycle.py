"""Read-only R2 image audit and repeated injected touch exits; no camera IO.

Outputs stay in work/r2-lifecycle-audit. This cannot model physical touch,
hardware stack margins, DMA ownership, or actual card/power timing.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'work/r2-lifecycle-audit'
BUILD = ROOT / 'work/combined-game'
BASE = ROOT / 'work/native-build'
RELEASE = ROOT / 'artifacts/om3-games-bundle-buttons-r2/card/OM3MOD'
R2_SHA = '9d4cc6e7ea2d57e53dc46f90cdc6527c54eb79af8197dec6461bfb3a4b8fb2b5'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    meta = json.loads((BUILD / 'build.json').read_text(encoding='utf-8'))
    sy = meta['symbols']
    image = BUILD / 'row-main.bin'
    assert hashlib.sha256(image.read_bytes()).hexdigest() == R2_SHA
    mismatch = [name for name, digest in meta['source_sha256'].items()
                if hashlib.sha256((ROOT / 'native' / name).read_bytes()).hexdigest() != digest]
    assert not mismatch, mismatch
    source = (BASE / 'replay.mjs').read_text(encoding='utf-8')
    source = source.replace("['GUIDES.BIN','LABELS.BIN','LOOKS.BIN','TONES.BIN']",
                            "['GUIDES.BIN','LABELS.BIN','TONES.BIN']")
    assert "['GUIDES.BIN','LABELS.BIN','TONES.BIN']" in source
    source = source.replace('  log.push(e);', f'''
  e.games=rd({sy['games_state']},1)[0];
  e.timer=u16({sy['mario_handle']}); e.epoch=u32({sy['mario_epoch']});
  e.ticks=u32({sy['mario_ticks']}); e.keys=rd({sy['mario_keys']},1)[0];
  e.paintValid=rd({sy['games_paint_valid']},1)[0];
  e.screen=u32({sy['games_screen']});
  e.touchSlot=u32(0x615fbd40); e.pmSlot=u32(0x615d0b08);
  log.push(e);''')
    source = source.replace("  else if (t.startsWith('hold:'))", '''
  else if(t.startsWith('gui-touch:')) {
    const [kind,x,y]=t.slice(10).split(',').map(Number);
    if(!s.touch_index) for(let i=1;i<=334;i++) if(lab.message_for(i)===0x9100){s.touch_index=i;break;}
    s.post_touch(kind,x,y);
  }
  else if(t==='stale-tick') {
    lab.calls(STALE_POST,{a0:(u32(EPOCH)-1)>>>0});
  }
  else if (t.startsWith('hold:'))'''.replace('STALE_POST', str(sy['mario_post_tick']-0x10021020)).replace('EPOCH',str(sy['mario_epoch'])))
    source = source.replace('curStep = t; s.idle_slice(lab.lab_time() + 1200e6)',
                            "curStep = t; s.idle_slice(lab.lab_time() + (t === 'wait' ? 1200e6 : 250e6))")
    script = OUT / 'replay.mjs'
    script.write_text(source, encoding='utf-8')
    env = dict(os.environ, OM_EMU_MODEL='E147', GAME_CARD_FILES=str(RELEASE))
    for key in ('NCALL','NOUT','GAME_STATE','GAME_GC','WATCH','WSTACK','WFROM','WIDS','WRANGE'):
        env.pop(key, None)

    def run(name, card, commands, extra=None):
        with (OUT / (name+'.log')).open('w',encoding='utf-8') as stream:
            subprocess.run(['node', str(script), (ROOT/'work/om-emu/emu').as_uri(),
                            str(image), str(card), str(OUT/(name+'.json')),
                            str(OUT/(name+'.omsd')), commands], cwd=ROOT, env=dict(env, **(extra or {})),
                           stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=300)
        result=json.loads((OUT/(name+'.json')).read_text(encoding='utf-8'))
        assert not result['engineErrors'], result['engineErrors']
        print(name, 'replay completed', flush=True)
        return result['log']

    entry='s1 ok ok '+('down '*13)+'ok '
    commands='wait gui-touch:1,450,300 gui-touch:3,450,300 wait '
    for cycle in range(3):
        for game in range(4):
            commands += entry+('down '*game)+'ok '
            if game >= 2:
                commands += 'hold:right '
            commands += 'gui-touch:1,450,300 gui-touch:3,450,300 stale-tick wait '
    if '--reuse-exit-replay' in sys.argv:
        previous=json.loads((OUT/'validation.json').read_text(encoding='utf-8'))
        assert previous['image_sha256']==R2_SHA and previous['game_touch_exits']==12
        replay=json.loads((OUT/'repeat-touch-exits.json').read_text(encoding='utf-8'))
        assert not replay['engineErrors']
        events=replay['log']
    else:
        run('seed', BASE/'blank.omsd', 'seed')
        events=run('repeat-touch-exits', OUT/'seed.omsd', commands)
    exits=[]
    entered=[]
    for i,e in enumerate(events):
        assert e['touchSlot']==0x61294d13 and e['pmSlot']==0x6125becc, e
        if e['step']=='gui-touch:1,450,300' and e['games'] >= 2:
            entered.append(e['games'])
            if e['games'] >= 4:
                assert e['timer'] != 0, e
        if e['step']=='gui-touch:3,450,300':
            assert e['games']==0 and e['timer']==0 and e['keys']==0, e
            assert e['paintValid']==0 and e['screen']==0, e
            exits.append(e)
            if i+2<len(events) and events[i+1]['step']=='stale-tick':
                assert e['ticks']==events[i+1]['ticks']==events[i+2]['ticks'], events[i:i+3]
    assert entered==[2,3,4,5]*3, entered
    assert len(exits)==13, len(exits)
    # Inspect the firmware's real periodic-timer pool, not just our handle.
    # R2 disassembly: create 0x60076b6d, delete 0x60076de7, 32 x 24-byte slots.
    # +2 is active, +12 callback, +16 callback argument (our generation).
    spec=[]
    for cycle in range(64):
        for fn in ('mario_start','mario_stop'):
            spec.append(dict(name=f'{cycle}:{fn}', pc='B',
                regs=dict(d2=0x2222,d3=0x3333,a2=0x4444,a3=0x5555),
                mem=[['B','dd000000000004cb'], ['B+1','='+str(sy[fn])+'-B']],
                stop=['B+7'], max=100000,
                read=[[sy['mario_handle'],2], [0xa32c47b8,32*24]]))
    (OUT/'timer-spec.json').write_text(json.dumps(spec),encoding='utf-8')
    run('timer-pool',OUT/'seed.omsd','s1 ncall',
        dict(NCALL=str(OUT/'timer-spec.json'),NOUT=str(OUT/'timer-results.json')))
    native=json.loads((OUT/'timer-results.json').read_text(encoding='utf-8'))
    for result in native['out']:
        assert result['steps']<100000, result['name']
        assert int(result['regs']['sp'],16)==int(native['SP'],16),result['name']
        for reg,value in [('d2',0x2222),('d3',0x3333),('a2',0x4444),('a3',0x5555)]:
            assert int(result['regs'][reg],16)==value,(result['name'],reg)
        pool=bytes.fromhex(result['mem'][1])
        active=[i for i in range(32)
                if int.from_bytes(pool[i*24+2:i*24+4],'little')==1
                and int.from_bytes(pool[i*24+12:i*24+16],'little')==sy['mario_tick_isr']]
        started=result['name'].endswith('mario_start')
        assert len(active)==int(started),(result['name'],active)
        assert bool(int.from_bytes(bytes.fromhex(result['mem'][0]),'little'))==started
    print('64 timer start/stop pairs released actual firmware slots; ABI balanced',flush=True)
    report=dict(image_sha256=R2_SHA, source_hashes_match=True,
                game_touch_exits=len(entered), outside_game_touch_exits=1,
                timer_start_stop_pairs=64,
                passes=['original three-file card; no probe hooks',
                        'all four games re-entered three times',
                        'touch release clears timer, keys, paint validity and screen',
                        'old-generation deferred ticks do not advance games',
                        'actual timer pool releases every game timer; stack/register ABI balanced'],
                limitations=['injected GUI events, not physical controller',
                             'no hardware stack/DMA/boot timing proof',
                             'not a measurement of complete firmware heap usage'])
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    main()
