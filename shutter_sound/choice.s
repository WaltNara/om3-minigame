/* E147 shutter speaker playback. Capture posts to UI_OUT, which owns
 * the player and runs native completion on its own task. */
.am33_2
.text
.global es_dispatch, es_wave
.extern sound_choice
.global es_copy_done, es_prepare_player, es_rewind_copy
.extern audio_set_irq, set_flag_irq, ui_end, stock_prepare_player, copy_resume
.set COPY_DONE_FLAG, 8
.extern ui_flag, ui_wait, ui_stock_exec, ui_request
.extern ui_resource_size, ui_size_resume, ui_wave_resume
.extern wave_5d, wave_5d_bytes, wave_d850, wave_d850_bytes

.set UI_BUSY, 0xa32da3a8
.set UI_OTHER_BUSY, 0xa32da40c
.set AUD_PLAY_COUNT, 0x62b43dac
.set WAV_POINTER, 0xa32da344
.set WAV_BYTES, 0xa32da348
.set EXPOSURE_FLAG, 16

.extern get_drive

.extern sd_buffer, sd_length, sd_loading, sd_lease


/* Stock natural completion and lamp requests run before this dispatch.
 * Give the native synchronous queue priority over capture playback. */
es_dispatch:
 /* The copy path signals TX done even if it skips the WAV end callback.
  * Close our player on UI_OUT after the native TX-done flag is set. */
 btst COPY_DONE_FLAG,d2
 beq check_native_queue
 movbu (copy_active),d0
 cmp 0,d0
 beq check_native_queue
 clr d0
 movbu d0,(copy_active)
 movbu (UI_BUSY),d0
 cmp 1,d0
 bne check_native_queue
 mov 2,d0
 movbu d0,(UI_BUSY)
 call ui_end,[],72
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
 jmp ui_wait
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

/* Last call in the TX done interrupt callback. Preserve its native signal. */
es_copy_done:
 call audio_set_irq,[d2,d3,a2],32
 movbu (copy_active),d0
 cmp 0,d0
 beq done_irq
 movhu (ui_flag),d0
 exth d0
 mov COPY_DONE_FLAG,d1
 call set_flag_irq,[d2,d3,a2],28
done_irq:
 ret [],4
copy_active: .byte 0
playing_choice: .byte 0
.balign 4
copy_generation: .long 0
copy_consumed: .long 0


.balign 4
preview_pointer: .long 0
preview_bytes: .long 0
preview_request:
 .long 0,0,0,0,0              /* play, stock mode, resource ID, timing */
 .long 100,100,100,0           /* native volume record */
