# Advice for further OM-3 game development

For the newer separate launcher, see the concise [Games development notes](native/GAMES_DEVELOPMENT_NOTES.md).

Start from the working native 2048 integration. Prove the camera interface before expanding the game; this prevents most of the repeated work encountered here.

1. **Define the deliverable first.** Specify the game, camera entry point, controls and exit behavior. Build the requested game around that contract. Keep one current implementation and clearly label abandoned prototypes.

2. **Freeze the firmware baseline.** Record the camera model, firmware version, upstream commit and input hashes. The current addresses belong to OM-3 firmware 1.1. Read Caduceus's relevant research notes before changing hooks or loaded memory ranges. Keep manufacturer binaries in ignored working folders.

3. **Prove one complete camera interaction early.** Draw a tile at the intended size and position, handle all required physical buttons, then exit through MENU and the shutter. Confirm ordinary camera settings remain unchanged. Complete this small native test before implementing the full game. For each failure, use one hypothesis and a focused check.

4. **Test the assembly calling convention separately.** Distinguish `CALLS` from `CALL`, including the stack space introduced by `CALL [],4`. Check register restoration and return addresses. Preserve MDR when the return path needs it; multiplication can overwrite it. Resolve external branch targets at link time and inspect the final disassembly.

5. **Reuse the proven graphics path.** Supply uncached addresses to graphics DMA. For firmware-resident image data, obtain the uncached alias by adding `0x40000000`. Keep RLE runs within scanlines. Preserve the working surface, palette and unscaled bitmap call. A larger image also needs a suitable drawing position; changing its descriptor alone is insufficient.

6. **Budget memory and work explicitly.** The current reference uses a 16-byte board, an 18,052-byte compressed drawing buffer and 26 KiB of additional loaded section memory. Derive buffer bounds, measure stack use, and load only the necessary aligned pages within the proven range. Update on input, skip blocked moves, and avoid animation timers unless needed. Instruction counts are useful measurements; camera frame-time claims need hardware timing.

7. **Validate, package and preserve the result.** Compare compiled game rules with an independent reference. Check screenshots, input, restart, exit and settings preservation in the full emulator. Package the exact tested firmware hash with its matching card files. Rerun affected checks after relevant changes; once they pass, finish the package. Label emulator and physical-camera results separately. Physical-camera validation remains outstanding for this build.

Useful starting points: [native implementation](native/2048.s), [compact graphics](native/assets.py), [tests](native/test2048.py), and [Caduceus research notes](vendor/caduceus-om3/research/NOTES.md).
