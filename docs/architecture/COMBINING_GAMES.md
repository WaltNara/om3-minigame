# Combining games in one firmware

The OM-3 accepts one `DCOLYMP/E1479999.BIN`. Game code lives in that image's main
block; installing another game image replaces it. Coexistence means linking all
games and one launcher together. OM3MOD data files are not separate game binaries.

## Integration

| Layer | Current owner |
| --- | --- |
| Picture Mode Games row, input/paint/transition hooks | native/combined_host.s |
| Launcher navigation and labels | native/combined_menu.s, combined_launcher*.s/py |
| GUI ticks, generations and cancellation | native/combined_bridge.s |
| Fifth-game host generation | native/flappy_build.py |
| Per-game rules/render/assets | matching modules in native/ |
| Linking/patching | native/build_combined.py |
| Build/test/package configuration | build/games.json |

States: 0 closed, 1 launcher, 2 2048, 3 Minesweeper, 4 Mario, 5 Breakout, 6 Flappy.
Launcher index 5 is Back. The fifth-game generator inserts checked input/start/
paint/tick branches; adding a manifest entry alone does not generate these.

The loaded extension starts at `0x60f59800` with a 256 KiB ceiling. Accepted r5
loads 232 KiB, leaving 24 KiB. Include alignment, buffers and appended tables in
this budget. Do not enlarge the loader range casually. Keep fixed buffers, no
retained event pointers, and state/render work on the GUI task. Timers post
messages and cancel on exit; generation checks reject stale ticks.

Touch ownership belongs only to Flappy. The hook completes the native reply even
when it suppresses widget navigation. Terminal kinds 3/4/5 release the contact
latch. See the [touch guide](../TOUCH_DEVELOPMENT_GUIDE.md).

## Card data and verification

GUIDES.BIN, LABELS.BIN and TONES.BIN must match the pinned Caduceus firmware.
The current package includes these three; optional film files are not required.
Preserve existing custom LOOKS/EDITS/BUNDLES files.

Build one image, run native rule/render checks and full-camera input/exit replays,
verify exact image/report hashes, then package under a new name. Local checks and
hardware reports are distinct. See [workflow](BUNDLE_ARCHITECTURE.md),
[development](../DEVELOPMENT.md), and [status](../STATUS.md).
