# Separate Games build status

The experimental Games build puts 2048 in **Picture Mode > Games > 2048** on
COLOR1–4. Its board is 384 × 480, up from 256 × 320 in the original build.
The launcher and game use arrows and dials; OK selects, INFO starts a new
round, MENU goes back one level, and a shutter half-press exits. Re-entering
2048 from the launcher resumes that session; leaving Games ends it. The camera's
HSL screen is no longer used for gameplay.

The package is [om3-games-experimental.zip](../artifacts/om3-games-experimental.zip).
It targets OM-3 firmware 1.1 and is **emulator-tested, not camera-tested**.
The previous HSL-based package remains separate. TinyMario is the selected
next game candidate; it has not been implemented.

The final image passed the emulator replay for launcher selection, four arrows,
both dials against an independent 2048 model, scoring, spawning, restart,
session resume, panel removal and settings preservation. On LCD/EVF output
change, the game clears its state and saved drawing pointer. The emulator did
not establish normal return to shooting after a switch; its final state in the
test was a black-screen state. Earlier versions passed 617 native CPU rule and
renderer cases, a comparison of HSL and WB with unmodified Caduceus, and Games
entry and shutter exit on all four COLOR profiles. Those broader checks were
not rerun after the final scoped rendering guard and display-switch changes.

The native display submission path calls `EXEC_END`, which waits on the OSD
completion event before returning to the GUI task. That supports the buffer
lifetime design, but the emulator executes drawing synchronously; real
latency, error handling, display changes and responsiveness still need a
physical-camera test. The build loads 90,112 additional bytes, including a
37,972-byte compressed board buffer. It makes no heap allocations.

Rebuild and repeat the focused checks from the project root:

```
py -3 native/probe_games_row.py
py -3 native/test_games_display.py
py -3 native/package_games.py
```

The builder verifies the pinned Caduceus baseline and uses the existing local
toolchain, emulator harness and paired card image. Outputs and detailed logs
are under `work/separate-games`. The packager checks the exact tested main
image, source hashes and firmware container checksums; it does not install or
upload anything.
