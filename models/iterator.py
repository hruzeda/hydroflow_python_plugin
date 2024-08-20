from typing import Optional

from models.feature import Feature
from models.segment import Segment
from models.vertex import Vertex
from utils.geometry import Geometry


class IteratorRow:
    def __init__(
        self,
        point: Optional[Vertex] = None,
        event_type=-1,
        segmentA: Optional[Segment] = None,
        segmentB: Optional[Segment] = None,
    ):
        self.point = point
        self.eventType = event_type
        self.segmentA = segmentA
        self.segmentB = segmentB

    def cleanup(self):
        self.point = None
        self.eventType = -1
        self.segmentA = None
        self.segmentB = None


class IteratorPoint:
    def __init__(self, x=-1, y=-1, z=-1):
        self.x = x
        self.y = y
        self.z = z

    def cleanup(self):
        self.x = -1
        self.y = -1
        self.z = -1


class Iterator:
    def __init__(self, geo: Geometry):
        self.geo = geo
        self.rows: list[IteratorRow] = []
        self.points: list[IteratorPoint] = []

    def next(self):
        if len(self.rows) == 0:
            return self.rows.pop()

    def addRows(self, features: list[Feature], checkFlag=False):
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

    def iteratorRowComparator(self, a: IteratorRow, b: IteratorRow):
        # Avaliando o indice do item de varredura.
        if self.geo.smallerThan(b.point.x, a.point.x):  # Índice menor primeiro
            return True
        elif self.geo.equalsTo(a.point.x, b.point.x):
            # Avaliando o tipo dos eventos
            if a.eventType == 0 and b.eventType == 0:  # São do mesmo tipo: entrada!
                # Avaliando altura na linha de varredura (y).
                if self.geo.smallerThan(b.point.y, a.point.y):
                    return True
            elif a.eventType == 1 and b.eventType == 1:  # São do mesmo tipo: saída!
                xA = a.segmentA.getSmallerX(self.geo.tolerance)
                xB = b.segmentA.getSmallerX(self.geo.tolerance)
                if self.geo.smallerThan(xB, xA):
                    return True  # Entra depois, sai depois!

        # São de tipos diferentes!
        return a.eventType != b.eventType

    def sortRows(self) -> None:
        self.rows.sort(self.iteratorRowComparator)

    def cleanup(self):
        self.geo = None

        for line in self.rows:
            line.cleanup()
        self.rows = []

        for point in self.points:
            point.cleanup()
        self.points = []
