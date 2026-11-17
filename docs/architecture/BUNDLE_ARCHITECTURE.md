# Bundle workflow

`build/games.json` inventories IDs/controls/sources and selects composer arguments,
environment, tests, reports and evidence. Native dispatch/linking remain explicit
in `native/build_combined.py`, `combined_host.s` and `flappy_build.py`.

`build/build.py` builds five games into `work/current-games`, runs the configured
suite, checks image/source/report hashes and loaded size, then writes
`bundle-build.json`. `--verify-existing` rechecks without rebuilding/replaying.
A manifest hash prevents packaging with a changed configuration.

`build/package.py` requires current evidence, rebuilds the firmware container,
checks every component and includes separate `card/` and stock `restore/` trees.
Only version-matched GUIDES/LABELS/TONES are added, plus public docs, source paths,
test evidence, SHA256SUMS and the PowerShell verifier. The generated README explains
Flappy touch and the recorded camera baseline. `--dry-run` checks inputs without
writing; `--name` selects a new release. Existing releases are never overwritten.

Current reports cover Flappy physics/render/playability, GUI lifecycle, native
touch protocol and outside-game parity, not exhaustive fresh checks of every
historical game. Source-only CI is another layer. See
[development](../DEVELOPMENT.md) and [status](../STATUS.md).
