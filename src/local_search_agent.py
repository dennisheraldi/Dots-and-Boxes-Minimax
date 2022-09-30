from time import time
from typing import Tuple
from Bot import Bot
from pseudoboard import PseudoBoard, Move
from GameState import GameState
from GameAction import GameAction
from player import Player
from util import DEBUG, LOG_TIME, VERBOSE


class LocalSearchAgent:
    board: PseudoBoard
    turn: Player

    max_depth: int

    evaluated: int

    def __init__(self, state, turn):
        # type: (GameState, Player) -> None

        self.board = PseudoBoard.of(state)
        self.turn = turn

    def search(self):
        # type: () -> Tuple[Move, int]

        best_eval = -9
        move = None

        for (orientation, position) in self.board.available_moves():
            self.board.play(orientation, position)

            _eval = self.board.eval(self.turn)
            if _eval > best_eval:
                best_eval = _eval
                move = (orientation, position)

            self.board.revert()

        if DEBUG and VERBOSE:
            self.board.play(move[0], move[1])
            print(f"Free squares: {self.board.free_squares()}")
            print(f"Chains: {len(self.board.get_chains())}")
            print(f"Loops: {len(self.board.get_loops())}")
            self.board.revert()

        return (move, best_eval)


class LocalSearchBot(Bot):

    def get_action(self, state):
        # type: (GameState) -> GameAction

        start = 0
        if LOG_TIME:
            start = time()

        if state.player1_turn:
            turn = Player.ODD
        else:
            turn = Player.EVEN

        agent = LocalSearchAgent(state, turn)
        move, val = agent.search()

        if DEBUG:
            print(f"Best move: {move}. Eval: {val}")

        if LOG_TIME:
            print(f"Thinking time: {round(time() - start, 2)}s")

        return GameAction(move[0], (move[1][1], move[1][0]))
