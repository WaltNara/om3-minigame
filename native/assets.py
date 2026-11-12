"""Original compact 2048 graphics. Concatenable RLE rows; no framebuffer.

Every row segment contains a multiple of five 12-bit tokens, so the camera
only copies prepacked words to compose a board. Runs never cross scanlines.
"""
import struct

FONT={
 '0':['111','101','101','101','111'],'1':['010','110','010','010','111'],
 '2':['110','001','010','100','111'],'3':['110','001','010','001','110'],
 '4':['101','101','111','001','001'],'5':['111','100','110','001','110'],
 '6':['011','100','111','101','111'],'7':['111','001','010','010','010'],
 '8':['111','101','111','101','111'],'9':['111','101','111','001','110'],
 'A':['010','101','111','101','101'],'C':['011','100','100','100','011'],
 'D':['110','101','101','101','110'],'E':['111','100','110','100','111'],
 'G':['011','100','101','101','011'],'H':['101','101','111','101','101'],
 'I':['111','010','010','010','111'],'K':['101','101','110','101','101'],
 'L':['100','100','100','100','111'],'M':['101','111','111','101','101'],
 'N':['101','111','111','111','101'],'O':['111','101','101','101','111'],
 'P':['110','101','110','100','100'],'R':['110','101','110','101','101'],
 'S':['011','100','010','001','110'],'T':['111','010','010','010','010'],
 'U':['101','101','101','101','111'],'V':['101','101','101','101','010'],
 'W':['101','101','111','111','101'],'Y':['101','101','010','010','010'],
 '!':['010','010','010','000','010'],' ':['000']*5,
}

def pack_row(pixels):
    runs=[]
    for p in pixels:
        if runs and runs[-1][0]==p and runs[-1][1]<16:
            runs[-1][1]+=1
        else:
            runs.append([p,1])
    while len(runs)%5:
        i=next(i for i,r in enumerate(runs) if r[1]>1)
        p,n=runs[i]; runs[i:i+1]=[[p,n-1],[p,1]]
    tokens=[p*16+n-1 for p,n in runs]
    return b''.join(sum(t<<(12*j) for j,t in enumerate(tokens[k:k+5])).to_bytes(8,'little') for k in range(0,len(tokens),5))

def make(path):
    pool={}; definitions=[]
    def intern(b):
        if b not in pool:
            name=f'row_{len(pool)}'; pool[b]=name
            definitions.append(f'{name}:\n'+''.join(' .byte '+','.join(map(str,b[k:k+24]))+'\n' for k in range(0,len(b),24)))
        return pool[b]
    rows=[]; lengths=[]
    for exponent in range(18):
        # Palette indices already used by the camera's guide images.
        # Opaque white cells and dark digits stay legible with the guide LUT.
        bg=10
        for style in range(6):
            p=[7]*4+[bg]*60
            if exponent and style:
                text=str(1<<exponent); x=(64-(len(text)*8-2))//2
                for ch in text:
                    for bit in FONT[ch][style-1]:
                        for _ in range(2):
                            if bit=='1': p[x]=7
                            x+=1
                    x+=2
            b=pack_row(p); rows.append((len(b),intern(b))); lengths.append(len(b))
    gap=pack_row([7]*64); blank=pack_row([7]*256)
    head='.balign 4\ntile_rows:\n'+''.join(f' .long {n},{label}\n' for n,label in rows)
    head+=f'gap_row:\n .long {len(gap)},{intern(gap)}\nblank_row:\n .long {len(blank)},{intern(blank)}\n'
    # Each 8-pixel character row fits exactly five tokens (one 64-bit word).
    head+='char_rows:\n'
    for code in range(128):
        glyph=FONT.get(chr(code),FONT[' '])
        for style in range(5):
            p=[7]+[10 if v=='1' else 7 for v in glyph[style] for _ in range(2)]+[7]
            b=pack_row(p); assert len(b)==8
            head+=f' .long {intern(b)}\n'
    head+='move_maps:\n'
    maps=[[[y*4+x for y in range(4)] for x in range(4)],
          [[y*4+x for y in range(3,-1,-1)] for x in range(4)],
          [[y*4+x for x in range(4)] for y in range(4)],
          [[y*4+x for x in range(3,-1,-1)] for y in range(4)]]
    for m in maps: head+=' .byte '+','.join(str(v) for line in m for v in line)+'\n'
    for label,text in [('hud_top','2048 SCORE 00000000'),('hud_play','ARROWS MOVE  HOLD OK NEW'),('hud_won','2048! KEEP PLAYING'),('hud_dead','GAME OVER  HOLD OK NEW')]:
        head+=f'{label}:\n .ascii "{text.ljust(32)}"\n'
    head+='.set score_digits,hud_top+11\npowers10:\n .long 10000000,1000000,100000,10000,1000,100,10,1\n'
    maxlens=[max(lengths[e*6+s] for e in range(18)) for s in range(6)]
    cap=4*4*(50*maxlens[0]+4*len(gap)+2*sum(maxlens[1:]))+2*(10*32*8+22*len(blank))+4
    assert cap<24576
    head+=''.join(definitions)
    head+=f'.balign 4\n.global board_buffer, board_buffer_end\nboard_buffer:\n .space {cap},0\nboard_buffer_end:\n'
    path.write_text(head,encoding='ascii')
    return {'compressed_board_capacity':cap,'asset_row_bytes':sum(map(len,pool)),
            'full_framebuffer_bytes':256*320,'tile_exponent_bytes':16,
            'heap_allocations':0,'row_copy_max_bytes':max(maxlens)}
