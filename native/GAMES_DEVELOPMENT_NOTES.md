# Games development notes

The separate Games build runs 2048 from Picture Mode's Games row. Its current
entry, controls, validation and limitations are in [SEPARATE_GAMES_STATUS.md](SEPARATE_GAMES_STATUS.md).
Keep the existing experimental package and its tested image when developing a
new candidate; build and validate changes in a separate output directory.

## What worked

- **Menu entry:** the COLOR1–4 Picture Mode list, item table and nine row
  switches all need a consistent new entry. `probe_games_row.py` checks the
  baseline bytes, extends those tables and chains Caduceus's existing hooks.
  The Games row must consume its own controls rather than let the template
  photo-adjustment row handle them.
- **Painting:** simply posting a paint message did not repaint the panel: the
  area also had to be marked dirty. The build captures a live Picture Mode GUI
  root from a native paint message, validates its invalidate method and target,
  and requests an update through that root. It draws inside the camera's paint
  bracket before submission. Discard the captured root on leaving the row,
  changing screens or switching display output.
- **Input:** the GUI reads and clears dial counters before Picture Mode receives
  the dial event. The build records the nonzero native result for that event;
  reading the counters a second time gives zero. Consume key releases as well
  as presses when Games owns them. Picture Mode's inactivity timeout otherwise
  exits a game in progress.
- **Larger board:** the 384 × 480 renderer keeps prepacked RLE rows and a
  bounded buffer rather than a full framebuffer. Runs must stay within each
  scanline. Derive capacity from the worst row shapes when changing fonts,
  tile sizes or artwork; do not assume puzzle compression will suit sprites.
- **Assembly calls:** check whether the target constructs its own frame before
  choosing `CALL` or `CALLS`, and match its actual return frame. A 108-byte
  call to the bitmap routine faulted; its saved frame is 96 bytes. Preserve
  MDR where nested calls cross a `CALLS` return path.

## Before adding another game

Keep game rules, launcher state and presentation separate. TinyMario is the
next candidate, after this 2048 build has been validated further. It needs a
timed update, held/simultaneous controls and a moving-image renderer; none is
established by the event-driven 2048 replay. First demonstrate a moving
marker, reliable pause/exit and bounded rendering before porting a full game.

The native `EXEC_END` path waits on an OSD completion event, but OM-Emu
completes drawing synchronously. Physical-camera testing is still needed for
buffer lifetime, responsiveness and LCD/EVF behavior. The current emulator
switch test confirms Games state and its drawing pointer are cleared; it does
not establish a normal return to shooting after switching outputs.

## Mini Mario handoff (2026-11-11)

**The timer-to-GUI blocker is resolved in OM-Emu.** The separate build now
contains 2048 and an original single-screen platform course (not a TinyMario
source port). The course has a pixel character, one platform, a gap, a goal,
win/loss messages and restart. The 120 ms simulation tick gives a deliberate
pace. Left/Right hold to walk; Up or OK jumps; INFO restarts; MENU returns to
the launcher (re-entry starts a new run). Shutter/display transitions exit.

Build: `py -3 native/build_mario.py`. Output: `work/mario-game/row-main.bin`.
Validate: `py -3 native/test_mario_game.py`. The exact current image passed
launcher, held movement, simultaneous jump, winning, falling, restart, MENU,
2048 movement, shutter exit and display-switch cleanup. See
`work/mario-game/validation.json`, `play.json`, `display.json` and screenshots.
Main SHA-256: `efcb798106a99f192475a02d43038e1dc494f002bf77450dc888b2a7e1db5dba`.
Core and renderer tests also passed (`test_mario_core.py`, `test_mario_render.py`).

### Implementation and lessons

- `mario_bridge.s`: native software timer -> native deferred task -> GUI queue.
  The callback carries only a session generation, never a screen pointer.
  The GUI receive hook consumes our private `0x7ffe` event, ignores stale
  generations, advances physics, paints and invalidates the live root.
  Timer deletion and generation changes handle leaving/restarting; win/loss
  also stops the timer. This is emulator evidence, not a proof of all hardware
  concurrency behavior.
- OM-3 runtime addresses: timer create/delete `0x6007662a`/`0x60076665`,
  defer `0x600755ce`, queue post `0x610f48ef`, GUI receive `0x610fd05c`.
  The model-specific mapping in OM-Emu `ports.mjs` matters: OM-1 documentation
  addresses cannot be used unchanged. Each native CALL needs its correct
  frame and a free caller stack slot; preserve MDR across CALLS callbacks.
- `games_transition` receives zero during ordinary input too. Only stop on
  a nonzero transition, otherwise the game timer is cancelled immediately.
- `mario_host.s`/`mario_menu.s`/`mario_launcher_assets.py` integrate the launcher;
  `mario_core.s` owns rules; `mario_render.s`/`mario_assets.py` own graphics.
  Prepacked rows use a three-pixel movement grid to fit the extension space.
  The combined linked extension is 202,212 bytes, below the 256 KiB limit.
- Existing `work/separate-games` and the published 2048 package are untouched.

### Remaining work for a cheaper model

1. Package this exact validated image under a NEW artifact name, using
   `package_games.py` as a format/checksum reference. Use the Mario validation
   report and current source hashes; include generated `mario_assets.inc`,
   launcher assets and evidence. Do not overwrite the existing 2048 package.
2. Update the short package README and stale source comments (e.g. the copied
   menu comment still describes two choices). Further course/art polish is
   optional; it is deliberately only a small original platform course.
3. Physical-camera testing remains separate: animation timing, simultaneous
   buttons, buffer lifetime and normal shooting after LCD/EVF switches are
   not established by the emulator. Do not label the package hardware-tested.

No more reverse engineering of the timer/GUI handoff is needed to package the
current prototype. No installable Mario package has been created yet.

Low-cost ideas for making the course feel closer to the original, without a
large increase in per-frame work, are collected separately in
[MARIO_ENRICHMENT_IDEAS.md](MARIO_ENRICHMENT_IDEAS.md). They are suggestions
only; no Mario source file has been changed.

## Separate Minesweeper branch (2026-11-12)

A second, simpler game was requested in place of further Mario work. See
[MINES_STATUS.md](MINES_STATUS.md) for controls, limits and validation.

`build_mines.py` builds an isolated emulator-only image in `work/mines-game`
containing 2048 and an 8x8 Minesweeper. It copies the proven Games-row
patching and prepacked-RLE renderer, but installs **no periodic timer and no
GUI queue hook**, because Minesweeper is entirely event driven. The launcher
has three entries (2048, MINESWEEPER, Back).

This branch does not modify any Mario source file, the published 2048 Games
package, or the HSL-based 2048 package. Mario remains exactly as described in
the handoff above, including its outstanding packaging and hardware-testing
work. Keep the two branches separate: `work/mario-game` and
`work/mines-game` have independent images, validation reports and hashes.

All three emulator layers pass for the Minesweeper image: 20 native rule
cases, three decoded render frames, and six whole-camera replay scenarios.

### Minesweeper package (2026-11-12)

The image is now packaged as `artifacts/om3-minesweeper-experimental.zip`.
`package_mines.py` verifies the source hashes and all three validation
reports, rebuilds the firmware container checksum, and emits
`games-bundle.json` (hook sites, extension budget, launcher state numbers,
source hashes) plus `SHA256SUMS`. The package is one firmware carrying 2048
and Minesweeper behind a single launcher.

Coexistence is a build-time property: the OM-3 installs exactly one
`DCOLYMP/E1479999.BIN`, so two game packages cannot be flashed side by side.
To add a future game (for example the rewritten Mini Mario), compile it into
one combined image following
[COMBINING_GAMES.md](COMBINING_GAMES.md). The package keeps the user's
`LOOKS.BIN`, `EDITS.BIN` and `BUNDLES.BIN` and only supplies the
version-matched `GUIDES.BIN`, `LABELS.BIN` and `TONES.BIN`.

A held OK is no longer a restart control in either game. OK starts a new
Minesweeper round once a round has ended; INFO also restarts and is the sole
restart key in 2048. A counter probe confirmed the firmware never sends
`0x903e` to the Games CALL handler on this screen, so the old 2048 long-press
shortcut was unreachable; the finding and its evidence are recorded in
[KNOWN_ISSUES.md](KNOWN_ISSUES.md). 2048 is now deprioritised and its source
is left alone.

Build, validation and packaging bookkeeping moved to a manifest-driven layer
in `native/bundle/` ([BUNDLE_ARCHITECTURE.md](BUNDLE_ARCHITECTURE.md)). One
`games.json` declares every game module, its state id, buffer, sources, tests,
reports and screenshots; `bundle/build.py` runs the proven composer and all
registered checks; `bundle/package.py` is the generic packager. No installable
package is produced until all games, including the rewritten Mini Mario, are
final, because every new game invalidates the previous single firmware zip.

The earlier "return to shooting after a display switch" gap is resolved as
far as OM-Emu allows. Leaving Games with a shutter half-press puts the camera
in shooting state `0x0108`; an LCD/EVF switch and back re-enters that state,
and a full shutter press is handled with no engine errors. An identical
switch script gives the same GUI trajectory on the untouched Caduceus main
block, so the old `ID_ST_BLACK_SCREEN` (stock menu-closed state `0x0104`) is
not a Games regression. Switching displays **while a game is open** still
lands in the stock Picture Mode screen whose live-view re-entry the emulator
cannot model; that narrow case remains hardware-only. OM-Emu attaches no
live-view scene here, so no photograph is actually captured.

The package is still emulator-tested only and has not been installed on a
camera.

## Rich Mario and combined development image (2026-11-12)

The older single-screen handoff above is superseded by [MARIO_STATUS.md](MARIO_STATUS.md).
The raw development image now combines three games using a pooled launcher.
Follow [BUNDLE_ARCHITECTURE.md](BUNDLE_ARCHITECTURE.md); packaging is deferred.

Useful lessons: a 96-byte logical row plus reusable prepacked chunks avoids
object-position table growth; keep physics in world coordinates and subtract
camera position only for drawing. Latch jump presses before the 120ms tick,
and track Up/OK separately. Bound the output for all chunk patterns, not just
screenshots. A longer course needs a complete input-driven traversal test.
The 2048 restart control is INFO, as approved; verify live and finished rounds
instead of chasing a held event the Picture Mode screen never delivers.

## Breakout and touch lesson (2026-11-12)

[Breakout](BREAKOUT_STATUS.md) is state 5, sharing Mario's buffer and the timer
owned by `combined_bridge.s`. For E147, do not confuse SEND_EVENT's input words
with the GUI queue payload: touch arrives as a pointer to kind/x/y halfwords.
Read it synchronously and consume only during the game. OM-Emu disables this
body's controller, so native SEND_EVENT tests are GUI evidence, not a hardware
touch proof. A uint16 memory load into an address register also traps in this
emulator; loading a data register and then moving it works.

## Four-game release and hardware review (2026-11-12)

The user requested final packaging. `om3-games-bundle-experimental` includes the
four games, exact stock 1.1 restore firmware, a read-only file/card verifier,
and [installation/rollback instructions](INSTALL_AND_RESTORE.md). Older
packaging-deferred notes above describe earlier stages.

Breakout touch now changes state only; drawing follows the 120ms timer.
A 34-message burst checks that gestures add no renders beyond timer ticks;
touches on finished screens are ignored. Avoid tying expensive rendering to
hardware input frequency. The [risk review](HARDWARE_RISK_REVIEW.md) separates
tested bounds/exits from unmeasured heat, hardware queues, touch and DMA timing.
Package verification includes every container checksum and ZIP readback;
keep stock restore bytes separate because both images use the same SD filename.

## Button-only r2 after hardware feedback

The user reports general success but failed touch and a freeze entering
Breakout. Removed the entire game touch hook and parser, not just the HUD.
Breakout now uses held Left/Right and OK. Hardware causality is unproven;
do not describe emulator success as a confirmed freeze fix. Touch events are
only injected in regression tests to confirm unchanged stock dispatch.
The Games title's stock font box clipped its top; r2 uses a padded bitmap
below the game, preserving all stock strings except this custom title.
Keep the original archive for provenance and stock restore; ship r2 separately.
