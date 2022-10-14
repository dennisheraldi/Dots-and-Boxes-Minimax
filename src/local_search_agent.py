from time import time
from typing import Tuple
from Bot import Bot
from pseudoboard import PseudoBoard, Move
from GameState import GameState
from GameAction import GameAction
from player import Player
from util import DEBUG, LOG_TIME, VERBOSE
from logger import LOGGER

class LocalSearchAgent:
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

    def search(self):
        # type: () -> Tuple[Move, int]

        best_eval = -99
        move = None

        for (orientation, position) in self.board.available_moves(self.randomize):
            self.board.play(orientation, position)

            _eval = self.board.objective(self.turn, self.use_eval)
            if _eval > best_eval:
                best_eval = _eval
                move = (orientation, position)

            self.board.revert()

        if LOGGER.is_debug() and LOGGER.is_verbose():
            self.board.play(move[0], move[1])
            LOGGER.debug(f"Free squares: {self.board.free_squares()}", verbose=True)
            LOGGER.debug(f"Chains: {len(self.board.get_chains())}", verbose=True)
            LOGGER.debug(f"Loops: {len(self.board.get_loops())}", verbose=True)
            self.board.revert()

        return move, best_eval


class LocalSearchBot(Bot):

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

        agent = LocalSearchAgent(state, turn, self.randomize, self.use_eval)
        move, val = agent.search()

        LOGGER.debug(f"Best move: {move}. Eval: {val}")
        LOGGER.perf(f"Thinking time: {round(time() - start, 2)}s")

        return GameAction(move[0], (move[1][1], move[1][0]))
