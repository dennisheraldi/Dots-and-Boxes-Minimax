"""Agent abstract class."""
from threading import Timer

from datatypes import Eval, Move
from pseudoboard import PseudoBoard

THINKING_TIME = 4.9


class Agent(object):
    """An interface for agent.

    Inherit this to create your own agents.
    """

    def __init__(self):
        self.board: PseudoBoard = None

    def search(self) -> Eval:
        self.timer = Timer(THINKING_TIME, self.force_stop)
        self.timeout = False
        self.timer.start()

        rand_move = self.board.available_moves(randomize=True)[0]
        res = self._search()

        if not self.timeout:
            self.timer.cancel()
        if res is None or res.move is None:
            # return random move
            res = Eval(
                move=rand_move,
                score=0
            )

        return Eval(
            move=Move(
                orientation=res.move.orientation,
                position=res.move.position[::-1]
            ),
            score=res.score
        )

    def force_stop(self):
        self.timeout = True

    def _search(self) -> Eval:
        """Return the evaluation result of the agent.

        Evaluation result consist of move and score.

        Raises:
            NotImplementedError: If not implemented.
        """
        raise NotImplementedError()
