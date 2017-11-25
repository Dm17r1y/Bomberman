#!/usr/bin/python3

import abc


class PlayerController(abc.ABC):

    @abc.abstractclassmethod
    def select_action(self):
        pass


class GameController(abc.ABC):
    pass
