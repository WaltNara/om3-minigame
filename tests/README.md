# Tests

`build/games.json` selects the current suite, run by `build/build.py`.
Individual current checks use `OM3_FLAPPY_BUILD=work/current-games`:
`test_flappy.py`, `test_flappy_touch_reply.py`, `test_flappy_outside.py`.
They require the native build, OM-Emu and paired harness card.

Other scripts preserve per-game and earlier integration checks. Several need
historical outputs/metadata, so discovering and running all test*.py files is not
a supported command. `test_flappy_touch.py` is the withdrawn r3 ABI experiment,
not evidence of safe touch. CI runs `test_repository.py`, repository checks and
desktop rules without firmware or compiler.
