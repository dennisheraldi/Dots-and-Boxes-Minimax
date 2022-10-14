from random import shuffle
from typing import Literal, Tuple
import numpy as np
from GameState import GameState
from player import Player
from tile import Tile, Tiles
from util import DEBUG, VERBOSE

Flag = list[list[bool]]
Chain = list[Tile]
Chains = list[Chain]
Loops = list[Chain]

Orientation = Literal["row", "col"]
Position = Tuple[int, int]
Move = Tuple[Orientation, Position]
Moves = list[Move]


class PseudoBoard:

    loops: list[list[Tile]]
    chains: list[list[Tile]]
    dirty: bool
    chain_part: list[bool]

    move_stack: Moves
    square_stack: list[Tuple[list[Position], Player]]
    turn_stack: list[Player]

    board_status: list[list[int]]
    row_status: list[list[int]]
    col_status: list[list[int]]
    player1_turn: bool

    def __init__(self, board_status, row_status, col_status, player1_turn):
        self.board_status = board_status
        self.row_status = row_status
        self.col_status = col_status
        self.player1_turn = player1_turn

        self.loops = []
        self.chains = []
        self.dirty = True
        self.chain_part = [False for _ in range(9)]

        self.move_stack = []
        self.square_stack = []
        self.turn_stack = []

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

    @staticmethod
    def of(state):
        # type: (GameState) -> PseudoBoard

        return PseudoBoard(
            state.board_status,
            state.row_status,
            state.col_status,
            state.player1_turn
        )

    def play(self, orientation, position):
        # type: (Orientation, Position) -> PseudoBoard

        self.move_stack.append((orientation, position))

        tile1 = position

        if orientation == "row":
            self.row_status[position] = 1
            tile2 = (position[0] - 1, position[1])
        else:
            self.col_status[position] = 1
            tile2 = (position[0], position[1] - 1)

        player = self.player_to_play()
        square = ([], player)
        should_switch = True
        if PseudoBoard.valid_tile(tile1) and self.openings_count(tile1) == 0:
            self.board_status[tile1] = player.score()
            square[0].append(tile1)
            should_switch = False
        if PseudoBoard.valid_tile(tile2) and self.openings_count(tile2) == 0:
            self.board_status[tile2] = player.score()
            square[0].append(tile2)
            should_switch = False

        self.square_stack.append(square)
        self.turn_stack.append(player)

        if should_switch:
            self.switch()

        self.dirty = True

        return self

    def revert(self):
        # type: () -> PseudoBoard

        (orientation, position) = self.move_stack.pop()

        if orientation == "row":
            self.row_status[position] = 0
        else:
            self.col_status[position] = 0

        (positions, _) = self.square_stack.pop()
        for position in positions:
            self.board_status[position] = 0

        if len(positions) == 0:
            self.switch()

        self.turn_stack.pop()

        return self

    def ended(self):
        # type: () -> bool

        return len(self.available_moves()) == 0

    def switch(self):
        # type: () -> None

        self.player1_turn = not self.player1_turn

    def objective(self, player, use_eval=False):
        # type: (Player, bool) -> int
        return self.eval(player) if use_eval else self.utility(player)

    def eval(self, player):
        # type: (Player) -> int

        # !! Too slow for python
        factor = 1 if self.player_to_play() == player else -1
        return self.squares(player) - self.squares(player.opponent()) + (
            self.chain_value() + self.free_squares() + self.loop_value()
        ) * factor

    def utility(self, player):
        # type: (Player) -> int

        return self.squares(player) - self.squares(player.opponent())

    def free_squares(self):
        # type: () -> int

        sq = 0
        for x in range(3):
            for y in range(3):
                if self.openings_count((x, y)) == 1 and not self.chain_part[3 * x + y]:
                    sq += 1

        return sq

    def chain_value(self):
        # type: () -> int

        if self.dirty:
            self.calculate_chains()

        noscs = []
        oscs = []
        hoscs = []
        nolcs = []
        olcs = []

        for chain in self.chains:
            end1 = chain[0]
            end2 = chain[-1]

            a = self.openings_count(end1)
            b = self.openings_count(end2)
            length = len(chain)

            if length == 2:
                if a == 2 and b == 2:
                    # Open short chain
                    oscs.append(length)
                elif a == 2 or b == 2:
                    hoscs.append(length)
                else:
                    noscs.append(length)
            else:
                if a == 2 and b == 2:
                    # Open long chain
                    olcs.append(length)
                else:
                    nolcs.append(length)

        fac = -1 ** len(hoscs)

        if len(olcs) == 0:
            ov = 0
        else:
            ov = sum(olcs) - 4 * len(olcs) + 4

        return sum(noscs) + sum(hoscs) - sum(oscs) + sum(nolcs) - ov * fac

    def loop_value(self):
        # type: () -> int

        if self.dirty:
            self.calculate_chains()

        v = 0
        for loop in self.loops:
            v -= len(loop)

        return v

    def squares(self, player):
        # type: (Player) -> int

        squares = 0

        for x in range(3):
            for y in range(3):
                if self.board_status[x, y] == player.score():
                    squares += 1

        return squares

    def available_moves(self, randomize=False):
        # type: (bool) -> Moves

        moves = []

        for x in range(4):
            for y in range(3):
                if not self.row_status[x, y]:
                    moves.append(("row", (x, y)))

        for x in range(3):
            for y in range(4):
                if not self.col_status[x, y]:
                    moves.append(("col", (x, y)))

        if randomize:
            shuffle(moves)

        return moves

    def player_to_play(self):
        # type: () -> Player

        if self.player1_turn:
            return Player.ODD
        else:
            return Player.EVEN

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

        self.chains = []
        self.chain_part = [False for _ in range(9)]
        self.loops = []

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
                        for tile in chain:
                            (x, y) = tile
                            self.chain_part[3 * x + y] = True
                        chains.append(chain)

        for chain in chains:
            if len(chain) >= 4 and self.connected(chain[0], chain[-1]):
                self.loops.append(chain)
            else:
                self.chains.append(chain)

        self.dirty = False

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

        if chainables == 0:
            return []

        if chainables > 1:
            repeat = 2

        for _ in range(repeat):
            while chained:
                chained = False

                for neighbor in neighbors:
                    (x, y) = neighbor
                    if not flags[x][y] or \
                            not self.connected(tile, neighbor) or \
                            not self.chainable(neighbor):
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

    @staticmethod
    def valid_tile(tile):
        # type: (Tile) -> bool

        (x, y) = tile

        return 0 <= x < 3 and 0 <= y < 3


def h_line(cond):
    return "---" if cond else "   "


def v_line(cond):
    return "|" if cond else " "


def player_mark(player):
    return " " if player is None else str(player)
