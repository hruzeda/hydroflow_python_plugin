from models.segment import Segment
from utils.geometry import Geometry
from utils.message import Message


class Position:
    def __init__(self, geo: Geometry, log: Message):
        self.geo = geo
        self.log = log
        self.list = []

    def delete(self, indice: int) -> None:
        if indice < len(self.lista):
            self.list.pop(indice)

    def locate(self, linhaVarredura: float, segmento: Segment) -> int:
        return self.binarySearch(0, len(self.list) - 1, linhaVarredura, segmento)

    def binarySearch(
        self, start: int, end: int, iteratorRow: float, segment: Segment
    ) -> int:
        result = -1  # Não encontrou.

        if end < self.list.size() and start <= end:
            middle = round((start + end) / 2)
            segItem = self.list.at(middle)

            # Comparando segmento com item central.
            if segment.compareTo(segItem) == 0:
                result = middle
            else:
                # Avaliando as posições.
                comparison = self.comparePosition(iteratorRow, segment, segItem)

                if comparison == -1:  # segmento está abaixo.
                    result = self.binarySearch(middle + 1, end, iteratorRow, segment)
                else:  # comparacao = 1; segmento está acima.
                    result = self.binarySearch(start, middle - 1, iteratorRow, segment)

        return result

    def comparePosition(
        self, iteratorRow: float, first: Segment, second: Segment
    ) -> int:
        result = 0

        # Calculando os pontos relativos.
        pFirst = self.geo.calculateRelativePoint(iteratorRow, first)
        pSecond = self.geo.calculateRelativePoint(iteratorRow, second)

        if self.geo.equalsTo(pFirst, pSecond):
            # Mesma altura relativa.

            # Avaliando os vértices.
            if first.isPoint(self.geo.tolerance) or second.isPoint(self.geo.tolerance):
                result = first.compareTo(second)
            elif (
                self.geo.equalsTo(pFirst, first.a)
                and self.geo.equalsTo(first.a, second.b)
            ) or (
                self.geo.equalsTo(pSecond, second.a)
                and self.geo.equalsTo(first.b, second.a)
            ):
                # Primeiro entrando ou saindo.

                # Tratando os casos 1 e 2.
                if self.geo.equalsTo(first.a.y, second.a.y):
                    result = self.geo.compararAngulos(first, second)
                    if result == 0:
                        # Tratando o caso 1 (segmentos horizontais). Arbitrei!
                        result = self.geo.compararValores(first.a.x, second.a.x)
                else:
                    result = self.geo.compararValores(first.a.y, second.a.y)

            # Testando casos 6 e 7.
            elif (
                self.geo.equalsTo(pFirst, first.b)
                and self.geo.equalsTo(first.b, second.b)
            ) or (
                self.geo.equalsTo(pFirst, first.b)
                and not self.geo.equalsTo(pSecond, second.a)
                and not self.geo.equalsTo(pSecond, second.b)
            ):
                # Caso 6.

                # Determinando a linha de varredura.
                if self.geo.isGreater(first.a.x, second.a.x):
                    iteratorRow = first.a.x
                else:
                    iteratorRow = second.a.x

                # Comparando os segmentos.
                result = self.comparePosition(iteratorRow, first, second)

            # Tratando o caso 8.
            elif (
                not self.geo.equalsTo(pFirst, first.a)
                and not self.geo.equalsTo(pFirst, first.b)
                and not self.geo.equalsTo(pSecond, second.a)
                and not self.geo.equalsTo(pSecond, second.b)
            ):
                # Comparando invertido por ser interseção.
                result = self.geo.compararAngulos(second, first)

            # Tratando os casos 4 e 5.
            else:
                result = self.geo.compararAngulos(first, second)
        else:
            # Alturas relativas diferentes.
            result = self.geo.compararValores(pFirst.y, pSecond.y)

        return result
