/* E147 GUI switch branch. Owned touches latch one flap, then run the stock
 * handler's no-payload path to send its normal event-35 completion reply.
 * A local zeroed shadow event skips widget navigation without changing the
 * original event or payload. Stock outer cleanup still receives the original.
 * No drawing, retained payload pointers or custom heap allocation here. */
.am33_2
.text
.global flappy_touch_repaired,flappy_contact,flappy_drain
flappy_touch_repaired:
 add -36,sp
 mov d0,(20,sp)
 mov d1,(24,sp)
 mov a0,(28,sp)
 mov a1,(32,sp)
 movbu (games_state),d0
 cmp 6,d0
 bne ftr_outside
 movbu (games_row_selected),d0
 cmp 1,d0
 bne ftr_outside
 movbu (games_paint_valid),d0
 cmp 1,d0
 bne ftr_outside
 mov (games_screen),d0
 cmp 0,d0
 beq ftr_outside
 cmp 0,a3
 beq ftr_forward
 mov (12,a3),a0
 cmp 0,a0
 beq ftr_complete
 movbu (a0),d0
 cmp 3,d0
 beq ftr_release
 /* A short tap may end with TAP/DCLICK instead of RELEASE. All terminal
  * kinds re-arm contact; none queues a second flap for the same gesture. */
 cmp 4,d0
 beq ftr_release
 cmp 5,d0
 beq ftr_release
 cmp 1,d0
 bne ftr_complete
 movbu (flappy_contact),d0
 cmp 0,d0
 bne ftr_complete
 clr d0
 movbu d0,(flappy_drain)
 mov 1,d0
 movbu d0,(flappy_contact)
 movbu d0,(flappy_pending)
 bra ftr_complete
ftr_release:
 clr d0
 movbu d0,(flappy_contact)
 movbu d0,(flappy_drain)
 bra ftr_complete
ftr_outside:
 movbu (flappy_drain),d0
 cmp 0,d0
 beq ftr_forward
 cmp 0,a3
 beq ftr_forward
 mov (12,a3),a0
 cmp 0,a0
 beq ftr_forward
 movbu (a0),d0
 cmp 3,d0
 beq ftr_release
 cmp 4,d0
 beq ftr_release
 cmp 5,d0
 beq ftr_release
 cmp 1,d0
 bne ftr_complete
 /* Fresh outside contact ends the interrupted gesture's drain. */
 clr d0
 movbu d0,(flappy_drain)
ftr_forward:
 mov (20,sp),d0
 mov (24,sp),d1
 mov (28,sp),a0
 mov (32,sp),a1
 add 36,sp
 mov flappy_touch_original,a0
 jmp flappy_touch_original
ftr_complete:
 /* The stock handler only reads shadow+12 on this path, then builds its
  * normal [35,57,0,0,0] no-action reply. Its own 120-byte call frame and
  * epilogue are retained, including the pending-touch flag and reply sender.
  * sp+4..19 hold the shadow; sp+20..35 hold our volatile-register saves. */
 clr d0
 mov d0,(4,sp)
 mov d0,(8,sp)
 mov d0,(12,sp)
 mov d0,(16,sp)
 mov sp,a0
 add 4,a0
 call flappy_touch_dispatch,[d2,d3,a2,a3],120
 mov (20,sp),d0
 mov (24,sp),d1
 mov (28,sp),a0
 mov (32,sp),a1
 add 36,sp
 clr d2
 jmp flappy_touch_continue
.balign 4
flappy_contact: .byte 0
flappy_drain: .byte 0
