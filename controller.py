#!/usr/bin/python3

import abc


class PlayerController(abc.ABC):

    @abc.abstractclassmethod
    def select_action(self):
        pass

    def set_player(self, player):
        self._player = player


class GameController(abc.ABC):
    pass
