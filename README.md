# OM-3 Extras

Five native games and selectable electronic shutter sounds for the OM SYSTEM
OM-3, firmware 1.1 (E147 build 1100), based on
[Caduceus for OM-3](https://github.com/androidfanman/caduceus-om3) v0.26.2.

Set the creative dial to **COLOR 1–4**, then open **Picture Mode → Games**
from the Super Control Panel. MENU backs up one level. A shutter half-press
returns to shooting.

| Game | Controls |
| --- | --- |
| 2048 | Arrows/dials; INFO restarts |
| Minesweeper | Arrows/dials, OK to open, INFO to flag |
| Mini Mario | Left/right; Up/OK to jump; scrolling map |
| Breakout | Left/right paddle; OK launches |
| Flappy | Tap or Up/OK; slow pace, variable pipe spacing, live distance |

Only Flappy uses touch. The r5 Picture Mode launcher is the camera-tested
touch baseline. [Current status and limits](docs/STATUS.md)

Open **MENU → Setup → page 2, Information Record → ES sound**. Press OK,
use the arrows to pick **Silent**, **5D**, **D850**, **Ciallo**, **Man** or
**Custom**, and press OK again to select. Use Silent Single or Silent
Sequential for capture playback. The last three choices load from `OM3MOD`
on the SD card.

## Start here

- [Install, use Games and ES sound, and restore stock](shutter_sound/TRIAL_NATIVE.md)
- [Sound filenames, format, size limits, and conversion](shutter_sound/SOUND_FILES.md)
- [Build and test the latest image](docs/DEVELOPMENT.md)
- [Touch development guide](docs/TOUCH_DEVELOPMENT_GUIDE.md)
- [Earlier r5 Picture Mode install](docs/INSTALL_FIVE_GAMES.md)

After setting up the external inputs in the development guide:

```powershell
py -3 shutter_sound/prepare_presets.py --fetch --public-only
py -3 build/extras.py all
```

## Layout

```text
build/                 manifest, build/test driver, packager, verifier
menu_extension/        menu replays and earlier Setup launcher trial
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

The Extras builder starts from the r5 game image and adds the native Setup
row, capture hooks and SD sound loader. Firmware,
generated packages, and personal audio files stay out of Git.

## License

Apache-2.0; see [LICENSE](LICENSE) and [NOTICE](NOTICE). Caduceus is an external
Apache-2.0 dependency. Manufacturer firmware is not redistributed in this repository.
