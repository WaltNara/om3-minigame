# Separate Games panel probe

Run `py -3 native/probe_separate_panel.py` after preparing the existing emulator. The probe uses the unmodified Caduceus image and the existing paired card image, with all outputs under `work/separate-games/`. It does not build or install firmware.

On the third Down press in Picture Mode, the emulator debugger substitutes a static 256 x 320 image into one bitmap operation at `0x610f784f`. The replay checks that this operation is reached, that alternating bands appear in the screenshot, and that the OSD engine reports no errors. The image appears on a non-HSL tone-curve row, but later native drawing overlaps part of it. This establishes a possible drawing context, not a usable launcher: the operation belongs to another widget and replacing it removes that widget's bitmap.

Next locate a later, screen-scoped paint point or a suitable native element, establish its redraw and lifetime behavior, and repeat the proof without replacing a camera widget. The debugger substitution is not firmware code, and it does not establish safe asynchronous buffer reuse on hardware. Do not package this probe as a camera build.

An additional E147 trace of the same three row changes reaches `0x610f7fe9` once on each change, inside a drawing bracket just before its end. Its caller chain includes `0x610f70d4` and `0x610f32c5`; the same surrounding routines are shared with other screens. This is a lead for a later draw, not a verified Games hook: the correct surface, screen guard, draw order and buffer lifetime still need proof. The trace is at `work/separate-games/present-trace.json`.

`py -3 native/probe_late_paint.py` builds a separate emulator-only firmware image and arms a one-frame native hook at that point. It checks two bitmap calls, visible panel bands and engine errors. The image appears without substituting a stock widget, but is translucent and interacts with the existing screen. The two hardcoded surface addresses are experimental and must not be shipped. A first attempt faulted because the bitmap call's saved frame is 96 bytes; the current probe uses 96. It does not establish screen ownership, a repaint trigger or hardware-safe buffer reuse.

The standalone `games_menu.s` implements launcher navigation independently of the rendering host. Run `py -3 native/test_games_menu.py` for its native instruction checks. It is not yet connected to Picture Mode or 2048.
