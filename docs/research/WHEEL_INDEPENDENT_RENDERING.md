# Directions for a wheel independent game interface

Research record, 2026-11-11. Ideas only; no firmware edits or new execution tests.
Evidence comes from the local Caduceus and OM-Emu sources. None of the proposed
game interfaces below is established on a physical camera.

See the [follow-up research](WHEEL_INDEPENDENT_RESEARCH.md) for closer source
inspection, including the 456/457 discrepancy and emulator timing/paint limits.

## What independence means

The launcher and game should work without opening any HSL wheel. They should
not replace COLOR1 handlers, change the stock guide descriptors, or rewrite
wheel cursor setting 2197 to request drawing. They need their own input state,
image data, redraw trigger and exit handling.

The entrance and renderer are separate decisions. A Games row in Picture Mode
can launch a wheel-independent interface while still depending on that parent
screen. An entrance in Setup or a button shortcut would remove that remaining
Picture Mode dependency, but requires further menu/event mapping.

## Promising rendering directions

### 1 A game element in a visible native scene

**Best first direction to investigate.** Caduceus already loads the WB grid
scene into a holder belonging to the displayed Picture Mode screen and restores
the original scene afterwards. Investigate an existing bitmap or simple panel
element that can display a game-owned image descriptor in such a holder.

Trace `sc_cap`, `gr_upd`, `gr_is` and `gr_ref` in upstream `editor.s`. The notes
identify scene 498 and Picture Mode's layer-457 holder for the WB experiment.
These identify a lifecycle pattern, not a ready-made game canvas. A game panel
must preserve the WB feature and use a suitable visible holder/layout.

**First proof:** display a static launcher panel from a non-HSL row; change its
selection; restore the previous screen on exit. Establish the element's actual
paint callback and clipping before attempting animation. Hidden/startup holders
previously produced no drawing because they had no usable displayed canvas.

### 2 Draw directly during a known native paint callback

Use a visible parent element's paint callback to call the firmware's rectangle,
bitmap and text routines with its valid registered surface. This could avoid
constructing an entire new scene. Restrict the extra drawing to launcher/game
mode and the intended parent screen.

The existing Picture Mode `pu_hook` at `0x611d04ec` is a lead for tracking the
selected row and requesting updates. **It is not evidence of a safe drawing
bracket.** Trace the resulting native paint path before issuing graphics calls.
The same distinction applies to facade/property setters: they are redraw leads,
not general-purpose rendering APIs.

**First proof:** identify the owning task, paint entry/return, surface, clipping
and draw order; add a small test rectangle inside that paint operation. Prove
that normal redraws do not erase or repeatedly accumulate the overlay.

### 3 Inject an overlay before native frame submission

OM-Emu exposes `EXEC_START`, `EXEC_END`, `GPI_DRAW_BITMAP`, `GPI_DRAW_RECT`,
`DRAW_TEXT` and `GPI_UPDATE`. A possible bridge is to draw the game near the end
of the correct GUI drawing bracket, after normal background drawing and before
submission. It could reuse one existing visible surface without wheel images.

This is a broader hook than a dedicated element. Find a specific caller/task
and screen context; prevent recursion and repeated injection. A display-update
call alone does not establish that drawing is currently safe. Do not start a
nested graphics bracket blindly or retain a surface after its owner is destroyed.

**First proof:** trace one menu frame, identify its bracket and active buffer,
then draw a marker that survives normal refreshes and disappears on exit.
Keep this as a fallback if a local paint callback proves difficult to identify.

### 4 Give Games its own native GUI state

The cleanest eventual separation: a launcher screen owns its elements, input
and game viewport. OM-Emu names `STATE_TABLE`, `DISPATCH`, `STATE_LOG` and
`GUICALLER`, which are leads for tracing state construction and transitions.
Upstream `pm_ev` and `gx_map` show existing transition handling.

Do not assume an unused state number can simply be registered. Map state-table
structure, parent transitions, construction/destruction and TFT/EVF handling.
**First proof:** a blank owned screen with a title, selection and reliable back
navigation. Higher investigation cost; pursue after proving a native draw path.

## Menu and game image methods

- **Launcher:** a short game registry, cursor and text/tile labels. Repaint only
  when selection or contents change. Games is an action, not a photo setting.
- **Puzzles:** retain bounded compressed-row composition, presented from the
  interface's own image descriptor and invalidation path.
- **Action games:** consider a small software image converted to the supported
  OSD bitmap format. Packed 128x64 monochrome pixels occupy 1,024 bytes; conversion
  and presentation buffers are additional. Native rectangle/bitmap operations
  are another option for sparse sprites, subject to measured call overhead.
- **Scrolling:** investigate native `GPI_DRAW_COPY` / block-copy for moving the
  background and repainting exposed strips. Source/destination buffers, clipping
  and overlapping-copy behavior need verification before depending on it.
- **Animation:** investigate native GUI timeout/event scheduling. A timer should
  request an update; render in the owning GUI paint context. Cancel pending work
  on exit. The emulator's timer support is a research aid, not a proven game tick.

Keep the registered surface, palette and buffer ownership intact. The current
successful unscaled bitmap call is a starting point; hardware scaling remains
unproven. Derive worst-case conversion capacity and establish DMA completion
before reusing buffers. Direct display-register or arbitrary framebuffer writes
would require substantially more ownership/synchronization work and are deferred.

## Research order and completion criterion

Investigate **visible scene/element first, local paint callback second**. Use a
frame-submission overlay only if those paths are unsuitable. A standalone GUI
state is the longer-term option for a launcher accessible outside Picture Mode.

The decisive demonstration is: open Games without opening HSL, draw and change a
launcher, run a moving marker, exit/re-enter cleanly, and retain working COLOR1
HSL and WB controls. Only then select the approach for the next game.

## Source leads

- [Caduceus GUI hooks](vendor/caduceus-om3/firmware/src/editor.s): `pm_list`,
  `pu_hook`, `sc_cap`, `gr_upd`, `pm_ev`, `gx_map`.
- [Caduceus research](vendor/caduceus-om3/research/NOTES.md): Test 13 visible-layer
  findings and subsequent WB-holder lifetime fixes.
- [OM-Emu drawing API](work/om-emu/emu/src/lab/osd.mjs): registered records,
  drawing brackets, rectangle/bitmap/block-copy calls.
- [OM-Emu GUI observers](work/om-emu/emu/src/lab/menu.mjs): state dispatch,
  draw logs, text clipping and display updates.
- [OM-Emu display/timers](work/om-emu/emu/src/lab/display.mjs): software-timer
  initialization and native display handling.
- [Public OM-Emu repository](https://github.com/flatpanda/om-emu): the emulator
  uses model-specific address translation and named stand-ins. Its reference
  constants must be resolved for E147 and converted appropriately; do not copy
  E143 constants directly into OM-3 firmware.

Keep the game's image composition independent of its presentation callback.
That allows the same game renderer to survive a later move from a Picture Mode
overlay to an independent screen.
