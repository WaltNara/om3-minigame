/* Breakout uses the same prepacked chunks and buffer as Mario, exclusively.
 * Every world row consists of 96 logical pixels, repeated four scanlines. */
.am33_2
.text
.global breakout_paint
breakout_paint:
 movm [d2,d3,a2,a3],(sp)
 add -24,sp
 mov mario_buffer+0x40000000,a3
 mov 0x0b17f1df,d0
 mov d0,(a3)
 inc4 a3
 clr d2
br_paint_rows:
 cmp 96,d2
 blt br_header
 cmp 432,d2
 bge br_footer_row
 mov mario_scratch,a0
 mov 24,d0
 clr d1
br_clear:
 mov d1,(a0)
 inc4 a0
 add -1,d0
 bne br_clear
 mov d2,d3
 lsr 2,d3
 mov 0,d0
 mov 2,d1
 call br_span,[],4
 mov 94,d0
 mov 96,d1
 call br_span,[],4
 cmp 24,d3
 bne br_draw_bricks
 mov 0,d0
 mov 96,d1
 call br_span,[],4
br_draw_bricks:
 mov breakout_rects,a2
 clr d0
 mov d0,(8,sp)
br_draw_brick:
 mov (8,sp),d0
 mov breakout_bricks,a0
 add d0,a0
 movbu (a0),d0
 cmp 0,d0
 beq br_draw_next
 mov (8,a2),d0
 cmp d0,d3
 blt br_draw_next
 mov (12,a2),d0
 cmp d0,d3
 bge br_draw_next
 mov (a2),d0
 mov (4,a2),d1
 call br_span,[],4
br_draw_next:
 add 16,a2
 mov (8,sp),d0
 inc d0
 mov d0,(8,sp)
 cmp 18,d0
 bne br_draw_brick
 cmp 102,d3
 blt br_ball
 cmp 104,d3
 bge br_ball
 mov (breakout_state),d0
 mov d0,d1
 add 20,d1
 call br_span,[],4
br_ball:
 mov (breakout_state+8),d0
 cmp d0,d3
 blt br_chunks
 add 2,d0
 cmp d0,d3
 bge br_chunks
 mov (breakout_state+4),d0
 mov d0,d1
 add 2,d1
 call br_span,[],4
br_chunks:
 mov mario_row_buffer,a0
 mov mario_scratch,a2
 mov 12,d3
br_chunk_loop:
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
 bne br_chunk_loop
 mov a0,d0
 mov mario_row_buffer,d1
 sub d1,d0
 mov d0,(4,sp)
 mov 4,d3
br_repeat_row:
 mov (4,sp),d0
 mov mario_row_buffer,a1
 mov a3,a0
 call mr_copy,[],4
 mov a0,a3
 add -1,d3
 bne br_repeat_row
 add 4,d2
 bra br_paint_rows
br_header:
 cmp 48,d2
 bge br_life_header
 mov (breakout_state+20),d0
 mov br_titles,a1
 bra br_header_index
br_life_header:
 mov (breakout_state+24),d0
 mov br_lives,a1
br_header_index:
 mov d0,d1
 asl 1,d0
 add d1,d0
 asl 3,d0
 mov d2,d1
 cmp 48,d1
 blt br_head_y
 add -48,d1
br_head_y:
 lsr 1,d1
 add d1,d0
 asl 3,d0
 add d0,a1
 bra br_copy_static
br_footer_row:
 cmp 480,d2
 beq br_paint_done
 mov (breakout_state+20),d0
 mov d0,d1
 asl 1,d0
 add d1,d0
 asl 3,d0
 mov d2,d1
 add -432,d1
 lsr 1,d1
 add d1,d0
 asl 3,d0
 mov br_footer,a1
 add d0,a1
br_copy_static:
 mov (a1),d0
 mov (4,a1),a1
 mov a3,a0
 call mr_copy,[],4
 mov a0,a3
 inc d2
 bra br_paint_rows
br_paint_done:
 add 24,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4
/* Set [d0,d1) in the scratch row; clip defensively. */
br_span:
 cmp 0,d0
 bge br_span_hi
 clr d0
br_span_hi:
 cmp 96,d1
 ble br_span_begin
 mov 96,d1
br_span_begin:
 cmp d1,d0
 bge br_span_done
 mov mario_scratch,a0
 add d0,a0
 sub d0,d1
 mov 1,d0
br_span_loop:
 movbu d0,(a0)
 inc a0
 add -1,d1
 bne br_span_loop
br_span_done:
 ret [],4
.include "breakout_assets.inc"
