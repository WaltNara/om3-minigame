# Games menu and rendering: research findings

2026-11-11. Research only; firmware and packages unchanged. No new execution
tests or physical-camera results. This develops the earlier
[rendering directions](WHEEL_INDEPENDENT_RENDERING.md).

## Recommended direction

Use a small Games launcher hosted by a native GUI element, with game-owned image
data rendered during that element's normal paint. A Picture Mode row is the
shortest entrance to investigate; a Setup menu entrance is a useful alternative.
Neither requires opening HSL in principle. Neither has been implemented here.

Separate the launcher/game logic from the host element so it can later move to
a standalone screen. Prefer event-driven repaint for the launcher and 2048;
introduce a timed update only for animated games.

## What the sources establish

| Finding | Implication |
|---|---|
| Caduceus `sc_cap` captures a visible Picture Mode holder; `gr_upd` loads scene 498; `gr_ref` invokes its update method. | A native scene replacement has an existing lifecycle pattern. It does not establish that an arbitrary game bitmap element can be inserted. |
| Current code defines `GLY = 456`, although surrounding comments and older notes mention 457 and sometimes scene 485. Executed instructions load scene 498. | Use the pinned code and actual object identity; do not copy older scene/layer numbers blindly. |
| The holder capture checks GUI state `0x0418`. Other screens share layer 456. Re-entry has explicit `gr_wait`/`gr_fine` guards. | A pointer from a previous screen is unsafe. Capture only the intended live holder and invalidate it on exit. |
| The documented menu paint path handles message `0x1002`, paints layers and children, brackets drawing, flips front/back buffers and copies between them. | Drawing directly into a visible buffer can be overwritten. Integrate with native paint and presentation ownership. |
| The OSD lab reads registered surfaces as 16-byte `<IIHHHH>` records: base, kind, stride, height, x, y. Text drawing uses a richer graphics context. | A surface descriptor is not interchangeable with a text GC or widget object. Trace the chosen operation's actual argument type. |

The menu paint trace is for **OM-1 E143 v1.9**, not a measured OM-3 callback.
OM-Emu translates addresses per model. Its message numbers, object layouts and
call signatures remain leads requiring E147 verification before use.

## Two important limits on confidence

**Picture Mode paint depends on an emulator substitute.** The menu specification
records S-BGDRAW overriding a paint gate for shooting/direct WB/Picture Mode and
playback. Setup menu entry and menu close take the native gate path. This makes
Setup worth comparing as a host; it does not prove Setup integration is easier
or camera-ready. Existing game replay success cannot establish the missing
application/background coordination on real hardware.

**Drawing latency is not modelled.** FIDELITY-NOTES section 1.3 says the emulator
finishes the whole OSD command list inside the CPU write that starts it. It cannot
expose buffer-reuse races caused by a real blitter taking time. Keep image and
palette storage alive until the native completion boundary is understood. Two
buffers alone do not establish safety if both can still be in flight.

## Concrete design to investigate

1. **Entrance:** add a Games action whose selection opens a separate launcher.
   Highlighting the row should not activate gameplay. The existing Picture Mode
   extension touches item tables, counts and dispatch, so appending a label alone
   is insufficient. Setup requires a separate table/event investigation.
2. **Paint:** locate a simple native image element's constructor, paint callback,
   clipping and invalidation path. Submit through its existing drawing bracket;
   do not nest `EXEC_START/END` or call display-update arbitrarily. `pu_hook` is a
   row-update lead, not an established safe paint callback.
3. **Image:** begin with a fixed small bitmap and persistent descriptor/palette.
   A 128×64 packed monochrome working image costs 1 KiB; a 160×96 8-bit image
   costs 15 KiB, before conversion, descriptors or presentation buffers. Choose
   the native upload format after verifying the callback. Defer scaling and
   overlapping blits until their behavior is established.
4. **Updates and exit:** keys change state and request native repaint. A future
   timer should enqueue an update in the owning GUI context. On MENU, shutter
   exit or screen change, deactivate the game, cancel updates and discard stale
   callbacks using a session identifier. Preserve the native screen transition.

LCD/EVF switching needs explicit treatment: the documented menu and direct-screen
layouts differ, and direct Picture Mode re-entry can reset selection. Do not
retain a graphics context or assume a holder survives a display change.

## Next proof and remaining unknowns

First establish one non-HSL entrance, a static launcher, selection changes and
clean exit/re-entry. Then move one marker using the same paint path. Verify HSL
and WB still work; test LCD/EVF transitions and repeated exits. Physical-camera
validation must separately cover rendering completion and responsiveness.

Still unresolved: the exact E147 image-element callback and creation method,
its native invalidate operation, the game input routing, and the hardware-safe
buffer completion boundary. These are the next research targets. No defensible
numerical success probability follows from the present evidence.

## Reproducible sources

- Caduceus pinned commit `f4d2569eb46817795ec5ffaf931ba058d2c0d029`:
  [editor.s](vendor/caduceus-om3/firmware/src/editor.s), especially `pm_list`,
  `pu_hook`, `sc_cap`, `gr_upd`, `gr_ref`, `gx_map`;
  [menu table patches](vendor/caduceus-om3/firmware/build.py).
- OM-Emu inspected checkout `88b753ddb9c0fac35366802133e849600aa519d5`:
  [menu specification](work/om-emu/docs/om1-menu-spec.md), sections 1, 14–15;
  [drawing API](work/om-emu/emu/src/lab/osd.mjs), `record`, `drawing_enter/exit`;
  [GUI observers](work/om-emu/emu/src/lab/menu.mjs);
  [fidelity limits](work/om-emu/emu/FIDELITY-NOTES.md), section 1.3.
- [Public upstream overview](https://github.com/flatpanda/om-emu) confirms the
  lab uses model ports and stand-ins rather than a full reset-to-boot simulation.
  Local pinned source is the basis of the detailed findings above.
