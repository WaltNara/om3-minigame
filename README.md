# OM-3 Minigames

Five native games inside **Picture Mode > Games** on the OM SYSTEM OM-3,
firmware 1.1 (E147 build 1100), built on
[Caduceus for OM-3](https://github.com/androidfanman/caduceus-om3) v0.26.2.

| Game | Controls |
| --- | --- |
| 2048 | Arrows/dials; INFO restarts |
| Minesweeper | Arrows/dials, OK to open, INFO to flag |
| Mini Mario | Left/right; Up/OK to jump; scrolling map |
| Breakout | Left/right paddle; OK launches |
| Flappy | Tap or Up/OK; slow pace, variable pipe spacing, live distance |

MENU returns to the launcher; shutter leaves Games. Only Flappy owns touch.
**r5 is the accepted baseline:** the user reports a perfect camera touch test.
See [current status and limits](docs/STATUS.md).

Modified firmware carries installation risk. Use the supported model/version,
a charged battery, and keep stock rollback. Read the
[installation guide](docs/INSTALL_FIVE_GAMES.md) before installing.
Firmware and dependencies are kept locally and are not committed here.

## Start here

- Install/play: [installation and controls](docs/INSTALL_FIVE_GAMES.md).
- Build/change games: [development guide](docs/DEVELOPMENT.md).
- Touch: [working implementation and lessons](docs/TOUCH_DEVELOPMENT_GUIDE.md).
- Limits: [status](docs/STATUS.md), [hardware review](docs/HARDWARE_RISK_REVIEW.md).

After setting up the external inputs in the development guide:

```powershell
py -3 build/build.py                     # five-game build + current validation
py -3 build/build.py --verify-existing   # recheck hashes and reports
py -3 build/package.py --dry-run         # verify packaging inputs
py -3 build/package.py --name my-release # create a NEW local package
```

## Layout

```text
build/                 manifest, build/test driver, packager, verifier
native/                camera assembly, assets, low-level build/setup
tests/                native/emulator scripts and source-only checks
docs/                 installation, development, status, touch guide
   architecture/       integration contracts
   history/            earlier installation and camera records
tools/
   diagnostics/        failure reproductions and probes
   legacy/             superseded standalone builders and packagers
   desktop-prototypes/ early desktop games
```

`vendor/`, `work/`, and `artifacts/` are ignored dependencies, generated outputs,
and packages. Private historical notes stay in ignored `docs/archive/` and
`docs/research/`. See [organization decisions](docs/REPOSITORY.md).

The manifest inventories games and drives build/test/package commands. Native
linking and dispatch remain explicit; adding a manifest entry alone adds no game.

## License

Apache-2.0; see [LICENSE](LICENSE) and [NOTICE](NOTICE). Caduceus is an external
Apache-2.0 dependency. Manufacturer firmware is not redistributed in this repository.
