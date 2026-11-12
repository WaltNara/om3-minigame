# Minesweeper build and package status

An experimental, event-driven 8x8 Minesweeper has been added to a separate
Games build and packaged as `om3-minesweeper-experimental.zip`. It targets
OM-3 firmware 1.1 / E147 build 1100 through Caduceus v0.26.2 and is
**tested in OM-Emu only; it has not been tested on a physical camera**.

The package is a single firmware image containing **2048 and Minesweeper
behind one Games launcher**. Because the camera installs exactly one
`E1479999.BIN`, games cannot be flashed as separate packages; see
[COMBINING_GAMES.md](COMBINING_GAMES.md) for the contract used to combine
game modules into one image. The earlier `om3-games-experimental` and
`om3-2048-experimental` packages, and every Mini Mario source file, are
untouched. Mario has its own suggestion list in
[MARIO_ENRICHMENT_IDEAS.md](MARIO_ENRICHMENT_IDEAS.md).

Build and packaging bookkeeping now lives in the manifest-driven
[BUNDLE_ARCHITECTURE.md](BUNDLE_ARCHITECTURE.md); packaging of a revised
bundle is deferred until every game is final. Known limitations, including
the 2048 held-OK issue, are collected in
[KNOWN_ISSUES.md](KNOWN_ISSUES.md).

## Where it lives

Build output: `work/mines-game/`. Main image: `work/mines-game/row-main.bin`.
Installable package: `artifacts/om3-minesweeper-experimental.zip` (directory
`artifacts/om3-minesweeper-experimental/`). Main image SHA-256:
`8ce72c52e664bdd383927a379e9d761504870a30bff811dfc7f406be687a3ca6`
Firmware SHA-256:
`054f4c24ecfbbd548c9689bf1dbbce2790af3dfde76ea2b13ae45a932ddbbf15`

| File | Purpose |
| --- | --- |
| `mines_core.s` | Board state, mine placement, flood fill, flags, win/loss |
| `mines_render.s` | Prepacked RLE row compositor and HUD counters |
| `mines_assets.py` | Tile rows, character rows, HUD text, row lookup tables |
| `mines_host.s` | Games row, input dispatch, paint invalidation, bitmap submission |
| `mines_menu.s` | Three-entry launcher navigation |
| `mines_launcher_assets.py` | Static launcher bitmaps |
| `build_mines.py` | Firmware patcher and assembler/linker driver |
| `package_mines.py` | Package builder, manifest and checksum generator |
| `test_mines_core.py` | Native CPU rule checks against an independent model |
| `test_mines_render.py` | RLE decode and pixel comparison inside OM-Emu |
| `test_mines_game.py` | Whole-camera replay, display-switch and shooting checks |

## Gameplay and controls

The board is 8x8 with 10 mines. Mines are placed on the first opening move,
never in that cell's 3x3 neighbourhood, so the first click is always safe and
always opens an area. Empty areas expand through a bounded breadth-first
queue. Neighbour counts, flags, a revealed-cell counter and win/loss states
are all held in fixed-size native data.

Open Picture Mode from the Super Control Panel on COLOR1-4, scroll to Games
at the end of the list and press OK. The launcher offers 2048, MINESWEEPER
and Back; arrows or a dial change the selection and OK enters.

| Input | Action in Minesweeper |
| --- | --- |
| Arrows / main and sub dials | Move the highlighted cursor |
| OK | Open the cursor cell; **after a win or loss, start a new round** |
| INFO | Toggle a flag; after a win or loss, start a new round |
| MENU | Return to the launcher; re-entering resumes the session |
| Shutter half-press | Leave Games through the camera's own path |
| LCD/EVF switch | Clear Games state and reset the round |

**A held OK is not a control.** The earlier long-press restart was removed
from both Minesweeper and 2048 because it is ambiguous and hard to judge on
this body. A new round is started normally with OK once a round has ended;
INFO also works, and INFO starts a new 2048 round at any time. The 2048 HUD
now reads `ARROWS MOVE  INFO NEW` / `GAME OVER  INFO NEW GAME`. The camera
firmware never delivers `0x903e` to the Games input handler in this branch,
so the old `HOLD OK NEW` shortcut was unreachable rather than merely removed;
see [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for the probe evidence.

A win opens all safe cells (54 of 64) and flags the mines. A loss reveals
every mine and marks the one that was opened. The HUD shows remaining mines,
opened cells and flags. There is deliberately one course and no pause, timer
or chording.

## Camera-safety choices

- No heap allocation, no animation timer, and no GUI queue hook. Unlike the
  Mario prototype, this build installs no periodic timer at all; it is fully
  event driven, like the original 2048 integration.
- Rendering copies prepacked RLE words only. Every row segment is a whole
  number of five 12-bit tokens and no run crosses a scanline. The renderer
  never encodes a scanline at runtime and never uses a full framebuffer.
- The Minesweeper buffer is a fixed 59,476 bytes, derived from the worst-case
  row layout. `mines_buffer_end` is guarded by a sentinel in the render test.
- Only palette indices 7 (background) and 10 (foreground) are used, the pair
  already proven by the 2048 guide images. Grid lines, glyph shapes and an
  inverted cursor cell distinguish tiles without untested colours.
- The added loaded section is 180,224 bytes, below the 256 KiB extension
  limit. The linked `.text` blob is 178,432 bytes.
- Games owns input only while it is active. Key releases are consumed; the
  shutter half-press is passed back to the camera. Display switches and real
  screen transitions clear Games state. The 2048 game and its board buffer
  remain untouched.
- The package keeps the user's film simulations: `LOOKS.BIN`, `EDITS.BIN` and
  `BUNDLES.BIN` are not overwritten. Only the version-matched `GUIDES.BIN`,
  `LABELS.BIN` and `TONES.BIN` are supplied; a default `LOOKS.BIN` is offered
  under `optional/` only.

## Validation

Rebuild, repeat all three layers, and repackage from the project root:

```
py -3 native/build_mines.py
py -3 native/test_mines_core.py
py -3 native/test_mines_render.py
py -3 native/test_mines_game.py
py -3 native/package_mines.py
```

- `test_mines_core.py`: 20 native CPU cases replayed in OM-Emu, comparing the
  assembled board and state byte-for-byte with an independent Python model.
  Covers movement, flag toggle, deferred mine placement, first-click safety,
  neighbour counts, flood fill, win and loss.
- `test_mines_render.py`: three native frames (fresh, mid-game, loss) are
  decoded from `mines_buffer` and compared pixel-for-pixel with reference
  frames; the buffer sentinel stays intact.
- `test_mines_game.py`: six whole-camera scenarios. Covers the Games row,
  launcher, cursor movement, first-click opening, flag toggle, MENU, a 2048
  regression move, session resume, shutter exit, end-of-round restart with OK,
  ignored held-OK presses in both games, display-switch cleanup, the return
  to shooting, and an identical display-switch script replayed on the
  untouched Caduceus main block for parity.
- `package_mines.py` re-verifies every source hash and all three validation
  reports, rebuilds the firmware container checksum, and writes
  `games-bundle.json` plus `SHA256SUMS`.

### Display switching and normal shooting

`ID_ST_BLACK_SCREEN` in earlier reports is the stock **menu-closed** GUI
state (`0x0104`), not a crash: the same state appears on the untouched
Caduceus baseline. The earlier "return to shooting not established" gap is
now resolved as far as OM-Emu allows:

- After leaving Games with a shutter half-press, the camera is in the
  shooting state (`0x0108`). Switching LCD to EVF and back re-enters that
  same shooting state, and a full shutter press is handled without leaving
  it or producing engine errors.
- The same display-switch script produces an identical GUI trajectory on the
  patched image and on the untouched baseline, so the patch does not change
  the stock display path.
- Switching displays **while a game is running** clears the Games session and
  leaves the camera in the stock Picture Mode screen, with no engine errors.
  OM-Emu does not model live-view re-entry from that screen; this one case
  remains a hardware-only check.
- OM-Emu attaches no live-view scene in this replay, so no photograph is
  actually captured and the shooting screen composes as a flat frame. The
  GUI state, not the pixels, is the evidence.

## Limitations

Emulator evidence is not hardware evidence. Real drawing latency, physical
button behaviour, concurrent key handling, buffer lifetime and normal
shooting after a display switch made **from inside the Games menu** still
need a physical camera. The 3x5 bitmap font is coarse at this scale. This
build is not installed or uploaded to a camera.
