**Status update:** [r2 on-camera validation passed](ON_CAMERA_VALIDATION_R2.md), as confirmed by the user after installation. Earlier pending-retest statements below describe the pre-confirmation state. Long-session and instrumented hardware checks remain unverified.

# Future camera-game development

## Current baseline

Four-game r2: 2048, Minesweeper, Mini Mario, button-only Breakout. User hardware
feedback on r1: mostly works; touch failed; entering Breakout froze the body.
r2 removes touch parsing/interception entirely. Do not call that freeze fixed
until the user confirms entry, play and exit on hardware. Preserve the r1
archive as historical evidence, not the recommended installation.

## Keep development small

- Start from native/bundle/games.json and the combined builder. One camera
  update holds all games; standalone historical builders are not the baseline.
- Fixed memory and bounded rendering; retain the 240 KiB target and 16 KiB
  reserve. Shared Mario/Breakout buffers belong only to the active game.
- Use physical buttons first. Picture Mode does not deliver the old held-OK
  event reliably; INFO restarts 2048. Mario latches short jump presses.
- No touch experiments without a separate hardware probe. Emulator SEND_EVENT
  injection does not emulate the E147 controller. Stock touch can close Games;
  r2 passes it through and tests timer cleanup.
- Keep GUI state/rendering on the GUI task, cancel timers on exits and endings,
  and reject stale epochs. Slow-frame queue growth and DMA lifetime remain
  hardware questions; avoid increasing frame rate without measurements.
- Shared UI changes need screenshots of the unopened Games row, launcher and
  all games. The footer uses an empty custom stock string plus a 120x32 bitmap
  at (390,554), with padded glyphs. Do not alter stock camera strings/fonts.

## Check and release

Run py -3 native/bundle/build.py. Reports must match the exact raw-image hash;
verify-existing is only for already-completed matching tests. The label test
compares six view crops and checks glyph padding. Breakout tests include a
button-only full clear, real GUI button play, ignored game-touch actions,
stock touch exit, restart, endings, shutter/display/MENU and stale callbacks.

Use a new package_name per release; never overwrite an earlier archive.
package.py checks stock/base hashes, all container checksums, exact decoded
main image, and ZIP readback. Ship matching GUIDES/LABELS/TONES, no optional
film presets, and separate exact stock restore bytes. Both install and restore
use E1479999.BIN: never confuse their source folders.

Record user hardware results separately from emulator results. First retest:
open Breakout without touching the display, use Left/Right, serve with OK,
exit with MENU and shutter, then confirm ordinary photography. If entry still
freezes, capture the exact sequence and compare with Mario before changing
shared timer or rendering code. Do not keep reflashing speculative changes.
