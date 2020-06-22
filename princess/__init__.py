# princess/__init__.py

from enum import Enum
PLAYER = Enum('PLAYER', 'OTHER PRINCESS', module=__name__)
GAMESTATE = Enum('STATE', 'INIT ACTIVE OVER', module=__name__)

from .model import GameModel
from .operations import GameOperations
from .view import GameView
from .events import GameEvents

class Game(GameModel, GameOperations, GameView, GameEvents):

    def __init__(self):
        """Base game class for Princess Charlotte."""
        GameModel.__init__(self)
        GameOperations.__init__(self)
        GameView.__init__(self)
        GameEvents.__init__(self)
