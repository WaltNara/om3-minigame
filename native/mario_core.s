/* Original scrolling platformer. World pixels, feet above ground, 120ms tick.
 * Inputs: left=1 right=2 Up=4 OK=8 fresh jump latch=16.
 * Fixed objects, no firmware calls. First five words retain prototype ABI. */
.am33_2
.text
.global mario_reset,mario_step,mario_state,mario_floor
mario_reset:
 mov mario_state,a0
 clr d0
 mov 16,d1
reset_words:
 mov d0,(a0)
 inc4 a0
 add -1,d1
 bne reset_words
 mov 18,d0
 mov d0,(mario_state)
 mov 620,d0
 mov d0,(mario_state+36)
 mov 1,d0
 mov d0,(mario_state+44)
 mov d0,(mario_state+56)
 ret [],4
/* Highest terrain under the 12px-wide player's feet. d0=x -> d0=height. */
mario_floor:
 mov d0,d1
 lsr 4,d0
 mov mario_heights,a0
 add d0,a0
 movbu (a0),d0
 extb d0
 add 11,d1
 lsr 4,d1
 mov mario_heights,a0
 add d1,a0
 movbu (a0),d1
 extb d1
 cmp d1,d0
 bge floor_return
 mov d1,d0
floor_return:
 ret [],4
mario_step:
 movm [d2,d3,a2,a3],(sp)
 add -24,sp
 mov mario_state,a3
 mov d0,d2
 mov (16,a3),d0
 cmp 0,d0
 bne step_done
 mov (52,a3),d0
 inc d0
 mov d0,(52,a3)
 mov d2,d0
 and 12,d0
 mov (12,a3),d1
 mov d0,(12,a3)
 cmp 0,d1
 bne check_latch
 cmp 0,d0
 bne fresh_jump
check_latch:
 mov d2,d0
 and 16,d0
 beq keep_buffer
fresh_jump:
 mov 2,d0
 mov d0,(60,a3)
keep_buffer:
 mov (a3),d0
 call mario_floor,[],4
 mov (4,a3),d1
 cmp d0,d1
 bne try_jump
 mov 2,d0
 mov d0,(56,a3)
try_jump:
 mov (60,a3),d0
 cmp 0,d0
 beq horizontal
 mov (56,a3),d0
 cmp 0,d0
 beq horizontal
 mov 12,d0
 mov d0,(8,a3)
 clr d0
 mov d0,(60,a3)
 mov d0,(56,a3)
horizontal:
 mov (a3),d3
 mov d2,d0
 and 3,d0
 cmp 1,d0
 bne move_right
 mov 1,d1
 mov d1,(48,a3)
 add -3,d3
 bra clamp_x
move_right:
 cmp 2,d0
 bne clamp_x
 clr d1
 mov d1,(48,a3)
 add 3,d3
clamp_x:
 mov (20,a3),d0
 cmp d0,d3
 bge right_limit
 mov d0,d3
right_limit:
 cmp 1140,d3
 ble wall_check
 mov 1140,d3
wall_check:
 mov d3,d0
 call mario_floor,[],4
 mov (4,a3),d1
 cmp d0,d1
 bge block_wall
 mov (a3),d3
block_wall:
 cmp 437,d3
 blt x_ready
 cmp 464,d3
 bge x_ready
 mov (4,a3),d0
 cmp 64,d0
 bge x_ready
 add 24,d0
 cmp 48,d0
 ble x_ready
 mov (a3),d3
x_ready:
 mov d3,(a3)
 mov d3,d0
 call mario_floor,[],4
 mov d0,(4,sp)
 mov (4,a3),d2
 mov d2,(8,sp)
 mov (8,a3),d1
 add d1,d2
 add -1,d1
 cmp 437,d3
 blt landing
 cmp 464,d3
 bge landing
 mov (8,sp),d0
 cmp 0,d1
 blt block_top
 add 24,d0
 cmp 48,d0
 bgt landing
 mov d2,d0
 add 24,d0
 cmp 48,d0
 blt landing
 mov 24,d2
 clr d1
 mov (32,a3),d0
 cmp 0,d0
 bne landing
 mov 1,d0
 mov d0,(32,a3)
 mov (28,a3),d0
 inc d0
 mov d0,(28,a3)
 bra landing
block_top:
 cmp 64,d0
 blt landing
 cmp 64,d2
 bgt landing
 mov 64,d0
 mov d0,(4,sp)
landing:
 mov (4,sp),d0
 cmp -64,d0
 beq airborne
 cmp d0,d2
 bgt airborne
 mov d0,d2
 clr d1
 mov 2,d0
 mov d0,(56,a3)
airborne:
 mov d2,(4,a3)
 mov d1,(8,a3)
 mov (56,a3),d0
 cmp 0,d0
 beq decay_buffer
 add -1,d0
 mov d0,(56,a3)
decay_buffer:
 mov (60,a3),d0
 cmp 0,d0
 beq check_fall
 add -1,d0
 mov d0,(60,a3)
check_fall:
 cmp -32,d2
 bgt collect
 jmp lose
collect:
 mov mario_coin_positions,a2
 mov 1,d0
 mov d0,(12,sp)
coin_loop:
 mov (24,a3),d0
 mov (12,sp),d1
 and d1,d0
 bne next_coin
 mov (a2),d0
 sub d3,d0
 cmp -8,d0
 blt next_coin
 cmp 12,d0
 bge next_coin
 mov (4,a2),d0
 sub d2,d0
 cmp 0,d0
 blt next_coin
 cmp 32,d0
 bge next_coin
 mov (24,a3),d0
 or d1,d0
 mov d0,(24,a3)
 mov (28,a3),d0
 inc d0
 mov d0,(28,a3)
next_coin:
 add 8,a2
 mov (12,sp),d0
 asl 1,d0
 mov d0,(12,sp)
 cmp 64,d0
 bne coin_loop
 mov (40,a3),d0
 cmp 0,d0
 bne camera
 mov (36,a3),d0
 mov (20,a3),d1
 add 400,d1
 cmp d1,d0
 bgt camera
 mov (44,a3),d1
 add d1,d0
 cmp 600,d0
 bgt enemy_right
 mov 1,d1
enemy_right:
 cmp 664,d0
 blt enemy_moved
 mov -1,d1
enemy_moved:
 mov d0,(36,a3)
 mov d1,(44,a3)
 sub d3,d0
 cmp -16,d0
 ble camera
 cmp 12,d0
 bge camera
 cmp 16,d2
 bgt camera
 mov (8,sp),d0
 cmp 16,d0
 blt lose
 mov (8,a3),d0
 cmp 0,d0
 bge lose
 mov 1,d0
 mov d0,(40,a3)
 mov 16,d0
 mov d0,(4,a3)
 mov 8,d0
 mov d0,(8,a3)
camera:
 mov d3,d0
 add -228,d0
 mov (20,a3),d1
 cmp d1,d0
 ble goal
 cmp 768,d0
 ble store_camera
 mov 768,d0
store_camera:
 mov d0,(20,a3)
goal:
 cmp 1104,d3
 blt step_done
 mov 1,d0
 mov d0,(16,a3)
 bra step_done
lose:
 mov 2,d0
 mov d0,(16,a3)
step_done:
 add 24,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4
.balign 4
/* x,y,vy,held jump,result,camera,coin mask,coin count,used block,
 * enemy x,enemy dead,enemy direction,facing left,tick,coyote,buffer */
mario_state: .space 64,0
.include "mario_level.inc"
