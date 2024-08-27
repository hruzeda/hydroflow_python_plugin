from math import sqrt
from typing import Optional

from ..models.segment import Segment
from ..models.vertex import Vertex


class Geometry:
    def __init__(self, tolerance=0):
        self.tolerance = tolerance

    def smallerThan(self, a, b):
        return a + self.tolerance < b

    def greaterThan(self, a, b):
        return a - self.tolerance > b

    def equalsTo(
        self,
        a: Optional[Vertex] = None,
        b: Optional[Vertex] = None,
        aX: Optional[float] = None,
        bX: Optional[float] = None,
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
        if aX and bX:
            return abs(aX - bX) <= self.tolerance
        return False

    def intersection(self, primeiro: Segment, segundo: Segment) -> Optional[Vertex]:
        """
        Retorna valor booleano, indicando se existe ou não interseção entre
        os segmentos. Caso exista, o ponto de interseção e passado em "I".
        """
        # Calculando s e t;
        denon = (segundo.b.x - segundo.a.x) * (primeiro.b.y - primeiro.a.y) - (
            segundo.b.y - segundo.a.y
        ) * (primeiro.b.x - primeiro.a.x)
        if abs(denon) > self.tolerance:
            s = (
                (segundo.b.x - segundo.a.x) * (segundo.a.y - primeiro.a.y)
                - (segundo.b.y - segundo.a.y) * (segundo.a.x - primeiro.a.x)
            ) / denon
            t = (
                (primeiro.b.x - primeiro.a.x) * (segundo.a.y - primeiro.a.y)
                - (primeiro.b.y - primeiro.a.y) * (segundo.a.x - primeiro.a.x)
            ) / denon

            # Verificando se há interseção.
            if (s > -self.tolerance and s < (1 + self.tolerance)) and (  # pylint: disable=chained-comparison
                t > -self.tolerance and t < (1 + self.tolerance)  # pylint: disable=chained-comparison
            ):
                x = primeiro.a.x + (s * (primeiro.b.x - primeiro.a.x))
                y = primeiro.a.y + (s * (primeiro.b.y - primeiro.a.y))
                return Vertex(x, y)
        return None

    def calculateRelativePoint(self, x: float, segment: Segment) -> Vertex:
        p = None
        a = segment.a
        b = segment.b

        # o segmento é vertical. Retorna o vértice com o menor "y"!
        if segment.isVertical(self.tolerance) or a.withinIteratorRow(
            x, self.tolerance
        ):
            p = Vertex(a.x, a.y)
        else:  # o segmento não é vertical.
            if b.withinIteratorRow(
                x, self.tolerance
            ):  # A linha de varredura "x" intercepta o vértice "b".
                p = Vertex(b.x, b.y)
            else:
                # Calculando o ponto relativo.
                # Para a.x < b.x
                # double dx = b.x - a.x;
                # double dy = b.y - a.y;
                # double  t = (x - a.x) / dx;
                # y = (t * dy) + p.x;
                # ou
                # y = (((x - a.x) / (b.x - a.x)) * (b.y - a.y)) + a.y;
                y = (((x - a.x) / (b.x - a.x)) * (b.y - a.y)) + a.y
                p = Vertex(x, y)
        return p

    def compare(self, a: float, b: float) -> int:
        if self.smallerThan(a, b):
            return -1
        if self.greaterThan(a, b):
            return 1
        return 0

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
        if comp > 0:
            return -1
        return 0

    def subtract(self, a: Vertex, b: Vertex) -> Vertex:
        """
        Subtrai das coordenadas de "a" as coordenadas de "b".
        """
        return Vertex(a.x - b.x, a.y - b.y)
