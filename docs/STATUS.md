# Firmware status

## Current Games and ES sound trial

**OM-3 1.1, E147.** Current trial main `39c9f50f7c3a5a3f195d7b8f83f5372513a7eb7919efd67c133318ab24854738`.
Games return to the COLOR 1–4 Picture Mode launcher
with the r5 game and touch code. While the launcher or a game owns the
screen, the through-image display path skips new preview submissions. It
resumes on exit. The owner confirmed good game play and live-view pause on
image `23a591b4d8d3`. Sensor and ISP activity and power savings remain unmeasured.

**ES sound** is a native text row under **MENU → Setup → Information Record**.
Select Silent, 5D, D850, Ciallo, Man or Custom. Capture notifications from the
E147 buffer manager trigger playback in Silent Single and Silent Sequential.
While custom audio is active, UI_OUT checks native transmitter ownership on
shot events and a 32 ms timed wait. Once the transmitter releases its object,
the worker closes the owned player through the native audio teardown. A new
shot can rewind the PCM cursor. Supported bursts can coalesce sound requests.
The game section loads 232 KiB. The sound section adds 216 KiB for embedded
clips, code and one SD WAV buffer.

OM-Emu fixtures exercise both native capture call sites. Three consecutive
5D singles played the complete clip and released the player. A three-shot
Silent Sequential replay restarted Ciallo twice and played the last clip to
completion. Custom played 48,000 frames. Mechanical Single and the Silent
choice emitted zero added audio. The new replay also drops the first clip's
TX-done notification and checks that subsequent shots remain audible.

On the preceding `23a591b4d8d3` image, the owner heard ES sound on the first
shot or burst after boot, followed by standard silent playback. The menu
still showed the selected sound. Repeated playback on the current image
requires a camera check.

[Install and use Games and ES sound](../shutter_sound/TRIAL_NATIVE.md) ·
[Sound file requirements](../shutter_sound/SOUND_FILES.md) ·
[Build and test](DEVELOPMENT.md)

The Setup Games trial was withdrawn after the camera owner reported disturbing
refresh during play. [Retired trial record](history/SETUP_GAMES_TRIAL.md)

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
