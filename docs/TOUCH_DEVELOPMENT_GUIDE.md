# Touch control: working baseline and development guide

## Camera result — 2026-11-16

The user reports the real-camera test is **perfect** with the latest terminal-event
repair (v2, packaged as five-game r5). Treat this as a successful reported camera
acceptance test, not a measured long-duration endurance test. Earlier r4 avoided
the freeze but missed over half of normal taps. No physical event trace was taken.

Current raw SHA256:
`a3b5e0aa720f3703f6d3adcf771edb855ac99d63c24c116816976ff37c203ed8`.
Source: `flappy_touch_reply.s`; build: `work/flappy-touch-v2`; release:
`artifacts/om3-games-bundle-five-r5`. Preserve that release and its stock rollback.
Loaded extension is 232 KiB with 24 KiB margin. Variable pipe spacing remains.

## Rules for future games

- Own touch only inside the valid game page. Forward fresh outside-page events
  through the stock route; cancel game input on exit and drain an interrupted gesture.
- Every consumed event must receive its native completion reply. The stock
  null-payload path used here completes the handshake without widget navigation.
  Returning through GUI cleanup alone caused the earlier deadlock.
- Queue one action on initial contact (kind 1). Clear contact on release, tap,
  and double-tap endings (3/4/5). Do not add another action on completion.
- Preserve registers, stack and original event bytes. Never retain payload pointers.
  Keep drawing, file I/O and allocations out of the touch hook; use the GUI task.
- Keep fixed state and bounded input. The pending bit merges multiple presses
  before the 120 ms tick. A single short tap survives release. Avoid unbounded
  queues or delayed automatic actions after the player stops tapping.
- Do not blindly flap on standalone kind 4: sequences such as 1,3,4 could then
  double-count. If misses return, first add small RAM counters/recent-kind history
  and display them through the existing GUI timer. Do not tune controller settings
  or increase rendering speed without evidence.

For a future drag game, establish coordinate layout, jitter and terminal sequences
first. Track bounded latest coordinates, update on the GUI tick, and cancel on exit.
The successful tap test does not validate drag control or justify restoring old Breakout code.

## Full-menu candidate

The Extras host reuses the r5 Flappy handler and timer. It checks that the native
Setup panel still owns a valid paint target before accepting a game touch. The
same 14 protocol scenarios now run through either launcher. For Extras, set
`OM3_FLAPPY_BUILD=work/menu-extension/games` after building that candidate.
Its replay observed 181 replies and 181 returned waits for 181 events. Fresh
touches on the stock Setup list resumed stock handling after an interrupted
gesture. The earlier physical acceptance result applies to r5. The new host's
hardware touch behavior and recovery after switching displays remain open.
[Full-menu implementation and replay](../menu_extension/README.md)

## Verification and release

Build and validate with `py -3 build/build.py`. For individual checks, set
`OM3_FLAPPY_BUILD=work/current-games`, then run `tests/test_flappy_touch_reply.py`,
`tests/test_flappy.py`, and `tests/test_flappy_outside.py` from the repository root.
Tests must exercise the native application queue and reply wait, not only GUI injection.
Cover 1,3; 1,4; 1,5; 1,3,4; held input; short taps; retry; interrupted gestures;
MENU/shutter exits; and outside-game parity. Current reports pass 181 touch events,
1,750 physics cases, 26 render frames and 14 outside snapshots.

Tie reports to the exact raw hash. Package under a new release name, preserve the
accepted release/rollback, and record camera results separately. E147's physical
controller remains unmodelled; display-switch recovery and long-session stability
were not specifically reported by this latest camera test.

Detailed r3-freeze and r4-missed-tap diagnoses, plus superseded plans and probe
notes, are kept locally and deliberately not published in this repository.
