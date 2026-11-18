# OM-3 shutter sound development

Generated sound banks, mapping reports and probe results go in
`work/shutter-sound/`. The current build uses the r5 games image and a native
Setup row, **ES sound**. The selection lasts for the powered session.

## Current results

- The [current trial](TRIAL_NATIVE.md) uses the native menu font and loads
  **Ciallo**, **Man** and **Custom** from `OM3MOD`. Missing and malformed
  files stay unselected. The format supports 48,000 PCM frames, or one
  second. `build_native.py` assembles the row, SD loader and CapBuf hooks.
  `build/extras.py all` builds, tests and packages the combined image.
- Playback uses the native copy path. A capture requests the sound on UI_OUT
  in Silent Single or Silent Sequential. A new capture rewinds the copy
  cursor before the next refill. The transport drains audio already queued
  for hardware. UI_OUT closes the player after the native transmitter
  releases ownership. The tests cover repeated starts after a lost TX-done
  notification or rejected audio registration, byte-matched PCM and a burst
  with a complete final tail. Each completed playback must leave the native
  audio handles, copy task, transmitter and WAV buffer lease idle.
  [Sound file guide](SOUND_FILES.md)

## Earlier trials and research

- The repaired E147 emulator probe plays PCM byte for byte through native audio
  code. The 100-cycle run released the player each time. The AF-key control uses
  OM-Emu's synthesized beep. The OM-3 factory samples are outside the updater.
- Native direct playback of 5D waited about 141 ms for the remaining clip when
  stopped 25 ms into playback. The copied path played 5D correctly during
  ordinary completion, then timed out during early stop. Both results came
  from OM-Emu.
- A 160-byte native [copy renderer](copy_retrigger.s) restarts the sample cursor
  inside the existing 4 ms copy periods. Host-generated shots restarted Man
  at 10 fps and Ciallo at 20 fps with exact PCM and 30–32 ms of simulated
  buffering. When two requests arrived for one period, the latest played.
  The final request played its full tail. A separate Silent transition
  replaced the tail with silence after the buffered periods. A regular D850
  copy on the patched image also passed with the renderer disarmed.
- The [memory probe](memory.py) verified a native section-1 loader request for
  32 KiB of extra pages and played the complete 5D WAV from the loader's
  uncached address. OM-Emu supplies the NAND read. The 224 KiB erased run beyond
  the existing section-1 copy still needs a physical ownership check.
## Current implementation

- `layout.json` pins E147 stock and accepted r5 hashes, candidate functions,
  corrected audio globals and an erased region for further loader analysis.
- `audit.py` verifies both images, expected function prefixes and erased candidate
  bytes. It produces evidence only; function prefixes do not establish the ABI
  or prove that the candidate region is safely loaded.
- `bank.py` encodes and validates the experimental one-slot bank. Its bounded
  payload is PCM16 stereo 48 kHz, up to five seconds, with a SHA256 checksum. The WAV
  uses LIST/INFO metadata and a short-sound IKEY, with 16-byte-aligned sample data.
- `convert.py` generates an original deterministic click or converts a PCM16 mono
  or stereo WAV, resampling, removing leading silence and limiting peak amplitude.
  Its linear resampler is intended for initial short-clip experiments. It rejects
  experimental banks beyond five seconds. Use the separate one-second SD
  format for the camera loader.
- `retrigger.py` is the executable host reference for a stop/start worker.
  The implemented copy renderer instead moves the clip cursor in AUD_COPY_DATA.
  It handles only copies from the dedicated transport WAV, with one latest
  generation published by its caller. The native driver owns the pending DMA
  periods. In-flight periods finish before the new clip starts.
- `presets.json` and `prepare_presets.py` prepare Canon 5D and Nikon D850 burst
  and single-shot variants plus the two supplied funny clips. Off / Silent is
  the default, represented by no sound bank. See [sources and previews](SOURCES.md).
- `emulator/map_audio.mjs` derives E147 audio-function candidates using the existing
  E143 mapping engine and checks firmware hashes.
- `build_copy_retrigger.py` builds an independent raw r5 overlay that uses
  padding inside the existing section-6 load. The DMA renderer starts disarmed.
  `memory.py` builds a separate raw image to test the section-1 copy boundary.
- `emulator/probe.mjs` starts the E147 native audio tasks with a channel-13
  codec model. It produces structured evidence for normal playback, early
  stop, loading and generation changes. The patched image uses a finite
  host-owned transport WAV for the copied route. The replay labels the
  CPU-2 and NAND stand-ins. The pinned OM-Emu revision is
  `88b753ddb9c0fac35366802133e849600aa519d5`.
## Run

Use `py -3 build/extras.py all` for the current Games and SD-sound trial.
The [developer guide](../docs/DEVELOPMENT.md) covers inputs, validation and
optionally including the local Ciallo and Man files.

From the repository root, with the existing local firmware/tool dependencies:

```powershell
py -3 shutter_sound/test_assets.py
py -3 shutter_sound/test_retrigger.py
py -3 shutter_sound/test_presets.py
py -3 shutter_sound/audit.py
py -3 shutter_sound/convert.py --click --out work/shutter-sound/SHUTTER.BIN
node shutter_sound/emulator/map_audio.mjs
node shutter_sound/emulator/probe.mjs 3
node shutter_sound/emulator/probe.mjs 100 --no-trace
```

Prepare all local sound choices and 10/20 fps listening previews:

```powershell
py -3 shutter_sound/prepare_presets.py --fetch
```

With prepared presets, run the two raw developer builds and their probes:

```powershell
py -3 shutter_sound/memory.py
node shutter_sound/emulator/probe.mjs 3 --section1 --report=work/shutter-sound/probe-section1.json
py -3 shutter_sound/build_copy_retrigger.py
node shutter_sound/emulator/probe.mjs 2 --render-fps=10 --bank=work/shutter-sound/presets/man-full.BIN --report=work/shutter-sound/probe-render-10.json
node shutter_sound/emulator/probe.mjs 2 --render-fps=20 --bank=work/shutter-sound/presets/ciallo-full.BIN --report=work/shutter-sound/probe-render-20.json
node shutter_sound/emulator/probe.mjs 2 --render-fps=20 --mute --bank=work/shutter-sound/presets/ciallo-full.BIN --report=work/shutter-sound/probe-render-silent.json
node shutter_sound/emulator/probe.mjs 3 --render-control --trace-capture --bank=work/shutter-sound/presets/nikond850-single.BIN --report=work/shutter-sound/probe-render-control.json
```

For a personal sound:

```powershell
py -3 shutter_sound/convert.py --input C:/sounds/click.wav --out work/shutter-sound/SHUTTER.BIN
```

The native WAV parser receives the payload starting at a 16-byte-aligned base.
Use `--cut` on a direct bank to reproduce legacy stop behavior. Add `--copy` to
reproduce the early-stop wait in the copied route. Those gates are expected to
fail under the current model. The tested renderer uses native completion and
the probe's explicit end/close to release the finite transport window.

Expect one click for each ordinary electronic single. Bursts use the latest
request available for the next period and may skip superseded requests. Keep
the capture task free of waits and leave movie and AF audio priority with the
stock firmware. To ship, the worker needs bounds on sustained playback and a
verified way to yield the native player after an idle period.

## Sound bank v1

The little-endian header is 48 bytes:

| Offset | Field |
| --- | --- |
| 0 | Eight-byte magic `OM3SND\0\0` |
| 8 | u32 version, currently 1 |
| 12 | u32 payload byte count |
| 16 | SHA256 of the complete WAV payload, 32 bytes |
| 48 | Canonical WAV payload |

The reader rejects unsupported versions, inconsistent or excessive lengths,
checksum changes, duplicate required chunks, noncanonical metadata, unsupported
PCM formats and misaligned sample data. A checksum detects corruption; it is not
an authenticity signature. This format is for developer tools. The camera reads the WAV payload.
