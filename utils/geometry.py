from math import sqrt
from typing import Optional

from models.vertex import Vertex


class Geometry:
    def __init__(self, tolerance=0):
        self.tolerance = tolerance

    def smallerThan(self, a, b):
        return a + self.tolerance < b

    def equalsTo(
        self,
        a: Optional[Vertex] = None,
        b: Optional[Vertex] = None,
        aX: Optional[float] = None,
        bX: Optional[float] = None,
    ):
        if a and b:
            return sqrt(pow(b.x - a.x, 2) + pow(b.y - a.y, 2)) <= self.tolerance
        return abs(aX - bX) <= self.tolerance
