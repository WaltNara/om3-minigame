/* Reusable chunks, GUI thread only. Each world row is built at 4px resolution
 * in 96 bytes, assembled from prepacked 32px chunks, then copied four times.
 * No per-pixel framebuffer, heap, object-combination tables, or RLE encoder. */
.am33_2
.text
.global mario_paint,mr_copy,mario_scratch,mario_row_buffer,mario_chunks
/* Copy d0 bytes a1 -> a0; advances a0. */
mr_copy:
 mov (a1),d1
 mov d1,(a0)
 inc4 a1
 inc4 a0
 add -4,d0
 bne mr_copy
 ret [],4
/* Plot a row of up to 8 white pixels, with transparent zero bits.
 * d0=world x, d1=bit mask. Clips both viewport edges. */
mr_sprite:
 movm [d2,d3,a2,a3],(sp)
 mov (mario_state+20),d2
 lsr 2,d2
 asr 2,d0
 sub d2,d0
 mov mario_scratch,a0
 add d0,a0
 mov 8,d3
sprite_bits:
 mov d1,d2
 and 1,d2
 beq sprite_next
 cmp 0,d0
 blt sprite_next
 cmp 96,d0
 bge sprite_next
 movbu d2,(a0)
sprite_next:
 inc d0
 inc a0
 lsr 1,d1
 add -1,d3
 bne sprite_bits
 movm (sp),[d2,d3,a2,a3]
 ret [],4
mario_paint:
 movm [d2,d3,a2,a3],(sp)
 add -24,sp
 mov mario_buffer+0x40000000,a3
 mov 0x0b17f1df,d0
 mov d0,(a3)
 inc4 a3
 clr d2
paint_rows:
 cmp 96,d2
 blt header_row
 cmp 432,d2
 bge footer_row
 /* Each scratch pixel covers 4x4 display pixels. */
 mov mario_scratch,a2
 clr d3
terrain_pixels:
 mov (mario_state+20),d0
 and -4,d0
 mov d3,d1
 asl 2,d1
 add d1,d0
 lsr 4,d0
 mov mario_heights,a0
 add d0,a0
 movbu (a0),d0
 extb d0
 cmp -64,d0
 beq sky_pixel
 mov 400,d1
 sub d0,d1
 cmp d1,d2
 blt sky_pixel
 mov 1,d0
 bra terrain_store
sky_pixel:
 clr d0
terrain_store:
 movbu d0,(a2)
 inc a2
 inc d3
 cmp 96,d3
 bne terrain_pixels
 /* A few original cloud silhouettes give scrolling a visible backdrop. */
 cmp 176,d2
 blt clouds_done
 cmp 192,d2
 bge clouds_done
 mov 31,d3
 cmp 184,d2
 bge cloud_mask
 mov 14,d3
cloud_mask:
 mov 80,d0
 mov d3,d1
 call mr_sprite,[],4
 mov 416,d0
 mov d3,d1
 call mr_sprite,[],4
 mov 736,d0
 mov d3,d1
 call mr_sprite,[],4
 mov 1040,d0
 mov d3,d1
 call mr_sprite,[],4
clouds_done:
 /* Flag stays in world coordinates, while the HUD stays in screen space. */
 cmp 304,d2
 blt coins
 cmp 400,d2
 bge coins
 mov 1108,d0
 mov 1,d1
 call mr_sprite,[],4
 cmp 320,d2
 bge coins
 mov 1088,d0
 mov 63,d1
 call mr_sprite,[],4
coins:
 mov mario_coin_positions,a2
 mov 1,d3
coin_rows:
 mov (mario_state+24),d0
 and d3,d0
 bne coin_next
 mov (4,a2),d0
 mov 400,d1
 sub d0,d1
 sub d2,d1
 cmp 0,d1
 ble coin_next
 cmp 12,d1
 bgt coin_next
 mov (a2),d0
 mov 3,d1
 call mr_sprite,[],4
coin_next:
 add 8,a2
 asl 1,d3
 cmp 64,d3
 bne coin_rows
 /* Block outline and its changed used face. */
 cmp 336,d2
 blt enemy
 cmp 352,d2
 bge enemy
 mov d2,d0
 add -336,d0
 lsr 2,d0
 mov (mario_state+32),d1
 asl 2,d1
 add d1,d0
 mov mario_block_poses,a0
 add d0,a0
 movbu (a0),d1
 mov 448,d0
 call mr_sprite,[],4
enemy:
 mov (mario_state+40),d0
 cmp 0,d0
 bne hero
 cmp 384,d2
 blt hero
 cmp 400,d2
 bge hero
 mov d2,d0
 add -384,d0
 lsr 2,d0
 mov mario_enemy_pose,a0
 add d0,a0
 movbu (a0),d1
 mov (mario_state+36),d0
 call mr_sprite,[],4
hero:
 mov (mario_state+4),d0
 asr 2,d0
 asl 2,d0
 mov 376,d1
 sub d0,d1
 mov d2,d0
 sub d1,d0
 cmp 0,d0
 blt chunks
 cmp 24,d0
 bge chunks
 lsr 2,d0
 mov mario_hero_poses,a0
 add d0,a0
 mov (mario_state+8),d0
 cmp 0,d0
 bne jump_pose
 mov (mario_state+52),d0
 and 2,d0
 beq pose_ready
 add 6,a0
 bra pose_ready
jump_pose:
 add 12,a0
pose_ready:
 movbu (a0),d1
 mov (mario_state+48),d0
 cmp 0,d0
 beq facing_ready
 mov d1,d0
 and 1,d0
 asl 2,d0
 mov d1,d3
 and 4,d3
 lsr 2,d3
 or d3,d0
 and 2,d1
 or d0,d1
facing_ready:
 mov (mario_state),d0
 call mr_sprite,[],4
chunks:
 mov mario_row_buffer,a0
 mov mario_scratch,a2
 mov 12,d3
chunk_loop:
 clr d0
 movbu (7,a2),d1
 or d1,d0
 asl 1,d0
 movbu (6,a2),d1
 or d1,d0
 asl 1,d0
 movbu (5,a2),d1
 or d1,d0
 asl 1,d0
 movbu (4,a2),d1
 or d1,d0
 asl 1,d0
 movbu (3,a2),d1
 or d1,d0
 asl 1,d0
 movbu (2,a2),d1
 or d1,d0
 asl 1,d0
 movbu (1,a2),d1
 or d1,d0
 asl 1,d0
 movbu (a2),d1
 or d1,d0
 add 8,a2
 asl 3,d0
 mov mario_chunks,a1
 add d0,a1
 mov (a1),d0
 mov (4,a1),a1
 call mr_copy,[],4
 add -1,d3
 bne chunk_loop
 mov a0,d0
 mov mario_row_buffer,d1
 sub d1,d0
 mov d0,(4,sp)
 mov 4,d3
repeat_row:
 mov (4,sp),d0
 mov mario_row_buffer,a1
 mov a3,a0
 call mr_copy,[],4
 mov a0,a3
 add -1,d3
 bne repeat_row
 add 4,d2
 bra paint_rows
header_row:
 cmp 48,d2
 bge coin_header
 mov (mario_state+16),d0
 mov d0,d1
 asl 1,d0
 add d1,d0
 asl 4,d0
 add d2,d0
 asl 3,d0
 mov mario_headers,a1
 add d0,a1
 bra copy_static
coin_header:
 mov (mario_state+28),d0
 mov d0,d1
 asl 1,d0
 add d1,d0
 asl 4,d0
 add d2,d0
 add -48,d0
 asl 3,d0
 mov mario_coin_hud,a1
 add d0,a1
 bra copy_static
footer_row:
 cmp 480,d2
 beq paint_done
 mov d2,d0
 add -432,d0
 asl 3,d0
 mov mario_footer,a1
 add d0,a1
copy_static:
 mov (a1),d0
 mov (4,a1),a1
 mov a3,a0
 call mr_copy,[],4
 mov a0,a3
 inc d2
 bra paint_rows
paint_done:
 add 24,sp
 movm (sp),[d2,d3,a2,a3]
 ret [],4
.include "mario_assets.inc"
