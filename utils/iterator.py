from typing import Optional

from ..models.feature import Feature
from ..models.segment import Segment
from ..models.vertex import Vertex
from .geometry import Geometry


class IteratorRow:
    def __init__(
        self,
        point: Vertex,
        event_type: int,
        segmentA: Segment,
        segmentB: Optional[Segment] = None,
    ) -> None:
        self.point = point
        self.eventType = event_type
        self.segmentA = segmentA
        self.segmentB = segmentB


class IteratorPoint:
    def __init__(self, point: Vertex, segment: Segment) -> None:
        self.point = point
        self.segments = [segment]

    def insertSegment(self, segment: Segment, start: int = 0, end: int = 0) -> None:
        if end == 0:
            end = len(self.segments)

        if start < end:
            # Obtendo o registro central.
            middle = round((start + end) / 2)
            item = self.segments[middle]

            # Comparando os segmentos.
            comp = segment.compareTo(item)

            # Segmento menor que item central.
            if comp < 0:
                if middle == 0 or start == end:
                    self.segments.append(segment)
                else:
                    self.insertSegment(segment, 0, (middle - 1))

            # Segmento maior que item central.
            elif comp > 0:
                if start < end:
                    self.insertSegment(segment, (middle + 1), end)
                else:
                    self.segments.append(segment)


class Iterator:
    def __init__(self, geo: Geometry) -> None:
        self.geo = geo
        self.rows: list[IteratorRow] = []
        self.points: list[IteratorPoint] = []

    def cleanup(self) -> None:
        self.rows = []
        self.points = []

    def next(self) -> Optional[IteratorRow]:
        if self.rows:
            return self.rows.pop()
        return None

    def addRows(self, features: list[Feature], checkFlag=False) -> None:
        for feature in features:
            if checkFlag and not feature.process:
                continue

            for segment in feature.segments_list:
                self.rows.append(
                    IteratorRow(
                        point=Vertex(x=segment.a.x, y=segment.a.y),
                        segmentA=segment,
                        event_type=0,
                    )
                )
                self.rows.append(
                    IteratorRow(
                        point=Vertex(x=segment.b.x, y=segment.b.y),
                        segmentA=segment,
                        event_type=1,
                    )
                )

    def iteratorRowSorter(self, a: IteratorRow, b: IteratorRow) -> int:
        # Avaliando o indice do item de varredura.
        if self.geo.smallerThan(b.point.x, a.point.x):  # Índice menor primeiro
            return 1
        if self.geo.equalsTo(a.point.x, b.point.x):
            # Avaliando o tipo dos eventos
            if a.eventType == 0 and b.eventType == 0:  # São do mesmo tipo: entrada!
                # Avaliando altura na linha de varredura (y).
                return 1 if self.geo.smallerThan(b.point.y, a.point.y) else -1
            if a.eventType == 1 and b.eventType == 1:  # São do mesmo tipo: saída!
                xA = a.segmentA.getSmallerX(self.geo.tolerance)
                xB = b.segmentA.getSmallerX(self.geo.tolerance)
                return (
                    1 if self.geo.smallerThan(xB, xA) else -1
                )  # Entra depois, sai depois!

        # São de tipos diferentes!
        return 1 if a.eventType == b.eventType else -1

    def iteratorRowComparator(self, iteratorRow: float, point: Vertex) -> int:
        if point.withinIteratorRow(iteratorRow, self.geo.tolerance):
            if self.geo.smallerThan(iteratorRow, point.x):
                return -1
            return 1
        return 0

    def sortRows(self) -> None:
        self.rows.sort(self.iteratorRowSorter)  # TODO: bad comparator

    def createIteratorPoint(
        self, ponto: Vertex, segmentoA: Segment, segmentoB: Optional[Segment] = None
    ) -> IteratorPoint:
        pontoV = Vertex(ponto.x, ponto.y)
        iteratorPoint = IteratorPoint(pontoV, segmentoA)
        if segmentoB:
            iteratorPoint.insertSegment(segmentoB)
        return iteratorPoint

    def iteratorPointComparator(self, primeiro: Vertex, segundo: Vertex) -> int:
        if self.geo.equalsTo(a=primeiro, b=segundo):
            if self.geo.equalsTo(aX=primeiro.x, bX=segundo.x):
                if self.geo.smallerThan(primeiro.y, segundo.y):
                    return -1
                return 1  # y do primeiro > y do segundo.
            if self.geo.smallerThan(primeiro.x, segundo.x):
                return -1
            return 1  # x do primeiro > x do segundo.
        return 0

    def addIteratorPoint(
        self,
        iteratorRow: IteratorRow,
        start: int = 0,
        end: int = 0,
    ) -> None:
        iteratorPoint = self.createIteratorPoint(
            iteratorRow.point, iteratorRow.segmentA, iteratorRow.segmentB
        )
        if len(self.points) == 0:
            self.points.append(iteratorPoint)
        elif end == 0:
            end = len(self.points)

        if start < end:
            # Obtendo o registro central.
            middle = round((start + end) / 2)
            item = self.points[middle]

            # Comparando os pontos.
            comp = self.iteratorPointComparator(iteratorRow.point, item.point)

            if comp == 0:  # São iguais.
                # Inserindo os segmentos no ponto de varredura existente.
                item.insertSegment(iteratorRow.segmentA)
                if iteratorRow.segmentB:  # Interseção.
                    item.insertSegment(iteratorRow.segmentB)
            elif comp < 0:  # Ponto < Ponto do meio (incluir antes).
                if middle == 0 or start == end:
                    self.points.insert(middle, iteratorPoint)
                else:
                    self.addIteratorPoint(iteratorRow, 0, (middle - 1))
            elif comp > 0:  # Ponto > Ponto do meio (incluir depois).
                if middle == (len(self.points) - 1):  # Ultimo registro.
                    self.points.append(iteratorPoint)
                elif start == end:
                    self.points.insert((middle + 1), iteratorPoint)
                else:
                    self.addIteratorPoint(iteratorRow, (middle + 1), end)

    def searchIteratorPoint(
        self, start: int, end: int, iteratorRow: float
    ) -> Optional[IteratorPoint]:
        if start <= end:
            # Calculando o meio (indice).
            middle = round((start + end) / 2)

            # Lendo o registro do meio.
            item = self.points[middle]

            # Analisando a linha de varredura do registro do meio.
            comp = self.iteratorRowComparator(iteratorRow, item.point.y)

            if comp == 0:  # Encontrou!
                self.points.pop(middle)
                return item
            if (
                comp < 0
            ):  # Linha de varredura é menor que a ordenada do ponto do meio.
                if middle > 0:
                    return self.searchIteratorPoint(0, (middle - 1), iteratorRow)
            else:  # Linha de varredura é maior que a ordenada do ponto do meio.
                if middle < (len(self.points) - 1):
                    return self.searchIteratorPoint(
                        (middle + 1), (len(self.points) - 1), iteratorRow
                    )

        return None
