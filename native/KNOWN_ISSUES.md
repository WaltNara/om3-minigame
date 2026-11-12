**Status update:** [r2 on-camera validation passed](ON_CAMERA_VALIDATION_R2.md), as confirmed by the user after installation. Earlier pending-retest statements below describe the pre-confirmation state. Long-session and instrumented hardware checks remain unverified.

# Known issues and resolved input changes

Evidence is from OM-Emu on OM-3 firmware 1.1 / E147 with Caduceus v0.26.2.
Physical-camera validation is still outstanding.

## 2048 restart: resolved by using INFO

**The current combined development build uses INFO to start a new round.**
The user approved replacing long press with another control. Both the normal
and game-over HUD advertise INFO. Short OK and held OK leave the board alone;
there is no new timer or input hook for 2048.

The old Games build advertised `HOLD OK NEW`, but Picture Mode delivers only
OK press/release (`0x900c` / `0x900d`), not the held event (`0x903e`). A probe
recorded zero held events; `work/separate-games/controltrace.json` confirms
the same behavior. The original HSL-wheel build uses a different input owner
and does receive the held event. Its historic controls are unchanged.

`build_combined.py` removes the obsolete held-OK branch from generated 2048
code and corrects both HUD hints. `combined_host.s` handles INFO. The combined
Minesweeper/cross-game replay checks INFO after a live, lost and won 2048 round:
score, move count and flags reset, with exactly two starting tiles. End-state
cases inject their flags and counters; restart itself uses real key events.
Older archives are historical builds. The four-game
`om3-games-bundle-experimental` package includes this correction.

## Remaining hardware checks

- LCD/EVF switching while Games is open leaves the stock Picture Mode screen.
  The untouched Caduceus baseline follows the same GUI trajectory. Physical
  live-view re-entry still needs checking.
- OM-Emu has no live-view scene in these replays. Full shutter is handled in
  shooting state `0x0108`, but an actual photograph is not captured.
- Rendering latency, real button feel, concurrent input and graphics-buffer
  lifetime need a camera. Mario keeps its 120ms target; native instruction
  counts are not hardware frame-time measurements.

## Breakout entry freeze reported on hardware

The previous release froze when entering Breakout; touch also failed. r2 removes
all game touch interception, payload access and gesture code. The cause of the
entry freeze is not established, so this is not yet a hardware-confirmed fix.
Controls are now held Left/Right, OK and INFO. See BREAKOUT_STATUS.md.
