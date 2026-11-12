"""Reusable RLE chunks: 96-byte scratch row, 256 tiny patterns, no frame encoder.

Art uses deliberate 4px pixels. World physics keeps full pixel precision.
The buffer bound covers every possible row pattern, not sampled scenes.
"""
from pathlib import Path
import assets_large as a
import mario_level
W,H=384,480
WORLD_TOP,WORLD_BOTTOM=96,432
a.FONT.update(J=['001','001','001','101','010'],F=['111','100','110','100','100'],B=['110','101','110','101','110'])
a.FONT['/']=['001','001','010','100','100']

def make(path):
    pool={}; defs=[]
    def intern(p):
        b=a.pack_row(p)
        if b not in pool:
            name=f'mr_{len(pool)}'; pool[b]=name
            defs.append(name+':\n .byte '+','.join(map(str,b))+'\n')
        return f' .long {len(b)},{pool[b]}\n'
    rows='.balign 4\nmario_chunks:\n'
    lengths=[]
    for mask in range(256):
        p=[10 if mask & (1<<i) else 7 for i in range(8) for _ in range(4)]
        lengths.append(len(a.pack_row(p))); rows+=intern(p)
    assert max(lengths)==16
    def label(p,text,y,scale=3):
        x=(W-len(text)*4*scale)//2
        for ch in text:
            for yy,line in enumerate(a.FONT.get(ch,a.FONT[' '])):
                for xx,v in enumerate(line):
                    if v=='1':
                        for dy in range(scale):
                            start=(y+yy*scale+dy)*W+x+xx*scale
                            p[start:start+scale]=bytes([10])*scale
            x+=4*scale
    # Each header has a fixed title strip and a separately selected coin strip.
    rows+='mario_headers:\n'; header_lengths=[]
    for text in ['MINI MARIO','COURSE CLEAR!','TRY AGAIN!']:
        p=bytearray([7])*(W*48); label(p,text,14,4)
        ls=[]
        for y in range(48):
            row=p[y*W:(y+1)*W]; rows+=intern(row); ls.append(len(a.pack_row(row)))
        header_lengths.append(sum(ls))
    rows+='mario_coin_hud:\n'; coin_lengths=[]
    for count in range(8):
        p=bytearray([7])*(W*48); label(p,f'COURSE 1  COINS {count}/7',12,3)
        ls=[]
        for y in range(48):
            row=p[y*W:(y+1)*W]; rows+=intern(row); ls.append(len(a.pack_row(row)))
        coin_lengths.append(sum(ls))
    p=bytearray([7])*(W*48)
    label(p,'ARROWS MOVE  UP OK JUMP',2,3); label(p,'INFO RETRY  MENU BACK',25,3)
    rows+='mario_footer:\n'; footer_size=0
    for y in range(48):
        row=p[y*W:(y+1)*W]; rows+=intern(row); footer_size+=len(a.pack_row(row))
    capacity=4+max(header_lengths)+max(coin_lengths)+footer_size+336*12*max(lengths)
    rows+=''.join(defs)
    rows+='\n.balign 4\nmario_scratch: .space 96,0\n'
    rows+='mario_row_buffer: .space 192,0\n'
    rows+='mario_hero_poses: .byte 6,7,3,7,2,5, 6,7,3,7,2,6, 6,7,3,7,5,2\n'
    rows+='mario_enemy_pose: .byte 6,15,9,10\n'
    rows+='mario_coin_pose: .byte 3,3,3\n'
    rows+='mario_block_poses: .byte 15,9,13,15, 15,9,9,15\n'
    rows+=f'.balign 4\n.global mario_buffer,mario_buffer_end\nmario_buffer: .space {capacity},0\nmario_buffer_end:\n'
    Path(path).write_text(rows,encoding='ascii')
    mario_level.make(Path(path).with_name('mario_level.inc'))
    return {'capacity':capacity,'scratch_bytes':288,'max_chunk':max(lengths),'unique_rows':len(pool),'asset_bytes':sum(map(len,pool)),'world_width':1152,'pixel_scale':4}
