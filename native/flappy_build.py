"""Generate fifth-game host variants; preserve the four-game release sources."""
from pathlib import Path

def edit(s,old,new):
    assert s.count(old)==1,old
    return s.replace(old,new)

def prepare(root,out,touch=False):
    s=(root/'native/combined_host.s').read_text()
    s=edit(s,' cmp 5,d2\n beq breakout_input',' cmp 6,d2\n beq flappy_input\n cmp 5,d2\n beq breakout_input')
    at='breakout_input:\n'
    code='''flappy_input:
 cmp 0x900c,d0
 beq flappy_press
 cmp 0x9004,d0
 beq flappy_press
 cmp 0x900d,d0
 beq flappy_release_ok
 cmp 0x9005,d0
 beq flappy_release_up
 cmp 0x9014,d0
 beq flappy_restart
 cmp 0x900e,d0
 beq mario_menu_exit
 cmp 0x9601,d0
 beq display_change
 cmp 0x972b,d0
 beq consumed
 cmp 0x9031,d0
 beq consumed
 cmp 0x9032,d0
 beq consumed
 cmp 0x903e,d0
 beq consumed
 cmp 0x9004,d0
 blt pm_stock
 cmp 0x9015,d0
 ble consumed
 bra pm_stock
flappy_press:
 cmp 0x9004,d0
 beq flappy_up
 movbu (mario_keys),d2
 and 8,d2
 bne consumed
 bset 8,(mario_keys)
 bra flappy_queue
flappy_up:
 movbu (mario_keys),d2
 and 4,d2
 bne consumed
 bset 4,(mario_keys)
flappy_queue:
 mov 1,d2
 movbu d2,(flappy_pending)
 bra consumed
flappy_release_ok:
 bclr 8,(mario_keys)
 bra consumed
flappy_release_up:
 bclr 4,(mario_keys)
 bra consumed
flappy_restart:
 movm [other],(sp)
 movm [d2,d3,a2,a3],(sp)
 add -32,sp
 call mario_stop,[],4
 call flappy_reset,[],4
 call flappy_paint,[],4
 call mario_start,[],4
 mov 1,d0
 bra request_paint
'''
    s=edit(s,at,code+at)
    s=edit(s,' cmp 5,d0\n beq start_breakout',' cmp 6,d0\n beq start_flappy\n cmp 5,d0\n beq start_breakout')
    s=edit(s,'start_breakout:\n','start_flappy:\n call flappy_reset,[],4\n call flappy_paint,[],4\n call mario_start,[],4\n bra game_resumed\nstart_breakout:\n')
    s=edit(s,' cmp 5,d0\n beq render_mario',' cmp 6,d0\n beq render_mario\n cmp 5,d0\n beq render_mario')
    (out/'flappy-host.s').write_text(s)
    s=(root/'native/combined_bridge.s').read_text()
    s=edit(s,' clr d0\n movbu d0,(mario_keys)',' clr d0\n movbu d0,(flappy_pending)\n movbu d0,(mario_keys)')
    if touch:
        s=edit(s,' clr d0\n movbu d0,(flappy_pending)',
            ' movbu (flappy_contact),d0\n cmp 0,d0\n beq fp_no_drain\n movbu d0,(flappy_drain)\nfp_no_drain:\n clr d0\n movbu d0,(flappy_contact)\n movbu d0,(flappy_pending)')
    s=edit(s,' cmp 5,d0\n beq br_tick_valid',' cmp 6,d0\n beq br_tick_valid\n cmp 5,d0\n beq br_tick_valid')
    s=edit(s,' cmp 5,d0\n beq br_tick\n',' cmp 6,d0\n beq fp_tick\n cmp 5,d0\n beq br_tick\n')
    s=edit(s,'tick_invalidate:\n',' bra tick_invalidate\nfp_tick:\n call flappy_step,[],4\n call flappy_paint,[],4\ntick_invalidate:\n')
    s=edit(s,' cmp 5,d0\n bne mario_result',' cmp 6,d0\n beq tick_running\n cmp 5,d0\n bne mario_result')
    (out/'flappy-bridge.s').write_text(s)
    s=(root/'native/combined_menu.s').read_text()
    s=edit(s,' cmp 4,d0\n beq leave',' cmp 5,d0\n beq leave')
    s=edit(s,' mov 4,d0\n bra select_valid',' mov 5,d0\n bra select_valid')
    s=edit(s,' cmp 5,d0\n blt select_valid',' cmp 6,d0\n blt select_valid')
    (out/'flappy-menu.s').write_text(s)
