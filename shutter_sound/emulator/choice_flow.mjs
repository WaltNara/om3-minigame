import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

export function testChoice(player, build, audio, saveDriveFrame, sdFiles) {
  const s = player.session, { lab } = s, { sim } = lab;
  const sy = build.symbols;
  const checks = [];
  const byte = (at) => sim.read(at, 1)[0];
  const state = () => byte(sy.games_state);
  const preset = () => byte(sy.sound_choice);
  const idle = (ms) => {
    s.idle_slice(lab.lab_time() + ms * 1e6);
    player.publish_audio();
  };
  const key = (id) => {
    s.key(id, 'down');
    s.camapp.pump();
    idle(80);
    s.key(id, 'up');
    s.camapp.pump();
    idle(200);
  };
  const pcmSince = (index) => Buffer.concat(audio.slice(index)
    .filter((event) => event.source === 'native')
    .map((event) => Buffer.from(event.samples.buffer, event.samples.byteOffset, event.samples.byteLength)));
  const sha = (pcm) => createHash('sha256').update(pcm).digest('hex');
  const sdPreset = label => {
    const pcm = sdFiles[label].subarray(112);
    return { frames: pcm.length / 4, pcm_sha256: sha(pcm) };
  };
  const writeCardFile = (name, bytes) => {
    const st = s.storage, f = st.f.fileif;
    const filename = st.f.names.drive + ':\\OM3MOD\\' + name;
    const fp = st.fileif(f.open, [st.cstr(filename), st.cstr('wb')], filename);
    assert.ok(fp, `open fixture ${name}`);
    const block = lab.alloc(new Uint8Array(8192), 64);
    for (let offset = 0; offset < bytes.length; offset += 8192) {
      const part = bytes.subarray(offset, offset + 8192);
      sim.write(block, part);
      assert.equal(st.fileif(f.write, [block, 1, part.length, fp], name), part.length);
    }
    assert.equal(st.fileif(f.close, [fp], name), 0);
  };
  const capture = (label, expected) => {
    const from = audio.length, before = s.camapp.release;
    s.key('s1', 'down');
    s.camapp.pump();
    idle(250);
    assert.equal(pcmSince(from).length, 0, 'half-press');
    s.key('s2', 'down');
    s.camapp.pump();
    idle(750);
    s.key('s2', 'up');
    s.camapp.pump();
    s.key('s1', 'up');
    s.camapp.pump();
    idle(450);
    assert.equal(s.camapp.release, before + 1, label);
    if (expected) idle(expected.frames / 48 + 40);
    const pcm = pcmSince(from);
    assert.equal(pcm.length, expected ? expected.frames * 4 : 0, label);
    if (expected) assert.equal(sha(pcm), expected.pcm_sha256, label);
    checks.push({ label, native_frames: pcm.length / 4, pcm_sha256: sha(pcm) });
  };

  idle(1500);
  sim.write(0xa32de590, Uint8Array.of(255, 3, 0, 0));
  sim.write(0x60369308, Uint8Array.of(0, 240, 0, 0));
  key('s1');
  key('menu');
  assert.equal(Buffer.from(sim.read(0x6037e8cc, 2)).readUInt16LE(), 329);
  for (let i = 0; i < 3; i++) key('down');
  key('ok');
  assert.equal(state(), 7);
  assert.equal(s.through_off, true);
  key('down');
  key('ok');
  assert.equal(state(), 8);
  assert.equal(preset(), 0);

  function commit(value, label, expected = build.presets[label]) {
    const before = audio.length;
    key('ok');
    assert.equal(preset(), value);
    assert.equal(state(), 7);
    assert.equal(s.through_off, true);
    if (expected && expected.frames > 8000) idle(expected.frames / 48 + 40);
    const pcm = pcmSince(before);
    if (expected) {
      assert.equal(pcm.length, expected.frames * 4, label);
      assert.equal(sha(pcm), expected.pcm_sha256, label);
    } else {
      assert.equal(pcm.length, 0, label);
    }
    assert.equal(byte(0xa32da3a8), 0, 'native short-sound player released');
    assert.equal(s.audio_hw.status().port.running, false);
    checks.push({ label, native_frames: pcm.length / 4, pcm_sha256: sha(pcm) });
  }

  let before = audio.length;
  key('down');
  assert.equal(pcmSince(before).length, 0, 'moving the cursor is silent');
  commit(1, '5D');
  key('ok');
  assert.equal(byte(sy.sound_cursor), 1);
  key('down');
  commit(2, 'D850');
  key('ok');
  before = audio.length;
  key('down');
  key('ok');
  assert.equal(state(), 8, 'missing clip leaves the chooser open');
  assert.equal(preset(), 2);
  key('menu');
  assert.equal(preset(), 2);
  assert.equal(pcmSince(before).length, 0, 'unavailable and cancelled choices stay silent');
  if (build.single_exposure) {
    key('s1');
    assert.equal(lab.state(), 0x0108);
    assert.equal(lab.get(3265), 0);
    capture('Mechanical Single', null);
    key('ok');
    key('down');
    key('down');
    assert.equal(lab.get(261), 3265, 'stock SCP Drive field');
    s.dial_input('main', 1);
    s.camapp.pump();
    idle(150);
    assert.equal(lab.get(3265), 30, 'Silent Single');
    key('s1');
    assert.equal(lab.state(), 0x0108);
    capture('Silent Single', build.presets.D850);
    key('menu');
    for (let i = 0; !byte(sy.games_row_selected) && i < 4; i++) key('down');
    assert.equal(byte(sy.games_row_selected), 1);
    key('ok');
    key('down');
  }
  key('ok');
  assert.equal(state(), 8);
  if (sdFiles) {
    writeCardFile('CIALLO.WAV', sdFiles.Ciallo);
    key('down');
    commit(3, 'Ciallo', sdPreset('Ciallo'));
    writeCardFile('MAN.WAV', sdFiles.Man);
    key('ok');
    key('down');
    commit(4, 'Man', sdPreset('Man'));
    writeCardFile('CUSTOM.WAV', sdFiles.Custom.subarray(0, -4));
    key('ok');
    key('down');
    before = audio.length;
    key('ok');
    assert.equal(state(), 8, 'truncated clip leaves the chooser open');
    assert.equal(preset(), 0, 'an overwritten SD clip is released');
    assert.equal(pcmSince(before).length, 0);
    writeCardFile('CUSTOM.WAV', sdFiles.Custom);
    commit(5, 'Custom', sdPreset('Custom'));
    key('s1');
    capture('Silent Single with Custom selected', sdPreset('Custom'));
    key('menu');
    for (let i = 0; !byte(sy.games_row_selected) && i < 4; i++) key('down');
    assert.equal(byte(sy.games_row_selected), 1);
    key('ok');
    key('down');
    key('ok');
    assert.equal(byte(sy.sound_cursor), 5);
    const oversized = Buffer.concat([sdFiles.Custom, Buffer.alloc(4)]);
    oversized.writeUInt32LE(oversized.length - 8, 4);
    oversized.writeUInt32LE(oversized.length - 112, 108);
    writeCardFile('CUSTOM.WAV', oversized);
    before = audio.length;
    key('ok');
    assert.equal(state(), 8, 'oversized clip leaves the chooser open');
    assert.equal(preset(), 0);
    assert.equal(pcmSince(before).length, 0);
    key('down');
  } else {
    key('up');
    key('up');
  }
  commit(0, 'Silent');
  key('s1');
  assert.equal(lab.state(), 0x0108);
  if (build.single_exposure) capture('Silent Single with Silent selected', null);
  if (saveDriveFrame) {
    const describe = action => ({ action, gui: lab.state(), drive: lab.get(3265),
      cursor: [lab.get(261), lab.get(293)], settings: lab.settings_log.slice(-4) });
    const choices = [describe('shooting')];
    key('ok');
    choices.push(describe('scp'));
    let found = lab.get(261) === 3265;
    for (let row = 0; row < 8 && !found; row++) {
      const seen = new Set();
      for (let col = 0; col < 8 && !found; col++) {
        const cursor = lab.get(261);
        if (seen.has(cursor)) break;
        seen.add(cursor);
        key('right');
        choices.push(describe('right'));
        found = lab.get(261) === 3265;
      }
      if (!found) {
        key('down');
        choices.push(describe('down'));
        found = lab.get(261) === 3265;
      }
    }
    if (found) {
      saveDriveFrame(0);
      for (let i = 0; i < 14; i++) {
        s.dial_input('main', 1);
        s.camapp.pump();
        idle(100);
        choices.push(describe('main+1'));
        saveDriveFrame(choices.at(-1).drive);
      }
    }
    checks.push({ drives: choices });
  }
  return checks;
}
