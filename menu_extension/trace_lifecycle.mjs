// Observe stock MENU versus the accepted Games host. No firmware patch or flash.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import zlib from 'node:zlib';
const root = fileURLToPath(new URL('../', import.meta.url));
const mode = process.argv[2] ?? 'stock';
if (!['stock', 'r5'].includes(mode)) throw Error('use stock or r5');
globalThis.OM_EMU_MODEL = 'E147';
process.env.OM_EMU_MODEL = 'E147';
const imp = p => import(pathToFileURL(path.join(root, 'work/om-emu/emu', p)).href);
const {loadBlock, ORIGINAL, checkImage} = await imp('checks/lib/env.mjs');
const {A, fact} = await imp('src/fw/model.mjs');
const {runtime} = await imp('src/lab/hle.mjs');
const {expandImage} = await imp('src/fw/expand.mjs');
const {Player} = await imp('src/lab/player.mjs');
const {PLAYER_PARSER} = await imp('scenarios/session_replay.mjs');
const {cardFromImage} = await imp('src/lab/sdcard.mjs');
const raw = fs.readFileSync(mode === 'stock' ? ORIGINAL : path.join(root, 'work/current-games/row-main.bin'));
const hash = createHash('sha256').update(raw).digest('hex');
if (mode === 'stock') checkImage(raw);
else if (hash !== 'a3b5e0aa720f3703f6d3adcf771edb855ac99d63c24c116816976ff37c203ed8') throw Error('wrong r5 image');
let card = cardFromImage(fs.readFileSync(path.join(root, 'work/native-build/paired.omsd')));
const pl = new Player({...PLAYER_PARSER, tab:'7,6,6', no_browser:true, idle:'off', a15:'on', audio:'off', out:'<out>', no_wait_on_error:true},
  {rom:expandImage(raw), resBlock:loadBlock(), createHash,
    card:{open:()=>card, save:x=>{card=x;}}, wallClock:()=>performance.now()/1000,
    deflate:(b,l)=>new Uint8Array(zlib.deflateSync(b,{level:l})), inflate:b=>new Uint8Array(zlib.inflateSync(b))});
const report = {schema:1, mode, image_sha256:hash, status:'started',
  scope:'Native application requests observed; S-TRAACK stands in for the receiver. No sensor/power measurement.',
  events:[], snapshots:[], instrumentation:[], fixtures:[]};
const out = path.join(root,'work/menu-extension');
fs.mkdirSync(out,{recursive:true});
let stage='boot';
try {
  if(mode==='r5') {
    const ca=await imp('src/lab/camapp.mjs');
    ca.CA_TASK_ENTRIES.push(0x50a6e603);
    report.fixtures.push('allow task 0x50a6e603 as existing r5 replay does');
  }
  pl.open_session();
  if(pl.phase!=='running') throw Error(pl.error?.stack ?? pl.phase);
  const s=pl.session, lab=s.lab, sim=lab.sim;
  const symbols=mode==='r5' ? JSON.parse(fs.readFileSync(path.join(root,'work/current-games/build.json'))).symbols : null;
  const u16=a=>{const b=sim.read(a,2);return b[0]|b[1]<<8;};
  const watch=(at,name,fn)=>{
    const previous=lab.hooks.get(runtime(at));
    report.instrumentation.push({name,notation:at,runtime:runtime(at),previous:previous?.[1]??null});
    if(previous) lab.wrap(at,prev=>(h,r)=>{fn(r);return prev(h,r);},'research-'+name);
    else lab.observe(at,(_l,r)=>fn(r),'research-'+name);
  };
  const add=(name,r,data)=>report.events.push({stage,name,ms:lab.lab_time()/1e6,caller:r.mdr,...data});
  watch(fact('shooting.auto_through',0x50abd373),'ctrlAutoThrough',r=>add('ctrlAutoThrough',r,{ctrl:r.d0}));
  for(const at of [A(0x50af7cb9),A(0x50af7cbe)]) watch(at,'transaction',r=>{
    if(r.a1 && u16(r.a1+4)===991) add('TRA991',r,{ctrl:sim.u32(r.a1+32)});
  });
  for(const [name,key,ref] of [['startShootingService','shooting.start',0x50ae1124],['endShootingService','shooting.end',0x50ad7e8a]])
    watch(fact(key,ref),name,r=>add(name,r,{}));
  // The existing renderer patches this native paint tail. Count execution
  // under the full menu to see whether it is reachable without Picture Mode.
  const paintTailByStage = {};
  watch(0x510d6fc9,'native paint tail',()=>{
    paintTailByStage[stage]=(paintTailByStage[stage] ?? 0)+1;
  });
  report.paint_tail_by_stage=paintTailByStage;
  const snap=label=>{
    const rec={label,ms:lab.lab_time()/1e6,gui:lab.state_name(lab.state()),
      through_off_standin:s.through_off,shooting_service:s.camapp.shooting,
      recording:s.camapp.recording,images:s.camapp.images.length};
    if(lab.state()===0x0b02) rec.menu_panel=lab.panels.at(-1)?.[1] ?? null;
    if(mode==='r5') Object.assign(rec,{game:sim.read(symbols.games_state,1)[0],
      timer:u16(symbols.mario_handle),ticks:sim.u32(symbols.mario_ticks)});
    report.snapshots.push(rec);console.log(JSON.stringify(rec));
  };
  const idle=ms=>s.idle_slice(lab.lab_time()+ms*1e6);
  const click=(key,label=key)=>{stage=label;s.key(key,'down');s.camapp.pump();idle(150);s.key(key,'up');s.camapp.pump();idle(1200);snap(label);};
  idle(1500);
  if(mode==='r5') {
    sim.write(0xa32de590,new Uint8Array([255,3,0,0]));sim.write(0x60369308,new Uint8Array([0,240,0,0]));
    report.fixtures.push('same section-ready/card-media words as existing r5 replay; neither changes through state');
  }
  snap('after-boot');
  click('s1','startup-halfpress');
  if(lab.state()!==0x0108) throw Error('startup did not reach shooting GUI');
  snap('shooting');
  click('menu','menu-open');
  stage='menu-idle';idle(3000);snap(stage);
  click('menu','menu-close');
  click('menu','menu-reopen');
  // Seeded to Setup page 6, Firmware Version. OK opens its read-only panel.
  click('ok','menu-detail-open');
  click('menu','menu-detail-back');
  click('s1','menu-halfpress-exit');
  if(mode==='r5') {
    click('ok','super-control');click('ok','picture-mode');
    for(let i=0;i<13;i++)click('down','row-'+(i+1));
    click('ok','games-launcher');
    for(let i=0;i<4;i++)click('down','launcher-'+(i+1));
    click('ok','flappy-enter');
    stage='flappy-idle';idle(3000);snap(stage);
    click('s1','flappy-halfpress-exit');
    click('menu','menu-after-games');
    click('menu','shooting-after-games-menu');
  }
  const e=report.events, at=k=>report.snapshots.find(x=>x.label===k);
  if(!e.some(x=>x.stage==='menu-open'&&x.name==='TRA991'&&x.ctrl===0)||
     !['menu-close','menu-halfpress-exit'].every(stage=>e.some(x=>x.stage===stage&&x.name==='TRA991'&&x.ctrl===1)))
    throw Error('MENU stop/restart request missing');
  if(!at('menu-idle').through_off_standin||at('menu-close').through_off_standin||at('menu-halfpress-exit').through_off_standin)
    throw Error('MENU through-state mismatch');
  if(at('menu-detail-open').menu_panel!==440||at('menu-detail-back').menu_panel!==329||
     !at('menu-detail-open').through_off_standin||!at('menu-detail-back').through_off_standin||
     e.some(x=>x.stage.startsWith('menu-detail')&&x.name==='TRA991')||
     !paintTailByStage['menu-detail-open']||!paintTailByStage['menu-detail-back'])
    throw Error('Full-menu detail lifecycle or paint did not match');
  if(mode==='r5'&&(at('games-launcher').game!==1||at('flappy-enter').game!==6||at('flappy-idle').through_off_standin||
     at('flappy-idle').ticks<=at('flappy-enter').ticks||at('flappy-halfpress-exit').game!==0||at('flappy-halfpress-exit').timer!==0))
    throw Error('Games comparison did not reach expected states');
  if(report.snapshots.some(x=>x.recording!==null||x.images!==0)) throw Error('Unexpected recording or capture in idle comparison');
  report.status='pass';
} catch(e) {report.status='failed';report.error=e.stack;process.exitCode=1;}
finally {
  fs.writeFileSync(path.join(out,`lifecycle-${mode}.json`),JSON.stringify(report,null,2)+'\n');
  pl.session?.close();
}
console.log(JSON.stringify({mode,status:report.status,events:report.events,error:report.error}));
