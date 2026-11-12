**Status update:** [r2 on-camera validation passed](ON_CAMERA_VALIDATION_R2.md), as confirmed by the user after installation. Earlier pending-retest statements below describe the pre-confirmation state. Long-session and instrumented hardware checks remain unverified.

# Revision r2 hardware update

The user reports the previous four-game release mostly worked, but Breakout
froze on entry and touch failed. r2 removes all game touch code and uses buttons
only. The entry-freeze cause is unproven; r2 requires a short hardware retest.
The Games footer is now a padded bitmap below the board. No optional films ship.

The following review describes the previous release; its touch refinement and
no-physical-camera statements are historical. Flash interruption, graphics
buffer timing, heat and queued-tick risks remain applicable.

# Hardware risk review — four-game bundle

Reviewed 2026-11-12. **The serious risk is installing modified firmware.**
There is no identified game-specific mechanism that directly damages the
sensor, shutter or lens, but code review and an emulator cannot establish
hardware safety or assign a reliable failure probability. No physical camera
has been used. This is an experimental build, not a hardware-qualified release.

| Risk | What reduces it / what remains |
| --- | --- |
| Interrupted or incompatible flash can prevent boot | Standard OM-3 1.1 only; full battery; exact pinned stock/base hashes; all container component checksums; decoded packaged main equals the tested image. Separate, hash-verified original firmware is included. Do not interrupt writing. Restore still requires a working updater. |
| GUI overload during a dense drag | **Refined:** touch updates state without rendering. The existing 120 ms timer draws the latest paddle position; a 34-message gesture burst is checked against timer-only redraw counts. End-screen touches do not restart gestures or redraw. Added visual wait is at most one scheduled tick, plus processing/display delay. |
| Battery drain and heat during play | Puzzle games have no animation timer; action games target 8.3 ticks/s and stop on tested exits and endings. No new overclock, voltage, thermal-limit, sensor or lens-control code is introduced by the games. Nevertheless they run in the camera's Picture Mode environment, not a proven low-power mode. Its inactivity timeout is suppressed; sleep, thermal response and actual power use remain unmeasured. Use short sessions and exit when finished. |
| Memory corruption or graphics timing can freeze the camera | Fixed buffers, worst-case output bounds, 16 KiB extension reserve, pixel comparisons and end sentinels are checked. GUI task owns game/render state; no touch pointer is retained; old-session ticks are ignored. Asynchronous graphics-buffer lifetime is still hardware-unverified; bounds tests cannot prove DMA timing. |
| Slow hardware queues / delayed exit | MENU, shutter and display exits, timer cancellation and stale callbacks pass native GUI replay. There is no pending-tick coalescing; a body unable to service the 120 ms cadence could accumulate work. Actual responsiveness, power-switch/low-battery/sleep paths and simultaneous input require physical checks. |
| Effects outside Games | This includes the pinned Caduceus firmware features, not just four applications loaded from SD. Mismatched GUIDES/LABELS/TONES are avoided by shipping and checking the matching set. Normal shooting, storage and long-duration stability still need a real body; photo/settings backups remain necessary. |

Game rounds do not persist scores or write firmware. Flashing occurs only through
the installation/update process; the full Caduceus baseline has its own settings
storage behavior. This review is not a claim that the complete mod performs no
card writes or has received a full firmware audit.

Validation covers native game rules, bounded rendering, complete Mario traversal,
an input-driven 18-brick Breakout clear, cross-game navigation and tested exit
paths. Real touch delivery is specifically unproven: E147's physical controller
is disabled in OM-Emu, so tests inject at the firmware's SEND_EVENT boundary.
Instruction counts (Mario up to 305,733; Breakout up to 159,637 per sampled draw)
are **not** millisecond measurements on the camera.

The useful remaining gate is a short, supervised hardware trial: verify normal
photography and exit responsiveness, then touch tracking/frame pace, then warmth
and battery behavior. Stop using the mod if exits become unreliable or the body
gets unusually hot. Do not disable thermal protection or alter touch-controller
initialization to compensate for emulator limitations. Larger changes to timer
concurrency or display buffering should follow measured evidence.

Rollback details: [INSTALL_AND_RESTORE.md](INSTALL_AND_RESTORE.md). The
[upstream install guide](https://github.com/androidfanman/caduceus-om3/blob/main/docs/INSTALL.md)
documents the SD updater and stock restore; the [OM-3 manual](https://learning.omsystem.com/OM-3/zz_html_manual/en/error_codes_308.html)
describes high-temperature warnings and cooling. Neither source qualifies this
game build as safe or guarantees recovery after a failed flash.
