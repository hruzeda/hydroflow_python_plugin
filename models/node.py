class Node:
    def __init__(self, featureId: int) -> None:
        self.featureId = featureId
        self.flow = 0
        self.shreve = 0
        self.children: list[Node] = []
        self.strahlerValues: list[int] = []
        self._strahler = 0

    @property
    def strahler(self) -> int:
        if self.strahlerValues:
            self._strahler = self.calcularStrahler()
        return self._strahler

    @strahler.setter
    def strahler(self, value: int) -> None:
        self._strahler = value

    def addChild(self, node: "Node") -> None:
        self.children.append(node)

        # Incluindo valor de Strahler.
        self.strahlerValues.append(node.strahler)

        # Calculando o valor de Shreve.
        self.shreve = self.shreve + node.shreve

    def calcularStrahler(self) -> int:
        a = 0
        b = 0
        reg = 0

        # Selecionando os dois maiores valores.
        for i in self.strahlerValues:
            reg = i
            if reg > a:
                b = max(a, b)
                a = reg
            elif reg > b:
                b = reg

        # Calculando Strahler.
        if a == b:
            return a + 1
        if a > b:
            return a
        return b
