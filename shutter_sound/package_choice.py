"""Package the exact emulator-verified Silent Single and Extras trial."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

from bank import decode
from build_choice import ROOT, SD_OUT, SINGLE_OUT, SD_MAX_BYTES, WORK

sys.path.insert(0, str(ROOT / "menu_extension"))
from package_trial import package_trial


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sd", action="store_true")
    parser.add_argument("--include-local-sounds", action="store_true")
    args = parser.parse_args()
    if args.include_local_sounds and not args.sd:
        parser.error("--include-local-sounds requires --sd")
    here = Path(__file__).resolve().parent
    out = SD_OUT if args.sd else SINGLE_OUT
    proof = out / "sound-preview.json"
    checks = json.loads(proof.read_bytes()).get("checks", [])
    results = {row["label"]: row for row in checks}
    if any(results.get(label, {}).get("native_frames") != count for label, count in [
        ("5D", 2880), ("D850", 2880), ("Mechanical Single", 0),
        ("Silent Single", 2880), ("Silent", 0), ("Silent Single with Silent selected", 0)
    ]):
        raise ValueError("The native chooser replay must verify preview, exposure and Silent")
    files = {}
    if args.sd:
        if args.include_local_sounds:
            for name, file in (("Ciallo", "ciallo-full"), ("Man", "man-full")):
                preset = decode((WORK / "shutter-sound/presets" / (file + ".BIN")).read_bytes())
                digest = hashlib.sha256(preset["pcm"]).hexdigest()
                if len(preset["wav"]) > SD_MAX_BYTES or results.get(name, {}).get("pcm_sha256") != digest:
                    raise ValueError(f"SD replay must verify the exact {name} file")
                files[f"card/OM3MOD/{name.upper()}.WAV"] = preset["wav"]
        if not results.get("Silent Single with Custom selected", {}).get("native_frames"):
            raise ValueError("The SD replay must verify Custom on exposure")
        files.update({"SOUND_FILES.md": (here / "SOUND_FILES.md").read_bytes(),
                      "tools/convert.py": (here / "convert.py").read_bytes(),
                      "tools/bank.py": (here / "bank.py").read_bytes()})
    instructions = here / ("TRIAL_SD.md" if args.sd else "TRIAL.md")
    package_trial(out, instructions, (proof, here / "SOURCES.md"), files)
