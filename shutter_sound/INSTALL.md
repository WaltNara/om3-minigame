# OM-3 Games and ES sound

For OM SYSTEM OM-3 firmware 1.1, E147 build 1100. The package includes
Caduceus v0.26.2, five Picture Mode games with paused live-view display, and
the ES sound setting. The documented camera test applies to `8bf67c77473a`.

## Install or update

1. Fully charge the battery and extract the ZIP. Copy the contents of `card/`
   to the SD root. This places the updater at `DCOLYMP/E1479999.BIN` and the
   matching `GUIDES.BIN`, `LABELS.BIN` and `TONES.BIN` in `OM3MOD`. Keep
   photos and any personal files already on the card. Use `card/` to install
   and `restore/` only to return to stock.
2. Run the verifier from the extracted folder, substituting your SD drive
   for `X:\`.

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\Verify-Package.ps1 -CardRoot X:\ -Mode Install
   ```

3. Eject the card and put it in the powered-off camera. Hold **OK** while
   turning it on, and keep holding until the update starts. A steady lamp
   indicates writing. Leave the battery and card in place until the lamp
   blinks to indicate completion. `UPSTREAM_INSTALL.md` describes the lamp
   sequence and troubleshooting.
4. Power off. Remove `DCOLYMP/E1479999.BIN` from the card on the PC and keep
   `OM3MOD` on the card. Start the camera normally.

## ES sound

Open **MENU → Setup (wrench) → page 2, Information Record → ES sound**.
Press **OK** or **Right** to edit. Use the arrows to cycle through **Silent**,
**5D**, **D850**, **Ciallo**, **Man** and **Custom**. Press **OK** to load and
select the displayed choice. Press **MENU** to cancel an edit.

Return to shooting with a shutter half-press. Use **Silent Single** or
**Silent Sequential** (heart icon) to hear the selection on capture. Choose
**Silent** to disable the added sound. Power-off resets the selection to Silent.
The camera validates the three SD choices on OK and shows `No WAV on card`,
`Invalid WAV` or `Player busy` when it cannot load the file. See `SOUND_FILES.md`
for paths and conversion.

5D and D850 are built in and last 60 ms each. The package built with
`--include-local-sounds` also carries the supplied Ciallo and Man files.
This build fixes the first-shot-only volume drop by restoring the playback
gain each time a new sound starts. The ES sound row controls clip selection.
On bursts, a new request can restart a long clip after the queued audio
plays. At high frame rates, some requests may be combined.

## Games

Set the creative dial to **COLOR 1–4**. In the Super Control Panel, open
**Picture Mode**, scroll to **Games**, and press **OK**. Use the arrows and
OK to pick a game. MENU returns to the launcher. A shutter half-press leaves
Games and returns to shooting. Lift your finger before pressing MENU in Flappy.
Live-view display updates pause in the launcher and games and resume
when you return to shooting.

| Game | Controls |
| --- | --- |
| 2048 | Arrows or dials to move, INFO to restart |
| Minesweeper | Arrows or dials to move, OK to open, INFO to flag |
| Mini Mario | Left and right to move, Up or OK to jump |
| Breakout | Left and right to move the paddle, OK to launch |
| Flappy | Tap, Up, or OK to flap |

## Restore stock

Copy `restore/DCOLYMP/E1479999.BIN` to the card at the same path. Verify it
with the command above using `-Mode Restore`, then follow the same updater
steps. Removing the SD files alone leaves the installed firmware in place.
