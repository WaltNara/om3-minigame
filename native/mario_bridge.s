/* Timer -> deferred task -> GUI queue. Only GUI owns game/render state.
 * Each session has a generation; delayed messages are consumed and ignored. */
.am33_2
.text
.global mario_start,mario_stop,mario_keys,mario_epoch,mario_ticks,mario_handle,mario_gui_hook
mario_start:
 movm [d2,d3,a2,a3],(sp)
 add -4,sp
 call mario_stop,[],4
 mov (mario_epoch),d0
 inc d0
 mov d0,(mario_epoch)
 mov d0,a1
 mov mario_tick_isr,a0
 mov 130,d0
 mov 120,d1
 call timer_create,[d2],8
 movhu d0,(mario_handle)
 add 4,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4
mario_stop:
 movm [d2,d3,a2,a3],(sp)
 add -4,sp
 clr d0
 movbu d0,(mario_keys)
 movhu (mario_handle),d1
 cmp 0,d1
 beq stop_done
 movhu d0,(mario_handle)
 mov (mario_epoch),d0
 inc d0
 mov d0,(mario_epoch)
 mov 2,d0
 call timer_delete,[d2],8
stop_done:
 add 4,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4
/* CALLS entry: a0 is the immutable generation, never a GUI pointer. */
mario_tick_isr:
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 add -4,sp
 mov a0,a1
 mov mario_post_tick,a0
 call defer_call,[d2,d3,a2,a3],40
 add 4,sp
 movm (sp),[d2,d3,a2,a3]
 movm (sp),[other]
 rets
mario_post_tick:
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 add -32,sp
 mov a0,d0
 mov (mario_epoch),d1
 cmp d1,d0
 bne post_done
 mov d0,(12,sp)
 mov 0x7ffe,d0
 mov d0,(4,sp)
 mov -2,d0
 mov d0,(8,sp)
 clr d0
 mov d0,(16,sp)
 mov d0,(20,sp)
 mov d0,(24,sp)
 mov d0,(28,sp)
 mov 1,d0
 call queue_entry,[d2,d3,a2,a3],24
post_done:
 add 32,sp
 movm (sp),[d2,d3,a2,a3]
 movm (sp),[other]
 rets
/* Replaces native trace call at the GUI message receive boundary. */
mario_gui_hook:
 cmp 0x7ffe,d0
 beq gui_tick
 call gui_trace,[],4
 jmp gui_resume
gui_tick:
 mov (404,sp),d0
 mov (mario_epoch),d1
 cmp d1,d0
 bne gui_skip
 movbu (games_state),d0
 cmp MARIO_GAME_STATE,d0
 bne gui_skip
 movbu (games_paint_valid),d0
 cmp 0,d0
 beq gui_skip
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 add -32,sp
 mov (mario_ticks),d0
 inc d0
 mov d0,(mario_ticks)
 movbu (mario_keys),d0
 bclr 16,(mario_keys)
 call mario_step,[],4
 call mario_paint,[],4
 mov (games_paint_msg+8),a0
 clr d0
 mov 2,d1
 mov 0,a1
 mov invalidate,a2
 calls (a2)
 mov (mario_state+16),d0
 cmp 0,d0
 beq tick_running
 call mario_stop,[],4
tick_running:
 add 32,sp
 movm (sp),[d2,d3,a2,a3]
 movm (sp),[other]
gui_skip:
 jmp gui_next
.balign 4
mario_epoch: .long 0
mario_ticks: .long 0
mario_handle: .short 0
mario_keys: .byte 0
