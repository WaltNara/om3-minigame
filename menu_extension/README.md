# OM-3 full-menu Extras

Started 2026-11-18 after pausing shutter playback work. Target the OM-3's normal
MENU interface, with an opaque menu/game background, independent of Picture Mode
and the creative dial. The separate E147 candidate now runs the five r5 game
cores from a native Setup row. The accepted Picture Mode release remains available.

## Camera menu

```text
MENU → Setup (wrench) → 2. Information Record → Extras
                                                Games
                                                Shutter sound
```

Extras is the fourth row, below Copyright Info. Setup page 2 has room for it
within the seven visible rows. This uses the existing page and its cursor
memory. All stock tabs, pages and rows remain available. The candidate takes
Picture Mode from the Caduceus baseline, which has no Games row.

**Games** opens the five-game launcher. MENU returns from a game to the launcher,
then to Extras, then to the original Setup row. A shutter half-press returns to
shooting. Flappy uses tap, Up or OK. Other games use their existing controls.

**Shutter sound** offers Silent, 5D, D850, Ciallo and Man. OK remembers the
choice in RAM for the powered session. MENU cancels. Silent is the default
and the effective electronic shutter sound for all choices in this candidate.
Camera audio playback remains a separate project.

## Build and replay the candidate

Use the previously prepared development inputs and accepted r5 linked game
blob. Run these commands from the repository root. The new image, screenshots
and hash-bound reports are written under `work/menu-extension/games/`.

```powershell
py -3 menu_extension/build_menu.py
node menu_extension/test_games.mjs
$env:OM3_FLAPPY_BUILD = 'work/menu-extension/games'
py -3 tests/test_flappy_touch_reply.py
py -3 tests/test_flappy.py
py -3 tests/test_flappy_outside.py
Remove-Item Env:OM3_FLAPPY_BUILD
py -3 menu_extension/package_trial.py
```

The packager verifies all four reports and reuses the project container builder.
It produces a local trial archive with the card files and a separate official
restore image. [Camera trial instructions](TRIAL.md)

## Menu and game ownership

The builder adds mode `0x7e01` to page 236's label, help and cursor-order lists.
The replay compares those tables and the stock value registrations, checks the
original Picture Mode hooks and rows against the baseline, and navigates to the
new item with camera button events. The native ListMenu viewer publishes
variable 232. The adapter reads its tab, page, fourth-row focus, label type
and help-box state. It retains a boolean. Only ListMenu panel 329 can accept
the entry key.

Each paint draws an opaque native rectangle underneath the game. The two
drawing contexts cover the menu widgets. Input-driven screens use no game
timer. Timed games use the existing 120 ms deferred GUI timer and validated
paint root. MENU, shutter exit and display teardown cancel the active session.
The replay checks the rendered text, edits and cancellation in the sound chooser,
2048 moves, Minesweeper cursor movement, timed play and native live-view requests.

The camera-accepted r5 Flappy handler remains byte-identical. Its wrapper
checks the current menu panel, GUI state, selected row, paint validity and
screen ownership. Other opaque Extras screens acknowledge touches without
operating the covered stock settings. Outside Extras, fresh touches use the
stock route. Interrupted gestures keep the one-byte drain until a terminal
event or fresh outside press. Every consumed event uses the native event-35
reply. The tests cover the sender's wait, original event bytes, register
restoration and the stack. E147 touch-controller timing, post-switch recovery,
endurance and power on a physical body are still unmeasured.
[Touch development guide](../docs/TOUCH_DEVELOPMENT_GUIDE.md)

The guide's 14 application-queue scenarios passed for raw image
`2912d4c11c58ed2056b33dd5fd14f89a2b37df4d43ba2caab95ed28bdc057fea`.
All 181 touch events had exactly one reply and one returned sender wait.
The 64-tap sequence mixed release, tap and double-tap endings and produced
64 flaps. A trailing tap notification after release produced no extra flap.
The suite also reproduced stock filtering of MENU while a finger was down,
tested a forced exit during contact, then verified that a fresh press on
the visible Setup list went through stock. All 14 outside-game camera/profile
snapshots matched the reference. The display-switch check covers teardown.

## Live view and migration cost

The OM-3's stock MENU entry asks its shooting component to stop live view. MENU
exit and shutter half-press ask it to resume. A game hosted inside this menu can
inherit that stop/resume behavior. The camera keeps the higher-level shooting
service ready during the menu, which gives us a stock path back to photography.

| E147 path exercised | Live-view control requests | Screen and game behavior |
| --- | --- | --- |
| Open MENU from shooting | Stop (`TRA 991`, `0`) | Full menu, GUI state `0x0b02`, panel 329 |
| Open Firmware Version, then press MENU | No new request | Panel 440 returns to 329 inside the same menu state |
| Close MENU or half-press from the menu list | Resume (`TRA 991`, `1`) | Returns to shooting state `0x0108` |
| Open r5 Games and enter Flappy | No stop request in this path | Picture Mode state `0x0418` remains active, Flappy advances 22 ticks in three simulated seconds |

The observations come from the stock and r5 firmware running in OM-Emu. The
camera application generates the requests in native code. The emulator answers
on behalf of their receiver (`S-TRAACK`) and tracks the requested live-view state
(`S-THROUGH`). In the E147 disassembly, dispatcher table `0x60f10b50` routes 991
to `0x50d8f0c9`, which calls the component at `0x50c9805f`. Its zero branch calls
the through-image force-stop routine `0x50bf0b08`. Its one branch calls the start
routine `0x50bf0aa6`. Table addresses are runtime and code addresses here are
OM-Emu notation. This checks the receiving path statically on the OM-3 build,
using the [OM-Emu through-image analysis](https://github.com/flatpanda/om-emu/blob/88b753ddb9c0fac35366802133e849600aa519d5/docs/hle-gaps.md#412-the-tra-layer-tra-485-who-handles-991-and-what-answers-990-d-unless-tagged)
as the E143 reference.

Both idle replays show zero captures and no active movie recording. The expected
resource saving is from stopping continuous preview work. Sensor readout, ISP
and lens activity, memory residency, current draw and heat on the physical OM-3
remain unmeasured. The LCD, native GUI and game rendering still need power.

The stock MENU list and its detail panel both execute the generic paint tail at
runtime `0x610f7fe9`, the same site r5 uses to submit game bitmaps. That supports
reuse of the drawing path and game buffers. The original r5 wrapper used
Picture Mode row selection, objects and fixed layers. The new adapter receives
keys on ListMenu, invalidates the validated menu root and reuses the shared GUI
queue for timer delivery. Its touch and cancellation regressions run against
this menu target.

## Evidence collected locally

Run from the root:

```powershell
node menu_extension/inspect.mjs
node menu_extension/map_lifecycle.mjs
node menu_extension/trace_lifecycle.mjs stock
node menu_extension/trace_lifecycle.mjs r5
```

This uses the existing external OM-Emu table decoder, selects E147 before imports,
verifies stock and accepted-r5 SHA256, decodes English labels from checked stock
resources and compares both main-menu inventories. It writes only
`work/menu-extension/inventory.json`. It neither changes firmware nor installs
hooks. The 2026-11-18 run passed:

- E147 has the newer ListMenu framework and eight tabs.
- Setup tab ID 7 has six pages, IDs 235–240, with real native records.
- The stock and accepted-r5 main-menu inventories are identical.
- Page 3 is Monitor/Sound/Connection; page 6 is Reset/Clock/Language/Others.
- **ID collision:** native main-menu mode 5380 is Quick Sleep Mode. Games uses
  5380 in the separate Picture Mode row list. Reusing it in ListMenu would be
  incorrect. Allocate and verify fresh IDs across the relevant registries.

The map and traces write `lifecycle-map.json`, `lifecycle-stock.json` and
`lifecycle-r5.json` to the same output directory. Replays observe existing hooks
without replacing their behavior. The r5 replay uses the existing paired card
and its usual section-ready fixture. The live-view control result does not rely
on those fixtures, since the stock run produces the same menu requests.

The main-menu layout uses tab entries, page-group records, keyed label/help/value
lists, custom value handlers, mode aliases and row ordering. Main-menu IDs,
settings-store IDs and Picture Mode row IDs must be treated as separate namespaces
until their lookup paths are checked. The report records E147 addresses rather
than assuming E143 locations.

## GitHub references reviewed

- [flatpanda/om-emu](https://github.com/flatpanda/om-emu): its README demonstrates
  E147's native Setup menu after MENU. The pinned local checkout supplies
  `emu/src/lab/menudata.mjs`, `menu.mjs`, `refs/menuref.mjs`, and the menu/navigation
  checks. These are the closest references for native table structure and tests.
- [Caduceus OM-3 research notes](https://github.com/androidfanman/caduceus-om3/blob/main/research/NOTES.md):
  native Button Function menu additions provide same-model precedents for list,
  item-info, validator and picker changes. The notes also describe a parked
  Firmware Version-screen investigation. Read the precise section before reuse;
  latest upstream findings do not automatically apply to our pinned v0.26.2.
- [cakelesscoder/caduceus-ep7](https://github.com/cakelesscoder/caduceus-ep7): useful
  extension/patch architecture, but a different model; never copy its addresses.
- [fishcu/oly_fw_analysis](https://github.com/fishcu/oly_fw_analysis): broader
  firmware research; not evidence of a ready-made E147 Games menu.
- [azqeurio/om-c-firmware](https://github.com/azqeurio/om-c-firmware): relevant
  shutter research, but the inspected public README does not supply a reusable
  full-menu Games host. Prior release analysis is recorded in the audio plan.

## Original investigation and migration sequence

The following sequence records the original proposal. The candidate above
uses a row on page 2 and shares the existing menu lifecycle. The separate
audio backend and physical measurements remain open.

1. Map the native ListMenu action dispatch, submenu entry/return, string lookup
   and page bounds on pinned E147. Verify a fresh ID and loaded code allocation.
   Start with an Extras entry opening a static opaque screen under the stock menu
   lifecycle. Verify that entry and navigation stay under the initial stop
   request and that only the final exit restarts live view. Capture the native
   action dispatch, screenshot, MENU return and shutter exit.
2. Implement an independent host for Games: entry/exit, input ownership, GUI-task
   timers, invalidation and painting. Reuse game cores/assets. Current
   `native/combined_host.s` binds `games_update`, `games_pm`, saved paint messages
   and render hooks to a live Picture Mode row; merely moving its label would
   retain that dependency. Never retain a stale native screen pointer.
3. Start with 2048 for button input and redraw, then verify a timed game before
   routing all five games through the new host. Preserve Flappy's terminal touch
   replies and release handling. Test all game exits, display changes, touch held
   during transitions, timer cancellation, and normal menu/shooting afterward.
4. Add the shutter choice with Silent default once its native backend is usable.
   Keep incomplete controls out of a released image. Sound playback remains an
   independent backend; this menu is its configuration interface.
5. Build a separate candidate and validate outside-game behavior before removing
   the old Picture Mode Games row. Final target has only the MENU entry. Keep the
   accepted r5 artifacts for rollback and avoid rebasing other Caduceus features
   as part of this host migration.

For the hardware comparison, use matched LCD brightness, lens, camera mode,
wireless settings, power source and sleep settings. Compare stock MENU against
idle Picture Mode first. After moving a game, compare the same game and input
sequence under both hosts. Record average input power where a meter is available,
temperature over the same interval, and half-press to usable live view. Baseline
menu measurements estimate the opportunity. The same-game comparison measures
the actual benefit with game drawing and timers active. The physical tests are
pending.
