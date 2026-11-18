# Shutter sound checkpoint — 2026-11-18

**After this checkpoint**, the Extras trial gained the five-label, session-only
chooser. Native playback, loader placement and burst restart have since passed
isolated emulator experiments. Use the [current audio status](../shutter_sound/README.md)
and [integration plan](SHUTTER_SOUND_PLAN.md). The entries below describe the
audio project at the time it was paused.

Paused at the user's request to investigate moving extensions into the full MENU
interface. No shutter firmware candidate has been built, packaged or installed.
The accepted five-r5 build remains the camera-tested baseline. Working sources
are preserved in `shutter_sound/`; generated evidence is in ignored
`work/shutter-sound/`. This checkpoint supersedes the earlier power-stall diagnosis.

## Requirements retained

- Device-wide menu choices: **Silent, 5D, D850, Ciallo, Man**. Silent is default.
  Source catalog labels currently include manufacturer names; shorten the actual
  camera labels when implementing controls.
- Each accepted electronic shot interrupts its previous clip and restarts at
  frame zero. While stopping, keep only the newest pending shot. Never wait on
  audio in the capture task; stale callbacks must not stop the replacement.
- Preserve the supplied funny clips in full, within the validated allocation.
  The host converter accepts up to five seconds; camera RAM capacity is unproved.
- Keep ordinary silent operation and stock AF/movie audio behavior.
- New direction: Games and shutter controls belong in the full MENU, independent
  of the creative dial. See the [menu investigation](../menu_extension/README.md).

## Completed and last verified

- Experimental one-slot bank encoder/validator, PCM16 stereo 48 kHz converter,
  integrity/length checks, conservative level and edge fades.
- Host retrigger reference with generation IDs and latest-request replacement.
- 23 host tests passed in the preceding work: 10 assets, 9 retrigger, 4 presets.
  These are not native-camera playback tests.
- CC0 Canon 5D-family and Nikon D850 recordings downloaded with pinned hashes;
  source credits in [SOURCES.md](../shutter_sound/SOURCES.md). Exact 5D generation
  is uncertain. Both have 60 ms burst edits and longer single-shot edits.
- Ciallo (~908 ms) and Man (~547 ms) converted without discarding their tails.
  Originals remain local and ignored, without assumed redistribution rights.
- Offline 10/20 fps previews and exact restart-prefix checks generated for all
  six variants in `work/shutter-sound/presets/`; `validation.json` records results.
- Static stock/r5 audit and E143-to-E147 audio mapping produced. Corrected E147
  sound globals and NAND index location are in `layout.json` and the plan.

## Native playback investigation: incomplete

`shutter_sound/emulator/probe.mjs` is an isolated host-initiated E147 experiment.
It changes model facts and hooks only inside its process, not external sources
or camera firmware. Native AUD_MAIN (83), AUD_COPY_DATA and AUD_WATCH_DOG start;
CPU-2 wake-up/monitor use existing emulator stand-ins. Player open, volume and
short-sound WAV parsing were reached. No native PCM playback pass exists.

The latest failed trace reaches codec SPI configuration/transfer, deeper than the
previously suspected power/GPIO wait. Disassembly indicates E147 codec channel
**13**, while the upstream E143 CodecLink models channel **14**. A process-local
channel-13 adaptation was added, but its validity has not been established.

**Critical probe defect found immediately before pausing:** `MenuLab.observe()`
in external `emu/src/lab/menu.mjs` replaces an existing hook. Diagnostic observers
in our probe therefore overwrite both the newly wrapped SIO codec hooks and the
existing `sync_send` emulation. The failed transfer trace is contaminated by this
instrumentation. It does not prove a camera defect or an emulator hardware gap.
On resuming audio, replace diagnostic observers with a helper that wraps an
existing runtime-address hook, otherwise observes the unhooked native function.
Preserve the previous hook and rerun before changing transport behavior. Do not
bypass the wait or patch the camera based on this trace.

After fixing instrumentation: prove three native play/end/close cycles, then
100 cycles with exact PCM and clean ownership; verify native stop/restart,
automatic completion, stale callbacks and long clips. Sequential explicit
end/close alone cannot establish retrigger behavior.

Still absent: camera sound loader/preload allocation, native worker, accepted-shot
hook, electronic-mode gates, actual menu controls, persisted preference, firmware
overlay builder and installable package. Audio probe and bank files cannot be
used as a camera update.

## Baselines and dependencies

- Stock E147 main SHA256:
  `5e8d376e9111a44ac0352f26030d7c1b17026d42c45f3600cfa02a0e8c5b7d59`.
- Accepted five-r5 main (`work/current-games/row-main.bin`) SHA256:
  `a3b5e0aa720f3703f6d3adcf771edb855ac99d63c24c116816976ff37c203ed8`.
- Caduceus v0.26.2 commit: `f4d2569eb46817795ec5ffaf931ba058d2c0d029`.
- External OM-Emu commit: `88b753ddb9c0fac35366802133e849600aa519d5`.
  Existing Windows edits in `bin/debug.mjs`, `bin/modelcheck.mjs`, `bin/run.mjs`,
  `checks/lib/env.mjs`, `host/blobs.mjs` predate this feature; preserve them.
- Game extension uses 232/256 KiB, with 16 KiB required reserve, leaving ~8 KiB
  for additions under that policy. Remaining erased segment-1 bytes
  `[0x2fdfd0,0x335fe0)` are a candidate only; loader residency/ownership unproved.
- Main code notation is `0x50000000 + body offset`; runtime is
  `0x60021020 + body offset`. Flash-library mapping differs.

Resume commands and source descriptions are in the
[audio README](../shutter_sound/README.md). No new audio runs were made while
recording this pause.
