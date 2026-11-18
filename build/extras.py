"""Build, test and package the current OM-3 Games and SD-sound trial."""

import argparse
import os
from pathlib import Path
import subprocess
import sys

import manifest


ROOT = Path(__file__).resolve().parents[1]
def run(program, *args, env=None):
    print("==>", *args, flush=True)
    subprocess.run([program, *args], cwd=ROOT, env=env, check=True)


def build(flags):
    data = manifest.load()
    game = data["image"]
    output = ROOT / game["output_dir"]
    if not all((output / name).is_file() for name in ("row-main.bin", "build.json")):
        run(sys.executable, game["builder"], *game["builder_args"],
            env=dict(os.environ, **game["environment"]))
    run(sys.executable, "shutter_sound/build_native.py", *flags)


def test(diagnostics, flags):
    directory = "diagnostics" if diagnostics else "native"
    out = f"work/shutter-sound/{directory}"
    env = dict(os.environ, OM3_FLAPPY_BUILD=out)
    if not (ROOT / "work/shutter-sound/audio-map.json").is_file():
        run("node", "shutter_sound/emulator/map_audio.mjs")
    run("node", "shutter_sound/emulator/probe.mjs", "--choice", *flags,
        f"--report={out}/sound-preview.json")
    run("node", "tests/test_picture_games.mjs", env=env)
    for name in ("test_flappy_touch_reply.py", "test_flappy.py", "test_flappy_outside.py"):
        run(sys.executable, "tests/" + name, env=env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=("all", "build", "test", "package"), nargs="?", default="all")
    parser.add_argument("--include-local-sounds", action="store_true",
                        help="include the tested Ciallo and Man WAV files in the local archive")
    parser.add_argument("--diagnostics", action="store_true",
                        help="build a separate image with the on-camera audio readout")
    args = parser.parse_args()
    flags = ["--diagnostics"] if args.diagnostics else []
    if args.step in ("all", "build"):
        build(flags)
    if args.step in ("all", "test"):
        test(args.diagnostics, flags)
    if args.step in ("all", "package"):
        local = ["--include-local-sounds"] if args.include_local_sounds else []
        run(sys.executable, "shutter_sound/package_choice.py", *flags, *local)


if __name__ == "__main__":
    main()
