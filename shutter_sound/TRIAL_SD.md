# OM-3 Extras shutter sound SD trial

This trial targets the OM SYSTEM OM-3 E147 with firmware 1.1. It includes
a stock restore. Local packages built with the supplied sounds include
Ciallo and Man in the card folder. Games, the menu, SD files, and audio
playback passed OM-Emu tests. The expanded loader region and speaker
playback still need a test on the physical OM-3.

1. Verify the model and firmware version, fully charge the battery, and
   back up photos and settings.
2. Extract the trial. Copy the contents of `card/` to the SD card root.
   If the archive includes Ciallo and Man, they are in `card/OM3MOD/`. Run
   `Verify-Package.ps1 -CardRoot X:\ -Mode Install` with the card's drive letter.
3. Insert the card with the camera off. Hold OK while powering it on.
   Wait for the update to finish, keeping the card and battery in place.
   See `UPSTREAM_INSTALL.md` for the updater indicators.
4. Power off. Remove `DCOLYMP/E1479999.BIN` from the card on the PC and
   keep the `OM3MOD` folder.
5. Open **MENU → Setup → Information Record → Extras → Shutter sound**.
   Select **Ciallo** or **Man**, then press OK to load and preview it.
   Return to shooting and select **Silent Single** (the heart icon).
   The **Silent** option in Extras turns off the added sound.

`SOUND_FILES.md` lists the exact filenames, audio requirements and the
command for making your own `CUSTOM.WAV`.

## Games

Open **MENU → Setup → Information Record → Extras → Games**. The Setup
tab has a wrench icon, and Information Record is page 2. The creative
dial can stay in its usual position. MENU backs up one screen. A shutter
half-press returns directly to shooting.

| Game | Controls |
| --- | --- |
| 2048 | Arrows or dials, INFO to restart |
| Minesweeper | Arrows or dials, OK to open, INFO to flag |
| Mini Mario | Left and right to move, Up or OK to jump |
| Breakout | Left and right to move the paddle, OK to launch |
| Flappy | Tap, Up, or OK to flap |

Lift your finger before pressing MENU in Flappy. Other games use their
buttons. The emulator records the stock live-view stop request on entering
the menu.

## Restore stock

To restore stock 1.1, copy the file under `restore/DCOLYMP/` to the same
card path, verify with `-Mode Restore`, then repeat the updater steps.
