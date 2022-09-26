from enum import Enum


class Player(Enum):
    ODD = 0
    EVEN = 1

    def of(value):
        match value:
            case -4: return Player.ODD
            case 4: return Player.EVEN
            case _: return None

    def score(self):
        match self:
            case Player.ODD: return -4
            case Player.EVEN: return 4

    def opponent(self):
        match self:
            case Player.ODD: return Player.EVEN
            case Player.EVEN: return Player.ODD

    def __str__(self):
        match self:
            case Player.ODD: return "O"
            case Player.EVEN: return "E"
