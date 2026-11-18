/* E147 SD presets. The menu loads one immutable WAV before publishing the
 * selection. The audio task leases the buffer through player startup. */
.am33_2
.text
.global es_load_sd, sd_length, sd_loading, sd_lease
.extern sound_choice
.ifndef NATIVE_MENU
.global es_select_error, es_open_sound
.extern extra_redraw, open_sound_resume
.endif
.extern fopen, fread, fclose, sd_buffer, wav_limit

.set UI_BUSY, 0xa32da3a8
.set UI_OTHER_BUSY, 0xa32da40c
.set AUD_PLAY_COUNT, 0x62b43dac

/* d0 is the slot ID. Menu calls with [d2,d3,a2,a3],28. */
es_load_sd:
 mov d0,d3
 cmp 5,d0
 bhi missing
 mov 1,d2
 movbu d2,(sd_loading)
 movbu (sd_lease),d2
 cmp 0,d2
 bne busy
 movbu (UI_BUSY),d2
 cmp 0,d2
 bne busy
 movbu (UI_OTHER_BUSY),d2
 cmp 0,d2
 bne busy
 movbu (AUD_PLAY_COUNT),d2
 cmp 0,d2
 bne busy
 add -3,d0
 asl2 d0
 mov sd_paths,a0
 mov (d0,a0),a0
 mov sd_read,a1
 call fopen,[],4
 cmp 0,a0
 beq missing

 /* A read replaces the prior SD clip. Withdraw its selection first. */
 mov a0,(4,sp)
 movbu (sound_choice),d2
 cmp 3,d2
 bcs load_wav
 clr d2
 movbu d2,(sound_choice)
load_wav:
 clr d2
 mov d2,(sd_length)
 mov sd_buffer,a2
 mov a2,a0
 mov 1,d0
 mov wav_limit+1,d1
 mov (4,sp),a1
 call fread,[d2,d3,a2,a3],24
 mov d0,d3
 mov (4,sp),a0
 call fclose,[d2,a2,a3],16
 cmp 0,d0
 bne bad_wav
 cmp 116,d3
 bcs bad_wav
 cmp wav_limit,d3
 bhi bad_wav
 btst 3,d3
 bne bad_wav
 mov (4,a2),d0
 add 8,d0
 cmp d3,d0
 bne bad_wav
 mov (108,a2),d0
 add 112,d0
 cmp d3,d0
 bne bad_wav

 mov sd_wav_header,a3
 clr d1
check_header:
 cmp 4,d1
 beq next_word
 cmp 108,d1
 beq next_word
 mov (d1,a2),d0
 mov (d1,a3),d2
 cmp d0,d2
 bne bad_wav
next_word:
 add 4,d1
 cmp 112,d1
 bcs check_header
.ifdef NATIVE_MENU
 /* The file format stays compatible. The native copy player uses SHUT1. */
 mov copy_key,a3
 mov 20,d1
 add wav_key_offset,a2
copy_key_word:
 mov (a3),d0
 mov d0,(a2)
 inc4 a3
 inc4 a2
 add -4,d1
 bne copy_key_word
.endif
 mov d3,(sd_length)
 clr d0
 movbu d0,(sd_loading)
 ret [d2,d3,a2,a3],28

missing:
 /* A removed file cannot remain selected by pressing OK again. */
 movbu (sound_choice),d0
 cmp d3,d0
 bne missing_notice
 clr d0
 movbu d0,(sound_choice)
missing_notice:
.ifdef NATIVE_MENU
 mov 1,d1
.else
 mov sd_msg_missing+0x40000000,d1
.endif
 bra reject
bad_wav:
.ifdef NATIVE_MENU
 mov 2,d1
.else
 mov sd_msg_bad+0x40000000,d1
.endif
 bra reject
busy:
.ifdef NATIVE_MENU
 mov 3,d1
.else
 mov sd_msg_busy+0x40000000,d1
.endif
reject:
.ifndef NATIVE_MENU
 mov d1,(sd_notice)
.endif
 clr d0
 movbu d0,(sd_loading)
.ifdef NATIVE_MENU
 mov d1,d0
.else
 mov 1,d0
.endif
 ret [d2,d3,a2,a3],28

.ifndef NATIVE_MENU
es_open_sound:
 mov sd_msg_ready+0x40000000,d2
 mov d2,(sd_notice)
 movbu (sound_choice),d2
 jmp open_sound_resume
es_select_error:
 jmp extra_redraw
.endif

.balign 4
sd_length: .long 0
sd_loading: .byte 0
sd_lease: .byte 0
.balign 4
sd_paths: .long ciallo_path,man_path,custom_path
sd_read: .asciz "rb"
ciallo_path: .asciz "C:\\OM3MOD\\CIALLO.WAV"
man_path: .asciz "C:\\OM3MOD\\MAN.WAV"
custom_path: .asciz "C:\\OM3MOD\\CUSTOM.WAV"

.ifdef NATIVE_MENU
.balign 4
copy_key: .asciz "PRM_AUD_SHUT1_VOL"
.balign 4
.include "native_wav.inc"
.else
.include "sd_custom.inc"
.endif
