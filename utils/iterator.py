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
        self.__init__()


class IteratorPoint:
    def __init__(self, x=-1, y=-1, z=-1):
        self.x = x
        self.y = y
        self.z = z
        self.segments: list[Segment] = []

    def cleanup(self):
        self.__init__()

    def insertSegment(
        self, segment: Segment, start: Optional[int] = 0, end: Optional[int] = 0
    ):
        if end == 0:
            end = len(self.segments)

        if start < end:
            # Obtendo o registro central.
            middle = round((start + end) / 2)
            item = self.segments[middle]

            # Comparando os segmentos.
            comp = segment.compararSegmentos(item)

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

    def iteratorRowSorter(self, a: IteratorRow, b: IteratorRow):
        # Avaliando o indice do item de varredura.
        if self.geo.smallerThan(b.point.x, a.point.x):  # Índice menor primeiro
            return 1
        elif self.geo.equalsTo(a.point.x, b.point.x):
            # Avaliando o tipo dos eventos
            if a.eventType == 0 and b.eventType == 0:  # São do mesmo tipo: entrada!
                # Avaliando altura na linha de varredura (y).
                return 1 if self.geo.smallerThan(b.point.y, a.point.y) else -1
            elif a.eventType == 1 and b.eventType == 1:  # São do mesmo tipo: saída!
                xA = a.segmentA.getSmallerX(self.geo.tolerance)
                xB = b.segmentA.getSmallerX(self.geo.tolerance)
                return (
                    1 if self.geo.smallerThan(xB, xA) else -1
                )  # Entra depois, sai depois!

        # São de tipos diferentes!
        return 1 if a.eventType == b.eventType else -1

    def iteratorRowComparator(self, iteratorRow: float, point: Vertex):
        if point.naLinhaDeVarredura(iteratorRow, self.geo.tolerance):
            if self.geo.smallerThan(iteratorRow, point.x):
                return -1
            return 1
        return 0

    def sortRows(self) -> None:
        self.rows.sort(self.iteratorRowSorter)

    def cleanup(self):
        self.geo = None

        for line in self.rows:
            line.cleanup()
        self.rows = []

        for point in self.points:
            point.cleanup()
        self.points = []

    def createIteratorPoint(
        self, ponto: Vertex, segmentoA: Segment, segmentoB: Optional[Segment] = None
    ):
        pontoV = Vertex(ponto.x, ponto.y)
        iteratorPoint = IteratorPoint(pontoV, segmentoA)
        if segmentoB:
            iteratorPoint.insertSegment(segmentoB)
        return iteratorPoint

    def iteratorPointComparator(self, primeiro: Vertex, segundo: Vertex):
        if self.geo.equalsTo(a=primeiro, b=segundo):
            if self.geo.equalsTo(aX=primeiro.x, bX=segundo.x):
                if self.geo.smallerThan(primeiro.y, segundo.y):
                    return -1
                else:  # y do primeiro > y do segundo.
                    return 1
            elif self.geo.smallerThan(primeiro.x, segundo.x):
                return -1
            else:  # x do primeiro > x do segundo.
                return 1
        return 0

    def addIteratorPoint(
        self, iteratorRow: IteratorRow, start: Optional[int] = 0, end: Optional[int] = 0
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
                    self.addIteratorPoint(iteratorPoint, 0, (middle - 1))
            elif comp > 0:  # Ponto > Ponto do meio (incluir depois).
                if middle == (len(self.points) - 1):  # Ultimo registro.
                    self.points.append(iteratorPoint)
                elif start == end:
                    self.points.insert((middle + 1), iteratorPoint)
                else:
                    self.addIteratorPoint(iteratorPoint, (middle + 1), end)

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
                iteratorPoint = item
                self.points.pop(middle)
            elif (
                comp < 0
            ):  # Linha de varredura é menor que a ordenada do ponto do meio.
                if middle > 0:
                    iteratorPoint = self.searchIteratorPoint(
                        0, (middle - 1), iteratorRow
                    )
            else:  # Linha de varredura é maior que a ordenada do ponto do meio.
                if middle < (len(self.points) - 1):
                    iteratorPoint = self.searchIteratorPoint(
                        (middle + 1), (len(self.points) - 1), iteratorRow
                    )

        return iteratorPoint
