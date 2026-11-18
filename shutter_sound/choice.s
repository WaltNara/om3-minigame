/* E147 Extras speaker trial. The GUI posts one private UI_OUT flag.
 * UI_OUT owns the player and runs native completion on its own task. */
.am33_2
.text
.global es_save_choice, es_dispatch, es_wave
.extern sound_cursor, sound_choice, show_extras, extra_consumed
.extern ui_flag, set_flag, ui_wait, ui_stock_exec, ui_request
.extern ui_resource_size, ui_size_resume, ui_wave_resume
.extern wave_5d, wave_5d_bytes, wave_d850, wave_d850_bytes

.set UI_BUSY, 0xa32da3a8
.set UI_OTHER_BUSY, 0xa32da40c
.set AUD_PLAY_COUNT, 0x62b43dac
.set WAV_POINTER, 0xa32da344
.set WAV_BYTES, 0xa32da348
.set SHUTTER_FLAG, 8
.set EXPOSURE_FLAG, 16

.ifdef SINGLE_SHOT
.global es_exposure
.extern shoot_post_resume, get_drive
.endif

.ifdef SD_CUSTOM
.extern es_load_sd, sd_buffer, sd_length, sd_loading, sd_lease, es_select_error
.endif

es_save_choice:
 movbu (sound_cursor),d2
.ifndef SD_CUSTOM
 cmp 2,d2
 bhi unavailable
.endif
 add -20,sp
 mov d0,(4,sp)
 mov d1,(8,sp)
 mov a0,(12,sp)
 mov a1,(16,sp)
.ifdef SD_CUSTOM
 cmp 3,d2
 bcs commit_choice
 mov d2,d0
 call es_load_sd,[d2,d3,a2,a3],28
 cmp 0,d0
 bne refused
commit_choice:
.endif
 movbu d2,(sound_choice)
 cmp 0,d2
 beq confirmed
 movhu (ui_flag),d0
 exth d0
 mov SHUTTER_FLAG,d1
 call set_flag,[d2,d3,a2],40
confirmed:
 mov (4,sp),d0
 mov (8,sp),d1
 mov (12,sp),a0
 mov (16,sp),a1
 add 20,sp
 jmp show_extras
.ifdef SD_CUSTOM
refused:
 mov (4,sp),d0
 mov (8,sp),d1
 mov (12,sp),a0
 mov (16,sp),a1
 add 20,sp
 jmp es_select_error
.else
unavailable:
 jmp extra_consumed
.endif

/* Stock natural completion and lamp requests run before this dispatch.
 * Give the native synchronous queue priority and drop a busy preview. */
es_dispatch:
 btst 4,d2
 bne stock_exec
.ifdef SINGLE_SHOT
 btst SHUTTER_FLAG|EXPOSURE_FLAG,d2
.else
 btst SHUTTER_FLAG,d2
.endif
 beq wait_more
 movbu (UI_BUSY),d0
 cmp 0,d0
 bne wait_more
 movbu (UI_OTHER_BUSY),d0
 cmp 0,d0
 bne wait_more
 movbu (AUD_PLAY_COUNT),d0
 cmp 0,d0
 bne wait_more
.ifdef SINGLE_SHOT
 btst SHUTTER_FLAG,d2
 bne selected
 mov 3265,d0
 call get_drive,[],4
 cmp 30,d0                      /* E147 SCP labels 30 as Silent Single. */
.ifdef BURST_SHOT
 beq selected
 cmp 32,d0                      /* E147 Silent Sequential. */
.endif
 bne wait_more
selected:
.endif
 movbu (sound_choice),d0
 cmp 1,d0
 beq preview_5d
 cmp 2,d0
.ifdef SD_CUSTOM
 bne preview_sd
.else
 bne wait_more
.endif
 mov wave_d850,a0
 mov wave_d850_bytes,d1
 bra set_preview
preview_5d:
 mov wave_5d,a0
 mov wave_5d_bytes,d1
.ifdef SD_CUSTOM
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
.endif
set_preview:
 mov a0,(preview_pointer)
 mov d1,(preview_bytes)
 mov preview_request,a0
 call ui_request,[d2,d3,a2,a3],16
.ifdef SD_CUSTOM
close_lease:
 clr d0
 movbu d0,(sd_lease)
.endif
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
 mov a2,a0
 mov 1,d1
 jmp ui_wave_resume
stock_wave:
 movhu (a3),d1
 mov 2,d0
 call ui_resource_size,[d2,d3,a2],16
 jmp ui_size_resume

.ifdef SINGLE_SHOT
/* CBC_SHOOTING_COMMON posts START_EXPOSE (0x88). Keep the stock
 * publication and do the drive gate and sound work on UI_OUT. */
es_exposure:
 mov d0,(12,sp)
 mov d1,d3
 cmp 0x88,d0
 bne expose_resume
 movbu (sound_choice),d2
 cmp 0,d2
 beq expose_resume
 add -12,sp
 mov a0,(4,sp)
 mov a1,(8,sp)
 movhu (ui_flag),d0
 exth d0
 mov EXPOSURE_FLAG,d1
 call set_flag,[d2,d3,a2],40
 mov (4,sp),a0
 mov (8,sp),a1
 add 12,sp
 mov (12,sp),d0
 mov d3,d1
expose_resume:
 mov 188,d2
 jmp shoot_post_resume
.endif

.balign 4
preview_pointer: .long 0
preview_bytes: .long 0
preview_request:
 .long 0,0,0,0,0              /* play, stock mode, resource ID, timing */
 .long 100,100,100,0           /* native volume record */
