"""Original three-screen course shared by native collision and graphics.
One signed height per 16px column; -64 is a pit. No borrowed game assets.
"""
WIDTH = 1152
HEIGHTS = [0] * 72
for first, last, height in [(10,12,16),(12,14,32),(14,16,48),
                            (16,18,32),(18,20,16),(20,23,-64),
                            (48,51,-64),(56,58,16),(58,60,32),
                            (60,62,48),(62,64,32),(64,66,16)]:
    HEIGHTS[first:last] = [height] * (last-first)
COINS = [(120,40),(212,76),(344,36),(520,52),(792,36),(968,84)]
BLOCK_X, BLOCK_BOTTOM, BLOCK_TOP = 448, 48, 64
GOAL_X = 1104

def make(path):
    path.write_text('.balign 4\n.global mario_heights,mario_coin_positions\n'
        'mario_heights:\n .byte '+','.join(str(h & 255) for h in HEIGHTS)+
        '\n.balign 4\nmario_coin_positions:\n'+
        ''.join(f' .long {x},{y}\n' for x,y in COINS), encoding='ascii')
