#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hey, my kid brother tried to write a docstring
before bedtime...it didn't end well.
"""
import random

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

class GameOver(Exception):
    """Raise this exception to end the game."""
    def __init__(self, winner, princess):
        self.winner = winner
        self.princess = princess

class PrincessGame(object):

    def __init__(self, owner=None):
        self.chars = dict(THE_CHARS)
        self.__charlotte = None
        self.player = {'princess': None, 'other': None}
        self.turndeck = []
        self.cluedeck = []

    def set_players(self, princess, other):
        self.player['princess'] = princess
        self.player['other'] = other

    def reset(self):
        """Resets the game to its original state."""
        random.seed()
        self.turndeck = list(self.chars.keys())
        random.shuffle(self.turndeck)

        self.cluedeck = list(self.chars.keys())
        random.shuffle(self.cluedeck)
        self.__charlotte = self.cluedeck.pop()

        self.turn = 1

        return self.__charlotte


    def start_turn(self):
        """Returns a list of four characters available this turn."""
        if self.turndeck == []:
            self.turndeck = list(self.chars.keys())
            random.shuffle(self.turndeck)

        this_turn = self.turndeck[:4]
        self.turndeck = self.turndeck[4:]

        return this_turn

    def get_clue(self):
        """Reveal a character who is not the princess."""
        ### Although this should be impossible, we check anyway:
        if self.cluedeck == []:
            return None
        clue = self.cluedeck.pop()
        return clue

    def end_turn(self):
        """Ends the turn."""
        self.turn += 1
        if self.turn > MAX_TURNS:
            raise GameOver('princess', self.__charlotte)

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
