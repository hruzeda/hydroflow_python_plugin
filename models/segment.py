from typing import Optional

from .vertex import Vertex


class Segment:
    def __init__(
        self,
        segmentId: int,
        featureId: int,
        setId: Optional[int],
        a: Vertex,
        b: Vertex,
    ):
        self.segmentId = segmentId
        self.featureId = featureId
        self.setId = setId
        self.a = a
        self.b = b
        self.isMouth = False

    def getSmallerX(self, tolerance: float) -> float:
        return self.a.x if self.a.x + tolerance < self.b.x else self.b.x

    def isPoint(self, tolerance: float) -> bool:
        return (
            abs(self.a.x - self.b.x) <= tolerance
            and abs(self.a.y - self.b.y) <= tolerance
        )

    def isHorizontal(self, tolerance: float) -> bool:
        return not self.isPoint(tolerance) and abs(self.a.y - self.b.y) <= tolerance

    def isVertical(self, tolerance: float) -> bool:
        return not self.isPoint(tolerance) and abs(self.a.x - self.b.x) <= tolerance

    def compareTo(self, segment: "Segment") -> int:
        # Compara dois segmentos
        # Valores de retorno:
        #  1 - se este objeto é menor que o informado.
        #  0 - se este objeto é igual ao informado.
        #  1 - se este objeto é maior que o informado.
        # Critério de ordenação:
        #  1º - idConjunto;
        #  2º - idFeicao;
        #  3° - id.

        if self.setId and segment.setId:
            if self.setId < segment.setId:
                return -1
            if self.setId > segment.setId:
                return 1
        if self.featureId < segment.featureId:
            return -1
        if self.featureId > segment.featureId:
            return 1
        if self.segmentId < segment.segmentId:
            return -1
        if self.segmentId > segment.segmentId:
            return 1
        return 0
