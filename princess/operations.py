# princess/operations.py
"""
Base Game Operations.
"""
import random
from .model import GameOver
from princess import GAMESTATE

class GameOperations(object):

    def __init__(self):
        pass

    def reset_game(self):
        """
        Reset the game to its original state.

        1. Restock/shuffle the character turn deck.
        2. Restock/shuffle the character clue deck.
        3. Reset the GAMESTATE and turn number.
        4. Set secret identity for Charlotte.
        """
        if self.state == GAMESTATE.ACTIVE:
            raise GameOver(self, None)
        random.seed()
        # 1 #
        self.turndeck = list(self.chars.keys())
        random.shuffle(self.turndeck)
        # 2 #
        self.cluedeck = list(self.chars.keys())
        random.shuffle(self.cluedeck)
        # 3 #
        self.state = GAMESTATE.INIT
        self.turn = 0
        # 4 #
        self.princess = self.cluedeck.pop()

