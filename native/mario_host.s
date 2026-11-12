/* Emulator-only label hook for the experimental Games row. */
.am33_2
.text
.extern original_string
.extern original_update, original_pm, original_transition, games_event, games_state
.extern queue_resume, queue_entry, paint_resume, original_end, bitmap, games_selection, invalidate
.extern new_round, paint, play_move, board_buffer
.global games_paint_msg
.global games_string, games_update, games_pm, games_transition, games_row_selected, games_screen, games_queue_hook, games_paint_valid, games_render_hook, games_draw_count, games_render_seen, games_render_state, games_dial_hook
games_string:
 cmp 0x7f08,d0
 bne label_go
 mov title,a0
 ret [d2],8
label_go:
 cmp 0x7f09,d0
 bne stock
 mov go_title,a0
 ret [d2],8
stock:
 jmp original_string
/* Called before Caduceus's Picture Mode update. a0/d0 are overwritten by it. */
games_update:
 mov (4,sp),a0
 movhu (a0),d0
 cmp 5380,d0
 beq row_yes
 clr d0
 movbu d0,(games_row_selected)
 movbu d0,(games_paint_valid)
 mov d0,(games_screen)
 jmp original_update
row_yes:
 mov a3,(games_screen)
 mov 1,d0
 movbu d0,(games_row_selected)
 jmp original_update
/* Picture Mode's CALLS handler. Only claim keys while Games owns input. */
games_pm:
 movm [d2],(sp)
 movbu (games_state),d2
 cmp 3,d2
 bne regular_input
 cmp 0x9008,d0
 beq mario_left_on
 cmp 0x9009,d0
 beq mario_left_off
 cmp 0x900a,d0
 beq mario_right_on
 cmp 0x900b,d0
 beq mario_right_off
 cmp 0x9004,d0
 beq mario_jump_on
 cmp 0x9005,d0
 beq mario_jump_off
 cmp 0x900c,d0
 beq mario_ok_on
 cmp 0x900d,d0
 beq mario_ok_off
 cmp 0x9014,d0
 beq mario_restart
 cmp 0x900e,d0
 beq mario_menu_exit
 bra regular_input
mario_left_on:
 bset 1,(mario_keys)
 bra consumed
mario_left_off:
 bclr 1,(mario_keys)
 bra consumed
mario_right_on:
 bset 2,(mario_keys)
 bra consumed
mario_right_off:
 bclr 2,(mario_keys)
 bra consumed
mario_jump_on:
 movbu (mario_keys),d2
 and 4,d2
 bne consumed
 bset 16,(mario_keys)
 bset 4,(mario_keys)
 bra consumed
mario_jump_off:
 bclr 4,(mario_keys)
 bra consumed
mario_ok_on:
 movbu (mario_keys),d2
 and 8,d2
 bne consumed
 bset 16,(mario_keys)
 bset 8,(mario_keys)
 bra consumed
mario_ok_off:
 bclr 8,(mario_keys)
 bra consumed
mario_restart:
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 add -32,sp
 call mario_reset,[],4
 call mario_paint,[],4
 call mario_start,[],4
 mov 1,d0
 bra request_paint
mario_menu_exit:
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 add -20,sp
 mov d0,(4,sp)
 mov d1,(8,sp)
 mov a0,(12,sp)
 mov a1,(16,sp)
 call mario_stop,[],4
 mov (4,sp),d0
 mov (8,sp),d1
 mov (12,sp),a0
 mov (16,sp),a1
 add 20,sp
 movm (sp),[d2,d3,a2,a3]
 movm (sp),[other]
 bra key_menu
regular_input:
 cmp 0x900c,d0
 beq key_ok
 cmp 0x9004,d0
 beq key_up
 cmp 0x9006,d0
 beq key_down
 cmp 0x9008,d0
 beq key_left
 cmp 0x900a,d0
 beq key_right
 cmp 0x9009,d0
 beq key_release
 cmp 0x900b,d0
 beq key_release
 cmp 0x903e,d0
 beq key_restart
 cmp 0x9014,d0
 beq key_restart
 cmp 0x9015,d0
 beq key_release
 cmp 0x900e,d0
 beq key_menu
 cmp 0x900f,d0
 beq menu_release
 cmp 0x9032,d0
 beq main_dial
 cmp 0x9031,d0
 beq sub_dial
 cmp 0x9005,d0
 beq key_release
 cmp 0x9007,d0
 beq key_release
 cmp 0x900d,d0
 beq key_release
 cmp 0x972b,d0                    /* Picture Mode inactivity timeout */
 beq key_timeout
 cmp 0x9601,d0                    /* display output changes: screen is rebuilt */
 beq display_change
 bra pm_stock
display_change:
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 add -20,sp
 mov d0,(4,sp)
 mov d1,(8,sp)
 mov a0,(12,sp)
 mov a1,(16,sp)
 call mario_stop,[],4
 mov (4,sp),d0
 mov (8,sp),d1
 mov (12,sp),a0
 mov (16,sp),a1
 add 20,sp
 movm (sp),[d2,d3,a2,a3]
 movm (sp),[other]
 clr d2
 movbu d2,(games_state)
 movbu d2,(games_row_selected)
 movbu d2,(games_paint_valid)
 movbu d2,(games_ok_held)
 movbu d2,(games_menu_held)
 movbu d2,(games_game_ready)
 mov d2,(games_dial_pending)
 mov d2,(games_screen)
 bra pm_stock
key_ok:
 movbu (games_state),d2
 cmp 0,d2
 bne menu_ok
 movbu (games_row_selected),d2
 cmp 0,d2
 beq pm_stock
 mov 1,d0
 bra ok_dispatch
menu_ok:
 cmp 2,d2
 beq consumed
 mov 4,d0
ok_dispatch:
 mov 1,d2
 movbu d2,(games_ok_held)
 bra dispatch
key_up:
 movbu (games_state),d2
 cmp 0,d2
 beq pm_stock
 cmp 2,d2
 beq move_up
 mov 2,d0
 bra dispatch
key_down:
 movbu (games_state),d2
 cmp 3,d2
 beq consumed
 movbu (games_state),d2
 cmp 0,d2
 beq pm_stock
 cmp 2,d2
 beq move_down
 mov 3,d0
 bra dispatch
key_left:
 movbu (games_state),d2
 cmp 0,d2
 beq suppress_on_row
 cmp 1,d2
 beq launcher_previous
 mov 2,d0
 bra game_move
key_right:
 movbu (games_state),d2
 cmp 0,d2
 beq suppress_on_row
 cmp 1,d2
 beq launcher_next
 mov 3,d0
 bra game_move
launcher_previous:
 mov 2,d0
 bra dispatch
launcher_next:
 mov 3,d0
 bra dispatch
main_dial:
 movbu (games_state),d2
 cmp 3,d2
 beq consumed
 movbu (games_state),d2
 cmp 0,d2
 beq suppress_on_row
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 add -32,sp
 clr d3
 bra dial_fetch
sub_dial:
 movbu (games_state),d2
 cmp 3,d2
 beq consumed
 movbu (games_state),d2
 cmp 0,d2
 beq suppress_on_row
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 add -32,sp
 mov 1,d3
dial_fetch:
 mov (games_dial_pending),d0
 clr d1
 mov d1,(games_dial_pending)
 exth d0
 cmp 0,d0
 beq no_repaint
 mov d0,d2
 movbu (games_state),d0
 cmp 1,d0
 beq dial_menu
 cmp 0,d3
 bne dial_horizontal
 clr d0
 cmp 0,d2
 blt dial_move
 mov 1,d0
 bra dial_move
dial_horizontal:
 mov 2,d0
 cmp 0,d2
 blt dial_move
 mov 3,d0
dial_move:
 call play_move,[],4
 bra request_paint
dial_menu:
 mov 2,d0
 cmp 0,d2
 blt dial_menu_event
 mov 3,d0
dial_menu_event:
 call games_event,[],4
 bra request_paint
key_menu:
 movbu (games_state),d2
 cmp 0,d2
 beq pm_stock
 mov 1,d2
 movbu d2,(games_menu_held)
 mov 5,d0
 bra dispatch
menu_release:
 movbu (games_menu_held),d2
 cmp 0,d2
 beq pm_stock
 clr d2
 movbu d2,(games_menu_held)
 bra consumed
move_up:
 clr d0
 bra game_move
move_down:
 mov 1,d0
game_move:
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 add -32,sp
 call play_move,[],4
 bra request_paint
key_restart:
 movbu (games_state),d2
 cmp 0,d2
 beq suppress_on_row
 cmp 2,d2
 bne consumed
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 add -32,sp
 call new_round,[],4
 call paint,[],4
 mov 1,d0
 bra request_paint
key_release:
 cmp 0x900d,d0
 bne release_other
 movbu (games_ok_held),d2
 cmp 0,d2
 beq release_other
 clr d2
 movbu d2,(games_ok_held)
 bra consumed
release_other:
 movbu (games_state),d2
 cmp 0,d2
 beq pm_stock
 bra consumed
key_timeout:
 movbu (games_state),d2
 cmp 0,d2
 beq pm_stock
 bra consumed
dispatch:
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 add -32,sp
 call games_event,[],4
 cmp 3,d0
 bne check_start
 clr d1
 movbu d1,(games_game_ready)
 mov d1,(games_dial_pending)
check_start:
 cmp 2,d0
 bne request_paint
 movbu (games_state),d0
 cmp 3,d0
 beq start_mario
 movbu (games_game_ready),d1
 cmp 0,d1
 bne game_resumed
 call new_round,[],4
 call paint,[],4
 mov 1,d0
 movbu d0,(games_game_ready)
start_mario:
 movbu (games_state),d0
 cmp 3,d0
 bne game_resumed
 call mario_reset,[],4
 call mario_paint,[],4
 call mario_start,[],4
game_resumed:
 mov 1,d0
request_paint:
 cmp 0,d0
 beq no_repaint
 movbu (games_paint_valid),d0
 cmp 0,d0
 beq no_repaint
 /* The paint message identifies the live GUI root at +8. Mark every
  * layer dirty before posting; a bare paint message has no dirty area. */
 mov (games_paint_msg+8),a0
 clr d0
 mov 2,d1
 mov 0,a1
 mov invalidate,a2
 calls (a2)
no_repaint:
 add 32,sp
 movm (sp),[d2,d3,a2,a3]
 movm (sp),[other]
consumed:
 movm (sp),[d2]
 clr d0
 mov 8,d1
 rets
pm_stock:
 movm (sp),[d2]
 jmp original_pm
suppress_on_row:
 movbu (games_row_selected),d2
 cmp 0,d2
 bne consumed
 bra pm_stock
/* Any real screen transition ends this experimental Games session. */
games_transition:
 cmp 0,d0
 beq transition_stock
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 add -20,sp
 mov d0,(4,sp)
 mov d1,(8,sp)
 mov a0,(12,sp)
 mov a1,(16,sp)
 call mario_stop,[],4
 mov (4,sp),d0
 mov (8,sp),d1
 mov (12,sp),a0
 mov (16,sp),a1
 add 20,sp
 movm (sp),[d2,d3,a2,a3]
 movm (sp),[other]
 cmp 0,d0
 beq transition_stock
 clr d1
 movbu d1,(games_state)
 movbu d1,(games_row_selected)
 movbu d1,(games_ok_held)
 movbu d1,(games_menu_held)
 movbu d1,(games_game_ready)
 movbu d1,(games_paint_valid)
 mov d1,(games_screen)
transition_stock:
 jmp original_transition
/* Retain the most recent native paint message only while the Games row is live. */
games_queue_hook:
 mov sp,a0
 movm [d2,d3,a2,a3],(sp)
 add -4,sp
 mov a1,(sp)
 mov a0,a2
 mov d0,d2
 mov (28,a2),d0
 cmp 0x1002,d0
 bne queue_done
 movbu (games_row_selected),d0
 cmp 0,d0
 beq queue_done
 /* Only retain the live GUI root whose invalidate method and target match. */
 mov (36,a2),a0
 cmp 0,a0
 beq queue_done
 mov (a0),a1
 mov (296,a1),a1
 mov invalidate,d0
 cmp d0,a1
 bne queue_done
 mov (72,a0),d0
 mov (40,a2),a1
 cmp d0,a1
 bne queue_done
 add 28,a2
 mov games_paint_msg,a3
 mov 7,d3
save_message:
 mov (a2),d0
 mov d0,(a3)
 inc4 a2
 inc4 a3
 add -1,d3
 bne save_message
 mov 1,d0
 movbu d0,(games_paint_valid)
queue_done:
 mov d2,d0
 mov (sp),a1
 add 4,sp
 movm (sp),[d2,d3,a2,a3]
 mov sp,a0
 movhu d0,(4,sp)
 add 28,a0
 jmp queue_resume
/* The camera reads and clears dial counters before dispatching the event.
 * Save the nonzero result for the subsequent Picture Mode handler. */
games_dial_hook:
 movbu (games_state),d0
 cmp 0,d0
 beq dial_original_return
 cmp 0,d2
 beq dial_original_return
 mov d2,(games_dial_pending)
dial_original_return:
 mov d2,d0
 exth d0
 ret [d2,d3,a2,a3],36
/* Add an immutable launcher bitmap before the camera submits its paint. */
games_render_hook:
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 add -32,sp
 mov (games_render_seen),d0
 inc d0
 mov d0,(games_render_seen)
 movbu (games_state),d0
 movbu d0,(games_render_state)
 movbu (games_row_selected),d1
 cmp 0,d1
 beq render_done
 cmp 1,d0
 beq render_menu
 cmp 3,d0
 beq render_mario
 cmp 2,d0
 bne render_done
 mov board_buffer+0x40000000,a2
 bra render_ready
render_mario:
 mov mario_buffer+0x40000000,a2
 bra render_ready
render_menu:
 mov (games_draw_count),d0
 inc d0
 mov d0,(games_draw_count)
 mov launcher0+0x40000000,a2
 movbu (games_selection),d0
 cmp 0,d0
 beq render_first
 mov launcher1+0x40000000,a2
 cmp 1,d0
 beq render_first
 mov launcher2+0x40000000,a2
render_first:
render_ready:
 clr d0
 mov d0,(4,sp)
 mov d0,(8,sp)
 mov d0,(12,sp)
 mov d0,(16,sp)
 mov 1,d0
 mov d0,(20,sp)
 mov 258,d0
 mov 60,d1
 mov 0x62b77c74,a0
 mov a2,a1
 call bitmap,[d2,d3,a2,a3],96
 clr d0
 mov d0,(4,sp)
 mov d0,(8,sp)
 mov d0,(12,sp)
 mov d0,(16,sp)
 mov 1,d0
 mov d0,(20,sp)
 mov 258,d0
 mov 60,d1
 mov 0x62b77c84,a0
 mov a2,a1
 call bitmap,[d2,d3,a2,a3],96
render_done:
 add 32,sp
 movm (sp),[d2,d3,a2,a3]
 movm (sp),[other]
 call original_end,[],4
 jmp paint_resume
.balign 4
games_row_selected: .byte 0
games_ok_held: .byte 0
games_menu_held: .byte 0
games_game_ready: .byte 0
games_paint_valid: .byte 0
.balign 4
games_screen: .long 0
games_draw_count: .long 0
games_dial_pending: .long 0
games_render_seen: .long 0
games_render_state: .byte 0
.balign 4
games_paint_msg: .space 28,0
.balign 2
title: .short 71,97,109,101,115,0
go_title: .short 71,79,0
.balign 4
launcher0: .incbin "launcher0.bin"
.balign 4
launcher1: .incbin "launcher1.bin"

.balign 4
launcher2: .incbin "launcher2.bin"
