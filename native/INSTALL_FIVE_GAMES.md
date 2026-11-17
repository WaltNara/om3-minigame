# Update to five games / restore original OM-3

**Current install target: `om3-games-bundle-five-r5` (accepted touch build).**
The r3 package described in older copies of this guide was withdrawn for a
reproduced touch deadlock; r4 stopped the freeze but missed >50% of taps. Neither
should be reinstalled. r5 clears the contact latch on terminal kinds 3/4/5 and
has a user-reported good on-camera touch result. See the
[touch development guide](TOUCH_DEVELOPMENT_GUIDE.md). The steps below apply
unchanged to r5: substitute its ZIP name where r3 is named historically.

For the standard OM SYSTEM OM-3, firmware 1.1 / E147 build 1100 only.
This includes Caduceus v0.26.2; no separate installation or optional film files
are required. Local checks are emulator-only; the camera touch result is a user
report, not a measured endurance test. The earlier four-game release was used
on the camera, with rare freezes subsequently reported.

## Update from your installed four-game version

1. Fully charge the battery. Back up photos and important camera settings.
   Extract `om3-games-bundle-five-r5.zip` completely (earlier local copies used
   the withdrawn r3 name). Keep `restore/` on the PC.
2. Open PowerShell in the extracted package folder and verify:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\Verify-Package.ps1
   ```

3. Copy **the contents of `card/`** to your SD root, replacing the update BIN
   and the three matching OM3MOD files. Keep DCIM and personal settings files.
   No formatting or stock restore is needed before updating the previous mod.

   ```text
   SD root/
     DCIM/                        existing photos
     DCOLYMP/E1479999.BIN          from card/DCOLYMP/
     OM3MOD/GUIDES.BIN
     OM3MOD/LABELS.BIN
     OM3MOD/TONES.BIN
   ```

   Keep existing LOOKS/EDITS/BUNDLES if you have them; none are supplied or
   required for the games. Do not put the outer `card` folder on the SD.
   Do not copy `restore/` during this step: its BIN has the same filename.
4. Verify the actual SD copy, replacing `X:\` with its drive letter:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\Verify-Package.ps1 -CardRoot X:\ -Mode Install
   ```

5. Safely eject and put the card in the powered-off camera. **Hold OK, switch
   on, and keep holding until updating starts.** A steady lamp means writing.
   Do not interrupt power or remove/open the card/battery while writing.
   Upstream reports about two minutes, but wait for blinking completion rather
   than using elapsed time. Immediate blinking without a writing phase may be
   rejection; recheck the files before trying again.
6. After completion, power off. On the PC remove **only
   `DCOLYMP/E1479999.BIN`** from the SD. Keep OM3MOD. Boot normally and half-press
   the shutter once. In COLOR1–4, open Picture Mode from the Super Control Panel,
   scroll to Games and press OK. Confirm all five games appear.

Test MENU/shutter exits and normal shooting first. In Flappy, tap or press OK/Up
to flap; the live distance starts on your first flap. INFO resets; MENU returns
to the launcher. **Lift your finger before pressing MENU** — stock ignores MENU
while a finger is held. The other four games retain their button controls and
stock touch behaviour. Do not leave Games running unattended; exit if the camera
becomes unusually warm. Touch recovery after an LCD/EVF switch is not verified.

## Return to the previous four games

Use the preserved `om3-games-bundle-buttons-r2` package's `card/` contents and
its verifier, then perform the same hold-OK update. Do not mix firmware BINs.
That older package is separate from this ZIP.

## Restore original firmware

1. Copy this package's **`restore/DCOLYMP/E1479999.BIN`** to the SD's
   `DCOLYMP/E1479999.BIN`, replacing the games updater. It is the hash-verified,
   unmodified official OM-3 1.1 image.
2. Verify before inserting the card:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\Verify-Package.ps1 -CardRoot X:\ -Mode Restore
   ```

3. Use the same full-battery, hold-OK power-on procedure. Wait for the steady
   writing phase to finish and the lamp to blink; then power off and remove the
   update BIN from the SD.
4. Boot normally. Games should be absent. Check shooting/playback and reload
   saved settings if needed. Stock ignores OM3MOD; archive/remove it if desired.

Deleting SD files or resetting settings does not uninstall the mod. Reflashing
restores firmware, not a snapshot of all settings. Both versions can report 1.1.
Rollback depends on the card updater still functioning; it is not guaranteed
recovery after an interrupted flash. `UPSTREAM_INSTALL.md` contains the pinned
upstream procedure. No camera/card writes are performed by the package verifier.
