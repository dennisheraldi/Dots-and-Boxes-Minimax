"""MiniMax Agent definitions."""
import math
from time import time

from agent import Agent
from Bot import Bot
from datatypes import Eval, Move
from GameAction import GameAction
from GameState import GameState
from logger import LOGGER
from player import Player
from pseudoboard import PseudoBoard
from util import unreachable

MAX = math.inf
MIN = -math.inf


class MinimaxAgent(Agent):
    """MiniMax agent class definition."""

    def __init__(self, state: GameState, randomize=False, use_eval=True):
        """Initialize the agent.

        Args:
            state (GameState): The initial state of the game.
            randomize (bool, optional): Randomize the neighbor.
                Defaults to False.
            use_eval (bool, optional): Use heuristics to eval.
                Defaults to True.
        """
        super().__init__()
        self.board = PseudoBoard(state)
        self.player: Player = Player.of(state.player1_turn)
        self.randomize = randomize
        self.use_eval = use_eval

    def minimax(
        self,
        board: PseudoBoard,
        alpha: float,
        beta: float,
        depth: int,
        is_max=True,
    ) -> Eval:
        """Recursive MiniMax algorithm.

        Args:
            board (PseudoBoard): The current board.
            alpha (float): The alpha value.
            beta (float): The beta value.
            depth (int): The current depth.
            is_max (bool, optional): Is maximize player. Defaults to True.

        Returns:
            Eval: The best move and its score.
        """
        self.evaluated += 1
        # Guard
        if self.player != board.player:
            if is_max:
                unreachable('Agent should not call max for opponent.')
        elif not is_max:
            unreachable('Agent should not call min for self.')

        # Is leaf or depth exceeded
        if board.ended() or depth == self.max_depth:
            return Eval(
                move=None,
                score=board.objective(self.player, self.use_eval),
            )

        # Initial values
        action: Move = None
        curr_val = MIN if is_max else MAX

        # Iterate over all possible moves
        for (orientation, position) in board.available_moves(self.randomize):
            # Move
            if self.timeout:
                break

            # Save current player and generate new state based on selected move
            past_player = board.player
            board.play(orientation, position)

            # Do minimax over the child with increased depth
            cond_max = past_player == board.player and is_max
            _, node_val = self.minimax(
                board,
                alpha,
                beta,
                depth + 1,
                cond_max or (not is_max and past_player != board.player),
            )
            # Revert board
            board.revert()

            # Update action based on generated val and current v
            if is_max:
                if node_val > curr_val:
                    action = Move(orientation, position)
                    curr_val = node_val
                alpha = max(curr_val, alpha)
            else:
                if node_val < curr_val:
                    action = Move(orientation, position)
                    curr_val = node_val
                beta = min(curr_val, beta)

            # Alpha beta pruning
            if beta <= alpha:
                break
        return Eval(move=action, score=curr_val)

    def _search(self) -> Eval:
        """Search for the best move.

        Returns:
            Eval: The best move and its score.
        """
        self.evaluated = 0

        moves = len(self.board.available_moves())
        if moves > 18:
            self.max_depth = 4
        elif moves > 14:
            self.max_depth = 5
        elif moves > 10:
            self.max_depth = 6
        else:
            self.max_depth = 8

        res = self.minimax(self.board, MIN, MAX, 0)
        LOGGER.debug(f'Evaluated {self.evaluated} states')
        return res


class MinimaxBot(Bot):
    """Minimax bot class definition."""

    def __init__(self, randomize=False, use_eval=True):
        """Initialize a minimax bot.

        Args:
            randomize (bool, optional): Randomize neighbor choice.
                Defaults to False.
            use_eval (bool, optional): Use heurisitics to evaluate.
                Defaults to True.
        """
        self.randomize = randomize
        self.use_eval = use_eval

    def get_action(self, state: GameState) -> GameAction:
        """Get the next action for minimax bot.

        Args:
            state (GameState): The current state of the game.

        Returns:
            GameAction: The next action.
        """
        start = time()
        agent = MinimaxAgent(state, self.randomize)
        move, evaluate = agent.search()
        dur = round(time() - start, 2)
        LOGGER.debug(f'Best move: {move}. Eval: {evaluate}')
        LOGGER.perf(f'Thinking time: {dur}s')
        return GameAction(move[0], move[1])
