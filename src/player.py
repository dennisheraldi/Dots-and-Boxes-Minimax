from enum import Enum


class Player(Enum):
    odd = 0
    even = 1

    @classmethod
    def of(cls, player_val):
        match player_val:
            case True: return cls.odd
            case False: return cls.even
            case -4: return cls.odd
            case 4: return cls.even
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
