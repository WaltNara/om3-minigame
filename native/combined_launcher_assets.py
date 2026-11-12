"""Shared five-entry launcher: pooled immutable rows and one bounded buffer."""
from pathlib import Path
import struct
import assets_large as a
ENTRIES=('2048','MINESWEEPER','MINI MARIO','BREAKOUT','BACK')
a.FONT.setdefault('B',['110','101','110','101','110'])

def make(out):
    pool={}; maps=[]; cap=0
    for selected in range(len(ENTRIES)):
        p=bytearray([7])*(384*480)
        def rect(x,y,w,h,c):
            for yy in range(y,y+h):p[yy*384+x:yy*384+x+w]=bytes([c])*w
        def label(text,y,scale,c):
            x=(384-len(text)*4*scale)//2
            for ch in text:
                for yy,row in enumerate(a.FONT.get(ch,a.FONT[' '])):
                    for xx,bit in enumerate(row):
                        if bit=='1':rect(x+xx*scale,y+yy*scale,scale,scale,c)
                x+=4*scale
        label('GAMES',32,6,10)
        for i,title in enumerate(ENTRIES):
            y=108+i*72
            if i==selected:rect(20,y-14,344,56,10)
            label(title,y,6,7 if i==selected else 10)
        indices=[];size=4
        for y in range(480):
            b=a.pack_row(p[y*384:(y+1)*384]);size+=len(b)
            if b not in pool:pool[b]=len(pool)
            indices.append(pool[b])
        maps+=indices;cap=max(cap,size)
    source='.balign 4\nlauncher_maps:\n .short '+','.join(map(str,maps))+'\n.balign 4\nlauncher_rows:\n'
    for b,i in pool.items():source+=f' .long {len(b)},lr_{i}\n'
    for b,i in pool.items():source+=f'lr_{i}:\n .byte '+','.join(map(str,b))+'\n'
    source+=f'.balign 4\n.global launcher_buffer,launcher_buffer_end\nlauncher_buffer: .space {cap},0\nlauncher_buffer_end:\n'
    # Small, padded footer avoids the stock title's clipped font box.
    pixels=bytearray([7])*(120*32)
    for i,ch in enumerate('GAMES'):
        for yy,row in enumerate(a.FONT[ch]):
            for xx,bit in enumerate(row):
                if bit=='1':
                    for dy in range(3):
                        off=(8+yy*3+dy)*120+31+i*12+xx*3
                        pixels[off:off+3]=bytes([10])*3
    footer=struct.pack('<I',31 | (119<<12) | (11<<24))+b''.join(a.pack_row(pixels[y*120:(y+1)*120]) for y in range(32))
    source+='.balign 4\n.global games_footer\ngames_footer:\n .byte '+','.join(map(str,footer))+'\n'
    (Path(out)/'combined_launcher.inc').write_text(source,encoding='ascii')
    return {'capacity':cap,'pooled_rows':len(pool),'row_bytes':sum(map(len,pool))}
