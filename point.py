#!/usr/bin/python3

from enum import Enum


class Point:

    def __init__(self, x: int, y: int):
        self._x = x
        self._y = y

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    def __add__(self, other_point: 'Point') -> 'Point':
        return Point(self.x + other_point.x, self.y + other_point.y)

    def __mul__(self, coefficient: int):
        return Point(self.x * coefficient, self.y * coefficient)

    def __rmul__(self, coefficient: int):
        return self * coefficient

    def __eq__(self, o: object) -> bool:
        return type(o) is Point and self.x == o.x and self.y == o.y

    def __hash__(self) -> int:
        return hash(self.x)*31 + hash(self.y)

    def __str__(self):
        return "(" + str(self._x) + ", " + str(self._y) + ")"


class Direction(Enum):
    Up = Point(0, 1)
    Down = Point(0, -1)
    Left = Point(-1, 0)
    Right = Point(1, 0)
    Stand = Point(0, 0)
