import unittest
from demo import Game, merge_line


class RulesTests(unittest.TestCase):
    def test_merge_once_per_tile(self):
        self.assertEqual(merge_line([2, 2, 2, 2]), ([4, 4, 0, 0], 8))
        self.assertEqual(merge_line([2, 2, 4, 0]), ([4, 4, 0, 0], 4))
        self.assertEqual(merge_line([4, 0, 4, 4]), ([8, 4, 0, 0], 8))

    def test_all_directions(self):
        for direction, cells, destination in [
            ("left", [0, 1], 0), ("right", [0, 1], 3),
            ("up", [0, 4], 0), ("down", [0, 4], 12),
        ]:
            with self.subTest(direction=direction):
                game = Game(12)
                game.board = [0] * 16
                for i in cells:
                    game.board[i] = 2
                self.assertTrue(game.move(direction))
                self.assertEqual(game.board[destination], 4)
                self.assertEqual(game.score, 4)
                self.assertEqual(sum(v != 0 for v in game.board), 2)

    def test_no_op_does_not_spawn_or_consume_randomness(self):
        game = Game(1)
        game.board = [2, 0, 0, 0] + [0] * 12
        before, rng = game.board[:], game.rng.getstate()
        self.assertFalse(game.move("left"))
        self.assertEqual(game.board, before)
        self.assertEqual(game.rng.getstate(), rng)
        self.assertEqual((game.score, game.moves), (0, 0))

    def test_game_over_and_vertical_escape(self):
        game = Game(1)
        game.board = [2, 4, 2, 4, 4, 2, 4, 2] * 2
        self.assertTrue(game.over)
        game.board[4] = 2
        self.assertFalse(game.over)
        game.board[4] = 0
        self.assertFalse(game.over)

    def test_random_play_conserves_tile_sum_except_spawn(self):
        game = Game(7)
        for i in range(400):
            before = sum(game.board)
            changed = game.move(("left", "up", "right", "down")[i % 4])
            self.assertIn(sum(game.board) - before, (2, 4) if changed else (0,))
            self.assertTrue(all(v == 0 or (v > 0 and v & (v - 1) == 0) for v in game.board))


if __name__ == "__main__":
    unittest.main()
