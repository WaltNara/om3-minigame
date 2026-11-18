# Tests

Run `py -3 build/extras.py test` after building the combined image. This
runs the ES sound replay, Picture Mode and display pause checks, Flappy
gameplay and touch tests, and outside-game parity checks against the same
image. Reports go to `work/shutter-sound/native`.
[Development setup](../docs/DEVELOPMENT.md)

For the games-only r5 baseline, `build/build.py` runs the suite defined in
`build/games.json`. Individual Flappy checks use
`OM3_FLAPPY_BUILD=work/current-games` for that baseline.

Other scripts preserve per-game and earlier integration checks. Several need
historical outputs/metadata, so discovering and running all test*.py files is not
a supported command. `test_flappy_touch.py` is the withdrawn r3 ABI experiment,
not evidence of safe touch. CI runs `test_repository.py`, repository checks and
desktop rules without firmware or compiler.
