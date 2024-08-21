from math import sqrt
from typing import Optional

from models.segment import Segment
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

    def intersection(self, primeiro: Segment, segundo: Segment) -> Optional[Vertex]:
        # Calculando s e t;
        denon = (segundo.b.x - segundo.a.x) * (primeiro.b.y - primeiro.a.y) - (
            segundo.b.y - segundo.a.y
        ) * (primeiro.b.x - primeiro.a.x)
        if abs(denon) > self.tolerance:
            s = (
                (segundo.b.x - segundo.a.x) * (segundo.a.y - primeiro.a.y)
                - (segundo.b.y - segundo.a.y) * (segundo.a.x - primeiro.a.x)
            ) / denon
            t = (
                (primeiro.b.x - primeiro.a.x) * (segundo.a.y - primeiro.a.y)
                - (primeiro.b.y - primeiro.a.y) * (segundo.a.x - primeiro.a.x)
            ) / denon

            # Verificando se há interseção.
            if (s > -self.tolerance and s < (1 + self.tolerance)) and (
                t > -self.tolerance and t < (1 + self.tolerance)
            ):
                x = primeiro.a.x + (s * (primeiro.b.x - primeiro.a.x))
                y = primeiro.a.y + (s * (primeiro.b.y - primeiro.a.y))
                return Vertex(x, y)
        return None
