# Development guide — interfaces and extending the bundle

This is the entry point for working on the minigames. It describes the **usable
interfaces** and how to add or change a game. Gameplay rules are out of scope —
the games are standard.

## Prerequisites (dependencies, obtained separately)

1. **Caduceus for OM-3** v0.26.2, pinned at commit `f4d2569…`. Clone
   `https://github.com/androidfanman/caduceus-om3` into `vendor/caduceus-om3/`.
   Its `releases/v0.26.2` and `firmware/` directories are consumed by the build.
2. **Your official OM-3 firmware 1.1 file** (`OLY_E_147_1100_…BIN`). The build
   patches this into the combined image and produces the stock restore bytes. It
   is never committed.
3. Toolchain: MN10300 binutils (`native/build_toolchain.sh`) and `om-emu` are
   staged under `work/` for local builds.

## The build pipeline

```
native/bundle/games.json   →  manifest (single source of truth)
native/build_combined.py    →  patches Caduceus baseline, links game modules
                                 → work/combined-game/row-main.bin
native/bundle/build.py      →  builds, runs registered checks, verifies hashes
                                 + 256 KiB budget, writes bundle-build.json
native/bundle/package.py    →  assembles card/ + restore/ + verification
                                 → artifacts/<package_name>.zip
```

Commands (run from the repo root):

```powershell
py -3 native/bundle/build.py                   # build + validate
py -3 native/bundle/build.py --verify-existing # re-verify without rerunning checks
py -3 native/test_combined_game.py             # native + full-camera replay checks
py -3 native/bundle/package.py                 # produce a release zip
py -3 native/bundle/package.py --dry-run       # inputs only
```

`package.py` checks every container checksum, includes the exact stock restore
bytes, and reads the finished ZIP back to verify CRCs/hashes. Use a **new
`package_name`** per release; existing archives are never overwritten.

## The interface a game must implement

Each game is a module registered in `games.json` and linked by
`build_combined.py`. The shared contract:

- **State id** — a unique integer (2048 = 2, Minesweeper = 3, Mario = 4,
  Breakout = 5; Back returns to the launcher). `combined_host.s` dispatches input
  and paint by this id.
- **Source / asset files** — `core` (rules + state + draw buffer), `render`
  (RLE / prepacked scanline drawing), `assets` (packed rows / bitmaps), and a host
  fragment for input. All buffers are **fixed-size and bounded**; no heap, no
  retained screen pointer.
- **Launcher entry** — one label + one pooled bitmap; extend the selection wrap
  and Back index in `combined_menu.s`.
- **Controls** — declared in `games.json`. Keys are native GUI events: OK
  `0x900c`, INFO `0x9014`, dpad `0x9004/6/8/a`. The held-OK event (`0x903e`) is
  **not** delivered in Picture Mode, so 2048 uses INFO to restart.
- **Tests + evidence** — per-game native rule/render checks and a whole-camera
  replay are listed in `games.json` and must pass before packaging.

## Adding a new game (steps)

1. Register it in `native/bundle/games.json`: state id, sources, assets, controls,
   tests, evidence. List any helper scripts under `support_sources` so they are
   hashed into the source archive.
2. Implement `core` / `render` / `assets`; add input + startup + render branches
   in `combined_host.s`; extend launcher navigation in `combined_menu.s`; link the
   module in `build_combined.py`.
3. Keep fixed-size state and bounded buffers; prefer event-driven games. Timed
   games (Mario, Breakout) must post ticks to the GUI queue and keep all
   state/render on the GUI task, cancelling timers on exit and discarding stale
   epochs.
4. Rebuild and validate: target ≤240 KiB including appended tables, within the 256
   KiB ceiling, keeping the 16 KiB reserve.
5. Package only when ready (`package.py`); verify with `--dry-run` first.

## Hard rules

- One camera update holds all games; the standalone historical builders are not
  the baseline.
- Do not increase frame rate without measured evidence; slow-frame queue growth
  and graphics-buffer DMA lifetime are still hardware-open questions.
- No touch experiments without a separate hardware probe; emulator SEND_EVENT
  injection does not emulate the E147 controller.
  Follow the [touch development guide](../native/TOUCH_DEVELOPMENT_GUIDE.md):
  establish delivery and gesture semantics before coordinate-based gameplay.
- Consumed touch events must still complete the native application's reply
  handshake. Test through the application queue; direct GUI injection missed
  the r3 deadlock.
- Test tap/double-tap endings as alternatives to release, not only after it.
  The r4 contact latch stayed set on 1,4 and 1,5 sequences despite completing
  every reply; r5 clears it on terminal kinds 3/4/5.
- Never confuse the install vs restore `E1479999.BIN` source folders.
- Record user hardware results separately from emulator results.

## Where to look

- `native/BUNDLE_ARCHITECTURE.md` — manifest-driven build / validate / package.
- `native/COMBINING_GAMES.md` — low-level hook + budget contract.
- `native/INSTALL_AND_RESTORE.md` — card layout, install, rollback.
- `native/HARDWARE_RISK_REVIEW.md` — what is and isn't validated on hardware.
- `native/KNOWN_ISSUES.md` — resolved input changes + remaining hardware checks.

## Native implementation lessons

- Verify CALL versus CALLS stack frames and saved registers with small native
  probes before adding a new hook. Preserve MDR when the caller needs it;
  multiplication can overwrite it. Link branch destinations and inspect disassembly.
- Pass the existing graphics API uncached addresses (firmware-resident data
  uses the +0x40000000 alias), keep RLE runs within scanlines, and preserve the
  proven surfaces and unscaled draw calls. Derive buffer bounds before linking.
- Prove entry, input, redraw and exit early. Keep emulator results and user
  hardware confirmation distinct; instruction counts are not camera timings.

Historical probes, stage-by-stage handoffs and research notes are deliberately
not published in this repository; the accepted baseline and its current
validation reports are linked above.
