# OM-3 SD shutter sounds

Put the WAV files in **OM3MOD** at the root of the camera's SD card.
Open **MENU → Setup → Information Record → ES sound**. Press OK to edit,
use the arrows to choose a sound, and press OK to load it. Use **Silent
Single** or **Silent Sequential** to hear it during capture. Choose **Silent**
to turn the added sound off.

| ES sound choice | SD file | Included duration |
| --- | --- | --- |
| Ciallo | `OM3MOD/CIALLO.WAV` | 908 ms, supplied in the local trial |
| Man | `OM3MOD/MAN.WAV` | 547 ms, supplied in the local trial |
| Custom | `OM3MOD/CUSTOM.WAV` | Up to 1 second, supplied by you |

5D and D850 are built in. Each is 60 ms. The camera loads SD sounds when
you press OK and keeps the successful selection in memory until power-off.
After replacing a file, select its menu entry again to load the new sound.

- **No WAV on card** means the camera could not open the file at the listed path.
  Check the card and filename. The requested sound stays unselected.
- **Invalid WAV** means the file failed the format or size check. Convert it
  with the included tool. If this read replaced an active SD clip, the
  camera goes back to Silent.
- **Player busy** means an audio player still owns the buffer. Let playback
  finish, then press OK again.

## Preparing CUSTOM.WAV

From the extracted trial folder, with Python 3 installed, run this command.
Replace `X:` with the SD drive letter.

```powershell
py -3 tools/convert.py --sd --input "my-sound.wav" --out "X:\OM3MOD\CUSTOM.WAV"
```

The input can be a **16-bit PCM WAV**, mono or stereo, at **8–192 kHz**.
For an MP3, M4A, or other format, export it as a 16-bit PCM WAV in an audio
editor first. Trim the clip to at most one second. The converter removes
leading silence, applies short fades, limits the peak to about −6 dBFS,
and writes the camera's WAV metadata. It reports an error if the result
exceeds the limit.

| Camera-ready WAV requirement | Value |
| --- | --- |
| Format | RIFF/WAVE, signed 16-bit little-endian PCM |
| Channel count and sample rate | 2 channels at 48,000 Hz |
| Size of a stereo sample frame | 4 bytes |
| Data rate | 192,000 bytes per second |
| Length limit | 48,000 frames, 1,000 ms |
| Maximum WAV file size | 192,112 bytes, including the 112-byte header |
| Internal layout | Exact header from `convert.py --sd`, including the camera's short-sound key and a 16-byte-aligned PCM start |

Use Ciallo and Man as supplied. The short 5D and D850 clips suit
closely spaced shots. Continuous shooting may skip sound requests.
