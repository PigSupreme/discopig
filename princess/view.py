# princess/view.py
"""
Base Game View.
"""
from princess import GAMESTATE, PLAYER

class GameView(object):

    def __init__(self):
        pass

    @property
    def status_str(self):
        """Printable game status."""
        if self.state == GAMESTATE.INIT:
            return "Game has not started."
        elif self.state == GAMESTATE.ACTIVE:
            return f"Game active, turn {self.turn}"
        elif self.state == GAMESTATE.OVER:
            return f"Game Over, winner was ???"

    @property
    def current_str(self):
        """Printable string showing current player."""
        # TODO: PLAYER Enum class should take care of this.
        try:
            return self.player[self.current]
        except KeyError:
            return "PLAYER_UNKNOWN"

    def get_turn_leader(self):
        """Which player should start this turn?"""
        # Odd turns are lead by un-princess
        if (self.turn % 2) == 1:
            return PLAYER.OTHER
        else:
            return PLAYER.PRINCESS

    @property
    def is_active(self):
        """Is this game in the ACTIVE state?"""
        return self.state == GAMESTATE.ACTIVE
