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
DEPTH = 8


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
        self.board = PseudoBoard(state)
        self.player: Player = Player.of(state.player1_turn)
        self.randomize = randomize
        self.use_eval = use_eval

    def search(self, max_depth: int) -> Eval:
        """Search for the best move.

        Args:
            max_depth (int): The maximum depth to search.

        Returns:
            Eval: The best move and its score.
        """
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

        res = self.minimax(self.board, MIN, MAX, 0)
        LOGGER.debug(f'Evaluated {self.evaluated} states')
        return res

    def minimax(
        self,
        board: PseudoBoard,
        alpha: float,
        beta: float,
        depth: int,
        is_max: bool = True,
    ) -> Eval:
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
        action = Move(action.orientation, action.position[::-1])
        return Eval(move=action, score=curr_val)


class MinimaxBot(Bot):
    def __init__(self, randomize=False, use_eval=True):
        self.randomize = randomize
        self.use_eval = use_eval

    def get_action(self, state: GameState) -> GameAction:
        start = time()
        agent = MinimaxAgent(state, self.randomize)
        move, evaluate = agent.search(DEPTH)
        dur = round(time() - start, 2)
        LOGGER.debug(f'Best move: {move}. Eval: {evaluate}')
        LOGGER.perf(f'Thinking time: {dur}s')
        return GameAction(move[0], move[1])
