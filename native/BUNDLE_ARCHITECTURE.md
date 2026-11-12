# Games bundle architecture

The camera installs one firmware image, with one Games launcher. The current
development image contains **2048, Minesweeper, Mini Mario, Breakout, Back**, with states
2, 3, 4, 5 and Back index 4. Historical packages remain available but are unchanged.
The user has now requested the four-game package; installation and rollback
are in [INSTALL_AND_RESTORE.md](INSTALL_AND_RESTORE.md).

`native/bundle/games.json` records the builder, launcher entries, module sources,
controls, checks and evidence. `build_combined.py` links the modules and patches
one Caduceus baseline; `combined_host.s` owns input and paint dispatch;
`combined_menu.s` owns navigation. `combined_launcher_assets.py` and
`combined_launcher.s` pool repeated rows into one bounded launcher buffer.

## Build and validate

```
py -3 native/bundle/build.py
py -3 native/bundle/build.py --verify-existing
```

The first command builds the raw image, runs all registered checks, verifies
image/source/report hashes and the extension budget, then writes
`work/combined-game/bundle-build.json`. It does not package. The second command
verifies existing build/evidence without rerunning unchanged checks; use it
only after the registered tests have completed on the same image.

The authoritative development image is `work/combined-game/row-main.bin`.
`test_combined_game.py` runs the native Mario rule/render checks, its full
camera replay, and the Minesweeper native and camera checks, including 2048
INFO restart and display-switch parity against the baseline. All reports must
pass; image-bearing reports must match the candidate SHA-256.

## Adding another game

1. Register its unique state, sources, assets, controls, tests and evidence in
   `games.json`. List helper test scripts in `support_sources` so they are also
   included in source hashes and a future source archive.
2. Extend the launcher navigation and shared launcher entries. Add input,
   startup and render branches in `combined_host.s`; link the new module in
   `build_combined.py`. Keep the old standalone builders as historical paths.
3. Keep fixed-size state and bounded buffers. Prefer event-driven games. Mario and Breakout
   are the deliberate exceptions: their shared timer posts through a deferred task to the
   GUI queue; only the GUI task updates state and paints, and generation checks
   discard stale callbacks. Do not add per-game timer/queue hooks casually.
4. Rebuild and validate the combined image. Target at most 240 KiB including
   appended tables, within the proven 256 KiB ceiling. The current launcher
   shares its rows; further games may also need buffer sharing or smaller art.
5. Package only when the intended release is ready using
   `py -3 native/bundle/package.py`. Existing release targets are not overwritten;
   use a new manifest package name for a later release. Packaging checks every
   container checksum, includes exact stock restoration bytes, and reads the
   completed ZIP back to verify CRCs and hashes. `--dry-run` checks inputs only.

Version-matched GUIDES/LABELS/TONES travel with firmware at packaging time.
Keep the user's LOOKS/EDITS/BUNDLES. See [COMBINING_GAMES.md](COMBINING_GAMES.md)
for the firmware/card contract. Emulator results are not camera validation.

Breakout is the fourth game; its controls and the physical-touch limitation are
recorded in [KNOWN_ISSUES.md](KNOWN_ISSUES.md). `combined_bridge.s` dispatches
timer events to the active game and consumes touch only in Breakout. Breakout
shares Mario's output buffer and chunk assets; neither keeps pixels when
inactive. The five-entry launcher retains its own bounded buffer. Native
full-clear, touch GUI and lifecycle tests run via `test_breakout.py`.
