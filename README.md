# OM-3 Minigames

Two features for the OM SYSTEM OM-3 (firmware 1.1, E147 build 1100), based on
[Caduceus for OM-3](https://github.com/androidfanman/caduceus-om3) v0.26.2:

- **Games** — five native games with paused live-view display.
- **ES sound** — selectable electronic-shutter sound on capture.

The combined build `8bf67c77473a` was tested on a real OM-3.
[Camera test results](docs/STATUS.md)

## Quick install (no build needed)

1. Download `artifacts/om3-extras-8bf67c77473a.zip`. Use the `-local` variant
   instead if you want the supplied Ciallo and Man sounds included.
2. Copy the **contents of `card/`** to the root of an SD card.
3. With the camera **off**, hold **OK** while powering on until the updater
   starts. Keep the battery and card in place until it finishes.
4. Power off, delete `DCOLYMP/E1479999.BIN` from the card, keep `OM3MOD/`,
   then boot normally.

Games is now under **COLOR 1–4 → Picture Mode → Games**; ES sound is under
**MENU → Setup → Information Record → ES sound**. To return to stock, copy
`restore/DCOLYMP/E1479999.BIN` to the same card path and repeat the updater.
Full steps, verification and rollback: [install guide](shutter_sound/INSTALL.md).

## Games

Set the creative dial to **COLOR 1–4**, then open **Picture Mode → Games**
from the Super Control Panel. Live-view display updates pause while the
launcher or a game is open and resume on exit. MENU backs up one level.
A shutter half-press returns to shooting.

| Game | Controls |
| --- | --- |
| 2048 | Arrows/dials; INFO restarts |
| Minesweeper | Arrows/dials, OK to open, INFO to flag |
| Mini Mario | Left/right; Up/OK to jump; scrolling map |
| Breakout | Left/right paddle; OK launches |
| Flappy | Tap or Up/OK; slow pace, variable pipe spacing, live distance |

Flappy accepts touch and button controls. Lift your finger before pressing MENU.

## ES sound

Open **MENU → Setup → page 2, Information Record → ES sound**. Press OK,
use the arrows to pick **Silent**, **5D**, **D850**, **Ciallo**, **Man** or
**Custom**, and press OK again to select. Use Silent Single or Silent
Sequential for capture playback. **5D** and **D850** are built in. **Ciallo**,
**Man** and **Custom** load their matching WAV files from `OM3MOD` on the SD
card. **Silent** is the startup default. [Prepare SD sounds](shutter_sound/SOUND_FILES.md)

## Build and develop

- [Build and test the latest image](docs/DEVELOPMENT.md)
- [Touch development guide](docs/TOUCH_DEVELOPMENT_GUIDE.md)

After setting up the external inputs in the development guide:

```powershell
py -3 shutter_sound/prepare_presets.py --fetch --public-only
py -3 build/extras.py all
```

## Layout

```text
build/                 manifest, build/test driver, packager, verifier
native/                camera assembly, assets, low-level build/setup
shutter_sound/         native player, SD loader, format converter and audio replay
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

The Extras builder starts from the r5 game image and adds the live-view
display pause, native Setup row and SD sound loader.

## License

Apache-2.0; see [LICENSE](LICENSE) and [NOTICE](NOTICE). Caduceus is an external
Apache-2.0 dependency. Manufacturer firmware is not redistributed in this repository.
