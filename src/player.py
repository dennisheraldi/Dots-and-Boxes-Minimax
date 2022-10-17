from enum import Enum


class Player(Enum):
    odd = 0
    even = 1

    @staticmethod
    def of(player_val):
        match player_val:
            case True: return Player.odd
            case False: return Player.even
            case -4: return Player.odd
            case 4: return Player.even
            case _: return None

    def score(self):
        match self:
            case Player.odd: return -4
            case Player.even: return 4

    def opponent(self):
        match self:
            case Player.odd: return Player.even
            case Player.even: return Player.odd

    def __str__(self):
        match self:
            case Player.odd: return 'O'
            case Player.even: return 'E'
