"""Adapt the upstream replay harness for its documented SDLOAD task and Windows."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
UP = ROOT/'vendor/caduceus-om3'
WORK = ROOT/'work/native-build'
for source, name in [('research/emulator/session_probe2.mjs','blank.mjs'), ('tools/emulator/session_ed1.mjs','replay.mjs')]:
    text = (UP/source).read_text(encoding='utf-8')
    text = '// Derived from Caduceus for OM-3, Apache-2.0; see vendor LICENSE and NOTICE.\n' + text
    # The pinned v0.26.2 SD worker entry, confirmed by the emulator's refused task start.
    needle = 'pl.open_session();'
    setup = "const ca = await import(EMU + '/src/lab/camapp.mjs');\nca.CA_TASK_ENTRIES.push(0x50a6e603);\n"
    assert needle in text
    text = text.replace(needle, setup+needle)
    if name == 'replay.mjs':
        text = text.replace('log.push(e);', "if (process.env.GAME_STATE) { const p=parseInt(process.env.GAME_STATE,16); e.game=[...rd(p,16)]; e.score=u32(p+16); e.rng=u32(p+20); e.moves=u32(p+24); e.flags=u32(p+28); e.active=rd(p+32,1)[0]; e.renderBytes=u32(p+36); }\n  e.gselect = [u32(0xa49edf88+12),u32(0xa49edf88+16).toString(16)];\n  log.push(e);")
        text = text.replace('while (!stops.includes(dd.m.getRegs()[9] >>> 0) && n < (cs.max || 200000)) { dd.m.step(); n++; }',
            'let minsp = dd.m.getRegs()[8] >>> 0; while (!stops.includes(dd.m.getRegs()[9] >>> 0) && n < (cs.max || 200000)) { dd.m.step(); n++; const g=dd.m.getRegs(); minsp=Math.min(minsp,g[8]>>>0); if(g[14]) throw new Error(cs.name+": native CPU fault "+g[14]+" at "+(g[9]>>>0).toString(16)); }')
        text = text.replace('name: cs.name, steps: n, regs: {}, mem: []','name: cs.name, steps: n, stackBytes: SP-minsp, regs: {}, mem: []')
        text = text.replace('{ wlog, hits, log, card:', '{ draws: lab.draw_log.filter(d=>d.op==="bitmap" && d.width===256), engineErrors: lab.engine.errors(), wlog, hits, log, card:')
        text = text.replace('log.push(e);','if(process.env.GAME_GC) e.gc=Buffer.from(rd(parseInt(process.env.GAME_GC,16),32)).toString("hex");\n  log.push(e);')
        # Let the emulated camera's own FAT/file stack create the paired card
        # files. This avoids mtools and host-side filesystem approximations.
        seed = r"""
  else if (t === 'seed') {
    const st = s.storage, c = st.f.fileif;
    const dir = st.f.names.drive + ':\\OM3MOD';
    st.fileif(c.mkdir, [st.cstr(dir)], 'demo mkdir');
    for (const name of ['GUIDES.BIN','LABELS.BIN','LOOKS.BIN','TONES.BIN']) {
      const bytes = fs.readFileSync(process.env.GAME_CARD_FILES + '/' + name);
      const fp = st.fileif(c.open, [st.cstr(dir + '\\' + name),st.cstr('wb')], 'demo fopen');
      if (!fp) throw new Error('Cannot open ' + name);
      for (let o=0; o<bytes.length; o+=2048) {
        const b=bytes.subarray(o,Math.min(o+2048,bytes.length));
        const n=st.fileif(c.write,[lab.alloc(b,64),1,b.length,fp],'demo fwrite');
        if (n!==b.length) throw new Error('Short write '+name);
      }
      if (st.fileif(c.close,[fp],'demo fclose')!==0) throw new Error('Close failed '+name);
      console.log('SEEDED',name,bytes.length);
    }
  }
"""
        text = text.replace("  else if (t.startsWith('hold:'))", seed + "  else if (t.startsWith('hold:'))")
    (WORK/name).write_text(text, encoding='utf-8')
