#!/usr/bin/python3

from point import Direction, Point
from collections import defaultdict
from controller import *


CELL_WIDTH = 16
EXPLOSION_LIVE = 100
CORNER_SIZE = 8


class OutOfMapRangeException(Exception):
    pass


class Map:

    def __init__(self):
        self._objects = defaultdict(list)

    def add_map_object(self, map_object: 'MapObject', coordinates: 'Point'):
        self._objects[coordinates].append(map_object)

    def get_map_objects(self, coordinates: Point):
        if coordinates not in self._objects:
            return []
        return self._objects[coordinates].copy()

    @staticmethod
    def round(number: int, cell_width: int) -> int:
        modulo = number % cell_width
        if modulo < cell_width / 2:
            return number - modulo
        else:
            return number + cell_width - modulo

    def add_bomb(self, bomb: 'Bomb', coordinates: 'Point'):
        self.add_map_object(bomb, Point(
            Map.round(coordinates.x, CELL_WIDTH),
            Map.round(coordinates.y, CELL_WIDTH)
        ))

    def enumerate_all_objects(self):
        for point in self._objects.keys():
            for game_object in self.get_map_objects(point):
                yield point, game_object

    @staticmethod
    def are_intersected(first_coordinates: Point,
                        second_coordinates: Point):

        return abs(first_coordinates.x - second_coordinates.x) < \
               CELL_WIDTH and \
               abs(first_coordinates.y - second_coordinates.y) < \
               CELL_WIDTH

    def get_collisions(self, map_object: 'MapObject', coordinates: 'Point')\
            -> list:
        collisions = []
        for object_coordinates, game_object in \
                ((point, obj)
                 for point, obj in self.enumerate_all_objects()
                 if obj != map_object):
            if Map.are_intersected(coordinates, object_coordinates):
                collisions.append(game_object)

        return collisions

    @property
    def occupied_cells(self) -> set:
        return set(self._objects.keys())


class Game:

    def __init__(self,
                 game_map: 'Map',
                 controller: 'GameController',
                 player: 'Player'):
        self._map = game_map
        self._controller = controller
        self._player = player

    @property
    def player(self) -> 'Player':
        return self._player

    @property
    def map(self):
        return self._map

    def make_turn(self):
        animations = []
        intermediate_map = Map()
        for point in self._map.occupied_cells:
            for game_object in self._map.get_map_objects(point):
                action = game_object.move(point, self._map)
                new_animations = action.change_game_state(
                    game_object, point, self._map, intermediate_map
                )
                for animation in new_animations:
                    animations.append(animation)

        game_map = Map()
        for point in intermediate_map.occupied_cells:
            for game_object in intermediate_map.get_map_objects(point):
                other_objects = intermediate_map.get_collisions(game_object,
                                                                point)
                game_object.solve_collision(other_objects)
                if not game_object.is_dead:
                    game_map.add_map_object(game_object, point)

        self._map = game_map
        return animations


class Animation:

    def __init__(self, object, location, direction):
        self.object = object
        self.location = location
        self.direction = direction


class Move:

    def __init__(self, direction):
        self._direction = direction

    @property
    def direction(self):
        return self._direction

    def change_game_state(self, game_object, coordinates, old_map, game_map):
        collisions = old_map.get_collisions(game_object,
                                            coordinates + self.direction.value)
        old_collisions = old_map.get_collisions(game_object, coordinates)
        if game_object.can_move(collisions, old_collisions):
            game_map.add_map_object(game_object,
                                    coordinates + self.direction.value)
            return (Animation(game_object, coordinates, self.direction),)
        else:
            directions = (Direction.Up, Direction.Down) \
                    if self.direction in (Direction.Right, Direction.Left) \
                    else (Direction.Right, Direction.Left)
            for new_direction in directions:
                for i in range(1, CORNER_SIZE + 1):
                    point = i * new_direction.value + self.direction.value
                    collisions = old_map.get_collisions(game_object, coordinates + point)
                    if game_object.can_move(collisions, old_collisions):
                        game_map.add_map_object(game_object, coordinates + new_direction.value)
                        return (Animation(game_object, coordinates, new_direction),)
        game_map.add_map_object(game_object, coordinates)
        return (Animation(game_object, coordinates, Direction.Stand),)


class PutBomb:

    def __init__(self, bomb):
        self._bomb = bomb

    @property
    def bomb(self):
        return self._bomb

    def change_game_state(self, game_object, coordinates, old_map, game_map):
        animations = []
        point = Point(Map.round(coordinates.x, CELL_WIDTH),
                      Map.round(coordinates.y, CELL_WIDTH))
        collisions = old_map.get_collisions(game_object, point)
        if len(collisions) == 0:
            game_map.add_bomb(self.bomb, coordinates)
            game_object.set_last_bomb(self.bomb)
            animations.append(Animation(self.bomb, coordinates, Direction.Stand))
        game_map.add_map_object(game_object, coordinates)
        animations.append(Animation(game_object, coordinates, Direction.Stand))
        return animations


class Explose:

    def __init__(self, center: 'Point', radius: int):
        self._center = center
        self._radius = radius

    def change_game_state(self, game_object, coordinates, old_map, game_map):
        animations = []
        stop_explosion_objects = (Block, Bomb, Bonus)
        game_map.add_map_object(ExplosionBlock(EXPLOSION_LIVE), coordinates)
        for direction in (Direction.Right, Direction.Left,
                          Direction.Up, Direction.Down):
            for i in range(1, self._radius):
                point = Point(coordinates.x +
                              i * direction.value.x * CELL_WIDTH,
                              coordinates.y +
                              i * direction.value.y * CELL_WIDTH)
                explosion = ExplosionBlock(EXPLOSION_LIVE)
                animations.append(Animation(explosion, point, Direction.Stand))
                game_map.add_map_object(explosion, point)
                collisions = old_map.get_collisions(None, point)
                if any(game_object in map(type, collisions)
                       for game_object in stop_explosion_objects):
                    break
        return animations


class MapObject:

    def __init__(self):
        self._is_dead = False

    def can_move(self, collisions, old_collisions):
        return True

    def move(self, coordinates: 'Point', old_map: 'Map'):
        return Move(Direction.Stand)

    def solve_collision(self, other_objects):
        pass

    @property
    def is_dead(self):
        return self._is_dead


class Player(MapObject):

    def __init__(self, controller: 'PlayerController'):
        super().__init__()
        self._controller = controller
        self._last_bomb = None

    def set_last_bomb(self, bomb):
        self._last_bomb = bomb

    def move(self, coordinates: 'Point', old_map: 'Map'):
        return self._controller.select_action()

    def can_move(self, collisions, old_collisions):
        objects = [Block, Bomb]
        return not any(game_object in map(type, collisions)
                       for game_object in objects
                       if game_object != self._last_bomb and
                       self._last_bomb not in old_collisions)

    def solve_collision(self, other_objects: list):
        objects = [Monster, ExplosionBlock]
        if any(game_object in map(type, other_objects)
               for game_object in objects):
            self._is_dead = True


class Monster(MapObject):

    def solve_collision(self, other_objects):
        if ExplosionBlock in map(type, other_objects):
            self._is_dead = True


class Block(MapObject):
    pass


class Bomb(MapObject):

    def __init__(self, tick_delay: int, explosion_radius: int):
        super().__init__()
        self._tick_delay = tick_delay
        self._explosion_radius = explosion_radius

    def move(self, coordinates: 'Point', old_map: 'Map'):
        self._tick_delay -= 1
        if self._tick_delay == 0:
            self._is_dead = True
            return Explose(coordinates, self._explosion_radius)
        return Move(Direction.Stand)


class ExplosionBlock(MapObject):

    def __init__(self, life_time: int):
        super().__init__()
        self._life_time = life_time

    def solve_collision(self, other_objects):
        self._life_time -= 1
        if self._life_time == 0:
            self._is_dead = True


class Bonus(MapObject):

    def solve_collision(self, other_objects):
        if Player in map(type, other_objects):
            self._is_dead = True

