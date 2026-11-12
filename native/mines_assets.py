"""Prepacked RLE graphics for an 8x8 camera Minesweeper board.

Every row segment is a whole number of five 12-bit RLE tokens, exactly like
the 2048 board. The renderer only copies prepacked words; it never encodes a
scanline at runtime, allocates memory or runs an animation timer. Two palette
indices are used: 7 (background) and 10 (foreground), the pair already proven
by the 2048 guide images.
"""
from pathlib import Path
import assets_large as a

W, H = 384, 480
HEADER, FOOTER = 48, 432
CELL = 48
COLS = ROWS = 8
BG, FG = 7, 10
STYLES = 7                 # 0 blank, 1..5 glyph rows, 6 horizontal frame
CURSOR_TYPES = 13
# Cell kinds: hidden, flag, open blank, open 1..8, mine, exploded mine.
T_HIDDEN, T_FLAG, T_BLANK, T_MINE, T_BOOM = 0, 1, 2, 11, 12

FONT = dict(a.FONT,
            F=['111', '100', '110', '100', '100'],
            B=['110', '101', '110', '101', '110'],
            X=['101', '101', '010', '101', '101'],
            Z=['111', '001', '010', '100', '111'],
            J=['001', '001', '001', '101', '010'])
GLYPH_MINE = ['010', '111', '111', '111', '010']
GLYPH_FLAG = ['011', '111', '011', '010', '010']
HUD_TOP = 'MINES 10  OPEN 00  FLAGS 00     '
HUD_PLAY = 'ARROWS MOVE  OK OPEN  INFO FLAG '
HUD_WON = 'ALL CLEAR!  OK NEW GAME'.ljust(32)
HUD_DEAD = 'BOOM!  OK NEW GAME'.ljust(32)


def glyph_for(kind):
    if kind == T_FLAG:
        return GLYPH_FLAG
    if kind in (T_MINE, T_BOOM):
        return GLYPH_MINE
    if 3 <= kind <= 10:
        return FONT[str(kind - 2)]
    return FONT[' ']


def tile_pixels(kind, style, cursor):
    """One 48-pixel scanline of a cell. style selects the glyph row.

    Every cell carries a two-pixel vertical grid line and three horizontal
    grid lines, so hidden tiles never merge into one solid block. The cursor
    cell is inverted: a background interior with a bright border.
    """
    hidden = kind in (T_HIDDEN, T_FLAG)
    exploded = kind == T_BOOM
    bg = FG if (hidden != exploded) else BG
    if cursor:
        bg = BG if bg == FG else FG
    ink = BG if bg == FG else FG
    frame = ink
    p = [bg] * CELL
    for x in (0, 1, CELL - 2, CELL - 1):
        p[x] = frame
    if style == 6:
        p = [frame] * CELL
    if 1 <= style <= 5:
        line = glyph_for(kind)[style - 1]
        x = (CELL - 12) // 2
        for bit in line:
            for _ in range(4):
                if bit == '1':
                    p[x] = ink
                x += 1
    return p


def y_tables():
    modes, cells, styles = [], [], []
    for y in range(H):
        if y < HEADER or y >= FOOTER:
            local = y if y < HEADER else y - FOOTER
            glyph_line = 12 <= local < 27
            modes.append(2 if glyph_line else 1)
            cells.append(0)
            styles.append((local - 12) // 3 if glyph_line else 0)
        else:
            local = y - HEADER
            modes.append(0)
            cells.append(local // CELL)
            inside = local % CELL
            if inside < 3 or inside >= 45:
                styles.append(6)
            elif 14 <= inside < 34:
                styles.append(1 + (inside - 14) // 4)
            else:
                styles.append(0)
    return modes, cells, styles


def byte_table(name, values):
    out = f'{name}:\n'
    for i in range(0, len(values), 24):
        out += ' .byte ' + ','.join(map(str, values[i:i + 24])) + '\n'
    return out


def make(path):
    path = Path(path)
    pool = {}
    defs = []

    def intern(pixels):
        b = a.pack_row(pixels)
        if b not in pool:
            name = f'mr_{len(pool)}'
            pool[b] = name
            chunk = ','.join(map(str, b))
            defs.append(f'{name}:\n .byte {chunk}\n')
        return pool[b], len(b)

    # One (length, pointer) entry for each cell kind and scanline style.
    entries = []
    max_row = 0
    for cursor in (0, 1):
        for kind in range(CURSOR_TYPES):
            for style in range(STYLES):
                label, size = intern(tile_pixels(kind, style, cursor))
                entries.append((size, label))
                max_row = max(max_row, size)

    # Five glyph rows for every ASCII character used by the HUD.
    char_entries = []
    for code in range(128):
        glyph = FONT.get(chr(code), FONT[' '])
        for style in range(5):
            p = [BG] + [FG if v == '1' else BG for v in glyph[style] for _ in range(3)] + [BG] * 2
            label, size = intern(p)
            assert size == 8
            char_entries.append(label)

    blank_label, blank_size = intern([BG] * W)
    modes, cells, styles = y_tables()
    hud_line = 32 * 8
    board_line = COLS * max_row
    # Blank HUD rows copy one whole-line RLE word, not 32 empty characters.
    capacity = 4 + sum(hud_line if m == 2 else blank_size if m == 1 else board_line
                       for m in modes)
    assert capacity < 0x40000

    out = '.balign 4\n'
    out += 'mines_tile_rows:\n' + ''.join(f' .long {n},{label}\n' for n, label in entries)
    out += 'mines_char_rows:\n' + ''.join(f' .long {label}\n' for label in char_entries)
    out += f'mines_blank_row:\n .long {blank_size},{blank_label}\n'
    for name, text in (('mines_hud_top', HUD_TOP), ('mines_hud_play', HUD_PLAY),
                       ('mines_hud_won', HUD_WON), ('mines_hud_dead', HUD_DEAD)):
        assert len(text) <= 32, (name, len(text))
        out += f'{name}:\n .ascii "{text.ljust(32)}"\n'
    out += ('.set mines_left_digits,mines_hud_top+6\n'
            '.set mines_open_digits,mines_hud_top+15\n'
            '.set mines_flags_digits,mines_hud_top+25\n')
    out += byte_table('mines_y_mode', modes)
    out += byte_table('mines_y_cell', cells)
    out += byte_table('mines_y_style', styles)
    # Eight neighbour indices per cell; 255 marks an off-board neighbour.
    out += '.global mines_neighbors\nmines_neighbors:\n'
    for idx in range(COLS * ROWS):
        row, col = divmod(idx, COLS)
        ns = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = row + dr, col + dc
                ns.append(rr * COLS + cc if 0 <= rr < ROWS and 0 <= cc < COLS else 255)
        out += ' .byte ' + ','.join(map(str, ns)) + '\n'
    out += ''.join(defs)
    out += (f'\n.balign 4\n.global mines_buffer,mines_buffer_end\n'
            f'mines_buffer: .space {capacity},0\nmines_buffer_end:\n')
    path.write_text(out, encoding='ascii')
    return {'capacity': capacity, 'max_tile_row': max_row, 'unique_rows': len(pool),
            'hud_line_bytes': hud_line, 'board_line_bytes': board_line,
            'full_framebuffer_bytes': W * H, 'board_bytes': COLS * ROWS,
            'heap_allocations': 0, 'animation_timer': 0}
