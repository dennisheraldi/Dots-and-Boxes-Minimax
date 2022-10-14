from time import time
from typing import Tuple
from Bot import Bot
from pseudoboard import PseudoBoard, Move
from GameState import GameState
from GameAction import GameAction
from player import Player
from util import DEBUG, LOG_TIME, unreachable
from logger import LOGGER
import math

MAX = math.inf
MIN = -math.inf
DEPTH = 8


class MinimaxAgent:
    board: PseudoBoard
    turn: Player

    max_depth: int
    evaluated: int
    randomize: bool
    use_eval: bool

    def __init__(self, state, turn, randomize=False, use_eval=True):
        # type: (GameState, Player, bool, bool) -> None

        self.board = PseudoBoard.of(state)
        self.turn = turn
        self.randomize = randomize
        self.use_eval = use_eval

    def search(self, max_depth):
        # type: (int) -> Tuple[Move, int]

        alpha = MIN
        beta = MAX
        self.max_depth = max_depth
        self.evaluated = 0

        moves = len(self.board.available_moves())
        if moves > 18:
            self.max_depth = 4
        elif moves > 14:
            self.max_depth = 5
        elif moves > 11:
            self.max_depth = 6
        else:
            self.max_depth = 8

        res = self._max(self.board, alpha, beta, 0)
        LOGGER.debug(f"Evaluated {self.evaluated} states")
        return res

    def _max(self, board, alpha, beta, depth):
        # type: (PseudoBoard, float, float, int) ->  Tuple[Move, int]

        self.evaluated += 1

        # Guard
        if self.turn != board.player_to_play():
            unreachable("Agent should not call _max for opponent.")

        if board.ended() or depth == self.max_depth:
            return None, board.objective(self.turn, self.use_eval)

        action = None
        v = MIN

        for (orientation, position) in board.available_moves(self.randomize):

            past_player = board.player_to_play()
            new_state = board.play(orientation, position)

            if past_player == new_state.player_to_play():
                fn = self._max
            else:
                fn = self._min

            _, val = fn(new_state, alpha, beta, depth + 1)
            board.revert()

            if val > v:
                action = (orientation, position)
                v = val

            if v >= beta:
                return (orientation, position), v

            if v > alpha:
                alpha = v

        return action, v

    def _min(self, board, alpha, beta, depth):
        # type: (PseudoBoard, float, float, int) -> Tuple[Move, int]

        self.evaluated += 1

        # Guard
        if self.turn == board.player_to_play():
            unreachable("Agent should not call _min for self.")

        if board.ended() or depth == self.max_depth:
            return None, board.objective(self.turn, self.use_eval)

        action = None
        v = MAX

        for (orientation, position) in board.available_moves(self.randomize):
            past_player = board.player_to_play()
            new_state = board.play(orientation, position)

            if past_player == new_state.player_to_play():
                fn = self._min
            else:
                fn = self._max

            _, val = fn(new_state, alpha, beta, depth + 1)
            board.revert()

            if val < v:
                action = (orientation, position)
                v = val

            if v <= alpha:
                return (orientation, position), v

            if v < beta:
                beta = v

        return action, v


class MinimaxBot(Bot):

    randomize: bool
    use_eval: bool

    def __init__(self, randomize=False, use_eval=True):
        # type: (bool, bool) -> None
        self.randomize = randomize
        self.use_eval = use_eval

    def get_action(self, state):
        # type: (GameState) -> GameAction

        start = time()

        if state.player1_turn:
            turn = Player.ODD
        else:
            turn = Player.EVEN

        agent = MinimaxAgent(state, turn, self.randomize)
        move, val = agent.search(DEPTH)

        LOGGER.debug(f"Best move: {move}. Eval: {val}")
        LOGGER.perf(f"Thinking time: {round(time() - start, 2)}s")

        return GameAction(move[0], (move[1][1], move[1][0]))
