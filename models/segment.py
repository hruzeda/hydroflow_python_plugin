from typing import Optional

from models.vertex import Vertex


class Segment:
    def __init__(self) -> None:
        self.id = -1
        self.featureId = -1
        self.setId = -1
        self.a: Optional[Vertex] = None
        self.b: Optional[Vertex] = None
        self.isMouth = False

    def getSmallerX(self, tolerance: float) -> float:
        return self.a.x if self.a.x + tolerance < self.b.x else self.b.x
