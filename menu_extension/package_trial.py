"""Make a local camera-trial archive from the exact image that passed the menu replay."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import zipfile

from build_menu import OUT, ROOT

sys.path.insert(0, str(ROOT / "build"))
import manifest
from package import firmware_container


def package_trial(out=OUT, instructions=None, audio_evidence=None, extra_files=None):
    meta = json.loads((out / "build.json").read_text())
    main = (out / "row-main.bin").read_bytes()
    digest = hashlib.sha256(main).hexdigest()
    report = json.loads((out / "replay.json").read_text())
    if (report.get("status"), report.get("sha256"), meta["candidate_sha256"]) != ("pass", digest, digest):
        raise ValueError("The full-menu replay must pass for this candidate")
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
        "README.md": (instructions or Path(__file__).with_name("TRIAL.md")).read_bytes(),
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
    for name in ("setup", "extras", "sound", "launcher", "2048", "flappy"):
        files["evidence/" + name + ".png"] = (out / (name + ".png")).read_bytes()
    if audio_evidence is not None:
        proof, credits = audio_evidence
        playback = json.loads(proof.read_bytes())
        if (playback.get("status"), playback.get("image_sha256")) != ("passed", digest):
            raise ValueError("The native sound replay must pass for this candidate")
        files["evidence/shutter-sound.json"] = proof.read_bytes()
        files["SOUND_SOURCES.md"] = credits.read_bytes()
    if extra_files:
        if files.keys() & extra_files.keys():
            raise ValueError("Extra files overlap the trial package")
        files.update(extra_files)
    files["SHA256SUMS"] = "".join(f"{hashlib.sha256(blob).hexdigest()}  {name}\n"
                                  for name, blob in sorted(files.items())).encode("ascii")
    prefix = ("om3-es-sd-trial" if meta.get("sd_custom") else
              "om3-es-single-trial" if audio_evidence else "om3-extras-trial")
    dest = ROOT / "artifacts" / f"{prefix}-{digest[:12]}.zip"
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
    package_trial()
