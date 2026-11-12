# Combining camera games into one installable image

Current development: `build_combined.py` / `combined_host.s` / `combined_menu.s`
combine 2048 (state 2), Minesweeper (3), Mini Mario (4), and Breakout (5),
with Back at index 4.
The shared launcher uses pooled rows and one buffer. Read
[BUNDLE_ARCHITECTURE.md](BUNDLE_ARCHITECTURE.md) for current commands.
The four-game release is `om3-games-bundle-experimental`; see
[INSTALL_AND_RESTORE.md](INSTALL_AND_RESTORE.md). The two-game package described
below remains a historical reference.

**Short version:** the OM-3 installs exactly one firmware update file,
`DCOLYMP/E1479999.BIN`. Game code lives in that firmware's main block, not in
the `OM3MOD` data files. Two game packages therefore cannot be flashed side by
side — the last one written wins. Coexistence means **one combined firmware
image with one Games launcher**, built once from all game modules.
[BUNDLE_ARCHITECTURE.md](BUNDLE_ARCHITECTURE.md) documents the manifest-driven
layer that registers those modules; this file remains the low-level hook and
budget contract.

The `om3-minesweeper-experimental` package is already such a bundle: it keeps
2048 intact and adds Minesweeper behind the same Games row. It is a strict
superset of the earlier `om3-games-experimental` package (same Caduceus
v0.26.2 baseline, same version-matched card files).

## What a combined image contributes

| Layer | Owner in this build |
| --- | --- |
| Games row in Picture Mode and key/paint hooks | `mines_host.s` |
| Launcher navigation and state numbers | `mines_menu.s` |
| Launcher bitmaps (one per selection) | `mines_launcher_assets.py` |
| Game rules, state and drawing buffer | `mines_core.s`, `mines_render.s`, `mines_assets.py` |
| 2048 rules, state and drawing buffer | `2048_large.s`, `assets_large.py` |
| Patcher, assembler/linker driver | `build_mines.py` |

`games-bundle.json` in the package records the exact hook sites, extension
region, state numbers, symbol names, source hashes and validation hashes for
the shipped image. Treat it as the machine-readable contract.

## Contract for adding another game

These are the only change points; everything else is shared.

1. **Launcher.** Add one entry and one bitmap; extend the selection wrap and
   the Back index in `games_event`, and add the new state number.
2. **Host dispatch.** Add one input branch in `games_pm` and one render branch
   in `games_render_hook` for the new state and its drawing buffer.
3. **Module.** Link the new rules/render files into `build_mines.py` and keep
   every buffer bounded and prepacked. No heap, no retained screen pointer.
4. **One image.** Rebuild a single `row-main.bin`, then rerun all three
   emulator layers and the whole-camera replay before packaging. Two separate
   `E1479999.BIN` files are never both active.

State numbers in the shipped image: 0 closed, 1 launcher, 2 = 2048,
3 = Minesweeper. Launcher index 2 is Back. The extension region starts at
`0x60f59800` with a 256 KiB ceiling; the shipped image uses about 176 KiB of
it. Any added game must fit the remainder, or the loader range must be revised
and revalidated.

## Card files and coexistence with Caduceus data

- `GUIDES.BIN`, `LABELS.BIN` and `TONES.BIN` are version-matched to the
  firmware. Copy the three from the package together with the firmware.
- **Keep** your existing `LOOKS.BIN`, `EDITS.BIN` and `BUNDLES.BIN`. They hold
  your film simulations and edits. This package deliberately ships its
  default `LOOKS.BIN` under `optional/`, not under `card/`, so installing the
  games does not overwrite them.
- Never mix `OM3MOD` files from different Caduceus versions; the camera can
  freeze if `GUIDES.BIN` and the firmware disagree.

## Verification expectations

A combined image needs its own evidence. Re-run the native CPU rule checks,
the RLE pixel decode frames and the whole-camera replay (including a 2048
regression move, shutter exit, display-switch cleanup and the return to
shooting). Regenerate the package hashes and validation report. Emulator
evidence is never hardware evidence: drawing latency, physical button timing,
buffer lifetime and live-view re-entry after a display switch still need a
physical camera.
