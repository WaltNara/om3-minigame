/* E147 ListMenu. The GUI task owns the launcher, game keys and rendering.
 * Core game data, the deferred timer bridge and the touch reply ABI come from r5. */
.am33_2
.text
.global menu_view, menu_keys, menu_panel, menu_transition, menu_paint, menu_touch

/* Call at the native ListMenu viewer's publication of variable 232.
 * Take only a boolean from the record. The viewer owns its memory. */
menu_view:
 movm [d2],(sp)
 movbu (games_state),d2
 cmp 0,d2
 bne view_done
 movbu (6,a0),d2
 cmp 1,d2                       /* Setup tab, normal row focus */
 bne disarm
 movbu (144,a0),d2
 cmp 2,d2
 bne disarm
 movbu (2535,a0),d2             /* fourth row's selected background */
 cmp 1,d2
 bne disarm
 movbu (2536,a0),d2
 cmp 5,d2
 bne disarm
 movbu (2677,a0),d2             /* INFO help box owns the next key */
 cmp 0,d2
 bne disarm
 /* The fourth row must be our type-5 literal, independent of language. */
 movhu (520,a0),d2
 cmp 5,d2
 bne disarm
 mov 1,d2
 movbu d2,(games_row_selected)
 bra view_done
disarm:
 clr d2
 movbu d2,(games_row_selected)
 movbu d2,(games_paint_valid)
 mov d2,(games_screen)
 mov d2,(games_paint_msg+8)
view_done:
 movm (sp),[d2]
 jmp native_set_variable

/* Only this ListMenu CALLS handler can enter Games. Non-game messages go
 * through its original prologue including the original saved registers. */
menu_keys:
 movm [d2],(sp)
 movhu (native_panel_id),d2
 cmp 329,d2
 bne native_keys
 movbu (games_state),d2
 cmp 0,d2
 bne running_keys
 cmp 0x900f,d0
 bne check_ok_release
 movbu (games_menu_held),d2
 cmp 0,d2
 bne game_key
check_ok_release:
 cmp 0x900d,d0
 bne check_open
 movbu (games_ok_held),d2
 cmp 0,d2
 bne game_key
check_open:
 cmp 0x900c,d0
 bne native_keys
 movbu (games_row_selected),d2
 cmp 1,d2
 bne native_keys
 movbu (games_paint_valid),d2
 cmp 1,d2
 bne native_keys
 mov (games_paint_msg+8),d2
 mov d2,(games_screen)
 clr d2
 movbu d2,(extras_selection)
 jmp show_extras
running_keys:
 cmp 0x9601,d0
 bne regular_key
 /* A same-panel output rebuild can invalidate the old drawing target. */
 add -20,sp
 mov d0,(4,sp)
 mov d1,(8,sp)
 mov a0,(12,sp)
 mov a1,(16,sp)
 call menu_cleanup,[],4
 mov (4,sp),d0
 mov (8,sp),d1
 mov (12,sp),a0
 mov (16,sp),a1
 add 20,sp
 jmp native_keys
regular_key:
 cmp 0x9004,d0
 blt native_keys
 cmp 0x900f,d0
 ble game_key
 cmp 0x9014,d0
 beq game_key
 cmp 0x9015,d0
 beq game_key
 cmp 0x9031,d0
 beq game_key
 cmp 0x9032,d0
 beq game_key
 cmp 0x903e,d0
 bne native_keys
game_key:
 movbu (games_state),d2
 cmp 7,d2
 bge extras_key
 cmp 1,d2
 bne shared_key
 cmp 0x900e,d0
 beq leave_launcher
 cmp 0x900c,d0
 bne shared_key
 movbu (games_selection),d2
 cmp 5,d2
 beq leave_launcher
shared_key:
 movm (sp),[d2]
 jmp games_pm
native_keys:
 movm (sp),[d2]
 movm [d2,d3,a2,a3],(sp)
 add -52,sp
 jmp native_keys_resume

/* 7 is Extras, 8 is its independent sound chooser. A selected preference
 * lasts until power-off. Silent remains effective until native audio exists. */
leave_launcher:
 clr d2
 movbu d2,(games_game_ready)
 movbu d2,(games_ok_held)
 movbu d2,(games_menu_held)
 mov d2,(games_dial_pending)
show_extras:
 mov 7,d2
 movbu d2,(games_state)
 jmp extra_redraw
extras_key:
 cmp 0x900c,d0
 beq extras_accept
 cmp 0x900e,d0
 beq extras_back
 cmp 0x9004,d0
 beq previous
 cmp 0x9008,d0
 beq previous
 cmp 0x9006,d0
 beq next
 cmp 0x900a,d0
 beq next
 cmp 0x9031,d0
 beq extras_dial
 cmp 0x9032,d0
 bne extra_consumed
extras_dial:
 mov (games_dial_pending),d0
 clr d1
 mov d1,(games_dial_pending)
 exth d0
 cmp 0,d0
 beq extra_consumed
 blt previous
next:
 mov 1,d1
 bra select_option
previous:
 mov -1,d1
select_option:
 mov extras_selection,a0
 mov 2,d0
 cmp 7,d2
 beq move_selection
 mov sound_cursor,a0
 mov 5,d0
move_selection:
 movbu (a0),d2
 add d1,d2
 cmp 0,d2
 bge wrap_high
 mov d0,d2
 add -1,d2
wrap_high:
 cmp d0,d2
 blt save_selection
 clr d2
save_selection:
 movbu d2,(a0)
 bra extra_redraw
extras_accept:
 cmp 8,d2
 beq save_sound
 movbu (extras_selection),d2
 cmp 0,d2
 bne open_sound
 /* Use the same open event as the shared launcher. */
 movbu d2,(games_state)
 jmp shared_key
open_sound:
 movbu (sound_choice),d2
 movbu d2,(sound_cursor)
 mov 8,d2
 movbu d2,(games_state)
 bra extra_redraw
save_sound:
 movbu (sound_cursor),d2
 movbu d2,(sound_choice)
 jmp show_extras
extras_back:
 cmp 8,d2
 beq show_extras
 clr d2
 movbu d2,(games_state)
 mov d2,(games_screen)
 mov 1,d2
 movbu d2,(games_menu_held)
extra_redraw:
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 add -32,sp
 mov 1,d0
 jmp request_paint
extra_consumed:
 jmp consumed

/* An in-menu panel change can happen without a GUI state transition. Drop
 * the captured paint root before stock replaces the panel. */
menu_panel:
 cmp 329,d3
 beq panel_done
 movm [d2],(sp)
 movbu (games_row_selected),d2
 cmp 0,d2
 beq panel_restore
 add -20,sp
 mov d0,(4,sp)
 mov d1,(8,sp)
 mov a0,(12,sp)
 mov a1,(16,sp)
 call menu_cleanup,[],4
 mov (4,sp),d0
 mov (8,sp),d1
 mov (12,sp),a0
 mov (16,sp),a1
 add 20,sp
panel_restore:
 movm (sp),[d2]
panel_done:
 call native_panel_prepare,[],0
 jmp native_panel_resume

menu_cleanup:
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 add -4,sp
 call mario_stop,[],4
 clr d0
 movbu d0,(games_state)
 movbu d0,(games_row_selected)
 movbu d0,(games_game_ready)
 movbu d0,(games_menu_held)
 movbu d0,(games_ok_held)
 movbu d0,(games_paint_valid)
 mov d0,(games_screen)
 mov d0,(games_paint_msg+8)
 mov d0,(games_dial_pending)
 add 4,sp
 movm (sp),[d2,d3,a2,a3]
 movm (sp),[other]
 ret [],4

menu_transition:
 cmp 0,d0
 beq transition_done
 movm [d2],(sp)
 movbu (games_row_selected),d2
 cmp 0,d2
 beq transition_restore
 /* Preserve the state machine's returned transition and volatile arguments. */
 add -20,sp
 mov d0,(4,sp)
 mov d1,(8,sp)
 mov a0,(12,sp)
 mov a1,(16,sp)
 call menu_cleanup,[],4
 mov (4,sp),d0
 mov (8,sp),d1
 mov (12,sp),a0
 mov (16,sp),a1
 add 20,sp
transition_restore:
 movm (sp),[d2]
transition_done:
 jmp original_transition

/* Fill both native drawing contexts before the shared game renderer submits
 * its centered bitmap. This is a pair of rectangle commands per redraw. */
menu_paint:
 movm [d2],(sp)
 movbu (games_state),d2
 cmp 0,d2
 bne draw_game
 movm (sp),[d2]
 call original_end,[],4
 jmp paint_resume
draw_game:
 movm (sp),[d2]
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 add -20,sp
 mov 0x62b77c74,a2
 mov 2,d3
draw_background:
 mov 600,d0
 mov d0,(4,sp)
 mov 7,d0
 mov d0,(8,sp)
 mov 1,d0
 mov d0,(12,sp)
 clr d0
 clr d1
 mov a2,a0
 mov 900,a1
 call native_rectangle,[d2,d3,a2,a3],92
 add 16,a2
 add -1,d3
 bne draw_background
 movbu (games_state),d0
 cmp 7,d0
 blt shared_paint
 mov extras_items,a3
 cmp 7,d0
 beq draw_label
 mov sound_items,a3
draw_label:
 mov (8,a3),a2
 cmp 0,a2
 beq draw_cursor
 mov (a3),d0
 mov (4,a3),d1
 call draw_text_bitmap,[],4
 add 12,a3
 bra draw_label
draw_cursor:
 movbu (games_state),d0
 cmp 7,d0
 bne sound_arrow
 movbu (extras_selection),d0
 mov 80,d1
 mul d0,d1
 add 205,d1
 bra paint_arrow
sound_arrow:
 movbu (sound_cursor),d0
 mov 58,d1
 mul d0,d1
 add 140,d1
paint_arrow:
 mov 254,d0
 mov extras_arrow+0x40000000,a2
 call draw_text_bitmap,[],4
 add 20,sp
 movm (sp),[d2,d3,a2,a3]
 movm (sp),[other]
 call original_end,[],4
 jmp paint_resume
shared_paint:
 add 20,sp
 movm (sp),[d2,d3,a2,a3]
 movm (sp),[other]
 jmp games_render_hook

draw_text_bitmap:
 movm [d2,d3,a2,a3],(sp)
 add -24,sp
 mov d0,d2
 mov d1,d3
 mov 0x62b77c74,a3
text_layer:
 clr d0
 mov d0,(4,sp)
 mov d0,(8,sp)
 mov d0,(12,sp)
 mov d0,(16,sp)
 mov 1,d0
 mov d0,(20,sp)
 mov d2,d0
 mov d3,d1
 mov a3,a0
 mov a2,a1
 call bitmap,[d2,d3,a2,a3],96
 add 16,a3
 mov 0x62b77c94,d0
 cmp d0,a3
 bne text_layer
 add 24,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4

/* Keep the stock synchronous completion on every gesture. While a button-only
 * game or the launcher is visible, touches must not reach the Setup widgets. */
menu_touch:
 movm [d2],(sp)
 movbu (games_state),d2
 cmp 0,d2
 beq standard_touch
 movhu (native_panel_id),d2
 cmp 329,d2
 bne outside_touch
 mov (native_gui_state),d2
 cmp 0x0b02,d2
 bne outside_touch
 movbu (games_row_selected),d2
 cmp 1,d2
 bne outside_touch
 movbu (games_paint_valid),d2
 cmp 1,d2
 bne outside_touch
 mov (games_screen),d2
 cmp 0,d2
 beq outside_touch
 movbu (games_state),d2
 cmp 6,d2
 beq standard_touch
 cmp 0,a3
 beq standard_touch
 movm (sp),[d2]
 add -36,sp
 mov d0,(20,sp)
 mov d1,(24,sp)
 mov a0,(28,sp)
 mov a1,(32,sp)
 mov (12,a3),a0
 cmp 0,a0
 beq finish_touch
 movbu (a0),d0
 cmp 3,d0
 beq end_touch
 cmp 4,d0
 beq end_touch
 cmp 5,d0
 beq end_touch
 cmp 1,d0
 bne finish_touch
 movbu d0,(flappy_drain)
finish_touch:
 jmp ftr_complete
end_touch:
 jmp ftr_release
outside_touch:
 movm (sp),[d2]
 add -36,sp
 mov d0,(20,sp)
 mov d1,(24,sp)
 mov a0,(28,sp)
 mov a1,(32,sp)
 jmp ftr_outside
standard_touch:
 movm (sp),[d2]
 jmp flappy_touch_repaired

.global extras_selection, sound_choice, sound_cursor
extras_selection: .byte 0
sound_choice: .byte 0
sound_cursor: .byte 0
.include "extras.inc"
