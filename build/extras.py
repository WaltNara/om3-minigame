"""Build, test and package the current OM-3 Games and SD-sound trial."""

import argparse
import os
from pathlib import Path
import subprocess
import sys

import manifest


ROOT = Path(__file__).resolve().parents[1]
SD_DIR = "work/shutter-sound/sd"
ENV = dict(os.environ, OM3_MENU_BUILD=SD_DIR, OM3_FLAPPY_BUILD=SD_DIR)


def run(program, *args, env=ENV):
    print("==>", *args, flush=True)
    subprocess.run([program, *args], cwd=ROOT, env=env, check=True)


def build():
    data = manifest.load()
    game = data["image"]
    output = ROOT / game["output_dir"]
    if not all((output / name).is_file() for name in ("row.bin", "build.json")):
        run(sys.executable, game["builder"], *game["builder_args"],
            env=dict(os.environ, **game["environment"]))
    run(sys.executable, "menu_extension/build_menu.py")
    run(sys.executable, "shutter_sound/build_choice.py", "--sd")


def test():
    if not (ROOT / "work/shutter-sound/audio-map.json").is_file():
        run("node", "shutter_sound/emulator/map_audio.mjs")
    run("node", "shutter_sound/emulator/probe.mjs", "--choice", "--sd",
        f"--report={SD_DIR}/sound-preview.json")
    run("node", "menu_extension/test_games.mjs")
    for name in ("test_flappy_touch_reply.py", "test_flappy.py", "test_flappy_outside.py"):
        run(sys.executable, "tests/" + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=("all", "build", "test", "package"), nargs="?", default="all")
    parser.add_argument("--include-local-sounds", action="store_true",
                        help="include the tested Ciallo and Man WAV files in the local archive")
    args = parser.parse_args()
    if args.step in ("all", "build"):
        build()
    if args.step in ("all", "test"):
        test()
    if args.step in ("all", "package"):
        local = ["--include-local-sounds"] if args.include_local_sounds else []
        run(sys.executable, "shutter_sound/package_choice.py", "--sd", *local)


if __name__ == "__main__":
    main()
