# Mini Mario implementation status

The richer game is implemented in the combined **2048 / Minesweeper / Mini
Mario / Breakout / Back** launcher. The current four-game package and rollback
are described in [INSTALL_AND_RESTORE.md](INSTALL_AND_RESTORE.md).

- One original 1,152px course: three viewport widths, two gaps, raised stairs,
  six optional coins, a once-per-run reward block, one slow stompable patrol,
  and a finish flag. Unlimited retries; no audio, lives, power-ups or checkpoint.
- Camera follows at x=228 (about 60% of the 384px view), stops at the map end,
  and does not scroll backwards. World coordinates drive collision; the HUD
  stays fixed. Background clouds and terrain move together.
- Hold Left/Right to walk. Up or OK jumps; separate key tracking and a press
  latch preserve short taps. One tick of edge grace and landing buffering
  soften the 120ms simulation pace. INFO restarts; MENU returns to Games.
- Original 4px pixel art has facing, walk and jump poses. Collision retains
  full pixel precision; graphics round positions down by at most 3px.

## Implementation and budget

`mario_level.py` owns the 72-column terrain and six coin positions; the same
native data feeds collision and drawing. Rules use 64 bytes of state. Drawing
uses a 96-byte scratch row, a 192-byte compressed row, and 256 prepacked chunk
patterns. No heap, full pixel framebuffer, runtime RLE encoder, or combination
of player/object-position asset tables is needed. The renderer's 73,356-byte
output allocation bounds every possible chunk pattern, including unused worst
cases. Seven scene checks use at most 41,076 bytes and about 306k native
instructions per draw, versus 48,924 for the old prototype sample (about
6.2x more). This is the cost of bounded composition and a richer scene, not
a claim of unchanged drawing speed. These are emulator instruction counts,
not physical frame timings; the 120ms camera target still needs hardware
measurement. See `mario-render/performance-comparison.json`.

Validation passed on 2026-11-12: 30 Mario rule cases, 7 pixel-exact scene
frames, full course/input/cleanup replay, 20 Minesweeper rule cases, 3 Mines
render frames, and cross-game/display/2048 INFO restart checks.

The five-entry launcher shares pooled immutable rows and one output buffer,
replacing a full bitmap per entry. The four-game extension fits the
240 KiB target, including patch tables (245,760 loaded bytes). Read the exact hash and byte count
from `work/combined-game/build.json` and `bundle-build.json` after validation.

The existing timer -> deferred task -> GUI-message bridge remains in use.
Only the GUI task changes game state or paints. Epoch checks reject late
messages; MENU, shutter, display switches, restart, win and loss stop/reset the
timer. The linked `MARIO_GAME_STATE` is 4 in the combined build, 3 in the old
isolated build.

## Build and evidence

```
py -3 native/bundle/build.py
```

This builds and validates raw firmware only. `native/bundle/package.py` creates
the release once validation passes. The authoritative development image is
`work/combined-game/row-main.bin`; it is not an installable camera update.
Mario's core, decoded-frame and full-camera reports are under that directory
in `mario-core`, `mario-render` and `mario-replay`. The replay traverses the
course through actual input, tests loss/retry, short taps, independent Up/OK,
scrolling, timer cleanup, and a 2048 regression move. Minesweeper retains its
native rule/render checks and camera/display regression replay.

Hardware validation remains outstanding: real button feel, rendering latency,
DMA buffer lifetime and display/live-view re-entry. Preserve the 120ms target
until those measurements justify a change. The old single-screen sources and
validated image were saved under `work/mario-before-enrichment/` for comparison.

## Fourth-game integration

Breakout now shares Mario's graphics storage when active. The authoritative
shared timer/GUI code is `combined_bridge.s`; the isolated builder still uses
`mario_bridge.s`. The launcher has five entries, with Back at index 4. Use the
current bundle metadata for exact size and hashes. Mario's rules and course
are unchanged.
