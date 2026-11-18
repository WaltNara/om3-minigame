// Replay through the camera application, ListMenu and GUI task on E147.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import {fileURLToPath, pathToFileURL} from 'node:url';

globalThis.OM_EMU_MODEL = process.env.OM_EMU_MODEL = 'E147';
const root = fileURLToPath(new URL('../', import.meta.url));
const imp = p => import(pathToFileURL(path.join(root, 'work/om-emu/emu', p)).href);
const {Player} = await imp('src/lab/player.mjs');
const {PLAYER_PARSER} = await imp('scenarios/session_replay.mjs');
const {cardFromImage} = await imp('src/lab/sdcard.mjs');
const {loadBlock} = await imp('checks/lib/env.mjs');
const {expandImage} = await imp('src/fw/expand.mjs');
const {write_png} = await imp('checks/lib/png.mjs');
const {words_to_rgb} = await imp('src/lab/display.mjs');
const {A} = await imp('src/fw/model.mjs');
const {runtime} = await imp('src/lab/hle.mjs');
const {CA_TASK_ENTRIES} = await imp('src/lab/camapp.mjs');
const M = await imp('src/lab/menudata.mjs');
const out = path.resolve(root, process.env.OM3_MENU_BUILD ?? 'work/menu-extension/games');
const manifest = JSON.parse(fs.readFileSync(path.join(out, 'build.json')));
const pictureMode = manifest.host === 'picture-mode';
const sy = manifest.symbols, raw = fs.readFileSync(path.join(out, 'row-main.bin'));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
assert.equal(sha(raw), manifest.candidate_sha256);
const base=fs.readFileSync(path.join(root,pictureMode?'work/current-games/row-main.bin':'work/native-build/base-main.bin'));
assert.equal(sha(base),manifest.base_sha256);
const tables=new M.Image(base), candidate=new M.Image(raw), mode=manifest.mode;
assert.deepEqual(M.tabs(candidate),M.tabs(tables));
for (const [id,page] of M.groups(tables)) {
  const next=M.groups(candidate).get(id);
  assert.ok(![...(page.labels??[]),...(page.helps??[])].some(row=>row.key===mode));
  assert.ok(!page.values?.has(mode));
  if(id!==236) assert.deepEqual(next,page);
  else {
    assert.deepEqual(next.labels.slice(0,-1),page.labels);
    assert.deepEqual(next.helps.slice(0,-1),page.helps);
    assert.deepEqual(next.values,page.values);
    assert.deepEqual(next.labels.at(-1),{key:mode,type:5,id:0,literal:pictureMode?'ES sound':'Extras'});
  }
}
assert.ok(!M.custom_value_handlers(tables).has(mode) && !M.mode_alias(tables).has(mode));
for(const [kind,sub] of M.row_order(tables)) for(const [k,rows] of sub) {
  assert.ok(!rows.includes(mode));
  assert.deepEqual(M.row_order(candidate).get(kind).get(k),kind===240&&k===0?[...rows,mode]:rows);
}
// Picture Mode layout and callbacks match the image this build starts from.
for(const [addr,len] of [[0x60f49a63,17+52],[0x60f49e08,25*40],
    [0x611d040f,24],[0x611d0848,20],[0x611d04ec,6],[0x6125becc,6]])
  assert.ok(raw.subarray(addr-0x60021020,addr-0x60021020+len).equals(base.subarray(addr-0x60021020,addr-0x60021020+len)));
CA_TASK_ENTRIES.push(0x50a6e603);
let card = cardFromImage(fs.readFileSync(path.join(root, 'work/native-build/paired.omsd')));
const player = new Player({...PLAYER_PARSER, tab:'7,2,1', no_browser:true, idle:'off',
  a15:'on', audio:'off', touch:'gui', no_wait_on_error:true}, {
  rom:expandImage(raw), resBlock:loadBlock(), createHash, card:{open:()=>card,save:x=>{card=x;}},
  wallClock:()=>performance.now()/1000, deflate:(b,l)=>zlib.deflateSync(b,{level:l}), inflate:b=>zlib.inflateSync(b),
});
const report = {sha256:sha(raw), snapshots:[], through:[], touch:{replies:0,waits:0,returns:0,flaps:0}};
try {
  player.open_session();
  assert.equal(player.phase, 'running', player.error?.stack);
  const s = player.session, {lab} = s, sim = lab.sim;
  const byte = a => sim.read(a,1)[0];
  const u16 = a => Buffer.from(sim.read(a,2)).readUInt16LE();
  const state = () => byte(sy.games_state), ticks = () => sim.u32(sy.mario_ticks);
  const timer = () => u16(sy.mario_handle);
  const panel = () => u16(0x6037e8cc);
  let stage = 'startup';
  const observe = (at, fn) => {
    if (lab.hooks.has(runtime(at))) lab.wrap(at, prev=>(h,r)=>{fn(r); return prev(h,r);}, 'menu-test');
    else lab.observe(at, (_lab,r)=>fn(r), 'menu-test');
  };
  for (const at of [A(0x50af7cb9), A(0x50af7cbe)]) observe(at,r=>{
    if (r.a1 && u16(r.a1+4)===991) report.through.push({stage,ctrl:sim.u32(r.a1+32)});
  });
  const touch = report.touch;
  let touchFrame=null;
  observe((sy.menu_touch ?? sy.flappy_touch_repaired)-0x10021020,r=>{
    assert.equal(touchFrame,null);
    const record=sim.u32(r.a3+12);
    touchFrame={regs:Object.fromEntries(['d0','d1','d3','a0','a1','a2','a3','sp'].map(k=>[k,r[k]])),
      event:Buffer.from(sim.read(r.a3,28)), record, bytes:record?Buffer.from(sim.read(record,12)):null};
  });
  observe(0x61294d13-0x10021020,()=>{touchFrame=null;}); // forwarded to stock
  observe(0x61294e57-0x10021020,r=>{
    if(!touchFrame) return;
    for(const [k,v] of Object.entries(touchFrame.regs)) assert.equal(r[k],v,k);
    assert.equal(r.d2,0);
    assert.deepEqual(Buffer.from(sim.read(r.a3,28)),touchFrame.event);
    if(touchFrame.record) assert.deepEqual(Buffer.from(sim.read(touchFrame.record,12)),touchFrame.bytes);
    touchFrame=null;
  });
  observe(0x610c0e7e-0x10021020,r=>{if(sim.u32(r.a1)===35) touch.replies++;});
  observe(0x610c829e-0x10021020,()=>touch.waits++);
  observe(0x610c82a0-0x10021020,()=>touch.returns++);
  observe(sy.flappy_step-0x10021020,()=>{if(byte(sy.flappy_pending)) touch.flaps++;});
  const snap = label => {
    const row = {label, gui:lab.state(), panel:panel(), game:state(), throughOff:s.through_off,
      timer:timer(), ticks:ticks(), armed:byte(sy.games_row_selected), paint:byte(sy.games_paint_valid),
      contact:byte(sy.flappy_contact), drain:byte(sy.flappy_drain), images:s.camapp.images.length,
      recording:s.camapp.recording};
    report.snapshots.push(row);
    console.log(JSON.stringify(row));
    return row;
  };
  const idle = ms => s.idle_slice(lab.lab_time()+ms*1e6);
  const key = (id,label=id) => {
    stage=label; s.key(id,'down'); s.camapp.pump(); idle(80);
    s.key(id,'up'); s.camapp.pump(); idle(200); return snap(label);
  };
  const picture = name => {
    const [w,h,pixels] = s.frame('now', false);
    const rgb=words_to_rgb(pixels);
    write_png(path.join(out,name+'.png'),w,h,rgb);
    if (name==='extras' || name==='sound') {
      const rows=name==='extras' ? [80,205,285] : [64,140,198,256,314,372,480];
      for (const y of rows) {
        let ink=0;
        for(let j=y;j<y+16;j++) for(let x=278;x<720;x++)
          if(rgb[(j*w+x)*3]>160) ink++;
        assert.ok(ink>20,`Missing text on ${name} at y=${y}`);
      }
    }
    return sha(rgb);
  };
  const checkPreview = (stage, expected) => {
    const site = manifest.game_preview_gate;
    if (!site) return;
    const permit = 0xa32da638, previous = sim.u32(permit);
    const resume = site + 5 - 0x10021020;
    lab.hook(resume, (h, r) => h.return_here(r, [0,4]), 'through preview gate fixture');
    try {
      sim.word(permit, previous | 3);
      for (const mask of [1, 2]) {
        const answer = lab.call(site - 0x10021020, {d0:mask}, null, [0,4], 20000).d0;
        assert.equal(answer, expected, `${stage}: display permit ${mask}`);
      }
      assert.equal(sim.u32(permit), previous | 3);
      (report.previewGate ??= []).push({stage, permit:expected});
    } finally {
      lab.hooks.delete(runtime(resume));
      sim.word(permit, previous);
    }
  };
  // Reuse the paired-card readiness of the accepted r5 camera replay.
  idle(1500);
  sim.write(0xa32de590, Uint8Array.of(255,3,0,0));
  sim.write(0x60369308, Uint8Array.of(0,240,0,0));
  const openPictureGames = () => {
    key('ok'); key('ok');
    for(let i=0;i<13;i++) key('down');
    assert.equal(byte(sy.games_row_selected),1);
    key('ok','launcher'); assert.equal(state(),1); picture('launcher');
  };
  key('s1');
  if (pictureMode) {
    checkPreview('shooting', 1);
    openPictureGames();
    checkPreview('launcher', 0);
  } else {
  key('menu','setup'); assert.equal(panel(),329);
  assert.equal(s.through_off,true);
  for(let i=0;i<3;i++) key('down');
  picture('setup');
  key('info','row-help'); assert.equal(byte(sy.games_row_selected),0);
  key('info','row-help-close'); assert.equal(byte(sy.games_row_selected),1);
  key('ok','extras'); assert.equal(state(),7); picture('extras');
  const dial=(id,n)=>{s.dial_input(id,n);s.camapp.pump();idle(200);};
  dial('main',1); assert.equal(byte(sy.extras_selection),1,'rear dial in Extras');
  dial('main',-1); assert.equal(byte(sy.extras_selection),0);
  key('down'); key('ok','sound'); assert.equal(state(),8);
  assert.equal(byte(sy.sound_choice),0); assert.equal(byte(sy.sound_cursor),0);
  key('down'); key('down'); picture('sound');
  key('ok','choose-d850'); assert.equal(byte(sy.sound_choice),2); assert.equal(state(),7);
  key('ok','reopen-sound'); assert.equal(byte(sy.sound_cursor),2);
  key('down'); key('menu','cancel-sound'); assert.equal(byte(sy.sound_choice),2);
  key('menu','back-to-setup'); assert.equal(state(),0); assert.equal(panel(),329);
  key('ok','extras-again'); assert.equal(state(),7);
  key('ok','launcher'); assert.equal(state(),1); picture('launcher');
  key('menu','back-to-extras'); assert.equal(state(),7);
  key('ok','reopen-launcher'); assert.equal(state(),1);
  }
  key('ok','2048'); assert.equal(state(),2); const before=Buffer.from(sim.read(sy.board,16));
  for(const k of ['left','down','right']) key(k);
  assert.notDeepEqual(Buffer.from(sim.read(sy.board,16)),before); picture('2048');
  key('menu'); assert.equal(state(),1);
  for(const [selection,name] of [[1,'mines'],[2,'mario'],[3,'breakout'],[4,'flappy']]) {
    key('down'); key('ok',name); assert.equal(state(),selection+2);
    if(selection===1) {
      const cursor=byte(sy.mines_cursor); key('right'); assert.notEqual(byte(sy.mines_cursor),cursor);
    } else {
      if(name==='breakout') {key('ok','serve'); assert.equal(sim.u32(sy.breakout_state+20),1);}
      const ballY=sim.u32(sy.breakout_state+8);
      assert.notEqual(timer(),0); const start=ticks(); idle(1500); snap(name+'-idle');
      assert.ok(ticks()>start); assert.equal(s.through_off,!pictureMode);
      if(name==='breakout') assert.notEqual(sim.u32(sy.breakout_state+8),ballY);
    }
    if(selection===4) break;
    key('menu'); assert.equal(state(),1); assert.equal(timer(),0);
  }
  picture('flappy');
  checkPreview('playing', 0);
  stage='touch';
  const sample=(act,x=450,y=300)=>{
    s.touch(act,x,y); s.camapp.pump(); idle(65);
    while(s.pending_touch()) s.touch_gui_step();
  };
  const previous=touch.flaps;
  report.panelTouchModel=s.touch_on;
  if(s.touch_on) {
    sample('down'); sample('up'); idle(200); snap('touch-tap');
    report.panelTapFlaps=touch.flaps-previous; assert.equal(report.panelTapFlaps,1);
  }
  // Exercise the native application gesture queue, including all three
  // terminal kinds. Queue completion, sender wake-up and game action are
  // independently observed. No direct game-state or GUI touch injection.
  const events=[0,0x03000073,0x03000074,0x03000075,0x03000076,0x03000078];
  const gesture = kind => {
    const old=[touch.replies,touch.waits,touch.returns];
    const event=Buffer.alloc(200); event.writeUInt32LE(events[kind]);
    event.writeUInt32LE(450,12); event.writeUInt32LE(300,16); event.writeUInt32LE(0x3000,188);
    const queue=sim.u32(sim.u32(0x6036ee7c)+208);
    lab.calls(0x510a7450,{a0:queue,a1:lab.alloc(event,4)},undefined,undefined,2000000);
    s.settle('application touch');
    assert.deepEqual([touch.replies,touch.waits,touch.returns],old.map(n=>n+1));
    assert.equal(touchFrame,null);
  };
  for(const end of Array.from({length:18},(_,i)=>3+i%3)) {
    const count=touch.flaps;
    gesture(1); idle(200); gesture(1); gesture(2); idle(200);
    assert.equal(touch.flaps,count+1);
    gesture(end); assert.equal(byte(sy.flappy_contact),0);
  }
  key('s1','shutter-exit'); assert.equal(lab.state(),0x0108);
  assert.equal(state(),0); assert.equal(timer(),0); assert.equal(s.through_off,false);
  checkPreview('after shutter exit', 1);
  const stopped=ticks(); idle(1500); assert.equal(ticks(),stopped);
  assert.deepEqual(report.through.filter(e=>e.stage!=='startup' && e.stage!=='s1'), pictureMode ? [] :
    [{stage:'setup',ctrl:0},{stage:'shutter-exit',ctrl:1}]);
  assert.ok(report.snapshots.every(r=>r.images===0 && r.recording===null));
  if (pictureMode) {
    openPictureGames();
    for(let i=0;byte(sy.games_selection)!==4 && i<6;i++) key('down');
  } else {
  key('menu','reopen-setup'); assert.equal(panel(),329); assert.equal(s.through_off,true);
  key('ok','reopen-extras'); assert.equal(state(),7);
  // A touch on the opaque hub cannot hit one of the Setup widgets underneath.
  gesture(1); gesture(4); assert.equal(state(),7); assert.equal(byte(sy.flappy_drain),0);
  key('ok'); assert.equal(state(),1);
  key('up'); assert.equal(byte(sy.games_selection),5);
  key('ok','launcher-back-item'); assert.equal(state(),7);
  key('ok'); key('up'); key('up'); assert.equal(byte(sy.games_selection),4);
  }
  key('ok'); assert.equal(state(),6); assert.notEqual(timer(),0);
  gesture(1); assert.equal(byte(sy.flappy_contact),1);
  stage='display-change'; s.display_input('eye',1); idle(300); snap(stage);
  assert.equal(state(),0); assert.equal(timer(),0); assert.equal(byte(sy.games_paint_valid),0);
  assert.equal(sim.u32(sy.games_screen),0); assert.equal(byte(sy.flappy_contact),0);
  checkPreview('after display change', 1);
  const afterSwitch=ticks(); idle(1000); assert.equal(ticks(),afterSwitch);
  report.status='pass';
} catch(e) {
  report.status='failed'; report.error=e.stack; console.error(e.stack); process.exitCode=1;
} finally {
  fs.writeFileSync(path.join(out,'replay.json'),JSON.stringify(report,null,2)+'\n');
  player.session?.close();
}
