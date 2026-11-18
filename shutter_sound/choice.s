/* E147 shutter speaker playback. Capture posts to UI_OUT, which owns
 * the player and runs native completion on its own task. */
.am33_2
.text
.global es_dispatch, es_wave, es_wait, es_stock_complete, es_end_wait
.extern sound_choice
.global es_prepare_player, es_rewind_copy
.extern ui_end, stock_prepare_player, copy_resume, audio_wait, audio_end_resume
.extern ui_flag, ui_wait_resume, ui_complete_resume, ui_stock_exec, ui_request
.extern ui_resource_size, ui_size_resume, ui_wave_resume
.extern wave_5d, wave_5d_bytes, wave_d850, wave_d850_bytes

.set UI_BUSY, 0xa32da3a8
.set UI_OTHER_BUSY, 0xa32da40c
.set AUD_PLAY_COUNT, 0x62b43dac
.set TX_OWNER, 0x62b43c30
.set TX_SEQUENCE, 0x62b43f80
.set UI_PLAYER, 0xa32da414
.set WAV_POINTER, 0xa32da344
.set WAV_BYTES, 0xa32da348
.set EXPOSURE_FLAG, 16

.extern get_drive

.extern sd_buffer, sd_length, sd_loading, sd_lease


/* No flag from the audio interrupt is required to wake UI_OUT. Only the
 * custom playback interval uses a timed wait. Clear the event output first
 * because a timeout leaves the previous event word in place. */
es_wait:
 clr d0
 mov d0,(36,sp)
 movbu (copy_active),d0
 cmp 0,d0
 beq wait_forever
 mov 32,d0
 bra wait_native
wait_forever:
 mov -1,d0
wait_native:
 mov d0,(4,sp)
 movhu (ui_flag),d0
 jmp ui_wait_resume

/* The WAV's end callback can run before the TX interrupt releases its
 * object. For our clip, defer the stock UI close until that release. */
es_stock_complete:
 movbu (copy_active),d0
 cmp 0,d0
 beq stock_complete
 mov (UI_PLAYER),d0
 mov (copy_player),d1
 cmp d0,d1
 beq stock_complete_resume
stock_complete:
 call ui_end,[],72
stock_complete_resume:
 jmp ui_complete_resume

/* The stock ISR clears TX_OWNER and its callback clears TX_SEQUENCE.
 * These two native ownership records outlive the flag wakeup. */
es_dispatch:
 movbu (copy_active),d0
 cmp 0,d0
 beq check_native_queue
 mov (UI_PLAYER),d0
 mov (copy_player),d1
 cmp d0,d1
 bne released_copy
 mov (TX_OWNER),d0
 cmp 0,d0
 bne check_native_queue
 mov (TX_SEQUENCE),d0
 cmp 0,d0
 bne check_native_queue
 movbu (UI_BUSY),d0
 cmp 0,d0
 beq released_copy
 mov 1,d0
 movbu d0,(copy_closing)
 mov 2,d0
 movbu d0,(UI_BUSY)
 call ui_end,[],72
released_copy:
 clr d0
 movbu d0,(copy_closing)
 movbu d0,(copy_active)
 /* If the final period was already queued, replay the newest request now. */
 mov (copy_generation),d0
 mov (copy_consumed),d1
 cmp d1,d0
 beq check_native_queue
 or EXPOSURE_FLAG,d2
check_native_queue:
 btst 4,d2
 bne stock_exec
 btst EXPOSURE_FLAG,d2
 beq wait_more
 mov 3265,d0
 call get_drive,[],4
 cmp 30,d0
 beq check_player
 cmp 32,d0
 bne wait_more
check_player:
 movbu (copy_active),d0
 cmp 0,d0
 beq check_busy
 movbu (sound_choice),d0
 movbu (playing_choice),d1
 cmp d1,d0
 bne wait_more
 mov (copy_generation),d0
 inc d0
 mov d0,(copy_generation)
 bra wait_more
check_busy:
 movbu (UI_BUSY),d0
 cmp 0,d0
 bne wait_more
 movbu (UI_OTHER_BUSY),d0
 cmp 0,d0
 bne wait_more
 movbu (AUD_PLAY_COUNT),d0
 cmp 0,d0
 bne wait_more
 movbu (sound_choice),d0
 cmp 1,d0
 beq preview_5d
 cmp 2,d0
 bne preview_sd
 mov wave_d850,a0
 mov wave_d850_bytes,d1
 bra set_preview
preview_5d:
 mov wave_5d,a0
 mov wave_5d_bytes,d1
 bra set_preview
preview_sd:
 cmp 3,d0
 bcs wait_more
 cmp 5,d0
 bhi wait_more
 mov 1,d0
 movbu d0,(sd_lease)
 movbu (sd_loading),d0
 cmp 0,d0
 bne close_lease
 mov (sd_length),d1
 cmp 0,d1
 beq close_lease
 mov sd_buffer,a0
set_preview:
 mov a0,(preview_pointer)
 mov d1,(preview_bytes)
 movbu (sound_choice),d0
 movbu d0,(playing_choice)
 clr d0
 mov d0,(copy_generation)
 mov d0,(copy_consumed)
 mov preview_request,a0
 call ui_request,[d2,d3,a2,a3],16
close_lease:
 clr d0
 movbu d0,(sd_lease)
wait_more:
 jmp es_wait
stock_exec:
 and 4,d2
 jmp ui_stock_exec

/* UI_OUT has opened the stock short-sound player. Use an embedded WAV
 * only for the request with our private record address. Stock requests
 * keep the original type-2 lookup and its call-frame layout. */
es_wave:
 mov preview_request+4,a0
 cmp a3,a0
 bne stock_wave
 mov (preview_pointer),d0
 mov d0,(WAV_POINTER)
 mov (preview_bytes),d0
 mov d0,(WAV_BYTES)
 mov (UI_PLAYER),d0
 mov d0,(copy_player)
 mov 1,d0
 movbu d0,(copy_active)
 mov a2,a0
 mov 1,d1
 jmp ui_wave_resume
stock_wave:
 movhu (a3),d1
 mov 2,d0
 call ui_resource_size,[d2,d3,a2],16
 jmp ui_size_resume

/* The UI sound path prepares a short clip. The native copy player already
 * has its format and volume from the ordinary open/volume commands. */
es_prepare_player:
 mov preview_request+4,a0
 cmp a3,a0
 beq skip_short_setup
 jmp stock_prepare_player
skip_short_setup:
 ret [d2,d3,a2],60

/* AUD_COPY_DATA owns the native PCM cursor and remaining byte count. Rewind
 * only the validated range of our active clip before filling its next period. */
es_rewind_copy:
 movbu (copy_active),d2
 cmp 0,d2
 beq native_copy
 mov (copy_generation),d2
 mov (copy_consumed),d3
 cmp d2,d3
 beq native_copy
 mov (a0),a2
 mov (4,a2),a2
 mov (48,a2),a3
 mov (preview_pointer),d3
 add 112,d3
 mov a3,d1
 cmp d3,d1
 bcs native_copy
 mov (52,a2),d1
 cmp 0,d1
 beq native_copy
 mov (preview_bytes),d1
 add -112,d1
 add d3,d1
 mov a3,a1
 mov d1,a3
 cmp a3,a1
 bcc native_copy
 mov d3,(48,a2)
 sub d3,d1
 mov d1,(52,a2)
 mov d2,(copy_consumed)
native_copy:
 mov a0,(12,sp)
 mov d0,(28,sp)
 clr d3
 jmp copy_resume

/* AUD_MAIN handles command 0x49. UI_OUT only arms this one close after
 * the transmitter has been released. Keep the copy-data teardown and
 * player close, even if the TX notification has already been consumed. */
es_end_wait:
 mov d0,(8,sp)
 movbu (copy_closing),d0
 cmp 0,d0
 beq wait_stock_end
 mov (copy_player),d0
 cmp d0,d2
 bne wait_stock_end
 mov (TX_OWNER),d0
 cmp 0,d0
 bne wait_stock_end
 mov (TX_SEQUENCE),d0
 cmp 0,d0
 beq end_wait_resume
wait_stock_end:
 mov (8,sp),d0
 call audio_wait,[d2,d3,a2,a3],56
end_wait_resume:
 jmp audio_end_resume

copy_active: .byte 0
copy_closing: .byte 0
playing_choice: .byte 0
.balign 4
copy_generation: .long 0
copy_consumed: .long 0
copy_player: .long 0


.balign 4
preview_pointer: .long 0
preview_bytes: .long 0
preview_request:
 .long 0,0,0,0,0              /* play, stock mode, resource ID, timing */
 .long 100,100,100,0           /* native volume record */
