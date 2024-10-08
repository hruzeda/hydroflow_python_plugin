from decimal import Decimal


class Vertex:
    def __init__(
        self,
        vertexId: int = -1,
        x: Decimal = Decimal(0),
        y: Decimal = Decimal(0),
        last: bool = False,
    ) -> None:
        self.vertexId = vertexId
        self.x = x
        self.y = y
        self.last = last

    def equalsTo(self, p: "Vertex") -> bool:
        return self.x == p.x and self.y == p.y

    def withinTolerance(self, otherX: Decimal, tolerance: Decimal) -> bool:
        return abs(otherX - self.x) <= tolerance

    def isExtremity(self) -> bool:
        return self.vertexId == 0 or self.last

    def __str__(self) -> str:
        return f"Vertex {self.vertexId} ({self.x}, {self.y})"
