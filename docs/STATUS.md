# Firmware status

## Current Extras and SD sound trial

**OM-3 1.1, E147.** The current image is
`8db210d58a601d6546a26d635587ef2d288069f0e13af1d755ca16b47f50af72`.
Games and Shutter sound open from **MENU → Setup → Information Record →
Extras**. In OM-Emu, entry requested stock live-view stop. All five games,
181 touch replies and returned waits, and outside-game parity passed.

The SD replay played the complete Ciallo and Man samples, rejected missing,
truncated and oversized WAVs, and played a 48,000-frame Custom clip on a
Silent Single exposure. Half-press, ordinary Single, and the Silent
selection produced zero added PCM. The linked game section still loads
240 KiB. The SD-sound build adds 216 KiB to section 1 for WAVs, code, and
one selected clip buffer. The native loader test supplied NAND reads
through OM-Emu. Physical boot, touch and speaker playback on this image
still require testing. Burst playback remains outside this trial.

[Install and use Extras](../shutter_sound/TRIAL_SD.md) ·
[Sound file requirements](../shutter_sound/SOUND_FILES.md) ·
[Build and test](DEVELOPMENT.md)

## Camera-tested Picture Mode baseline

Accepted release: **five-r5**, five games with Flappy touch, terminal-event
cleanup, variable pipe spacing and live distance. On 2026-11-16 the user reported
the real-camera test was perfect. No event trace or endurance duration was supplied.

Raw SHA256: `a3b5e0aa720f3703f6d3adcf771edb855ac99d63c24c116816976ff37c203ed8`.
Loaded extension: 232 KiB / 256 KiB; margin 24 KiB.

Local r5 evidence: 181 native touch events/replies/returned waits, 1,750 physics
cases, 26 render frames, seven GUI scenarios, 17 playability streams of 3,000
ticks, and 14 outside-game snapshots. The reorganized build must preserve the
raw hash; current reports live in `work/current-games`.

Only Flappy owns touch. Other games retain stock touch, which can leave Games.
Lift the finger before MENU. E147 controller emulation, touch recovery after
LCD/EVF switching, sustained stability and earlier rare R2 freezes remain open.
See [hardware review](HARDWARE_RISK_REVIEW.md).

r3 is withdrawn for a missing touch reply/deadlock. r4 repaired the reply but
missed over half of normal taps. r5 clears contact on release/tap/double-tap
endings (3/4/5). Preserve accepted packages and stock rollback unchanged.
