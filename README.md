# OM-3 Native Minigames

A small pack of native minigames that run inside **Picture Mode → Games** on the
OM SYSTEM OM-3 (firmware 1.1), built on top of the
[Caduceus for OM-3](https://github.com/androidfanman/caduceus-om3) firmware patch.

> ⚠️ **Experimental.** Installing modified firmware can brick a camera. Do it only
> at your own risk, on a full battery, and keep the stock restore image. Emulator
> checks are not hardware proof; the accepted five-game **r5** build additionally
> has a user-reported good on-camera touch result. See
> [`native/HARDWARE_RISK_REVIEW.md`](native/HARDWARE_RISK_REVIEW.md) and
> [`native/TOUCH_DEVELOPMENT_GUIDE.md`](native/TOUCH_DEVELOPMENT_GUIDE.md).

## What's in the box

| Game | One-line note |
| --- | --- |
| 2048 | arrow/dial move, INFO restarts, MENU/shutter exits |
| Minesweeper | 8×8, first-click-safe, flood fill, flag |
| Mini Mario | scrolling auto-runner, button jump |
| Breakout | button-only paddle |
| Flappy | slow tap-controlled flight; live distance; **the touch-enabled game** |

All five share one Games launcher. Only Flappy owns touch: a tap queues one flap
and all consumed touch events complete the camera's native reply handshake. The
other four keep stock touch behaviour; buttons work in all five. See
[`native/TOUCH_DEVELOPMENT_GUIDE.md`](native/TOUCH_DEVELOPMENT_GUIDE.md) for the
accepted implementation rules and validation commands.

The camera installs exactly **one** firmware image (`DCOLYMP/E1479999.BIN`), so
the games are combined into a single image at build time — see
[`native/COMBINING_GAMES.md`](native/COMBINING_GAMES.md). Current accepted source
build: `py -3 native/build_combined.py --flappy-touch` (raw image SHA256
`a3b5e0aa720f3703f6d3adcf771edb855ac99d63c24c116816976ff37c203ed8`, five-r5).

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
│   └── DEVELOPMENT.md        # interfaces & how to extend  ← start here
├── native/                   # game source, build, tests, docs
│   ├── bundle/               # manifest-driven build & package framework
│   ├── 2048*.s, mines_*.s, mario_*.s, breakout_*.s, flappy_*.s, combined_*.s
│   ├── INSTALL_FIVE_GAMES.md  # current five-game install / rollback
│   ├── TOUCH_DEVELOPMENT_GUIDE.md  # touch event ownership / gesture rules
│   ├── BUNDLE_ARCHITECTURE.md, COMBINING_GAMES.md
│   └── HARDWARE_RISK_REVIEW.md, KNOWN_ISSUES.md, …
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
(`om3-games-bundle-five-r5`); binaries are **not** committed to this repository.
Follow [`native/INSTALL_FIVE_GAMES.md`](native/INSTALL_FIVE_GAMES.md) (current
five-game flow) or [`native/INSTALL_AND_RESTORE.md`](native/INSTALL_AND_RESTORE.md)
(the earlier four-game reference). Short version: copy `card/` to the SD root,
hold OK while powering on, wait for the lamp to blink, then delete
`DCOLYMP/E1479999.BIN` from the card. Keep the `OM3MOD/` files. Never mix install
and restore BINs.

## Release notes — five-r5 (accepted touch baseline)

- Fixes the r3 touch **deadlock** (missing native completion reply) and the r4
  **missed taps** (stale contact latch when a gesture ended with kind 4/5).
- Touch owns only the Flappy page; terminal kinds 3/4/5 clear contact, one flap
  per initial contact, no payload retention or extra state.
- Local gates: 181 touch events with 181 replies/waits returned, 1,750 physics
  cases, 26 raster frames, seven GUI scenarios, 14 outside-game parity snapshots.
  Camera: user reports the touch test is perfect; no event trace or endurance
  duration was recorded.
- Still open: E147's physical controller is unmodelled, long-session stability
  and touch recovery after an LCD/EVF switch are unverified, and earlier rare
  R2 freezes are a separate unresolved issue.
- Earlier r3 is withdrawn; r4 (no freeze, missed taps) is the comparison
  baseline; both are preserved as local-only release packages.

## License

The game modules in this project are licensed under the **Apache License 2.0** —
see [`LICENSE`](LICENSE). They build on Caduceus for OM-3 (Apache-2.0,
androidfanman), which is a separate project referenced as a dependency and **not**
included here. No OM Digital Solutions / Olympus firmware is redistributed by this
repository.
