# princess/model.py
"""
Base Game Model.
"""
from enum import Enum

GAMESTATE = Enum('STATE', 'INIT ACTIVE OVER')
PLAYER = Enum('PLAYER', 'OTHER PRINCESS')

THE_CHARS = {
    'Holmes': 'RED',
    'Watson': 'BROWN',
    'Smith' : 'YELLOW',
    'LeStrade': 'BLUE',
    'Stealthy': 'GREEN',
    'Goodley': 'BLACK',
    'Gull': 'PURPLE',
    'Bert': 'ORANGE',
    }
MAX_TURNS = 8

class GameError(RuntimeError):
    """Generic exception for in-game runtime errors."""
    pass


class GameOver(GameError):
    """Raise this exception to end the game."""
    def __init__(self, game, winner):
        game.state = GAMESTATE.OVER
        if winner == None:
            self.reason = "Game aborted."
        else:
            self.winner = winner
            self.princess = game.princess
            if game.turn > game.max_turn:
                self.reason = "Turns expired."
            else:
                self.reason = "Unmasked wrong princess."


class GameModel(object):

    def __init__(self, owner=None):
        self.chars = dict(THE_CHARS)
        self.__charlotte = None
        self.player = {x: None for x in PLAYER} # Unused?
        self.turndeck = []
        self.cluedeck = []
        self.available_chars = []
        self.current = None
        self.state = GAMESTATE.INIT
        self.max_turn = MAX_TURNS

    @staticmethod
    def other(player: PLAYER):
        """Convenience function for PLAYER values."""
        if isinstance(player, PLAYER):
            return PLAYER(3 - player.value)
        else:
            raise ValueError(f'Invalid PLAYER type: {player}')

    @property
    def princess(self):
        """The secret identity of Princess Charlotte."""
        return self.__charlotte

    @princess.setter
    def princess(self, character):
        if character not in self.chars.keys():
            raise ValueError(f'Invalid character: {character}')
        # Can only change the princess during INIT state
        if self.state != GAMESTATE.INIT:
            raise GameError('Can only change the princess during game init.')
        else:
            self.__charlotte = character
