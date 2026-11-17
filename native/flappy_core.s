/* Slow button flight: fixed-point y/velocity (quarter logical pixels).
 * State: y, velocity, pipe x, gap top, mode (0 ready,1 play,2 lost),
 * distance, seed, second pipe x/gap. Two fixed slots recycle indefinitely.
 * Spacing 56/72/88/104; closest gaps differ by at most 3 logical pixels.
 * 1 virtual metre = 4 horizontal pixels.
 * One tick = 120ms, pipe speed = 4 physical pixels. */
.am33_2
.text
.global flappy_reset,flappy_step,flappy_state,flappy_pending
flappy_reset:
 mov flappy_state,a0
 mov 240,d0
 mov d0,(a0)
 clr d0
 mov d0,(4,a0)
 mov d0,(16,a0)
 mov d0,(20,a0)
 movbu d0,(flappy_pending)
 mov 90,d0
 mov d0,(8,a0)
 mov 45,d0
 mov d0,(12,a0)
 mov 0x6d2b79f5,d0
 mov d0,(24,a0)
 mov 90,d0
 mov 45,d1
 call fp_next_pipe,[],4
 mov d0,(flappy_state+28)
 mov d1,(flappy_state+32)
 ret [],4
/* d0/d1 = preceding x/gap -> next x/gap. Only volatile registers used.
 * Small vertical steps for close pairs; clamp all openings inside the world. */
fp_next_pipe:
 add -12,sp
 mov d0,(4,sp)
 mov d1,(8,sp)
 mov (flappy_state+24),d0
 mov d0,d1
 asl 13,d1
 xor d1,d0
 mov d0,d1
 lsr 17,d1
 xor d1,d0
 mov d0,d1
 asl 5,d1
 xor d1,d0
 mov d0,(flappy_state+24)
 mov d0,a0
 and 3,d0
 asl 4,d0
 add 56,d0
 mov d0,a1
 mov (4,sp),d1
 add d1,d0
 mov d0,(4,sp)
 mov a0,d0
 lsr 2,d0
 and 7,d0
 cmp 56,a1
 bne fp_gap_wider
 cmp 3,d0
 ble fp_gap_sign
 mov 3,d0
 bra fp_gap_sign
fp_gap_wider:
 cmp 88,a1
 blt fp_gap_sign
 asl 1,d0
 cmp 12,d0
 ble fp_gap_sign
 mov 12,d0
fp_gap_sign:
 mov a0,d1
 and 32,d1
 beq fp_gap_add
 clr d1
 sub d0,d1
 mov d1,d0
fp_gap_add:
 mov (8,sp),d1
 add d0,d1
 cmp 32,d1
 bge fp_gap_low_ok
 mov 32,d1
fp_gap_low_ok:
 cmp 63,d1
 ble fp_gap_ready
 mov 63,d1
fp_gap_ready:
 mov (4,sp),d0
 add 12,sp
 ret [],4
flappy_step:
 movm [d2,d3,a2,a3],(sp)
 add -4,sp
 mov flappy_state,a3
 movbu (flappy_pending),d2
 clr d0
 movbu d0,(flappy_pending)
 mov (16,a3),d0
 cmp 2,d0
 bne fp_alive
 cmp 0,d2
 beq fp_done
 call flappy_reset,[],4
fp_alive:
 cmp 0,d2
 beq fp_no_flap
 mov 1,d0
 mov d0,(16,a3)
 mov -10,d0
 mov d0,(4,a3)
fp_no_flap:
 mov (16,a3),d0
 cmp 1,d0
 bne fp_done
 mov (4,a3),d0
 inc d0
 cmp 10,d0
 ble fp_velocity
 mov 10,d0
fp_velocity:
 mov d0,(4,a3)
 mov (a3),d1
 add d0,d1
 mov d1,(a3)
 cmp 104,d1
 blt fp_lost
 cmp 412,d1
 bgt fp_lost
 mov (20,a3),d0
 cmp 99999999,d0
 bge fp_distance_ready
 inc d0
 mov d0,(20,a3)
fp_distance_ready:
 mov (8,a3),d2
 add -1,d2
 mov d2,(8,a3)
 mov (28,a3),d0
 add -1,d0
 mov d0,(28,a3)
 cmp -12,d2
 bge fp_second_recycle
 mov (32,a3),d1
 call fp_next_pipe,[],4
 mov d0,(8,a3)
 mov d1,(12,a3)
fp_second_recycle:
 mov (28,a3),d0
 cmp -12,d0
 bge fp_collision_setup
 mov (8,a3),d0
 mov (12,a3),d1
 call fp_next_pipe,[],4
 mov d0,(28,a3)
 mov d1,(32,a3)
fp_collision_setup:
 mov a3,a2
 add 8,a2
 mov 2,d3
fp_collision:
 mov (a2),d2
 cmp 30,d2
 bge fp_next_collision
 mov d2,d0
 add 12,d0
 cmp 24,d0
 ble fp_next_collision
 mov (a3),d0
 mov (4,a2),d1
 asl2 d1
 cmp d1,d0
 blt fp_lost
 add 128,d1
 add 16,d0
 cmp d1,d0
 bgt fp_lost
fp_next_collision:
 add 20,a2
 add -1,d3
 bne fp_collision
 bra fp_done
fp_lost:
 mov 2,d0
 mov d0,(16,a3)
fp_done:
 add 4,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4
.balign 4
flappy_state: .space 36,0
flappy_pending: .byte 0
