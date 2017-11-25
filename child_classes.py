#!/usr/bin/python3

from logic import *
import random


class SimpleMonster(Monster):

    def __init__(self):
        super().__init__()
        self.object_types = [Block, Bomb, Bonus]
        self.direction = None

    def move(self, coordinates: 'Point', old_map: 'Map'):
        if self.direction and self._can_move(old_map, coordinates +
                self.direction.value):
            return Move(self.direction)
        directions = [Direction.Up, Direction.Down,
                      Direction.Left, Direction.Right]
        random.shuffle(directions)
        for direction in directions:
            if self._can_move(old_map, coordinates + direction.value):
                self.direction = direction
                return Move(direction)
        self.direction = None
        return Move(Direction.Stand)

    def can_move(self, collisions, old_collisions):
        return all(obj not in map(type, collisions)
                   for obj in self.object_types)

    def _can_move(self, game_map, location):
        collisions = game_map.get_collisions(self, location)
        return all(obj not in map(type, collisions)
                   for obj in self.object_types)


class CleverMonster(SimpleMonster):

    def move(self, coordinates: 'Point', old_map: 'Map'):
        path = []


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
