#!/usr/bin/python3

from logic import Map, CELL_WIDTH, Point, Block
import random
from child_classes import DestroyableBlock, SimpleMonster

class LevelCreator:

    def __init__(self, legend):
        self.legend = legend

    def create_level(self, level):
        game_map = Map()
        for y, line in enumerate(level):
            for x, char in enumerate(line):
                if char in self.legend:
                    objects = self.legend[char]()
                    for obj in objects:
                        game_map.add_map_object(obj, Point(x * CELL_WIDTH,
                                                           y * CELL_WIDTH))
                elif char != " ":
                    raise Exception("Cell not in legend: " + char)

        return game_map

    def create_random_level(self, map_width, map_height):
        game_map = Map()
        self._add_borders(game_map, map_width, map_height)
        self._add_single_blocks(game_map, map_width, map_height)
        empty_points = [
            Point(CELL_WIDTH, CELL_WIDTH),
            Point(CELL_WIDTH, 2 * CELL_WIDTH),
            Point(2 * CELL_WIDTH, CELL_WIDTH)
        ]
        game_map.add_map_object(DestroyableBlock(), Point(CELL_WIDTH * 3, CELL_WIDTH))
        game_map.add_map_object(DestroyableBlock(), Point(CELL_WIDTH, CELL_WIDTH * 3))
        self._add_random_objects(game_map, map_width, map_height, empty_points)
        return game_map

    def _add_borders(self, game_map, map_width, map_height):
        for i in range(0, map_width):
            game_map.add_map_object(Block(), Point(i * CELL_WIDTH, 0))
            game_map.add_map_object(Block(), Point(i * CELL_WIDTH,
                                               (map_height - 1) * CELL_WIDTH))

        for i in range(1, map_height - 1):
            game_map.add_map_object(Block(), Point(0, i * CELL_WIDTH))
            game_map.add_map_object(Block(),
                                    Point((map_height - 1) * CELL_WIDTH,
                                          i * CELL_WIDTH))


    def _add_single_blocks(self, game_map, map_width, map_height):
        for i in range(0, map_width):
            for j in range(0, map_height):
                location = Point(i * CELL_WIDTH, j * CELL_WIDTH)
                if i % 2 == 0 and j % 2 == 0 and \
                        len(list(game_map.get_map_objects(location))) == 0:
                    game_map.add_map_object(Block(), location)

    def _add_random_objects(self, game_map, map_width, map_height,
                            empty_positions):
        for i in range(0, map_width):
            for j in range(0, map_height):
                coordinates = Point(i * CELL_WIDTH, j * CELL_WIDTH)
                if coordinates not in empty_positions and \
                        len(list(game_map.get_map_objects(coordinates))) == 0:
                    self._add_random_object(game_map, coordinates)

    def _add_random_object(self, game_map, coordinates):
        if random.randint(0, 1) == 0:
            game_map.add_map_object(DestroyableBlock(), coordinates)
        elif random.randint(0, 3) == 0:
            game_map.add_map_object(SimpleMonster(), coordinates)
