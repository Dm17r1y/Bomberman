#!/usr/bin/python3

from logic import Map, CELL_SIZE, Point
import random
from child_classes import DestroyableBlock, SimpleMonster, UnbreakableBlock


class LevelCreator:

    EMPTY_CHAR = " "

    def __init__(self, legend):
        self.legend = legend

    def create_level(self, level):
        game_map = Map()
        height = len(level)
        width = max(len(level_) for level_ in level)
        for y, line in enumerate(level):
            for x, char in enumerate(line):
                if char in self.legend:
                    objects = self.legend[char]()
                    for obj in objects:
                        game_map.add_map_object(obj, Point(x * CELL_SIZE,
                                                           y * CELL_SIZE))
                elif char != LevelCreator.EMPTY_CHAR:
                    raise Exception("Cell not in legend: " + char)

        return game_map, width, height

    @staticmethod
    def create_random_level(map_width, map_height):
        game_map = Map()
        LevelCreator._add_borders(game_map, map_width, map_height)
        LevelCreator._add_single_blocks(game_map, map_width, map_height)
        empty_points = [
            Point(CELL_SIZE, CELL_SIZE),
            Point(CELL_SIZE, 2 * CELL_SIZE),
            Point(2 * CELL_SIZE, CELL_SIZE)
        ]
        game_map.add_map_object(DestroyableBlock(),
                                Point(CELL_SIZE * 3, CELL_SIZE))
        game_map.add_map_object(DestroyableBlock(),
                                Point(CELL_SIZE, CELL_SIZE * 3))
        LevelCreator._add_random_objects(game_map, map_width, map_height,
                                         empty_points)
        return game_map

    @staticmethod
    def _add_borders(game_map, map_width, map_height):
        for i in range(0, map_width):
            game_map.add_map_object(UnbreakableBlock(),
                                    Point(i * CELL_SIZE, 0))
            game_map.add_map_object(UnbreakableBlock(),
                                    Point(i * CELL_SIZE,
                                          (map_height - 1) * CELL_SIZE))

        for i in range(1, map_height - 1):
            game_map.add_map_object(UnbreakableBlock(),
                                    Point(0, i * CELL_SIZE))
            game_map.add_map_object(UnbreakableBlock(),
                                    Point((map_height - 1) * CELL_SIZE,
                                          i * CELL_SIZE))

    @staticmethod
    def _add_single_blocks(game_map, map_width, map_height):
        for i in range(0, map_width):
            for j in range(0, map_height):
                location = Point(i * CELL_SIZE, j * CELL_SIZE)
                if i % 2 == 0 and j % 2 == 0 and \
                        len(list(game_map.get_map_objects(location))) == 0:
                    game_map.add_map_object(UnbreakableBlock(), location)

    @staticmethod
    def _add_random_objects(game_map, map_width, map_height,
                            empty_positions):
        for i in range(0, map_width):
            for j in range(0, map_height):
                coordinates = Point(i * CELL_SIZE, j * CELL_SIZE)
                if coordinates not in empty_positions and \
                        len(list(game_map.get_map_objects(coordinates))) == 0:
                    LevelCreator._add_random_object(game_map, coordinates)

    @staticmethod
    def _add_random_object(game_map, coordinates):
        if random.randint(0, 1) == 0:
            game_map.add_map_object(DestroyableBlock(), coordinates)
        elif random.randint(0, 3) == 0:
            game_map.add_map_object(SimpleMonster(), coordinates)
