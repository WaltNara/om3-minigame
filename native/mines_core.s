/* Event-driven 8x8 Minesweeper rules for the OM-3 Games row.
 * No heap, no timer, no firmware calls and no retained GUI pointers.
 * Board byte: bit 7 mine, bit 6 revealed, bit 5 flag, bits 0-3 neighbour count.
 * Mines are placed on the first opening move, never in that 3x3 area.
 * Flags: bit 0 started, bit 1 won, bit 2 lost.
 */
.am33_2
.text
.extern mines_neighbors
.global mines_reset, mines_move, mines_open, mines_flag
.global mines_board, mines_cursor, mines_flags, mines_revealed
.global mines_flag_count, mines_boom, mines_rng, mines_moves

/* Xorshift32, as used by the 2048 build. No OS random service or division. */
mines_random:
 mov (mines_rng),d0
 mov d0,d1
 asl 13,d1
 xor d1,d0
 mov d0,d1
 lsr 17,d1
 xor d1,d0
 mov d0,d1
 asl 5,d1
 xor d1,d0
 mov d0,(mines_rng)
 ret [],4

/* Start a fresh round. The board stays empty until the first opening move. */
mines_reset:
 movm [d2,d3,a2,a3],(sp)
 add -4,sp
 mov mines_board,a0
 clr d0
 mov 16,d1
reset_loop:
 mov d0,(a0)
 inc4 a0
 add -1,d1
 bne reset_loop
 clr d0
 mov d0,(mines_cursor)
 mov d0,(mines_flags)
 mov d0,(mines_revealed)
 mov d0,(mines_flag_count)
 mov d0,(mines_moves)
 mov -1,d0
 mov d0,(mines_boom)
 call mines_random,[],4
 add 4,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4

/* d0: 0 up, 1 down, 2 left, 3 right. Returns 1 when the cursor moved. */
mines_move:
 movm [d2,d3,a2,a3],(sp)
 mov (mines_cursor),d1
 mov d1,d2
 and 7,d2
 lsr 3,d1
 cmp 0,d0
 bne move_not_up
 add -1,d1
 and 7,d1
 bra move_done
move_not_up:
 cmp 1,d0
 bne move_not_down
 inc d1
 and 7,d1
 bra move_done
move_not_down:
 cmp 2,d0
 bne move_not_left
 add -1,d2
 and 7,d2
 bra move_done
move_not_left:
 cmp 3,d0
 bne move_bad
 inc d2
 and 7,d2
move_done:
 asl 3,d1
 add d2,d1
 mov (mines_cursor),d0
 cmp d1,d0
 beq move_bad
 mov d1,(mines_cursor)
 mov (mines_moves),d0
 inc d0
 mov d0,(mines_moves)
 mov 1,d0
 bra move_ret
move_bad:
 clr d0
move_ret:
 movm (sp),[d2,d3,a2,a3]
 ret [],4

/* Toggle a flag on the cursor cell. Revealed cells cannot be flagged. */
mines_flag:
 movm [d2,d3,a2,a3],(sp)
 mov (mines_flags),d0
 and 6,d0
 bne flag_bad
 mov (mines_cursor),d0
 mov mines_board,a0
 add d0,a0
 movbu (a0),d1
 mov d1,d2
 and 64,d2
 bne flag_bad
 mov d1,d2
 and 32,d2
 bne flag_remove
 or 32,d1
 mov (mines_flag_count),d2
 inc d2
 bra flag_store
flag_remove:
 and 223,d1
 mov (mines_flag_count),d2
 add -1,d2
flag_store:
 movbu d1,(a0)
 mov d2,(mines_flag_count)
 mov 1,d0
 bra flag_ret
flag_bad:
 clr d0
flag_ret:
 movm (sp),[d2,d3,a2,a3]
 ret [],4

/* Mark one cell revealed. d0 is the cell index. */
mines_reveal_cell:
 mov mines_board,a0
 add d0,a0
 movbu (a0),d1
 or 64,d1
 movbu d1,(a0)
 mov (mines_revealed),d1
 inc d1
 mov d1,(mines_revealed)
 ret [],4

/* Place ten mines away from d0, then count neighbours for every safe cell. */
mines_place:
 movm [d2,d3,a2,a3],(sp)
 add -24,sp
 mov d0,(4,sp)
 mov mines_safe,a0
 clr d0
 mov 16,d1
place_clear:
 mov d0,(a0)
 inc4 a0
 add -1,d1
 bne place_clear
 mov mines_safe,a0
 mov (4,sp),d1
 add d1,a0
 mov 1,d1
 movbu d1,(a0)
 mov (4,sp),d0
 asl 3,d0
 mov mines_neighbors,a1
 add d0,a1
 mov 8,d2
place_safe:
 movbu (a1),d0
 add 1,a1
 cmp 255,d0
 beq place_safe_next
 mov mines_safe,a0
 add d0,a0
 mov 1,d1
 movbu d1,(a0)
place_safe_next:
 add -1,d2
 bne place_safe
 clr d2
 clr d3
place_mine_loop:
 cmp 10,d2
 bge place_counts
 inc d3
 cmp 256,d3
 bge place_counts
 call mines_random,[],4
 and 63,d0
 mov d0,(8,sp)
 mov mines_safe,a0
 add d0,a0
 movbu (a0),d1
 cmp 0,d1
 bne place_mine_loop
 mov mines_board,a0
 mov (8,sp),d1
 add d1,a0
 movbu (a0),d1
 and 128,d1
 bne place_mine_loop
 or 128,d1
 movbu d1,(a0)
 inc d2
 bra place_mine_loop
place_counts:
 clr d2
place_cell:
 mov mines_board,a0
 mov d2,d0
 add d0,a0
 movbu (a0),d1
 and 128,d1
 bne place_next
 mov d2,d0
 asl 3,d0
 mov mines_neighbors,a1
 add d0,a1
 clr d3
 mov 8,d0
 mov d0,(12,sp)
place_neighbour:
 movbu (a1),d0
 add 1,a1
 cmp 255,d0
 beq place_neighbour_next
 mov mines_board,a2
 add d0,a2
 movbu (a2),d1
 and 128,d1
 beq place_neighbour_next
 inc d3
place_neighbour_next:
 mov (12,sp),d0
 add -1,d0
 mov d0,(12,sp)
 bne place_neighbour
 mov mines_board,a0
 mov d2,d0
 add d0,a0
 movbu (a0),d1
 or d3,d1
 movbu d1,(a0)
place_next:
 inc d2
 cmp 64,d2
 bne place_cell
 add 24,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4

/* Open the cursor cell, expand empty areas and resolve win or loss. */
mines_open:
 movm [d2,d3,a2,a3],(sp)
 add -24,sp
 mov (mines_flags),d0
 and 6,d0
 bne open_bad
 mov (mines_flags),d0
 and 1,d0
 bne open_placed
 mov (mines_cursor),d0
 call mines_place,[],4
 mov (mines_flags),d0
 or 1,d0
 mov d0,(mines_flags)
open_placed:
 mov (mines_cursor),d0
 mov mines_board,a0
 add d0,a0
 movbu (a0),d1
 mov d1,d2
 and 96,d2
 bne open_bad
 mov d1,d2
 and 128,d2
 bne open_boom
 mov (mines_cursor),d0
 call mines_reveal_cell,[],4
 mov mines_queue,a0
 mov (mines_cursor),d1
 movbu d1,(a0)
 clr d0
 mov d0,(4,sp)
 mov 1,d0
 mov d0,(8,sp)
open_queue_loop:
 mov (4,sp),d0
 mov (8,sp),d1
 cmp d1,d0
 bge open_queue_done
 inc d0
 mov d0,(4,sp)
 add -1,d0
 mov mines_queue,a0
 add d0,a0
 movbu (a0),d0
 mov mines_board,a1
 add d0,a1
 movbu (a1),d1
 and 15,d1
 bne open_queue_loop
 mov d0,(12,sp)
 asl 3,d0
 mov mines_neighbors,a2
 add d0,a2
 mov 8,d0
 mov d0,(16,sp)
open_neighbour:
 movbu (a2),d0
 add 1,a2
 cmp 255,d0
 beq open_neighbour_next
 mov d0,(20,sp)
 mov mines_board,a1
 add d0,a1
 movbu (a1),d1
 and 224,d1
 bne open_neighbour_next
 mov (20,sp),d0
 call mines_reveal_cell,[],4
 mov mines_board,a1
 mov (20,sp),d0
 add d0,a1
 movbu (a1),d1
 and 15,d1
 bne open_neighbour_next
 mov mines_queue,a0
 mov (8,sp),d0
 add d0,a0
 mov (20,sp),d1
 movbu d1,(a0)
 inc d0
 mov d0,(8,sp)
open_neighbour_next:
 mov (16,sp),d0
 add -1,d0
 mov d0,(16,sp)
 bne open_neighbour
 bra open_queue_loop
open_queue_done:
 mov (mines_revealed),d0
 cmp 54,d0
 bne open_ret_ok
 mov (mines_flags),d0
 or 2,d0
 mov d0,(mines_flags)
 mov mines_board,a0
 clr d2
open_win_flag:
 movbu (d2,a0),d0
 and 128,d0
 beq open_win_next
 movbu (d2,a0),d0
 or 32,d0
 movbu d0,(d2,a0)
open_win_next:
 inc d2
 cmp 64,d2
 bne open_win_flag
 mov 10,d0
 mov d0,(mines_flag_count)
 bra open_ret_ok
open_boom:
 mov (mines_flags),d0
 or 4,d0
 mov d0,(mines_flags)
 mov (mines_cursor),d0
 mov d0,(mines_boom)
 mov mines_board,a0
 clr d2
open_show:
 movbu (d2,a0),d0
 and 128,d0
 beq open_show_next
 movbu (d2,a0),d0
 or 64,d0
 movbu d0,(d2,a0)
open_show_next:
 inc d2
 cmp 64,d2
 bne open_show
open_ret_ok:
 mov 1,d0
 bra open_ret
open_bad:
 clr d0
open_ret:
 add 24,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4

.balign 4
mines_board: .space 64,0
mines_cursor: .long 0
mines_flags: .long 0
mines_revealed: .long 0
mines_flag_count: .long 0
mines_boom: .long -1
mines_rng: .long 0x6d2b79f5
mines_moves: .long 0
.balign 4
mines_queue: .space 64,0
mines_safe: .space 64,0
