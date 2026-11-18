/* E147 per-frame CapBuf call sites. Reissue each displaced CALL with its
 * original saved registers and frame size. */
.am33_2
.text
.global es_capture_main, es_capture_fast
.extern capbuf_append, capbuf_taken_picture, sound_choice, ui_flag, set_flag
.extern capbuf_main_resume, capbuf_fast_resume

es_capture_main:
 call notify_frame,[],4
 call capbuf_append,[d2,d3,a2,a3],28
 jmp capbuf_main_resume

es_capture_fast:
 call notify_frame,[],4
 call capbuf_taken_picture,[a2],20
 jmp capbuf_fast_resume

notify_frame:
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 movbu (sound_choice),d2
 cmp 0,d2
 beq done
 add -20,sp
 mov d0,(4,sp)
 mov d1,(8,sp)
 mov a0,(12,sp)
 mov a1,(16,sp)
 movhu (ui_flag),d0
 exth d0
 mov 16,d1
 call set_flag,[d2,d3,a2],40
 mov (4,sp),d0
 mov (8,sp),d1
 mov (12,sp),a0
 mov (16,sp),a1
 add 20,sp
done:
 movm (sp),[d2,d3,a2,a3]
 movm (sp),[other]
 ret [],4
