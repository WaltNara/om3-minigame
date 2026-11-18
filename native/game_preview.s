/* Use the display API's own no-permit branch while a Picture Mode game
 * owns the screen. Leave the shared permit, shooting and GUI layers alone. */
.am33_2
.text
.global game_preview_permit
.extern games_state, games_row_selected, through_permit, through_resume

game_preview_permit:
 movbu (games_state),d1
 cmp 0,d1
 beq stock_permit
 movbu (games_row_selected),d1
 cmp 1,d1
 bne stock_permit
 clr d0
 jmp through_resume
stock_permit:
 call through_permit,[d2,d3,a2],16
 jmp through_resume
