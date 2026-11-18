# Development

## Setup

Native builds currently use Python 3, Node.js and MN10300 binutils on Windows.
Source-only checks also run on Linux. External inputs are not in Git.

From the repository root, check out the pinned dependencies and prepare the
official firmware and assembler inputs.

```powershell
git clone https://github.com/androidfanman/caduceus-om3.git vendor/caduceus-om3
git -C vendor/caduceus-om3 checkout f4d2569eb46817795ec5ffaf931ba058d2c0d029
git clone https://github.com/flatpanda/om-emu.git work/om-emu
git -C work/om-emu checkout 88b753ddb9c0fac35366802133e849600aa519d5
py -3 native/fetch_inputs.py stock
py -3 native/fetch_inputs.py binutils
```

In an MSYS/MinGW shell, run `bash native/build_toolchain.sh` from the
repository root. Supply GCC and make on PATH or set `OM3_MAKE`.
The output is `work/toolchain/`. The combined firmware and emulator use E147.
The test runner also uses E143 to regenerate the audio address map on a
fresh checkout. [Pinned OM-Emu setup reference](https://github.com/flatpanda/om-emu/blob/88b753ddb9c0fac35366802133e849600aa519d5/emu/README.md)

Return to PowerShell to prepare the harness and paired card.

```powershell
$env:OM_EMU_MODEL='E147'
py -3 native/windows_emu.py
node work/om-emu/emu/bin/fetch-fw.mjs --model E147 --bin work/OLY_E_147_1100_0000_0000.BIN
node work/om-emu/emu/bin/fetch-fw.mjs --model E143
py -3 native/build.py
py -3 native/prepare_emulator.py
$emu = ([Uri](Resolve-Path work/om-emu/emu).Path).AbsoluteUri
node work/native-build/blank.mjs $emu work/native-build/main.bin blank work/native-build/blank-check.json work/native-build/blank.omsd
py -3 tests/test_emulator.py seed
py -3 tests/test_emulator.py validate
```

`native/build.py` creates the harness baseline. The installable combined
image comes from `build/extras.py`. The local replay used Node.js 24.18.0.

## Current workflow

Prepare the built-in 5D and D850 WAVs once. FFmpeg must be on PATH, or pass its
location with `--ffmpeg`. The public build uses the pinned downloads and does
not need personal audio.

```powershell
py -3 tools/check_repository.py
py -3 shutter_sound/prepare_presets.py --fetch --public-only
py -3 build/extras.py all
```

`build/extras.py` also accepts `build`, `test` or `package`. It starts from
the exact r5 game image in `work/current-games`, adds the display pause and
native **ES sound** setting, and writes `work/shutter-sound/native/row-main.bin`.
The tests cover repeated volume requests, single and burst playback, resource
release, SD sound validation, the live-view pause, and touch and outside-game
regressions. Packaging verifies the image hash against those reports. The
resulting `artifacts/om3-extras-<hash>.zip` includes the updater, matching card
files, the stock updater and the install guide.

To include the supplied personal sounds in a `-local.zip` package, put
`Ciallo.m4a` and `man.MP3` in `shutter_sound/`, then use:

```powershell
py -3 shutter_sound/prepare_presets.py --fetch
py -3 build/extras.py all --include-local-sounds
```

Keep firmware ZIPs and personal audio local. The optional `--diagnostics`
flag builds a separate ES sound readout. Use `build/build.py` for the earlier
games-only r5 workflow. [Install guide](../shutter_sound/INSTALL.md) ·
[ES sound diagnostics](../shutter_sound/ES_STATUS.md) ·
[Games-only workflow](architecture/BUNDLE_ARCHITECTURE.md)

## Adding/changing a game

Native assembly and assets remain grouped by filename in `native/`, keeping
camera-tested includes/imports simple. `combined_host.s` owns input/paint,
`combined_menu.s` owns navigation, and `combined_bridge.s` posts GUI ticks.
`flappy_build.py` generates fifth-game hosts with checked string replacements;
this is a maintenance constraint, not a plugin interface.

1. Implement bounded core/render/assets with a unique state ID (2-6 are taken).
   Extend startup/input/paint/launcher dispatch and linker inputs.
2. Register sources, controls, tests and honest validation scope in
   `build/games.json`. Tests must name the exact image they ran.
3. Budget loaded bytes including alignment/tables. r5 uses 232 KiB with 24 KiB
   spare. Keep at least 16 KiB reserve under the 256 KiB ceiling.
4. Prove entry/input/render/exits, run relevant checks, package under a new name,
   and record camera results in `docs/STATUS.md`.

## Implementation rules

- GUI task alone owns game/render state. Timers post messages; cancel them on
  exit and discard stale generations.
- Preserve CALL/CALLS frames and registers; never retain event payload pointers.
- Bound RLE output and scanlines; use proven surfaces/uncached aliases. Emulator
  instruction counts are not camera rendering timings.
- Complete one native reply per consumed touch; clear contact on endings 3/4/5.
  Test through the waiting application producer. See the [touch guide](TOUCH_DEVELOPMENT_GUIDE.md).
- Keep hardware reports separate from local tests. Display-switch recovery and
  sustained stability remain open. Do not raise frame rate speculatively.

See [integration](architecture/COMBINING_GAMES.md) and
[bundle workflow](architecture/BUNDLE_ARCHITECTURE.md).
