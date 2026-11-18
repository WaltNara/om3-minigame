/* Optional on-camera readout. Counters are bytes in RAM and wrap at 256.
 * This observer does not publish playback requests or write to the card. */
.am33_2
.text
.global es_diag_draw, es_diag_exposure
.global diag_capture, diag_posted, diag_hls, diag_wake, diag_ask, diag_open, diag_close
.global diag_drive, diag_gate
.extern shoot_post_resume, sound_choice, copy_active, copy_closing

/* Observe CBC_SHOOTING_COMMON as a candidate trigger independently of
 * CapBuf. Replay the native register and stack setup on every return. */
es_diag_exposure:
 mov d0,(12,sp)
 mov d1,d3
 cmp 0x88,d0
 bne resume_exposure
 movbu (sound_choice),d2
 cmp 0,d2
 beq resume_exposure
 movbu (diag_hls),d2
 inc d2
 movbu d2,(diag_hls)
resume_exposure:
 mov 188,d2
 jmp shoot_post_resume

/* The normal ListMenu viewer still owns the widgets. Replace the four
 * displayed text records for the current publication only. */
es_diag_draw:
 mov a0,a2
 add 148,a2
 mov diag_rows,a3
 clr d0
 movbu (copy_active),d1
 cmp 0,d1
 beq read_owner
 or 1,d0
read_owner:
 mov (0x62b43c30),d1
 cmp 0,d1
 beq read_sequence
 or 2,d0
read_sequence:
 mov (0x62b43f80),d1
 cmp 0,d1
 beq read_closing
 or 4,d0
read_closing:
 movbu (copy_closing),d1
 cmp 0,d1
 beq snapshot_done
 or 8,d0
snapshot_done:
 movbu d0,(diag_tx)
row:
 mov (a3),a1
 cmp 0,a1
 beq drawn
 mov 5,d0
 movhu d0,(a2)
 movhu d0,(868,a2)
 movhu (6,a2),d0
 movhu d0,(874,a2)
 mov a2,a0
 add 12,a0
label_character:
 movhu (a1),d0
 movhu d0,(a0)
 add 2,a1
 add 2,a0
 cmp 0,d0
 bne label_character
 mov a2,a0
 add 880,a0
 mov a3,a1
 inc4 a1
 mov 3,d3
value:
 mov a1,d2
 mov (a1),a1
 movbu (a1),d0
 mov d2,a1
 mov d0,d2
 lsr 4,d0
 call digit,[],4
 mov d2,d0
 and 15,d0
 call digit,[],4
 inc4 a1
 add -1,d3
 beq end_value
 mov 32,d0
 movhu d0,(a0)
 add 2,a0
 bra value
end_value:
 clr d0
 movhu d0,(a0)
 add 124,a2
 add 16,a3
 bra row
drawn:
 ret [d2,d3,a2,a3],20

digit:
 cmp 10,d0
 bcs decimal
 add 7,d0
decimal:
 add 48,d0
 movhu d0,(a0)
 add 2,a0
 ret [],4

.balign 4
diag_rows:
 .long capture_label,diag_capture,diag_posted,diag_hls
 .long worker_label,diag_wake,diag_ask,diag_open
 .long close_label,diag_close,diag_drive,diag_gate
 .long state_label,0xa32da3a8,0x62b43dac,diag_tx
 .long 0
capture_label: .short 67,97,112,32,47,32,80,111,115,116,32,47,32,72,76,83,0
worker_label: .short 87,97,107,101,32,47,32,65,115,107,32,47,32,79,112,101,110,0
close_label: .short 67,108,111,115,101,32,47,32,68,114,105,118,101,32,47,32,71,97,116,101,0
state_label: .short 66,117,115,121,32,47,32,80,108,97,121,32,47,32,84,88,0
diag_capture: .byte 0
diag_posted: .byte 0
diag_hls: .byte 0
diag_wake: .byte 0
diag_ask: .byte 0
diag_open: .byte 0
diag_close: .byte 0
diag_drive: .byte 0
diag_gate: .byte 0
diag_tx: .byte 0
.balign 4
