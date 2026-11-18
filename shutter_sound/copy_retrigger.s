/* Experiment on the native E147 audio copy path. Only copies from the
 * dedicated transport WAV can enter the renderer. AUD_COPY_DATA owns cursor
 * and consumed generation. The publisher changes requested generation with
 * one aligned store. The clip and transport remain immutable while armed. */
.am33_2
.text
.global render_shutter_pcm
.global stream_begin, stream_end, clip_begin, clip_end, shutter_requested
.extern stock_memcpy

/* memcpy ABI at 60adc465: a0 destination, a1 source, d0 byte count.
 * The converter's call site supplies [d2,d3,a2,a3],28. */
render_shutter_pcm:
 mov (stream_begin),d2
 cmp 0,d2
 beq stock_copy
 mov a1,d3
 cmp d2,d3
 bcs stock_copy
 cmp 768,d0
 bne stock_copy
 add d0,d3
 mov (stream_end),d2
 cmp d2,d3
 bhi stock_copy

 mov (shutter_requested),d2
 mov (shutter_consumed),d3
 cmp d3,d2
 beq keep_cursor
 mov d2,(shutter_consumed)
 clr d3
 cmp 0,d2                     /* Silent cancels the active clip. */
 beq render
 mov (clip_begin),d3
 bra render
keep_cursor:
 mov (clip_cursor),d3
render:
 mov d3,a2
 mov (clip_end),a3
 mov a0,d1
 mov d0,d2
 cmp 0,d3
 beq fill_silence

/* Copy each stereo frame, then fill the rest of the native period. */
copy_frames:
 cmp a3,a2
 bcc fill_silence
 mov (a2),d3
 mov d3,(a0)
 inc4 a2
 inc4 a0
 add -4,d2
 bne copy_frames
 bra rendered
fill_silence:
 clr d3
fill_frames:
 mov d3,(a0)
 inc4 a0
 add -4,d2
 bne fill_frames
rendered:
 mov a2,(clip_cursor)
 mov d1,d0
 ret [d2,d3,a2,a3],28
stock_copy:
 add -4,sp
 call stock_memcpy,[d2,d3,a2,a3],28
 ret [d2,d3,a2,a3],32

.balign 4
stream_begin: .long 0
stream_end: .long 0
clip_begin: .long 0
clip_end: .long 0
shutter_requested: .long 0
shutter_consumed: .long 0
clip_cursor: .long 0
