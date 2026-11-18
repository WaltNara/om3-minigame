# Shutter preset sources

Prepared 2026-11-18. The built-in sounds use CC0 shutter recordings. The
preset names follow the camera models identified by the recordists.

| Preset | Creator and source | Preparation |
| --- | --- | --- |
| Canon 5D | [chrisvink, shutter click Canon EOS 5D Mark II or III](https://freesound.org/people/chrisvink/sounds/270435/) | Public HQ MP3 preview of a single shutter click; exact II/III model is uncertain. 60 ms burst and approximately 164 ms single-shot edits. |
| Nikon D850 | [matikuki, D850 Nikon Camera DSLR Shutter](https://freesound.org/people/matikuki/sounds/567228/) | Public HQ MP3 preview containing single shots and 7 fps bursts; recorded with a Zoom H4n Pro. Select the first significant onset for 60 ms burst and 300 ms single-shot excerpts. |
| Ciallo | User-supplied `Ciallo.m4a` | Approximately 908 ms after leading-silence removal. Preserve the remaining clip. |
| Man | User-supplied `man.MP3` | Approximately 547 ms after leading-silence removal. Preserve the remaining clip. |
| Off / Silent | Original electronic-shutter behavior | No audio file or playback request. Default selection. |

Both Freesound pages explicitly identify
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). Source URLs and
download SHA256 values are pinned in `presets.json`. Converted files include
credits in the generated directory. Changes include MP3 decoding, resampling to
PCM16 stereo 48 kHz, onset selection, cropping for the camera variants, peak
limiting and edge fades. These are derived previews; the original high-resolution
WAV downloads require a Freesound login and were not downloaded.

The two personal recordings are retained locally and excluded from source
publication; no redistribution license has been assumed for them.

## GitHub projects examined

[WonderLantern Z5](https://github.com/WonderLantern/wonder-lantern-z5) includes five
test WAVs. Its [notice](https://github.com/WonderLantern/wonder-lantern-z5/blob/main/NOTICE.md)
states the maintainer provided open-source audio without copyright restrictions,
but does not establish specific professional camera models for those recordings.
[WonderLantern Z6](https://github.com/WonderLantern/WonderLantern-z6/blob/main/README.en.md)
identifies its camera examples as a generic film camera and a Soviet leaf shutter.
The selected Canon/Nikon recordings have clearer camera provenance. No firmware
or audio was copied from those GitHub projects.

## Continuous shooting

The firmware embeds the 60 ms 5D and D850 edits. During supported bursts, a
new shot can restart a clip once buffered audio plays. The latest request
takes precedence when several arrive before the next refill. Generated
`*-10fps.wav` and `*-20fps.wav` files are offline listening previews.

## Reproduce and preview

```powershell
py -3 shutter_sound/prepare_presets.py --fetch
py -3 shutter_sound/test_presets.py
py -3 shutter_sound/test_retrigger.py
```

The tool uses FFmpeg from PATH, an explicit `--ffmpeg` path, or `imageio-ffmpeg`
under `work/shutter-sound/python-deps`.

Output: `work/shutter-sound/presets/`, containing one bank per sound variant,
ordinary WAV listening previews, 10/20 fps previews, `CREDITS.txt`, and a generated
`presets.json` with durations, edits and hashes. Silent is represented as a null
bank. The player uses one buffer for the selected SD WAV.
