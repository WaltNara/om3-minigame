/* Host-independent Games navigation. No firmware calls or retained pointers.
 * d0 event (1=open, 2=up, 3=down, 4=OK, 5=MENU, 6=shutter).
 * d0 result: 0=pass to host/game, 1=redraw, 2=start game,
 * 3=leave launcher, 4=shutter transition. State: 0=closed, 1=menu,
 * 2=2048, 3=Minesweeper.
 * Selection: 0=2048, 1=Minesweeper, 2=Back. Game contents are owned by
 * the caller.
 */
.am33_2
.text
.global games_event, games_state, games_selection
games_event:
 movm [d2],(sp)
 movbu (games_state),d2
 cmp 6,d0
 beq shutter
 cmp 0,d2
 beq closed
 cmp 5,d0
 beq menu_key
 cmp 1,d2
 bne pass
 cmp 2,d0
 beq select_previous
 cmp 3,d0
 beq select_next
 cmp 4,d0
 bne pass
 movbu (games_selection),d0
 cmp 2,d0
 beq leave
 add 2,d0
 movbu d0,(games_state)
 mov 2,d0
 bra done
closed:
 cmp 1,d0
 bne pass
 mov 1,d0
 movbu d0,(games_state)
 clr d0
 movbu d0,(games_selection)
 mov 1,d0
 bra done
select_previous:
 movbu (games_selection),d0
 add -1,d0
 cmp 0,d0
 bge select_valid
 mov 2,d0
 bra select_valid
select_next:
 movbu (games_selection),d0
 inc d0
 cmp 3,d0
 blt select_valid
 clr d0
select_valid:
 movbu d0,(games_selection)
 mov 1,d0
 bra done
menu_key:
 cmp 2,d2
 blt leave
 mov 1,d0
 movbu d0,(games_state)
 bra done
leave:
 clr d0
 movbu d0,(games_state)
 mov 3,d0
 bra done
shutter:
 cmp 0,d2
 beq pass
 clr d0
 movbu d0,(games_state)
 mov 4,d0
 bra done
pass:
 clr d0
done:
 movm (sp),[d2]
 ret [],4
.balign 4
games_state: .byte 0
games_selection: .byte 0
