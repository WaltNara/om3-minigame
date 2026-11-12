/* Original small Breakout rules. Logical coordinates are 4px display cells.
 * Ball is 2x2; paddle 20x2. Three lives, 18 bricks, serve between lives.
 * State: paddle x, ball x,y, dx,dy, mode (0 ready/1 play/2 win/3 lose),
 * lives, bricks left, reserved; followed by 18 brick bytes. */
.am33_2
.text
.global breakout_reset,breakout_step,breakout_serve,breakout_state
breakout_reset:
 mov breakout_state,a0
 mov 38,d0
 mov d0,(a0)
 mov 3,d0
 mov d0,(24,a0)
 mov 18,d0
 mov d0,(28,a0)
 clr d0
 mov d0,(32,a0)
 mov breakout_bricks,a1
 mov 18,d1
br_reset_loop:
 mov 1,d0
 movbu d0,(a1)
 inc a1
 add -1,d1
 bne br_reset_loop
br_ready:
 mov breakout_state,a0
 clr d0
 mov d0,(20,a0)
 mov d0,(32,a0)
 mov (a0),d0
 add 9,d0
 mov d0,(4,a0)
 mov 99,d0
 mov d0,(8,a0)
 mov 1,d0
 mov d0,(12,a0)
 mov -2,d0
 mov d0,(16,a0)
 ret [],4
breakout_serve:
 mov breakout_state,a0
 mov (20,a0),d0
 cmp 0,d0
 bne br_serve_done
 mov 1,d0
 mov d0,(20,a0)
br_serve_done:
 ret [],4
breakout_step:
 movm [d2,d3,a2,a3],(sp)
 add -16,sp
 mov breakout_state,a3
 /* Left/right use the timer's existing held-key mask. */
 and 3,d0
 mov (a3),d1
 cmp 1,d0
 bne br_right
 add -3,d1
 bra br_clamp
br_right:
 cmp 2,d0
 bne br_clamp
 add 3,d1
br_clamp:
 cmp 2,d1
 bge br_high
 mov 2,d1
br_high:
 cmp 74,d1
 ble br_moved
 mov 74,d1
br_moved:
 mov d1,(a3)
 mov (20,a3),d0
 cmp 0,d0
 bne br_play
 add 9,d1
 mov d1,(4,a3)
 bra br_done
br_play:
 cmp 1,d0
 bne br_done
 /* Two 1-cell substeps avoid tunnelling through bricks and paddle. */
 mov 2,d0
 mov d0,(4,sp)
br_substep:
 mov (4,a3),d2
 mov (8,a3),d3
 mov d2,(8,sp)
 mov d3,(12,sp)
 mov (12,a3),d0
 add d0,d2
 cmp 2,d2
 bge br_wall_right
 mov 2,d2
 mov 1,d0
br_wall_right:
 cmp 92,d2
 ble br_wall_done
 mov 92,d2
 mov -1,d0
br_wall_done:
 mov d0,(12,a3)
 mov (16,a3),d0
 cmp 0,d0
 blt br_up
 inc d3
 bra br_top
br_up:
 add -1,d3
br_top:
 cmp 25,d3
 bge br_paddle
 mov 25,d3
 mov 2,d0
 mov d0,(16,a3)
br_paddle:
 mov (16,a3),d0
 cmp 0,d0
 blt br_bricks
 mov (12,sp),d0
 cmp 100,d0
 bgt br_bricks
 cmp 100,d3
 blt br_bricks
 mov (a3),d0
 mov d2,d1
 add 2,d1
 cmp d0,d1
 ble br_bricks
 add 20,d0
 cmp d0,d2
 bge br_bricks
 mov 100,d3
 mov -2,d0
 mov d0,(16,a3)
 /* Paddle half controls the rebound direction, so every brick is reachable. */
 mov (a3),d0
 add 9,d0
 cmp d0,d2
 blt br_bounce_left
 mov 1,d0
 bra br_bounce_set
br_bounce_left:
 mov -1,d0
br_bounce_set:
 mov d0,(12,a3)
br_bricks:
 mov breakout_bricks,a2
 clr d0
br_brick_loop:
 mov d0,(br_index)
 movbu (a2),d1
 cmp 0,d1
 beq br_next
 /* Precomputed 4-word rectangles avoid multiply/divide in the frame path. */
 asl 4,d0
 mov breakout_rects,a0
 add d0,a0
 mov (a0),d0
 mov d2,d1
 add 2,d1
 cmp d0,d1
 ble br_next
 mov (4,a0),d0
 cmp d0,d2
 bge br_next
 mov (8,a0),d0
 mov d3,d1
 add 2,d1
 cmp d0,d1
 ble br_next
 mov (12,a0),d0
 cmp d0,d3
 bge br_next
 clr d0
 movbu d0,(a2)
 mov (28,a3),d0
 add -1,d0
 mov d0,(28,a3)
 /* Resolve against previous vertical position, otherwise a side contact. */
 mov (12,sp),d0
 add 2,d0
 mov (8,a0),d1
 cmp d1,d0
 ble br_vertical_hit
 mov (12,sp),d0
 mov (12,a0),d1
 cmp d1,d0
 bge br_vertical_hit
 mov (12,a3),d0
 not d0
 inc d0
 mov d0,(12,a3)
 mov (8,sp),d2
 bra br_hit_done
br_vertical_hit:
 mov (16,a3),d0
 not d0
 inc d0
 mov d0,(16,a3)
 mov (12,sp),d3
br_hit_done:
 mov (28,a3),d0
 cmp 0,d0
 bne br_store
 mov 2,d0
 mov d0,(20,a3)
 bra br_store
br_next:
 inc a2
 mov (br_index),d0
 inc d0
 cmp 18,d0
 bne br_brick_loop
br_store:
 mov d2,(4,a3)
 mov d3,(8,a3)
 cmp 108,d3
 blt br_more
 mov (24,a3),d0
 add -1,d0
 mov d0,(24,a3)
 cmp 0,d0
 beq br_lost
 call br_ready,[],4
 bra br_done
br_lost:
 mov 3,d0
 mov d0,(20,a3)
 bra br_done
br_more:
 mov (20,a3),d0
 cmp 1,d0
 bne br_done
 mov (4,sp),d0
 add -1,d0
 mov d0,(4,sp)
 bne br_substep
br_done:
 add 16,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4
.balign 4
.global breakout_bricks,breakout_rects
breakout_state: .space 36,0
breakout_bricks: .space 18,0
.balign 4
br_index: .long 0
.include "breakout_level.inc"
