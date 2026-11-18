# OM-3 Extras electronic shutter sound trial

This trial targets the OM SYSTEM OM-3 E147 on firmware 1.1.
The emulator plays the 60 ms samples through the native sound task.
The camera's exposure timing, the extra section-1 pages and physical
speaker playback need a real-body trial.

1. Press MENU and open Setup (wrench), page 2, Information Record.
2. Open **Extras**, then **Shutter sound**. Select **5D** or **D850** and
   press OK to hear its preview and remember the choice until power-off.
3. Half-press the shutter to return to shooting, then choose **Silent Single**
   (the single-frame icon with a heart) in the camera's drive setting. Take a
   photo to hear the selected clip on exposure start.
4. Select **Silent** in Extras and press OK to clear the choice. MENU cancels
   browsing.

This trial enables sound for Silent Single. Drive modes including Silent
Sequential use their stock behavior. Ciallo and Man are visible while their
full clips await a verified buffer.

## Installing and restoring

1. Verify the model and firmware version, fully charge the battery, and
   back up photos and settings.
2. Extract the archive. Copy the contents of `card/` to the SD root. Verify
   the copied files with `Verify-Package.ps1 -CardRoot X:\ -Mode Install`,
   substituting the card drive letter.
3. Insert the card with the camera off. Hold OK while powering it on and
   leave the battery and card in place until the update completes. See
   `UPSTREAM_INSTALL.md` for the completion indicators.
4. Power off and remove `DCOLYMP/E1479999.BIN` from the card on the PC. Keep the
   three supplied `OM3MOD` files for Extras.
5. To restore stock 1.1, copy the file under `restore/DCOLYMP/` to the same
   card path, verify with `-Mode Restore`, and repeat the updater steps.
