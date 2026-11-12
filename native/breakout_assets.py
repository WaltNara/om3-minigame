"""Original Breakout rectangles and compact HUD; shared Mario chunk buffer."""
from pathlib import Path
import assets_large as a
RECTS=[(2+c*16,14+c*16,30+r*7,35+r*7) for r in range(3) for c in range(6)]
def make(path):
    path=Path(path);pool={};rows='';defs=[]
    def intern(p):
        b=a.pack_row(p)
        if b not in pool:
            name='br_row_'+str(len(pool));pool[b]=name
            defs.append(name+':\n .byte '+','.join(map(str,b))+'\n')
        return f' .long {len(b)},{pool[b]}\n'
    def strip(text):
        p=bytearray([7])*(384*48)
        lines=text.split('|')
        for li,line in enumerate(lines):
            x=(384-len(line)*8)//2;ybase=16 if len(lines)==1 else 4+li*24
            for ch in line:
                for yy,row in enumerate(a.FONT.get(ch,a.FONT[' '])):
                    for xx,v in enumerate(row):
                        if v=='1':
                            for dy in range(2):
                                i=(ybase+yy*2+dy)*384+x+xx*2;p[i:i+2]=bytes([10])*2
                x+=8
        return [p[y*384:(y+1)*384] for y in range(48)]
    maxima=[]
    for label,texts in [('br_titles',['BREAKOUT','BREAKOUT','ALL CLEAR!','GAME OVER']),('br_lives',['BALLS 0','BALLS 1','BALLS 2','BALLS 3']),('br_footer',['OK TO LAUNCH|LEFT RIGHT  MENU BACK','LEFT RIGHT PADDLE|INFO NEW  MENU BACK','ALL BRICKS CLEARED|INFO NEW  MENU BACK','TRY AGAIN|INFO NEW  MENU BACK'])]:
        rows+=label+':\n';sizes=[]
        for t in texts:
            p=strip(t);rows+=''.join(intern(r) for r in p[::2]);sizes.append(sum(len(a.pack_row(r)) for r in p))
        maxima.append(max(sizes))
    path.write_text('.balign 4\n'+rows+''.join(defs),encoding='ascii')
    path.with_name('breakout_level.inc').write_text('breakout_rects:\n'+''.join(' .long '+','.join(map(str,r))+'\n' for r in RECTS),encoding='ascii')
    return {'max_output_bytes':4+sum(maxima)+336*12*16,'state_bytes':54,'bricks':18,'shared_buffer':'mario_buffer'}
