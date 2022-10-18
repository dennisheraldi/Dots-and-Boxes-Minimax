"""Custom data types for the application."""
from typing import List, Literal, NamedTuple, Tuple

from player import Player

Orientation = Literal['row', 'col']
Tile = Tuple[int, int]
Tiles = List[Tile]


class Position(NamedTuple):
    """Position for row and col."""

    row: int
    col: int


class Move(NamedTuple):
    """Move definition for the game."""

    orientation: Orientation
    position: Position


class Square(NamedTuple):
    """Square definition for the game."""

    tiles: Tiles
    player: Player


class Eval(NamedTuple):
    """Evaluation result for the game."""

    move: Move
    score: int


Flag = List[bool]
Flags = List[List[bool]]
Chain = List[Tile]
Chains = List[Chain]
Loops = List[Chain]
Moves = List[Move]
