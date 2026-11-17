"""Small static HUD; flight uses existing Mario chunks, scratch and buffer."""
from pathlib import Path
import assets_large as a

def make(path,touch=False):
    pool={};defs=[];source='.balign 4\n';maxima=[]
    ready='FLAPPY  TAP TO START' if touch else 'FLAPPY  OK TO START'
    footer='TAP OR OK UP TO FLAP' if touch else 'OK OR UP TO FLAP'
    for label,texts in [('fp_titles',[ready,'FLAPPY  EASY FLIGHT','FLAPPY  TRY AGAIN']),
                        ('fp_footer',[footer+'|INFO RESET  MENU BACK']*3)]:
        source+=label+':\n';sizes=[]
        for text in texts:
            p=bytearray([7])*(384*48)
            for li,line in enumerate(text.split('|')):
                x=(384-len(line)*8)//2
                for ch in line:
                    for y,row in enumerate(a.FONT.get(ch,a.FONT[' '])):
                        for xx,v in enumerate(row):
                            if v=='1':
                                for dy in range(2):
                                    i=(4+li*24+y*2+dy)*384+x+xx*2;p[i:i+2]=bytes([10])*2
                    x+=8
            sizes.append(0)
            for y in range(0,48,2):
                b=a.pack_row(p[y*384:(y+1)*384]);sizes[-1]+=2*len(b)
                if b not in pool:
                    name=f'fp_row_{len(pool)}';pool[b]=name
                    defs.append(name+':\n .byte '+','.join(map(str,b))+'\n')
                source+=f' .long {len(b)},{pool[b]}\n'
        maxima.append(max(sizes))
    Path(path).write_text(source+''.join(defs),encoding='ascii')
    # Exhaust both fixed slots: leading position, spacing and independent row
    # presence of each pipe and bird. Ordering of slots cannot change a row.
    # The renderer packs 12 chunks, not a generic arbitrary-pixel scanline.
    maxrow=0
    for x in range(-12,97):
        for spacing in (56,72,88,104):
            for flags in range(8):
                p=[0]*96
                spans=[(0,2),(94,96)]
                if flags&1:spans.append((x,x+12))
                if flags&2:spans.append((x+spacing,x+spacing+12))
                if flags&4:spans.append((24,30))
                for lo,hi in spans:
                    for i in range(max(0,lo),min(96,hi)):p[i]=1
                maxrow=max(maxrow,sum(len(a.pack_row([10 if b else 7 for b in p[i:i+8] for _ in range(4)])) for i in range(0,96,8)))
    return dict(max_output_bytes=4+sum(maxima)+15*32*8+33*len(a.pack_row([7]*384))+336*maxrow,max_world_row_bytes=maxrow,shared_buffer='mario_buffer',tick_ms=120,pipe_pixels_per_second=33.3,gap_pixels=128,pipe_slots=2,pipe_spacing_pixels=[224,288,352,416],max_gap_shift_pixels=[12,28,48,48])
