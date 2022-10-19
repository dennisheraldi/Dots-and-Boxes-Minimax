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
    """Local search agent class definition"""
    board: PseudoBoard
    turn: Player

    evaluated: int
    use_eval: bool

    def __init__(self, state: GameState, turn: Player, use_eval=True):
        """Initialize the agent

        Args:
            state (GameState): The initial state of the game
            turn (Player): Get the turn of player
            use_eval (bool, optional): Use heuristics to eval. Defaults to True.
        """
        self.board = PseudoBoard(state)
        self.turn = turn
        self.use_eval = use_eval

    def _search(self) -> Eval:
        """Search for the best move

        Returns:
            Eval: The best move and its score. 
        """
        best_eval = -99
        move: Move = None

        for (orientation, position) in self.board.available_moves():
            if self.timeout:
                break

            self.board.play(orientation, position)

            eval = self.board.objective(self.turn, self.use_eval)
            if eval  > best_eval:
                best_eval = eval
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

        return Eval(move, best_eval)


class LocalSearchBot(Bot):
    """Local Search Bot class definition"""
    use_eval: bool

    def __init__(self, use_eval=True):
        """Initialize local search bot 

        Args:
            use_eval (bool, optional): Use heuristics to eval. Defaults to True.
        """
        # type: (bool, bool) -> None
        self.use_eval = use_eval

    def get_action(self, state):
        """Get action of game state

        Args:
            state (_type_): State of the game

        Returns:
            _type_: Game action 
        """
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
