class Vertex:
    def __init__(
        self, vertexId: int = -1, x: float = 0, y: float = 0, last: bool = False
    ) -> None:
        self.vertexId = vertexId
        self.x = x
        self.y = y
        self.last = last

    def equalsTo(self, p: "Vertex") -> bool:
        return self.x == p.x and self.y == p.y

    def withinTolerance(self, otherX: float, tolerance: float) -> bool:
        return abs(otherX - self.x) <= tolerance

    def isExtremity(self) -> bool:
        return self.vertexId == 0 or self.last
