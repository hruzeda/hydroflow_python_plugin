class Node:
    def __init__(self, featureId):
        self.featureId = featureId
        self.flow = 0
        self.strahler = 0
        self.shreve = 0
        self.children = []
        self.strahlerValues = []

    def addChild(self, node: "Node") -> None:
        if node != 0:
            self.children.append(node)

            # Incluindo valor de Strahler.
            self.strahlerValues.append(node.strahler)

            # Calculando o valor de Shreve.
            # shreve = shreve + no.getShreve()
