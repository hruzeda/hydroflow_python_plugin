from decimal import Decimal

from .vertex import Vertex


class Segment:
    def __init__(
        self,
        segmentId: int,
        featureId: int,
        originalFeatureId: int,
        setId: int,
        a: Vertex,
        b: Vertex,
    ):
        self.segmentId = segmentId
        self.featureId = featureId
        self.originalFeatureId = originalFeatureId
        self.setId = setId
        self.a = a
        self.b = b
        self.isMouth = False

    def getSmallerX(self, tolerance: Decimal) -> Decimal:
        return self.a.x if self.a.x + tolerance < self.b.x else self.b.x

    def isPoint(self, tolerance: Decimal) -> bool:
        return (
            abs(self.a.x - self.b.x) <= tolerance
            and abs(self.a.y - self.b.y) <= tolerance
        )

    def isHorizontal(self, tolerance: Decimal) -> bool:
        return not self.isPoint(tolerance) and abs(self.a.y - self.b.y) <= tolerance

    def isVertical(self, tolerance: Decimal) -> bool:
        return not self.isPoint(tolerance) and abs(self.a.x - self.b.x) <= tolerance

    def compareTo(self, other: "Segment") -> int:
        # Compara dois segmentos
        # Valores de retorno:
        #  1 - se este objeto é menor que o informado.
        #  0 - se este objeto é igual ao informado.
        #  1 - se este objeto é maior que o informado.
        # Critério de ordenação:
        #  1º - idConjunto;
        #  2º - idFeicao;
        #  3° - id.

        if self.setId < other.setId:
            return -1
        if self.setId > other.setId:
            return 1
        if self.originalFeatureId < other.originalFeatureId:
            return -1
        if self.originalFeatureId > other.originalFeatureId:
            return 1
        if self.segmentId < other.segmentId:
            return -1
        if self.segmentId > other.segmentId:
            return 1
        return 0

    def __str__(self) -> str:
        return (
            f"Segment {self.segmentId} ({self.featureId})\n"
            f"Original FID: {self.originalFeatureId}\n"
            f"a: {self.a}\n"
            f"b: {self.b}"
        )
