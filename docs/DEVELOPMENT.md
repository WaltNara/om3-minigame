# Development

## Setup

Native builds currently use Python 3, Node.js and MN10300 binutils on Windows.
Source-only checks also run on Linux. External inputs are not in Git.

1. Clone Caduceus into `vendor/caduceus-om3`, checking out commit
   `f4d2569eb46817795ec5ffaf931ba058d2c0d029` (v0.26.2).
2. Obtain your official OM-3 1.1 firmware. `py -3 native/fetch_inputs.py stock`
   downloads/verifies the upstream-pinned file into `work/`.
3. Fetch sources with `py -3 native/fetch_inputs.py binutils`. In an MSYS/MinGW
   shell, run `bash native/build_toolchain.sh`. Supply GCC/make on PATH or set
   `OM3_MAKE`; output is `work/toolchain/`.
4. Obtain OM-Emu under `work/om-emu/emu` using Caduceus's emulator instructions.
   `native/windows_emu.py` provides Windows adaptation. Source-only CI does not
   download the emulator or manufacturer firmware.
5. Run `py -3 native/build.py`, `py -3 native/prepare_emulator.py`, then
   `py -3 tests/test_emulator.py seed` and `py -3 tests/test_emulator.py validate` to prepare the baseline and paired card.
   This setup builder includes the old guessing game as a harness seed;
   it is not the combined release to install.

Before seeding, create the blank card with the generated blank helper:

```powershell
$env:OM_EMU_MODEL='E147'
py -3 native/windows_emu.py
node work/native-build/blank.mjs file:///D:/path/to/project/work/om-emu/emu work/native-build/main.bin blank work/native-build/blank-check.json work/native-build/blank.omsd
```

Replace the file URL with your checkout location. Run this after generating the
helpers, before `test_emulator.py seed` and `validate`.

## Current workflow

Run from the repository root:

```powershell
py -3 tools/check_repository.py
py -3 build/build.py
py -3 build/build.py --verify-existing
py -3 build/package.py --dry-run
py -3 build/package.py --name my-new-release
```

`build/games.json` selects `--flappy-touch`, `work/current-games`, current tests,
docs and evidence. Builder and tests receive the same output path. The driver
writes `bundle-build.json` after checking image/source/report hashes and the
256 KiB loaded budget. Known native report success formats are accepted through
a shared validator; an explicit matching image hash is required.

Current checks cover Flappy physics/render/playability, GUI exits, touch protocol
and outside-game parity. They do not claim exhaustive fresh coverage of the four
other games. Historical per-game scripts remain in `tests/`; see its README.

The reorganized build must match accepted r5 raw bytes. Source-path metadata
changes. The sealed r5 source snapshot, package and rollback stay untouched.
Future gameplay changes need separate camera checks. Packaging uses published
source/docs plus external inputs and generated evidence; it preserves source
paths, checks the firmware container/restore and reads back ZIP hashes. Choose a
new name; releases are never overwritten. Local packages contain firmware and
must not be committed or uploaded as part of source maintenance.

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
