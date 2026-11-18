// Isolated E147 native-audio experiment. Changes only in-memory model facts.
// Does not patch firmware or modify the external OM-Emu checkout.
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { createHash } from 'node:crypto';
import { fileURLToPath, pathToFileURL } from 'node:url';
const root = fileURLToPath(new URL('../../', import.meta.url));
const out = path.join(root,'work/shutter-sound');
fs.mkdirSync(out,{recursive:true});
const args=process.argv.slice(2);
const option=(name,defaultValue)=>args.find(arg=>arg.startsWith(name+'='))?.slice(name.length+1)??defaultValue;
const reportFile=option('--report',path.join(out,'native-audio-probe.json'));
globalThis.OM_EMU_MODEL = 'E147';
process.env.OM_EMU_MODEL = 'E147';
const imp = p => import(pathToFileURL(path.join(root,'work/om-emu/emu',p)).href);
const report = {schema:1, status:'started', scope:'host-initiated native playback; no capture hook or camera validation', cycles:[]};
let pl;
try {
  const map = JSON.parse(fs.readFileSync(path.join(out,'audio-map.json')));
  const {MODELS} = await imp('src/fw/models.mjs');
  const main=fs.readFileSync(path.join(root,'work/om-emu/unpacked/E147/OLY_E_147_1100_0000_0000.BIN.blk00000000.OE.0100.bin'));
  if(map.e147_sha256!==MODELS.E147.rom_sha256 || createHash('sha256').update(main).digest('hex')!==map.e147_sha256)
    throw Error('stale audio map or wrong E147 image; rerun map_audio.mjs');
  for(const [name,rec] of Object.entries(map.functions)) {
    const bytes=Buffer.from(rec.expected,'hex'),offset=rec.notation-0x50000000;
    if(offset<0||!main.subarray(offset,offset+bytes.length).equals(bytes))throw Error(`${name}: map bytes mismatch`);
  }
  report.image_sha256=map.e147_sha256;
  const f = Object.fromEntries(Object.entries(map.functions).map(([k,v])=>[k,v.notation]));
  // E147 AUD_MAIN disassembly: starts at +0x6d/+0x9b; CPU2 at +0xf/+0x8b;
  // queue receive at +0xb6. Main id word is checked against its static task entry.
  MODELS.E147.audio = {main:f.main, main_id:0x60042d74,
    starts:[0x60042d72,0x60042cdc], cpu2:[[0x600435c0,'AUD_WAKEUP'],[0x600435ae,'AUD_LEVEL_MONITOR']],
    task_start_cpu:f.task_start_cpu,reply:f.reply,stage:6,exec_queue:0x60043184};
  const {loadImage,loadBlock} = await imp('checks/lib/env.mjs');
  const {expandImage}=await imp('src/fw/expand.mjs');
  const {runtime}=await imp('src/lab/hle.mjs');
  const {Player} = await imp('src/lab/player.mjs');
  const {PLAYER_PARSER} = await imp('scenarios/session_replay.mjs');
  const digest=data=>createHash('sha256').update(data).digest('hex');
  const renderFps=Number(option('--render-fps','0'));
  if(![0,10,20].includes(renderFps))throw Error('renderer test supports 10 or 20 fps');
  const renderControl=args.includes('--render-control');
  const testChooser=args.includes('--choice');
  const choiceDirectory='native';
  const mute=args.includes('--mute');
  if(mute&&!renderFps)throw Error('--mute requires a renderer rate');
  let image=loadImage(), placement, renderer, chooser, card;
  const useRenderer=renderFps||renderControl;
  if(args.includes('--section1')||useRenderer||testChooser) {
    const {CA_TASK_ENTRIES}=await imp('src/lab/camapp.mjs');
    CA_TASK_ENTRIES.push(0x50a6e603);
    if(Number(args.includes('--section1'))+Number(Boolean(useRenderer))+Number(testChooser)>1)
      throw Error('use separate loader, renderer and chooser runs');
    if(testChooser) {
      chooser=JSON.parse(fs.readFileSync(path.join(out,choiceDirectory,'build.json')));
      MODELS.E147.ui_out={init:f.ui_init,task:f.ui_task};
      const {cardFromImage}=await imp('src/lab/sdcard.mjs');
      card=cardFromImage(fs.readFileSync(path.join(root,'work/native-build/paired.omsd')));
    } else if(useRenderer)renderer=JSON.parse(fs.readFileSync(path.join(out,'copy-retrigger/build.json')));
    else placement=JSON.parse(fs.readFileSync(path.join(out,'memory-probe/memory.json')));
    const raw=fs.readFileSync(path.join(out,testChooser?`${choiceDirectory}/row-main.bin`:
      useRenderer?'copy-retrigger/row-main.bin':'memory-probe/main.bin'));
    const expected=chooser?.candidate_sha256??renderer?.candidate_sha256??placement.sha256;
    if(digest(raw)!==expected)throw Error('experimental image does not match its report');
    image=expandImage(raw);
    report.image_sha256=expected;
    report.layout_sha256=map.e147_sha256;
  }
  const events=[];
  pl=new Player({...PLAYER_PARSER,no_browser:true,idle:'off',a15:'on',out:'<out>',no_wait_on_error:true,audio:'on',
    ...(testChooser?{tab:'7,2,1'}:{})},
    {rom:image,resBlock:loadBlock(),createHash,wallClock:()=>performance.now()/1000,onAudio:e=>events.push(...e),
      ...(card?{card:{open:()=>card,save:x=>{card=x;}},
        deflate:(b,l)=>zlib.deflateSync(b,{level:l}),inflate:b=>zlib.inflateSync(b)}:{})});
  pl.open_session();
  if (pl.phase !== 'running' || !pl.session?.audio_hw) throw Error(`audio bring-up failed: ${pl.error?.stack ?? pl.phase}`);
  const s=pl.session,lab=s.lab,sim=lab.sim,hw=s.audio_hw;
  // E147's codec uses channel 13 (50a62f69/50a63256), while the upstream
  // E143 CodecLink intercepts channel 14. Reuse its chip/transport model only
  // for the E147 channel in this experiment; other channels keep their hooks.
  const link=hw.codec;
  const e147Sio=await imp('src/lab/scpulink.mjs');
  for(const [name,method,byDescriptor] of [['SIO_OPEN','_open',false],['SIO_CONFIG','_config',true],['SIO_TRANSFER','_transfer',true],['SIO_CLOSE','_close',false]]) {
    lab.wrap(e147Sio[name],prev=>(h,r)=>{
      const channel=byDescriptor?sim.read(r.a0,1)[0]:(r.d0&255);
      return channel===13?link[method](h,r):prev(h,r);
    },'S-E147CODEC-'+name);
  }
  report.codec_channel=13;
  report.bringup=hw.status();

  function replaySection1(start,end) {
    const base=0x60021020, dest=sim.u32(0x60029b28), flash=sim.u32(0x60029b2c);
    const overlay=image.subarray(start-base,end-base);
    const load=0x500022b1, inherited=lab.hooks.get(runtime(load));
    const blank=new Uint8Array(16384).fill(0xa5);
    // OM-Emu maps the entire image. Recreate the native loader's copy with
    // emulated NAND and preserve already-initialized stock section-1 data.
    for(let offset=0;offset<overlay.length;offset+=blank.length)
      sim.write(start+offset,blank.subarray(0,overlay.length-offset));
    const read=(h,r,previous)=>{
      if(r.a1!==flash)return previous(h,r);
      if(r.d0!==end-dest||r.d1!==0x10200||((r.a0^dest)&0x1fffffff)!==0)
        throw Error(`unexpected section-1 NAND arguments ${r.a0.toString(16)} ${r.d0.toString(16)} ${r.d1.toString(16)}`);
      if(report.loader)throw Error('duplicate section-1 read');
      report.loader={dest:r.a0,flash,bytes:r.d0,extended_bytes:end-start,
        model:'native section loader with emulated NAND'};
      for(let offset=0;offset<overlay.length;offset+=blank.length)
        sim.write(r.a0+(start-dest)+offset,overlay.subarray(offset,offset+blank.length));
      h.finish(r,{d0:0});
    };
    if(inherited)lab.wrap(load,previous=>(h,r)=>read(h,r,previous),'S-SECTION1-PROBE');
    else lab.hook(load,(h,r)=>read(h,r,(_h,native)=>lab.passthrough(native)),'S-SECTION1-PROBE');
    try {
      lab.call(0x50024eb5,{d0:1},null,null,200000);
    } finally {
      if(inherited)lab.hooks.set(runtime(load),inherited);
      else lab.hooks.delete(runtime(load));
    }
    if(!report.loader)throw Error('native section loader did not read the overlay');
    for(let offset=0;offset<overlay.length;offset+=blank.length) {
      const chunk=overlay.subarray(offset,offset+blank.length);
      if(!Buffer.from(sim.read(start+offset,chunk.length)).equals(chunk))
        throw Error('native loader did not copy the extended pages');
    }
  }

  if(chooser) {
    const {testChoice}=await import('./choice_flow.mjs');
    report.scope=chooser.scope;
    report.chooser_trace=[];
    report.copy_trace = [];
    for (const [name, at] of Object.entries({period:f.period, play:f.seq_play,
        start:f.seq_start, stop:0x60ae23ba-0x10021020})) {
      lab.observe(at, (_l,r) => {
        if (report.copy_trace.length < 24) report.copy_trace.push({name,d0:r.d0,d1:r.d1,
          a0:r.a0, param:Buffer.from(sim.read(r.a0,name==='play'?96:16)).toString('hex'),
          player:Buffer.from(sim.read(0x62b43db8+128,12)).toString('hex')});
      }, 'es-copy-'+name);
    }
    for(const [name,at] of Object.entries({
      save:chooser.symbols.es_menu_keys, capture_main:chooser.symbols.es_capture_main,
      capture_fast:chooser.symbols.es_capture_fast, copy_done:chooser.symbols.es_copy_done,
      dispatch:chooser.symbols.es_dispatch,
      resource:chooser.symbols.es_wave,flag:0x6004cd21,request:0x6017b9de,
      reply:0x6017be6c,flag_return:0x6004cd92,wake:0x6017b7a7,
      branch:0x6017b7b4,wait:0x6017b7a0,native_set:0x60035ee7,
    })) {
      const notation=at-0x10021020;
      const record=r=>{
        const flag=sim.read(0x60042fca,1)[0];
        if(['flag','native_set'].includes(name)&&r.d0!==flag)return;
        if(name==='flag_return'&&(r.d3!==flag))return;
        if(report.chooser_trace.length<100)report.chooser_trace.push({
          name,d0:r.d0,d1:r.d1,d2:r.d2,a0:r.a0,a3:r.a3,caller:r.mdr,
          busy:sim.read(0xa32da3a8,1)[0],play_count:sim.read(0x62b43dac,1)[0],
          ui_state:lab.nk.state(s.ui_out_tid),word:sim.u32(r.sp+36)});
      };
      if(lab.hooks.has(runtime(notation)))lab.wrap(notation,prev=>(h,r)=>{record(r);return prev(h,r);},'choice-'+name);
      else lab.observe(notation,(_l,r)=>record(r),'choice-'+name);
    }
    const {write_png}=await imp('checks/lib/png.mjs');
    const {words_to_rgb}=await imp('src/lab/display.mjs');
    const saveFrame=name=>{
      const [width,height,pixels]=s.frame('now',false);
      write_png(path.join(out,choiceDirectory,`${name}.png`),width,height,words_to_rgb(pixels));
    };
    replaySection1(chooser.wave_start,chooser.wave_end);
    const prepared=name=>fs.readFileSync(path.join(out,'presets',name));
    const optional=(name,fallback)=>fs.existsSync(path.join(out,'presets',name))?prepared(name):prepared(fallback);
    const custom=prepared('canon5d-single.wav');
    const exactLimit=Buffer.alloc(chooser.sd_max_bytes);
    custom.copy(exactLimit);
    exactLimit.writeUInt32LE(exactLimit.length-8,4);
    exactLimit.writeUInt32LE(exactLimit.length-112,108);
    const sdFiles={
      Ciallo:optional('ciallo-full.wav','canon5d-single.wav'),
      Man:optional('man-full.wav','nikond850-single.wav'),
      Custom:exactLimit,
    };
    report.checks=testChoice(pl,chooser,events,saveFrame,sdFiles);
  } else {
    const traceEnabled=!process.argv.includes('--no-trace');
    report.trace_enabled=traceEnabled;
    const watch=(at,fn,name)=>{
      if(!traceEnabled)return;
      if(lab.hooks.has(runtime(at))) {
        lab.wrap(at,prev=>(h,r)=>{fn(r);return prev(h,r);},name);
      } else {
        lab.observe(at,(_l,r)=>fn(r),name);
      }
    };
    report.trace=[];
    for(const name of ['seq_play','seq_start','short_key','period','isr'])watch(f[name],r=>{
      if(report.trace.length<40)report.trace.push({name,pc:r.pc,d0:r.d0,d1:r.d1,a0:r.a0,a1:r.a1});
    },'probe-'+name);
    report.sends=[];
    report.codec_calls=[];
    const sio = await imp('src/lab/scpulink.mjs');
    for(const name of ['SIO_OPEN','SIO_CONFIG','SIO_TRANSFER','SIO_CLOSE'])
      watch(sio[name],r=>{if(lab.lt.current()===lab.nk.tcb(hw.main_tid)&&report.codec_calls.length<30)
        report.codec_calls.push({name,caller:r.mdr,d0:r.d0,a0:r.a0,a1:r.a1,bytes:r.a0?Buffer.from(sim.read(r.a0,28)).toString('hex'):null});},'probe-codec-'+name);
    report.waits=[];
    const { SVC } = await imp('src/lab/kernel.mjs');
    for(const name of ['twai_sem','wai_flg','twai_flg','loc_mtx','trcv_dtq'])
      watch(SVC[name],r=>{
        if(report.last_command==='0x41'&&lab.lt.current()===lab.nk.tcb(hw.main_tid)&&report.waits.length<60)report.waits.push({name,task:lab.lt.current(),caller:r.mdr,d0:r.d0,d1:r.d1,a0:r.a0,a1:r.a1});
      },'probe-wait-'+name);
    report.power_trace=[];
    for(const at of [0x50060c39,0x5005e863,0x50054f53,0x5003bea3,0x5003bfee,0x500603c1,0x5005e97e,0x50a641e1])
      watch(at,r=>{if(lab.lt.current()===lab.nk.tcb(hw.main_tid)&&report.power_trace.length<40)report.power_trace.push({at,caller:r.mdr,d0:r.d0,d1:r.d1,a0:r.a0});},'probe-power-'+at);
    watch(f.sync_send,r=>{if(report.sends.length<20)report.sends.push({queue:r.d0&65535,cmd:r.d1,caller:r.mdr});},'probe-send');
    for(const at of [0x50abe89f,0x50ac0496,0x50ac04c3,0x50ac04d0,0x50ac04d6,0x50ac04dc,0x50ac04e3,0x50ac050c,0x50ac0525,0x50ac05a1])
      watch(at,r=>{if(report.trace.length<40)report.trace.push({at,d0:r.d0,d1:r.d1});},'probe-stage-'+at);
    if(args.includes('--trace-capture')) {
      if(!traceEnabled)throw Error('capture trace requires tracing');
      const layout=JSON.parse(fs.readFileSync(path.join(root,'shutter_sound/layout.json')));
      const hits=[];
      let stage='startup';
      for(const name of ['capture','capture_fast']){
        const {notation,expected}=layout.functions[name],at=Number(notation);
        const bytes=Buffer.from(expected,'hex'),offset=at-0x50000000;
        if(!Buffer.from(image.subarray(offset,offset+bytes.length)).equals(bytes))throw Error(`${name}: capture bytes mismatch`);
        watch(at,r=>hits.push({name,stage,pc:r.pc,caller:r.mdr}),'probe-'+name);
      }
      const beforeRelease=s.camapp.release;
      stage='half-press';
      s.key('s1','down');s.camapp.pump();s.idle_slice(lab.lab_time()+300e6);
      stage='full-press';
      s.key('s2','down');s.camapp.pump();s.idle_slice(lab.lab_time()+700e6);
      s.key('s2','up');s.camapp.pump();
      s.key('s1','up');s.camapp.pump();
      s.idle_slice(lab.lab_time()+300e6);
      report.capture={hits:hits.slice(),lab_releases:s.camapp.release-beforeRelease,
        stand_in:pl.stand_ins_in_use().includes('S-RELSEQ')};
      if(report.capture.lab_releases!==1)throw Error('capture trace did not produce one simulated release');

      // Exercise the mapped normal site independently with an empty CapBuf
      // list. The method links buffers. The simulated S2 above establishes
      // whether the camera application's release reaches it on its own.
      stage='isolated-buffer-append';
      const owner=lab.alloc(new Uint8Array(0x120),16);
      const first=lab.alloc(new Uint8Array(64),16);
      const second=lab.alloc(new Uint8Array(64),16);
      const append=Number(layout.functions.capture.notation);
      for(const record of [first,second])
        lab.call(append,{a0:owner,a1:record,d0:0},null,[0xf0,28],1000);
      if(sim.u32(owner+276)!==first||sim.u32(owner+260)!==second||
         sim.u32(first+40)!==second||sim.u32(second+24)!==first||sim.u32(second+40)!==0)
        throw Error('capture candidate did not link the fixture buffers');
      report.capture.fixture={linked:2,hits:hits.slice(report.capture.hits.length)};
    }
    let wav;
    if(placement) {
      const {trial_start:start,trial_end:end,main_runtime_base:base,wav_bytes:n}=placement;
      const section=placement.sections_before_probe[0];
      wav=Buffer.from(image.subarray(start-base,start-base+n));
      if(digest(wav)!==placement.wav_sha256||start!==section.end)throw Error('section-1 WAV placement mismatch');
      replaySection1(start,end);
      report.input='5D WAV from section-1 probe';
    } else if(args.includes('--control')) {
      const {labSoundArea}=await imp('src/lab/soundres.mjs');
      wav=Buffer.from(labSoundArea().sounds[0].wav);
      report.input='OM-Emu AF-key control';
    } else {
      report.input=option('--bank',path.join(out,'SHUTTER.BIN'));
      const raw=fs.readFileSync(report.input);
      if(raw.subarray(0,8).toString('hex')!=='4f4d33534e440000' || raw.readUInt32LE(8)!==1 || raw.readUInt32LE(12)!==raw.length-48 ||
         !createHash('sha256').update(raw.subarray(48)).digest().equals(raw.subarray(16,48))) throw Error('invalid generated bank');
      wav=raw.subarray(48);
    }
    let dataOffset=-1,size=0;
    for(let o=12;o+8<=wav.length;) {
      const n=wav.readUInt32LE(o+4);
      if(o+8+n>wav.length)throw Error('WAV chunk exceeds file');
      if(wav.toString('ascii',o,o+4)==='data'){dataOffset=o+8;size=n;}
      o+=8+n+(n&1);
    }
    if(dataOffset<0 || dataOffset%16 || !size || size%4 || size>48000*4*5)throw Error('invalid generated PCM');
    if(args.includes('--copy')||renderer) {
      // The driver uses the copy task for the stock SHUT1 key. Keep the
      // chunk lengths and sample alignment identical to the direct-mode run.
      const key=wav.indexOf('PRM_AUD_CSHUT1_VOL');
      if(placement||key<0||key>=dataOffset)throw Error('copy experiment requires a CSHUT1 bank file');
      wav=Buffer.from(wav);
      wav.write('PRM_AUD_SHUT1_VOL\0',key,'ascii');
      report.copy_experiment=true;
    }
    let clip;
    if(renderFps) {
      if(!traceEnabled||args.includes('--cut'))throw Error('renderer requires tracing and the normal completion path');
      if(size<19200)throw Error('use a clip longer than the tested shot interval');
      clip=wav.subarray(dataOffset,dataOffset+size);
      size=Math.ceil((size+192000*(6/renderFps+0.10))/768)*768;
      if(size>48000*4*5)throw Error('test stream exceeds the PCM bound');
      // The source-address guard identifies this transport. The stock
      // converter would emit zero throughout if our renderer never ran.
      wav=Buffer.concat([wav.subarray(0,dataOffset),Buffer.alloc(size)]);
      wav.writeUInt32LE(wav.length-8,4);
      wav.writeUInt32LE(size,dataOffset-4);
    }
    // The boot section loader returns the uncached alias for the NAND
    // transfer. The audio DMA port uses that same alias for WAV data.
    const wavAt=placement ? report.loader.dest+placement.trial_start-placement.sections_before_probe[0].dest : lab.alloc(wav,128);
    const descAt=lab.alloc(new Uint8Array(160),16), recAt=lab.alloc(new Uint8Array(8),16);
    const desc=new Uint8Array(96),dd=new DataView(desc.buffer);
    dd.setUint32(0,1,true);dd.setUint32(4,wavAt,true);dd.setUint32(8,wav.length,true);
    sim.write(descAt,desc);
    const timed=fn=>{
      const previous=lab.lt.on_idle, previousLimit=lab.lt.idle_again_limit;
      const deadline=lab.lab_time()+2e9;
      lab.lt.idle_again_limit=100000;
      let moves=0;
      lab.lt.on_idle=()=>{
        if(++moves>400||lab.lab_time()>=deadline)throw Error(`probe timeout waiting for ${report.last_command??'open'}`);
        lab.run_to_event(deadline);
        lab.kernel.deliver();
        return 'again';
      };
      try{return fn();}finally{lab.lt.on_idle=previous;lab.lt.idle_again_limit=previousLimit;}
    };
    const queue=hw.exec_queue();
    const commandAt=lab.alloc(new Uint8Array(64),16);
    const vols=lab.alloc(new Uint8Array(new Int32Array([100,100,100,0]).buffer),16);
    let player;
    const send=(cmd)=>{
      report.last_command='0x'+cmd.toString(16);
      const bytes=new Uint8Array(64),dv=new DataView(bytes.buffer);bytes[0]=cmd;
      dv.setUint32(4,player,true);dv.setUint32(12,descAt,true);
      dv.setUint32(40,descAt+96,true); // opaque post field, no callbacks registered in this host fixture
      if(cmd===0x22)dv.setUint32(48,vols,true);
      sim.write(commandAt,bytes);
      const rc=timed(()=>lab.call(f.sync_send,{d0:queue,a0:commandAt,d1:1},null,null,2000000)).d0|0;
      report.commands??=[];report.commands.push({cmd,rc});
      if(rc!==0)throw Error(`command ${report.last_command} returned ${rc}`);
      return rc;
    };
    const cycles=Number(args.find(arg=>!arg.startsWith('--'))??3);
    if(!Number.isInteger(cycles)||cycles<1||cycles>100)throw Error('cycles must be 1..100');
    const periods=[],requests=[];
    let renderSymbols;
    const put=(address,value)=>{
      const bytes=Buffer.alloc(4);
      bytes.writeUInt32LE(value);
      sim.write(address,bytes);
    };
    if(renderFps) {
      renderSymbols=renderer.symbols;
      const src=wavAt+dataOffset, clipAt=lab.alloc(clip,16);
      put(renderSymbols.stream_begin,src);
      put(renderSymbols.stream_end,src+size);
      put(renderSymbols.clip_begin,clipAt);
      put(renderSymbols.clip_end,clipAt+clip.length);
      report.retrigger={fps:renderFps,clip_frames:clip.length/4,stream_frames:size/4,mute,renders:[]};
      watch(renderSymbols.render_shutter_pcm-0x10021020,r=>{
        if(r.a1>=src&&r.a1+r.d0<=src+size&&r.d0===768)
          periods.push(sim.u32(renderSymbols.shutter_requested));
      },'probe-copy-render');
    }
    for(let i=0;i<cycles;i++){
      const before=events.length;
      const cycleFirstGen=1+i*10;
      if(renderFps) {
        periods.length=0;
        requests.length=0;
        put(renderSymbols.shutter_requested,cycleFirstGen);
      }
      s.begin('99-shutter-audio-probe');
      player=timed(()=>lab.call(f.open,{a0:recAt,d0:300},null,null,200000)).d0>>>0;
      if(player>2)throw Error(`open returned ${player}`);
      const rc=[send(0x22),send(0x41),send(0x45)];
      s.settle('shutter-audio-start');s.end('shutter-audio-start','debug',[],[]);
      if(renderFps) {
        const t0=lab.lab_time();
        for(let shot=1;shot<=6;shot++){
          s.idle_slice(t0+shot*1e9/renderFps);
          pl.publish_audio();
          const gen=cycleFirstGen+shot+(shot===6?1:0);
          // Two requests before one period must produce only the latest.
          if(shot===6)put(renderSymbols.shutter_requested,gen-1);
          put(renderSymbols.shutter_requested,gen);
          requests.push({gen,at_ns:lab.lab_time()});
        }
        if(mute){
          s.idle_slice(t0+7e9/renderFps);
          put(renderSymbols.shutter_requested,0);
          requests.push({gen:0,at_ns:lab.lab_time()});
        }
      }
      for(let k=0;k<Math.ceil((size/192000+0.14)/0.06);k++){s.idle_slice(lab.lab_time()+60e6);pl.publish_audio();}
      const native=events.slice(before).filter(e=>e.source==='native');
      const pcm=Buffer.concat(native.map(e=>Buffer.from(e.samples.buffer,e.samples.byteOffset,e.samples.byteLength)));
      let expected=wav.subarray(dataOffset,dataOffset+size);
      if(renderFps) {
        if(periods.length<size/768)throw Error(`renderer handled only ${periods.length} periods`);
        expected=Buffer.alloc(size);
        const onsets=new Map();
        let generation=-1,offset=0;
        for(const [block,gen] of periods.slice(0,size/768).entries()){
          if(gen!==generation){
            if(onsets.has(gen))throw Error(`renderer returned to stale generation ${gen}`);
            onsets.set(gen,block);
            generation=gen;
            offset=0;
          }
          if(gen)clip.copy(expected,block*768,Math.min(offset,clip.length),Math.min(offset+768,clip.length));
          offset+=768;
        }
        const firstTime=native[0]?.t_lab_ns;
        if(!Number.isFinite(firstTime)||onsets.size!==requests.length+1||onsets.get(cycleFirstGen)!==0)
          throw Error(`expected one attack per request, got ${JSON.stringify([...onsets])}`);
        const delays=requests.map(({gen,at_ns})=>{
          const block=onsets.get(gen);
          const ms=(firstTime+block*4e6-at_ns)/1e6;
          if(!Number.isFinite(ms)||ms<0||ms>=1000/renderFps)throw Error(`generation ${gen} onset delay ${ms} ms`);
          return {gen,block,delay_ms:ms};
        });
        if(delays[0].block*768>=clip.length)throw Error('old clip ran to completion before restart');
        if(!mute&&size-delays.at(-1).block*768<clip.length)throw Error('final clip lacks its full tail');
        report.retrigger.renders.push({cycle:i,delays,coalesced:1});
      }
      const padded=report.copy_experiment ? Buffer.concat([expected,Buffer.alloc((768-size%768)%768)]) : expected;
      if(!pcm.equals(padded))throw Error(`PCM mismatch at cycle ${i}: ${pcm.length}/${padded.length}`);
      s.begin('99-shutter-audio-release');
      rc.push(send(0x49),timed(()=>lab.call(f.close,{a0:recAt},null,null,200000)).d0|0);
      s.settle('shutter-audio-release');s.end('shutter-audio-release','debug',[],[]);
      if(rc.some(x=>x!==0))throw Error(`command failures: ${rc}`);
      const port=hw.status().port;
      if(port.running||port.playing||port.underruns||port.overruns)throw Error(`port not clean: ${JSON.stringify(port)}`);
      report.cycles.push({index:i,frames:pcm.length/4,sha256:createHash('sha256').update(pcm).digest('hex'),rc,port});
    }
    if(args.includes('--cut')) {
      s.begin('99-shutter-audio-retrigger');
      player=timed(()=>lab.call(f.open,{a0:recAt,d0:300},null,null,200000)).d0>>>0;
      if(player>2)throw Error(`retrigger open returned ${player}`);
      send(0x22);
      send(0x41);
      send(0x45);
      s.settle('retrigger-start');s.end('retrigger-start','debug',[],[]);
      const before=events.length;
      s.idle_slice(lab.lab_time()+25e6);
      s.begin('99-shutter-audio-interrupt');
      const stopAt=lab.lab_time();
      if(!hw.status().port.playing)throw Error('first clip finished before interrupt');
      send(0x46);
      send(0x49);
      const closeRc=timed(()=>lab.call(f.close,{a0:recAt},null,null,200000)).d0|0;
      if(closeRc!==0)throw Error(`interrupted close returned ${closeRc}`);
      report.interrupt={stop_ms:(lab.lab_time()-stopAt)/1e6,port:hw.status().port};
      s.settle('retrigger-stop');s.end('retrigger-stop','debug',[],[]);
      pl.publish_audio();
      const interruptedFrames=events.slice(before).filter(e=>e.source==='native').reduce((n,e)=>n+e.samples.length/2,0);
      report.interrupt.frames=interruptedFrames;
      if(interruptedFrames>=size/4)throw Error(`stop waited for a full clip (${interruptedFrames} frames)`);
      if(report.interrupt.port.running||report.interrupt.port.playing)throw Error('interrupted audio port still active');
    }
  }
  report.status='passed';
  report.stand_ins=pl.stand_ins_in_use();
} catch(e) {report.status='failed';report.error=e.stack??String(e);process.exitCode=1;
  try{const l=pl.session.lab;report.tasks=[...l.task_states()];report.audio=pl.session.audio_hw?.status();report.kernel=l.kernel.events.slice(-12);
    report.task_stacks=[83,160].map(id=>{const tcb=l.nk.tcb(id),sp=l.sim.u32(tcb+24);return{id,tcb,sp,words:Array.from({length:100},(_,i)=>l.sim.u32(sp+i*4))};});
  }catch{}
}
finally {
  try{pl?.close_session();}catch(e){report.close_error=String(e);process.exitCode=1;report.status='failed';}
  fs.writeFileSync(reportFile,JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report.status==='failed'?report:{status:report.status,cycles:report.cycles.length},null,2));
}
