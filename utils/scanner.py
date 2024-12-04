import functools
from decimal import Decimal
from typing import Optional

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
        if not self.segments:
            self.segments.append(segment)
            return

        start = 0
        end = len(self.segments) - 1
        while start <= end:
            middle = (start + end) // 2
            item = self.segments[middle]
            comp = segment.compareTo(item)

            if comp < 0:
                if middle == 0 or start == end:
                    self.segments.insert(middle, segment)
                    return
                end = middle - 1

            elif comp > 0:
                if start >= end:
                    self.segments.append(segment)
                    return
                start = middle + 1

            else:
                return


class Scanner:
    def __init__(self, geo: Geometry) -> None:
        self.geo = geo
        self.lines: list[ScanLine] = []
        self.vertices: list[ScanVertex] = []

    def next(self) -> Optional[ScanLine]:
        result = None
        if self.lines:
            result = self.lines[-1]
            self.lines.pop()
        return result

    def nextInLine(self, scanLine: Decimal) -> Optional[ScanVertex]:
        result = None

        start = 0
        end = len(self.vertices) - 1
        while start <= end:
            middle = (start + end) // 2
            item = self.vertices[middle]
            comp = self.scanLineComparator(scanLine, item.vertex)

            if comp == 0:
                result = self.vertices[middle]
                self.vertices.pop(middle)
                break

            if comp < 0:
                if middle <= start:
                    break
                end = middle - 1

            else:
                if middle >= end:
                    break
                start = middle + 1

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

    def add(self, line: ScanLine) -> None:
        if not self.lines:
            self.lines.append(line)
            return

        start = 0
        end = len(self.lines) - 1
        while start <= end:
            middle = (start + end) // 2
            item = self.lines[middle]
            comp = self.scanLineComparator2(line, item)

            if comp > 0:
                if start == middle:
                    self.lines.insert(middle, line)
                    return
                if middle <= 0:
                    self.lines.insert(0, line)
                    return
                end = middle - 1

            elif comp < 0:
                if end == middle:
                    if middle == len(self.lines) - 1:
                        self.lines.append(line)
                        return
                    self.lines.insert(middle + 1, line)
                    return
                start = middle + 1

            else:  # item já existe. nada a fazer.
                return

        self.lines.append(line)

    def scanLineComparator(self, scanLine: Decimal, vertex: Vertex) -> int:
        if not vertex.withinTolerance(scanLine, self.geo.tolerance):
            return -1 if self.geo.smallerThan(scanLine, vertex.x) else 1
        return 0

    def scanLineComparator2(self, a: ScanLine, b: ScanLine) -> int:
        if self.geo.smallerThan(a.vertex.x, b.vertex.x):
            return -1
        if self.geo.smallerThan(b.vertex.x, a.vertex.x):
            return 1
        if a.eventType == b.eventType:
            if all(
                [
                    a.segmentA.segmentId == b.segmentA.segmentId,
                    a.segmentA.featureId == b.segmentA.featureId,
                    a.segmentA.setId == b.segmentA.setId,
                    a.segmentB
                    and b.segmentB
                    and a.segmentB.segmentId == b.segmentB.segmentId
                    and a.segmentB.featureId == b.segmentB.featureId
                    and a.segmentB.setId == b.segmentB.setId,
                ]
            ):
                return 0
            if self.geo.smallerThan(a.vertex.y, b.vertex.y):
                return -1
            if self.geo.smallerThan(b.vertex.y, a.vertex.y):
                return 1
            if self.geo.compareAngles(a.segmentA, b.segmentA) >= 0:
                return 1
            return -1
        if (
            a.eventType == 0
            and b.eventType == 1
            or a.eventType == 0
            and b.eventType == 2
            or a.eventType == 2
            and b.eventType == 1
        ):
            return -1
        if (
            a.eventType == 1
            and b.eventType == 0
            or a.eventType == 1
            and b.eventType == 2
            or a.eventType == 2
            and b.eventType == 0
        ):
            return 1
        return 0

    def scanLineSorter(self, a: ScanLine, b: ScanLine) -> int:
        if self.geo.smallerThan(b.vertex.x, a.vertex.x):
            return -1
        if self.geo.posEqualsTo(a.vertex.x, b.vertex.x):
            if a.eventType == 0 and b.eventType == 0:
                if self.geo.smallerThan(b.vertex.y, a.vertex.y):
                    return -1
            elif a.eventType == 1 and b.eventType == 1:
                if self.geo.smallerThan(
                    b.segmentA.getSmallerX(self.geo.tolerance),
                    a.segmentA.getSmallerX(self.geo.tolerance),
                ):
                    return -1
            elif (
                a.eventType == 1
                and b.eventType == 0
                or a.eventType == 2
                and b.eventType == 1
                or a.eventType == 0
                and b.eventType == 2
            ):
                return -1
        return 1

    def sortLines(self) -> None:
        self.lines.sort(key=functools.cmp_to_key(self.scanLineSorter))

    def createScanPoint(
        self, vertex: Vertex, segmentA: Segment, segmentB: Optional[Segment] = None
    ) -> ScanVertex:
        pontoV = Vertex(x=vertex.x, y=vertex.y)
        scanPoint = ScanVertex(pontoV, segmentA)
        if segmentB:
            scanPoint.insertSegment(segmentB)
        return scanPoint

    def scanPointComparator(self, primeiro: Vertex, segundo: Vertex) -> int:
        if self.geo.equalsTo(primeiro, segundo):
            return 0

        if self.geo.posEqualsTo(primeiro.x, segundo.x):
            if self.geo.smallerThan(primeiro.y, segundo.y):
                return -1
            return 1  # y do primeiro > y do segundo.

        # x do primeiro > x do segundo.
        return -1 if self.geo.smallerThan(primeiro.x, segundo.x) else 1

    def addScanPoint(self, scanLine: ScanLine) -> None:
        scanPoint = self.createScanPoint(
            scanLine.vertex, scanLine.segmentA, scanLine.segmentB
        )

        if not self.vertices:
            self.vertices.append(scanPoint)
            return

        start = 0
        end = len(self.vertices) - 1
        while start <= end:
            middle = (start + end) // 2
            item = self.vertices[middle]
            comp = self.scanPointComparator(scanPoint.vertex, item.vertex)

            if comp == 0:
                item.insertSegment(scanLine.segmentA)
                if scanLine.segmentB:
                    item.insertSegment(scanLine.segmentB)
                return

            if comp < 0:
                if middle == 0 or start == end:
                    self.vertices.insert(middle, scanPoint)
                    return
                end = middle - 1

            if comp > 0:
                if middle == len(self.vertices) - 1:
                    self.vertices.append(scanPoint)
                    return
                if start == end:
                    self.vertices.insert(middle + 1, scanPoint)
                    return
                start = middle + 1
