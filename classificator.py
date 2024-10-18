from decimal import Decimal
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
            previousPoint = scanLine.vertex.x

        while scanLine is not None:
            scanLineVertex = scanLine.vertex
            scanLineCoord = scanLineVertex.x
            record = scanLine.segmentA

            if self.geo.smallerThan(previousPoint, scanLineCoord):
                self.processScanPoints(previousPoint)
                previousPoint = scanLineCoord

            # Inserir segmento(s) no ponto de varredura.
            self.scanner.addScanPoint(scanLine)

            # Processando o evento da linha de varredura.
            if scanLine.eventType == 0:  # Extremo esquerdo. Segmento entrando.
                # Inserindo em posição.
                index_A = self.position.insert(record)

                # Verificando segmento imediatamente acima.
                above = self.position.above(index_A)
                if above:  # Se há segmento acima:
                    self.evaluateSegments(scanLineVertex, above, record)

                # Verificando segmento imediatamente abaixo.
                below = self.position.below(index_A)
                if below:  # Se há segmento abaixo:
                    self.evaluateSegments(scanLineVertex, record, below)

            elif scanLine.eventType == 1:
                # Localizando o segmento em Posicao.
                index_A = self.position.locate(scanLineCoord, record)

                # Verificando segmento imediatamente acima.
                above = self.position.above(index_A)
                if above:
                    # Verificando segmento imediatamente abaixo.
                    below = self.position.below(index_A)
                    if below:
                        self.evaluateSegments(scanLineVertex, above, below)

                # Excluindo de posição.
                self.position.delete(index_A)

            elif scanLine.eventType == 2 and scanLine.segmentB:  # Interseção.
                # Separando interseção por toque.
                if all(
                    [
                        not self.geo.equalsTo(scanLineVertex, scanLine.segmentA.a),
                        not self.geo.equalsTo(scanLineVertex, scanLine.segmentA.b),
                        scanLine.segmentB
                        and not self.geo.equalsTo(
                            scanLineVertex, scanLine.segmentB.a
                        )
                        and not self.geo.equalsTo(
                            scanLineVertex, scanLine.segmentB.b
                        ),
                    ]
                ):
                    # Localizando os segmentos.
                    index_A = self.position.locate(scanLineCoord, scanLine.segmentA)
                    index_B = self.position.locate(scanLineCoord, scanLine.segmentB)

                    # Trocando segmentos de posição .
                    self.position.swap(index_A, index_B)

                    # Verificando segmento imediatamente acima.
                    above = self.position.above(index_A)
                    if above:  # Se há segmento acima:
                        self.evaluateSegments(
                            scanLineVertex, above, scanLine.segmentB
                        )

                    # Verificando segmento imediatamente abaixo.
                    below = self.position.below(index_B)
                    if below:  # Se há segmento abaixo:
                        self.evaluateSegments(
                            scanLineVertex, scanLine.segmentA, below
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

    def processScanPoints(self, scanLine: Decimal) -> None:
        test = []

        # Obtendo o primeiro ponto de varradura.
        scanVertex = self.scanner.nextInLine(scanLine)
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

            scanVertex = self.scanner.nextInLine(scanLine)

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
                    currentFeature.mouthFeatureId = currentFeature.originalFeatureId
                else:
                    # Árvore já processada. Existe interconexão entre bacias!
                    basinConnection = True
            else:
                parentFeature = self.drainage.getFeature(parent.featureId)
                if parentFeature and currentFeature.mouthFeatureId < 0:
                    currentFeature.mouthFeatureId = parentFeature.originalFeatureId
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
                childSegments = self.topologicalRelations.findChildSegments(
                    segment.originalFeatureId,
                    -1 if parent.setId == 1 else parent.originalFeatureId,
                    sibling_nodes,
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

                if len(childSegments) > 2 and self.params.strahlerOrderType == 1:
                    # Gravando a mensagem de mais de três afluentes no log.
                    self._log_too_many_children(segment, childSegments)

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
                        featureId=node.featureId,
                        flow=node.flow,
                        strahler=node.strahler,
                        shreve=node.shreve,
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
                        + str(segment.originalFeatureId)
                        + " e FID"
                        + str(parent.originalFeatureId)
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
                        + str(currentFeature.originalFeatureId)
                        + msg_3
                        + str(currentFeature.mouthFeatureId)
                        + msg_4
                        + "\n\n"
                        + msg_5
                    )

        return result, node

    def _log_too_many_children(
        self, segment: Segment, childSegments: list[Segment]
    ) -> None:
        self.log.append(
            "Aviso! Estrutura topológica não esperada para "
            "hierarquização Strahler. "
            f"A Feição FID{segment.originalFeatureId} "
            "recebe mais de dois afluentes em um mesmo ponto.\n"
            "Os identificadores desses afluentes são:"
        )

        # Listando os filhos.
        for i, child in enumerate(childSegments):
            self.log.append(f"   {i + 1} - FID{child.originalFeatureId}")

    def evaluateProcessing(self) -> int:
        result = 0

        for i in range(self.drainage.getTotalFeatures()):
            feature = self.drainage.getFeature(i)
            if feature and (
                feature.flow == 0
                or (self.params.strahlerOrderType > 0 and feature.strahler == 0)
                or (self.params.shreveOrderEnabled and feature.shreve == 0)
            ):
                self.log.append(
                    f"Aviso: a feição FID{feature.originalFeatureId} "
                    "não foi processada. Confira a topologia da rede de drenagem."
                )
                self.drainage.obs.set_value(
                    feature.originalFeatureId, "Feicao nao processada."
                )
                feature.hasObservation = True
                result = 1

        return result
