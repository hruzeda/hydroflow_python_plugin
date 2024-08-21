from typing import Optional

from models.vertex import Vertex


class Segment:
    def __init__(
        self,
        id=-1,
        featureId=-1,
        setId=-1,
        a: Optional[Vertex] = None,
        b: Optional[Vertex] = None,
    ):
        self.id = id
        self.featureId = featureId
        self.setId = setId
        self.a = a
        self.b = b
        self.isMouth = False

    def getSmallerX(self, tolerance: float) -> float:
        return self.a.x if self.a.x + tolerance < self.b.x else self.b.x

    def isPoint(self, tolerance: float):
        return (
            abs(self.a.x - self.b.x) <= tolerance
            and abs(self.a.y - self.b.y) <= tolerance
        )

    def isHorizontal(self, tolerancia: float) -> bool:
        if not self.isPoint(tolerancia):
            if abs(self.a.y - self.b.y) <= tolerancia:
                return True
        return False

    def isVertical(self, tolerance: float):
        return not self.isPoint(tolerance) and abs(self.a.x - self.b.x) <= tolerance

    def compareTo(self, segmento: "Segment") -> int:
        # Compara dois segmentos
        # Valores de retorno:
        #  1 - se este objeto é menor que o informado.
        #  0 - se este objeto é igual ao informado.
        #  1 - se este objeto é maior que o informado.
        # Critério de ordenação:
        #  1º - idConjunto;
        #  2º - idFeicao;
        #  3° - id.

        if self.featureId < segmento.featureId:
            return -1
        elif self.featureId > segmento.featureId:
            return 1
        else:
            if self.setId < segmento.setId:
                return -1
            elif self.setId > segmento.setId:
                return 1
            else:
                if self.id < segmento.id:
                    return -1
                elif self.id > segmento.id:
                    return 1
