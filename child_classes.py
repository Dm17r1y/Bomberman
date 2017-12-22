#!/usr/bin/python3

from logic import *
import random
from queue import Queue


LONG_RANGE_EXPLOSION_RADIUS = 5


class SimpleMonster(Monster):

    def __init__(self):
        super().__init__()
        self.object_types = [Block, Bomb, Bonus]
        self.direction = None

    def move(self, coordinates: 'Point', old_map: 'Map'):
        if self.direction and self._can_move(old_map,
                                             coordinates +
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
        return self._correct_collisions_to_move(collisions)

    def _can_move(self, game_map, location):
        collisions = game_map.get_collisions(location)
        return self._correct_collisions_to_move(collisions)

    def _correct_collisions_to_move(self, collisions):
        return all(not isinstance(collision, type_)
                   for collision in collisions
                   for type_ in self.object_types)


class CleverMonster(SimpleMonster):

    VISION_RANGE = 10

    def __init__(self):
        super().__init__()
        self._next_point = None
        self._player_position = None

    def in_vision_range(self, my_coordinates, object_coordinates):
        return abs(my_coordinates.x - object_coordinates.x) < \
               self.VISION_RANGE * CELL_SIZE and \
               abs(my_coordinates.y - object_coordinates.y) < \
               self.VISION_RANGE * CELL_SIZE

    def move(self, coordinates: 'Point', old_map: 'Map'):
        if self._next_point != None and self._next_point != coordinates:
            return self._switch_action(self._next_point - coordinates)
        visited = set()
        rounded_coordinates = Map.round_point(coordinates, CELL_SIZE)
        queue = Queue()
        queue.put(rounded_coordinates)
        track = {}
        player_position = None
        while not queue.empty():
            if player_position != None:
                break
            node = queue.get()
            for direction in (Direction.Down, Direction.Up,
                              Direction.Left, Direction.Right):
                new_node = node + (direction.value * CELL_SIZE)
                collisions = old_map.get_collisions(new_node)

                if new_node not in visited and \
                        self.in_vision_range(coordinates, new_node) and \
                        self._correct_collisions_to_move(collisions):

                    visited.add(new_node)
                    queue.put(new_node)
                    track[new_node] = node

                    if any(isinstance(collision, Player)
                           for collision in collisions):
                        player_position = new_node
                        break
        if player_position is None:
            self._next_point = None
            return Move(Direction.Stand)
        else:
            next_point = player_position
            points = []
            while track[next_point] != rounded_coordinates:
                next_point = track[next_point]
                points.append(next_point)
            # print('-------------------')
            # for point in points:
            #     print(point, end="; ")
            # print()
            # print("my coordinates", coordinates)
            # print("next point", next_point)
            # print('-------------------')

            direction = next_point - coordinates
            self._next_point = next_point
            self._player_position = player_position
            return self._switch_action(direction)

    def _switch_action(self, direction):
        if direction.x > 0:
            return Move(Direction.Right)
        elif direction.x < 0:
            return Move(Direction.Left)
        elif direction.y > 0:
            return Move(Direction.Up)
        elif direction.y < 0:
            return Move(Direction.Down)
        else:
            return Move(Direction.Stand)


class StrongMonster(SimpleMonster):

    def solve_collision(self, other_objects):
        if any(isinstance(object_, HighPoweredExplosion)
               for object_ in other_objects):
            self._is_dead = True


class UnbreakableBlock(Block):
    pass


class FortifiedBlock(Block):

    def solve_collision(self, other_objects):
        if any(isinstance(object_, HighPoweredExplosion)
               for object_ in other_objects):
            self._is_dead = True


class DestroyableBlock(Block):

    def solve_collision(self, other_objects):
        if any(isinstance(object_, ExplosionBlock)
               for object_ in other_objects):
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

    def add_bonus(self, player):
        player.set_bomb_type(HighPowerBomb)


class LongExplosionBonus(Bonus):

    def add_bonus(self, player):
        player.add_buff(LongRangeExplosionBuff())


class ImmuneBonus(Bonus):

    def add_bonus(self, player):
        player.add_buff(ImmuneBuff())


class ImmuneBuff(Buff):

    def start(self, player):
        player.immune = True

    def end(self, player):
        player.immune = False


class LongRangeExplosionBuff(Buff):

    def start(self, player):
        player.set_bomb_radius(LONG_RANGE_EXPLOSION_RADIUS)

    def end(self, player):
        player.set_bomb_radius(START_EXPLOSION_RADIUS)
