#!/usr/bin/python3

from logic import *
import random


class SimpleMonster(Monster):

    def __init__(self):
        super().__init__()
        self.direction = None

    def move(self, location, old_map):

        if self.direction and self._can_move(old_map, location +
                self.direction.value):
            return Move(self.direction)
        directions = [Direction.Up, Direction.Down,
                      Direction.Left, Direction.Right]
        random.shuffle(directions)
        for direction in directions:
            if self._can_move(old_map, location + direction.value):
                self.direction = direction
                return Move(direction)
        self.direction = None
        return Move(Direction.Stand)

    def _can_move(self, game_map, location):
        object_types = [Block, Bomb, Bonus]
        collisions = game_map.get_collisions(self, location)
        return all(obj not in map(type, collisions) for obj in object_types)


class CleverMonster(Monster):
    pass


class StrongMonster(Monster):
    pass


class StoneBlock(Block):
    pass


class DestroyableBlock(Block):
    pass


class SimpleBomb(Bomb):
    pass


class HighPowerBomb(Bomb):
    pass


class ManyBombBonus(Bonus):
    pass


class HighBombBonus(Bonus):
    pass


class ImmuneBombBonus(Bonus):
    pass
