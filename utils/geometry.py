from decimal import Decimal
from math import sqrt
from typing import Optional

from ..models.segment import Segment
from ..models.vertex import Vertex


class Geometry:
    def __init__(self, tolerance: Decimal = Decimal(0)) -> None:
        self.tolerance = tolerance

    def smallerThan(self, a: Decimal, b: Decimal) -> bool:
        return a + self.tolerance < b

    def greaterThan(self, a: Decimal, b: Decimal) -> bool:
        return a - self.tolerance > b

    def equalsTo(
        self,
        a: Optional[Vertex] = None,
        b: Optional[Vertex] = None,
        aPos: Optional[Decimal] = None,
        bPos: Optional[Decimal] = None,
    ) -> bool:
        """
        Aplicação da equação reduzida da circunferência.
        Considerções:
             Vertice "a" é o centro da circunferência;
             Vertice "b" é o elemento em análise.
        Resposta:
             Verdadeiro se o vertice "b" está contido na circunferência com centro
             no vertice "a" e raio igual a tolerância.
        """
        if a and b:
            return sqrt(pow(b.x - a.x, 2) + pow(b.y - a.y, 2)) <= self.tolerance
        if aPos and bPos:
            return abs(aPos - bPos) <= self.tolerance
        return False

    def intersection(self, primeiro: Segment, segundo: Segment) -> Optional[Vertex]:
        """
        Retorna o ponto de interseção, se encontrado entre, os segmentos.
        """
        a = primeiro.a
        b = primeiro.b
        c = segundo.a
        d = segundo.b

        # Calculando o determinante.
        det = (d.x - c.x) * (b.y - a.y) - (d.y - c.y) * (b.x - a.x)

        if abs(det) > self.tolerance:
            s = ((d.x - c.x) * (c.y - a.y) - (d.y - c.y) * (c.x - a.x)) / det
            t = ((b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)) / det

            if self.tolerance * -1 < s < (
                1 + self.tolerance
            ) and self.tolerance * -1 < t < (1 + self.tolerance):
                return Vertex(x=a.x + (s * (b.x - a.x)), y=a.y + (s * (b.y - a.y)))
        return None

    def calculateRelativePoint(self, x: Decimal, segment: Segment) -> Vertex:
        # o segmento é vertical. Retorna o vértice com o menor "y"!
        if segment.isVertical(self.tolerance) or segment.a.withinTolerance(
            x, self.tolerance
        ):
            return Vertex(x=segment.a.x, y=segment.a.y)

        # o segmento não é vertical.
        if segment.b.withinTolerance(
            x, self.tolerance
        ):  # A linha de varredura "x" intercepta o vértice "b".
            return Vertex(x=segment.b.x, y=segment.b.y)

        # Calculando o ponto relativo.
        # Para a.x < b.x
        # double dx = b.x - a.x;
        # double dy = b.y - a.y;
        # double  t = (x - a.x) / dx;
        # y = (t * dy) + p.x;
        # ou
        # y = (((x - a.x) / (b.x - a.x)) * (b.y - a.y)) + a.y;
        y = (
            ((x - segment.a.x) / (segment.b.x - segment.a.x))
            * (segment.b.y - segment.a.y)
        ) + segment.a.y
        return Vertex(x=x, y=y)

    def compare(self, a: Decimal, b: Decimal) -> int:
        if self.smallerThan(a, b):
            return -1
        return 1 if self.greaterThan(a, b) else 0

    def compareAngles(self, first: Segment, second: Segment) -> int:
        """
        Compara o ângulo inclinação dos segmentos.
        Resposta:
                 -1 o ângulo do primeiro é menor que o ângulo do segundo segmento
                  0 o ângulo do primeiro é igual ao ângulo do segundo segmento
                  1 o ângulo do primeiro é maior que o ângulo do segundo segmento
        """
        a = self.subtract(first.b, first.a)
        b = self.subtract(second.b, second.a)

        # Comparando.
        comp = (a.x * b.y) - (b.x * a.y)

        if comp < 0:
            return 1
        return -1 if comp > 0 else 0

    def subtract(self, a: Vertex, b: Vertex) -> Vertex:
        """
        Subtrai das coordenadas de "a" as coordenadas de "b".
        """
        return Vertex(x=a.x - b.x, y=a.y - b.y)
