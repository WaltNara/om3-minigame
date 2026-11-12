/* Native OM-3 1.1 / Caduceus 0.26.2 experiment.
 * COLOR1's colour-wheel handlers become a tiny guessing game.
 * ABI and redraw sequence adapted from Caduceus editor.s (Apache-2.0).
 * No flash writes, file writes, allocations or photography-setting changes at runtime.
 */
.am33_2
.text
.include "original.inc"
.global game_init, game_info, game_up, game_down, game_event, game_state
.global other_init, leave_game

/* Preserve all incoming arguments while restoring the shared guide resources. */
other_init:
 movm [other],(sp)
 add -4,sp
 call restore,[],4
 add 4,sp
 movm (sp),[other]
 jmp original_init
leave_game:
 movm [other],(sp)
 add -4,sp
 call restore,[],4
 add 4,sp
 movm (sp),[other]
 jmp original_trig

game_init:
 movm [d2,d3,a2,a3],(sp)
 add -8,sp
 mov a0,a3
 movm [other],(sp)
 add -4,sp
 call restore,[],4
 add 4,sp
 movm (sp),[other]
 calls original_init
 mov d0,(4,sp)
 call save_guides,[],4
 call new_round,[],4
 call paint,[],4
 mov (4,sp),d0
 ret [d2,d3,a2,a3],24

game_info:
 cmp 0x9014,d0
 beq info_go
 jmp original_info
info_go:
 movm [d2,d3,a2,a3],(sp)
 add -8,sp
 mov a0,a3
check_guess:
 movbu (guess),d0
 movbu (secret),d1
 cmp d1,d0
 beq won
 bcs too_low
 mov 2,d0
 bra checked
too_low:
 mov 1,d0
 bra checked
won:
 mov 3,d0
checked:
 movbu d0,(status)
 bra finish

game_up:
 movm [d2,d3,a2,a3],(sp)
 add -8,sp
 mov a0,a3
 movbu (guess),d0
 inc d0
 cmp 10,d0
 bcs set_guess
 mov 1,d0
 bra set_guess
game_down:
 movm [d2,d3,a2,a3],(sp)
 add -8,sp
 mov a0,a3
 movbu (guess),d0
 add -1,d0
 bne set_guess
 mov 9,d0
set_guess:
 movbu d0,(guess)
 clr d0
 movbu d0,(status)
 bra finish

game_event:
 cmp 0x903e,d0
 beq reset_go
 jmp original_event
reset_go:
 movm [d2,d3,a2,a3],(sp)
 add -8,sp
 mov a0,a3
 call new_round,[],4
finish:
 call paint,[],4
 /* Re-write the existing cursor value through the same facade as ed_info.
  * This asks the stock GUI to redraw without changing a colour setting. */
 call facade,[],4
 mov (a0),a2
 mov (12,a2),a2
 mov sp,a1
 add 4,a1
 mov 2197,d0
 calls (a2)
 cmp 0,d0
 bne finished
 call facade,[],4
 mov (a0),a2
 mov (4,a2),a2
 mov (4,sp),a1
 clr d1
 mov 2197,d0
 calls (a2)
finished:
 mov 1,d0
 ret [d2,d3,a2,a3],24

/* Helpers use CALL [],4. Inputs/outputs scratch d0,d1,a0,a1 only. */
new_round:
 movbu (secret),d0
 add 4,d0
 cmp 10,d0
 bcs round_ok
 add -9,d0
round_ok:
 movbu d0,(secret)
 mov 5,d0
 movbu d0,(guess)
 clr d0
 movbu d0,(status)
 ret [],4
paint:
 movbu (status),d0
 mov d0,d1
 asl 3,d0
 add d1,d0
 movbu (guess),d1
 add d1,d0
 add -1,d0
 asl 3,d0
 mov pictures,a1
 add d0,a1
 mov GDESC,a0
 mov (a1),d0
 mov d0,(12,a0)
 mov GSELECT,a0
 mov d0,(12,a0)
 mov (4,a1),d0
 mov d0,(16,a0)
 mov GDESC,a0
 mov d0,(16,a0)
 ret [],4
save_guides:
 mov GDESC,a0
 mov saved_guides,a1
 mov (12,a0),d0
 mov d0,(a1)
 mov (16,a0),d0
 mov d0,(4,a1)
 mov GSELECT,a0
 mov (12,a0),d0
 mov d0,(8,a1)
 mov (16,a0),d0
 mov d0,(12,a1)
 mov 1,d0
 movbu d0,(active)
 ret [],4
restore:
 movbu (active),d0
 cmp 0,d0
 beq restored
 mov saved_guides,a1
 mov GDESC,a0
 mov (a1),d0
 mov d0,(12,a0)
 mov (4,a1),d0
 mov d0,(16,a0)
 mov GSELECT,a0
 mov (8,a1),d0
 mov d0,(12,a0)
 mov (12,a1),d0
 mov d0,(16,a0)
 clr d0
 movbu d0,(active)
restored:
 ret [],4
.balign 4
game_state:
guess: .byte 5
secret: .byte 0
status: .byte 0
active: .byte 0
saved_guides: .long 0,0,0,0
.include "pictures.inc"
