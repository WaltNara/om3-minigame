# ES sound development

Use **MENU → Setup → Information Record → ES sound** to choose the sound.
5D and D850 are built in. Ciallo, Man and Custom load from `OM3MOD` when the
selection is confirmed. The selection lasts until power-off.
[Install guide](INSTALL.md) · [SD WAV format](SOUND_FILES.md) · [Preset credits](SOURCES.md)

## Playback and ownership

- `native_menu.s` uses the stock Setup viewer. `sd_choice.s` validates and
  loads one WAV into a fixed buffer. Selecting a sound does the card read.
- `capture_sound.s` signals the `UI_OUT` worker from the existing capture
  paths. The worker checks the drive mode and starts playback in Silent Single
  and Silent Sequential. A new shot can rewind the current PCM cursor before
  the next refill. Audio already queued to the transmitter plays first.
- `choice.s` supplies fresh volume values to the native player on every new
  start. Native command `0x22` divides three values by ten in place. Reusing
  the converted values caused the first-shot-only failure on the camera.
- `UI_OUT` closes the player once the native transmitter releases ownership.
  A rejected registration releases the opened handle directly. While waiting
  for release, the worker polls every 32 ms with a budget of 48 polls after
  the latest request. Playback keeps the selected buffer available until the
  player releases it.

## Build and verify

`py -3 build/extras.py all` builds and tests the combined firmware and packages
the tested image. The verifier ties the game, touch, menu and audio reports to
the image hash. `emulator/choice_flow.mjs` checks the volume request at the
native handler because OM-Emu's PCM capture is upstream of the speaker gain.
The optional `--diagnostics` build adds an INFO readout on the ES sound row.
[Development setup](../docs/DEVELOPMENT.md) · [Verification results](../docs/STATUS.md) ·
[First-shot diagnosis](ES_STATUS.md)

The memory and copy-retrigger probes remain available for firmware research.
`bank.py` uses a versioned, checksummed bank for development tools and preset
generation. The camera menu loads WAV files. The installable image comes from
`build_native.py`, with `layout.json` pinning the accepted games image and sound
region.
