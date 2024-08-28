import functools
from typing import Optional

from qgis.core import Qgis, QgsMessageLog

from ..models.feature import Feature
from ..models.segment import Segment
from ..models.vertex import Vertex
from .geometry import Geometry


class ScanLine:
    def __init__(
        self,
        vertex: Vertex,
        eventType: int,
        segmentA: Segment,
        segmentB: Optional[Segment] = None,
    ) -> None:
        self.vertex = vertex
        self.eventType = eventType
        self.segmentA = segmentA
        self.segmentB = segmentB


class ScanVertex:
    def __init__(self, vertex: Vertex, segment: Segment) -> None:
        self.vertex = vertex
        self.segments = [segment]

    def insertSegment(self, segment: Segment) -> None:
        for item in self.segments:
            comp = segment.compareTo(item)

            if comp == 0:
                return

            if comp < 0:
                self.segments.insert(comp, segment)
                return

        self.segments.append(segment)


class Scanner:
    def __init__(self, geo: Geometry) -> None:
        self.geo = geo
        self.lines: list[ScanLine] = []
        self.vertices: list[ScanVertex] = []

    # def cleanup(self) -> None:
    #     self.lines = []
    #     self.points = []

    def next(self) -> Optional[ScanLine]:
        if self.lines:
            return self.lines.pop()
        return None

    def nextInLine(self, previousPoint: Vertex) -> Optional[ScanVertex]:
        result = None
        for i, item in enumerate(self.vertices):
            if item.vertex.withinTolerance(previousPoint, self.geo.tolerance):
                result = self.vertices.pop(i)
                break
        return result

    def addLines(self, features: list[Feature]) -> None:
        for feature in features:
            if not feature.process:
                continue

            for segment in feature.segmentsList:
                self.lines.append(
                    ScanLine(
                        vertex=Vertex(x=segment.a.x, y=segment.a.y),
                        segmentA=segment,
                        eventType=0,
                    )
                )
                self.lines.append(
                    ScanLine(
                        vertex=Vertex(x=segment.b.x, y=segment.b.y),
                        segmentA=segment,
                        eventType=1,
                    )
                )

    def scanLineSorter(self, a: ScanLine, b: ScanLine) -> int:
        if self.geo.equalsTo(aX=a.vertex.x, bX=b.vertex.x):
            # Avaliando o tipo dos eventos
            if a.eventType == 0 and b.eventType == 0:  # São do mesmo tipo: entrada!
                # Avaliando altura na linha de varredura (y).
                return 1 if self.geo.smallerThan(b.vertex.y, a.vertex.y) else -1
            if a.eventType == 1 and b.eventType == 1:  # São do mesmo tipo: saída!
                xA = a.segmentA.getSmallerX(self.geo.tolerance)
                xB = b.segmentA.getSmallerX(self.geo.tolerance)
                return (
                    1 if self.geo.smallerThan(xB, xA) else -1
                )  # Entra depois, sai depois!

            return 1 if a.eventType == b.eventType else -1

        return 1 if self.geo.smallerThan(b.vertex.x, a.vertex.x) else -1

    def sortLines(self) -> None:
        self.lines.sort(key=functools.cmp_to_key(self.scanLineSorter))

    def createScanPoint(
        self, ponto: Vertex, segmentoA: Segment, segmentoB: Optional[Segment] = None
    ) -> ScanVertex:
        pontoV = Vertex(ponto.x, ponto.y)
        scanPoint = ScanVertex(pontoV, segmentoA)
        if segmentoB:
            scanPoint.insertSegment(segmentoB)
        return scanPoint

    def scanPointComparator(self, primeiro: Vertex, segundo: Vertex) -> int:
        if self.geo.equalsTo(a=primeiro, b=segundo):
            return 0

        if self.geo.equalsTo(aX=primeiro.x, bX=segundo.x):
            if self.geo.smallerThan(primeiro.y, segundo.y):
                return -1
            return 1  # y do primeiro > y do segundo.

        # x do primeiro > x do segundo.
        return -1 if self.geo.smallerThan(primeiro.x, segundo.x) else 1

    def addScanPoint(self, scanLine: ScanLine) -> None:
        scanPoint = self.createScanPoint(
            scanLine.vertex, scanLine.segmentA, scanLine.segmentB
        )

        for i, item in enumerate(self.vertices):
            comp = self.scanPointComparator(scanLine.vertex, item.vertex)

            if comp == 0:
                item.insertSegment(scanLine.segmentA)
                if scanLine.segmentB:  # Interseção.
                    item.insertSegment(scanLine.segmentB)
                return

            if comp < 0:
                self.vertices.insert(i, scanPoint)
                return

        self.vertices.append(scanPoint)
