from typing import Optional

from .models.feature_set import FeatureSet
from .models.node import Node
from .models.position import Position
from .models.relation import Relation
from .models.segment import Segment
from .models.vertex import Vertex
from .params import Params
from .utils.geometry import Geometry
from .utils.message import Message
from .utils.scanner import ScanLine, Scanner


class Classificator:
    def __init__(
        self,
        drainage: FeatureSet,
        boundary: FeatureSet,
        params: Params,
        log: Message,
    ) -> None:
        self.drainage = drainage
        self.boundary = boundary
        self.params = params
        self.geo = Geometry(params.toleranceXY)
        self.scanner = Scanner(self.geo)
        self.topologicalRelations = Relation(log)
        self.position = Position(self.geo, log)
        self.log = log

    # def cleanup(self):
    #     self.log.cleanup()
    #     self.geo = Geometry(self.params.toleranceXY)
    #     self.scanner = Scanner(self.geo)
    #     self.topologicalRelations.cleanup()
    #     self.position = Position(self.geo, self.log)

    def classifyWaterBasin(self) -> int:
        """
        Códigos de retorno:
        0 - Processamento concluído com sucesso!
        1 - Processamento concluído com alertas!
        2 - Foz não identificada.
        3 - Mais de uma foz identificada.
        4 - Feição com mais de dois afluentes.
        5 - Relações topológicas inesperadas! (listado no log)
        """
        result = 0

        # Montando a linha de varredura.
        self.buildScanner()

        # Varrendo o plano;
        self.scanPlane()

        # Verificando a existência de relações topológicas inesperadas
        # (toque e interseção).
        if self.topologicalRelations.err:
            # Listando os eventos estranhos.
            self.topologicalRelations.reportUnexpectedRelations(self.log)
            result = 5
        else:
            # Classificando a bacia hidrográfica.
            result = self.buildTree()

            # Validando o processamento das feições.
            if result == 0:
                result = self.evaluateProcessing()
        return result

    def buildScanner(self) -> None:
        self.scanner.addLines(self.drainage.featuresList)
        self.scanner.addLines(self.drainage.newFeaturesList)
        self.scanner.addLines(self.boundary.featuresList)
        self.scanner.sortLines()

    def scanPlane(self) -> None:
        scanLine = self.scanner.next()
        if scanLine:
            previousPoint = scanLine.vertex

        while scanLine is not None:
            record = scanLine.segmentA

            if previousPoint.x != scanLine.vertex.x:
                self.processScanPoints(previousPoint)
                previousPoint = scanLine.vertex

            # Inserir segmento(s) no ponto de varredura.
            self.scanner.addScanPoint(scanLine)

            # Processando o evento da linha de varredura.
            if scanLine.eventType == 0:  # Extremo esquerdo. Segmento entrando.
                # Inserindo em posição.
                index_A = self.position.insert(record)

                # Verificando segmento imediatamente acima.
                above = self.position.above(index_A)
                if above:  # Se há segmento acima:
                    self.evaluateSegments(scanLine.vertex, above, record)

                # Verificando segmento imediatamente abaixo.
                below = self.position.below(index_A)
                if below:  # Se há segmento abaixo:
                    self.evaluateSegments(scanLine.vertex, record, below)
            elif scanLine.eventType == 1:
                # Localizando o segmento em Posicao.
                index_A = self.position.locate(scanLine.vertex.x, record)

                # Verificando segmento imediatamente acima.
                above = self.position.above(index_A)
                if above:
                    # Verificando segmento imediatamente abaixo.
                    below = self.position.below(index_A)
                    if below:
                        self.evaluateSegments(scanLine.vertex, above, below)

                # Excluindo de posição.
                self.position.delete(index_A)
            elif scanLine.eventType == 2:  # Interseção.
                # Separando interseção por toque.
                if (
                    not self.geo.equalsTo(scanLine.vertex, scanLine.segmentA.a)
                    and not self.geo.equalsTo(scanLine.vertex, scanLine.segmentA.b)
                    and scanLine.segmentB
                    and not self.geo.equalsTo(scanLine.vertex, scanLine.segmentB.a)
                    and not self.geo.equalsTo(scanLine.vertex, scanLine.segmentB.b)
                ):
                    # Localizando os segmentos.
                    index_A = self.position.locate(
                        scanLine.vertex.x, scanLine.segmentA
                    )
                    index_B = self.position.locate(
                        scanLine.vertex.x, scanLine.segmentB
                    )

                    # Trocando segmentos de posição .
                    self.position.swap(index_A, index_B)

                    # Verificando segmento imediatamente acima.
                    above = self.position.above(index_A)
                    if above:  # Se há segmento acima:
                        self.evaluateSegments(
                            scanLine.vertex, above, scanLine.segmentB
                        )

                    # Verificando segmento imediatamente abaixo.
                    below = self.position.below(index_B)
                    if below:  # Se há segmento abaixo:
                        self.evaluateSegments(
                            scanLine.vertex, scanLine.segmentA, below
                        )

            scanLine = self.scanner.next()

        # Processando os pontos da ultima linha de varredura.
        self.processScanPoints(previousPoint)

    def evaluateSegments(
        self, point: Vertex, above: Segment, below: Segment
    ) -> None:
        intersectionPoint = self.geo.intersection(above, below)

        # Verificando se há interseção.
        if intersectionPoint:
            # Selecionando a área de interesse para o ponto de interseção.
            if (
                intersectionPoint.x >= (point.x - self.geo.tolerance)
                and intersectionPoint.y >= (point.y - self.geo.tolerance)
            ) or (
                intersectionPoint.x > (point.x + self.geo.tolerance)
                and intersectionPoint.y < (point.y - self.geo.tolerance)
            ):
                # Separando as interseções do tipo encosta.
                if not (
                    (
                        self.geo.equalsTo(intersectionPoint, above.a)
                        and self.geo.equalsTo(intersectionPoint, below.b)
                    )
                    or (
                        self.geo.equalsTo(intersectionPoint, above.b)
                        and self.geo.equalsTo(intersectionPoint, below.a)
                    )
                    or (
                        self.geo.equalsTo(intersectionPoint, above.a)
                        and self.geo.equalsTo(intersectionPoint, below.a)
                    )
                    or (
                        self.geo.equalsTo(intersectionPoint, above.b)
                        and self.geo.equalsTo(intersectionPoint, below.b)
                    )
                ):
                    # Inserindo a interseção na lista de varredura.
                    self.scanner.add(
                        ScanLine(
                            vertex=intersectionPoint,
                            segmentA=above,
                            segmentB=below,
                            eventType=2,
                        )
                    )

    def processScanPoints(self, previousVertex: Vertex) -> None:
        test = []

        # Obtendo o primeiro ponto de varradura.
        scanVertex = self.scanner.nextInLine(previousVertex.x)
        while scanVertex is not None:
            if len(scanVertex.segments) > 1:  # Há relações topológicas.
                # Testando os segmentos.
                for segment in scanVertex.segments:
                    test.append(
                        (
                            self.geo.equalsTo(scanVertex.vertex, segment.a)
                            and (segment.a.isExtremity() or segment.setId == 1)
                        )
                        or (
                            self.geo.equalsTo(scanVertex.vertex, segment.b)
                            and (segment.b.isExtremity() or segment.setId == 1)
                        )
                    )

                # Avaliando as relações topológicas.
                for i in range(len(scanVertex.segments) - 1):
                    j = i + 1

                    if test[i] and test[j]:  # Encosta.
                        self.topologicalRelations.addRelation(
                            scanVertex.segments[i],
                            scanVertex.segments[j],
                            0,
                        )
                    elif test[i] or test[j]:  # Toca.
                        self.topologicalRelations.addRelation(
                            scanVertex.segments[i],
                            scanVertex.segments[j],
                            1,
                        )
                    else:  # Intercepta.
                        self.topologicalRelations.addRelation(
                            scanVertex.segments[i],
                            scanVertex.segments[j],
                            2,
                        )

                test.clear()

            scanVertex = self.scanner.nextInLine(previousVertex.x)

    def buildTree(self) -> int:
        """
        Valores de retorno:
        0 - processamento correto
        2 - foz não identificada
        3 - mais de uma foz identificada
        4 - nó com mais de dois filhos
        5 - nó em loop
        6 - bacias interconectadas
        """
        result = 0

        if self.topologicalRelations.mouths:
            # Montando os índices dos eventos.
            self.topologicalRelations.buildIndexes()

            # Construindo a árvore que representa cada bacia.
            for mouthRelation in self.topologicalRelations.mouths:
                # origem: segmento da foz; destino: segmento do limite.
                result = self.createNodes(
                    mouthRelation.source,
                    mouthRelation.destination,
                    [],
                    result,
                )[0]
        else:
            result = 2  # Foz não identificada!!!

        return result

    def createNodes(
        self,
        segment: Segment,
        parent: Segment,
        sibling_nodes: list[Segment],
        result: int,
    ) -> tuple[int, Optional[Node]]:
        """
        Valores para resultado:
        0 - processamento sem erros
        4 - nó com mais de dois filhos
        5 - nó em loop
        6 - bacias interconectadas
        """
        node = None

        if result == 0:
            # Verificando a condição de interconexão entre árvores.
            loopBasin = False
            basinConnection = False
            currentFeature = self.drainage.getFeature(segment.featureId)

            if not currentFeature:
                return 0, None

            if segment.isMouth:
                # A feição corrente é a feição da foz e o segmento pai é do
                # limite da bacia. É o início do processamento de uma bacia!

                # Verificando se a feição da foz já foi processada.
                if currentFeature.mouthFeatureId < 0:
                    # Árvore ainda não processada.
                    currentFeature.mouthFeatureId = currentFeature.featureId
                else:
                    # Árvore já processada. Existe interconexão entre bacias!
                    basinConnection = True
            else:
                parentFeature = self.drainage.getFeature(parent.featureId)
                if parentFeature and currentFeature.mouthFeatureId < 0:
                    currentFeature.mouthFeatureId = parentFeature.mouthFeatureId
                else:
                    # Feição já processada. Existe um loop na árvore!
                    loopBasin = True

            # Verificando a condição de loop na árvore ou interconexão entre árvores.
            if not loopBasin and not basinConnection:
                node = Node(segment.featureId)

                # Processando o fluxo.
                if len(currentFeature.segmentsList) > 1:  # Vários segmentos.
                    if segment.segmentId == 0:
                        node.flow = 2  # Inverter!
                    else:
                        node.flow = 1  # Manter!
                else:  # Segmento único.
                    # Verificando se o vértice "a" do segmento encosta no pai.
                    if segment.a.equalsTo(parent.a) or segment.a.equalsTo(parent.b):
                        if segment.a.vertexId == 0:
                            node.flow = 2  # Inverter!
                        else:
                            node.flow = 1  # Manter!
                    else:  # Então é o vértice "b" que encosta no pai.
                        if segment.b.vertexId == 0:
                            node.flow = 2  # Inverter!
                        else:
                            node.flow = 1  # Manter!

                # Obtendo os filhos.
                parentID = -1 if parent.setId == 1 else parent.featureId
                childSegments = self.topologicalRelations.findChildSegments(
                    segment.featureId, parentID, sibling_nodes
                )

                # Classificando o nó.
                childNode = None

                # Instanciar o nó com valor inicial 1 para Strahler e Shreve
                # para eliminar a necessidade de definit os valores para os nós.
                # Não será necessário avaliar (filhosSegmento.size() == 0).
                if not childSegments:  # Nó sem filhos. É folha!
                    # Classificando por Strahler
                    if self.params.strahlerOrderType > 0:
                        node.strahler = 1
                    # Classificando por Shreve.
                    if self.params.shreveOrderEnabled:
                        node.shreve = 1
                elif (
                    len(childSegments) == 1
                ):  # Fazer classificação do pai igual a do filho.
                    # Processando o filho único.
                    result, childNode = self.createNodes(
                        childSegments[0], segment, childSegments, result
                    )

                    if result == 0 and childNode:
                        node.addChild(childNode)

                        # Classificando por Strahler.
                        # TODO: Passar essa lógica para No::inserirFilhoNo()!
                        if self.params.strahlerOrderType > 0:
                            node.strahler = childNode.strahler

                        # Classificando por Shreve.
                        # TODO: Passar essa lógica para No::inserirFilhoNo()!
                        if self.params.shreveOrderEnabled:
                            node.shreve = childNode.shreve
                else:  # Nó com dois ou mais filhos.
                    if len(childSegments) > 2 and self.params.strahlerOrderType == 1:
                        # Gravando a mensagem de mais de três afluentes no log.
                        msg_1 = (
                            "Aviso! Estrutura topológica não esperada para "
                            "hierarquização Strahler."
                        )
                        msg_2 = " A Feição FID"
                        msg_3 = " recebe mais de dois afluentes em um mesmo ponto."
                        msg_4 = "Os identificadores desses afluentes são:"
                        msg_5 = (
                            "O resultado final apresentará a classificação "
                            "por Strahler relaxado."
                        )
                        self.log.append(
                            msg_1
                            + msg_2
                            + str(segment.featureId)
                            + msg_3
                            + "\n"
                            + msg_4
                        )

                        # Listando os filhos.
                        for i, child in enumerate(childSegments):
                            self.log.append(
                                "   " + str(i + 1) + " - FID" + str(child.featureId)
                            )
                        self.log.append("\n" + msg_5)

                        # Configurando a classificação Strahler leve.
                        self.params.strahlerOrderType = 2

                    # Cadastrando os nós filhos.
                    for child in childSegments:
                        result, childNode = self.createNodes(
                            child, segment, childSegments, result
                        )
                        if result == 0 and childNode:
                            # As regras para a classificação por Strahler e Shreve
                            # estão no método No::inserirFilhoNo().
                            node.addChild(childNode)

                # Gravando classificação.
                if result == 0:
                    self.drainage.setFeatureClassification(
                        node.featureId,
                        node.flow,
                        node.strahler,
                        node.shreve,
                    )
            else:  # Feição já processada!
                msg_1 = (
                    "Erro! impossível continuar! Estrutura topológica não "
                    "esperada para hierarquização."
                )
                msg_5 = "Confira a topologia e execute o processamento novamente."
                if loopBasin:
                    result = 5
                    msg_2 = " Existem feições em anel (loop)."
                    msg_4 = (
                        "Verifique as feições: FID"
                        + str(segment.featureId)
                        + " e FID"
                        + str(parent.featureId)
                        + "."
                    )
                    # Gravando o erro no log.
                    self.log.append(msg_1 + msg_2 + "\n" + msg_4 + "\n\n" + msg_5)
                else:  # Conexão entre bacias.
                    result = 6
                    msg_2 = " Os sistemas de drenagem associados a foz FID"
                    msg_3 = " e a foz FID"
                    msg_4 = " estão conectados."

                    # Gravando o erro no log.
                    self.log.append(
                        msg_1
                        + msg_2
                        + str(currentFeature.featureId)
                        + msg_3
                        + str(currentFeature.mouthFeatureId)
                        + msg_4
                        + "\n\n"
                        + msg_5
                    )

        return result, node

    def evaluateProcessing(self) -> int:
        result = 0
        msg_0 = ""
        msg_1 = "Aviso: a feição FID"
        msg_2 = " não foi processada. Confira a topologia da rede de drenagem."
        msg_3 = "Feicao nao processada."

        for i in range(self.drainage.getTotalFeatures()):
            feature = self.drainage.getFeature(i)
            if feature and (
                feature.flow == 0
                or (self.params.strahlerOrderType > 0 and feature.strahler == 0)
                or (self.params.shreveOrderEnabled and feature.shreve == 0)
            ):
                msg_0 = msg_1 + str(feature.featureId) + msg_2
                self.log.append(msg_0)
                self.drainage.obs.set_value(feature.featureId, msg_3)
                feature.hasObservation = True
                result = 1

        return result
