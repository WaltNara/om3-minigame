/* Native 2048 / OM-3 1.1. Caduceus integration (Apache-2.0).
 * No heap, framebuffer, timers or animation. Byte exponents, fixed scratch.
 * Native render copies prepacked RLE rows directly into uncached OSD memory. */
.am33_2
.text
.include "original.inc"
.global game_init,other_init,leave_game,game_info,game_event
.global game_up,game_down,game_left,game_right,game_nav,game_bitmap
.global game_transition
.global game_state,board,score,rng,moves,flags,active,slide,spawn,check_over,paint,new_round,play_move
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
/* Picture Mode's CALLS handler. Preserve MDR across nested calls. */
game_nav:
 movm [d2],(sp)
 movbu (active),d2
 cmp 0,d2
 beq nav_stock
 cmp 0x9004,d0
 beq nav_up
 cmp 0x9006,d0
 beq nav_down
 cmp 0x9008,d0
 beq nav_left
 cmp 0x900a,d0
 beq nav_right
nav_stock:
 movm (sp),[d2]
 jmp original_pm
nav_up:
 clr d0
 bra nav_go
nav_down:
 mov 1,d0
 bra nav_go
nav_left:
 mov 2,d0
 bra nav_go
nav_right:
 mov 3,d0
nav_go:
 movm (sp),[d2]
 movm [d2,d3,a2,a3],(sp)
 add -8,sp
 mov mdr,d1
 mov d1,(4,sp)
 call play_move,[],4
 cmp 0,d0
 beq nav_drawn
 call redraw,[],4
nav_drawn:
 mov (4,sp),d1
 mov d1,mdr
 add 8,sp
 movm (sp),[d2,d3,a2,a3]
 clr d0
 mov 8,d1
 rets
/* Wheel dial CALLS handlers. */
game_up:
 clr d0
 bra move_entry
game_down:
 mov 1,d0
 bra move_entry
game_left:
 mov 2,d0
 bra move_entry
game_right:
 mov 3,d0
move_entry:
 movm [d2,d3,a2,a3],(sp)
 add -4,sp
 call play_move,[],4
 cmp 0,d0
 beq move_drawn
 call redraw,[],4
move_drawn:
 mov 1,d0
 ret [d2,d3,a2,a3],20
game_info:
 cmp 0x9014,d0
 bne info_stock
 mov 1,d0
 rets
info_stock:
 jmp original_info
game_event:
 cmp 0x903e,d0
 beq restart
 jmp original_event
restart:
 movm [d2,d3,a2,a3],(sp)
 add -4,sp
 call new_round,[],4
 call paint,[],4
 call redraw,[],4
 mov 1,d0
 ret [d2,d3,a2,a3],20
/* Stock 96-byte GPI CALL frame. Only our bitmap is repositioned. */
game_bitmap:
 mov a1,d2
 cmp board_buffer+0x40000000,d2
 bne bitmap_stock
 mov 258,d0
 mov 60,d1
bitmap_stock:
 mov d1,d2
 mov a0,(44,sp)
 mov a1,(40,sp)
 jmp original_bitmap_resume
/* Clear the game and restore both guides on any real screen transition. */
game_transition:
 cmp 0,d0
 beq transition_stock
 movm [other],(sp)
 add -4,sp
 call restore,[],4
 add 4,sp
 movm (sp),[other]
transition_stock:
 jmp original_gx
play_move:
 movm [d2,d3,a2,a3],(sp)
 add -4,sp
 call slide,[],4
 cmp 0,d0
 beq played
 mov (moves),d0
 inc d0
 mov d0,(moves)
 call spawn,[],4
 call check_over,[],4
 call paint,[],4
 mov 1,d0
 bra played_return
played:
 clr d0
played_return:
 add 4,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4
/* Pure slide/merge/score. No spawning, graphics or firmware calls. */
slide:
 movm [d2,d3,a2,a3],(sp)
 add -24,sp
 asl 4,d0
 mov move_maps,a2
 add d0,a2
 mov board,a0
 mov before,a1
 mov 4,d0
copy_before:
 mov (a0),d1
 mov d1,(a1)
 inc4 a0
 inc4 a1
 add -1,d0
 bne copy_before
 clr d2
line_loop:
 mov a2,(4,sp)
 clr d0
 mov d0,(linebuf)
 mov d0,(lineout)
 mov d0,(8,sp)
 clr d3
gather:
 movbu (d3,a2),d0
 mov board,a0
 add d0,a0
 movbu (a0),d0
 cmp 0,d0
 beq gathered
 mov (8,sp),d1
 mov linebuf,a0
 add d1,a0
 movbu d0,(a0)
 inc d1
 mov d1,(8,sp)
gathered:
 inc d3
 cmp 4,d3
 bne gather
 clr d3
 clr d0
 mov d0,(12,sp)
merge_loop:
 mov (8,sp),d0
 cmp d0,d3
 bcc scatter_start
 mov linebuf,a0
 add d3,a0
 movbu (a0),d0
 inc d3
 mov (8,sp),d1
 cmp d1,d3
 bcc no_merge
 movbu (1,a0),d1
 cmp d0,d1
 bne no_merge
 inc d0
 inc d3
 mov 1,d1
 asl d0,d1
 mov (score),a0
 add d1,a0
 mov a0,(score)
no_merge:
 mov (12,sp),d1
 mov lineout,a0
 add d1,a0
 movbu d0,(a0)
 inc d1
 mov d1,(12,sp)
 bra merge_loop
scatter_start:
 clr d3
 mov (4,sp),a2
scatter:
 movbu (d3,a2),d0
 mov board,a0
 add d0,a0
 mov lineout,a1
 add d3,a1
 movbu (a1),d0
 movbu d0,(a0)
 inc d3
 cmp 4,d3
 bne scatter
 add 4,a2
 inc d2
 cmp 4,d2
 bne line_loop
 mov board,a0
 mov before,a1
 mov 4,d1
compare:
 mov (a0),d0
 mov (a1),d2
 cmp d2,d0
 bne changed
 inc4 a0
 inc4 a1
 add -1,d1
 bne compare
 clr d0
 add 24,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4
changed:
 mov 1,d0
 add 24,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4
/* Xorshift32 and multiply-high selection, no OS random service/division. */
random:
 mov (rng),d0
 mov d0,d1
 asl 13,d1
 xor d1,d0
 mov d0,d1
 lsr 17,d1
 xor d1,d0
 mov d0,d1
 asl 5,d1
 xor d1,d0
 mov d0,(rng)
 ret [],4
spawn:
 movm [d2,d3,a2,a3],(sp)
 add -4,sp
 mov board,a2
 mov empties,a3
 clr d2
 clr d3
find_empty:
 movbu (d2,a2),d0
 cmp 0,d0
 bne occupied
 movbu d2,(d3,a3)
 inc d3
occupied:
 inc d2
 cmp 16,d2
 bne find_empty
 cmp 0,d3
 beq no_empty
 call random,[],4
 and 65535,d0
 mul d3,d0
 lsr 16,d0
 movbu (d0,a3),d2
 call random,[],4
 and 65535,d0
 mov 10,d1
 mul d1,d0
 lsr 16,d0
 cmp 0,d0
 mov 1,d1
 bne spawn_two
 mov 2,d1
spawn_two:
 movbu d1,(d2,a2)
 mov 1,d0
 add 4,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4
no_empty:
 clr d0
 add 4,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4
new_round:
 movm [d2,d3,a2,a3],(sp)
 add -4,sp
 clr d0
 mov d0,(board)
 mov d0,(board+4)
 mov d0,(board+8)
 mov d0,(board+12)
 mov d0,(score)
 mov d0,(moves)
 mov d0,(flags)
 call spawn,[],4
 call spawn,[],4
 add 4,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4
/* bit 0: no moves, bit 1: reached 2048 (play continues). */
check_over:
 movm [d2,d3,a2,a3],(sp)
 clr d2
 clr d3
 mov board,a2
 mov 1,a3
over_loop:
 movbu (d2,a2),d0
 cmp 11,d0
 bcs not_won
 or 2,d3
not_won:
 cmp 0,d0
 beq can_play
 mov d2,d1
 and 3,d1
 cmp 3,d1
 beq below
 mov d2,a0
 add a2,a0
 movbu (1,a0),d1
 cmp d0,d1
 beq can_play
below:
 cmp 12,d2
 bcc next_over
 mov d2,a0
 add a2,a0
 movbu (4,a0),d1
 cmp d0,d1
 bne next_over
can_play:
 mov 0,a3
next_over:
 inc d2
 cmp 16,d2
 bne over_loop
 mov a3,d0
 or d0,d3
 mov d3,(flags)
 mov d3,d0
 movm (sp),[d2,d3,a2,a3]
 ret [],4
/* Whole-word packed row copies
 destination uses uncached alias. */
copy_row:
 mov (a1),d1
 mov d1,(a0)
 inc4 a0
 inc4 a1
 add -4,d0
 bne copy_row
 ret [],4
paint:
 movm [d2,d3,a2,a3],(sp)
 add -16,sp
 mov (score),d2
 mov powers10,a2
 mov score_digits,a3
 mov 8,d3
score_digit:
 mov (a2),d1
 mov 48,d0
score_sub:
 cmp d1,d2
 bcs digit_done
 sub d1,d2
 inc d0
 bra score_sub
digit_done:
 movbu d0,(a3)
 inc a3
 inc4 a2
 add -1,d3
 bne score_digit
 mov board_buffer+0x40000000,a3
 mov 0x0b17f1df,d0
 mov d0,(a3)
 inc4 a3
 clr d2
render_row:
 cmp 48,d2
 bcs hud_row
 cmp 432,d2
 bcc hud_row
 mov d2,d0
 add -48,d0
 mov d0,d1
 clr d0
large_div96:
 cmp 96,d1
 bcs large_div96_done
 add -96,d1
 inc d0
 bra large_div96
large_div96_done:
 asl2 d0
 mov d0,(4,sp)
 cmp 6,d1
 bcs gap_line
 clr d0
 cmp 40,d1
 bcs style_done
 cmp 55,d1
 bcc style_done
 add -40,d1
 clr d0
large_div3:
 cmp 3,d1
 bcs large_div3_done
 add -3,d1
 inc d0
 bra large_div3
large_div3_done:
 mov d0,d1
 inc d1
 mov d1,d0
style_done:
 mov d0,(8,sp)
 clr d3
tile_column:
 mov (4,sp),d0
 add d3,d0
 mov board,a0
 add d0,a0
 movbu (a0),d0
 cmp 18,d0
 bcs safe_tile
 mov 17,d0
safe_tile:
 mov d0,d1
 asl 1,d0
 add d1,d0
 asl 1,d0
 mov (8,sp),d1
 add d1,d0
 asl 3,d0
 mov tile_rows,a2
 add d0,a2
 bra copy_tile
gap_line:
 clr d3
gap_column:
 mov gap_row,a2
copy_tile:
 mov (a2),d0
 mov (4,a2),a1
 mov a3,a0
 call copy_row,[],4
 mov a0,a3
 inc d3
 cmp 4,d3
 beq row_done
 mov d2,d0
 add -48,d0
large_gap_mod:
 cmp 96,d0
 bcs large_gap_done
 add -96,d0
 bra large_gap_mod
large_gap_done:
 cmp 6,d0
 bcs gap_column
 bra tile_column
hud_row:
 mov hud_top,a2
 mov d2,d0
 cmp 432,d2
 bcs hud_style
 add -432,d0
 mov hud_play,a2
 mov (flags),d1
 btst 2,d1
 beq hud_not_won
 mov hud_won,a2
hud_not_won:
 btst 1,d1
 beq hud_style
 mov hud_dead,a2
hud_style:
 cmp 12,d0
 bcs blank_line
 cmp 27,d0
 bcc blank_line
 add -12,d0
 clr d1
large_hud_div3:
 cmp 3,d0
 bcs large_hud_done
 add -3,d0
 inc d1
 bra large_hud_div3
large_hud_done:
 mov d1,d0
 mov d0,(12,sp)
 clr d3
char_column:
 movbu (d3,a2),d0
 mov d0,d1
 asl2 d0
 add d1,d0
 mov (12,sp),d1
 add d1,d0
 asl2 d0
 mov char_rows,a1
 add d0,a1
 mov (a1),a1
 mov a3,a0
 mov 8,d0
 call copy_row,[],4
 mov a0,a3
 inc d3
 cmp 32,d3
 bne char_column
 bra row_done
blank_line:
 mov blank_row,a1
 mov (a1),d0
 mov (4,a1),a1
 mov a3,a0
 call copy_row,[],4
 mov a0,a3
row_done:
 inc d2
 cmp 480,d2
 bne render_row
 mov a3,d0
 mov board_buffer+0x40000000,d1
 sub d1,d0
 mov d0,(render_bytes)
 mov GDESC,a0
 mov d0,(12,a0)
 mov GSELECT,a1
 mov d0,(12,a1)
 mov board_buffer+0x40000000,d0
 mov d0,(16,a0)
 mov d0,(16,a1)
 add 16,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4
/* Rewriting the current editor cursor asks the existing GUI to redraw. */
redraw:
 movm [d2,d3,a2,a3],(sp)
 add -8,sp
 call facade,[],4
 mov (a0),a2
 mov (12,a2),a2
 mov sp,a1
 add 4,a1
 mov 2197,d0
 calls (a2)
 cmp 0,d0
 bne redrawn
 call facade,[],4
 mov (a0),a2
 mov (4,a2),a2
 mov (4,sp),a1
 clr d1
 mov 2197,d0
 calls (a2)
redrawn:
 add 8,sp
 movm (sp),[d2,d3,a2,a3]
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
board: .space 16,0
score: .long 0
rng: .long 0x6d2b79f5
moves: .long 0
flags: .long 0
active: .byte 0
 .balign 4
render_bytes: .long 0
saved_guides: .long 0,0,0,0
before: .space 16,0
linebuf: .long 0
lineout: .long 0
empties: .space 16,0
game_gc: .space 32,0
.include "assets.inc"

