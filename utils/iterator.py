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
        i = start
        while i < min(end, len(self.segments)):
            item = self.segments[i]
            comp = segment.compareTo(item)

            if comp == 0:
                return
            if comp < 0:
                self.segments.insert(i, segment)
                return

            i += 1

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

    def iteratorRowSorter(self, a: IteratorRow) -> tuple[int, int]:
        # Avaliando o indice do item de varredura.
        result = a.point.x
        if a.eventType == 0:
            result += a.point.y
        if a.eventType == 1:
            result += a.segmentA.getSmallerX(self.geo.tolerance)
        return a.eventType, result

    def iteratorRowComparator(self, iteratorRow: float, point: Vertex) -> int:
        if point.withinIteratorRow(iteratorRow, self.geo.tolerance):
            if self.geo.smallerThan(iteratorRow, point.x):
                return -1
            return 1
        return 0

    def sortRows(self) -> None:
        self.rows.sort(key=self.iteratorRowSorter)

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

        i = start
        while i < min(end, len(self.points)):
            item = self.points[i]
            comp = self.iteratorPointComparator(iteratorRow.point, item.point)

            if comp == 0:  # São iguais.
                item.insertSegment(iteratorRow.segmentA)
                if iteratorRow.segmentB:  # Interseção.
                    item.insertSegment(iteratorRow.segmentB)
                return
            if comp < 0:
                self.points.insert(i, iteratorPoint)
                return

            i += 1

        self.points.append(iteratorPoint)

    def searchIteratorPoint(self, iteratorRow: float) -> Optional[IteratorPoint]:
        for i, item in enumerate(self.points):
            if self.iteratorRowComparator(iteratorRow, item.point) == 0:
                return self.points.pop(i)
        return None
