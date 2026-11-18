// Read-only mapping experiment; this file never modifies the vendor checkout.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
const root = fileURLToPath(new URL('../../', import.meta.url));
const emuRoot = path.join(root, 'work/om-emu');
const imp = p => import(pathToFileURL(path.join(emuRoot, 'emu', p)).href);
const { buildMap, CODE_BASE } = await imp('src/fw/xmap.mjs');
const { PORTS } = await imp('src/fw/ports.mjs');
const { MODELS } = await imp('src/fw/models.mjs');
const read = (code, name) => fs.readFileSync(path.join(emuRoot, 'unpacked', code, name));
const a = read('E143', 'OLY_E_143_1900_0000_0000.BIN.blk00000000.OE.0100.bin');
const b = read('E147', 'OLY_E_147_1100_0000_0000.BIN.blk00000000.OE.0100.bin');
for (const [code, bytes] of [['E143', a], ['E147', b]]) {
  if (createHash('sha256').update(bytes).digest('hex') !== MODELS[code].rom_sha256) throw Error(`${code}: wrong image`);
}
const targets = { main: 0x50a62a05, reply: 0x50a62d75, open: 0x50aa9715,
  close: 0x50aa9795, seq_play: 0x50aac292, seq_start: 0x50aac5a2,
  period: 0x50aad2a0, isr: 0x50aa90e2, short_key: 0x50aaa824,
  task_start_cpu: 0x5002d325, sync_send: 0x5002e39d,
  ui_init: 0x5014f4e9, ui_task: 0x5014f56c, ui_request: 0x5014f7e0,
  ui_sound_id: 0x5014f927, ui_sound_ready: 0x5014f98a,
  ui_end: 0x5014fb87, ui_stop: 0x5014fbeb, ui_post_end: 0x5014fc6e };
const seeds = new Set([0]);
for (const x of [...Object.keys(PORTS.E147).map(Number), ...Object.values(targets)])
  if (x > CODE_BASE && x < CODE_BASE+a.length) seeds.add(x-CODE_BASE);
const map = buildMap(a,b,{baseA:0x60021020,baseB:0x60021020,seeds:[...seeds]});
const functions = {};
for (const [name, address] of Object.entries(targets)) {
  const offset = map.code[address-CODE_BASE];
  if (offset < 0) throw Error(`${name}: unmapped`);
  functions[name] = { e143: address, notation: CODE_BASE+offset,
    runtime: 0x60021020+offset, expected: b.subarray(offset,offset+24).toString('hex') };
}
const port = {};
for (const addr of [0x60042dca,0x60042dc8,0x60042d34,0x60043614,0x60043602,0x5002d325,0x600431d4,
  0x5002e39d,0xa32db094,0xa32db0f4,0xa32db164,0x62af27e0,0x62af27d4])
  port['0x'+addr.toString(16)] = PORTS.E147[addr] === undefined ? null : PORTS.E147[addr];
const report = {schema:1,status:'mapping candidates; disassembly review required',
  e143_sha256:createHash('sha256').update(a).digest('hex'),
  e147_sha256:createHash('sha256').update(b).digest('hex'),functions,port};
const out = path.join(root,'work/shutter-sound');
fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(path.join(out,'audio-map.json'), JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
