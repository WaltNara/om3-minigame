# Ideas for the camera Games menu and renderer

Design notes only. No implementation or firmware change is proposed as already
working. The current package still launches 2048 from COLOR1's HSL row.

See [wheel independent rendering directions](WHEEL_INDEPENDENT_RENDERING.md)
for concrete source leads, alternatives and the first proof needed for each.

## Games menu entrance

**Preferred entrance: add a Games action row at the end of Caduceus's Picture
Mode adjustments.** Keep all existing HSL and photography rows intact. The shared
row list could make the entrance available across COLOR profiles.

The existing `pm_list` and custom row machinery provide a starting point, but
adding a row also requires consistent item-table counts, labels, selection and
event dispatch. Games should be an action, with no value written to a photo
setting. Highlighting the row should show a short description; OK should launch.

Proposed navigation:

```text
Picture Mode > Games > 2048 / other available games / Back
```

Use a small registry of game names and callbacks, with only available games
selectable. Keep menu state separate from game state. Arrows or a dial select;
OK starts; MENU from a game returns to the launcher; MENU from the launcher
returns to Picture Mode. A shutter half-press exits the whole game interface.

## Where the menu and game can draw

| Method | Assessment |
| --- | --- |
| **Overlay in the existing Picture Mode screen** | Best first investigation. Give the Games row its own paint/update path on a visible layer. Draw an opaque panel for the launcher or game, then restore normal drawing on exit. Reuses a mapped screen lifecycle, but the correct callback, layer order and redraw trigger still need establishing. |
| **Custom scene in a visible screen holder** | Cleaner separation for several games. Caduceus's WB grid demonstrates swapping a scene in a visible holder and restoring it. A game scene needs its own layout, drawing and lifetime handling; the WB scene itself is only a reference. |
| **Completely independent GUI screen/state** | Cleanest eventual interface, with the most reverse engineering. State registration, screen construction, rendering, back navigation and destruction all need mapping. Defer until the overlay path works. |

Do not assume an unused or hidden layer will draw. The upstream experiments
found that a scene needs a holder belonging to the displayed screen and a valid
canvas. Avoid depending on a holder after its screen has been destroyed.

## Rendering strategy

**Launcher and puzzles:** retain event-driven drawing. Render the menu only when
selection or content changes. Reuse compressed glyph/tile rows and a bounded
output buffer, as 2048 does. The new row needs a drawing trigger independent of
the colour-wheel guide descriptor.

**Platformers and shooters:** investigate a small logical framebuffer. A packed
128x64 monochrome image uses 1,024 bytes; an 8-bit 160x96 image uses 15,360 bytes.
These figures exclude sprites, maps, drawing conversion, stack and output
buffers. Render the game there, then convert/present through the camera's OSD
path. This gives existing small game engines a straightforward pixel interface.

Use the working registered GPI surface and palette initially. The current
bitmap hook demonstrates repositioning our own image while preserving the
unscaled call. Hardware scaling is unproven here; integer enlargement during
conversion is a fallback, with its own buffer and CPU cost. Supply uncached DMA
addresses and keep RLE runs inside scanlines. Derive worst-case encoded capacity:
detailed moving images may compress much worse than a puzzle board.

For continuous updates, publish only completed images. Reuse one output buffer
only after establishing when the camera finishes reading it. Otherwise consider
two output buffers with safe swapping, and include both in the RAM budget.
Maintain one update/render loop for the active game; stop it when leaving.
Frame rate must be measured on hardware.

## Smallest useful investigation

First show a static Games launcher from the new row while leaving COLOR1 HSL
functional. Next show one moving sprite through that same paint path. Check
MENU, shutter exit and re-entry before adapting a larger game. Keep row highlight,
launcher visibility and active gameplay as distinct states, so normal camera
buttons are intercepted only in the appropriate state.

Source references: [row list](vendor/caduceus-om3/firmware/src/editor.s),
[row table construction](vendor/caduceus-om3/firmware/build.py),
[visible-holder experiments](vendor/caduceus-om3/research/NOTES.md), and
[current bitmap and exit hooks](native/2048.s).
