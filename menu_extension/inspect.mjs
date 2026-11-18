// Read-only E147 main-menu inventory. No firmware or emulator hooks are changed.
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
globalThis.OM_EMU_MODEL = 'E147';
process.env.OM_EMU_MODEL = 'E147';
const imp = p => import(pathToFileURL(path.join(root, 'work/om-emu/emu', p)).href);
const [M, env, model] = await Promise.all([
  imp('src/lab/menudata.mjs'), imp('checks/lib/env.mjs'), imp('src/fw/model.mjs'),
]);
const stock = env.readBytes(env.ORIGINAL);
env.checkImage(stock);
const accepted = fs.readFileSync(path.join(root, 'work/current-games/row-main.bin'));
const sha = b => createHash('sha256').update(b).digest('hex');
if (sha(accepted) !== 'a3b5e0aa720f3703f6d3adcf771edb855ac99d63c24c116816976ff37c203ed8')
  throw Error('accepted five-r5 image differs');
const strings = new M.Strings(['en'], env.loadImage(), env.loadBlock());
const inventory = bytes => {
  const img = new M.Image(bytes);
  const groups = M.groups(img);
  return M.tabs(img).map(tab => ({
    ...tab,
    pages: tab.pages.map(id => {
      const page = groups.get(id);
      return {id, record: page.record, title: M.render(page.title, strings, 'en'),
        rows: (page.labels ?? []).map(row => ({
          mode: row.key, label: M.render(row, strings, 'en'),
          choices: (page.values.get(row.key) ?? []).map(v => ({value: v.key, label: M.render(v, strings, 'en')})),
        }))};
    }),
  }));
};
const stockMenu = inventory(stock), acceptedMenu = inventory(accepted);
if (JSON.stringify(stockMenu) !== JSON.stringify(acceptedMenu))
  throw Error('r5 main-menu inventory differs from stock; review before extending');
const report = {schema: 1, model: model.MODEL, scope: 'static menu tables only; no new row executed',
  stock_sha256: sha(stock), accepted_sha256: sha(accepted),
  list_menu: model.fact('menu.list_menu', true),
  addresses: Object.fromEntries(['TAB_IDS', 'TAB_TABLE', 'GROUP_LIST', 'CUSTOM_VALUE', 'ROW_ORDER', 'PANEL_SWITCH']
    .map(k => [k, '0x' + M[k].toString(16)])),
  accepted_main_menu_equals_stock: true, tabs: stockMenu};
const out = path.join(root, 'work/menu-extension');
fs.mkdirSync(out, {recursive: true});
fs.writeFileSync(path.join(out, 'inventory.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({status: 'PASS', tabs: stockMenu.length,
  setup: stockMenu.find(t => t.id === 7).pages.map(p => ({id: p.id, title: p.title, rows: p.rows.length})),
  report: 'work/menu-extension/inventory.json'}, null, 2));
