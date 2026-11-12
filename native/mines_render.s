/* Bounded 384x480 RLE renderer for the Games Minesweeper board.
 * It only copies prepacked words into uncached OSD memory. Each scanline is
 * one HUD row or eight prepacked cell rows; no scanline is encoded at runtime.
 */
.am33_2
.text
.global mines_paint
.extern mines_board, mines_cursor, mines_flags, mines_revealed
.extern mines_flag_count, mines_boom

/* Copy d0 bytes from a1 to a0, advancing a0. d0 is a multiple of four. */
mines_copy_row:
 mov (a1),d1
 mov d1,(a0)
 inc4 a0
 inc4 a1
 add -4,d0
 bne mines_copy_row
 ret [],4

/* Write a two-digit decimal value: d0 value, a0 destination. */
mines_write2:
 clr d1
 add 48,d1
write2_loop:
 cmp 10,d0
 bcs write2_done
 add -10,d0
 inc d1
 bra write2_loop
write2_done:
 movbu d1,(a0)
 add 1,a0
 add 48,d0
 movbu d0,(a0)
 ret [],4

/* Classify a board cell as one of 13 tile kinds; add 13 for the cursor. */
mines_cell_type:
 movm [d2,d3,a2,a3],(sp)
 mov d0,d2
 mov mines_board,a0
 add d2,a0
 movbu (a0),d1
 mov (mines_flags),d0
 and 4,d0
 beq type_live
 mov d1,d0
 and 128,d0
 bne type_lost_mine
 bra type_live
type_lost_mine:
 mov (mines_boom),d0
 cmp d2,d0
 bne type_plain_mine
 mov 12,d0
 bra type_cursor
type_plain_mine:
 mov 11,d0
 bra type_cursor
type_live:
 mov d1,d0
 and 32,d0
 bne type_flagged
 mov d1,d0
 and 64,d0
 beq type_hidden
 mov d1,d0
 and 128,d0
 bne type_plain_mine
 mov d1,d0
 and 15,d0
 cmp 0,d0
 bne type_number
 mov 2,d0
 bra type_cursor
type_number:
 add 2,d0
 bra type_cursor
type_hidden:
 clr d0
 bra type_cursor
type_flagged:
 mov 1,d0
type_cursor:
 mov (mines_cursor),d1
 cmp d1,d2
 bne type_done
 add 13,d0
type_done:
 movm (sp),[d2,d3,a2,a3]
 ret [],4

mines_paint:
 movm [d2,d3,a2,a3],(sp)
 add -16,sp
 /* Refresh the three two-digit HUD counters. */
 mov 10,d0
 mov (mines_flag_count),d1
 sub d1,d0
 cmp 0,d0
 bge digits_left_ok
 clr d0
digits_left_ok:
 mov mines_left_digits,a0
 call mines_write2,[],4
 mov (mines_revealed),d0
 cmp 100,d0
 bcs digits_open_ok
 mov 99,d0
digits_open_ok:
 mov mines_open_digits,a0
 call mines_write2,[],4
 mov (mines_flag_count),d0
 cmp 100,d0
 bcs digits_flags_ok
 mov 99,d0
digits_flags_ok:
 mov mines_flags_digits,a0
 call mines_write2,[],4
 mov mines_buffer+0x40000000,a3
 mov 0x0b17f1df,d0
 mov d0,(a3)
 inc4 a3
 clr d2
render_row:
 mov mines_y_mode,a0
 add d2,a0
 movbu (a0),d0
 cmp 1,d0
 beq hud_blank
 cmp 2,d0
 beq hud_chars
/* One board scanline: eight prepacked cell rows. */
board_line:
 mov mines_y_cell,a0
 add d2,a0
 movbu (a0),d0
 asl 3,d0
 mov d0,(4,sp)
 mov mines_y_style,a0
 add d2,a0
 movbu (a0),d0
 mov d0,(8,sp)
 clr d3
tile_column:
 mov (4,sp),d0
 add d3,d0
 call mines_cell_type,[],4
 mov d0,d1
 asl 3,d1
 sub d0,d1
 mov (8,sp),d0
 add d0,d1
 asl 3,d1
 mov mines_tile_rows,a2
 add d1,a2
 bra copy_entry
/* A blank HUD scanline is one whole-line RLE word. */
hud_blank:
 mov mines_blank_row,a2
 mov (a2),d0
 mov (4,a2),a1
 mov a3,a0
 call mines_copy_row,[],4
 mov a0,a3
 bra row_done
/* A text HUD scanline is 32 prepacked character rows. */
hud_chars:
 mov mines_y_style,a0
 add d2,a0
 movbu (a0),d0
 mov d0,(8,sp)
 mov mines_hud_top,a0
 cmp 432,d2
 bcs hud_text_ready
 mov mines_hud_play,a0
 mov (mines_flags),d1
 and 2,d1
 cmp 0,d1
 beq hud_not_won
 mov mines_hud_won,a0
 bra hud_text_ready
hud_not_won:
 mov (mines_flags),d1
 and 4,d1
 cmp 0,d1
 beq hud_text_ready
 mov mines_hud_dead,a0
hud_text_ready:
 mov a0,(12,sp)
 clr d3
char_column:
 mov (12,sp),a0
 movbu (d3,a0),d0
 mov d0,d1
 asl 2,d0
 add d1,d0
 mov (8,sp),d1
 add d1,d0
 asl 2,d0
 mov mines_char_rows,a1
 add d0,a1
 mov (a1),a1
 mov a3,a0
 mov 8,d0
 call mines_copy_row,[],4
 mov a0,a3
 inc d3
 cmp 32,d3
 bne char_column
 bra row_done
copy_entry:
 mov (a2),d0
 mov (4,a2),a1
 mov a3,a0
 call mines_copy_row,[],4
 mov a0,a3
 inc d3
 cmp 8,d3
 bne tile_column
row_done:
 inc d2
 cmp 480,d2
 bne render_row
 add 16,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4

.include "mines_assets.inc"
