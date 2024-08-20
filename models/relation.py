from typing import Optional

from models.feature import Feature
from models.segment import Segment
from utils.message import Message


class RelationItem:
    def __init__(
        self,
        source: Optional[Segment] = None,
        destination: Optional[Segment] = None,
        relationType: Optional[int] = 0,
    ):
        self.source = source
        self.destination = destination
        self.relationType = relationType


class IndexItem:
    def __init__(self, feature: Feature, value: int):
        self.feature = feature
        self.value = value


class Relation:
    def __init__(self, log: Message) -> None:
        self.log = log

        self.items: list[RelationItem] = []
        self.err: list[RelationItem] = []
        self.mouths: list[RelationItem] = []

        self.index: list[IndexItem] = []
        self.primaryIndex: list[IndexItem] = []

    def cleanup(self) -> None:
        self.__init__(self.log)

    def insert(
        self,
        start: int,
        end: int,
        source: Segment,
        destination: Segment,
        relation_type: int,
    ) -> None:
        if start <= end:
            item = RelationItem(source, destination, relation_type)

            # Calculando o meio (indice).
            middle = (start + end) // 2

            # Lendo o item do meio.
            middle_item = self.items[middle] if relation_type == 0 else self.err[middle]

            # Comparando os itens.
            comparison = self.compare_position(item, middle_item)

            # (item < itemMeio)
            if comparison == -1:
                if start == end or start == middle:  # (inicio == fim) Não encontrou.
                    # Inserir no ponteiro atual(meio).
                    if relation_type == 0:
                        self.items.insert(middle, item)
                    else:
                        self.err.insert(middle, item)
                elif start < middle:  # (meio > 0)
                    self.insert(start, middle - 1, source, destination, relation_type)
                else:  # É inicio da lista (meio = 0).
                    if relation_type == 0:
                        self.items.insert(0, item)
                    else:
                        self.err.insert(0, item)
            # (item > itemMeio)
            elif comparison == 1:
                if relation_type == 0:
                    if middle == len(self.items) - 1:  # Se meio é ultimo elemento.
                        self.items.append(item)
                    elif start == end:
                        self.items.insert(middle, item)
                    else:
                        self.insert(middle + 1, end, source, destination, relation_type)
                else:  # Cadastrar relações indesejadas.
                    if middle == len(self.err) - 1:  # Se meio é ultimo elemento.
                        self.err.append(item)
                    elif start == end:
                        self.err.insert(middle, item)
                    else:
                        self.insert(middle + 1, end, source, destination, relation_type)

    def addMouth(self, basin: Segment, boundary: Segment) -> None:
        # Garantindo que o primeiro argumento é da bacia.
        item = RelationItem()
        if basin.setId == 0:
            basin.isMouth = True
            item.source = basin
            item.destination = boundary
        else:
            boundary.isMouth = True
            item.source = boundary
            item.destination = basin

        # Garantindo que a foz não foi incluida antes.
        found = False
        for i in range(len(self.mouths)):
            if item.source.idFeicao == self.mouths[i].source.featureId:
                found = True
                break

        if not found:
            # Inserindo em fozes.
            self.mouths.append(item)

    def addRelation(self, source: Segment, destination: Segment, relation_type: int):
        """
        Tipos de relação topológica:
        0 - Encosta
        1 - Toca
        2 - Intercepta
        """

        # Garantindo que o FID do primeiro segmento seja menor que o FID do segundo.
        if destination.featureId < source.featureId:
            temp = source
            source = destination
            destination = temp

        # Verificando se é relação entre foz e limite.
        # Só aceita relação topológica do tipo encosta entre foz e limite da bacia!
        if source.setId != destination.setId and relation_type == 0:
            self.addMouth(source, destination)  # Versão 1.3!

        # Verificando se os segmenos são de feições diferentes da bacia.
        elif (
            source.featureId != destination.featureId
            and source.setId == 0
            and destination.setId == 0
        ):
            if relation_type == 0:  # Escosta.
                if len(self.items) == 0:
                    self.items.append(RelationItem(source, destination, relation_type))
                else:
                    self.insert(
                        0, len(self.items) - 1, source, destination, relation_type
                    )
            else:  # Tipo de evento errado. Incluindo na lista de erros.
                if len(self.err) == 0:
                    self.err.append(RelationItem(source, destination, relation_type))
                else:
                    self.insert(
                        0, len(self.err) - 1, source, destination, relation_type
                    )
        # Os segmentos da orígem e destino são da mesma feição. Não gravar!

    def findChildSegments(
        self, featureId: int, parentFeatureId: int, siblings: list[Segment]
    ) -> list[Segment]:
        result = []

        # Obtendo o índice primário.
        primaryIndex = self.findPrimaryIndex(0, len(self.primaryIndex) - 1, featureId)
        if primaryIndex >= 0:
            reached_end = False
            evaluate = False
            isChild = False
            primaryItem = None
            eventItem = None
            relatedSegment = None
            childSegment = None
            indexSize = len(self.index)

            while not reached_end and primaryIndex < indexSize:
                # Obtendo o índice do evento.
                primaryItem = self.index[primaryIndex]

                if primaryItem.feature.id == featureId:
                    # Lendo evento.
                    eventItem = self.items[primaryItem.value]

                    evaluate = True
                    if (
                        eventItem.source.featureId == featureId
                        and eventItem.destination.featureId != parentFeatureId
                    ):
                        relatedSegment = eventItem.destination
                    elif (
                        eventItem.destination.featureId == featureId
                        and eventItem.source.featureId != parentFeatureId
                    ):
                        relatedSegment = eventItem.source
                    else:
                        evaluate = False

                    if evaluate:
                        isChild = True
                        for i in range(len(siblings)):
                            childSegment = siblings[i]
                            if relatedSegment.featureId == childSegment.featureId:
                                isChild = False
                        if isChild:
                            result.append(relatedSegment)

                    primaryIndex += 1
                else:
                    reached_end = True

        return result

    def compare_position(self, a: RelationItem, b: RelationItem) -> int:
        if (
            a.source.idFeicao == b.source.idFeicao
            and a.destination.idFeicao == b.destination.idFeicao
            and a.relationType == b.relationType
        ):
            return 0
        elif (
            a.source.idFeicao < b.source.idFeicao
            or (
                a.source.idFeicao == b.source.idFeicao
                and a.destination.idFeicao < b.destination.idFeicao
            )
            or (
                a.source.idFeicao == b.source.idFeicao
                and a.destination.idFeicao == b.destination.idFeicao
                and a.relationType < b.relationType
            )
        ):
            return -1
        else:
            return 1

    def findPrimaryIndex(self, start: int, end: int, featureId: int) -> int:
        if start <= end and self.primaryIndex:
            middle = (start + end) // 2
            item = self.primaryIndex[middle]

            if featureId == item.feature.id:
                return item.value
            else:
                if featureId < item.feature.id:
                    return self.findPrimaryIndex(start, middle - 1, featureId)
                else:
                    return self.findPrimaryIndex(middle + 1, end, featureId)
        return -1

    def compareIndexItems(self, a: IndexItem, b: IndexItem) -> bool:
        if a.feature.id == b.feature.id:
            if a.value < b.value:
                return True
        elif a.feature.id < b.feature.id:
            return True
        return False

    def buildIndexes(self) -> None:
        # Montando índice principal.
        self.index.clear()

        eventItem = None
        for i in range(len(self.items)):
            eventItem = self.items[i]

            # Verificando se são ocorrências de bacia.
            self.index.append(IndexItem(eventItem.source, i))
            self.index.append(IndexItem(eventItem.destination, i))

        # Ordenando o índice principal.
        self.index.sort(key=self.compareIndexItems)

        # Montando o índice primário.
        self.primaryIndex.clear()
        featureId = -1
        indexItem = None
        for i in range(len(self.index)):
            indexItem = self.index[i]
            if indexItem.feature.id != featureId:
                featureId = indexItem.feature.id
                self.primaryIndex.append(IndexItem(featureId, i))

    def reportUnexpectedRelations(self, log: Message) -> None:
        msg_1 = (
            "Erro! Impossível continuar! Encontradas relações topológicas inesperadas."
        )
        msg_2 = "São esperadas somente relações de encosta, entretanto foram encontradas as relações:"
        msg_3 = "Consulte a documentação deste aplicativo para mais detalhes sobre as relações topológicas esperadas e inesperadas."
        msg_4 = "Confira a topologia e execute o processamento novamente."
        log.append(msg_1 + "\n" + msg_2)

        if self.err:
            for item in self.err:
                eventType = (
                    " toca em FID" if item.relationType == 1 else " intercepta FID"
                )
                log.append(
                    "   FID"
                    + str(item.source.featureId)
                    + eventType
                    + str(item.destination.featureId)
                )
            log.append("   Total de relações: " + str(len(self.err)) + ".")
            log.append("\n" + msg_3)
            log.append(msg_4)
