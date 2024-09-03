from typing import Optional

from ..utils.geometry import Geometry
from ..utils.message import Message
from .segment import Segment


class Position:
    def __init__(self, geo: Geometry, log: Message) -> None:
        self.geo = geo
        self.log = log
        self.list: list[Segment] = []

    # def cleanup(self) -> None:
    #     self.list.clear()

    def delete(self, indice: int) -> None:
        if self.list and indice < len(self.list):
            self.list.pop(indice)

    def locate(self, scanLine: float, segment: Segment) -> int:
        for i, item in enumerate(self.list):
            if self.comparePosition(scanLine, segment, item) == 0:
                return i
        return -1

    def comparePosition(
        self, scanLine: float, first: Segment, second: Segment
    ) -> int:
        # Calculando os pontos relativos.
        pFirst = self.geo.calculateRelativePoint(scanLine, first)
        pSecond = self.geo.calculateRelativePoint(scanLine, second)

        if self.geo.equalsTo(pFirst, pSecond):
            # Mesma altura relativa.

            # Avaliando os vértices.
            if first.isPoint(self.geo.tolerance) or second.isPoint(
                self.geo.tolerance
            ):
                return first.compareTo(second)

            if (
                self.geo.equalsTo(pFirst, first.a)
                and self.geo.equalsTo(first.a, second.b)
            ) or (
                self.geo.equalsTo(pSecond, second.a)
                and self.geo.equalsTo(first.b, second.a)
            ):
                # Primeiro entrando ou saindo.

                # Tratando os casos 1 e 2.
                if self.geo.equalsTo(aPos=first.a.y, bPos=second.a.y):
                    result = self.geo.compareAngles(first, second)
                    if result == 0:
                        # Tratando o caso 1 (segmentos horizontais). Arbitrei!
                        return self.geo.compare(first.a.x, second.a.x)
                else:
                    return self.geo.compare(first.a.y, second.a.y)

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
                if self.geo.greaterThan(first.a.x, second.a.x):
                    scanLine = first.a.x
                else:
                    scanLine = second.a.x

                # Comparando os segmentos.
                return self.comparePosition(scanLine, first, second)

            # Tratando o caso 8.
            elif (
                not self.geo.equalsTo(pFirst, first.a)
                and not self.geo.equalsTo(pFirst, first.b)
                and not self.geo.equalsTo(pSecond, second.a)
                and not self.geo.equalsTo(pSecond, second.b)
            ):
                # Comparando invertido por ser interseção.
                return self.geo.compareAngles(second, first)

            # Tratando os casos 4 e 5.
            else:
                return self.geo.compareAngles(first, second)
        else:
            # Alturas relativas diferentes.
            return self.geo.compare(pFirst.y, pSecond.y)
        return 0

    def insert(self, segment: Segment) -> int:
        for i, item in enumerate(self.list):
            comp = self.comparePosition(segment.a.x, segment, item)

            if comp == 0:
                return i

            if comp < 0:
                self.list.insert(i, segment)
                return i

        self.list.append(segment)
        return len(self.list) - 1

    def above(self, index: int) -> Optional[Segment]:
        result = None
        if 0 < index < len(self.list):
            index -= 1
            result = self.list[index]
        return result

    def below(self, index: int) -> Optional[Segment]:
        result = None
        if 0 <= index < len(self.list) - 1:
            index += 1
            result = self.list[index]
        return result

    def swap(self, first: int, second: int) -> None:
        self.list[first], self.list[second] = self.list[second], self.list[first]
