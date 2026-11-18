# OM-3 Extras camera trial

This build targets the standard OM SYSTEM OM-3, firmware 1.1, E147 build 1100,
with Caduceus v0.26.2. Its full-menu host has been tested in OM-Emu. Physical
touch response, display switching, power consumption and hardware stability
still need a camera trial.

## Using Extras

Press MENU, open the Setup tab (wrench), then page 2, Information Record.
Select the fourth row, **Extras**, and press OK. Use the arrow keys to choose
**Games** or **Shutter sound**. MENU backs up one level. A shutter half-press
returns to shooting. The creative dial can stay in its usual position.

Games contains 2048, Minesweeper, Mini Mario, Breakout and Flappy. In Flappy,
tap or press Up or OK to flap. The other games use their buttons. Lift your
finger before a MENU keypress. The other Extras screens consume touches to
protect the native settings underneath.

Shutter sound offers Silent, 5D, D850, Ciallo and Man. OK remembers a preference
until power-off. MENU cancels browsing. The default is Silent. Electronic
shutter playback stays silent for every choice in this build.

## Installing and restoring

1. Verify the camera model and firmware version. Fully charge the battery and
   back up your photos and settings. Extract the entire local archive on the PC.
2. Run `Verify-Package.ps1` in the extracted folder. Copy the **contents of
   card/** to the SD root. Keep the separate `restore/` folder on the PC.
   For example, for an SD card at `X:\`, run
   `.\Verify-Package.ps1 -CardRoot X:\ -Mode Install` after copying.
3. With the camera powered off, insert the card. Hold OK as you power on until
   the update starts. Maintain power and leave the card in place until writing
   finishes and the completion indication appears. The bundled
   `UPSTREAM_INSTALL.md` describes the indicators.
4. Power off. Remove the updater `DCOLYMP/E1479999.BIN` from the SD on the PC.
   Keep the three `OM3MOD` files, then boot the camera normally.
5. To restore stock, use the copy of `DCOLYMP/E1479999.BIN` from `restore/`,
   verify with `-Mode Restore`, and follow the same update procedure. The
   previously accepted r5 package is a separate route back to Picture Mode Games.
