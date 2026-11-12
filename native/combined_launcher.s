/* One shared buffer assembled from immutable rows only when shown. */
.am33_2
.text
.global launcher_paint
launcher_paint:
 movm [d2,d3,a2,a3],(sp)
 mov launcher_buffer+0x40000000,a3
 mov 0x0b17f1df,d0
 mov d0,(a3)
 inc4 a3
 movbu (games_selection),d0
 /* selection * 960 bytes, avoiding MDR changes in a CALLS context. */
 mov d0,d1
 asl 10,d0
 asl 6,d1
 sub d1,d0
 mov launcher_maps,a2
 add d0,a2
 mov 480,d3
launcher_line:
 movhu (a2),d0
 add 2,a2
 asl 3,d0
 mov launcher_rows,a0
 add d0,a0
 mov (a0),d0
 mov (4,a0),a1
launcher_copy:
 mov (a1),d1
 mov d1,(a3)
 inc4 a1
 inc4 a3
 add -4,d0
 bne launcher_copy
 add -1,d3
 bne launcher_line
 movm (sp),[d2,d3,a2,a3]
 ret [],4
.include "combined_launcher.inc"
