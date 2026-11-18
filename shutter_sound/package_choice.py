"""Package the exact image that passed the Picture Mode and ES sound replays."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import zipfile

from bank import decode
from build_native import DIAG_OUT, OUT, SD_MAX_BYTES, SOURCE, WORK
from memory import ROOT

sys.path.insert(0, str(ROOT / "build"))
import manifest
from package import firmware_container


def package_extras(out, include_local_sounds):
    meta = json.loads((out / "build.json").read_text())
    main = (out / "row-main.bin").read_bytes()
    digest = hashlib.sha256(main).hexdigest()
    report = json.loads((out / "replay.json").read_text())
    if (report.get("status"), report.get("sha256"), meta["candidate_sha256"]) != ("pass", digest, digest):
        raise ValueError("The game and menu replay must pass for this candidate")
    if [row.get("permit") for row in report.get("previewGate", [])] != [1, 0, 0, 1, 1]:
        raise ValueError("The game preview gate must pass entry and exit checks")
    regressions = {}
    for folder in ("touch-reply", "outside", "validation"):
        relative = folder + "/validation.json"
        blob = (out / relative).read_bytes()
        manifest.check_report(json.loads(blob), digest)
        regressions["evidence/" + relative] = blob
    data = manifest.load()
    container, spec = firmware_container(data, main)
    release = ROOT / data["install"]["release_dir"]
    card = {Path(name.lstrip("*")).name: checksum for checksum, name in
            (line.split(maxsplit=2)[:2] for line in (release / "SHA256SUMS").read_text().splitlines() if line.strip())}
    files = {
        "card/DCOLYMP/E1479999.BIN": container,
        "restore/DCOLYMP/E1479999.BIN": (ROOT / "work" / spec["stock_file"]).read_bytes(),
        "Verify-Package.ps1": (ROOT / "build/Verify-Package.ps1").read_bytes(),
        "README.md": (SOURCE / "INSTALL.md").read_bytes(),
        "UPSTREAM_INSTALL.md": (ROOT / "vendor/caduceus-om3/docs/INSTALL.md").read_bytes(),
        "LICENSE": (ROOT / "LICENSE").read_bytes(),
        "NOTICE": (ROOT / "NOTICE").read_bytes(),
        "evidence/replay.json": (out / "replay.json").read_bytes(),
        **regressions,
    }
    for name in data["install"]["version_matched_card_files"]:
        blob = (release / name).read_bytes()
        if hashlib.sha256(blob).hexdigest() != card[name]:
            raise ValueError(f"Unexpected card asset {name}")
        files["card/OM3MOD/" + name] = blob
    pictures = ("setup", "sound", "launcher", "2048", "flappy")
    for name in pictures:
        files["evidence/" + name + ".png"] = (out / (name + ".png")).read_bytes()

    proof = (out / "sound-preview.json").read_bytes()
    playback = json.loads(proof)
    if (playback.get("status"), playback.get("image_sha256")) != ("passed", digest):
        raise ValueError("The native sound replay must pass for this candidate")
    results = {row["label"]: row for row in playback["checks"]}
    expected = [("Mechanical Single", 0), ("Single D850", 2880),
                ("Silent Single with Silent selected", 0), ("Custom", 48000),
                *((f"Single 5D {i}", 2880) for i in (1, 2, 3))]
    if any(results.get(label, {}).get("native_frames") != count for label, count in expected):
        raise ValueError("The sound replay must verify selection, repeated captures and Silent")
    if results.get("Sequential long-clip restart", {}).get("attacks") != 3:
        raise ValueError("The sound replay must verify consecutive burst restarts")
    sequential = results.get("Sequential Ciallo after burst", {})
    if not sequential.get("native_frames") or sequential.get("pcm_sha256") != results.get("Ciallo", {}).get("pcm_sha256"):
        raise ValueError("The same preset must play again after a completed burst")
    recovery = results.get("TX completion loss", {})
    if recovery.get("dropped") != 1 or not recovery.get("subsequent_playback"):
        raise ValueError("The sound replay must verify playback after a lost TX notification")
    start = results.get("Audio start rejection", {})
    if start.get("rejected") != 1 or not start.get("subsequent_playback"):
        raise ValueError("The sound replay must verify recovery after an audio start rejection")
    resources = results.get("Audio resource release", {})
    if resources.get("opened") != resources.get("closed") or resources.get("idle_checks", 0) < 20:
        raise ValueError("The sound replay must verify native audio resources are released")
    if results.get("Fresh volume per playback", {}).get("requests", 0) < 20:
        raise ValueError("The sound replay must verify fresh volume values on repeated requests")
    diagnostics = meta.get("diagnostics", False)
    if diagnostics:
        rows = results.get("On-camera audio status", {}).get("rows", [])
        if len(rows) != 4:
            raise ValueError("The sound replay must verify the camera readout")
        files["ES_STATUS.md"] = (SOURCE / "ES_STATUS.md").read_bytes()
        files["evidence/audio-status.png"] = (out / "audio-status.png").read_bytes()
    files.update({"evidence/shutter-sound.json": proof,
                  "SOUND_SOURCES.md": (SOURCE / "SOURCES.md").read_bytes(),
                  "SOUND_FILES.md": (SOURCE / "SOUND_FILES.md").read_bytes(),
                  "tools/convert.py": (SOURCE / "convert.py").read_bytes(),
                  "tools/bank.py": (SOURCE / "bank.py").read_bytes()})
    if include_local_sounds:
        for name, stem in (("Ciallo", "ciallo-full"), ("Man", "man-full")):
            preset = decode((WORK / "shutter-sound/presets" / (stem + ".BIN")).read_bytes())
            pcm_digest = hashlib.sha256(preset["pcm"]).hexdigest()
            if len(preset["wav"]) > SD_MAX_BYTES or results.get(name, {}).get("pcm_sha256") != pcm_digest:
                raise ValueError(f"SD replay must verify the exact {name} file")
            files[f"card/OM3MOD/{name.upper()}.WAV"] = preset["wav"]
    files["SHA256SUMS"] = "".join(f"{hashlib.sha256(blob).hexdigest()}  {name}\n"
                                  for name, blob in sorted(files.items())).encode("ascii")
    kind = "om3-es-status" if diagnostics else "om3-extras"
    suffix = "-local" if include_local_sounds else ""
    dest = ROOT / "artifacts" / f"{kind}-{digest[:12]}{suffix}.zip"
    dest.parent.mkdir(exist_ok=True)
    # Publish only a completely written and verified ZIP. Each main image gets
    # its own filename, including rebuilds of a previously tested candidate.
    with tempfile.TemporaryDirectory(dir=dest.parent) as tmp:
        archive = Path(tmp) / dest.name
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as output:
            for name, blob in files.items():
                output.writestr(name, blob)
        with zipfile.ZipFile(archive) as result:
            if set(result.namelist()) != files.keys() or any(
                    result.read(name) != blob for name, blob in files.items()):
                raise ValueError("Archive readback differs")
        archive.replace(dest)
    print(dest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-local-sounds", action="store_true")
    parser.add_argument("--diagnostics", action="store_true")
    args = parser.parse_args()
    package_extras(DIAG_OUT if args.diagnostics else OUT, args.include_local_sounds)
