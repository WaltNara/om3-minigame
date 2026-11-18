import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

export function testChoice(player, build, audio, saveDriveFrame, sdFiles) {
  const s = player.session, { lab } = s, { sim } = lab;
  const sy = build.symbols;
  const checks = [];
  const byte = (at) => sim.read(at, 1)[0];
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
  const editing = () => byte(sy.sound_editing);
  const cursor = () => byte(sy.sound_cursor);
  const notation = address => address - 0x10021020;
  const u16 = at => Buffer.from(sim.read(at, 2)).readUInt16LE();
  const captureFixture = site => {
    const record = lab.alloc(new Uint8Array(512), 16);
    const owner = lab.alloc(new Uint8Array(512), 16);
    if (site === build.capture_sites[0]) {
      // Start at the five displaced bytes and let the native append and
      // caller epilogue complete. The fixture stands in for the sensor.
      lab.call(notation(site), {a0: owner, a1: record, d0: 0},
               null, [0x30, 12], 100000);
      assert.equal(sim.u32(owner + 276), record);
    } else {
      const params = new Uint8Array(4);
      new DataView(params.buffer).setUint32(0, owner, true);
      sim.write(record + 72, params);
      lab.call(notation(0x60bc2286), {a0: record}, null, [0,0], 100000);
    }
    s.settle('capture sound dispatch');
  };
  const captureSite = (site, label, expected) => {
    const index = audio.length;
    captureFixture(site);
    const duration = (expected?.frames ?? 0) / 48 + 250;
    for (let elapsed = 0; elapsed < duration; elapsed += 16) idle(16);
    const pcm = pcmSince(index);
    const bytes = (expected?.frames ?? 0) * 4;
    assert.equal(pcm.length, Math.ceil(bytes / 768) * 768, label);
    assert.equal(byte(0xa32da3a8), 0, 'UI_OUT releases the clip');
    assert.equal(s.audio_hw.status().port.running, false);
    if (expected) {
      assert.equal(sha(pcm.subarray(0, bytes)), expected.pcm_sha256, label);
      assert.ok(pcm.subarray(bytes).every(v => v === 0));
    }
    checks.push({label, native_frames: bytes / 4, pcm_sha256: sha(pcm.subarray(0, bytes))});
  };
  const choose = (value, accepted = true) => {
    key('ok');
    assert.equal(editing(), 1);
    for (let i = 0; cursor() !== value && i < 6; i++) key('right');
    assert.equal(cursor(), value);
    const index = audio.length;
    key('ok');
    assert.equal(pcmSince(index).length, 0, 'selection commits without starting playback');
    assert.equal(editing(), accepted ? 0 : 1);
    if (accepted) assert.equal(preset(), value);
  };
  idle(1500);
  sim.write(0xa32de590, Uint8Array.of(255, 3, 0, 0));
  sim.write(0x60369308, Uint8Array.of(0, 240, 0, 0));
  key('s1');
  key('menu');
  assert.equal(u16(0x6037e8cc), 329);
  for (let i = 0; i < 3; i++) key('down');
  saveDriveFrame('setup');
  choose(3, false);
  saveDriveFrame('missing');
  key('menu');
  assert.equal(editing(), 0);
  assert.equal(preset(), 0);
  assert.equal(lab.state(), 0x0b02, 'cancel stays on Setup page');
  choose(1);
  key('ok');
  assert.equal(cursor(), 1);
  saveDriveFrame('sound');
  key('menu');
  key('s1');
  assert.equal(lab.get(3265), 0);
  captureSite(build.capture_sites[0], 'Mechanical Single', null);
  key('ok');
  key('down');
  key('down');
  assert.equal(lab.get(261), 3265, 'stock SCP Drive field');
  s.dial_input('main', 1);
  s.camapp.pump();
  idle(150);
  assert.equal(lab.get(3265), 30);
  key('s1');
  // Drop the first clip's TX completion flag while keeping the native TX
  // callback and ownership teardown. The next shot must still play.
  const txSignal = 0x60a853c3;
  const previous = lab.hooks.get(txSignal);
  const flag = u16(0x60043156);
  let dropped = 0;
  assert.notEqual(flag, 0);
  lab.hook(notation(txSignal), (h, r) => {
    if (r.d0 === flag && r.d1 === 0x80000000) {
      dropped++;
      h.finish(r, {d0:0});
    } else if (previous) previous[0](h, r);
    else h.passthrough(r);
  }, 'drop TX-done flag');
  try {
    captureSite(build.capture_sites[0], 'Single 5D 1', build.presets['5D']);
  } finally {
    if (previous) lab.hooks.set(txSignal, previous);
    else lab.hooks.delete(txSignal);
  }
  assert.equal(dropped, 1);
  captureSite(build.capture_sites[0], 'Single 5D 2', build.presets['5D']);
  captureSite(build.capture_sites[0], 'Single 5D 3', build.presets['5D']);
  checks.push({label:'TX completion loss', dropped, subsequent_playback:true});
  key('menu');
  choose(2);
  key('s1');
  captureSite(build.capture_sites[0], 'Single D850', build.presets.D850);
  key('menu');
  for (const [value, label] of [[3, 'Ciallo'], [4, 'Man'], [5, 'Custom']]) {
    const filename = label.toUpperCase() + '.WAV';
    if (label === 'Custom') {
      writeCardFile(filename, sdFiles[label].subarray(0, -4));
      choose(value, false);
      key('menu');
    }
    writeCardFile(filename, sdFiles[label]);
    choose(value);
    key('s1');
    captureSite(build.capture_sites[0], label, sdPreset(label));
    if (label === 'Ciallo') {
      key('ok');
      for (let i = 0; lab.get(261) !== 3265 && i < 3; i++) key('down');
      assert.equal(lab.get(261), 3265);
      for (let i = 0; lab.get(3265) !== 32 && i < 8; i++) {
        s.dial_input('main', 1);
        s.camapp.pump();
        idle(150);
      }
      assert.equal(lab.get(3265), 32, 'Silent Sequential');
      key('s1');
      captureSite(build.capture_sites[1], 'Sequential Ciallo', sdPreset(label));
      const from = audio.length;
      for (let i = 0; i < 3; i++) {
        captureFixture(build.capture_sites[1]);
        for (let p = 0; p < 5; p++) idle(16);
      }
      for (let p = 0; p < 80; p++) idle(16);
      const sound = sdFiles[label].subarray(112);
      const pcm = pcmSince(from);
      const onsets = [];
      for (let offset = 0; offset + 768 <= pcm.length; offset += 768)
        if (pcm.subarray(offset, offset + 768).equals(sound.subarray(0, 768))) onsets.push(offset);
      assert.equal(onsets.length, 3, 'successive captures restart the long sound');
      for (let i = 0; i + 1 < onsets.length; i++) {
        const bytes = onsets[i + 1] - onsets[i];
        assert.ok(bytes < sound.length);
        assert.deepEqual(pcm.subarray(onsets[i], onsets[i + 1]), sound.subarray(0, bytes));
      }
      assert.deepEqual(pcm.subarray(onsets.at(-1), onsets.at(-1) + sound.length), sound);
      assert.equal(byte(0xa32da3a8), 0);
      checks.push({label:'Sequential long-clip restart', attacks:onsets.length, frames:onsets.map(n => n / 4)});
      captureSite(build.capture_sites[1], 'Sequential Ciallo after burst', sdPreset(label));
      // Restore Silent Single for the remaining individual presets.
      key('ok');
      for (let i = 0; lab.get(3265) !== 30 && i < 8; i++) {
        s.dial_input('main', -1);
        s.camapp.pump();
        idle(150);
      }
      assert.equal(lab.get(3265), 30);
      key('s1');
    }
    key('menu');
  }
  choose(0);
  key('s1');
  captureSite(build.capture_sites[0], 'Silent Single with Silent selected', null);
  return checks;
}
