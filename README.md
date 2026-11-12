# OM-3 Native Minigames

A small pack of native minigames that run inside **Picture Mode → Games** on the
OM SYSTEM OM-3 (firmware 1.1), built on top of the
[Caduceus for OM-3](https://github.com/androidfanman/caduceus-om3) firmware patch.

> ⚠️ **Experimental.** Installing modified firmware can brick a camera. Do it only
> at your own risk, on a full battery, and keep the stock restore image. This code
> is **emulator-tested**; the current release (r2) has also passed a user
> on-camera check. See [`native/HARDWARE_RISK_REVIEW.md`](native/HARDWARE_RISK_REVIEW.md).

## What's in the box

| Game | One-line note |
| --- | --- |
| 2048 | arrow/dial move, INFO restarts, MENU/shutter exits |
| Minesweeper | 8×8, first-click-safe, flood fill, flag |
| Mini Mario | scrolling auto-runner, button jump |
| Breakout | button-only paddle (touch removed in r2) |

All four share one Games launcher. The camera installs exactly **one** firmware
image (`DCOLYMP/E1479999.BIN`), so the games are combined into a single image at
build time — see [`native/COMBINING_GAMES.md`](native/COMBINING_GAMES.md).

## Dependency — referenced, not included

This repository contains **only the game modules and their build/packaging
layer**. Two external pieces are required to build or run, and are **not** part
of this repo:

- **Caduceus for OM-3** v0.26.2 (Apache-2.0, androidfanman; derived from
  cakelesscoder/caduceus-ep7). Pinned at commit `f4d2569…`. Obtain it separately
  and place it at `vendor/caduceus-om3/`.
- **Your own official OM-3 firmware 1.1 file.** The patched image and the stock
  restore image are produced from it; manufacturer firmware is **not**
  redistributed here.

The local `vendor/`, `work/` and `artifacts/` directories are git-ignored — they
hold the fetched dependency, build intermediates and release zips respectively.

See [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) for the exact setup, build,
test and packaging flow.

## Project layout

```
om3-minigames/
├── README.md                 # this file
├── LICENSE                   # Apache-2.0 (this project)
├── NOTICE                    # provenance / dependency note
├── docs/
│   ├── DEVELOPMENT.md        # interfaces & how to extend  ← start here
│   └── research/             # historical design notes (not gameplay)
├── native/                   # game source, build, tests, status docs
│   ├── bundle/               # manifest-driven build & package framework
│   ├── 2048*.s, mines_*.s, mario_*.s, breakout_*.s, combined_*.s
│   ├── INSTALL_AND_RESTORE.md
│   ├── BUNDLE_ARCHITECTURE.md, COMBINING_GAMES.md
│   └── …                     # status & risk docs
├── tools/desktop-prototypes/ # early desktop/guessing prototypes (historical)
├── vendor/                   # Caduceus (git-ignored; fetched separately)
├── work/                     # build intermediates & firmware (git-ignored)
└── artifacts/                # release zips (git-ignored)
```

## For developers — interfaces & extension

The usable surface for adding or modifying a game is documented in
[`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md), with the machine-readable contract
in `native/bundle/games.json`. In short:

- **Manifest** — `native/bundle/games.json`: one entry per game (state id, source
  and asset files, controls, tests, evidence). No game names are hardcoded in the
  builder.
- **Dispatch** — `combined_host.s` owns input and paint dispatch by `games_state`;
  `combined_menu.s` owns launcher navigation; per-game `core`/`render`/`assets`
  modules implement the rules and drawing.
- **Build & validate** — `py -3 native/bundle/build.py` (and `--verify-existing`);
  `test_combined_game.py` runs native + replay checks; `py -3 native/bundle/package.py`
  produces a release (never overwrite an existing archive; use a new `package_name`).
- **Constraints** — one firmware image, fixed-size state, bounded buffers, ≤240 KiB
  extension with a 16 KiB reserve; timed games must keep state/render on the GUI
  task and cancel timers on exit.

Detailed references:
[`native/BUNDLE_ARCHITECTURE.md`](native/BUNDLE_ARCHITECTURE.md),
[`native/COMBINING_GAMES.md`](native/COMBINING_GAMES.md).

## Installing / restoring

The built firmware + card files are distributed as a binary release
(`om3-games-bundle-buttons-r2`). Follow
[`native/INSTALL_AND_RESTORE.md`](native/INSTALL_AND_RESTORE.md). Short version:
copy `card/` to the SD root, hold OK while powering on, wait for the lamp to
blink, then delete `DCOLYMP/E1479999.BIN` from the card. Keep the `OM3MOD/` files.

## License

The game modules in this project are licensed under the **Apache License 2.0** —
see [`LICENSE`](LICENSE). They build on Caduceus for OM-3 (Apache-2.0,
androidfanman), which is a separate project referenced as a dependency and **not**
included here. No OM Digital Solutions / Olympus firmware is redistributed by this
repository.
