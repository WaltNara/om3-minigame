"""Desktop 2048 experiment for a possible OM-3 port; Python standard library only."""
import random
import sys


def merge_line(line):
    """Slide toward index zero. Each tile merges at most once per move."""
    tiles = [value for value in line if value]
    result, score = [], 0
    i = 0
    while i < len(tiles):
        value = tiles[i]
        if i + 1 < len(tiles) and value == tiles[i + 1]:
            value *= 2
            score += value
            i += 1
        result.append(value)
        i += 1
    return result + [0] * (4 - len(result)), score


class Game:
    """No UI dependencies: four directions in, a 16-cell board and score out."""
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.reset()

    def reset(self):
        self.board = [0] * 16
        self.score = self.moves = 0
        self.spawn()
        self.spawn()

    def spawn(self):
        empty = [i for i, value in enumerate(self.board) if not value]
        if empty:
            self.board[self.rng.choice(empty)] = 4 if self.rng.random() < 0.1 else 2

    def move(self, direction):
        if direction not in ("left", "right", "up", "down"):
            raise ValueError(direction)
        previous = self.board[:]
        gained = 0
        for n in range(4):
            indices = ([4 * n + k for k in range(4)] if direction in ("left", "right")
                       else [4 * k + n for k in range(4)])
            if direction in ("right", "down"):
                indices.reverse()
            values, score = merge_line([self.board[i] for i in indices])
            gained += score
            for i, value in zip(indices, values):
                self.board[i] = value
        if self.board == previous:
            return False
        self.score += gained
        self.moves += 1
        self.spawn()
        return True

    @property
    def over(self):
        return not any(value == 0 for value in self.board) and not any(
            (i % 4 < 3 and value == self.board[i + 1]) or
            (i < 12 and value == self.board[i + 4])
            for i, value in enumerate(self.board)
        )


class Demo:
    # Desktop layout only; this does not emulate the camera display hardware.
    COLORS = {0: "#303736", 2: "#e4e8dd", 4: "#cddbc1", 8: "#afc694",
              16: "#8ead73", 32: "#d6c17a", 64: "#e4aa61", 128: "#e58c59",
              256: "#e16b50", 512: "#cc5261", 1024: "#aa648a", 2048: "#a38ac5"}

    def __init__(self, root):
        import tkinter as tk
        self.root = root
        self.game = Game()
        root.title("OM-3 mini-game / local demo")
        root.resizable(False, False)
        root.configure(bg="#171d1c")
        self.canvas = tk.Canvas(root, width=640, height=480, bg="#171d1c",
                                highlightthickness=0, takefocus=True)
        self.canvas.pack()
        controls = tk.Frame(root, bg="#171d1c", pady=10)
        controls.pack(fill="x")
        for title, action in [("Left", "left"), ("Up", "up"), ("Down", "down"),
                              ("Right", "right"), ("OK / New", "reset"), ("Menu / Exit", "exit")]:
            tk.Button(controls, text=title, command=lambda a=action: self.act(a),
                      bg="#303b36", fg="#eef0e7", activebackground="#52674b",
                      activeforeground="white", relief="flat", padx=12, pady=7,
                      takefocus=False).pack(side="left", padx=4)
        root.bind("<KeyPress>", self.key)
        self.canvas.focus_set()
        self.draw()

    def key(self, event):
        action = {"Left": "left", "Right": "right", "Up": "up", "Down": "down",
                  "a": "left", "d": "right", "w": "up", "s": "down",
                  "Return": "reset", "r": "reset", "Escape": "exit"}.get(event.keysym)
        if action:
            self.act(action)
            return "break"

    def act(self, action):
        if action == "exit":
            self.root.destroy()
            return
        if action == "reset":
            self.game.reset()
        else:
            self.game.move(action)
        self.draw()
        self.canvas.focus_set()

    def draw(self):
        c, g = self.canvas, self.game
        c.delete("all")
        c.create_text(24, 26, anchor="w", text="2048", fill="#eef0e7", font=("Segoe UI", 23, "bold"))
        c.create_text(616, 26, anchor="e", text="OM-3 STUDY  /  DESKTOP", fill="#9cae9f",
                      font=("Segoe UI", 10))
        for i, value in enumerate(g.board):
            x, y = 24 + (i % 4) * 92, 68 + (i // 4) * 92
            c.create_rectangle(x, y, x + 84, y + 84, fill=self.COLORS.get(value, "#8ba5c7"), width=0)
            if value:
                c.create_text(x + 42, y + 42, text=str(value), fill="#18231c",
                              font=("Segoe UI", 23 if value < 10000 else 17, "bold"))
        c.create_text(422, 80, anchor="nw", text=f"SCORE\n{g.score}\n\nMOVES\n{g.moves}",
                      fill="#eef0e7", font=("Segoe UI", 16, "bold"))
        c.create_text(422, 285, anchor="nw", text="Arrows / WASD: move\nEnter / R: new game\nEscape: exit",
                      fill="#aab8ac", font=("Segoe UI", 11), width=190)
        status = ("No moves left. Enter starts again." if g.over else
                  "2048 reached! Keep playing." if max(g.board) >= 2048 else
                  "Slide matching tiles together. Reach 2048.")
        c.create_text(24, 458, anchor="w", text=status, fill="#c8d4bc", font=("Segoe UI", 12))


def main():
    import tkinter as tk
    root = tk.Tk()
    smoke = "--smoke-test" in sys.argv
    if smoke:
        root.withdraw()
    app = Demo(root)
    if smoke:
        from types import SimpleNamespace
        app.game.board = [2, 2, 0, 0] + [0] * 12
        app.key(SimpleNamespace(keysym="Left"))
        assert app.game.score == 4 and app.game.moves == 1
        assert app.canvas.find_all()
        app.key(SimpleNamespace(keysym="Return"))
        assert app.game.score == 0 and sum(v != 0 for v in app.game.board) == 2
        root.update_idletasks()
        app.key(SimpleNamespace(keysym="Escape"))
        print("Tk smoke test passed: draw, input, reset, exit.")
    else:
        root.mainloop()


if __name__ == "__main__":
    main()
