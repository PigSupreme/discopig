# princess/view.py
"""
Base Game View.
"""
from .model import PLAYER

class GameView(object):

    def __init__(self):
        pass

    def get_turn_leader(self):
        """Which player should start this turn?"""
        # Odd turns are lead by un-princess
        if (self.turn % 2) == 1:
            return PLAYER.OTHER
        else:
            return PLAYER.PRINCESS
