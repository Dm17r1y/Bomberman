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
        return self._correct_collisions(collisions)

    def _can_move(self, game_map, location):
        collisions = game_map.get_collisions(self, location)
        return self._correct_collisions(collisions)

    def _correct_collisions(self, collisions):
        for collision in collisions:
            for type_ in self.object_types:
                if isinstance(collision, type_):
                    return False
        return True


class CleverMonster(SimpleMonster):

    VISION_RANGE = 10

    def move(self, coordinates: 'Point', old_map: 'Map'):

        visited = set()
        rounded_coordinates = Map.round_point(coordinates, CELL_WIDTH)
        stack = [rounded_coordinates]
        track = {}
        player_position = None
        while len(stack) > 0:
            node = stack.pop()
            for direction in (Direction.Down, Direction.Up,
                              Direction.Left, Direction.Right):
                new_node = node + (direction.value * CELL_WIDTH)
                collisions = old_map.get_collisions(self, new_node)

                if new_node not in visited and \
                        abs(coordinates.x - new_node.x) < \
                                        self.VISION_RANGE * CELL_WIDTH and \
                        abs(coordinates.y - new_node.y) < \
                                        self.VISION_RANGE * CELL_WIDTH and \
                        self._correct_collisions(collisions):

                    visited.add(new_node)
                    stack.append(new_node)
                    track[new_node] = node


                    if Player in map(type, collisions):
                        player_position = new_node
                        break
        if player_position is None:
            return Move(Direction.Stand)
        else:
            next_point = player_position
            while track[next_point] != rounded_coordinates:
                next_point = track[next_point]
            direction = next_point - coordinates
            if direction.x > 0:
                return Move(Direction.Right)
            elif direction.x < 0:
                return Move(Direction.Left)
            elif direction.y > 0:
                return Move(Direction.Up)
            else:
                return Move(Direction.Down)



class StrongMonster(SimpleMonster):

    def solve_collision(self, other_objects):
        for object in other_objects:
            if isinstance(object, HighPoweredExplosion):
                self._is_dead = True


class UnbreakableBlock(Block):
    pass


class StoneBlock(Block):

    def solve_collision(self, other_objects):
        for object in other_objects:
            if isinstance(object, HighPoweredExplosion):
                self._is_dead = True


class DestroyableBlock(Block):

    def solve_collision(self, other_objects):
        for object in other_objects:
            if isinstance(object, ExplosionBlock):
                self._is_dead = True


class SimpleBomb(Bomb):
    pass


class HighPowerBomb(Bomb):

    def __init__(self, tick_delay, explosion_radius):
        super().__init__(tick_delay, explosion_radius)
        self._explosion_type = HighPoweredExplosion


class HighPoweredExplosion(ExplosionBlock):
    pass


class HighBombBonus(Bonus):
    pass


class LongExplosionBonus(Bonus):
    pass


class ImmuneBonus(Bonus):
    pass
