/* Emulator experiment only. Called inside the GUI presentation bracket.
 * Disabled by default; the debugger arms it for one frame. */
.am33_2
.text
.extern bitmap
.extern original_end
.extern resume
.global probe, probe_flag, probe_image
probe:
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 add -32,sp
 movbu (probe_flag),d0
 cmp 0,d0
 beq finish
 clr d0
 movbu d0,(probe_flag)
 mov d0,(4,sp)
 mov d0,(8,sp)
 mov d0,(12,sp)
 mov d0,(16,sp)
 mov 1,d0
 mov d0,(20,sp)
 mov 322,d0
 mov 120,d1
 mov 0x62b77c44,a0
 mov probe_image+0x40000000,a1
 call bitmap,[d2,d3,a2,a3],96
 mov 0, d0
 mov d0,(4,sp)
 mov d0,(8,sp)
 mov d0,(12,sp)
 mov d0,(16,sp)
 mov 1,d0
 mov d0,(20,sp)
 mov 322,d0
 mov 120,d1
 mov 0x62b77c54,a0
 mov probe_image+0x40000000,a1
 call bitmap,[d2,d3,a2,a3],96
finish:
 add 32,sp
 movm (sp),[d2,d3,a2,a3]
 movm (sp),[other]
 call original_end,[],4
 jmp resume
.balign 4
probe_flag: .byte 0
.balign 4
probe_image: .incbin "panel.bin"
