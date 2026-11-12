/* Emulator-only periodic timer probe; no GUI pointers or camera writes. */
.am33_2
.text
.global mario_timer_start,mario_timer_stop,mario_timer_count,mario_timer_handle
mario_timer_start:
 movm [d2],(sp)
 mov 130,d0
 mov 120,d1
 mov mario_timer_callback,a0
 clr d2
 mov d2,a1
 call timer_create,[d2],8
 movhu d0,(mario_timer_handle)
 movm (sp),[d2]
 ret [],4
mario_timer_stop:
 movm [d2],(sp)
 mov 2,d0
 movhu (mario_timer_handle),d1
 call timer_delete,[d2],8
 clr d0
 movhu d0,(mario_timer_handle)
 movm (sp),[d2]
 ret [],4
mario_timer_callback:
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 mov (mario_timer_count),d0
 inc d0
 mov d0,(mario_timer_count)
 add -4,sp
 mov 2,d0
 call mario_step,[],4
 add 4,sp
 movm (sp),[d2,d3,a2,a3]
 movm (sp),[other]
 rets
.balign 4
mario_timer_count: .long 0
mario_timer_handle: .short 0
