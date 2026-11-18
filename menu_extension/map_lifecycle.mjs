// Candidate locations for the E143 through-image research on pinned E147.
// Map output requires disassembly review; this script changes no firmware.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const root=fileURLToPath(new URL('../',import.meta.url));
const imp=p=>import(pathToFileURL(path.join(root,'work/om-emu/emu',p)).href);
const {buildMap,CODE_BASE}=await imp('src/fw/xmap.mjs');
const {PORTS}=await imp('src/fw/ports.mjs');
const {MODELS,romPath}=await imp('src/fw/models.mjs');
const read=code=>fs.readFileSync(path.join(root,'work/om-emu',romPath(MODELS[code])));
const a=read('E143'),b=read('E147'),sha=b=>createHash('sha256').update(b).digest('hex');
for(const [code,bytes] of [['E143',a],['E147',b]])if(sha(bytes)!==MODELS[code].rom_sha256)throw Error('wrong '+code+' firmware');
const targets={ctrl_auto_through:0x50abd373,tra991_ctor:0x50ac1495,
  component_ctrl:0x50c7d457,
  cap_start:0x50bd0467,cap_force_stop:0x50bd04c9,
  cap_start_sync:0x50bcfeb1,cap_start_impl:0x50bcc0d8,
  api_tft_start:0x504214fc,menu_bank_fill:0x504223a4};
const seeds=new Set([0]);
for(const x of [...Object.keys(PORTS.E147).map(Number),...Object.values(targets)])
  if(x>CODE_BASE&&x<CODE_BASE+a.length)seeds.add(x-CODE_BASE);
const map=buildMap(a,b,{baseA:0x60021020,baseB:0x60021020,seeds:[...seeds]});
const functions={};
for(const [name,address] of Object.entries(targets)){
  const off=map.code[address-CODE_BASE];
  functions[name]=off<0?null:{e143:'0x'+address.toString(16),notation:'0x'+(CODE_BASE+off).toString(16),
    runtime:'0x'+(0x60021020+off).toString(16),expected:b.subarray(off,off+24).toString('hex')};
}
const report={scope:'candidate map; review disassembly before interpreting',e143_sha256:sha(a),e147_sha256:sha(b),functions};
const out=path.join(root,'work/menu-extension');fs.mkdirSync(out,{recursive:true});
const target=parseInt(functions.component_ctrl.notation)-CODE_BASE;
report.component_ctrl_call_candidates=[];
for(let i=b.indexOf(0xdd);i>=0&&i+7<=b.length;i=b.indexOf(0xdd,i+1))
  if(i+b.readInt32LE(i+1)===target)report.component_ctrl_call_candidates.push('0x'+(CODE_BASE+i).toString(16));
// E147 dispatcher at 0x50d8e829 subtracts 413, then probes 128 entries.
const dispatchTable=0x60f10b50;
const key=991-413;
for(let n=0;n<128;n++){
  const slot=(key+n)&127;
  const offset=dispatchTable-0x60021020+slot*8;
  const entry=b.readUInt32LE(offset);
  if(entry===0) break;
  if(entry!==key) continue;
  const address=b.readUInt32LE(offset+4);
  report.tra991_dispatch={table_runtime:dispatchTable,slot,key,case_runtime:address,case_notation:address-0x10021020};
  break;
}
if(!report.tra991_dispatch) throw Error('E147 dispatch table missing TRA991');
fs.writeFileSync(path.join(out,'lifecycle-map.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
