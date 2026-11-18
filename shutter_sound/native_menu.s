/* E147 ListMenu inline setting. The stock viewer and widgets own painting. */
.am33_2
.text
.global es_menu_view, es_menu_keys, es_menu_transition
.global sound_choice, sound_cursor, sound_editing
.extern native_set_variable, native_keys_resume, native_panel_id, native_gui_state
.extern games_transition, es_load_sd

.set FOURTH_LABEL, 520
.set FOURTH_VALUE, 1388
.set FOURTH_BACKGROUND, 2535

es_menu_view:
 movm [d2,d3,a2,a3],(sp)
 mov a0,a2
 movbu (6,a2),d2
 cmp 1,d2
 beq check_page
 cmp 2,d2
 bne leave_row
check_page:
 movbu (144,a2),d2
 cmp 2,d2
 bne leave_row
 movhu (FOURTH_LABEL,a2),d2
 cmp 5,d2
 bne leave_row
 clr d2
 movbu d2,(sound_focused)
 movbu (FOURTH_BACKGROUND,a2),d2
 cmp 1,d2
 bne end_edit
 movbu (FOURTH_BACKGROUND+1,a2),d2
 cmp 5,d2
 bne end_edit
 movbu (2677,a2),d2             /* stock help box owns input */
 cmp 0,d2
 bne end_edit
 mov 1,d2
 movbu d2,(sound_focused)
 bra write_value
leave_row:
 clr d2
 movbu d2,(sound_focused)
 movbu d2,(sound_editing)
 bra publish
end_edit:
 clr d2
 movbu d2,(sound_editing)
write_value:
 movhu (FOURTH_LABEL+6,a2),d3
 movbu (sound_editing),d2
 cmp 0,d2
 beq current_value
 movbu (sound_error),d2
 cmp 0,d2
 bne show_error
 movbu (sound_cursor),d2
 mov edit_labels,a3
 bra copy_label
show_error:
 add -1,d2
 mov error_labels,a3
 bra copy_label
current_value:
 movbu (sound_choice),d2
 mov choice_labels,a3
copy_label:
 asl2 d2
 mov (d2,a3),a3
 mov 5,d2
 movhu d2,(FOURTH_VALUE,a2)
 movhu d3,(FOURTH_VALUE+6,a2)
 add FOURTH_VALUE+12,a2
copy_character:
 movhu (a3),d2
 movhu d2,(a2)
 add 2,a3
 add 2,a2
 cmp 0,d2
 bne copy_character
publish:
 movm (sp),[d2,d3,a2,a3]
 jmp native_set_variable

es_menu_keys:
 movm [d2,d3,a2,a3],(sp)
 add -52,sp
 movhu (native_panel_id),d2
 cmp 329,d2
 bne stock_key
 mov (native_gui_state),d2
 cmp 0x0b02,d2
 bne stock_key
 movbu (sound_focused),d2
 cmp 0,d2
 beq stock_key
 movbu (sound_editing),d2
 cmp 0,d2
 bne edit_key
 cmp 0x900c,d0                  /* OK */
 beq enter_edit
 cmp 0x900a,d0                  /* Right */
 bne stock_key
enter_edit:
 movbu (sound_choice),d2
 movbu d2,(sound_cursor)
 clr d2
 movbu d2,(sound_error)
 inc d2
 movbu d2,(sound_editing)
 bra repaint
edit_key:
 cmp 0x900e,d0                  /* MENU */
 beq close_edit
 cmp 0x900c,d0
 beq save_choice
 cmp 0x9004,d0
 beq previous_choice
 cmp 0x9008,d0
 beq previous_choice
 cmp 0x9006,d0
 beq next_choice
 cmp 0x900a,d0
 beq next_choice
 bra stock_key
previous_choice:
 mov -1,d3
 bra move_choice
next_choice:
 mov 1,d3
move_choice:
 clr d2
 movbu d2,(sound_error)
 movbu (sound_cursor),d2
 add d3,d2
 cmp 0,d2
 bge wrap_choice
 mov 5,d2
wrap_choice:
 cmp 6,d2
 bcs store_cursor
 clr d2
store_cursor:
 movbu d2,(sound_cursor)
 bra repaint
save_choice:
 movbu (sound_cursor),d2
 cmp 3,d2
 bcs commit
 mov d1,(4,sp)
 mov a0,(8,sp)
 mov a1,(12,sp)
 mov d2,d0
 call es_load_sd,[d2,d3,a2,a3],28
 mov (4,sp),d1
 mov (8,sp),a0
 mov (12,sp),a1
 cmp 0,d0
 beq commit
 movbu d0,(sound_error)
 bra repaint
commit:
 movbu d2,(sound_choice)
close_edit:
 clr d2
 movbu d2,(sound_editing)
repaint:
 /* OK on our mode runs the stock view publication without opening a panel. */
 mov 0x900c,d0
stock_key:
 jmp native_keys_resume

es_menu_transition:
 cmp 0,d0
 beq continue_transition
 bclr 1,(sound_editing)
 bclr 1,(sound_focused)
continue_transition:
 jmp games_transition

sound_choice: .byte 0
sound_cursor: .byte 0
sound_focused: .byte 0
sound_editing: .byte 0
sound_error: .byte 0
.balign 4
.include "native_labels.inc"
