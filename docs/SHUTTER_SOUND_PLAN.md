# Electronic shutter sound after the OM-3 menu migration

This records the research leading to the earlier full-menu sound trials.
See the current [install guide](../shutter_sound/TRIAL_NATIVE.md) and
[file requirements](../shutter_sound/SOUND_FILES.md) for the capture-driven build.

Use the E147 firmware 1.1 **Extras camera trial** as the integration baseline.
The first audible milestone is one accepted electronic single shot playing one short
5D click while photography proceeds normally. The first engineering experiment
can run entirely on the PC. Native playback, the per-exposure notification and
memory ownership are three independent questions. Each has a decision below.

The native E147 prototype now restarts long samples inside its copied audio
stream at simulated 10 and 20 fps. The separate 32 KiB section-1 probe also
played the complete 5D WAV from the loader's uncached address in OM-Emu.
The Silent Single trial now connects the menu to the native player using
the application's `START_EXPOSE` notice. The stock SCP confirmed drive
value 30 as Silent Single. An emulated exposure in that mode played the
selected D850 clip. This first trial uses the two 60 ms professional clips
in a 24 KiB section-1 extension. The camera still needs a physical test.
[Implemented experiments and commands](../shutter_sound/README.md)

## Starting point

- **Menu.** MENU → Setup (wrench) → page 2, Information Record → Extras → Shutter sound
  already offers **Silent, 5D, D850, Ciallo, Man**. OK commits `sound_choice` to session RAM.
  MENU cancels. The separate Silent Single build wires the 5D and D850
  choices into preview and exposure playback. The shooting side works after
  Extras closes in the emulator. [Menu implementation](../menu_extension/menu_host.s)
- **Games.** The trial main is `2912d4c11c58ed2056b33dd5fd14f89a2b37df4d43ba2caab95ed28bdc057fea`.
  Its four emulator reports passed. The touch suite had 181 replies and 181
  returned waits, including 64 flaps for 64 taps. The three timed games advanced
  with live view stopped. The earlier r5 host has the user's camera acceptance.
  Physical acceptance of the new menu host is still open. [Game trial](../menu_extension/README.md)
- **Assets.** Six validated one-slot banks cover four audible menu choices.
  Single-shot edits are about 164 ms for 5D and 300 ms for D850. Both burst edits
  are 60 ms. Ciallo and Man keep their full tails, about 908 ms and 547 ms.
  The 23 host tests passed again when preparing this plan. They exercise file
  handling, presets and restart policy. [Audio tools](../shutter_sound/README.md) · [Sample provenance](../shutter_sound/SOURCES.md)

## Implementation decisions

| Unresolved question | First experiment and evidence to collect | Direction if it fails |
| --- | --- | --- |
| Can the native OM-3 audio player emit and finish a clip? | The corrected channel-13 probe passed 100 play/end/close cycles. A separate run passed with OM-Emu's AF-key control. | Wire the worker to native completion and preserve player ownership across menu exit and cooldown. |
| Can the speaker restart before the clip ends? | The direct stop waited for the full clip. The copied stop timed out under OM-Emu. The native renderer replaced sample cursors inside the copied stream and emitted the expected prefixes at 10 and 20 fps. | Bound stream duration and idle shutdown. Test rollover and movie/AF priority. A short 5D direct play makes a smaller single-shot pilot. |
| Which event means an electronic exposure was actually accepted? | Count an application exposure notification against the ordinary and fast capture candidates. Put an exposure ID or sequence alongside the mode and timestamps. Compare single shots, bursts, half-presses, blocked releases and cancellations. Require exactly one eligible notification per accepted frame. | Prefer a verified application notification if it handles both drive paths. If it represents a whole burst, evaluate a capture callback per drive path and choose one owner per frame. If the emulator substitutes the capture path, exercise the real callback and continuation in isolation, then verify event count and exposure-to-sound timing on the body. Keep unverified modes silent. |
| Where will code and samples fit? | The Extras image uses **244,044 bytes** in a **245,760-byte** rounded load. The renderer fits in its **1,716 bytes** of loaded padding. The first **32 KiB** of another section passed a native loader request with emulated NAND and playback from the uncached alias. | Keep the selected bank in owned, aligned RAM and the library on SD. The generic allocator caps requests at **16,448 bytes**. Verify a larger allocation or a bounded block pool. Check ownership and pressure during capture before expanding the static copy or reserving blocks. |
| Can bursts keep time without delaying capture? | Use the latest generation each period and skip superseded requests. The emulator showed **30–32 ms** of buffering. Measure capture cadence against Silent and check the attacks and final tail on the body. | Keep the professional burst edits and prioritize shot timing if a fast drive overwhelms playback. Drop stale requests. Keep each ordinary electronic single audible. |

OM-Emu substitutes parts of capture and synthesizes the mechanical shutter.
The exact Extras capture replay saw one simulated release with zero hits at
either CapBuf candidate. The playback traces count only native PCM.
[Audio checkpoint](SHUTTER_SOUND_CHECKPOINT.md) · [Probe](../shutter_sound/emulator/probe.mjs)

On E147 the ordinary CapBuf candidate is the native list append at
`0x60bbe8c0`. A direct fixture inserted two buffers and verified both links.
Four native call sites use it, including one from `entryEDIT_DOING`. The
fast candidate at `0x60bc1f9a` is `entryMAIN_TAKED_PIC`. Its callers include
`rcvADD_TAKED_PIC_InMAIN_FREE` and `rcvEDIT_DONE_InMAIN_PREPARES_EDIT`. The
next trigger candidate is the `ADD_TAKED_PIC` notice on the electronic still
path. Measure its timing and keep edit transitions from issuing a request.
The source addresses above use E147 runtime notation. These checks follow the
[OM-Emu analysis of DB's capture hooks](https://github.com/flatpanda/om-emu/blob/88b753ddb9c0fac35366802133e849600aa519d5/analysis/om-c-firmware/README.md).

## Integration sequence

1. **Playback on the PC.** Direct playback suits the initial 5D single.
   The copied renderer avoids a stop request for each frame. Connect real
   worker completion to each route and test shutdown before on-body integration.
2. **Read-only capture and memory verification in parallel.** Use the trial hash
   above for the conflict audit. The seven recorded audio/capture function
   prefixes still match in that image. Verify full instructions, callers and
   task context at the chosen site. Prove a RAM allocation survives menu exit
   and remains accessible until audio releases it. An erased range and a host
   test allocation each leave that question open.
3. **First camera candidate.** Use the existing **5D** choice, one preloaded
   short edit and ordinary electronic singles. On an accepted frame the capture
   path publishes a bounded request and immediately continues. The audio worker
   owns start, stop and cleanup. Keep the capture path free of waits, SD reads,
   allocation and audio calls. Give movie recording, AF audio and playback
   priority. Check the native sound-permission setting on E147. OM SYSTEM
   documents a separate sound permission in Silent Settings. [OM-3 manual](https://learning.omsystem.com/OM-3/zz_html_manual/en/silent_settings_114.html)
4. **Complete the chooser.** Keep stable IDs for the five labels. Load on OK or
   a verified post-startup idle event. Preloading both professional variants of
   the selected preset would take 43,316 bytes of bank files for 5D or 69,440 for
   D850. The largest supplied single bank is Ciallo at 174,484 bytes. These are
   file sizes. All six files total 392,448 bytes on SD. Measure transport,
   parser and DMA memory separately. Use a single published
   generation for each validated preload. On missing or corrupt media, make
   Silent effective and report the unavailable preset in Extras. For persistence,
   prefer an existing verified extension-settings service. Otherwise use a small
   versioned preference file with recoverable writes and an invalid-data default
   of Silent. Recheck after power cycling and swapping cards.
5. **Enable burst modes individually.** Each accepted shot publishes a new
   generation. The next renderable period starts the latest clip at frame
   zero. The native copy task replaces the remaining old tail beyond its
   already buffered periods. It may skip intervening requests. Silent clears
   pending work and renders silence through the owned stream. Mode changes,
   sleep and power-off revoke outstanding work. Free samples once ownership
   returns. On a missing acknowledgement, disable custom playback for the
   session and preserve the buffer. Keep Pro Capture
   prebuffering and computational sequences silent until their trigger policies
   are separately verified. [Executable retrigger reference](../shutter_sound/retrigger.py)

## Camera acceptance

Compare the menu-only trial, audio build with Silent, and the same build with
sound enabled using matched lens, exposure, card and drive settings. Start
with singles. Check that half-press, canceled exposure, mechanical shutter,
electronic first curtain and movie recording produce zero added clicks.
Use an independent exposure-time reference and a microphone to measure
exposure-to-sound delay and its spread. Compare shot count, saved files and
inter-frame intervals. At each proposed burst rate, measure how closely the
audio follows the burst and check for stale attacks after it ends. Missed
attacks are acceptable in continuous drive. Capture timing and saved frames
have priority.

Keep the audio worker dormant under Silent and release its audio resources
when playback ends. Check idle battery draw, movie audio, sleep/wake, return
to shooting and card changes. Re-run the exact-image Extras, game timer, touch
reply and outside-game tests. Package an audio trial separately with a verified
stock restore. The current Extras archive is the menu-only control for this
comparison. [Trial instructions](../menu_extension/TRIAL.md)

## Earlier research and references

| Evidence | What it establishes | Limit |
| --- | --- | --- |
| [Official OM-3 Silent Settings](https://learning.omsystem.com/OM-3/zz_html_manual/en/silent_settings_114.html) | Electronic shutter operation is normally silent; sound permission can be configured. | It does not document importing custom shutter sounds. |
| [DB firmware releases](https://github.com/azqeurio/om-c-firmware/releases) | Electronic shutter audio is an existing community feature; older releases explicitly report OM-1 success. The November 17 investigation examined dbv0.4.1. | The inspected reports do not establish successful playback on this OM-3 baseline. |
| [OM-Emu study of DB firmware](https://github.com/flatpanda/om-emu/blob/88b753ddb9c0fac35366802133e849600aa519d5/analysis/om-c-firmware/README.md) | A useful reference design: capture hooks, custom sound IDs, native WAV playback and additional controls. | Its detailed implementation study concerns version 0.3.2 and primarily E143. |
| Local `work/shutter-sound-research/` | Cross-build mapping scripts, 99 sound-related label candidates, a patch-overlay probe and prior session notes. | Several address and test-coverage claims need the corrections below. |
| [Current repository status](STATUS.md) and [development workflow](DEVELOPMENT.md) | A camera-tested r5 baseline, assembly tools, image verification and packaging already exist. | Audio adds new hardware and task-lifecycle behavior. |

Use the DB project as an implementation reference. Its inspected repository has
no license granting code or asset reuse. Write this implementation independently,
using documented firmware facts and original or appropriately licensed audio.
The [existing collaboration issue](https://github.com/azqeurio/om-c-firmware/issues/10)
also identifies the license and combined-firmware questions. The
[OM-5 reboot report](https://github.com/azqeurio/om-c-firmware/issues/9) makes
model-specific verification particularly important; it is not evidence of an
OM-3 failure.

### Address and emulator caveats from the r5 audit

The following were checked against the local firmware and source during planning.
Preserve the earlier research as history; carry these corrections into the new
address manifest and tests.

1. **Code notation differs from execution addresses.** The mapping scripts print
   `0x50000000 + main-block offset`, OM-Emu's disassembly notation. For the main
   code copy here, execution addresses are `0x60021020 + offset`. For example,
   the play function at notation `0x50b6e825` corresponds to `0x60b8f845` in the
   main runtime copy. A flash-library address has separate placement rules.
   Every proposed hook must record its block offset, notation, runtime address
   and loader segment explicitly.
2. **Audio globals move between models.** Direct E147 disassembly shows the
   sound-index pointer at `0xa32da42c`, with its owning allocation at
   `0xa32da428`; the WAV pointer and length are `0xa32da344` and `0xa32da348`.
   The earlier notes incorrectly retained E143's `0xa32db180`,
   `0xa32db098` and `0xa32db09c`. Re-derive all remaining globals, queue IDs,
   flags and task parameters individually.
3. **The OM-3 sound index is at NAND `0x4e3e0000`.** E147's loader at notation
   `0x501b5a59` reads that address. The old note's `0x4e420000` comes from E143;
   finding it in a flash guard does not identify E147's sound index. The design
   needs no writes to the factory sound area.
4. **An S2 emulator session does not prove the capture hook ran.** OM-Emu's
   `S-RELSEQ` substitutes for capture work and bypasses the CapBuf locations
   discussed in the reference design. `S-SHUTTERSND` also generates host-side
   clicks. Require trace hits at the actual hook and PCM with source `native`;
   synthetic clicks and host-injected calls are separate evidence.
5. **E147 native audio is a development dependency.** The inspected checkout
   supplies `MODELS.audio` for E143, with audio initialization and CPU-2 stand-ins.
   E147 needs its own verified facts and resource setup. The play-function entry
   probe ends before complete playback. The sentinel probe patches and reads an
   in-memory block; it does not execute the marker or prove loader residency.
6. **Erased bytes are not automatically usable memory.** The stock segment-1
   candidate contains 1,710 non-`0xff` bytes in r5. Its remaining contiguous erased
   run is body offsets `[0x2fdfd0, 0x335fe0)`, 229,392 bytes, corresponding to
   runtime `[0x6031eff0, 0x60357000)`. This is a candidate allocation only: prove
   loader coverage, ownership and lifetime before placing anything there.

The native-audio and capture limitations are documented in the local checkout's
`emu/FIDELITY-NOTES.md`, `emu/src/lab/audiohw.mjs`,
`emu/src/lab/shuttersnd.mjs` and
[OM-Emu audio notes](https://github.com/flatpanda/om-emu/blob/88b753ddb9c0fac35366802133e849600aa519d5/docs/hle-gaps.md).
