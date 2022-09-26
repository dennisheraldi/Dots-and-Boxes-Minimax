import numpy as np
from GameState import GameState
from player import Player
from tile import Tile, Tiles

from util import todo

Flag = list[list[bool]]
Chain = list[Tile]
Chains = list[Chain]
Loops = list[Chain]


class PseudoBoard(GameState):

    loops: list[list[Tile]]
    chains: list[list[Tile]]
    dirty: bool

    def __init__(self, *args):
        super().__init__(*args)
        self.loops = []
        self.chains = []
        self.dirty = True

    def __str__(self):
        rep = ""
        for i in range(3):
            a = self.row_status[i, 0]
            b = self.row_status[i, 1]
            c = self.row_status[i, 2]
            rep += f"+{h_line(a)}+{h_line(b)}+{h_line(c)}+\n"

            a = self.col_status[i, 0]
            b = self.col_status[i, 1]
            c = self.col_status[i, 2]
            d = self.col_status[i, 3]

            x = None
            y = None
            z = None

            rep += f"{v_line(a)} {player_mark(x)} {v_line(b)} {player_mark(y)} {v_line(c)} {player_mark(z)} {v_line(d)}\n"

        a = self.row_status[3, 0]
        b = self.row_status[3, 1]
        c = self.row_status[3, 2]
        rep += f"+{h_line(a)}+{h_line(b)}+{h_line(c)}+\n"

        return rep

    def of(state):
        # type: (GameState) -> PseudoBoard

        return PseudoBoard(
            state.board_status,
            state.row_status,
            state.col_status,
            state.player1_turn
        )

    def eval(self, player):
        # type: (Player) -> int

        todo("Implement evaluation (heuristic minimax) function.")

    def chainable_tiles(self):
        # type: () -> Tiles

        tiles = []
        for i in range(3):
            for j in range(3):
                if self.chainable((i, j)):
                    tiles.append((i, j))
        return tiles

    def chainable(self, tile):
        # type: (Tile) -> bool

        openings = self.openings_count(tile)
        return openings < 3 and openings != 0

    def calculate_chains(self):
        # type: () -> int

        tiles = self.chainable_tiles()
        flags = PseudoBoard.generate_flags()
        chains = []

        for tile in tiles:
            (x, y) = tile
            flags[x][y] = True

        for x in range(3):
            for y in range(3):
                tile = (x, y)

                if flags[x][y]:
                    flags[x][y] = False
                    chain = self.expand_chain(tile, flags)
                    if len(chain) >= 2:
                        chains.append(chain)

        for chain in chains:
            if self.connected(chain[0], chain[-1]):
                self.loops.append(chain)
            else:
                self.chains.append(chain)

    def expand_chain(self, start, flags):
        # type: (Tile, Flag) -> Chain

        tile = start
        chain = [start]
        neighbors = self.neighbors(tile)
        chained = True

        chainables = 0
        repeat = 1
        for neighbor in neighbors:
            if self.chainable(neighbor):
                chainables += 1

        if chainables > 1:
            repeat = 2

        for _ in range(repeat):
            while chained:
                chained = False

                for neighbor in neighbors:
                    (x, y) = neighbor
                    if not flags[x][y] or not self.connected(tile, neighbor):
                        continue

                    flags[x][y] = False
                    chained = True
                    chain.append(neighbor)

                    tile = neighbor
                    neighbors = self.neighbors(tile)

                    break

            # Case of start is not an end of the chain
            chained = True
            chain.reverse()
            tile = start
            neighbors = self.neighbors(tile)

        return chain

    def connected(self, tile1, tile2):
        # type: (Tile, Tile) -> bool

        (a, b) = tile1
        (c, d) = tile2

        diff = abs(c - a) + abs(d - b)
        if diff != 1:
            return False

        if a == c:
            if b > d:
                # b = d + 1, tile1 is rightside of tile2
                return not bool(self.col_status[a, b])
            else:
                # d = b + 1, tile1 is leftside of tile2
                return not bool(self.col_status[c, d])

        if b == d:
            if a > c:
                # a = c + 1, tile1 is below tile2
                return not bool(self.row_status[a, b])
            else:
                # c = a + 1, tile1 is above tile2
                return not bool(self.row_status[c, d])

    def get_chains(self):
        # type: () -> Chains

        if self.dirty:
            self.calculate_chains()

        return self.chains

    def get_loops(self):
        # type: () -> Loops

        if self.dirty:
            self.calculate_chains()

        return self.loops

    def openings_count(self, tile):
        # type: (Tile) -> int

        (x, y) = tile
        closings = self.row_status[x, y] + \
            self.row_status[x + 1, y] + \
            self.col_status[x, y] + \
            self.col_status[x, y + 1]

        return 4 - closings

    @staticmethod
    def generate_flags():
        # type: () -> Flag

        return [
            [False for _ in range(3)]
            for _ in range(3)
        ]

    @staticmethod
    def neighbors(tile):
        # type: (Tile) -> Tiles

        (x, y) = tile
        neighbors = []

        if x != 0:
            neighbors.append((x - 1, y))
        if x != 2:
            neighbors.append((x + 1, y))
        if y != 0:
            neighbors.append((x, y - 1))
        if y != 2:
            neighbors.append((x, y + 1))

        return neighbors


def h_line(cond):
    return "---" if cond else "   "


def v_line(cond):
    return "|" if cond else " "


def player_mark(player):
    return " " if player is None else str(player)


if __name__ == "__main__":
    board_status = np.zeros(
        shape=(3, 3))
    row_status = np.zeros(shape=(4, 3))
    col_status = np.zeros(shape=(3, 4))

    row_status[0, 0] = 1
    row_status[0, 1] = 1
    row_status[0, 2] = 1

    row_status[1, 0] = 1
    row_status[1, 1] = 1
    row_status[1, 2] = 1

    row_status[3, 0] = 1
    row_status[3, 2] = 1

    col_status[1, 0] = 1
    col_status[2, 1] = 1
    col_status[1, 2] = 1
    col_status[2, 2] = 1

    state = GameState(
        board_status,
        row_status,
        col_status,
        True
    )

    board = PseudoBoard.of(state)
    board.calculate_chains()

    print()
