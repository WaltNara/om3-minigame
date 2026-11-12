"""Generate static 384 x 480 launcher bitmaps for the emulator probe."""
from pathlib import Path
import struct
import assets

FONT=dict(assets.FONT, B=['110','101','110','101','110'],
          Z=['111','001','010','100','111'],
          X=['101','101','010','101','101'])
W,H=384,480
def image(selection):
    pixels=bytearray([7])*(W*H)
    def rect(x,y,w,h,c):
        for yy in range(y,y+h): pixels[yy*W+x:yy*W+x+w]=bytes([c])*w
    def label(text,x,y,scale,colour):
        for ch in text:
            glyph=FONT.get(ch,FONT[' '])
            for row,line in enumerate(glyph):
                for col,bit in enumerate(line):
                    if bit=='1':rect(x+col*scale,y+row*scale,scale,scale,colour)
            x+=4*scale
    label('GAMES',142,55,6,10)
    for i,(text,y) in enumerate((('2048',170),('BACK',280))):
        if selection==i:
            rect(80,y-22,224,74,10)
        label(text,152,y,6,7 if selection==i else 10)
    rows=[assets.pack_row(pixels[y*W:(y+1)*W]) for y in range(H)]
    return struct.pack('<I',0x0b17f1df)+b''.join(rows)
def make(out):
    for i in range(2):
        (Path(out)/f'launcher{i}.bin').write_bytes(image(i))
