"""PseudoBoard class definition and helper."""
from random import shuffle
from typing import List

from numpy import ndarray

from datatypes import (Chain, Chains, Flag, Flags, Loops, Move, Moves,
                       Orientation, Position, Square, Tile, Tiles)
from GameState import GameState
from player import Player


class PseudoBoard(object):
    """
    A class to represent board from game state.

    It will be used to calculate heuristics, utility, neighbors, etc.

    Example of game state
        A board of this configuration:
            ----xxxxx----
            |   |   Y   |
            ----YYYYY----
            |   |   |   Y
            ----XXXXX----
            |   Y   Y   |
            XXXXXXXXX----

        would produce row status:
            0 1 0
            0 1 0
            0 1 0
            1 1 0

        and col status:
            0 0 1 0
            0 0 0 1
            0 1 1 0
    """

    def __init__(self, state: GameState):
        """Generate new board from game state.

        Args:
            state (GameState): Game state to infer board from.
        """
        self.state = state
        self.player1_turn = state.player1_turn
        self._loops: Loops = []
        self._chains: Chains = []
        self.dirty = True
        self.chain_part: Flag = [False for _ in range(9)]
        self.move_stack: Moves = []
        self.square_stack: List[Square] = []

    def __str__(self) -> str:
        """Return a string representation of the board.

        Returns:
            str: String representation of the board.
        """
        rep = ''
        for i in range(4):
            for j in range(3):
                rep += f'+{h_line(self.state.row_status[i, j])}'
            rep += '+\n'

            if i < 3:
                for k in range(4):
                    rep += f'{v_line(self.state.col_status[i, k])} '
                    if k < 3:
                        player = Player.of(self.state.board_status[i, k])
                        rep += f'{player_mark(player)} '
                rep = rep[:-1] + '\n'
        rep += f'Player {self.player} to play'
        return rep

    def play(
        self,
        orientation: Orientation,
        position: Position,
    ):
        """Update PseudoBoard after playing a move.

        Args:
            orientation (Orientation): Orientation of the move.
            position (Position): Position of the move.
        """
        # Add this action to the move stack
        self.move_stack.append(Move(orientation, position))
        # Toggle status to one on that orientation and pos
        self.state.status(orientation)[position] = 1
        # Get player and square stack with this player
        player = self.player
        square = Square([], player)
        should_switch: bool = True
        # For both side of row/col (two tiles)
        for _ in range(2):
            # If the tile is creating a square,
            # Append it to square stack and don't switch player
            # (player can continue)
            if is_valid_tile(position):
                if self.openings_count(position) == 0:
                    self.state.board_status[position] = player.score()
                    square.tiles.append(position)
                    should_switch = False
            # Get next tile
            if orientation == 'row':
                position = (position[0] - 1, position[1])
            else:
                position = (position[0], position[1] - 1)
        # Add the square to the square stack and player to turn stack
        self.square_stack.append(square)
        # Switch player if should
        if should_switch:
            self.switch()
        # Set dirty after move
        self.dirty = True

    def revert(self):
        """Revert the last move."""
        # Pop last move, toggle back to 0 that orientation and pos
        (orientation, position) = self.move_stack.pop()
        self.state.status(orientation)[position] = 0

        # Pop last square, reset board state or switch player
        (positions, _) = self.square_stack.pop()
        if positions:  # Square created, revert all board state
            for pos in positions:
                self.state.board_status[pos] = 0
        else:  # No square created, switch player
            self.switch()

    def ended(self) -> bool:
        """Check if the game has ended.

        Returns:
            bool: True if the game has ended, False otherwise.
        """
        return not self.available_moves()

    def switch(self):
        """Switch player to play."""
        self.player1_turn = not self.player1_turn

    def objective(self, player: Player, use_eval=False) -> int:
        """Calculate objective value of the board for a player.

        If use_eval is True, will also use heuristics.

        Args:
            player (Player): Player to calculate objective value for.
            use_eval (bool, optional): Use heuristics. Defaults to False.

        Returns:
            int: Objective value of the board for a player.
        """
        return self.eval(player) if use_eval else self.utility(player)

    def eval(self, player: Player) -> int:
        """Calculate value of the board for a player.

        This function will use utility + heuristics
        Heuristics: factor * (chains + free square + loops)
        where factor is 1 if current player is evaluated player, -1 otherwise

        Args:
            player (Player): Player to calculate value for.

        Returns:
            int: Value of the board for a player.
        """
        factor = 1 if self.player == player else -1
        return self.utility(player) + (
            self.chain_value() + self.free_squares() + self.loop_value()
        ) * factor

    def utility(self, player: Player) -> int:
        """Calculate utility value of the board for a player.

        Utility: player squares - opponent squares

        Args:
            player (Player): Player to calculate utility value for.

        Returns:
            int: Utility value of the board for a player.
        """
        return self.squares(player) - self.squares(player.opponent())

    def free_squares(self) -> int:
        """Calculate number of free squares.

        Free square defined as a square that have 1 row/col left (open)
        and not being part of any chain

        e.g.
            +EEE+
            E   O
            +---+

        Returns:
            int: _description_
        """
        sq = 0
        for x in range(3):
            for y in range(3):
                if self.openings_count((x, y)) == 1:
                    if not self.chain_part[3 * x + y]:
                        sq += 1
        return sq

    def chain_value(self) -> int:
        """Calculate total value of all chains.

        Each chain will be calculated differently.

        There are 4 types of chains:
            oscs = open short chains
            olcs = open long chains
            hocs = half open chains
            nolcs = non-open long chains

        Returns:
            int: Total value of all chains.
        """
        noscs = oscs = hoscs = nolcs = 0
        olcs = len_olcs = len_hoscs = nolcs = 0
        for chain in self.chains:
            end1 = chain[0]
            end2 = chain[-1]
            a = self.openings_count(end1)
            b = self.openings_count(end2)
            length = len(chain)
            if length == 2:
                if a == 2 and b == 2:
                    # Open short chain
                    oscs += length
                elif a == 2 or b == 2:
                    hoscs += length
                    len_hoscs += 1
                else:
                    noscs += length
            else:
                if a == 2 and b == 2:
                    # Open long chain
                    olcs += length
                    len_olcs += 1
                else:
                    nolcs += length

        fac = -1 ** len_hoscs
        if len_olcs == 0:
            ov = 0
        else:
            ov = olcs - 4 * len_olcs + 4

        return noscs + hoscs - oscs + nolcs - ov * fac

    def loop_value(self) -> int:
        """Calculate how much chains are there in every loop.

        Returns:
            int: Negative value of total chains in every loop.
        """
        if self.dirty:
            self.calculate_chains()
        return -sum([len(loop) for loop in self.loops])

    def squares(self, player: Player) -> int:
        """Calculate number of squares for a player.

        Args:
            player (Player): Player to calculate number of squares for.

        Returns:
            int: Number of squares for the player.
        """
        res: ndarray = (self.state.board_status == player.score())
        return res.sum()

    def available_moves(self, randomize=False) -> Moves:
        """Get all available moves.

        Args:
            randomize (bool, optional): Randomize move to select.
                Defaults to False.

        Returns:
            Moves: List of available moves.
        """
        moves: Moves = []
        size = [4, 3]
        for orient in ('row', 'col'):
            for x in range(size[0]):
                for y in range(size[1]):
                    if not self.state.status(orient)[x, y]:
                        moves.append(Move(orient, (x, y)))
            size.reverse()
        # If randomize, shuffle moves
        if randomize:
            shuffle(moves)
        return moves

    def chainable(self, tile: Tile) -> bool:
        """Check if a tile is chainable.

        Tile is chainable if it has 1 or 2 row/col opens

        e.g.
             +---+ or +OOO+ or +EEE+ etc
             E   O    E   |    |   |
             +EEE+    +---+    +OOO+
        open:  1        2        2

        Args:
            tile (Tile): Tile to check.

        Returns:
            bool: True if tile is chainable, False otherwise.
        """
        openings = self.openings_count(tile)
        return openings < 3 and openings != 0

    def calculate_chains(self):
        """Calculate chains in the board."""
        self.chain_part = [False for _ in range(9)]
        self._chains = []
        self._loops = []
        flags: Flags = [
            [self.chainable((i, j)) for j in range(3)]
            for i in range(3)
        ]
        # For each tiles
        for x in range(3):
            for y in range(3):
                # If tile is chainable:
                # Toggle chainable flag to false (it will not be used
                # to expand chain), then expand chain for tile
                if flags[x][y]:
                    flags[x][y] = False
                    chain = self.expand_chain((x, y), flags)
                    # If tile can be chained with 2 or more tiles,
                    # flag all of them as a chain part
                    if len(chain) >= 2:
                        for (i, j) in chain:
                            self.chain_part[3 * i + j] = True
                        # If chain length is >= 4 and first tile and last
                        #   tile of the chain is connected, add it to loop
                        # else, add it to chain
                        if (
                            len(chain) >= 4 and
                            self.connected(chain[0], chain[-1])
                        ):
                            self._loops.append(chain)
                        else:
                            self._chains.append(chain)
        # We precalculated it, so it's not dirty anymore
        self.dirty = False

    def expand_chain(self, start: Tile, flags: Flags) -> Chain:
        """Expand chain from a tile.

        Args:
            start (Tile): Tile to start expanding chain from.
            flags (Flags): Flags to check if a tile is chainable
                or can be used to chain (not used by another chain).

        Returns:
            Chain: List of tiles in the chain.
        """
        # Expand a chainable `start` tile to form a chain of tiles
        tile = start
        chain = [start]
        neighbors = get_neighbors(tile)
        chained = True
        # We count for chainable neighbor (with max of 2)
        chainables = 0
        for nbor in neighbors:
            if self.chainable(nbor):
                chainables += 1
                if chainables > 1:
                    break
        # For each chainables attempt
        for _ in range(chainables):
            while chained:
                chained = False
                # For each neighbor
                for neighbor in neighbors:
                    (x, y) = neighbor
                    # if neighbor is already chained, or neighbor is not
                    # connected to current tile, or not chainable, skip
                    if (
                        not flags[x][y] or
                        not self.connected(tile, neighbor) or
                        not self.chainable(neighbor)
                    ):
                        continue
                    # Neighbor can be chained!
                    # toggle neighbor flag to false (already chained),
                    # toggle chained, and add neighbor to chain list
                    flags[x][y] = False
                    chained = True
                    chain.append(neighbor)
                    # Continue to expand chain with current tile = neighbor,
                    # get its neighbors, and skip other neighbors
                    tile = neighbor
                    neighbors = get_neighbors(tile)
                    break
            # Case of start is not an end of the chain, not making a loop:
            # we can chain start tile with its other neighbor
            # (remember, flag is already toggled to false if already used
            #  to chain, so we can't use it again)
            chained = True
            chain.reverse()
            tile = start
            neighbors = get_neighbors(tile)
        return chain

    def connected(self, tile1: Tile, tile2: Tile) -> bool:
        """Check if 2 tiles are connected.

        Two different tiles is connected if they has common open row/col.
        e.g.
            +EEE+EEE+ or +OOO+   BUT NOT   +OOO+EEE+ or +EEE+
            O   |   O    E   |             E   E   |    |   |
            +OOO+---+    +---+ < con-      +---+---+    +OOO+ < not connected
                ^        |   E   nected        ^ not    |   O
            connected    +OOO+             connected    +---+


        Args:
            tile1 (Tile): First tile.
            tile2 (Tile): Second tile.

        Returns:
            bool: True if 2 tiles are connected, False otherwise.
        """
        (a, b) = tile1
        (c, d) = tile2
        diff = abs(c - a) + abs(d - b)
        if diff != 1:
            return False
        if a == c:
            if b > d:
                # b = d + 1, tile1 is rightside of tile2
                return not bool(self.state.col_status[a, b])
            # d = b + 1, tile1 is leftside of tile2
            return not bool(self.state.col_status[c, d])
        if b == d:
            if a > c:
                # a = c + 1, tile1 is below tile2
                return not bool(self.state.row_status[a, b])
            # c = a + 1, tile1 is above tile2
            return not bool(self.state.row_status[c, d])

    def openings_count(self, tile: Tile) -> int:
        """Count number of openings in a tile.

        Args:
            tile (Tile): Tile to count openings.

        Returns:
            int: Number of openings in a tile.
        """
        # Destruct the tile tuple into x and y
        (x, y) = tile
        # Count the closing in that tile (row/col that has checked in the tile)
        # Opening count will be 4 - closing count
        closings = sum([
            self.state.row_status[x, y],
            self.state.row_status[x + 1, y],
            self.state.col_status[x, y],
            self.state.col_status[x, y + 1],
        ])
        return 4 - closings

    @property
    def player(self) -> Player:
        """Get current player.

        Returns:
            Player: Current player.
        """
        return Player.of(self.player1_turn)

    @property
    def chains(self) -> Chains:
        """Get chains in the board.

        Returns:
            Chains: List of chains in the board.
        """
        if self.dirty:
            self.calculate_chains()
        return self._chains

    @property
    def loops(self) -> Loops:
        """Get loops in the board.

        Returns:
            Loops: List of loops in the board.
        """
        if self.dirty:
            self.calculate_chains()
        return self._loops


def get_neighbors(tile: Tile) -> Tiles:
    """Get neighbors of a tile.

    Args:
        tile (Tile): Tile to get neighbors.

    Returns:
        Tiles: List of neighbors of a tile.
    """
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


def is_valid_tile(tile: Tile) -> bool:
    """Check if a tile is valid.

    Args:
        tile (Tile): Tile to check.

    Returns:
        bool: True if tile is valid, False otherwise.
    """
    (x, y) = tile
    return 0 <= x < 3 and 0 <= y < 3


def h_line(cond: bool) -> str:
    """Return horizontal line.

    Args:
        cond (bool): Condition to draw horizontal line.

    Returns:
        str: Horizontal line.
    """
    return '---' if cond else '   '


def v_line(cond: bool) -> str:
    """Return vertical line.

    Args:
        cond (bool): True if line is closed, False otherwise.

    Returns:
        str: Vertical line.
    """
    return '|' if cond else ' '


def player_mark(player: Player) -> str:
    """Return player mark.

    Args:
        player (Player): Player to get mark.

    Returns:
        str: Player mark.
    """
    return ' ' if player is None else str(player)
