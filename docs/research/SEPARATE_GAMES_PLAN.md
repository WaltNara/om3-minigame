# Separate Games implementation plan for Terra

Move 2048 from the COLOR1 HSL wheel to a Games entry at the end of Picture Mode's COLOR1–4 adjustment list. Use a separate launcher and game panel within that screen. Keep normal HSL and white-balance controls working.

The direction is sound and ready for staged implementation. The first stage must prove the native drawing and input path; the existing research has not established a working game panel outside HSL. A completely independent camera screen would require substantially more investigation and is outside this first version.

## User experience

- Highlighting Games shows its label or description. Only OK opens the launcher.
- The launcher contains **2048** and **Back**. Arrows or either dial change selection; OK selects.
- In 2048, arrows move tiles, the main dial moves up/down, the sub dial moves left/right, and held OK starts a new round.
- MENU from 2048 returns to the launcher; MENU or Back from the launcher returns to the Games row.
- A shutter half-press leaves the entire Games interface through the camera's normal transition.
- Returning to 2048 within one launcher session resumes the board. Leaving the Games interface ends that session; the next launch starts fresh.

## Recommended approach

Use the Picture Mode extension already present in Caduceus for the entrance. Give Games its own UI state and image data, rendered through a visible native element's normal paint operation. Keep game logic separate from this camera integration so the host can change later.

First investigate the native scene and element path demonstrated by the WB integration. That code establishes a lifecycle pattern, not a ready-made game canvas: do not take over the WB grid or assume its holder remains valid after a screen change. A scoped native paint callback is the fallback if an appropriate element cannot be used. Leave Setup-menu integration and a new standalone GUI screen for a later version.

Reuse the tested 2048 rules and compact image composition. Replace the current wheel-specific entry, input and redraw hooks. The finished interface must not depend on opening HSL, replacing its guide images, or changing a photography setting to request a repaint.

## Implementation order

1. **Preserve the working reference and prove the host.** Keep the existing wheel build and package available, and put experimental outputs in a separate directory. Identify and exercise a non-HSL entrance and native paint path with a static panel. Establish how repaint is requested and when image storage can be reused. If the first host fails, test the scoped paint fallback before integrating the game.
2. **Complete the Games launcher.** Add the row with consistent menu counts and dispatch. Implement selection, OK, Back, MENU and shutter exit. Prove repeated entry and exit, then move a small marker through the same drawing path. Highlighting Games must not activate gameplay or change photo settings.
3. **Move 2048 into the panel.** Reuse its rules and renderer, connect the agreed controls, and repaint only when state changes. Restore ordinary HSL behavior in the new build. Cancel game ownership on screen changes and never reuse a pointer to an old screen or drawing surface.
4. **Validate and package the new build.** Run the native rule checks and new UI replays against the exact candidate. Package separately with matching evidence and updated use instructions. Keep emulator results and physical-camera results distinct.

## Completion checks

| Area | Required result |
| --- | --- |
| Entrance | Games opens through OK from the new row on COLOR1–4 without opening HSL. |
| Navigation | Selection, Back, MENU, shutter exit and repeated re-entry follow the behavior above. |
| Gameplay | Moves, merges, score, spawning, restart and game over retain the tested behavior; blocked moves do not redraw. |
| Camera features | HSL and WB work before and after playing; Games inputs leave photo settings unchanged. |
| Rendering | The panel survives ordinary repaint, disappears on exit, and does not write into an image still being read by the drawing engine. |
| Display changes | LCD/EVF switching either rebuilds a valid Games panel or cleanly closes it; no stale callbacks or pointers survive. |
| Delivery | The package matches the tested firmware hash, includes its source and evidence, and states any remaining hardware checks. |

The current UI replay is tied to the wheel entrance and TFT screenshots, so it needs adaptation rather than reuse unchanged. Its settings comparison also drops the last two values; the new checks must explicitly cover HSL cursor/selection settings. The existing packager assumes exactly 26 KiB of added memory; replace that fixed expectation with a checked budget for the new build.

The emulator completes drawing synchronously and substitutes part of Picture Mode's paint coordination. It can prove navigation and rendered output, but cannot prove real drawing latency or buffer-reuse safety. Establish the native completion boundary before claiming safe image reuse; adding a second buffer alone is insufficient. Physical-camera responsiveness and display behavior remain separate validation work.

## Terra handoff

Implement this plan in order. Start with the smallest non-HSL panel proof and continue through launcher and 2048 integration when each stage passes. Keep code and output changes local; camera installation is a separate task. If neither proposed drawing path can be established, report the precise missing mechanism and retain the reproducible probe instead of presenting the transfer as complete.

Use [README.md](README.md) for the baseline and build commands, [WHEEL_INDEPENDENT_RESEARCH.md](WHEEL_INDEPENDENT_RESEARCH.md) for source leads, and [GAME_MENU_RENDERING_IDEAS.md](GAME_MENU_RENDERING_IDEAS.md) for the original interface proposal. The working code is [native/2048.s](native/2048.s); [native/test2048.py](native/test2048.py) and [native/package2048.py](native/package2048.py) provide the current verification and packaging patterns. Use the pinned local Caduceus and OM-Emu versions recorded in those documents.
