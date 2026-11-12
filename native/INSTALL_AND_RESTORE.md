# Install all four games / restore stock OM-3

This package contains 2048, Minesweeper, scrolling Mini Mario and Breakout in
**one unofficial firmware image**, including Caduceus v0.26.2 photo/film features.
It is emulator-tested only. It is for the **standard OM SYSTEM OM-3, firmware
1.1 (E147 build 1100)**. Do not use it on another model or assume compatibility
with a different firmware version. No separate Caduceus installation is needed.

## Before starting

1. Check the body's firmware version in Setup → Firmware Version. If it is
   1.0, use the official OM update process to reach 1.1 first. If it is another
   version, do not install this build until compatibility is checked.
2. Fully charge the battery. Back up photos and save camera settings through
   OM Workspace or OI.Share; photograph important settings that cannot be saved.
   Use a spare, camera-formatted SD card if available (formatting erases it).
3. Extract the ZIP completely on your PC. Keep the complete folder, especially
   `restore/`, somewhere you can find without the camera working.
4. In PowerShell opened in the extracted package folder, verify the files:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\Verify-Package.ps1
   ```

   Continue only if it reports PASS. The verifier only reads files; it never
   copies, deletes, or flashes anything.

## Update from our previous games release

Use `om3-games-bundle-buttons-r2.zip`. No stock restore is needed first.
Copy its `card/` contents onto the SD root, replacing the old update BIN and
GUIDES/LABELS/TONES. Keep photos and existing personal settings files.
Verify with the included script, then follow the hold-OK update steps below.
After success delete the update BIN. Confirm Breakout says OK TO LAUNCH and
LEFT RIGHT, and the small Games footer is centered with padding.
The previous release froze on Breakout entry; r2 removes its touch code but
needs a hardware retest before calling the freeze fixed.

## Install

1. Copy **the contents of `card/`** to the SD card root, beside `DCIM`.
   No optional film presets are needed.
   If already using Caduceus, back up and keep your existing LOOKS/EDITS/BUNDLES;
   replace GUIDES/LABELS/TONES with the three bundled files. Do not mix releases.

   ```text
   SD root/
     DCIM/
     DCOLYMP/E1479999.BIN       ← from card/DCOLYMP/
     OM3MOD/GUIDES.BIN
     OM3MOD/LABELS.BIN
     OM3MOD/TONES.BIN
   ```

   Do not copy the outer `card` or package folder onto the card. Do not copy
   `restore/` for installation: its BIN intentionally has the same filename.
2. Verify the actual card copy (replace `X:\` with its drive letter):

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\Verify-Package.ps1 -CardRoot X:\ -Mode Install
   ```

3. Safely eject the card. With the camera off and a full battery, insert it.
   **Hold OK before switching the camera on**; keep holding until updating starts.
4. The update lamp is steady while writing (upstream reports about two minutes).
   **Do not switch off, remove the card/battery, or open the battery door while
   writing.** Wait for the steady phase to finish and the lamp to blink; then
   switch off. Elapsed time alone is not a completion signal. Immediate blinking
   without a steady phase means rejection, not success; recheck the files and path.
5. On the PC, remove **only `DCOLYMP/E1479999.BIN`** from the SD card to prevent
   accidental reinstallation. Keep the matching `OM3MOD` files on cards used
   with the mod. Reinsert, boot normally, and half-press
   the shutter once. Turn the creative dial to COLOR, select COLOR1–4, open
   Picture Mode from the Super Control Panel, scroll to **Games**, and press OK.

MENU returns from a game to the launcher; choose BACK to leave that launcher.
Shutter half-press leaves Games through the camera's normal handler. Display
switching clears the session. Mario and Breakout cancel their timer on tested
exits and on win/loss. Game controls are in `README.md`; INFO restarts 2048.
Breakout uses held Left/Right and OK to serve; INFO restarts. No game touch controls remain. A swipe may close Games through the stock menu handler; use buttons.

## Restore the original firmware

1. Charge the battery and back up any new photos/settings. On the PC, copy
   **`restore/DCOLYMP/E1479999.BIN`** into the card's **`DCOLYMP/`** folder,
   replacing any games update BIN there. This is untouched official OM-3 1.1.
2. Verify the restore copy:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\Verify-Package.ps1 -CardRoot X:\ -Mode Restore
   ```

3. Safely eject, insert into the powered-off camera, and perform the same
   **hold OK → power on → steady writing → blinking completion → power off**
   procedure. The same no-interruption rule applies.
4. Remove the update BIN afterward. Stock firmware ignores `OM3MOD`; you can
   archive/remove that folder. Boot normally, confirm Games/film rows are gone,
   and check shooting and playback. Reload your settings backup if needed.

Both images can display version 1.1, so that number alone does not confirm
rollback. Reflashing restores the firmware, not a snapshot of every camera
setting. Reset/Initialize Settings and deleting SD files do **not** uninstall it.

This is the documented normal rollback route, not guaranteed brick recovery:
it depends on the camera's card updater still functioning. If an update is
interrupted and that updater no longer runs, repair/service may be required.
For a game freeze **outside an update**, try normal power-off; only then consider
removing the battery briefly and using the stock restore procedure. Never apply
that freeze advice during firmware writing.

## First use and references

Start with a short session: test MENU, shutter exit and ordinary photography,
then briefly test Breakout buttons and MENU. If it freezes again, discontinue
Breakout; removing touch does not establish the cause of the entry freeze. Do not leave
Games running unattended: Picture Mode's timeout is suppressed, and automatic
sleep/thermal behavior has not been tested on a body. Exit and let it cool if it
becomes unusually warm or reports high temperature. See `HARDWARE_RISK_REVIEW.md`.

The SD update/rollback method is from the [Caduceus installation guide](https://github.com/androidfanman/caduceus-om3/blob/main/docs/INSTALL.md);
the pinned version is included as `UPSTREAM_INSTALL.md`. Its launcher/download
steps are already completed for this package; use the files supplied here.
Official references: [firmware updates](https://explore.omsystem.com/c/en/firmware-update-instructions),
[settings backup](https://explore.omsystem.com/c/en/how-to-download-settings-in-your-camera),
[temperature warnings](https://learning.omsystem.com/OM-3/zz_html_manual/en/error_codes_308.html).
This local archive contains manufacturer firmware; keep it for personal use.
