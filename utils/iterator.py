import functools
from typing import Optional

from qgis.core import Qgis, QgsMessageLog

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
        if self.segments:
            for i in range(max(0, start), min(len(self.segments) - 1, end)):
                item = self.segments[i]
                comp = segment.compareTo(item)

                if comp == 0:
                    return

                if comp < 0:
                    self.segments.insert(i, segment)
                    return

        self.segments.insert(min(len(self.segments), end) + 1, segment)


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
            QgsMessageLog.logMessage(
                f"Adicionando items do iterator para {feature}",
                "HydroFlow",
                Qgis.MessageLevel.Info,
            )

            if checkFlag and not feature.process:
                continue

            for segment in feature.segmentsList:
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
        if self.geo.equalsTo(aX=a.point.x, bX=b.point.x):
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

    def iteratorRowXComparator(self, iteratorLine: float, point: Vertex) -> int:
        if point.withinIteratorRow(iteratorLine, self.geo.tolerance):
            return 0

        if self.geo.smallerThan(iteratorLine, point.x):
            return -1
        return 1

    def sortRows(self) -> None:
        self.rows.sort(key=functools.cmp_to_key(self.iteratorRowSorter))

    def createIteratorPoint(
        self, ponto: Vertex, segmentoA: Segment, segmentoB: Optional[Segment] = None
    ) -> IteratorPoint:
        pontoV = Vertex(ponto.x, ponto.y)
        iteratorPoint = IteratorPoint(pontoV, segmentoA)
        if segmentoB:
            iteratorPoint.insertSegment(segmentoB)
        return iteratorPoint

    def iteratorPointComparator(self, primeiro: Vertex, segundo: Vertex) -> int:
        if not self.geo.equalsTo(a=primeiro, b=segundo):
            if self.geo.equalsTo(aX=primeiro.x, bX=segundo.x):
                if self.geo.smallerThan(primeiro.y, segundo.y):
                    return -1
                return 1  # y do primeiro > y do segundo.
            if self.geo.smallerThan(primeiro.x, segundo.x):
                return -1
            return 1  # x do primeiro > x do segundo.
        return 0

    def addIteratorPoint(self, iteratorRow: IteratorRow) -> None:
        iteratorPoint = self.createIteratorPoint(
            iteratorRow.point, iteratorRow.segmentA, iteratorRow.segmentB
        )

        if self.points:
            for i, item in enumerate(self.points):
                comp = self.iteratorPointComparator(iteratorRow.point, item.point)

                if comp == 0:
                    # QgsMessageLog.logMessage(
                    #     "Ponto de varredura já existe!",
                    #     "HydroFlow",
                    #     Qgis.MessageLevel.Info,
                    # )
                    item.insertSegment(iteratorRow.segmentA)
                    if iteratorRow.segmentB:  # Interseção.
                        item.insertSegment(iteratorRow.segmentB)
                    return

                if comp < 0:
                    # QgsMessageLog.logMessage(
                    #     (
                    #         f"Ponto de varredura menor! Inserido no índice {i} "
                    #         f"de {len(self.points)}!"
                    #     ),
                    #     "HydroFlow",
                    #     Qgis.MessageLevel.Info,
                    # )
                    self.points.insert(i, iteratorPoint)
                    return

        # QgsMessageLog.logMessage(
        #     (
        #         f"Ponto de varredura é maior que os existentes. "
        #         f"Inserido no índice {len(self.points)}!"
        #     ),
        #     "HydroFlow",
        #     Qgis.MessageLevel.Info,
        # )
        self.points.append(iteratorPoint)

    def searchIteratorPoint(self, iteratorLine: float) -> Optional[IteratorPoint]:
        for i, item in enumerate(self.points):
            if self.iteratorRowXComparator(iteratorLine, item.point) == 0:
                return self.points.pop(i)
        return None
