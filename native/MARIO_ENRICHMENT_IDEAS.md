# Mini Mario: low-cost ideas for a more original-like game

Implementation update: the reviewed core plan is implemented; see
[MARIO_STATUS.md](MARIO_STATUS.md). The sections below preserve design options,
not an outstanding mandatory checklist. Final packaging remains deferred.

Suggestions only, deliberately without implementation detail. The aim is to
get much closer to the feel of the original while keeping the per-frame work,
the loaded extension and the camera's responsiveness essentially unchanged.
All of them assume the single-course, no-pause scope stays.

## Cheap wins (almost no extra work per frame)

- **Better jump feel.** Variable jump height, a few frames of coyote time and
  a small jump buffer. Pure arithmetic on a handful of state words.
- **Horizontal inertia.** Acceleration, friction and a walk/run distinction
  instead of fixed-speed movement. Same cost as the current physics.
- **Coarse, fixed frame pacing.** Move/animate in a small number of discrete
  steps rather than continuously; most frames then do almost nothing.
- **A real HUD.** Score, coins, lives and a course label using the existing
  character rows already proven by 2048 and Minesweeper.
- **Two or three player poses.** Facing left/right, running, jumping, hurt —
  a few small sprites swapped by a state index, not new rendering machinery.
- **Checkpoint respawn.** On death, restore a saved position instead of
  re-simulating; no extra object updates.
- **Flagpole finish with a short scripted celebration.** A few frame counters,
  then a win banner. No persistent animation loop.

## Moderate additions (bounded, fixed-size objects)

- **A compact tiled course** that scrolls in coarse steps, with one static
  background and a handful of distinct tile shapes. A longer level without a
  longer per-frame loop.
- **A small fixed pool of patrolling enemies** with stomp resolution and a
  simple knocked-out state. Cap the count so the worst case is a constant.
- **Question blocks and coins** that change a counter and a tile index when
  hit, plus one simple power-up that only swaps the player's sprite and size.
- **Two or three scripted set pieces** (a gap, a step, a moving platform on a
  fixed path) instead of a general level engine.
- **A short, fixed win/loss cue** built from the existing two-colour shapes.

## Keep it cheap

- Static scenery stays prepacked; only the few dynamic objects change.
- One level, no saving, no audio, no pause, no per-pixel collision.
- Keep the total dynamic object count and the drawing buffer bounded and
  asserted by the existing sentinel checks.

## Avoid (cost grows faster than the fun)

- Many simultaneous moving objects or free-form particle effects.
- Per-pixel collision, animated backgrounds or multi-layer parallax.
- A whole-scanline table per combination of moving objects — that multiplies
  the asset size with every new sprite type.
- Streaming level data from the card, runtime scanline encoding of the whole
  frame, or any heap allocation in the frame path.

The current character is a plain two-colour 12x24 shape with no facing or
animation; richer sprites are worth doing, but only after the drawing path
stops scaling with the number of object combinations.


## Recommended plan after review (2026-11-12)

Planning only; the ideas above are a menu, not requirements. The recommendation
is a focused renderer simplification followed by a small playable expansion.
Keep the working timer/deferred-task/GUI bridge and lifecycle handling.

### Why simplify first

The current build's symbol spans put Mario rules/state at 296 bytes, versus
90,964 bytes for renderer code, graphics tables and its output buffer. This
is not a CPU-time measurement, but it locates the main storage cost. The
renderer precomputes player shape x terrain x horizontal position. Adding
independent objects that way would multiply combinations.

The existing Mario+2048 linked blob is 202,212 bytes; Minesweeper+2048 is
178,432 bytes. The extension ceiling is 262,144 bytes, including appended
patch tables. These are separate bundles, not additive modules. A future
three-game bundle needs its own linked-size check; do not assume it fits.

### Useful compact references

- [ATtiny85Mario](https://github.com/shepherdingelectrons/ATtiny85Mario) is the
  closest small Mario-style reference. The [author's explanation](https://shepherdingelectrons.blogspot.com/2020/01/tinymario.html)
  describes scrolling and procedural terrain on hardware with 8 KB program
  memory and 512 bytes SRAM. Those are original-device limits, not an OM-3
  port estimate. Use it for ideas about economy; skip its OLED/audio stack.
  The repository identifies GPL-3.0; review attribution and asset terms if
  copying rather than independently implementing mechanics.
- [Arduino Platformer](https://github.com/jacmet/arduino-platformer) is the
  most useful architecture reference: 16x16 tiles, a compact map, a visible
  map window and small temporary buffers. The author reports about 21 KB
  flash and 1,090 bytes RAM. Its cheap scrolling depends on ILI9341 hardware,
  so that performance does not transfer to the camera. No reuse license was
  established in this review; use as a design reference for now.
- [Mystic Balloon](https://github.com/Team-ARG-Museum/ID-34-Mystic-Balloon)
  is an archived MIT-licensed Arduboy platformer reference. Consider its
  game organization if needed, rather than making a whole port a prerequisite.

### Implementation order and stopping points

1. **Simplify drawing, preserve the existing course.** Store terrain and
   small sprite poses separately. First try prepacked terrain plus native
   sprite draws inside the existing paint bracket; verify transparency and
   overlap before committing. If that fails, compose only affected small
   tile/row segments in bounded scratch storage. Do not enumerate all object
   combinations or encode a full framebuffer every tick. Keep the old build
   as a reference. Gate: same course and exit behavior, demonstrated sprite
   overlap, bounded buffers, and a smaller measured extension. If this gate
   fails, ship only the input improvements below; do not expand the engine.
2. **Improve forgiveness.** Latch jump presses in the input handler so a tap
   between 120 ms ticks is not lost. Track Up and OK independently. Add a
   one-tick jump buffer and one-tick grace after walking off an edge. Keep
   direct horizontal control and the current pace initially. Variable jump
   height is optional after playtesting; a few grace frames would already
   mean hundreds of milliseconds here. No run button or inertia initially.
3. **Add horizontal scrolling and a larger course.** After the renderer
   simplification, prove the scrolling design below with the existing terrain
   and player before adding more objects. Start with one course about three
   viewport widths long.
4. **Enrich that course.** Add a short staircase/raised route,
   up to six optional coins, one coin-releasing block, and one slow patrol
   enemy that can be stomped. Implement coins/terrain first, enemy second;
   the enemy is droppable if it complicates collisions or slows drawing.
   Use common terrain data for collision and rendering. Cap each object
   type and use rectangle/crossing checks. Show only coins collected; add
   facing and walk/jump poses through the new sprite path. Keep unlimited
   retries and the current flag/win/restart loop.
5. **Optional later additions:** one checkpoint if the longer course needs
   it. Moving platforms, power-up sizes, lives, audio and procedural
   generation remain deferred. Horizontal scrolling is now part of the
   planned core experience, replacing the earlier screen-by-screen proposal.

Preserve the 120 ms target until measurements justify changing it. Do not
promise unchanged per-frame cost: measure the worst populated scene against
the existing build. Suggested build target: at most 240 KiB including tables,
leaving 16 KiB reserve; this is a planning budget, not a measured result.
Tests should target short taps, edge grace, coin/block one-time rewards,
stomp-versus-side collisions, sprite overlaps/buffer limits, and the existing
MENU/shutter/display cleanup. Hardware timing remains unverified. Integrate
with the shipped 2048+Minesweeper bundle only after the enriched prototype
passes these checks; follow COMBINING_GAMES.md rather than merging binaries.

### Horizontal scrolling design (requested)

Keep the HUD stationary. Once the player reaches roughly 60% of the visible
playfield width, further rightward movement advances the camera: the terrain
moves left and more of the course appears on the right. At the map's far end,
the camera stops and the player walks toward the finish flag.

- Store player, terrain and object positions in world coordinates. Drawing
  uses `screen_x = world_x - camera_x`; collision uses world coordinates.
  Clamp the camera between zero and `map_width - viewport_width`.
- Start with forward-only camera tracking and allow walking left within the
  visible area, clamping the player at its left edge. Backward camera tracking
  can be added later if useful. Move the camera in the same small pixel steps
  as the player on each simulation tick; do not add a separate animation timer.
- Store a compact tile map, not a giant background bitmap. For example, a
  72x19 map with 16-pixel tiles spans three 384-pixel viewports and needs
  684 bytes at four bits per tile, excluding graphics and object metadata.
  This is a proposed format, not a measured complete memory budget.
- Draw only the visible map window plus a small edge margin. Keep active
  enemies bounded (one initially), and retain collected-coin/used-block state
  separately so leaving the viewport does not recreate rewards.
- Scrolling still moves every visible terrain pixel. Do not assume the
  camera supports the Arduino project's hardware scrolling or that drawing
  only the newly exposed column is enough. First verify a bounded visible
  viewport redraw using reusable terrain pieces and sprites. If it misses
  the existing timing budget, optimize or reduce visual complexity before
  increasing the update rate. Larger camera steps are a fallback to assess,
  not the default experience.
- Verify threshold behavior, map-end clamping, left-edge movement, tile
  boundaries, jumps/collisions during scrolling, object persistence, and
  reset of the camera on restart. If a checkpoint is added, restore its
  camera position too. Existing shutter/display cleanup must still pass.

The first scrolling milestone is simply the current character traversing a
longer map without glitches. Coins and enemies follow after that succeeds.

## Touchscreen candidate: Flip Lights

Recommend an original **4x4 Lights Out-style puzzle**. Tap a tile to flip it
and its immediate up/down/left/right neighbors; turn all tiles dark. Large
contrasting tiles, instant feedback and short rounds suit the camera better
than dragging, precision aiming or reaction games. [Simon Tatham's Flip](https://www.chiark.greenend.org.uk/~sgtatham/puzzles/doc/flip.html)
provides a reference for this cross-shaped rule and mouse/keyboard controls;
our proposed version fixes the cross rule and uses the all-dark objective.

- A 16-bit board plus 16 precomputed toggle masks; one XOR per move.
  Generate solvable puzzles by applying moves to the solved board, rejecting
  an unchanged result. Scramble length is not a guaranteed minimum solution.
- Fit four generously spaced rows into the existing 384x480 panel. Display
  moves and a completion banner. INFO starts another round, MENU exits;
  arrows+OK are a fallback. Tap the same tile again to undo its board effect.
- No timer, dragging, long press, sound, save system or solver in version 1.
  Reuse the event-driven grid drawing approach from Minesweeper.
- **First gate is touch routing, not puzzle rules.** OM-Emu's input notes say
  a tap on the stock direct Picture Mode screen can close it. Verify the
  E147 event mapping and coordinate transform, then handle/consume touch
  only while this game owns the screen. Count one action per completed tap;
  ignore drag/outside taps, cancel a gesture on exit/display changes, and
  prevent a game tap from reaching the camera's stock touch actions.
  Emulator routing is not proof of physical touchscreen behavior.

This is the recommended easy touch game, but its input hook still needs a
small proof. Do not advertise touchscreen support until that gate passes.
