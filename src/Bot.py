from GameAction import GameAction
from GameState import GameState


class Bot(object):
    # An interface for bot. Inherit it to create your own bots!
    def get_action(self, state: GameState) -> GameAction:
        # Returns action based on state.
        raise NotImplementedError()
