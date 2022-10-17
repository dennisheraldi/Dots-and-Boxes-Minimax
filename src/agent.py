"""Agent abstract class."""
from datatypes import Eval


class Agent(object):
    """An interface for agent.

    Inherit this to create your own agents.
    """

    def search(self) -> Eval:
        """Return the evaluation result of the agent.

        Evaluation result consist of move and score.

        Raises:
            NotImplementedError: If not implemented.
        """
        raise NotImplementedError()
