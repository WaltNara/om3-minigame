"""Tighten static output bounds only. Renderer and packed row bytes unchanged."""
import re
from pathlib import Path

def replace_capacity(path,label,old,new):
    assert 0 < new <= old and new % 4 == 0
    p=Path(path); text=p.read_text(encoding='ascii')
    pattern=rf'({label}:\s*\.space ){old}(,0)'
    text,n=re.subn(pattern,lambda m:m[1]+str(new)+m[2],text)
    assert n==1
    p.write_text(text,encoding='ascii')

def install(tiles,mines):
    original_mines=mines.make
    def make_mines(path):
        info=original_mines(path)
        styles=mines.y_tables()[2][48:96]
        # Entire cell uses one kind and cursor status, not an independent
        # worst case on every scanline. At most one of 64 cells is the cursor.
        sizes=[[sum(len(tiles.pack_row(mines.tile_pixels(kind,style,cursor)))
                    for style in styles) for kind in range(mines.CURSOR_TYPES)] for cursor in (0,1)]
        plain=max(sizes[0]);cursor=max(sizes[1])
        cap=4+63*plain+max(plain,cursor)+2*(15*32*8+33*len(tiles.pack_row([7]*384)))
        old=info['capacity'];replace_capacity(path,'mines_buffer',old,cap)
        info.update(capacity=cap,previous_capacity=old,whole_cell_bounds=[plain,cursor])
        return info
    mines.make=make_mines
