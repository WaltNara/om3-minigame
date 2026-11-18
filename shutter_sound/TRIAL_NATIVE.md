# OM-3 Games and ES sound

For OM SYSTEM OM-3 firmware 1.1, E147 build 1100. The package includes
Caduceus v0.26.2, the five-game Picture Mode launcher, and a Setup sound row.

1. Charge the battery. Extract the package and copy the contents of `card/`
   to the root of the SD card. Keep personal files in `OM3MOD` and `DCIM`.
2. Verify the card with `Verify-Package.ps1 -CardRoot X:\ -Mode Install`,
   substituting the card's drive letter for `X:`.
3. Put the card in the powered-off camera. Hold OK while turning it on.
   Wait for the update to finish. `UPSTREAM_INSTALL.md` explains the lamp
   indications. Leave the card and battery in place during the update.
4. Power off and remove `DCOLYMP/E1479999.BIN` from the card on the PC.
   Keep `OM3MOD` on the card.

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

On fast bursts, a newer request can replace the rest of a long clip once the
already buffered audio plays. OM-Emu checks this behavior at the native
capture call sites. Repeated playback on the camera remains to be confirmed.
To check the former first-shot failure, select one preset, take three shots
with pauses between them, and listen for the same sound each time. Then try
two separate bursts with the preset still selected.

## Games

Set the creative dial to **COLOR 1–4**. In the Super Control Panel, open
**Picture Mode**, scroll to **Games**, and press **OK**. Use the arrows and
OK to pick a game. MENU returns to the launcher. A shutter half-press leaves
Games and returns to shooting. Lift your finger before pressing MENU in Flappy.
The camera skips live-view display updates while Games owns the screen.

| Game | Controls |
| --- | --- |
| 2048 | Arrows or dials to move, INFO to restart |
| Minesweeper | Arrows or dials to move, OK to open, INFO to flag |
| Mini Mario | Left and right to move, Up or OK to jump |
| Breakout | Left and right to move the paddle, OK to launch |
| Flappy | Tap, Up, or OK to flap |

## Restore stock

Copy `restore/DCOLYMP/E1479999.BIN` to the card at the same path. Verify it
with `-Mode Restore`, then follow the same updater steps.
