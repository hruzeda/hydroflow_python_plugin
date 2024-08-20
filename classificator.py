from typing import Optional

from models.feature_set import FeatureSet
from models.iterator import Iterator, IteratorRow
from models.node import Node
from models.params import Params
from models.position import Position
from models.relation import Relation
from utils.geometry import Geometry


class Classificator:
    def __init__(
        self,
        drainage: Optional[FeatureSet],
        boundary: Optional[FeatureSet],
        params: Params,
        log,
    ) -> None:
        self.drainage = drainage
        self.boundary = boundary
        self.params = params
        self.geo = Geometry(params.getToleranciaXY())
        self.iterator = Iterator(self.geo)
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
        self.buildIterator()

        # Varrendo o plano;
        self.iteratePlane()

        # Verificando a existência de relações topológicas inesperadas (toque e interseção).
        if self.topologicalRelations.haErros():
            # Listando os eventos estranhos.
            self.topologicalRelations.listarEventosInesperados(self.log)
            result = 5
        else:
            # Classificando a bacia hidrográfica.
            result = self.buildTree()

            # Validando o processamento das feições.
            if result == 0:
                result = self.evaluateProcessing()
        return result

    def buildIterator(self) -> None:
        self.iterator.addRows(self.drainage.featuresList)
        self.iterator.addRows(self.drainage.newFeaturesList, True)
        self.iterator.addRows(self.boundary.featuresList)
        self.iterator.sortRows()

    def iteratePlane(self) -> None:
        record = 0
        above = 0
        below = 0
        iteratorLine = 0
        previousIteration = 0
        index_A = 0
        index_B = 0
        lv = 0

        # Iniciando a varredura.
        lv = self.iterator.next()
        previousIteration = lv.point.x

        while lv != 0:
            iteratorLine = lv.point.x
            record = lv.segmentA

            # Verificando se mudou a linha de varredura.
            if self.geo.smallerThan(previousIteration, iteratorLine):
                # Processando a linha de varredura anterior.
                self.processIteratorPoints(previousIteration)
                previousIteration = iteratorLine

            # Inserir segmento(s) no ponto de varredura.
            self.iterator.inserirPontoVarredura(lv)

            # Processando o evento da linha de varredura.
            if lv.eventType == 0:  # Extremo esquerdo. Segmento entrando.
                # Inserindo em posição.
                index_A = self.position.inserir(record)

                # Verificando segmento imediatamente acima.
                above = self.position.acima(index_A)
                if above != 0:  # Se há segmento acima:
                    self.evaluateSegments(lv.point, above, record)

                # Verificando segmento imediatamente abaixo.
                below = self.position.abaixo(index_A)
                if below != 0:  # Se há segmento abaixo:
                    self.evaluateSegments(lv.point, record, below)
            elif lv.getTipoEvento() == 1:
                # Localizando o segmento em Posicao.
                index_A = self.position.localizar(iteratorLine, record)

                # Verificando segmento imediatamente acima.
                above = self.position.acima(index_A)
                if above != 0:
                    # Verificando segmento imediatamente abaixo.
                    below = self.position.abaixo(index_A)
                    if below != 0:
                        self.evaluateSegments(lv.point, above, below)

                # Excluindo de posição.
                self.position.excluir(index_A)
            elif lv.getTipoEvento() == 2:  # Interseção.
                # Separando interseção por toque.
                if (
                    not self.geo.equalsTo(lv.point, lv.segmentA.getA())
                    and not self.geo.equalsTo(lv.point, lv.segmentA.getB())
                    and not self.geo.equalsTo(lv.point, lv.segmentB.getA())
                    and not self.geo.equalsTo(lv.point, lv.segmentB.getB())
                ):
                    # Localizando os segmentos.
                    index_A = self.position.localizar(iteratorLine, lv.segmentA)
                    index_B = self.position.localizar(iteratorLine, lv.segmentB)

                    # Trocando segmentos de posição .
                    self.position.trocar(index_A, index_B)

                    # Verificando segmento imediatamente acima.
                    above = self.position.acima(index_A)
                    if above != 0:  # Se há segmento acima:
                        self.evaluateSegments(lv.point, above, lv.segmentB)

                    # Verificando segmento imediatamente abaixo.
                    below = self.position.abaixo(index_B)
                    if below != 0:  # Se há segmento abaixo:
                        self.evaluateSegments(lv.point, lv.segmentA, below)

            lv.limparVarreduraItem()
            lv = self.iterator.next()

        # Processando os pontos da ultima linha de varredura.
        self.processIteratorPoints(previousIteration)
        self.position.limparPosicao()

    def evaluateSegments(self, point, above, below) -> None:
        intersectionPoint = 0

        # Verificando se há interseção.
        if self.geo.pontoIntersecao(above, below, intersectionPoint):
            # Selecionando a área de interesse para o ponto de interseção.
            if (
                intersectionPoint.getX() >= (point.getX() - self.geo.getTolerancia())
                and intersectionPoint.getY()
                >= (point.getY() - self.geo.getTolerancia())
            ) or (
                intersectionPoint.getX() > (point.getX() + self.geo.getTolerancia())
                and intersectionPoint.getY() < (point.getY() - self.geo.getTolerancia())
            ):
                # Separando as interseções do tipo encosta.
                if not (
                    (
                        self.geo.equalsTo(intersectionPoint, above.getA())
                        and self.geo.equalsTo(intersectionPoint, below.getB())
                    )
                    or (
                        self.geo.equalsTo(intersectionPoint, above.getB())
                        and self.geo.equalsTo(intersectionPoint, below.getA())
                    )
                    or (
                        self.geo.equalsTo(intersectionPoint, above.getA())
                        and self.geo.equalsTo(intersectionPoint, below.getA())
                    )
                    or (
                        self.geo.equalsTo(intersectionPoint, above.getB())
                        and self.geo.equalsTo(intersectionPoint, below.getB())
                    )
                ):
                    # Inserindo a interseção na lista de varredura.
                    self.iterator.inserir(
                        IteratorRow(intersectionPoint, 2, [above, below])
                    )

    def processIteratorPoints(self, iteratorLine):
        segment = 0
        point = 0
        test = []

        # Obtendo o primiro ponto de varradura.
        iteratorPoint = self.iterator.getPontoVarredura(iteratorLine)

        while iteratorPoint != 0:
            if iteratorPoint.getQuantidadeSegmentos() > 1:  # Há relações topológicas.
                point = iteratorPoint.point

                # Testando os segmentos.
                for k in range(iteratorPoint.getQuantidadeSegmentos()):
                    segment = iteratorPoint.getSegmento(k)
                    test.append(
                        (
                            self.geo.equalsTo(point, segment.getA())
                            and (
                                segment.getA().eExtremo()
                                or segment.getIdConjunto() == 1
                            )
                        )
                        or (
                            self.geo.equalsTo(point, segment.getB())
                            and (
                                segment.getB().eExtremo()
                                or segment.getIdConjunto() == 1
                            )
                        )
                    )

                # Avaliando as relações topológicas.
                for i in range(iteratorPoint.getQuantidadeSegmentos() - 1):
                    for j in range(i + 1, iteratorPoint.getQuantidadeSegmentos()):
                        if test.at(i) and test.at(j):  # Encosta.
                            self.topologicalRelations.inserirRelacao(
                                iteratorPoint.getSegmento(i),
                                iteratorPoint.getSegmento(j),
                                0,
                            )
                        elif test.at(i) or test.at(j):  # Toca.
                            self.topologicalRelations.inserirRelacao(
                                iteratorPoint.getSegmento(i),
                                iteratorPoint.getSegmento(j),
                                1,
                            )
                        else:  # Intercepta.
                            self.topologicalRelations.inserirRelacao(
                                iteratorPoint.getSegmento(i),
                                iteratorPoint.getSegmento(j),
                                2,
                            )

            # Limpando o ponto de varedura corrente.
            iteratorPoint.limparPontoVarredura()

            # Lendo o próximo ponto de varredura.
            iteratorPoint = self.iterator.getPontoVarredura(iteratorLine)

    def buildTree(self):
        """
        Valores de retorno:
        0 - processamento correto
        2 - foz não identificada
        3 - mais de uma foz identificada - Não utilizado no processamento de várias fozes!
        4 - nó com mais de dois filhos
        5 - nó em loop
        6 - bacias interconectadas
        """
        result = 0

        if self.topologicalRelations.getQuantidadeFozes() > 0:
            # Montando os índices dos eventos.
            self.topologicalRelations.montarIndices()

            # Construindo a árvore que representa cada bacia.
            entrypointRelation = 0
            filhos = []
            for i in range(self.topologicalRelations.getQuantidadeFozes()):
                entrypointRelation = self.topologicalRelations.getFoz(i)

                # origem: segmento da foz; destino: segmento do limite.
                result = self.createNodes(
                    entrypointRelation.getOrigem(),
                    entrypointRelation.getDestino(),
                    filhos,
                    result,
                )[0]
        else:
            result = 2  # Foz não identificada!!!

        return result

    def createNodes(self, segment, parent, sibling_nodes, result):
        """
        Valores para resultado:
        0 - processamento sem erros
        4 - nó com mais de dois filhos
        5 - nó em loop
        6 - bacias interconectadas
        """
        node = 0

        if result == 0:
            # Verificando a condição de interconexão entre árvores.
            loopBasin = False
            basinConnection = False
            currentFeature = self.drainage.getFeicao(segment.getIdFeicao())

            if segment.getEFoz():
                # A feição corrente é a feição da foz e o segmento pai é do limite da bacia.
                # É o início do processamento de uma bacia!

                # Verificando se a feição da foz já foi processada.
                if currentFeature.getIdFeicaoFoz() < 0:
                    # Árvore ainda não processada.
                    currentFeature.setIdFeicaoFoz(currentFeature.getId())
                else:
                    # Árvore já processada. Existe interconexão entre bacias!
                    basinConnection = True
            else:
                if currentFeature.getIdFeicaoFoz() < 0:
                    currentFeature.setIdFeicaoFoz(
                        self.drainage.getFeicao(parent.getIdFeicao()).getIdFeicaoFoz()
                    )
                else:
                    # Feição já processada. Existe um loop na árvore!
                    loopBasin = True

            # Verificando a condição de loop na árvore ou interconexão entre árvores.
            if not loopBasin and not basinConnection:
                node = Node(segment.getIdFeicao())

                # Processando o fluxo.
                if currentFeature.getNSegmentos() > 1:  # Vários segmentos.
                    if segment.getId() == 0:
                        node.setFluxo(2)  # Inverter!
                    else:
                        node.setFluxo(1)  # Manter!
                else:  # Segmento único.
                    # Verificando se o vértice "a" do segmento encosta no pai.
                    if segment.getA().eIgual(parent.getA()) or segment.getA().eIgual(
                        parent.getB()
                    ):
                        if segment.getA().getId() == 0:
                            node.setFluxo(2)  # Inverter!
                        else:
                            node.setFluxo(1)  # Manter!
                    else:  # Então é o vértice "b" que encosta no pai.
                        if segment.getB().getId() == 0:
                            node.setFluxo(2)  # Inverter!
                        else:
                            node.setFluxo(1)  # Manter!

                # Obtendo os filhos.
                parentID = -1 if parent.getIdConjunto() == 1 else parent.getIdFeicao()
                newParent = 0  # O novo pai é o segmento atual!
                childSegments = self.topologicalRelations.getFilhosNo(
                    segment.getIdFeicao(), parentID, sibling_nodes, newParent
                )

                # Classificando o nó.
                childNode = 0

                # Instanciar o nó com valor inicial 1 para Strahler e Shreve para eliminar a necessidade
                # de usar os métodos No::setStrahler() e No::setShreve().
                # Não será necessário avaliar (filhosSegmento.size() == 0).
                if len(childSegments) == 0:  # Nó sem filhos. É folha!
                    # Classificando por Strahler
                    if self.params.getTipoOrdemStrahler() > 0:
                        node.setStrahler(1)
                    # Classificando por Shreve.
                    if self.params.getEOrdemShreve():
                        node.setShreve(1)
                elif (
                    len(childSegments) == 1
                ):  # Fazer classificação do pai igual a do filho.
                    # Processando o filho único.
                    result, childNode = self.createNodes(
                        childSegments[0], segment, childSegments, result
                    )

                    if result == 0:
                        node.inserirFilhoNo(childNode)

                        # Classificando por Strahler. Passar essa lógica para No::inserirFilhoNo()!
                        if self.params.getTipoOrdemStrahler() > 0:
                            node.setStrahler(childNode.getStrahler())

                        # //Classificando por Shreve. Passar essa lógica para No::inserirFilhoNo()!
                        if self.params.getEOrdemShreve():
                            node.setShreve(childNode.getShreve())
                else:  # Nó com dois ou mais filhos.
                    if (
                        len(childSegments) > 2
                        and self.params.getTipoOrdemStrahler() == 1
                    ):
                        # Gravando a mensagem de mais de três afluentes no log.
                        msg_1 = "Aviso! Estrutura topológica não esperada para hierarquização Strahler."
                        msg_2 = " A Feição FID"
                        msg_3 = " recebe mais de dois afluentes em um mesmo ponto."
                        msg_4 = "Os identificadores desses afluentes são:"
                        msg_5 = "O resultado final apresentará a classificação por Strahler relaxado."
                        self.log.append(
                            msg_1
                            + msg_2
                            + str(segment.getIdFeicao())
                            + msg_3
                            + "\n"
                            + msg_4
                        )

                        # Listando os filhos.
                        for i in range(len(childSegments)):
                            filho = childSegments[i]
                            self.log.append(
                                "   " + str(i + 1) + " - FID" + str(filho.getIdFeicao())
                            )
                        self.log.append("\n" + msg_5)

                        # Configurando a classificação Strahler leve.
                        self.params.setTipoOrdemStrahler(2)

                    # Cadastrando os nós filhos.
                    for i in range(len(childSegments)):
                        result, childNode = self.createNodes(
                            childSegments[i], segment, childSegments, result
                        )
                        if result == 0:
                            # As regras para a classificação por Strahler e Shreve estão no método No::inserirFilhoNo().
                            node.inserirFilhoNo(childNode)

                # Gravando classificação.
                if result == 0:
                    self.drainage.setFeatureClassification(
                        node.getIdFeicao(),
                        node.getFluxo(),
                        node.getStrahler(),
                        node.getShreve(),
                    )
            else:  # Feição já processada!
                msg_1 = "Erro! impossível continuar! Estrutura topológica não esperada para hierarquização."
                msg_2 = ""
                msg_3 = ""
                msg_4 = ""
                msg_5 = "Confira a topologia e execute o processamento novamente."
                if loopBasin:
                    result = 5
                    msg_2 = " Existem feições em anel (loop)."
                    msg_4 = (
                        "Verifique as feições: FID"
                        + str(segment.getIdFeicao())
                        + " e FID"
                        + str(parent.getIdFeicao())
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
                        + str(currentFeature.getId())
                        + msg_3
                        + str(currentFeature.getIdFeicaoFoz())
                        + msg_4
                        + "\n\n"
                        + msg_5
                    )

        return result, node

    def evaluateProcessing(self):
        result = 0
        msg_0 = ""
        msg_1 = "Aviso: a feição FID"
        msg_2 = " não foi processada. Confira a topologia da rede de drenagem."
        msg_3 = "Feicao nao processada."
        feature = 0

        for i in range(self.drainage.getTotalFeatures()):
            feature = self.drainage.getFeature(i)
            if (
                feature.getFluxo() == 0
                or (
                    self.params.getTipoOrdemStrahler() > 0
                    and feature.getStrahler() == 0
                )
                or (self.params.getEOrdemShreve() and feature.getShreve() == 0)
            ):
                msg_0 = msg_1 + str(feature.getId()) + msg_2
                self.log.append(msg_0)
                self.drainage.setObservacao(feature.getId(), msg_3)
                feature.setTemObservacao(True)
                result = 1

        return result
