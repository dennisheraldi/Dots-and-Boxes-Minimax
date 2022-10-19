"""Local search agent definition."""
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
    """Local search agent class definition."""

    def __init__(self, state: GameState, turn: Player, use_eval=True):
        """Initialize the agent.

        Args:
            state (GameState): The initial state of the game.
            turn (Player): Get the turn of player.
            use_eval (bool, optional): Use heuristics to eval.
                Defaults to True.
        """
        self.board = PseudoBoard(state)
        self.turn = turn
        self.use_eval = use_eval

    def _search(self) -> Eval:
        """Search for the best move.

        Returns:
            Eval: The best move and its score.
        """
        best_eval = -99
        move: Move = None
        
        # Store possible moves info
        possible_move = self.board.available_moves()

        # Iterate over possible moves 
        for _ in range(len(possible_move)):
            # Get random next move
            (orientation, position) = possible_move[randint(0, len(possible_move)-1)]

            # Delete the selected move from the list
            possible_move = tuple(x for x in possible_move if x != (orientation, position))

            # Move to the state of selected move
            self.board.play(orientation, position)

            evl = self.board.objective(self.turn, self.use_eval)
            if evl > best_eval:
                best_eval = evl
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
    """Local Search Bot class definition."""

    use_eval: bool

    def __init__(self, use_eval=True):
        """Initialize local search bot.

        Args:
            use_eval (bool, optional): Use heuristics to
                evaluate board. Defaults to True.
        """
        self.use_eval = use_eval

    def get_action(self, state: GameState) -> GameAction:
        """Get action of game state.

        Args:
            state (GameState): State of the game

        Returns:
            GameAction: Game action
        """
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
