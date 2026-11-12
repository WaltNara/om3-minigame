# Camera game candidates for later development

Recorded from our discussions on 2026-11-11. Target: OM SYSTEM OM-3 through
Caduceus. These are research candidates, not confirmed camera ports.

## Current implementation

**2048** is implemented in [native/2048.s](native/2048.s). Its 617 native CPU
checks and full UI replay passed. Additional loaded section memory is 26 KiB;
the board is 16 bytes and the compressed drawing buffer is 18,052 bytes.
Physical-camera validation remains outstanding. See [README](README.md).

The earlier number-guessing demo and desktop 2048 prototype are historical
experiments, superseded by native 2048.

## Mario style platformers

| Game and source | Why consider it | Porting notes |
| --- | --- | --- |
| **[ATtiny85Mario / TinyMario](https://github.com/shepherdingelectrons/ATtiny85Mario)** | Directly Mario-inspired; horizontal scrolling and procedural terrain. Best tiny Mario-style starting point from our search. | Original target has 8 KB program memory and 512 bytes SRAM; these are hardware limits, not measured OM-3 usage. Replace AVR display/audio code. Code repository identifies GPL-3.0. [Developer explanation](https://shepherdingelectrons.blogspot.com/2020/01/tinymario.html). |
| **[Arduino Platformer](https://github.com/jacmet/arduino-platformer)** | Mario/Giana Sisters-inspired colour platformer with gravity, platforms, coins and collectibles. Best colour starting point. | Author reports about 21 KB flash and 1,090 bytes RAM on the original platform. Uses 16x16 tiles and LCD hardware scrolling, which needs replacing on the camera. Reuse permissions need checking. |
| **[Mystic Balloon](https://github.com/Team-ARG-Museum/ID-34-Mystic-Balloon)** | Established Arduboy platformer with jumping and balloon floating. | MIT-licensed game; archived source. Adapt input, rendering and timing. Balloon mechanics differ from Mario. |
| **[CastleBoy](https://github.com/jlauener/CastleBoy)** | Compact Castlevania-style platforming and combat; originally our strongest economical action-platformer suggestion. | MIT-licensed project. Needs movement plus jump/attack combinations, sprite drawing and continuous updates. |
| **[Celeste Classic via ccleste](https://github.com/lemon32767/ccleste)** | Room-based jumping and dashing; portable C game core with no dynamic allocation. | More demanding timing and simultaneous input. The repository is archived; review code and asset reuse terms. A later candidate after basic platforming works. |

## First person action

| Game and source | Why consider it | Porting notes |
| --- | --- | --- |
| **[Catacombs of the Damned / Arduboy3D](https://github.com/jhhoward/Arduboy3D)** | Strongest economical Doom-like suggestion: pseudo-3D exploration, fireballs, loot, four monster types and ten generated dungeon floors. | MIT-licensed project designed for Arduboy. Replace platform services and establish reliable continuous rendering. [Existing Flipper port reference](https://github.com/apfxtech/FlipperCatacombs). |
| **[Anarch](https://gamebuino.com/fr/creations/anarch)** | More elaborate Doom-like game with existing embedded ports. | More ambitious than Catacombs. Its [raycastlib](https://gitlab.com/drummyfish/raycastlib/-/tree/master) uses integer arithmetic and no dynamic heap allocation. CC0 project; resolution and rendering features are configurable. Camera performance is unmeasured. |

## Turn based games

These should reuse more of the existing event-driven input and drawing approach.

| Game and source | Suggested camera controls | Why it fits |
| --- | --- | --- |
| **[Sokoban via Arduban](https://github.com/rprouse/Arduban)** | Arrows move; INFO undo; held OK restart. | Best next puzzle for gameplay variety. Small tile maps and compressed levels; use bounded undo history. Game code is MIT; retain level and asset credits. |
| **[Fifteen](https://www.chiark.greenend.org.uk/~sgtatham/puzzles/doc/fifteen.html)** | Arrows slide tiles; held OK shuffle. | Lowest-effort follow-up: reuse the 4x4 numbered board. Generate solvable shuffles. |
| **[Net / NetWalk](https://www.chiark.greenend.org.uk/~sgtatham/puzzles/doc/net.html)** | Arrows select; dial rotates; OK locks. | Particularly good match for camera dials; simple connection graphics. |
| **[Minesweeper / Mines](https://www.chiark.greenend.org.uk/~sgtatham/puzzles/doc/mines.html)** | Arrows select; OK reveals; INFO flags. | Familiar gameplay and few tile symbols. Start with a small readable board; guaranteed-solvable generation is an optional extra. |
| **[Lights Out / Flip](https://www.chiark.greenend.org.uk/~sgtatham/puzzles/doc/flip.html)** | Arrows select; OK toggles. | Very small rules and state. A simple Lights Out variant can be smaller than the full configurable Flip implementation. |
| **[Peg solitaire / Pegs](https://www.chiark.greenend.org.uk/~sgtatham/puzzles/doc/pegs.html)** | Arrows select; OK chooses peg/destination; INFO undo. | Static board and few graphical states; no timing requirements. |

[Simon Tatham's collection](https://www.chiark.greenend.org.uk/~sgtatham/puzzles/)
provides MIT-licensed source references for Fifteen, Net, Mines, Flip and Pegs.
Adapting selected rules and drawing code is a smaller undertaking than porting
the entire collection and its generators, solvers and desktop interface.

## Other real time candidate

**[Snake via ArduSnake](https://github.com/Chootin/ArduSnake)**: a plausible first
test of timed game updates before platformers or shooters. Proposed controls:
arrows turn, OK pauses. The source identifies GPL-3.0. Needs a reliable tick,
pause/resume and rapid input delivery.

## Priorities and resource assumptions

- **Next after 2048:** TinyMario is the selected platformer candidate. Prove the Games interface and 2048 integration first; TinyMario is not yet a camera port.
- **For the user's current Mario-style preference:** investigate TinyMario first;
  Arduino Platformer is the colour alternative, Mystic Balloon the established
  Arduboy alternative.
- **For Doom-like gameplay:** investigate Catacombs first; keep Anarch as a larger
  follow-up.
- **For a quick puzzle addition:** Fifteen needs the least new drawing; Sokoban
  offers more varied play; Net makes good use of the dials.
- Mario and Doom themselves were genre references. We have not established a
  direct port of either original game.

The earlier estimate of under 1 KB for small puzzle state/scratch excludes
rendering, level packs and undo history. A packed 128x64 monochrome framebuffer
is 1,024 bytes, but camera display conversion and other buffers add overhead.
Original-device memory figures do not predict OM-3 totals. A 15-20 FPS action
game target was proposed, not measured or promised.

Action games need held and simultaneous buttons, scheduled updates, reliable
pause/exit, and continuous rendering beyond what turn-based 2048 established.
An appropriate C/C++ cross-toolchain would make adapting the existing engines
more economical than translating them wholesale into assembly. Follow the
[development advice](DEVELOPMENT_ADVICE.md) and prove a small native gameplay
slice before expanding content.
