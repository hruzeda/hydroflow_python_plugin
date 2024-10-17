from decimal import Decimal
from typing import Optional

from ..utils.geometry import Geometry
from ..utils.message import Message
from .segment import Segment


class Position:
    def __init__(self, geo: Geometry, log: Message) -> None:
        self.geo = geo
        self.log = log
        self.list: list[Segment] = []

    def locate(self, scanLine: Decimal, segment: Segment) -> int:
        start = 0
        end = len(self.list) - 1
        while start <= end:
            middle = (start + end) // 2
            item = self.list[middle]

            if segment.compareTo(item) == 0:
                return middle
            comparison = self.comparePosition(scanLine, segment, item)
            if comparison < 0:
                start = middle + 1
            else:
                end = middle - 1

        return -1

    def comparePosition(
        self, scanLine: Decimal, first: Segment, second: Segment
    ) -> int:
        # Calculando os pontos relativos.
        pFirst = self.geo.calculateRelativePoint(scanLine, first)
        pSecond = self.geo.calculateRelativePoint(scanLine, second)

        if self.geo.equalsTo(pFirst, pSecond):
            # Mesma altura relativa.

            # Avaliando os vértices.
            if any(
                [
                    first.isPoint(self.geo.tolerance),
                    second.isPoint(self.geo.tolerance),
                ]
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
                    return result
                return self.geo.compare(first.a.y, second.a.y)

            # Testando casos 6 e 7.
            if self.geo.equalsTo(pFirst, first.b) and (
                self.geo.equalsTo(first.b, second.b)
                or (
                    not self.geo.equalsTo(pSecond, second.a)
                    and not self.geo.equalsTo(pSecond, second.b)
                )
            ):
                # Caso 6.
                # Determinando a linha de varredura e comparando os segmentos.
                return self.comparePosition(
                    first.a.x
                    if self.geo.greaterThan(first.a.x, second.a.x)
                    else second.a.x,
                    first,
                    second,
                )

            # Tratando o caso 8.
            if (
                not self.geo.equalsTo(pFirst, first.a)
                and not self.geo.equalsTo(pFirst, first.b)
                and not self.geo.equalsTo(pSecond, second.a)
                and not self.geo.equalsTo(pSecond, second.b)
            ):
                # Comparando invertido por ser interseção.
                return self.geo.compareAngles(second, first)

            # Tratando os casos 4 e 5.
            return self.geo.compareAngles(first, second)

        # Alturas relativas diferentes.
        return self.geo.compare(pFirst.y, pSecond.y)

    def insert(self, segment: Segment) -> int:
        if not self.list:
            self.list.append(segment)
            return 0

        start = 0
        end = len(self.list) - 1
        while True:
            middle = (start + end) // 2
            item = self.list[middle]
            comp = self.comparePosition(segment.a.x, segment, item)

            if comp < 0:
                if middle == end:
                    if middle == len(self.list) - 1:
                        self.list.append(segment)
                        return len(self.list) - 1
                    self.list.insert(middle + 1, segment)
                    return middle + 1
                start = middle + 1
            elif comp > 0:
                if middle == start:
                    self.list.insert(middle, segment)
                    return middle
                end = middle - 1
            else:
                return middle

    def delete(self, indice: int) -> None:
        if self.list and indice < len(self.list):
            self.list.pop(indice)

    def above(self, index: int) -> Optional[Segment]:
        if self.list and 0 < index < len(self.list):
            return self.list[index - 1]
        return None

    def below(self, index: int) -> Optional[Segment]:
        if self.list and index < len(self.list) - 1:
            return self.list[index + 1]
        return None

    def swap(self, first: int, second: int) -> None:
        self.list[first], self.list[second] = self.list[second], self.list[first]
