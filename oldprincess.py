#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hey, my kid brother tried to write a docstring
before bedtime...it didn't end well.
"""
import random
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

# Move Model?
class GameOver(Exception):
    """Raise this exception to end the game."""
    def __init__(self, winner, princess):
        self.winner = winner
        self.princess = princess

class PrincessGame(object):

    # MOVE Model (DONE)
    def __init__(self, owner=None):
        self.chars = dict(THE_CHARS)
        self.__charlotte = None
        self.player = {x: None for x in PLAYER}
        self.turndeck = []
        self.cluedeck = []
        self.current = None
        self.state = GAMESTATE.INIT

    # MOVE Model (DONE, expanded)
    @property
    def princess(self):
        return self.__charlotte

    # MOVE Events (for Bot??)
    def add_player(self, *, princess=None, other=None):
        """TODO: What are we using this for?"""
        if princess:
            self.player[PLAYER.PRINCESS] = princess
        if other:
            self.player[PLAYER.OTHER] = other

    # MOVE Events (for Bot??)
    def remove_player(self, *args):
        """TODO: This works with to add_player above."""
        for pl in args:
            if isinstance(pl, PLAYER):
                self.player[pl] = None

    # MOVE Operations (DONE)
    def reset(self):
        """Resets the game to its original state."""
        random.seed()
        self.turndeck = list(self.chars.keys())
        random.shuffle(self.turndeck)

        self.cluedeck = list(self.chars.keys())
        random.shuffle(self.cluedeck)

        self.state = GAMESTATE.INIT
        self.__charlotte = None
        self.turn = 0

    # MOVE Events (done)
    def start_game(self):
        """Choose the princess and prepare for turn 1."""
        self.__charlotte = self.cluedeck.pop()
        self.current = PLAYER.OTHER
        self.turn = 1

    # MOVE Events (DONE, edited)
    def start_turn(self):
        """Returns a list of four characters available this turn."""
        if self.turndeck == []:
            self.turndeck = list(self.chars.keys())
            random.shuffle(self.turndeck)

        this_turn = self.turndeck[:4]
        self.turndeck = self.turndeck[4:]

        # TODO: Instead of returning this, set some attributes...
        # ...that can be retreived later.
        return this_turn

    # MOVE Events (Done, slightly modified)
    def get_clue(self):
        """Reveal a character who is not the princess."""
        ### Although this should be impossible, we check anyway:
        if self.cluedeck == []:
            return None
        clue = self.cluedeck.pop()
        return clue

    # MOVE Events (Done, modified to use model.other())
    def end_turn(self):
        """Ends the turn and checks for game over."""
        self.turn += 1
        if self.turn > MAX_TURNS:
            raise GameOver('princess', self.__charlotte)
        # Switch players for next turn
        pval = self.current.value  # Will be 1 or 2
        self.current = PLAYER(3 - pval)

    # MOVE Events (DONE)
    def unmask_princess(self, char):
        """Unmask the princess (will end the game)."""
        if char not in self.chars.keys():
            raise ValueError(f'Invalid character: {char}')
            return None
        if char == self.__charlotte:
            raise GameOver('other', self.__charlotte)
            return True
        else:
            raise GameOver('princess', self.__charlotte)
            return False
