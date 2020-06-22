# princess/events.py
"""
Base Game Events.
"""
import random
from .model import GameOver, GameError
from princess import GAMESTATE, PLAYER

class GameEvents(object):

    def __init__(self):
        pass

    def start_game(self):
        """Set the starting player, state, and turn."""
        if self.state != GAMESTATE.INIT:
            raise GameError('Game is already started!')
            return
        self.current = PLAYER.OTHER
        self.turn = 1
        self.state = GAMESTATE.ACTIVE

    def start_turn(self):
        """
        Set up resources for this turn.

        1. Set the current player.
        2. Populate available characters.
        """
        if self.state != GAMESTATE.ACTIVE:
            raise GameError('Game is inactive!')
            return
        # 1 #
        self.current = self.get_turn_leader()
        # 2 #
        if self.turndeck == []:
            self.turndeck = list(self.chars.keys())
            random.shuffle(self.turndeck)
        self.available_chars = self.turndeck[:4]
        self.turndeck = self.turndeck[4:]

    def choose_char(self, char):
        """
        Choose a current character and do their action.

        1. Check that game is active and char is available.
        2. Simulated action (placeholder for later).
        3. Switch current player if needed.
        """
        # 1 #
        if self.state != GAMESTATE.ACTIVE:
            raise GameError('Game is inactive!')
            return
        if char not in self.available_chars:
            raise GameError(f'Character {char} is not available.')
            return
        # 2 #
        self.available_chars.remove(char)
        chars_left = len(self.available_chars)
        # 3 #
        # Switch when 3 or 1 characters are left
        if chars_left % 2 == 1:
            self.current = self.other(self.current)

    def end_turn(self):
        """Ends the turn and checks for game over."""
        if self.state != GAMESTATE.ACTIVE:
            raise GameError('Game is inactive!')
            return
        self.turn += 1
        if self.turn > self.max_turn:
            # Princess wins for not being discovered
            raise GameOver(self, PLAYER.PRINCESS)
        # Switch players for next turn
        self.current = self.other(self.current)

    def draw_clue(self):
        """Reveal a character who is not the princess."""
        if self.state != GAMESTATE.ACTIVE:
            raise GameError('Game is inactive!')
        try:
            clue = self.cluedeck.pop()
            return clue
        except IndexError: # Empty deck; should never happen
            raise GameError('Clue deck is empty!')

    def unmask_princess(self, char):
        """Unmask the princess (will end the game)."""
        if self.state != GAMESTATE.ACTIVE:
            raise GameError('Game is inactive!')
        if char not in self.chars.keys():
            raise ValueError(f'Invalid character: {char}')
        if self.current == PLAYER.PRINCESS:
            raise GameError('The princess cannot unmask herself!')
        if char == self.princess:
            raise GameOver(self, PLAYER.OTHER)
        else:
            raise GameOver(self, PLAYER.PRINCESS)
