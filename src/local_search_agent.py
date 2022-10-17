from random import randint
from time import time

from agent import Agent
from Bot import Bot
from datatypes import Eval, Move
from GameAction import GameAction
from GameState import GameState
from logger import LOGGER
from player import Player
from pseudoboard import PseudoBoard


class LocalSearchAgent(Agent):
    board: PseudoBoard
    turn: Player

    evaluated: int
    use_eval: bool

    def __init__(self, state: GameState, turn: Player, use_eval=True):
        self.board = PseudoBoard(state)
        self.turn = turn
        self.use_eval = use_eval

    def search(self) -> Eval:
        best_eval = -99
        move: Move = None

        # Store possible moves info
        possible_move = self.board.available_moves()

        # Iterate 70% of the possible moves
        for _ in range(int(0.7 * len(possible_move)) - 1):
            # Get random next move
            (orientation, position) = possible_move[
                randint(0, len(possible_move) - 1)
            ]

            # Delete the selected move from the list
            possible_move = tuple(
                mov
                for mov in possible_move
                if mov != Move(orientation, position)
            )

            # Move to the state of selected move
            self.board.play(orientation, position)

            # Evaluate the state
            _eval = self.board.objective(self.turn, self.use_eval)
            if _eval > best_eval:
                best_eval = _eval
                move = Move(orientation, position)

            self.board.revert()

        for (orientation, position) in self.board.available_moves(True):
            self.board.play(orientation, position)

            _eval = self.board.objective(self.turn, self.use_eval)
            if _eval > best_eval:
                best_eval = _eval
                move = Move(orientation, position)

            self.board.revert()

        if LOGGER.is_debug() and LOGGER.is_verbose():
            self.board.play(move[0], move[1])
            LOGGER.debug(
                f'Free squares: {self.board.free_squares()}',
                verbose=True,
            )
            LOGGER.debug(
                f'Chains: {len(self.board.chains)}',
                verbose=True,
            )
            LOGGER.debug(
                f'Loops: {len(self.board.loops)}',
                verbose=True,
            )
            self.board.revert()

        move = Move(move.orientation, move.position[::-1])
        return Eval(move, best_eval)


class LocalSearchBot(Bot):

    use_eval: bool

    def __init__(self, use_eval=True):
        # type: (bool, bool) -> None
        self.use_eval = use_eval

    def get_action(self, state):
        # type: (GameState) -> GameAction

        start = time()

        if state.player1_turn:
            turn = Player.odd
        else:
            turn = Player.even

        agent = LocalSearchAgent(state, turn, self.use_eval)
        move, val_node = agent.search()

        dur = round(time() - start, 2)
        LOGGER.debug(f'Best move: {move}. Eval: {val_node}')
        LOGGER.perf(f'Thinking time: {dur}s')

        return GameAction(move.orientation, move.position)
