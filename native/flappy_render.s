/* Flappy uses the same prepacked chunks and buffer as Mario, exclusively.
 * Every world row consists of 96 logical pixels, repeated four scanlines. */
.am33_2
.text
.global flappy_paint
flappy_paint:
 movm [d2,d3,a2,a3],(sp)
 add -24,sp
 mov (flappy_state+20),d2
 mov fp_distance_digits,a3
 mov powers10,a2
 mov 8,d3
fp_score_digit:
 mov (a2),d1
 mov 48,d0
fp_score_sub:
 cmp d1,d2
 bcs fp_score_ready
 sub d1,d2
 inc d0
 bra fp_score_sub
fp_score_ready:
 movbu d0,(a3)
 inc a3
 inc4 a2
 add -1,d3
 bne fp_score_digit
 mov mario_buffer+0x40000000,a3
 mov 0x0b17f1df,d0
 mov d0,(a3)
 inc4 a3
 clr d2
fp_paint_rows:
 cmp 96,d2
 blt fp_header
 cmp 432,d2
 bge fp_footer_row
 mov mario_scratch,a0
 mov 24,d0
 clr d1
fp_clear:
 mov d1,(a0)
 inc4 a0
 add -1,d0
 bne fp_clear
 mov d2,d3
 lsr 2,d3
 mov 0,d0
 mov 2,d1
 call br_span,[],4
 mov 94,d0
 mov 96,d1
 call br_span,[],4
 cmp 12,d3
 bne fp_draw_bricks
 mov 0,d0
 mov 96,d1
 call br_span,[],4
fp_draw_bricks:
 mov (flappy_state+12),d0
 cmp d0,d3
 blt fp_pipe
 add 32,d0
 cmp d0,d3
 blt fp_second_pipe
fp_pipe:
 mov (flappy_state+8),d0
 mov d0,d1
 add 12,d1
 call br_span,[],4
fp_second_pipe:
 mov (flappy_state+32),d0
 cmp d0,d3
 blt fp_second_span
 add 32,d0
 cmp d0,d3
 blt fp_bird
fp_second_span:
 mov (flappy_state+28),d0
 mov d0,d1
 add 12,d1
 call br_span,[],4
fp_bird:
 mov (flappy_state),d0
 lsr 2,d0
 cmp d0,d3
 blt fp_chunks
 add 4,d0
 cmp d0,d3
 bge fp_chunks
 mov 24,d0
 mov 30,d1
 call br_span,[],4
fp_chunks:
 mov mario_row_buffer,a0
 mov mario_scratch,a2
 mov 12,d3
fp_chunk_loop:
 clr d0
 movbu (7,a2),d1
 or d1,d0
 asl 1,d0
 movbu (6,a2),d1
 or d1,d0
 asl 1,d0
 movbu (5,a2),d1
 or d1,d0
 asl 1,d0
 movbu (4,a2),d1
 or d1,d0
 asl 1,d0
 movbu (3,a2),d1
 or d1,d0
 asl 1,d0
 movbu (2,a2),d1
 or d1,d0
 asl 1,d0
 movbu (1,a2),d1
 or d1,d0
 asl 1,d0
 movbu (a2),d1
 or d1,d0
 add 8,a2
 asl 3,d0
 mov mario_chunks,a1
 add d0,a1
 mov (a1),d0
 mov (4,a1),a1
 call mr_copy,[],4
 add -1,d3
 bne fp_chunk_loop
 mov a0,d0
 mov mario_row_buffer,d1
 sub d1,d0
 mov d0,(4,sp)
 mov 4,d3
fp_repeat_row:
 mov (4,sp),d0
 mov mario_row_buffer,a1
 mov a3,a0
 call mr_copy,[],4
 mov a0,a3
 add -1,d3
 bne fp_repeat_row
 add 4,d2
 bra fp_paint_rows
fp_header:
 cmp 48,d2
 bge fp_score_row
 mov (flappy_state+16),d0
 mov fp_titles,a1
fp_header_index:
 mov d0,d1
 asl 1,d0
 add d1,d0
 asl 3,d0
 mov d2,d1
 cmp 48,d1
 blt fp_head_y
 add -48,d1
fp_head_y:
 lsr 1,d1
 add d1,d0
 asl 3,d0
 add d0,a1
 bra fp_copy_static
fp_footer_row:
 cmp 480,d2
 beq fp_paint_done
 mov (flappy_state+16),d0
 mov d0,d1
 asl 1,d0
 add d1,d0
 asl 3,d0
 mov d2,d1
 add -432,d1
 lsr 1,d1
 add d1,d0
 asl 3,d0
 mov fp_footer,a1
 add d0,a1
fp_copy_static:
 mov (a1),d0
 mov (4,a1),a1
 mov a3,a0
 call mr_copy,[],4
 mov a0,a3
 inc d2
 bra fp_paint_rows
fp_score_row:
 cmp 60,d2
 blt fp_score_blank
 cmp 75,d2
 bge fp_score_blank
 mov d2,d0
 add -60,d0
 clr d1
fp_score_div:
 cmp 3,d0
 bcs fp_score_style
 add -3,d0
 inc d1
 bra fp_score_div
fp_score_style:
 mov d1,(12,sp)
 clr d3
fp_score_char:
 mov fp_score_text,a0
 movbu (d3,a0),d0
 add -32,d0
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
 call mr_copy,[],4
 mov a0,a3
 inc d3
 cmp 32,d3
 bne fp_score_char
 bra fp_score_next
fp_score_blank:
 mov blank_row,a1
 mov (a1),d0
 mov (4,a1),a1
 mov a3,a0
 call mr_copy,[],4
 mov a0,a3
fp_score_next:
 inc d2
 bra fp_paint_rows
fp_paint_done:
 add 24,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4
.include "flappy_assets.inc"
.balign 4
.global fp_score_text
fp_score_text: .ascii "DISTANCE "
fp_distance_digits: .ascii "00000000M              "
