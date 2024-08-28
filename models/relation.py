import functools

from qgis.core import Qgis, QgsMessageLog

from ..utils.message import Message
from .segment import Segment


class RelationItem:
    def __init__(
        self,
        source: Segment,
        destination: Segment,
        relationType: int,
    ):
        self.source = source
        self.destination = destination
        self.relationType = relationType


class IndexItem:
    def __init__(self, featureId: int, value: int):
        self.featureId = featureId
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
        self.items.clear()
        self.err.clear()
        self.mouths.clear()
        self.index.clear()
        self.primaryIndex.clear()

    def insert(
        self,
        source: Segment,
        destination: Segment,
        relation_type: int,
    ) -> None:
        newItem = RelationItem(source, destination, relation_type)

        if self.items:
            for i, item in enumerate(self.items if relation_type == 0 else self.err):
                comp = self.comparePosition(newItem, item)

                if comp == 0:
                    return

                if comp < 0:
                    if relation_type == 0:
                        self.items.insert(i, newItem)
                    else:
                        self.err.insert(i, newItem)
                    return

        if relation_type == 0:
            self.items.append(newItem)
        else:
            self.err.append(newItem)

    def addMouth(self, drainage: Segment, boundary: Segment) -> None:
        # Garantindo que o primeiro argumento é da bacia.

        if drainage.setId == 0:
            drainage.isMouth = True
            item = RelationItem(drainage, boundary, 0)
        else:
            boundary.isMouth = True
            item = RelationItem(boundary, drainage, 0)

        # Garantindo que a foz não foi incluida antes.
        found = False
        for mouth in self.mouths:
            if item.source.featureId == mouth.source.featureId:
                found = True
                break

        if not found:
            # Inserindo em fozes.
            self.mouths.append(item)

    def addRelation(self, source: Segment, destination: Segment, relationType: int):
        """
        Tipos de relação topológica:
        0 - Encosta
        1 - Toca
        2 - Intercepta
        """
        QgsMessageLog.logMessage(
            (
                f"Adicionando relação entre FID {source.featureId} "
                f"e FID {destination.featureId} do tipo {relationType}."
            ),
            "HydroFlow",
            Qgis.MessageLevel.Info,
        )

        # Garantindo que o FID do primeiro segmento seja menor que o FID do segundo.
        if destination.featureId < source.featureId:
            source, destination = destination, source

        # Verificando se é relação entre foz e limite.
        # Só aceita relação topológica do tipo encosta entre foz e limite da bacia!
        if source.setId != destination.setId and relationType == 0:
            self.addMouth(source, destination)  # Versão 1.3!

        # Verificando se os segmenos são de feições diferentes da bacia.
        elif (
            source.featureId != destination.featureId
            and source.setId == 0
            and destination.setId == 0
        ):
            if relationType == 0:  # Escosta.
                if not self.items:
                    self.items.append(
                        RelationItem(source, destination, relationType)
                    )
                else:
                    self.insert(source, destination, relationType)
            else:  # Tipo de evento errado. Incluindo na lista de erros.
                if not self.err:
                    self.err.append(RelationItem(source, destination, relationType))
                else:
                    self.insert(source, destination, relationType)
        # Os segmentos da orígem e destino são da mesma feição. Não gravar!

    def findChildSegments(
        self, featureId: int, parentFeatureId: int, siblings: list[Segment]
    ) -> list[Segment]:
        result = []

        # Obtendo o índice primário.
        primaryIndex = self.findPrimaryIndex(featureId)
        if primaryIndex >= 0:
            reached_end = False
            isChild = False
            primaryItem = None
            eventItem = None
            relatedSegment = None
            childSegment = None
            indexSize = len(self.index)

            while not reached_end and primaryIndex < indexSize:
                # Obtendo o índice do evento.
                primaryItem = self.index[primaryIndex]

                if primaryItem.featureId == featureId:
                    # Lendo evento.
                    eventItem = self.items[primaryItem.value]

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

                    if relatedSegment:
                        isChild = True
                        for childSegment in siblings:
                            if relatedSegment.featureId == childSegment.featureId:
                                isChild = False
                        if isChild:
                            result.append(relatedSegment)

                    primaryIndex += 1
                else:
                    reached_end = True

        return result

    def comparePosition(self, a: RelationItem, b: RelationItem) -> int:
        if (
            a.source.featureId == b.source.featureId
            and a.destination.featureId == b.destination.featureId
            and a.relationType == b.relationType
        ):
            return 0
        if (
            a.source.featureId < b.source.featureId
            or (
                a.source.featureId == b.source.featureId
                and a.destination.featureId < b.destination.featureId
            )
            or (
                a.source.featureId == b.source.featureId
                and a.destination.featureId == b.destination.featureId
                and a.relationType < b.relationType
            )
        ):
            return -1
        return 1

    def findPrimaryIndex(self, featureId: int) -> int:
        for item in self.primaryIndex:
            if featureId == item.featureId:
                return item.value
        return -1

    def compareIndexItems(self, a: IndexItem, b: IndexItem) -> int:
        return (
            b.value - a.value
            if a.featureId == b.featureId
            else b.featureId - a.featureId
        )

    def buildIndexes(self) -> None:
        # Montando índice principal.
        self.index.clear()

        eventItem = None
        for i, eventItem in enumerate(self.items):
            # Verificando se são ocorrências de bacia.
            self.index.append(IndexItem(eventItem.source.featureId, i))
            self.index.append(IndexItem(eventItem.destination.featureId, i))

        # Ordenando o índice principal.
        self.index.sort(key=functools.cmp_to_key(self.compareIndexItems))

        # Montando o índice primário.
        self.primaryIndex.clear()
        featureId = -1
        indexItem = None
        for i, indexItem in enumerate(self.index):
            if indexItem.featureId != featureId:
                self.primaryIndex.append(IndexItem(indexItem.featureId, i))

    def reportUnexpectedRelations(self, log: Message) -> None:
        msg_1 = (
            "Erro! Impossível continuar! "
            "Encontradas relações topológicas inesperadas."
        )
        msg_2 = (
            "São esperadas somente relações de encosta, "
            "entretanto foram encontradas as relações:"
        )
        msg_3 = (
            "Consulte a documentação deste aplicativo para mais "
            "detalhes sobre as relações topológicas esperadas e inesperadas."
        )
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
