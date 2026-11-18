# Firmware status

## Current Games and ES sound build

**OM-3 1.1, E147 build 1100.** The camera owner confirmed testing the latest
combined image on a real OM-3. Raw SHA-256
`8bf67c77473aafecd0f6f7ef07d4e31e8aaa8a737f26ec1f87a79a6936533afa`.
The owner did not report a test duration or per-mode results for this build.

The five games open via **COLOR 1–4 → Picture Mode → Games**. The display
skips new live-view submissions while the launcher or a game is open and
resumes on exit. The owner also confirmed the pause and game controls on the
earlier `23a591b4d8d3` build. Sensor and ISP activity and power savings remain
unmeasured.

**ES sound** is under **MENU → Setup → Information Record**. Silent Single and
Silent Sequential support the built-in 5D and D850 sounds and the Ciallo, Man
and Custom WAV files. Silent is the startup default. The game section loads
232 KiB. The sound section adds 216 KiB for code, clips and one SD WAV buffer.

### Emulator results for the exact image

- Both native capture hooks ran. Repeated 5D singles matched the clip and
  a three-shot Silent Sequential replay restarted Ciallo twice and played
  the last clip to completion. Custom played 48,000 frames. Mechanical
  Single and the Silent setting emitted zero added audio.
- All 23 audio requests supplied fresh volume values, with 23 opens,
  23 closes and 25 idle-state checks. Playback recovered after an injected
  lost transmitter notification and a rejected registration.
- The launcher, live-view pause and resume, Flappy touch replies, and
  behavior outside the games passed the combined-image replay.

The camera readout for the old first-shot-only failure showed all four shots
opening and closing their players. The native volume command mutates the
values in place, so reusing that record reduced 100 to 10, then 1, then 0.
The combined build refills the record before each new playback.
[First-shot diagnosis](../shutter_sound/ES_STATUS.md)

[Install and use Games and ES sound](../shutter_sound/INSTALL.md) ·
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
